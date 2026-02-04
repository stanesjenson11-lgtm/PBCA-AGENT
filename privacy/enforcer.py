"""
Privacy Enforcer
Blocks execution if violations are detected
"""

from typing import Tuple, List
from privacy.detector import scan_for_violations, PrivacyViolation


def enforce_privacy(text: str) -> Tuple[bool, str, List[PrivacyViolation]]:
    """
    Enforce privacy policies on input text
    
    Args:
        text: Input text to validate
    
    Returns:
        Tuple of (is_allowed, reason, violations)
        - is_allowed: True if no violations, False otherwise
        - reason: Human-readable explanation
        - violations: List of detected violations
    """
    violations = scan_for_violations(text)
    
    if not violations:
        return True, "No privacy violations detected", []
    
    # Build violation message
    violation_details = []
    for v in violations:
        violation_details.append(f"- {v.description} (matched: '{v.matched_text}')")
    
    reason = "Privacy violation detected:\n" + "\n".join(violation_details)
    
    return False, reason, violations


def check_and_block(text: str) -> dict:
    """
    Check text and return enforcement result
    
    Args:
        text: Text to check
    
    Returns:
        Dict with 'allowed', 'reason', and 'violations' keys
    """
    is_allowed, reason, violations = enforce_privacy(text)
    
    return {
        "allowed": is_allowed,
        "reason": reason,
        "violations": [
            {
                "type": v.pattern_name,
                "description": v.description,
                "matched": v.matched_text
            }
            for v in violations
        ]
    }


if __name__ == "__main__":
    # Test enforcement
    test_cases = [
        "Schedule a meeting tomorrow at 3 PM",
        "My password is secret123",
        "The API key is abc123def456ghi789"
    ]
    
    for text in test_cases:
        result = check_and_block(text)
        print(f"\nText: {text}")
        print(f"Allowed: {result['allowed']}")
        if not result['allowed']:
            print(f"Reason: {result['reason']}")
