# Aero-Code (ProofLoop™)

> **Deterministic Autonomous Software Engineering Agent with Cryptographically Auditable Verification Engine.**

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](pyproject.toml)
[![ProofLoop Verified](https://img.shields.io/badge/ProofLoop-Double--Verified-emerald.svg)](aero_code/verifier/)

---

## ⚡ What is Aero-Code?

Modern LLM-based coding agents frequently fall victim to **hallucination, vacuous tests, test suite corruption, and broken builds**.

**Aero-Code** solves this with **ProofLoop™**: a deterministic, self-correcting state machine orchestrating specialized agent roles paired with an immutable verification engine. Aero-Code will **never merge or propose a pull request without cryptographic-grade, double-verified evidence**:
1. An isolated regression test **MUST FAIL** on the unpatched codebase (confirming bug reproduction).
2. The regression test **MUST PASS** on the patched codebase (confirming bug resolution).
3. 100% of the baseline test suite **MUST REMAIN GREEN** (zero regressions).
4. **Git Guard** policy guarantees zero tampering with existing tests or configuration files.

---

## 🏗️ ProofLoop™ Architecture

```mermaid
flowchart TD
    Issue[Issue / Bug Report] --> Intake[1. Intake Agent]
    Intake --> Investigate[2. Investigator Agent]
    Investigate --> Research[3. Tavily Contextual Researcher]
    Research --> Repro[4. Repro Baseline Verification]
    Repro --> Patch[5. Patch Engineer (Nemotron)]
    Patch --> GitGuard{6. Git Guard Policy}
    GitGuard -- Policy Violation --> Retry[Escalate & Retry Budget]
    Retry --> Patch
    GitGuard -- Passed --> Sandbox[7. Isolated Sandbox Execution]
    Sandbox -- Test Failed --> Retry
    Sandbox -- Double-Verified --> Evidence[8. Evidence Report Generator]
    Evidence --> PR[9. Publish Pull Request]

    subgraph "Verification Engine"
        GitGuard
        Sandbox
        Evidence
    end

    subgraph "Nebius Token Factory"
        Patch
        Investigate
    end

    subgraph "Tavily AI Search ($3k Bonus)"
        Research
    end
```

---

## 🌟 Key Innovations

### 1. Nebius Token Factory & NVIDIA Nemotron Integration
- **Primary Model:** `nvidia/Nemotron-3-Nano-30b` for rapid root cause triage and unified diff proposal.
- **Escalation Model:** On test failure or Git Guard policy breach, the state machine automatically escalates to `nvidia/Nemotron-3-Ultra-550b` with contextual error feedback and higher reasoning depth.
- Standard OpenAI API compatibility via Nebius Token Factory base URL (`https://api.tokenfactory.nebius.com/v1/`).

### 2. Tavily Dynamic Contextual Research ($3,000 Bonus Track)
Aero-Code dynamically synthesizes precision search queries from stack traces and dependency manifests:
- Automatically parses exception types, failing module names, and package versions from `pyproject.toml` or `requirements.txt`.
- Queries Tavily API for exact migration guides, deprecation notes, and API changes.
- Cites documentation sources directly in the Pull Request body and Evidence Report.

### 3. Git Guard Policy Engine
- Protects baseline test suites (`tests/test_*.py`) from unauthorized agent edits.
- Protects project manifests (`pyproject.toml`, `setup.py`, CI workflows).
- Permits only new, isolated regression tests (`tests/test_*_regression.py`).

### 4. Real-Time Web Dashboard (FastAPI + SSE)
- Real-time Server-Sent Events (SSE) stream pipeline events from the `ProofLoopEventBus`.
- Interactive 9-phase stepper with live glow pulses.
- Real-time Double-Verification Matrix display.
- Integrated code diff viewer and live Tavily citation feed.

---

## 📊 Benchmark Suite & Evaluation Results

Aero-Code includes a curated seeded benchmark suite evaluated against real-world breaking changes:

| Benchmark Case ID | Target Package | Error Category | Reproduction Rate | Repair Rate | Double-Verification Rate |
| :--- | :--- | :--- | :---: | :---: | :---: |
| `pydantic_v2_migration` | `pydantic 2.6.1` | API Deprecation / Migration | **100%** | **100%** | **100% (VERIFIED)** |
| `requests_timeout_kwarg` | `requests 2.31.0` | Missing Parameter / Socket Hang | **100%** | **100%** | **100% (VERIFIED)** |
| **Suite Total** | - | - | **100%** | **100%** | **100% (VERIFIED)** |

Run the evaluation suite anytime via:
```bash
aero-code evaluate
```

---

## 🚀 Quickstart Guide

### 1. Clone & Install
```bash
git clone https://github.com/your-org/AeroCode.git
cd AeroCode

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install package with dependencies
pip install -e .
```

### 2. Configure Environment (Optional for Demo Mode)
```bash
cp .env.example .env
# Fill in your NEBIUS_API_KEY and TAVILY_API_KEY for live execution
```

*Note: Aero-Code defaults to `mode="demo"` out of the box with reproducible offline fixtures, allowing zero-credential evaluation.*

### 3. Run ProofLoop CLI with Web Dashboard
```bash
# Run pydantic migration case and open live Web UI
aero-code run --case pydantic_v2_migration --web
```

### 4. View Available Cases
```bash
aero-code cases
```

### 5. Launch Standalone Web Dashboard
```bash
aero-code web
# Opens browser at http://127.0.0.1:8000
```

---

## 🧪 Running Tests
```bash
pytest -v
```

The default suite includes mocked Docker lifecycle tests and requires no Docker daemon.
Real-container checks are opt-in (see below).

### Docker Sandbox (Live Mode)

Live ProofLoop runs use `DockerSandboxAdapter`; demo mode retains the local
subprocess adapter for reproducible, offline fixtures. Docker Desktop must be
running with Linux containers, or use a local Linux Docker daemon.

Build a trusted image **before** verification. This PowerShell example builds an
image for the bundled benchmarks without sending a repository build context:

```powershell
@'
FROM python:3.11-slim
RUN python -m pip install --no-cache-dir pytest pydantic requests
'@ | docker build --tag aero-code-sandbox:local -
```

For other repositories, build an image containing their dependencies and pytest,
then set `SANDBOX_IMAGE` in your environment or `.env`. Verification never pulls
images or installs packages, and an absent image is an explicit failure.

Every run stages a temporary repository copy, applies patches only to that copy,
and runs pytest in a disposable container with:

- 2 CPUs, 2 GiB RAM, no additional swap, and a 128-process limit.
- No network, no added capabilities, no privilege escalation, and an unprivileged user.
- A read-only root filesystem and staged-source mount; writable in-memory
  workspace (512 MiB) and temporary directory (64 MiB).
- A shared execution deadline capped at 60 seconds (shorter configured timeouts
  are respected), followed by force-removal with a separate 5-second cleanup limit.

Repository symlinks/junctions, `.env` files, version-control metadata, virtual environments,
and caches are excluded from both adapters' staged copies. Patch paths must stay
inside the workspace. Container environment variables come from the trusted image,
not the host. Credentials embedded in other repository files must be removed
before verification; these exclusions are not a general secret scanner.

Docker-unavailable runs fail closed by default. Setting
`SANDBOX_ALLOW_SUBPROCESS_FALLBACK=true` explicitly permits host subprocess
execution **only** when the CLI/daemon is unavailable, with a warning that
container isolation is lost. Failed tests, missing images, runtime failures,
timeouts, and cleanup failures never trigger fallback. Subprocess mode is for
trusted code, not zero-trust isolation.

Run the full suite on Windows:

```powershell
.\.venv\Scripts\pytest tests\ -v
```

Enable real-container integration tests after building the image:

```powershell
$env:AERO_CODE_DOCKER_INTEGRATION = "1"
$env:AERO_CODE_DOCKER_IMAGE = "aero-code-sandbox:local"
.\.venv\Scripts\pytest tests\test_docker_sandbox.py -v
```

These opt-in checks verify filesystem/network isolation, CPU/memory limits,
patch execution, failing tests, and hard timeouts. Without the opt-in flag they
are skipped, keeping CI independent of Docker.

---

## 📜 License

Licensed under the [Apache License, Version 2.0](LICENSE).
