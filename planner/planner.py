"""
Planner
Generates ordered execution plan from intent (no LLM)
"""

from typing import List, Dict
from planner.causal_graph import get_dependencies, get_constraint_action, validate_action


class ActionStep:
    """Represents a single action in the execution plan"""
    def __init__(self, action: str, parameters: dict, requires_approval: bool = False):
        self.action = action
        self.parameters = parameters
        self.requires_approval = requires_approval
    
    def __repr__(self):
        approval = " [APPROVAL REQUIRED]" if self.requires_approval else ""
        return f"ActionStep({self.action}, {self.parameters}){approval}"


def create_plan(intent: dict) -> List[ActionStep]:
    """
    Create ordered execution plan from parsed intent
    
    Args:
        intent: Parsed intent dictionary with 'intent', 'entities', 'constraints'
    
    Returns:
        Ordered list of ActionStep objects
    
    Raises:
        ValueError: If action is not whitelisted or invalid
    """
    action = intent["intent"]
    entities = intent.get("entities", {})
    constraints = intent.get("constraints", [])
    
    # Validate action is allowed
    if not validate_action(action):
        raise ValueError(f"Action '{action}' is not whitelisted")
    
    plan = []
    
    # Add constraint-triggered actions first
    for constraint in constraints:
        constraint_action = get_constraint_action(constraint)
        if constraint_action:
            # Add prerequisite action (e.g., contact lookup before drafting email)
            if constraint_action == "search_contact" and "recipient_name" in entities:
                plan.append(ActionStep(
                    action="search_contact",
                    parameters={"name": entities["recipient_name"]},
                    requires_approval=False
                ))
            elif constraint_action == "check_calendar" and "date" in entities:
                plan.append(ActionStep(
                    action="check_calendar",
                    parameters={"date": entities.get("date", "today")},
                    requires_approval=False
                ))
    
    # Add dependency actions
    dependencies = get_dependencies(action)
    for dep in dependencies:
        # Don't duplicate actions already added
        if not any(step.action == dep for step in plan):
            plan.append(ActionStep(
                action=dep,
                parameters=entities,
                requires_approval=False
            ))
    
    # Add main action
    requires_approval = "approval_required" in constraints
    plan.append(ActionStep(
        action=action,
        parameters=entities,
        requires_approval=requires_approval
    ))
    
    return plan


def plan_to_dict(plan: List[ActionStep]) -> List[dict]:
    """
    Convert plan to dictionary format for logging/debugging
    
    Args:
        plan: List of ActionStep objects
    
    Returns:
        List of dictionaries
    """
    return [
        {
            "action": step.action,
            "parameters": step.parameters,
            "requires_approval": step.requires_approval
        }
        for step in plan
    ]


if __name__ == "__main__":
    # Test planner
    test_intents = [
        {
            "intent": "draft_email",
            "entities": {"recipient_name": "John", "body": "Meeting postponed"},
            "constraints": ["contact_lookup", "approval_required"]
        },
        {
            "intent": "schedule_meeting",
            "entities": {"date": "tomorrow", "time": "3 PM"},
            "constraints": ["conflict_check", "approval_required"]
        },
        {
            "intent": "list_files",
            "entities": {"directory": "Documents"},
            "constraints": []
        }
    ]
    
    for intent in test_intents:
        print(f"\nIntent: {intent['intent']}")
        plan = create_plan(intent)
        for step in plan:
            print(f"  {step}")
