# Internal-service authentication for the Code Execution microservice.
#
# This service has /var/run/docker.sock mounted (required for its own
# Docker-sandboxed execution) and is reachable by every other container on
# app-network. Without this check, any other container reachable on that
# network — including one compromised via an unrelated bug elsewhere in the
# fleet — could run arbitrary shell commands here and pivot to full host
# root via the mounted socket. Every route in this service must depend on
# `require_internal_key`, matching the pattern already used by
# RG_Terminal_Sandbox (x-internal-service-key header, fails closed except
# in explicit development mode).

from fastapi import HTTPException, Request

from .config import settings


def require_internal_key(request: Request) -> None:
    internal_key = request.headers.get("x-internal-service-key")
    if internal_key != settings.INTERNAL_SERVICE_KEY and settings.ENVIRONMENT != "development":
        raise HTTPException(status_code=403, detail="Internal endpoint - access denied")
