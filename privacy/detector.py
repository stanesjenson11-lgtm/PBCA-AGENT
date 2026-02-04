"""
Privacy Violation Detector
Scans text for sensitive information using policies
"""

import re
import json
from typing import List, Dict
from config.settings import PRIVACY_POLICY_PATH


class PrivacyViolation:
    """Represents a detected privacy violation"""
    def __init__(self, pattern_name: str, description: str, matched_text: str, position: int):
        self.pattern_name = pattern_name
        self.description = description
        self.matched_text = matched_text
        self.position = position
    
    def __repr__(self):
        return f"PrivacyViolation({self.pattern_name}: {self.description})"


def load_policies() -> dict:
    """Load privacy policies from JSON file"""
    try:
        with open(PRIVACY_POLICY_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: Privacy policy file not found at {PRIVACY_POLICY_PATH}")
        return {"sensitive_patterns": [], "blocked_topics": [], "pii_keywords": []}


def scan_for_violations(text: str) -> List[PrivacyViolation]:
    """
    Scan text for privacy violations
    
    Args:
        text: Input text to scan
    
    Returns:
        List of detected violations (empty if clean)
    """
    violations = []
    policies = load_policies()
    
    # Check regex patterns
    for pattern in policies.get("sensitive_patterns", []):
        regex = pattern["regex"]
        matches = re.finditer(regex, text)
        
        for match in matches:
            violations.append(PrivacyViolation(
                pattern_name=pattern["name"],
                description=pattern["description"],
                matched_text=match.group(0),
                position=match.start()
            ))
    
    # Check blocked topics (case-insensitive keyword matching)
    text_lower = text.lower()
    for topic in policies.get("blocked_topics", []):
        if topic.lower() in text_lower:
            position = text_lower.find(topic.lower())
            violations.append(PrivacyViolation(
                pattern_name="blocked_topic",
                description=f"Blocked topic: {topic}",
                matched_text=topic,
                position=position
            ))
    
    # Check PII keywords
    for keyword in policies.get("pii_keywords", []):
        if keyword.lower() in text_lower:
            position = text_lower.find(keyword.lower())
            violations.append(PrivacyViolation(
                pattern_name="pii",
                description=f"PII keyword: {keyword}",
                matched_text=keyword,
                position=position
            ))
    
    return violations


if __name__ == "__main__":
    # Test the detector
    test_texts = [
        "My password is 12345",
        "The meeting is at 3 PM",
        "My SSN is 123-45-6789",
        "Please send the api_key: abcd1234567890xyz"
    ]
    
    for text in test_texts:
        violations = scan_for_violations(text)
        print(f"\nText: {text}")
        print(f"Violations: {violations}")
