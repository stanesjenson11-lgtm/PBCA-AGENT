"""
System Resource Monitor Tool
Check CPU, RAM, disk, and battery stats locally.
"""

import logging

logger = logging.getLogger(__name__)


class SystemTool:
    """Monitor system resources — CPU, RAM, disk, battery."""

    def execute(self, entities: dict) -> dict:
        """
        Execute system monitoring action.

        Args:
            entities: May contain 'metric' (cpu, ram, disk, battery, all).

        Returns:
            Result dict with system stats.
        """
        try:
            import psutil
        except ImportError:
            return {"success": False, "error": "psutil not installed. Run: pip install psutil"}

        metric = entities.get("metric", "all").lower()

        try:
            stats = {}

            if metric in ("cpu", "all"):
                stats["cpu_percent"] = psutil.cpu_percent(interval=1)
                stats["cpu_count"] = psutil.cpu_count()
                stats["cpu_freq"] = f"{psutil.cpu_freq().current:.0f} MHz" if psutil.cpu_freq() else "N/A"

            if metric in ("ram", "memory", "all"):
                mem = psutil.virtual_memory()
                stats["ram_total_gb"] = f"{mem.total / (1024**3):.1f} GB"
                stats["ram_used_gb"] = f"{mem.used / (1024**3):.1f} GB"
                stats["ram_percent"] = f"{mem.percent}%"
                stats["ram_available_gb"] = f"{mem.available / (1024**3):.1f} GB"

            if metric in ("disk", "all"):
                disk = psutil.disk_usage("/")
                stats["disk_total_gb"] = f"{disk.total / (1024**3):.1f} GB"
                stats["disk_used_gb"] = f"{disk.used / (1024**3):.1f} GB"
                stats["disk_free_gb"] = f"{disk.free / (1024**3):.1f} GB"
                stats["disk_percent"] = f"{disk.percent}%"

            if metric in ("battery", "all"):
                battery = psutil.sensors_battery()
                if battery:
                    stats["battery_percent"] = f"{battery.percent}%"
                    stats["battery_plugged"] = battery.power_plugged
                    secs = battery.secsleft
                    if secs > 0:
                        stats["battery_time_left"] = f"{secs // 3600}h {(secs % 3600) // 60}m"
                    else:
                        stats["battery_time_left"] = "Charging" if battery.power_plugged else "Unknown"
                else:
                    stats["battery"] = "No battery detected (desktop)"

            # Build formatted message
            message = self._format_stats(stats)

            return {
                "success": True,
                "stats": stats,
                "message": message
            }

        except Exception as e:
            logger.error(f"[SYSTEM] Error: {e}")
            return {"success": False, "error": f"Failed to get system stats: {e}"}

    def _format_stats(self, stats: dict) -> str:
        """Format stats into a readable string."""
        lines = ["📊 System Stats:"]
        for key, value in stats.items():
            label = key.replace("_", " ").title()
            lines.append(f"  • {label}: {value}")
        return "\n".join(lines)

    def get_capabilities(self) -> list:
        """Return supported actions for causal_graph.py."""
        return ["check_system"]


# Module-level instance
_tool = SystemTool()


def check_system(entities: dict = None) -> dict:
    """Check system stats."""
    return _tool.execute(entities or {})
