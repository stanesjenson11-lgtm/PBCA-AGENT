"""
Email Tool
Draft and send emails with contact lookup and approval workflow
"""

import json
from typing import Optional
from config.settings import CONTACTS_PATH, REQUIRE_APPROVAL_FOR_SEND


class EmailDraft:
    """Represents an email draft"""
    def __init__(self, to: str, subject: str, body: str, draft_id: int = None):
        self.to = to
        self.subject = subject
        self.body = body
        self.draft_id = draft_id or id(self)
    
    def __repr__(self):
        return f"EmailDraft(to={self.to}, subject={self.subject})"
    
    def format_preview(self) -> str:
        """Format draft for user preview"""
        return f"""📧 Draft Email Preview:
To: {self.to}
Subject: {self.subject}
Body: {self.body}

Reply 'send' to send, 'edit subject: New Subject' to change, or 'cancel'"""

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "draft_id": self.draft_id,
            "to": self.to,
            "subject": self.subject,
            "body": self.body
        }


# In-memory draft storage (would be persistent in production)
_drafts = {}


def load_contacts() -> list:
    """Load contacts from JSON file"""
    try:
        with open(CONTACTS_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: Contacts file not found at {CONTACTS_PATH}")
        return []


def search_contact(name: str) -> Optional[str]:
    """
    Search for contact email by name
    
    Args:
        name: Contact name or alias
    
    Returns:
        Email address or None if not found
    """
    contacts = load_contacts()
    name_lower = name.lower()
    
    for contact in contacts:
        # Check exact name match
        if contact["name"].lower() == name_lower:
            return contact["email"]
        
        # Check aliases
        for alias in contact.get("aliases", []):
            if alias.lower() == name_lower:
                return contact["email"]
    
    return None


def draft_email(to: str, subject: str, body: str) -> EmailDraft:
    """
    Create email draft
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body
    
    Returns:
        EmailDraft object
    """
    draft = EmailDraft(to=to, subject=subject, body=body)
    _drafts[draft.draft_id] = draft
    return draft


def send_email(draft_id: int) -> dict:
    """
    Send email using real SMTP
    
    Args:
        draft_id: Draft ID to send
    
    Returns:
        Result dictionary
    """
    if draft_id not in _drafts:
        return {"success": False, "error": "Draft not found"}
    
    draft = _drafts[draft_id]
    
    # Import settings specifically here to avoid circular imports or early init
    from config.settings import EMAIL_ADDRESS, EMAIL_PASSWORD, SMTP_SERVER, SMTP_PORT
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    # Check if credentials are configured
    if "your_email" in EMAIL_ADDRESS or "your_app_password" in EMAIL_PASSWORD:
        return {
            "success": False, 
            "error": "❌ Email credentials not configured in settings.py. Please set EMAIL_ADDRESS and EMAIL_PASSWORD (App Password)."
        }

    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = draft.to
        msg['Subject'] = draft.subject
        
        msg.attach(MIMEText(draft.body, 'plain'))
        
        print(f"[SMTP] Connecting to {SMTP_SERVER}:{SMTP_PORT}...")
        
        # Connect to SMTP server
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Upgrade connection to secure
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            
            print(f"[SMTP] Sending email to {draft.to}...")
            server.send_message(msg)
        
        # Clean up draft after sending
        del _drafts[draft_id]
        
        return {
            "success": True,
            "message": f"✅ Email sent successfully to {draft.to}"
        }
        
    except Exception as e:
        print(f"[SMTP ERROR]: {e}")
        return {
            "success": False,
            "error": f"Failed to send email: {str(e)}"
        }


def get_draft(draft_id: int) -> Optional[EmailDraft]:
    """Get draft by ID"""
    return _drafts.get(draft_id)


def update_draft(draft_id: int, subject: str = None, body: str = None) -> bool:
    """Update existing draft"""
    if draft_id not in _drafts:
        return False
    
    draft = _drafts[draft_id]
    if subject:
        draft.subject = subject
    if body:
        draft.body = body
    
    return True


if __name__ == "__main__":
    # Test email tool
    print("Testing contact lookup:")
    email = search_contact("John")
    print(f"John's email: {email}")
    
    print("\nTesting email draft:")
    draft = draft_email(
        to=email,
        subject="Meeting Update",
        body="The meeting has been postponed."
    )
    print(draft.format_preview())
    
    print("\nTesting email send:")
    result = send_email(draft.draft_id)
    print(result)
