# Code Execution Router

import logging
import httpx
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
from ..executor import code_executor

logger = logging.getLogger(__name__)
router = APIRouter()

# Billing service URL
BILLING_SERVICE_URL = "http://billing_service:8000"

# Credit costs from pricing.yaml
CREDIT_COSTS = {
    "code_execution_per_ms": 1.0,
    "min_code_execution": 100,
    "max_code_execution": 10000,
}

class CodeExecuteRequest(BaseModel):
    code: str
    language: str
    inputs: Optional[List[str]] = None
    timeout: Optional[int] = None

class CodeExecuteResponse(BaseModel):
    success: bool
    output: str
    error: Optional[str] = None
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
                    "reference_type": "code_execution",
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

@router.post("/execute", response_model=CodeExecuteResponse)
async def execute_code(request: CodeExecuteRequest, req: Request):
    """Execute code in sandbox and return output."""
    import time
    start_time = time.time()
    
    result = await code_executor.execute(
        code=request.code,
        language=request.language,
        inputs=request.inputs,
        timeout=request.timeout
    )
    
    # Calculate execution time and credits
    duration_ms = int((time.time() - start_time) * 1000)
    credits = max(
        CREDIT_COSTS["min_code_execution"],
        min(
            int(duration_ms * CREDIT_COSTS["code_execution_per_ms"]),
            CREDIT_COSTS["max_code_execution"],
        )
    )
    
    # Deduct credits if user_id is provided
    user_id = req.headers.get("x-user-id")
    if user_id:
        deduct_result = await deduct_credits(
            user_id=user_id,
            amount=credits,
            description=f"Code execution ({request.language}, {duration_ms}ms)"
        )
        logger.info(f"💳 Deducted {credits} credits for code execution")
        result["credits_deducted"] = credits
    
    return CodeExecuteResponse(**result)

@router.get("/languages")
async def get_supported_languages():
    """Get list of supported languages."""
    return {
        "languages": list(code_executor.LANGUAGE_CONFIGS.keys())
    }
