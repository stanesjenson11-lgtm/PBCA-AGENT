"""
Causal Graph
Defines dependencies between actions (no LLM involved)
"""

# Action dependency graph
# Format: action -> list of prerequisite actions
CAUSAL_DEPENDENCIES = {
    "send_email": ["draft_email"],
    "schedule_meeting": ["check_calendar"],
    "draft_email": [],  # May require contact_lookup via constraints
    "check_calendar": [],
    "list_files": [],
    "create_file": [],
    "create_directory": [],
    "delete_file": [],
    "open_app": [],
    "reminder": [],
    "web_search": [],
    "status": [],
    "help": []
}

# Constraints that trigger additional actions
CONSTRAINT_ACTIONS = {
    "contact_lookup": "search_contact",
    "conflict_check": "check_calendar",
    "approval_required": None,  # Handled by executor, not a separate action
}


def get_dependencies(action: str) -> list:
    """
    Get prerequisite actions for a given action
    
    Args:
        action: Action name
    
    Returns:
        List of prerequisite action names
    """
    return CAUSAL_DEPENDENCIES.get(action, [])


def get_constraint_action(constraint: str) -> str:
    """
    Get the action triggered by a constraint
    
    Args:
        constraint: Constraint name
    
    Returns:
        Action name or None
    """
    return CONSTRAINT_ACTIONS.get(constraint)


def validate_action(action: str) -> bool:
    """
    Check if action is in the whitelist
    
    Args:
        action: Action name to validate
    
    Returns:
        True if action is allowed
    """
    return action in CAUSAL_DEPENDENCIES


if __name__ == "__main__":
    # Test the graph
    print("Testing causal dependencies:")
    for action in ["send_email", "schedule_meeting", "list_files"]:
        deps = get_dependencies(action)
        print(f"{action} requires: {deps}")
