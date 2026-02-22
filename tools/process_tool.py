"""
Process Management Tool
List running processes and kill specific ones (with approval).
"""

import logging

logger = logging.getLogger(__name__)

# Processes that should NEVER be killed (safety whitelist)
PROTECTED_PROCESSES = {
    "system", "system idle process", "csrss.exe", "wininit.exe",
    "services.exe", "lsass.exe", "svchost.exe", "smss.exe",
    "explorer.exe", "winlogon.exe", "dwm.exe", "conhost.exe"
}


class ProcessTool:
    """List and manage running processes."""

    def execute(self, entities: dict) -> dict:
        """
        Execute process action.

        Args:
            entities: {
                'action': 'list' or 'kill',
                'name': str (process name for kill),
                'pid': int (process ID for kill),
                'filter': str (optional name filter for list)
            }
        """
        try:
            import psutil
        except ImportError:
            return {"success": False, "error": "psutil not installed. Run: pip install psutil"}

        action = entities.get("action", "list").lower()

        if action == "list":
            return self._list_processes(entities)
        elif action == "kill":
            return self._kill_process(entities)
        else:
            return {"success": False, "error": f"Unknown action: {action}"}

    def _list_processes(self, entities: dict) -> dict:
        """List running processes."""
        import psutil

        name_filter = entities.get("filter", entities.get("name", "")).lower()
        processes = []

        for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info"]):
            try:
                info = proc.info
                if name_filter and name_filter not in info["name"].lower():
                    continue
                processes.append({
                    "pid": info["pid"],
                    "name": info["name"],
                    "cpu": f"{info.get('cpu_percent', 0):.1f}%",
                    "memory_mb": f"{info['memory_info'].rss / (1024**2):.1f} MB" if info.get("memory_info") else "N/A"
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Sort by memory usage (descending)
        processes.sort(key=lambda p: float(p["memory_mb"].replace(" MB", "")) if "MB" in p["memory_mb"] else 0, reverse=True)

        # Limit to top 20
        top = processes[:20]
        total = len(processes)

        lines = [f"🔧 Processes ({total} total, top 20):"]
        for p in top:
            lines.append(f"  [{p['pid']}] {p['name']} — CPU: {p['cpu']}, RAM: {p['memory_mb']}")

        return {
            "success": True,
            "processes": top,
            "count": total,
            "message": "\n".join(lines)
        }

    def _kill_process(self, entities: dict) -> dict:
        """Kill a process by name or PID."""
        import psutil

        name = entities.get("name", "").lower()
        pid = entities.get("pid")

        if not name and not pid:
            return {"success": False, "error": "Specify process name or PID to kill."}

        # Safety check
        if name and name.lower() in PROTECTED_PROCESSES:
            return {"success": False, "error": f"⛔ Cannot kill protected system process: {name}"}

        killed = []
        try:
            for proc in psutil.process_iter(["pid", "name"]):
                try:
                    if pid and proc.info["pid"] == int(pid):
                        proc.terminate()
                        killed.append(f"{proc.info['name']} (PID {proc.info['pid']})")
                    elif name and name in proc.info["name"].lower():
                        if proc.info["name"].lower() in PROTECTED_PROCESSES:
                            continue
                        proc.terminate()
                        killed.append(f"{proc.info['name']} (PID {proc.info['pid']})")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            if killed:
                return {
                    "success": True,
                    "killed": killed,
                    "message": f"✅ Killed: {', '.join(killed)}"
                }
            else:
                return {"success": False, "error": f"No matching process found for '{name or pid}'."}

        except Exception as e:
            return {"success": False, "error": f"Failed to kill process: {e}"}

    def get_capabilities(self) -> list:
        return ["list_processes", "kill_process"]


_tool = ProcessTool()


def list_processes(entities: dict = None) -> dict:
    return _tool.execute({"action": "list", **(entities or {})})


def kill_process(entities: dict = None) -> dict:
    return _tool.execute({"action": "kill", **(entities or {})})
