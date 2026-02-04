"""
Task Scheduler
Persistent cron-like scheduling with approval
"""

import schedule
import time
import json
import threading
from datetime import datetime
from typing import Dict, Callable


# Scheduled task storage
_scheduled_tasks = []
_task_file = "memory/scheduled_tasks.json"


class ScheduledTask:
    """Represents a scheduled task"""
    def __init__(self, task_id: str, description: str, schedule_spec: str, 
                 action: str, parameters: dict, approved: bool = False):
        self.task_id = task_id
        self.description = description
        self.schedule_spec = schedule_spec  # e.g., "every monday at 09:00"
        self.action = action
        self.parameters = parameters
        self.approved = approved
        self.created_at = datetime.now().isoformat()
    
    def to_dict(self):
        return {
            "task_id": self.task_id,
            "description": self.description,
            "schedule_spec": self.schedule_spec,
            "action": self.action,
            "parameters": self.parameters,
            "approved": self.approved,
            "created_at": self.created_at
        }


def load_tasks():
    """Load scheduled tasks from file"""
    try:
        with open(_task_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def save_tasks():
    """Save scheduled tasks to file"""
    with open(_task_file, 'w') as f:
        json.dump([t.to_dict() for t in _scheduled_tasks], f, indent=2)


def create_scheduled_task(description: str, schedule_spec: str, 
                         action: str, parameters: dict) -> ScheduledTask:
    """
    Create a new scheduled task (requires approval before execution)
    
    Args:
        description: Human-readable description
        schedule_spec: Schedule specification
        action: Action to execute
        parameters: Action parameters
    
    Returns:
        ScheduledTask object
    """
    task_id = f"task_{int(time.time())}"
    
    task = ScheduledTask(
        task_id=task_id,
        description=description,
        schedule_spec=schedule_spec,
        action=action,
        parameters=parameters,
        approved=False
    )
    
    _scheduled_tasks.append(task)
    save_tasks()
    
    return task


def approve_task(task_id: str) -> bool:
    """Approve a scheduled task for execution"""
    for task in _scheduled_tasks:
        if task.task_id == task_id:
            task.approved = True
            save_tasks()
            return True
    return False


def remove_task(task_id: str) -> bool:
    """Remove a scheduled task"""
    global _scheduled_tasks
    original_len = len(_scheduled_tasks)
    _scheduled_tasks = [t for t in _scheduled_tasks if t.task_id != task_id]
    
    if len(_scheduled_tasks) < original_len:
        save_tasks()
        return True
    return False


def list_tasks() -> list:
    """List all scheduled tasks"""
    return [t.to_dict() for t in _scheduled_tasks]


class Scheduler:
    """Scheduler runner"""
    def __init__(self, task_callback: Callable):
        """
        Initialize scheduler
        
        Args:
            task_callback: Function to call when executing task
                          Signature: callback(action: str, parameters: dict) -> dict
        """
        self.task_callback = task_callback
        self.running = False
        self.thread = None
    
    def setup_schedules(self):
        """Setup all approved scheduled tasks"""
        schedule.clear()
        
        for task in _scheduled_tasks:
            if not task.approved:
                continue
            
            # Parse schedule spec and create schedule
            # Simple implementation - can be extended
            spec = task.schedule_spec.lower()
            
            def make_job(t=task):
                """Create job closure"""
                return lambda: self.execute_task(t)
            
            if "every monday" in spec and "09:00" in spec:
                schedule.every().monday.at("09:00").do(make_job())
            elif "every day" in spec and "10:00" in spec:
                schedule.every().day.at("10:00").do(make_job())
            # Add more schedule patterns as needed
    
    def execute_task(self, task: ScheduledTask):
        """Execute a scheduled task"""
        print(f"[SCHEDULER] Executing task: {task.description}")
        
        try:
            result = self.task_callback(task.action, task.parameters)
            print(f"[SCHEDULER] Task result: {result}")
        except Exception as e:
            print(f"[SCHEDULER] Task failed: {e}")
    
    def run(self):
        """Run scheduler loop"""
        self.running = True
        self.setup_schedules()
        
        while self.running:
            schedule.run_pending()
            time.sleep(1)
    
    def start(self):
        """Start scheduler in background thread"""
        if self.thread and self.thread.is_alive():
            return
        
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()
        print("[SCHEDULER] Started")
    
    def stop(self):
        """Stop scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        print("[SCHEDULER] Stopped")


if __name__ == "__main__":
    # Test scheduler
    def test_callback(action, parameters):
        print(f"Executing {action} with {parameters}")
        return {"success": True}
    
    scheduler = Scheduler(test_callback)
    
    # Create a task
    task = create_scheduled_task(
        description="Daily reminder",
        schedule_spec="every day at 10:00",
        action="send_reminder",
        parameters={"message": "Daily standup"}
    )
    print(f"Created task: {task.task_id}")
    
    # Approve it
    approve_task(task.task_id)
    print("Task approved")
    
    # List tasks
    print(f"Scheduled tasks: {list_tasks()}")
