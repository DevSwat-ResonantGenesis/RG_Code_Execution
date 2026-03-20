# Code Executor - Handles safe code execution in Docker sandbox

import asyncio
import subprocess
import tempfile
import os
import shutil
import json
import logging
from typing import Optional, Dict, Any, Tuple
from .config import settings

logger = logging.getLogger(__name__)

class CodeExecutor:
    """Executes code in isolated Docker sandbox environment."""
    
    LANGUAGE_CONFIGS = {
        "python": {
            "extension": ".py",
            "command": ["python3", "-u"],
            "image": "python:3.11-alpine",
            "workdir": "/sandbox"
        },
        "javascript": {
            "extension": ".js",
            "command": ["node"],
            "image": "node:18-alpine",
            "workdir": "/sandbox"
        },
        "js": {
            "extension": ".js",
            "command": ["node"],
            "image": "node:18-alpine",
            "workdir": "/sandbox"
        },
        "jsx": {
            "extension": ".jsx",
            "command": ["node"],
            "image": "node:18-alpine",
            "workdir": "/sandbox"
        },
        "typescript": {
            "extension": ".ts",
            "command": ["npx", "ts-node"],
            "image": "node:18-alpine",
            "workdir": "/sandbox"
        },
        "tsx": {
            "extension": ".tsx",
            "command": ["npx", "ts-node"],
            "image": "node:18-alpine",
            "workdir": "/sandbox"
        },
        "bash": {
            "extension": ".sh",
            "command": ["sh"],
            "image": "alpine:3.19",
            "workdir": "/sandbox"
        },
        "shell": {
            "extension": ".sh",
            "command": ["sh"],
            "image": "alpine:3.19",
            "workdir": "/sandbox"
        }
    }
    
    def __init__(self):
        self.active_containers = {}
    
    async def _create_sandbox_container(
        self,
        code: str,
        language: str,
        timeout: int,
        session_id: str
    ) -> Tuple[str, str]:
        """Create isolated Docker container for code execution."""
        config = self.LANGUAGE_CONFIGS[language]
        
        # Create temp directory for code
        temp_dir = tempfile.mkdtemp(prefix=f"code_exec_{session_id}_", dir="/tmp/rg_code_exec")
        code_file = os.path.join(temp_dir, f"main{config['extension']}")
        
        with open(code_file, 'w') as f:
            f.write(code)
        os.chmod(code_file, 0o644)
        os.chmod(temp_dir, 0o755)
        
        # Build secure Docker command
        docker_cmd = [
            "docker", "run",
            "-d",
            "--rm",
            f"--name=code_exec_{session_id}",
            
            # Resource limits
            "--memory=256m",
            "--memory-swap=256m",
            "--cpus=0.5",
            "--pids-limit=50",
            
            # Security
            "--security-opt=no-new-privileges",
            "--cap-drop=ALL",
            "--user=nobody",
            "--network=none",
            
            # Filesystem
            "--read-only",
            "--tmpfs=/tmp:rw,noexec,nosuid,size=10m",
            f"--workdir={config['workdir']}",
            f"-v={temp_dir}:{config['workdir']}:ro",
            
            config["image"],
            "sleep",
            str(timeout + 5)
        ]
        
        logger.info(f"Creating sandbox container for session {session_id}")
        
        proc = await asyncio.create_subprocess_exec(
            *docker_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise RuntimeError(f"Failed to create container: {stderr.decode()}")
        
        container_id = stdout.decode().strip()
        self.active_containers[session_id] = container_id
        
        return container_id, temp_dir
    
    async def _execute_in_container(
        self,
        container_id: str,
        language: str,
        timeout: int,
        inputs: Optional[list] = None
    ) -> Dict[str, Any]:
        """Execute code inside the container."""
        config = self.LANGUAGE_CONFIGS[language]
        
        exec_cmd = [
            "docker", "exec",
            "-i",  # Interactive for stdin
            container_id,
        ] + config["command"] + [f"{config['workdir']}/main{config['extension']}"]
        
        logger.info(f"Executing code in container {container_id[:12]}")
        
        proc = await asyncio.create_subprocess_exec(
            *exec_cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        # Prepare input
        stdin_data = None
        if inputs:
            stdin_data = '\n'.join(str(i) for i in inputs).encode()
        
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(input=stdin_data),
                timeout=timeout
            )
            
            return {
                "success": proc.returncode == 0,
                "output": stdout.decode('utf-8', errors='replace')[:settings.MAX_OUTPUT_SIZE],
                "error": stderr.decode('utf-8', errors='replace')[:settings.MAX_OUTPUT_SIZE] if stderr else None,
                "exit_code": proc.returncode
            }
            
        except asyncio.TimeoutError:
            # Kill container on timeout
            await asyncio.create_subprocess_exec(
                "docker", "kill", container_id,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            return {
                "success": False,
                "output": "",
                "error": f"Execution timed out after {timeout} seconds",
                "exit_code": -1
            }
    
    async def _cleanup_container(self, container_id: str, temp_dir: str, session_id: str) -> None:
        """Clean up container and temp files."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "docker", "stop", "-t", "2", container_id,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            
            self.active_containers.pop(session_id, None)
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            logger.info(f"Cleaned up container {container_id[:12]}")
        except Exception as e:
            logger.warning(f"Cleanup failed for {container_id[:12]}: {e}")
    
    async def execute(
        self,
        code: str,
        language: str,
        inputs: Optional[list] = None,
        timeout: Optional[int] = None,
        cwd: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute code in isolated Docker sandbox."""
        
        if language not in self.LANGUAGE_CONFIGS:
            return {
                "success": False,
                "output": "",
                "error": f"Unsupported language: {language}. Supported: {list(self.LANGUAGE_CONFIGS.keys())}",
                "exit_code": 1
            }
        
        timeout = timeout or settings.EXECUTION_TIMEOUT
        session_id = os.urandom(8).hex()
        container_id = None
        temp_dir = None
        
        try:
            # Create isolated container
            container_id, temp_dir = await self._create_sandbox_container(
                code, language, timeout, session_id
            )
            
            # Execute code in container
            result = await self._execute_in_container(
                container_id, language, timeout, inputs
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Sandbox execution failed: {e}")
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "exit_code": 1
            }
        finally:
            # Always cleanup
            if container_id and temp_dir:
                await self._cleanup_container(container_id, temp_dir, session_id)


class TerminalExecutor:
    """Executes terminal commands."""
    
    async def execute(
        self,
        command: str,
        cwd: Optional[str] = None,
        timeout: Optional[int] = None,
        env: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Execute terminal command and return output."""
        
        timeout = timeout or settings.EXECUTION_TIMEOUT
        work_dir = cwd or os.path.expanduser("~")
        
        # Merge environment
        exec_env = os.environ.copy()
        if env:
            exec_env.update(env)
        
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=work_dir,
                env=exec_env
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
                
                return {
                    "success": process.returncode == 0,
                    "stdout": stdout.decode('utf-8', errors='replace')[:settings.MAX_OUTPUT_SIZE],
                    "stderr": stderr.decode('utf-8', errors='replace')[:settings.MAX_OUTPUT_SIZE],
                    "exit_code": process.returncode
                }
                
            except asyncio.TimeoutError:
                process.kill()
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": f"Command timed out after {timeout} seconds",
                    "exit_code": -1
                }
                
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "exit_code": 1
            }


# Global instances
code_executor = CodeExecutor()
terminal_executor = TerminalExecutor()
