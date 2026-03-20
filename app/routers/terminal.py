# Terminal Execution Router

import logging
import httpx
import time
from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional, Dict
from ..executor import terminal_executor

logger = logging.getLogger(__name__)
router = APIRouter()

BILLING_SERVICE_URL = "http://billing_service:8000"
CREDIT_COSTS = {
    "terminal_per_ms": 1.0,
    "min_terminal": 50,
    "max_terminal": 5000,
}

class TerminalExecuteRequest(BaseModel):
    command: str
    cwd: Optional[str] = None
    timeout: Optional[int] = None
    env: Optional[Dict[str, str]] = None

class TerminalExecuteResponse(BaseModel):
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    credits_deducted: Optional[int] = None

async def deduct_credits(user_id: str, amount: int, description: str) -> dict:
    """Deduct credits from user's balance via billing service."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BILLING_SERVICE_URL}/billing/credits/deduct",
                json={
                    "amount": amount,
                    "reference_type": "terminal_session",
                    "description": description,
                },
                headers={"X-User-Id": user_id},
                timeout=5.0,
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.warning(f"Credit deduction failed: {e}")
        return {"error": str(e)}

@router.post("/execute", response_model=TerminalExecuteResponse)
async def execute_terminal_command(request: TerminalExecuteRequest, req: Request):
    """Execute terminal command and return output."""
    start_time = time.time()
    
    result = await terminal_executor.execute(
        command=request.command,
        cwd=request.cwd,
        timeout=request.timeout,
        env=request.env
    )
    
    # Calculate credits based on duration
    duration_ms = int((time.time() - start_time) * 1000)
    credits = max(
        CREDIT_COSTS["min_terminal"],
        min(
            int(duration_ms * CREDIT_COSTS["terminal_per_ms"]),
            CREDIT_COSTS["max_terminal"],
        )
    )
    
    # Deduct credits if user_id provided
    user_id = req.headers.get("x-user-id")
    if user_id:
        await deduct_credits(user_id, credits, f"Terminal command ({duration_ms}ms)")
        logger.info(f"💳 Deducted {credits} credits for terminal execution")
        result["credits_deducted"] = credits
    
    return TerminalExecuteResponse(**result)
