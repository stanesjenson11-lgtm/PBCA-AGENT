"""
Audit Logger
Persistent logging of all actions and decisions
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from config.settings import DB_PATH


def init_database():
    """Initialize audit log database"""
    # Create memory directory if it doesn't exist
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            source TEXT NOT NULL,
            user_id TEXT,
            intent TEXT NOT NULL,
            action TEXT,
            parameters TEXT,
            result TEXT,
            blocked_reason TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    print(f"[AUDIT] Database initialized at {DB_PATH}")


def log_action(source: str, user_id: str, intent: str, action: str = None, 
               parameters: dict = None, result: dict = None, blocked_reason: str = None):
    """
    Log an action to the audit trail
    
    Args:
        source: Source of request ('telegram', 'cli', 'scheduler')
        user_id: User identifier
        intent: Intent or request description
        action: Action taken
        parameters: Action parameters
        result: Result dictionary
        blocked_reason: Reason if action was blocked
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO audit_log 
        (timestamp, source, user_id, intent, action, parameters, result, blocked_reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        source,
        str(user_id),
        intent,
        action,
        json.dumps(parameters) if parameters else None,
        json.dumps(result) if result else None,
        blocked_reason
    ))
    
    conn.commit()
    conn.close()


def get_recent_logs(limit: int = 10) -> list:
    """Get recent audit log entries"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT timestamp, source, intent, action, result, blocked_reason
        FROM audit_log
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "timestamp": row[0],
            "source": row[1],
            "intent": row[2],
            "action": row[3],
            "result": row[4],
            "blocked_reason": row[5]
        }
        for row in rows
    ]


if __name__ == "__main__":
    # Test audit logger
    init_database()
    
    log_action(
        source="telegram",
        user_id="123456",
        intent="draft_email",
        action="search_contact",
        parameters={"name": "John"},
        result={"email": "john@example.com"}
    )
    
    print("Recent logs:")
    for log in get_recent_logs(5):
        print(f"  {log}")
