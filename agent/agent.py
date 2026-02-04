"""
Main Agent Orchestration
Implements the 8-step security pipeline
"""

import logging
from typing import Dict, Optional
from agent.intent_parser import parse_with_correction
from agent.mistral_llm import query_mistral
from agent.conversation import handle_conversation, is_greeting, is_joke_request
from privacy.enforcer import check_and_block
from planner.planner import create_plan, ActionStep
from tools import email_tool, calendar_tool, desktop_tool, web_search_tool
from memory.audit_logger import log_action


class Agent:
    """
    PBCA Agent - Privacy-Preserving AI Assistant
    Implements fail-safe execution pipeline
    """
    
    def __init__(self):
        self.pending_approvals = {}  # draft_id -> {type, data, step}
        logging.basicConfig(level=logging.INFO)
    
    async def process_message(self, user_id: str, message: str) -> str:
        """
        Main pipeline: Process user message through 8-step security flow
        """
        try:
            # STEP 1: Receive message
            logging.info(f"[AGENT] Processing message from {user_id}")
            
            # CHECK PENDING APPROVALS FIRST
            if str(user_id) in self.pending_approvals:
                if message.lower() in ['yes', 'y', 'confirm', 'send', 'approve']:
                    return self.handle_approval(user_id, True)
                elif message.lower() in ['no', 'n', 'cancel', 'stop']:
                    return self.handle_approval(user_id, False)
            
            # Check if this is a conversational message (greeting or joke request)
            if is_greeting(message) or is_joke_request(message):
                logging.info(f"[AGENT] Handling as conversational message")
                response = handle_conversation(user_id, message)
                log_action("telegram", user_id, "conversation", "chat", {"message": message}, {"response": response})
                return response
            
            # STEP 2: Parse intent with grammar correction
            try:
                intent = parse_with_correction(message)
                logging.info(f"[AGENT] Parsed intent: {intent['intent']}")
                
                # Check for explicit conversation intent
                if intent['intent'] == 'conversation':
                    logging.info(f"[AGENT] Intent is conversation, routing to handler")
                    response = handle_conversation(user_id, message)
                    log_action("telegram", user_id, "conversation", "chat", {"message": message}, {"response": response})
                    return response
                    
            except Exception as e:
                # If intent parsing fails, try conversational fallback
                logging.warning(f"[AGENT] Intent parsing failed, trying conversational handler: {e}")
                try:
                    response = handle_conversation(user_id, message)
                    log_action("telegram", user_id, "conversation", "chat", {"message": message}, {"response": response})
                    return response
                except Exception as conv_e:
                    error_msg = f"Failed to parse intent: {e}"
                    logging.error(f"[AGENT] {error_msg}")
                    log_action("telegram", user_id, message, blocked_reason=error_msg)
                    return f"❌ {error_msg}"
            
            # STEP 4: Enforce privacy (before planning)
            privacy_check = check_and_block(message)
            if not privacy_check["allowed"]:
                reason = privacy_check["reason"]
                logging.warning(f"[AGENT] Privacy violation: {reason}")
                log_action("telegram", user_id, message, blocked_reason=reason)
                return f"🔒 {reason}"
            
            # Also check corrected text if present
            if "corrected_text" in intent:
                privacy_check = check_and_block(intent["corrected_text"])
                if not privacy_check["allowed"]:
                    reason = privacy_check["reason"]
                    log_action("telegram", user_id, message, blocked_reason=reason)
                    return f"🔒 {reason}"
            
            # STEP 3: Generate causal plan
            try:
                plan = create_plan(intent)
                logging.info(f"[AGENT] Created plan with {len(plan)} steps")
            except Exception as e:
                error_msg = f"Planning failed: {e}"
                logging.error(f"[AGENT] {error_msg}")
                log_action("telegram", user_id, intent['intent'], blocked_reason=error_msg)
                return f"❌ {error_msg}"
            
            # STEP 5 & 6: Execute plan
            response = await self.execute_plan(user_id, intent, plan)
            
            # STEP 7: Log action (done in execute_plan)
            
            # STEP 8: Return response
            return response
        
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            logging.error(f"[AGENT] {error_msg}", exc_info=True)
            log_action("telegram", user_id, message, blocked_reason=error_msg)
            return f"❌ {error_msg}"
    
    def handle_approval(self, user_id: str, approved: bool) -> str:
        """Handle user response to approval request"""
        approval_data = self.pending_approvals.pop(str(user_id))
        
        if not approved:
            log_action("telegram", user_id, "approval", "cancel", approval_data)
            return "❌ Action cancelled."
            
        try:
            # Execute the pending action
            if approval_data["type"] == "email":
                draft_id = approval_data["draft_id"]
                result = email_tool.send_email(draft_id)
                log_action("telegram", user_id, "send_email", "send_email", {"draft_id": draft_id}, result)
                if result.get("success"):
                    return f"✅ Email sent successfully!"
                else:
                    return f"❌ Failed to send: {result.get('error')}"
                    
            elif approval_data["type"] == "action_step":
                # Re-execute the specific step
                step = approval_data["step"]
                # Bypass approval check this time
                step.requires_approval = False
                result = self.execute_action(step)
                log_action("telegram", user_id, "approval", step.action, step.parameters, result)
                return f"✅ {step.action} completed."
            
            return "✅ Approved."
            
        except Exception as e:
            logging.error(f"Approval execution failed: {e}")
            return f"❌ Error executing approved action: {e}"

    async def execute_plan(self, user_id: str, intent: dict, plan: list) -> str:
        """
        Execute action plan with approval gates and data dependency handling
        """
        results = []
        last_result = {}
        
        for step in plan:
            logging.info(f"[AGENT] Executing step: {step.action}")
            
            # Dependency Injection: Pass data from previous steps
            if step.action == 'send_email':
                # If we have a draft from previous step, use it
                if last_result and isinstance(last_result, dict) and 'draft_id' in last_result:
                    step.parameters['draft_id'] = last_result['draft_id']
            
            # FORCE APPROVAL for critical steps if not already set
            if step.action == 'draft_email':
                step.requires_approval = True

            try:
                result = self.execute_action(step)
                last_result = result
                
                if not result.get("success", False):
                    error_msg = result.get("error", "Unknown error")
                    log_action("telegram", user_id, intent['intent'], step.action, 
                             step.parameters, result, error_msg)
                    return f"❌ Action '{step.action}' failed: {error_msg}"
                
                results.append(result)
                
                # If this step requires approval (e.g. draft_email, delete_file), return preview and wait
                if step.requires_approval:
                    return self.request_approval(user_id, intent, step, result)
                
                # Log successful action
                log_action("telegram", user_id, intent['intent'], step.action, 
                         step.parameters, result)
            
            except Exception as e:
                error_msg = f"Execution error: {e}"
                logging.error(f"[AGENT] {error_msg}", exc_info=True)
                log_action("telegram", user_id, intent['intent'], step.action, 
                         step.parameters, blocked_reason=error_msg)
                return f"❌ {error_msg}"
        
        # All steps completed
        return self.format_response(intent, results)
    
    def execute_action(self, step: ActionStep) -> Dict:
        """
        Execute a single action step
        """
        action = step.action
        params = step.parameters
        
        # Route to appropriate tool
        if action == "search_contact":
            email = email_tool.search_contact(params.get("name", params.get("recipient_name")))
            if email:
                return {"success": True, "email": email}
            else:
                return {"success": False, "error": f"Contact '{params.get('name')}' not found"}
        
        elif action == "draft_email":
            to = params.get("to")
            # If no 'to', try to use result from contact search (not ideal but fallback)
            # Better: In execute_plan, we should inject this too if needed. 
            # But search_contact usually is skipped if entity extraction got the email. 
            # Here we just check params.
            
            if not to and "recipient_name" in params:
                to = email_tool.search_contact(params["recipient_name"])
            
            if not to:
                return {"success": False, "error": "No recipient specified"}
            
            subject = params.get("subject", "Message")
            body = params.get("body", "")
            
            draft = email_tool.draft_email(to, subject, body)
            return {
                "success": True,
                "draft_id": draft.draft_id,
                "draft": draft.to_dict(),  # Convert to dict for JSON serialization
                "preview": draft.format_preview()
            }
        
        elif action == "send_email":
            draft_id = params.get("draft_id")
            return email_tool.send_email(draft_id)
        
        elif action == "list_files":
            directory = params.get("directory", "Documents")
            return desktop_tool.list_files(directory)
        
        elif action == "create_file":
            path = params.get("path") or params.get("filename", "untitled.txt")
            content = params.get("content", "")
            return desktop_tool.create_file(path, content)
            
        elif action == "create_directory":
            # Extract directory path/name
            name = params.get("name")
            location = params.get("directory")
            
            if name and location and name.lower() not in location.lower():
                # User said "create folder X in Y"
                # Join them so desktop_tool can resolve location
                # desktop_tool.resolve_directory handles "downloads" -> "C:/.../Downloads"
                # So we pass "downloads/X"
                path = os.path.join(location, name)
            else:
                path = params.get("path") or location or name or "New Folder"
                
            return desktop_tool.create_directory(path)
        
        elif action == "delete_file":
            path = params.get("path") or params.get("filename")
            return desktop_tool.delete_file(path)
        
        elif action == "open_app":
            app_name = params.get("app_name")
            return desktop_tool.open_app(app_name)
        
        elif action == "check_calendar":
            date = params.get("date", "today")
            return calendar_tool.check_calendar(date)
        
        elif action == "schedule_meeting":
            title = params.get("title", "Meeting")
            time_str = params.get("time", "3 PM")
            date = params.get("date", params.get("day", "today"))
            description = params.get("description", "")
            return calendar_tool.create_event(title, time_str, 60, date, description)
        
        elif action == "status":
            return {
                "success": True,
                "status": "Agent operational",
                "features": ["LLM", "Privacy", "Scheduler"]
            }
        
        elif action == "help":
            return {
                "success": True,
                "help_text": "Send /help for command list"
            }
            
        elif action == "reminder":
            # Map reminder to calendar event
            # Logic: "remind me to call tim tomorrow at 10pm" -> create event
            # This relies on entities having date/time/description
            title = params.get("title", params.get("description", "Reminder"))
            time_str = params.get("time", "9 AM")
            date = params.get("date", "today")
            description = params.get("description", "Reminder created by Zeic")
            
            # Use calendar tool
            return calendar_tool.create_event(title, time_str, 30, date, description)
            
        elif action == "web_search":
            query = params.get("query")
            if not query:
                return {"success": False, "error": "No search query provided"}
            
            # 1. Perform Search
            search_result = web_search_tool.search(query)
            if not search_result["success"]:
                return search_result
            
            # 2. Synthesize Answer
            results = search_result["results"]
            if not results:
                return {"success": True, "answer": f"I couldn't find any information about '{query}'."}
            
            # Construct context for LLM
            context = "\n".join([f"- {r['title']}: {r['body']}" for r in results[:3]])
            
            system_prompt = "You are a helpful assistant. Answer the user's question based ONLY on the provided search results. Be concise and natural."
            prompt = f"User Question: {query}\n\nSearch Results:\n{context}\n\nAnswer:"
            
            try:
                answer = query_mistral(prompt, system_prompt)
                return {
                    "success": True,
                    "query": query,
                    "results": results,
                    "answer": answer
                }
            except Exception as e:
                return {"success": False, "error": f"Failed to synthesize answer: {e}"}

        else:
            return {"success": False, "error": f"Unknown action: {action}"}
    
    def request_approval(self, user_id: str, intent: dict, step: ActionStep, result: dict) -> str:
        """Generate approval request message"""
        action = step.action
        
        if action == "draft_email":
            # Store pending approval
            draft = result.get("draft")
            if draft:
                self.pending_approvals[str(user_id)] = {
                    "type": "email",
                    "draft_id": draft["draft_id"],  # Access as dict
                    "data": result
                }
            return result.get("preview", "")
        
        elif action == "delete_file":
            filename = step.parameters.get("filename")
            return f"⚠️ Delete {filename}? This cannot be undone. Reply 'yes' to confirm"
        
        elif action == "create_file":
            filename = step.parameters.get("filename")
            return f"📄 Creating {filename}. Reply 'yes' to confirm"
        
        else:
            return f"⚠️ Approve {action}? Reply 'yes' to confirm"
    
    def format_response(self, intent: dict, results: list) -> str:
        """Format final response from execution results"""
        action = intent["intent"]
        
        if action == "list_files":
            result = results[-1]
            files = result.get("files", [])
            count = result.get("count", 0)
            directory = result.get("directory", "")
            
            if count == 0:
                return f"📁 {directory} is empty"
            
            file_list = "\n".join([
                f"  {'📁' if f['type'] == 'directory' else '📄'} {f['name']}" +
                (f" ({f['size']} bytes)" if f['type'] == 'file' else "")
                for f in files[:20]  # Limit to 20
            ])
            
            more = f"\n... and {count - 20} more" if count > 20 else ""
            return f"📁 {directory} ({count} items):\n{file_list}{more}"
        
        elif action == "check_calendar":
            result = results[-1]
            events = result.get("events", [])
            date = result.get("date", "")
            
            if not events:
                return f"📅 No events on {date}"
            
            event_list = "\n".join([
                f"  • {e['title']} ({e['start']} - {e['end']})"
                for e in events
            ])
            return f"📅 Events on {date}:\n{event_list}"
        
        elif action == "schedule_meeting":
            result = results[-1]
            return f"✅ {result.get('message', 'Event created')}"
            
        elif action == "reminder":
            result = results[-1]
            return f"✅ {result.get('message', 'Reminder set')}"
        
        elif action == "create_file":
            result = results[-1]
            return f"✅ {result.get('message', 'File created')}"
            
        elif action == "create_directory":
            result = results[-1]
            return f"✅ {result.get('message', 'Directory created')}"
        
        elif action == "delete_file":
            result = results[-1]
            return f"✅ {result.get('message', 'File deleted')}"
            
        elif action == "web_search":
            result = results[-1]
            return f"🌐 {result.get('answer', 'No answer found.')}\n\n[Source: DuckDuckGo]"
        
        else:
            return "✅ Action completed successfully"


if __name__ == "__main__":
    # Test agent
    import asyncio
    
    async def test():
        agent = Agent()
        
        test_messages = [
            "list files in Documents",
            "check my calendar today",
        ]
        
        for msg in test_messages:
            print(f"\n>>> {msg}")
            response = await agent.process_message("test_user", msg)
            print(f"<<< {response}")
    
    asyncio.run(test())
