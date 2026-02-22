"""
Smart Email Inbox Triage Tool
Connect to Gmail inbox, read unread emails, and classify each
using local Mistral LLM as: Urgent / Reply-Needed / Can-Ignore.
Returns a ranked Telegram digest.
"""

import logging
import imaplib
import email
from email.header import decode_header
from datetime import datetime

logger = logging.getLogger(__name__)


class TriageTool:
    """
    Smart email triage — fetches unread emails and classifies them
    using Mistral (local LLM) into urgency categories.
    """

    def execute(self, entities: dict) -> dict:
        """
        Triage the inbox.

        Args:
            entities: {
                'count': int (max emails to triage, default 10),
                'folder': str (IMAP folder, default 'INBOX')
            }
        """
        from config.settings import EMAIL_ADDRESS, EMAIL_PASSWORD

        if "your_email" in EMAIL_ADDRESS or "your_app_password" in EMAIL_PASSWORD:
            return {
                "success": False,
                "error": "❌ Email credentials not configured. Set EMAIL_ADDRESS and EMAIL_PASSWORD in settings.py."
            }

        max_count = int(entities.get("count", 10))
        folder = entities.get("folder", "INBOX")

        try:
            # Connect to Gmail via IMAP
            logger.info("[TRIAGE] Connecting to IMAP...")
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            mail.select(folder)

            # Search for unread emails
            status, messages = mail.search(None, "UNSEEN")
            if status != "OK":
                return {"success": False, "error": "Failed to search inbox."}

            email_ids = messages[0].split()
            if not email_ids:
                return {
                    "success": True,
                    "count": 0,
                    "message": "📧 No unread emails! Your inbox is clean. 🎉"
                }

            # Limit
            email_ids = email_ids[-max_count:]
            logger.info(f"[TRIAGE] Found {len(email_ids)} unread emails.")

            # Fetch email summaries
            email_summaries = []
            for eid in email_ids:
                try:
                    _, msg_data = mail.fetch(eid, "(RFC822)")
                    msg = email.message_from_bytes(msg_data[0][1])

                    subject = self._decode_header(msg.get("Subject", "No Subject"))
                    sender = self._decode_header(msg.get("From", "Unknown"))
                    date = msg.get("Date", "Unknown")

                    # Get body preview
                    body = self._get_body(msg)[:300]

                    email_summaries.append({
                        "id": eid.decode(),
                        "from": sender,
                        "subject": subject,
                        "date": date,
                        "body_preview": body
                    })
                except Exception as e:
                    logger.error(f"[TRIAGE] Error parsing email {eid}: {e}")
                    continue

            mail.logout()

            if not email_summaries:
                return {"success": True, "count": 0, "message": "📧 Could not parse any emails."}

            # Classify using Mistral
            classified = self._classify_emails(email_summaries)

            # Format digest
            digest = self._format_digest(classified)

            return {
                "success": True,
                "count": len(classified),
                "emails": classified,
                "message": digest
            }

        except imaplib.IMAP4.error as e:
            logger.error(f"[TRIAGE] IMAP error: {e}")
            return {"success": False, "error": f"IMAP error: {e}"}
        except Exception as e:
            logger.error(f"[TRIAGE] Error: {e}")
            return {"success": False, "error": f"Triage failed: {e}"}

    def _decode_header(self, header: str) -> str:
        """Decode email header."""
        try:
            decoded, charset = decode_header(header)[0]
            if isinstance(decoded, bytes):
                return decoded.decode(charset or "utf-8", errors="replace")
            return str(decoded)
        except Exception:
            return str(header)

    def _get_body(self, msg) -> str:
        """Extract plain text body from email."""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    try:
                        return part.get_payload(decode=True).decode("utf-8", errors="replace")
                    except Exception:
                        continue
        else:
            try:
                return msg.get_payload(decode=True).decode("utf-8", errors="replace")
            except Exception:
                return ""
        return ""

    def _classify_emails(self, emails: list) -> list:
        """Classify emails using local Mistral LLM."""
        try:
            from agent.mistral_llm import query_mistral
        except ImportError:
            logger.error("[TRIAGE] Cannot import LLM interface.")
            for e in emails:
                e["category"] = "Unknown"
                e["summary"] = e["subject"]
            return emails

        for em in emails:
            try:
                prompt = f"""Classify this email into EXACTLY one category: URGENT, REPLY_NEEDED, or CAN_IGNORE.
Also provide a one-line summary.

From: {em['from']}
Subject: {em['subject']}
Body Preview: {em['body_preview'][:200]}

Respond in EXACTLY this format:
Category: [URGENT/REPLY_NEEDED/CAN_IGNORE]
Summary: [one-line summary]"""

                system = "You are an email classifier. Respond only in the exact format requested."
                result = query_mistral(prompt, system)

                # Parse response
                lines = result.strip().split("\n")
                category = "Unknown"
                summary = em["subject"]

                for line in lines:
                    if line.lower().startswith("category:"):
                        cat = line.split(":", 1)[1].strip().upper()
                        if cat in ("URGENT", "REPLY_NEEDED", "CAN_IGNORE"):
                            category = cat
                    elif line.lower().startswith("summary:"):
                        summary = line.split(":", 1)[1].strip()

                em["category"] = category
                em["summary"] = summary

            except Exception as e:
                logger.error(f"[TRIAGE] Classification failed for {em['subject']}: {e}")
                em["category"] = "Unknown"
                em["summary"] = em["subject"]

        return emails

    def _format_digest(self, emails: list) -> str:
        """Format classified emails into a digest."""
        # Sort by priority
        priority = {"URGENT": 0, "REPLY_NEEDED": 1, "CAN_IGNORE": 2, "Unknown": 3}
        emails.sort(key=lambda e: priority.get(e.get("category", "Unknown"), 3))

        icons = {"URGENT": "🔴", "REPLY_NEEDED": "🟡", "CAN_IGNORE": "🟢", "Unknown": "⚪"}

        lines = [f"📧 Inbox Triage ({len(emails)} emails):\n"]

        for em in emails:
            icon = icons.get(em["category"], "⚪")
            lines.append(f"{icon} [{em['category']}] {em['subject']}")
            lines.append(f"   From: {em['from']}")
            lines.append(f"   📝 {em['summary']}")
            lines.append("")

        return "\n".join(lines)

    def get_capabilities(self) -> list:
        return ["triage_inbox"]


_tool = TriageTool()


def triage_inbox(entities: dict = None) -> dict:
    return _tool.execute(entities or {})
