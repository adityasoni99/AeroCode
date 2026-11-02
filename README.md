# Aero-Code (ProofLoop™)

> **Deterministic software engineering agent with reproducible test evidence.**

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](pyproject.toml)
[![ProofLoop Verified](https://img.shields.io/badge/ProofLoop-Double--Verified-emerald.svg)](aero_code/verifier/)

---

## ⚡ What is Aero-Code?

Modern LLM-based coding agents frequently fall victim to **hallucination, vacuous tests, test suite corruption, and broken builds**.

**Aero-Code** addresses this with **ProofLoop™**: a bounded state machine orchestrating specialized agents and independent test verification. A `VERIFIED` verdict requires:
1. An isolated regression test **MUST FAIL** on the unpatched codebase (confirming bug reproduction).
2. The regression test **MUST PASS** on the patched codebase (confirming bug resolution).
3. 100% of the baseline test suite **MUST REMAIN GREEN** (zero regressions).
4. **Git Guard** accepts the patch without protected test/configuration edits.

Evidence is structured JSON/Markdown, not cryptographically signed proof.
Demo mode uses deterministic fixtures and a mock PR record when no GitHub token
is configured; it does not establish live API usage or publish a real patch branch.
Live GitHub publication is not yet validated end to end.

---

## 🏗️ ProofLoop™ Architecture

```mermaid
flowchart TD
    Issue[Issue / Bug Report] --> Intake[1. Intake Agent]
    Intake --> Investigate[2. Investigator Agent]
    Investigate --> Research[3. Tavily Contextual Researcher]
    Research --> Repro[4. Baseline Suite Check]
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

    subgraph "Tavily AI Search"
        Research
    end
```

---

## 🌟 Key Innovations

### 1. Nebius Token Factory & NVIDIA Nemotron Integration
- **Primary Model:** `nvidia/Nemotron-3.5-Lightning`, configurable through settings.
- **Escalation Model:** On verification failure or Git Guard rejection, retries use `nvidia/Nemotron-3-Ultra-550b-a55b`.
- Standard OpenAI API compatibility via Nebius Token Factory base URL (`https://api.tokenfactory.nebius.com/v1/`).

### 2. Tavily Contextual Research
Aero-Code dynamically synthesizes precision search queries from stack traces and dependency manifests:
- Uses the reported package/version and failing symbol to construct research queries.
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
- Three independently routed demo presets, visible errors, overlapping-run rejection,
  replayable SSE snapshots, polling recovery, and mobile/keyboard support.

---

## 📊 Benchmark Suite & Evaluation Results

Aero-Code includes three seeded fixtures. The results below were verified locally
with deterministic demo patches, using both subprocess and Docker adapters;
they are not a measurement of live LLM repair performance:

| Benchmark Case ID | Target Package | Error Category | Reproduction Rate | Repair Rate | Double-Verification Rate |
| :--- | :--- | :--- | :---: | :---: | :---: |
| `pydantic_v2_migration` | `pydantic 2.6.1` | API Deprecation / Migration | **100%** | **100%** | **100% (VERIFIED)** |
| `requests_timeout_kwarg` | `requests 2.31.0` | Missing Parameter / Socket Hang | **100%** | **100%** | **100% (VERIFIED)** |
| `paypal_webhook_signature` | PayPal-style local fixture | Missing/empty transmission headers | **100%** | **100%** | **100% (VERIFIED)** |
| **Suite Total** | - | - | **100%** | **100%** | **100% (VERIFIED)** |

Run the evaluation suite anytime via:
```bash
aero-code evaluate
```

---

## 🚀 Quickstart Guide

### 1. Clone & Install
```powershell
git clone https://github.com/adityasoni99/AeroCode.git
cd AeroCode

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install package with dependencies
pip install -e .
```

On Linux/macOS, activate with `source .venv/bin/activate` instead.

### 2. Configure Environment (Optional for Demo Mode)
```powershell
Copy-Item .env.example .env
# Fill in your NEBIUS_API_KEY and TAVILY_API_KEY for live execution
```

*Note: Aero-Code defaults to `mode="demo"` out of the box with reproducible offline fixtures, allowing zero-credential evaluation.*

The settings fields use unprefixed environment names: `MODE`, `TIMEOUT_SECONDS`,
`MAX_RETRIES`, `PRIMARY_MODEL`, and `ESCALATION_MODEL`. `--mode live` selects live
CLI execution; configure API keys and a prebuilt Docker image first. Without
Nebius credentials, the current client uses demo fixtures even in live mode,
so do not present such a run as live inference. The dashboard form selects demo mode.

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
Install the development extra for pytest:

```powershell
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\pytest tests\ -v
```

The default suite includes mocked Docker lifecycle tests and requires no Docker daemon.
Real-container checks are opt-in (see below).

### Verified Release: `v0.2.6-verified`

On November 2, 2026, the full Windows suite with Chromium and
`AERO_CODE_DOCKER_INTEGRATION=1` completed with **110 passed, 1 skipped**.
All 18 browser tests and all three real-container integration checks passed.
The sole skip requires Windows symlink privileges; the Windows junction test passed.
No sandbox containers remained after the three Docker-backed ProofLoop benchmarks.
These are local validation results, not a claim that remote CI has already run.

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

On Windows, installing Docker Desktop/WSL or enabling Virtual Machine Platform
can require a restart. If Docker cannot start, finish that restart before enabling
integration tests; CLI installation alone does not provide a working daemon.

### Dashboard Flow Tests

Install the optional Chromium browser test runtime:

```powershell
.\.venv\Scripts\python -m pip install -e ".[dev,browser]"
.\.venv\Scripts\python -m playwright install chromium
.\.venv\Scripts\pytest tests\test_dashboard_browser.py tests\test_web_flows.py tests\test_proofloop_verification.py -v
```

Browser tests start and stop their own local server. They cover all three presets,
required fields, keyboard submission, live pipeline/matrix/diff/citation updates,
repeat runs, reloads, disconnected SSE recovery, HTTP/network errors, and layout
at 320, 375, 768, 1024, and 1440 pixels. Backend tests cover run exclusion,
explicit runtime errors, replayable thread-safe SSE, and genuine bug reproduction.
CI installs Chromium and runs these tests; without the optional runtime, browser
tests skip while the backend suite remains available.

The dashboard presets target their corresponding bundled repository, not the
current project. Demo repairs use deterministic fixtures with no external API
calls. The PayPal fixture validates required header handling only; it is **not**
a cryptographic signature-verification implementation. Failed reproduction,
collection errors, and sandbox failures cannot produce a VERIFIED verdict.

## Releases & Hackathon Submissions

- `v0.1.0-mvp`: original foundation snapshot.
- `v0.2.0-paypal`: historical PayPal-style fixture/guardrail snapshot.
- `v0.2.5-agentic`: Docker adapter snapshot; does not contain the later UI fixes.
- `v0.2.6-verified`: validated Docker + dashboard fixes and corrected documentation.
- `v0.3.0-kiro` and `v0.4.0-codegeist`: future milestones, not available releases.

A tag does not prove entry eligibility or sponsor integration. See the
[submission sequence and checklist](docs/HACKATHON_SUBMISSIONS.md) for verified
event dates, reuse restrictions, remaining work, and publication steps.
[ROADMAP.md](ROADMAP.md) tracks engineering work separately from actual submissions.

---

## 📜 License

Licensed under the [Apache License, Version 2.0](LICENSE).
