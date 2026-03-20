# RG Code Execution

> **Part of the [ResonantGenesis](https://dev-swat.com) platform** — Isolated code execution, terminal commands, and preview server management.

[![Status: Production](https://img.shields.io/badge/Status-Production-brightgreen.svg)]()
[![Port: 8002](https://img.shields.io/badge/Port-8002-orange.svg)]()
[![License: RG Source Available](https://img.shields.io/badge/License-RG%20Source%20Available-blue.svg)](LICENSE.txt)

Provides sandboxed code execution for multiple languages, terminal command execution, and preview server management. Uses Docker-in-Docker for isolation.

## Features

- **Code execution** — Run code in isolated containers (Python, JavaScript, etc.)
- **Terminal commands** — Execute shell commands with timeout and resource limits
- **Preview servers** — Manage and proxy preview servers for web projects
- **Docker isolation** — Each execution runs in a fresh container

## Quick Start

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

## Deployment Status

- **Extracted from**: `genesis2026_production_backend/code_execution_service/`
- **Server path**: `/home/deploy/RG_Code_Execution`
- **Docker service**: `code_execution_service`
- **Volume mounts**: `/var/run/docker.sock`, `/tmp/rg_code_exec`

---
**Organization**: [DevSwat-ResonantGenesis](https://github.com/DevSwat-ResonantGenesis) | **Platform**: [dev-swat.com](https://dev-swat.com)
