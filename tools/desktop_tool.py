"""
Desktop Tool
Safe file and application operations with whitelisting
"""

import os
import subprocess
from typing import List, Dict
from pathlib import Path
from config.settings import WHITELISTED_APPS, SAFE_DIRECTORIES


def validate_path(path: str) -> bool:
    """
    Validate that path is in safe directory
    
    Args:
        path: Path to validate
    
    Returns:
        True if path is safe
    """
    abs_path = os.path.abspath(path)
    
    for safe_dir in SAFE_DIRECTORIES:
        safe_dir_abs = os.path.abspath(safe_dir)
        if abs_path.startswith(safe_dir_abs):
            return True
    
    return False


def resolve_directory(directory: str) -> str:
    """
    Resolve common directory names to absolute paths
    
    Args:
        directory: Directory name (e.g., "Documents", "Downloads")
    
    Returns:
        Absolute path
    """
    home = os.path.expanduser("~")
    common_dirs = {
        "documents": os.path.join(home, "Documents"),
        "downloads": os.path.join(home, "Downloads"),
        "desktop": os.path.join(home, "Desktop"),
        "home": home,
    }
    
    dir_lower = directory.lower()
    
    # Check exact match first
    if dir_lower in common_dirs:
        return common_dirs[dir_lower]
        
    # Check if it starts with a common dir + separator
    for name, path in common_dirs.items():
        if dir_lower.startswith(name + os.sep) or dir_lower.startswith(name + "/"):
            # Replace the alias with actual path
            # Need to preserve the rest of the path case-insensitively from input?
            # Actually, just use length of alias
            # "downloads/folder" -> "C:/Users/.../Downloads" + "/folder"
            suffix = directory[len(name):]
            return os.path.join(path, suffix.lstrip("/\\"))
            
    # If already a path, return as-is
    return directory


def list_files(directory: str) -> Dict:
    """
    List files in directory
    
    Args:
        directory: Directory path or name
    
    Returns:
        Dict with success status and file list
    """
    try:
        dir_path = resolve_directory(directory)
        
        if not validate_path(dir_path):
            return {
                "success": False,
                "error": f"Access denied: {dir_path} is not in safe directories"
            }
        
        if not os.path.exists(dir_path):
            return {
                "success": False,
                "error": f"Directory not found: {dir_path}"
            }
        
        if not os.path.isdir(dir_path):
            return {
                "success": False,
                "error": f"Not a directory: {dir_path}"
            }
        
        files = []
        for item in os.listdir(dir_path):
            item_path = os.path.join(dir_path, item)
            is_dir = os.path.isdir(item_path)
            size = os.path.getsize(item_path) if not is_dir else 0
            
            files.append({
                "name": item,
                "type": "directory" if is_dir else "file",
                "size": size
            })
        
        return {
            "success": True,
            "directory": dir_path,
            "files": files,
            "count": len(files)
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def create_file(path: str, content: str) -> Dict:
    """
    Create file with content
    
    Args:
        path: File path
        content: File content
    
    Returns:
        Result dictionary
    """
    try:
        abs_path = os.path.abspath(path)
        
        if not validate_path(abs_path):
            return {
                "success": False,
                "error": f"Access denied: {abs_path} is not in safe directories"
            }
        
        # Create parent directory if needed
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {
            "success": True,
            "message": f"Created {abs_path}",
            "path": abs_path
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def create_directory(path: str) -> Dict:
    """
    Create a new directory
    
    Args:
        path: Directory path
    
    Returns:
        Result dictionary
    """
    try:
        # Resolve path (handle aliases like 'Downloads/folder')
        path = resolve_directory(path)
        abs_path = os.path.abspath(path)
        
        if not validate_path(abs_path):
            return {
                "success": False,
                "error": f"Access denied: {abs_path} is not in safe directories"
            }
        
        if os.path.exists(abs_path):
            return {
                "success": False,
                "error": f"Path already exists: {abs_path}"
            }
            
        os.makedirs(abs_path, exist_ok=True)
        
        return {
            "success": True,
            "message": f"Created directory {abs_path}",
            "path": abs_path
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

    """
    Delete file (requires approval)
    
    Args:
        path: File path
    
    Returns:
        Result dictionary
    """
    try:
        abs_path = os.path.abspath(path)
        
        if not validate_path(abs_path):
            return {
                "success": False,
                "error": f"Access denied: {abs_path} is not in safe directories"
            }
        
        if not os.path.exists(abs_path):
            return {
                "success": False,
                "error": f"File not found: {abs_path}"
            }
        
        if os.path.isdir(abs_path):
            return {
                "success": False,
                "error": "Cannot delete directories"
            }
        
        os.remove(abs_path)
        
        return {
            "success": True,
            "message": f"Deleted {abs_path}"
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def open_app(app_name: str) -> Dict:
    """
    Open whitelisted application
    
    Args:
        app_name: Application name
    
    Returns:
        Result dictionary
    """
    app_lower = app_name.lower()
    
    if app_lower not in [app.lower() for app in WHITELISTED_APPS]:
        return {
            "success": False,
            "error": f"Application '{app_name}' not whitelisted"
        }
    
    try:
        # Use Windows start command
        subprocess.Popen(["start", app_name], shell=True)
        
        return {
            "success": True,
            "message": f"Opened {app_name}"
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    # Test desktop tool
    print("Testing list_files:")
    result = list_files("Documents")
    print(f"Success: {result.get('success')}")
    if result.get('success'):
        print(f"Files: {result.get('count')}")
    else:
        print(f"Error: {result.get('error')}")
