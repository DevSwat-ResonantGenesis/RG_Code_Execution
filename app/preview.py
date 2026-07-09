# Preview Server Manager - Handles dev server for live preview

import asyncio
import os
import signal
from typing import Optional, Dict, Any
from .config import settings

class PreviewManager:
    """Manages preview dev servers for projects."""
    
    def __init__(self):
        self.active_previews: Dict[str, Dict[str, Any]] = {}
        self._port_counter = settings.PREVIEW_PORT_RANGE_START
    
    def _resolve_project_path(self, project_path: str) -> str:
        """Refuse to serve/run anything outside the sandbox root."""
        root = settings.SANDBOX_ROOT
        os.makedirs(root, exist_ok=True)
        candidate = os.path.realpath(project_path)
        if candidate != root and not candidate.startswith(root + os.sep):
            raise ValueError(f"project_path must resolve under the sandbox root ({root})")
        if not os.path.isdir(candidate):
            raise ValueError(f"project_path does not exist: {candidate}")
        return candidate

    def _get_next_port(self) -> int:
        """Get next available port."""
        port = self._port_counter
        self._port_counter += 1
        if self._port_counter > settings.PREVIEW_PORT_RANGE_END:
            self._port_counter = settings.PREVIEW_PORT_RANGE_START
        return port
    
    async def start_preview(
        self,
        project_id: str,
        project_path: str,
        command: Optional[str] = None,
        port: Optional[int] = None
    ) -> Dict[str, Any]:
        """Start a preview server for a project.

        NOTE: this still spawns the dev-server process directly on this
        container's host process (unlike CodeExecutor/TerminalExecutor,
        which now run inside Docker sandboxes) — preview servers need to
        bind a real port the gateway can reach, and this service doesn't
        yet have the allowlisted-network sandbox that would require (the
        same Phase-3-style gap RG_Terminal_Sandbox's own design docs flag
        as not yet built). This is a known remaining risk, not fully fixed
        here. The path check below at least stops arbitrary host-path
        traversal via project_path — auth (see security.py) is the primary
        mitigation for this endpoint today.
        """
        try:
            project_path = self._resolve_project_path(project_path)
        except ValueError as e:
            return {"success": False, "error": str(e), "preview_url": None, "port": port, "process_id": None}

        # Stop existing preview if any
        if project_id in self.active_previews:
            await self.stop_preview(project_id)

        port = port or self._get_next_port()
        
        # Detect project type and default command
        if not command:
            command = self._detect_start_command(project_path, port)
        else:
            command = command.replace("{port}", str(port))
        
        try:
            # Start the dev server
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=project_path,
                preexec_fn=os.setsid  # Create new process group
            )
            
            # Store preview info
            self.active_previews[project_id] = {
                "process": process,
                "port": port,
                "command": command,
                "project_path": project_path
            }
            
            # Wait a bit for server to start
            await asyncio.sleep(2)
            
            # Check if process is still running
            if process.returncode is not None:
                stderr = await process.stderr.read()
                return {
                    "success": False,
                    "error": f"Server failed to start: {stderr.decode()}",
                    "preview_url": None,
                    "port": port,
                    "process_id": None
                }
            
            return {
                "success": True,
                "preview_url": f"http://localhost:{port}",
                "port": port,
                "process_id": str(process.pid)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "preview_url": None,
                "port": port,
                "process_id": None
            }
    
    async def stop_preview(self, project_id: str) -> Dict[str, Any]:
        """Stop a preview server."""
        
        if project_id not in self.active_previews:
            return {
                "success": False,
                "message": f"No active preview for project {project_id}"
            }
        
        preview = self.active_previews[project_id]
        process = preview["process"]
        
        try:
            # Kill the process group
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            await asyncio.sleep(0.5)
            
            # Force kill if still running
            if process.returncode is None:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            
            del self.active_previews[project_id]
            
            return {
                "success": True,
                "message": f"Preview stopped for project {project_id}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": str(e)
            }
    
    def _detect_start_command(self, project_path: str, port: int) -> str:
        """Detect the appropriate start command based on project type."""
        
        # Check for package.json (Node.js project)
        if os.path.exists(os.path.join(project_path, "package.json")):
            # Check for common frameworks
            try:
                import json
                with open(os.path.join(project_path, "package.json")) as f:
                    pkg = json.load(f)
                    scripts = pkg.get("scripts", {})
                    
                    if "dev" in scripts:
                        return f"npm run dev -- --port {port}"
                    elif "start" in scripts:
                        return f"PORT={port} npm start"
            except:
                pass
            return f"npm start"
        
        # Check for Python project
        if os.path.exists(os.path.join(project_path, "requirements.txt")):
            if os.path.exists(os.path.join(project_path, "manage.py")):
                return f"python manage.py runserver 0.0.0.0:{port}"
            elif os.path.exists(os.path.join(project_path, "app.py")):
                return f"python app.py"
            return f"python -m http.server {port}"
        
        # Default: simple HTTP server
        return f"python -m http.server {port}"
    
    def get_active_previews(self) -> Dict[str, Any]:
        """Get all active previews."""
        return {
            pid: {
                "port": info["port"],
                "project_path": info["project_path"],
                "running": info["process"].returncode is None
            }
            for pid, info in self.active_previews.items()
        }


# Global instance
preview_manager = PreviewManager()
