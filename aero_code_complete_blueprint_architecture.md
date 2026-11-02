# Aero-Code (ProofLoop)
## Technical Architecture & Hackathon Execution Master Plan

> **Historical blueprint; current status checked November 2, 2026.**
> Implemented: Python state machine, demo fixtures, Git Guard, Docker/subprocess
> adapters, SSE dashboard, and CLI. `v0.2.6-verified` recorded 110 passing tests
> with real Docker and Chromium, plus one Windows symlink privilege skip.
> OpenShell, Nebius remote jobs, MCP, Forge, and real end-to-end PR publication
> are not completed integrations. Live inference/search have not been validated
> by the offline test results. Reports are reproducible JSON/Markdown, not
> cryptographically signed artifacts.
> Use [README](README.md), [ROADMAP](ROADMAP.md), and
> [the submission guide](docs/HACKATHON_SUBMISSIONS.md) as current references.
> The Nebius event page currently says the event has ended; this blueprint is
> not evidence of registration, eligibility, or a completed submission.

> **Hackathon:** Nebius × NVIDIA Global AI Hackathon  
> **Primary Track:** Coding and Agentic Engineering  
> **Potential Bonus:** Best Use of Tavily ($3,000)  
> **Tagline:** The autonomous engineering agent that proves its fixes.  
> **Architecture Principle:** Deterministic orchestration, isolated execution, independently verified patches, and evidence-backed results.  
> **Implementation Priority:** Build one reliable end-to-end repair workflow before adding optional frameworks or infrastructure.

---

## Table of Contents
1. [Executive Summary](#1-executive-summary)
2. [Product Positioning](#2-product-positioning)
3. [Hackathon Compliance](#3-hackathon-compliance)
4. [Technical Stack](#4-technical-stack)
5. [ProofLoop Architecture](#5-proofloop-architecture)
6. [Agent Responsibilities](#6-agent-responsibilities)
7. [Tavily Research Strategy](#7-tavily-research-strategy)
8. [Git Guard and Verification](#8-git-guard-and-verification)
9. [Sandbox Security](#9-sandbox-security)
10. [NVIDIA OpenShell Integration](#10-nvidia-openshell-integration)
11. [Nebius and Nemotron Integration](#11-nebius-and-nemotron-integration)
12. [Repository Structure](#12-repository-structure)
13. [Evidence Report](#13-evidence-report)
14. [Benchmarking and Evaluation](#14-benchmarking-and-evaluation)
15. [IDE and Development Workflow](#15-ide-and-development-workflow)
16. [Implementation Roadmap](#16-implementation-roadmap)
17. [Budget and Resource Strategy](#17-budget-and-resource-strategy)
18. [Demonstration Video](#18-demonstration-video)
19. [Risks and Mitigations](#19-risks-and-mitigations)
20. [Acceptance Criteria](#20-acceptance-criteria)
21. [Final Submission Checklist](#21-final-submission-checklist)
22. [Final Product Vision](#22-final-product-vision)

---

## 1. Executive Summary

Aero-Code is an autonomous software engineering agent designed to bridge the gap between AI-generated code and developer trust.

Conventional coding agents can produce plausible patches that fail to address the underlying bug, overlook edge cases, or accidentally weaken tests. Aero-Code addresses this problem through **ProofLoop**, a bounded, deterministic workflow that investigates bugs, researches relevant documentation, generates patches, executes tests in isolated environments, and produces evidence-backed results.

### Core Platform Integrations
- **Nebius Token Factory:** Runtime inference backbone via OpenAI-compatible endpoints.
- **NVIDIA Nemotron:** Open-source foundation models for code reasoning, diagnosis, patch generation, and regression test design.
- **Tavily Search API:** Live contextual research for API documentation, breaking changes, and upstream release notes.
- **Deterministic Orchestration:** Lightweight state engine (or PocketFlow) to ensure reliable state transitions.
- **Isolated Execution Engine:** Docker containers initially, with NVIDIA OpenShell evaluated as a security runtime layer.
- **Nebius AI Cloud:** Serverless Jobs / DevPods for remote sandbox execution.
- **GitHub REST/GraphQL API:** Automated issue reading and reviewable draft Pull Request generation.

### The Core Differentiator
Aero-Code does not treat generated code as proof of correctness. It attempts to reproduce the original failure, establishes whether the proposed regression test detects the bug, validates the patch against immutable baseline tests, and records verifiable evidence. When verification fails, the agent attempts a bounded retry; if verification is impossible, it reports an inconclusive result instead of claiming false success.

> **Product Promise:** Research the bug. Reproduce the failure. Fix the code. Challenge the fix. Show the evidence.

---

## 2. Product Positioning

- **Product Name:** Aero-Code: ProofLoop
- **One-Line Pitch:** An autonomous engineering agent that researches bugs, repairs code, verifies its changes in an isolated environment, and generates an evidence-backed pull request.

### The Problem
AI coding agents generate code quickly, but developers waste significant time verifying whether those changes:
- Address the actual root cause rather than hiding symptoms.
- Reproduce and resolve the original failure.
- Preserve existing application behavior.
- Introduce hidden regressions.
- Depend on deprecated or incorrect API assumptions.
- Pass tests for valid reasons rather than due to deleted or weakened assertions.

### The Solution
ProofLoop introduces an explicit verification loop around code generation:
1. Investigate the issue and repository context.
2. Research relevant API or dependency documentation using Tavily.
3. Establish a reproducible baseline failure.
4. Generate a minimal patch and isolated regression test.
5. Enforce repository and test immutability policies.
6. Run tests in an isolated sandbox environment.
7. Retry a limited number of times using stderr feedback.
8. Generate a structured evidence report and draft pull request.

---

## 3. Hackathon Compliance

### Official References
- **Rules:** [Nebius Global AI Hackathon Rules](https://nebiusglobalaihackathon.devpost.com/rules)
- **FAQ:** [Nebius Global AI Hackathon FAQs](https://nebiusglobalaihackathon.devpost.com/details/faqs)

### Mandatory Compliance Checklist
- [ ] Verify an open event and register for an eligible track before submitting.
- [ ] Record live runtime inference calls to **Nebius Token Factory** (`https://api.tokenfactory.nebius.com/v1/`).
- [ ] Demonstrate an eligible **NVIDIA open-source model** (`nvidia/Nemotron-3.5-Lightning` or `nvidia/Nemotron-3-Ultra-550b-a55b`).
- [x] Provide a functional application and open-source public GitHub repository with an approved license (`MIT` or `Apache-2.0`).
- [ ] Demonstrate dynamic **Tavily API** calls to establish sponsor usage; cached demo citations do not qualify on their own.
- [x] Include comprehensive setup instructions and document all Nebius/NVIDIA technical integrations in the `README.md`.
- [ ] Submit a public YouTube video under the event's required length, clearly distinguishing live APIs from fixtures.

---

## 4. Technical Stack

| Layer | Recommended Technology | Purpose & Hackathon Requirement |
| :--- | :--- | :--- |
| **Runtime Inference** | **Nebius Token Factory** | Required model inference endpoint using standard OpenAI client |
| **Primary LLM** | `nvidia/Nemotron-3.5-Lightning` | Default model for triage, tool-calling, and reasoning |
| **Escalation LLM** | `nvidia/Nemotron-3-Ultra-550b-a55b` | Complex code reasoning and difficult patch generation |
| **Live Research** | **Tavily Python SDK** | Traceback-driven documentation and release-note search |
| **Orchestration** | Custom Python State Machine / PocketFlow | Explicit deterministic workflow transitions and retry limits |
| **Patch Validation** | **Git Guard** (Python AST / Git Diff) | Enforces immutability on baseline test suites |
| **Sandbox Engine** | **Docker Container / Nebius Serverless Jobs** | Safe, isolated execution of untrusted code and tests |
| **Security Layer** | **NVIDIA OpenShell** (Optional Spike) | Policy-enforced runtime sandbox and file/network boundary |
| **Integrations** | GitHub REST API | Issue intake and draft Pull Request publishing |
| **Data Schemas** | Pydantic v2 | Rigorous tool call and evidence report schema validation |

---

## 5. ProofLoop Architecture

```text
                  GitHub Issue / Bug Report
                             │
                             ▼
                   1. Investigator Agent
                             │
                             ▼
                2. Contextual Researcher Agent
                      (Tavily + Nemotron)
                             │
                             ▼
                   3. Baseline Reproducer
                             │
                             ▼
                    4. Patch Engineer
                (Patch + Regression Test)
                             │
                             ▼
                     5. Git Guard
                (Policy + Diff Validation)
                             │
                    ┌────────┴────────┐
                 Reject            Accept
                    │                 │
                    ▼                 ▼
               Stop / Log    6. Sandbox Runner
                                      │
                           ┌──────────┴──────────┐
                        Failure                Pass
                           │                     │
                           ▼                     ▼
                     Bounded Retry        Evidence Report
                           │                     │
                           ▼                     ▼
                      Revalidate          Draft GitHub PR
                           │
                  Retry Budget Exhausted
                           │
                           ▼
                      Inconclusive
```

---

## 6. Agent Responsibilities

### 6.1 Investigator
- **Inputs:** Issue description, stack trace, repository files, dependency specs.
- **Outputs:** Suspected root cause, implicated symbols, target source files.

### 6.2 Contextual Researcher
- **Inputs:** Traceback exception, package name, installed version.
- **Outputs:** Verified API specs, breaking changes, and upstream documentation retrieved via Tavily.

### 6.3 Patch Engineer
- **Inputs:** Triage findings, research context, source files.
- **Outputs:** Minimal code patch diff and isolated regression test (`tests/test_*_regression.py`).

### 6.4 Git Guard
- **Inputs:** Proposed patch diff.
- **Outputs:** Pass/Fail policy validation enforcing test suite immutability.

### 6.5 Sandbox Verifier
- **Inputs:** Clean repository workspace + approved patch.
- **Outputs:** Execution stdout/stderr, pytest exit codes, baseline vs. patched test results.

---

## 7. Tavily Research Strategy

To qualify for the **$3,000 Tavily Bonus**, search calls must be triggered dynamically by real error tracebacks:

1. **Parse Traceback:** Extract exception type (e.g., `AttributeError`, `ImportError`), library name, and line context.
2. **Read Manifest:** Extract exact package version from `pyproject.toml` or `requirements.txt`.
3. **Targeted Query:** Formulate search string: `"[Library] [Version] [Symbol/Error] API changes OR migration guide"`.
4. **Citation Extraction:** Pass relevant documentation excerpts to Nemotron and append source URLs directly into the final Evidence Report.

---

## 8. Git Guard and Verification

The **Git Guard** engine enforces strict repository policies before code execution:

1. **Immutable Baseline:** The original repository's `tests/` directory is read-only.
2. **Isolated Tests:** The agent may only add *new* test files matching `tests/test_*_regression.py`.
3. **Config Protection:** Changes to `pyproject.toml`, `setup.py`, or CI files are strictly rejected.
4. **Double Verification Rule:**
   - New regression test **MUST FAIL** on the original unpatched commit.
   - New regression test **MUST PASS** on the patched commit.
   - 100% of existing baseline tests **MUST PASS** without regressions.

---

## 9. Sandbox Security

Repository code is untrusted code. Aero-Code executes code inside isolated sandboxes:
- Non-root user execution inside disposable Docker containers.
- Resource constraints: 2 vCPUs, 2GB RAM max, strict 60-second timeouts.
- Network disabled during pytest execution.
- Docker does not inherit host API keys. Trusted images and repository files
  still require secret review. The demo subprocess adapter strips named keys
  but does not provide container isolation.

---

## 10. NVIDIA OpenShell Integration

Aero-Code evaluates **NVIDIA OpenShell** as an optional security runtime layer to enforce filesystem policy and network access controls for agent tools.

```text
               Aero-Code Orchestration Engine
                             │
                             ▼
                     Execution Adapter
                             │
                 ┌───────────┼───────────┐
                 ▼           ▼           ▼
             Docker      OpenShell    Nebius Jobs
            (Default)   (Optional)    (Optional)
```

---

## 11. Nebius and Nemotron Integration

Aero-Code communicates with Nebius Token Factory using the standard OpenAI Python SDK:

```python
import os
from openai import OpenAI

nebius_client = OpenAI(
    base_url=os.environ.get("NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1/"),
    api_key=os.environ["NEBIUS_API_KEY"],
)

# Supported NVIDIA Models on Nebius Token Factory
NEMOTRON_LIGHTNING = "nvidia/Nemotron-3.5-Lightning"
NEMOTRON_ULTRA = "nvidia/Nemotron-3-Ultra-550b-a55b"
```

---

## 12. Repository Structure

The following is the original proposed layout, not the implemented file tree.
The current package lives under `aero_code/` with `llm/`, `agents/`, `verifier/`,
`orchestrator/`, `tools/`, `schemas/`, and `web/`; benchmarks live under `benchmarks/`.
There is no implemented OpenShell/remote jobs runner or committed sandbox Dockerfile.

```text
aero-code/
├── app/
│   ├── main.py                  # CLI & Orchestration entry point
│   ├── state_machine.py         # Deterministic ProofLoop state engine
│   ├── schemas.py               # Pydantic data models
│   └── github_integration.py    # GitHub REST API client
├── agents/
│   ├── investigator.py          # Bug triage agent
│   ├── researcher.py            # Tavily context research agent
│   └── patch_engineer.py        # Fix & regression test generator
├── verifier/
│   ├── git_guard.py             # Diff validation & test immutability policy
│   ├── sandbox_runner.py        # Docker / Nebius Serverless Jobs executor
│   └── report_generator.py      # Markdown & JSON evidence report builder
├── tools/
│   ├── nebius_client.py         # Nebius Token Factory SDK client
│   └── tavily_client.py         # Contextual search wrapper
├── sandbox/
│   ├── Dockerfile.sandbox       # Safe execution container
│   └── runner.py                # In-sandbox test harness
├── benchmarks/
│   ├── cases/                   # Seeded open-source Python bugs
│   └── evaluate.py              # Benchmark runner
├── tests/                       # Aero-Code unit tests
├── .env.example
├── README.md
├── LICENSE                      # Apache-2.0 or MIT
├── AERO_CODE_BLUEPRINT.md
└── pyproject.toml
```

---

## 13. Evidence Report

Every run returns an EvidenceReport model with JSON/Markdown rendering support.
The following is a conceptual payload, not the current schema. Without a token,
the PR client returns a mock record; automated live branch publication is not validated.

```json
{
  "run_id": "aero-proof-20261026-001",
  "repository": "owner/repo",
  "baseline_commit": "a1b2c3d4",
  "patch_commit": "e5f6g7h8",
  "model_used": "nvidia/Nemotron-3.5-Lightning",
  "tavily_citations": [
    "https://docs.example.com/api/v2-changes"
  ],
  "verification_results": {
    "baseline_regression_test": "FAILED_AS_EXPECTED",
    "patched_regression_test": "PASSED",
    "immutable_test_suite": "PASSED_100_PERCENT"
  },
  "verdict": "VERIFIED"
}
```

---

## 14. Benchmarking and Evaluation

Aero-Code currently includes three seeded cases in `benchmarks/`; 10–20 cases
and comparative evaluation against other coding agents remain future goals:

- **Reproduction Rate:** % of cases where the bug baseline failure is reproduced.
- **Verified Repair Rate:** % of cases where the patch passes all Git Guard and sandbox checks.
- **False-Success Rate:** % of invalid or test-deleting patches caught and rejected (Target: 0%).

---

## 15. IDE and Development Workflow

- **Recommended IDE:** Cursor or VS Code.
- **Development Rule:** The IDE AI is used solely for writing application code. The runtime execution of Aero-Code itself strictly invokes **Nebius Token Factory** and **NVIDIA Nemotron** APIs to ensure 100% hackathon rule compliance.

---

## 16. Implementation Roadmap

```text
[ Phase 1 ] Setup Nebius & Tavily API Clients ──────────────► (Day 1)
[ Phase 2 ] Build Local Docker Sandbox & Git Guard Engine ────► (Day 2)
[ Phase 3 ] Implement ProofLoop State Machine & Retries ──────► (Day 3)
[ Phase 4 ] Add Nebius Cloud / OpenShell & Web Dashboard ─────► (Day 4)
[ Phase 5 ] Run Benchmarks, Record Demo & Submit ─────────────► (Day 5)
```

---

## 17. Budget and Resource Strategy

- **Inference & Search:** Funded via Nebius Builder Program free credits.
- **Compute Sandboxes:** Ran locally via Docker Desktop at $0 cost; remote sandbox hosted via Nebius Serverless Jobs / DevPods preview.

---

## 18. Demonstration Video

A 2.5-minute YouTube video demonstrating:
1. **0:00–0:30:** Bug intake from a failing GitHub issue.
2. **0:30–1:00:** Contextual documentation lookup via Tavily API.
3. **1:00–1:45:** Code patch generation via Nebius Nemotron and sandbox verification failure.
4. **1:45–2:15:** Self-correction loop, passing test execution, and Git Guard checks.
5. **2:15–2:30:** Verified evidence report and draft GitHub Pull Request creation.

---

## 19. Risks and Mitigations

- **Risk:** Remote sandbox latency or access restrictions.
  - *Mitigation:* Use the local Docker adapter; host subprocess fallback is explicit
    and allowed only when Docker is unavailable, not after failed container runs.
- **Risk:** Agent deleting or bypassing existing tests.
  - *Mitigation:* Git Guard engine strictly rejects any modification to existing test files.

---

## 20. Acceptance Criteria

- [ ] Live Nebius Token Factory inference validated with credentials.
- [ ] Live Tavily searches validated with credentials.
- [x] Regression failure on unpatched code is required before a VERIFIED verdict.
- [x] Existing test files are protected by Git Guard.
- [ ] A real published patch branch/PR contains a complete Evidence Report.

---

## 21. Final Submission Checklist

- [ ] Public GitHub repository created with `MIT` or `Apache-2.0` LICENSE.
- [ ] Working runtime calls to Nebius Token Factory verified.
- [ ] README includes setup instructions and architecture diagram.
- [ ] YouTube video (< 3 minutes) uploaded and added to Devpost.
- [ ] Devpost submission form completed before deadline.

---

## 22. Final Product Vision

Aero-Code transforms AI code generation from speculative drafts into trustworthy, self-verifying engineering work—giving developers complete confidence in every pull request.