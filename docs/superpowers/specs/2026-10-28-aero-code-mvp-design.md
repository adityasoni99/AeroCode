# Aero-Code (ProofLoop) MVP — Design Specification

- **Date:** 2026-10-28
- **Project:** Aero-Code (ProofLoop) Hackathon MVP
- **Target Track:** Coding and Agentic Engineering (Nebius × NVIDIA Global AI Hackathon)
- **Bonus Track:** Best Use of Tavily ($3,000)
- **Status:** Approved Design Spec

> **Historical design with current implementation notes (November 2, 2026).**
> The original intent is retained; the current reference is
> [README](../../../README.md), [ROADMAP](../../../ROADMAP.md), and
> [the submission guide](../../HACKATHON_SUBMISSIONS.md).
> `v0.2.6-verified` passed 110 tests with Docker and Chromium, with one Windows
> symlink privilege skip. Demo inference/search/PR results are fixtures, not proof
> of live sponsor usage; Evidence Reports are not cryptographically signed.

---

## 1. Goal & Product Positioning

Aero-Code is an autonomous software engineering agent built to solve the developer trust problem in AI-generated code. Rather than treating an LLM-generated patch as proof of correctness, Aero-Code executes **ProofLoop**: a bounded, deterministic workflow that reproduces the bug, researches documentation via Tavily, writes a minimal fix with Nemotron, validates repository and test immutability through Git Guard, executes tests in an isolated sandbox, and delivers a verifiable Evidence Report with a draft GitHub Pull Request.

---

## 2. Hackathon Compliance Matrix

| Requirement | Implementation in Aero-Code |
| :--- | :--- |
| **Track** | Coding and Agentic Engineering |
| **Runtime Inference Endpoint** | Nebius Token Factory (`https://api.tokenfactory.nebius.com/v1/`) |
| **Foundation Model** | `nvidia/Nemotron-3.5-Lightning` (Default) & `nvidia/Nemotron-3-Ultra-550b-a55b` (Escalation) |
| **Tavily Integration** | Dynamic, traceback-driven API searches with citations attached to PR |
| **License** | Apache-2.0 open-source license |
| **Sandbox Execution** | Isolated ephemeral workspace with strict 45-second timeout and credential stripping |
| **Video Demo Target** | Under 3 minutes showing live agent reasoning, Tavily lookup, sandbox run, and Evidence Report |

---

## 3. System Architecture & Modular Package Layout

Aero-Code is structured as an enterprise-grade, clean Python package with strict single-responsibility modules:

```text
aero-code/
├── aero_code/                   # Core Python package
│   ├── __init__.py
│   ├── config.py                # Environment & settings (Pydantic BaseSettings)
│   ├── state.py                 # ProofLoopState, Event bus & state transition model
│   ├── schemas/                 # Strict Pydantic v2 schemas
│   │   ├── __init__.py
│   │   ├── issues.py            # Issue & traceback models
│   │   ├── patch.py             # Patch proposal & AST diff models
│   │   ├── research.py          # Tavily search query & citation schemas
│   │   └── report.py            # EvidenceReport & audit log schemas
│   ├── agents/                  # Domain Agents
│   │   ├── __init__.py
│   │   ├── investigator.py      # Traceback parser & code root-cause locator
│   │   ├── researcher.py        # Tavily search caller & doc citation extractor
│   │   └── patch_engineer.py    # Nemotron patch & regression test generator
│   ├── verifier/                # Independent Trust & Verification Engine
│   │   ├── __init__.py
│   │   ├── git_guard.py         # Immutability policy & baseline test diff validator
│   │   ├── report_generator.py  # Markdown & JSON evidence report compiler
│   │   └── sandbox/             # Pluggable execution adapters
│   │       ├── base.py          # Abstract SandboxAdapter protocol
│   │       ├── subprocess.py    # Local isolated runner (tempdir, strict timeout)
│   │       └── docker.py        # Docker container runner (when Docker is active)
│   ├── llm/                     # Nebius Token Factory & NVIDIA Nemotron Client
│   │   ├── __init__.py
│   │   ├── client.py            # OpenAI SDK client pointing to Nebius Token Factory
│   │   └── prompts.py           # Structured system prompts & few-shot examples
│   ├── tools/                   # External APIs & Integrations
│   │   ├── __init__.py
│   │   ├── tavily_client.py     # Live Tavily SDK wrapper + fallback fixture cache
│   │   └── github_client.py     # GitHub REST API client for draft PR creation
│   ├── orchestrator/            # Deterministic ProofLoop Engine
│   │   ├── __init__.py
│   │   └── loop.py              # Bounded state machine with retry budget & rollback
│   ├── web/                     # Live Web Dashboard for Demos
│   │   ├── __init__.py
│   │   ├── server.py            # FastAPI server with Server-Sent Events (SSE)
│   │   └── static/              # Modern dark-mode single-page UI
│   └── cli.py                   # Rich CLI interface (`aero-code run ...`)
├── benchmarks/                  # Hackathon evaluation benchmarks
│   ├── cases/                   # Real-world seeded Python bug cases
│   └── evaluate.py              # Benchmark runner measuring reproduction & repair rate
├── tests/                       # Unit & integration tests for Aero-Code itself
│   ├── test_git_guard.py
│   ├── test_tavily_search.py
│   ├── test_state_machine.py
│   └── test_sandbox_runner.py
├── pyproject.toml               # Poetry/Hatch/Pip modern packaging
├── README.md                    # Hackathon documentation, architecture diagrams, video link
├── LICENSE                      # Apache-2.0 (hackathon requirement)
└── .env.example                 # NEBIUS_API_KEY, TAVILY_API_KEY, GITHUB_TOKEN
```

---

## 4. Deterministic State Machine & Double-Verification Rule

### 4.1 ProofLoop States
1. `INTAKE`: Ingests the bug report, traceback, and environment details.
2. `INVESTIGATE`: Parses the stack trace, identifies the failing symbol, and locates the implicated source files.
3. `RESEARCH`: Queries Tavily using dynamic package/version/error keywords and extracts official documentation citations.
4. `REPRODUCE_BASELINE`: Generates an isolated regression test (`tests/test_*_regression.py`) and executes it in the clean sandbox. It **must fail** to prove the bug is reproduced.
5. `GENERATE_PATCH`: Queries `nvidia/Nemotron-3.5-Lightning` on Nebius Token Factory with code context and Tavily citations to produce a minimal code patch.
6. `GIT_GUARD`: Analyzes the unified diff. If any existing test file in `tests/` or configuration file (`pyproject.toml`, etc.) is modified, the patch is rejected immediately.
7. `SANDBOX_EXECUTE`: Applies the patch in an ephemeral sandbox and executes `pytest`.
   - If tests fail and retry count $< 3$, error stderr is sent back to the Patch Engineer (escalating to `nvidia/Nemotron-3-Ultra-550b-a55b` on tough retries).
   - If tests pass, verify that all baseline tests also passed.
8. `EVIDENCE_REPORT`: Compiles structured JSON and Markdown evidence records.
9. `PUBLISH_PR`: Generates a GitHub draft PR with the verified fix and embedded Evidence Report.

### 4.2 The Double-Verification Rule
- **Condition 1 (Non-Vacuous Regression Test):** The new test must fail on unpatched
  code with pytest exit code 1. Collection errors, timeout, missing tests, and
  infrastructure failure do not establish reproduction.
- **Condition 2 (Bug Resolution):** New regression test MUST PASS on the patched codebase (exit code $= 0$).
- **Condition 3 (Zero Regressions):** 100% of baseline test suites must pass on the patched codebase.
- **Condition 4 (Baseline Test Immutability):** Zero modifications allowed to existing test files.

---

## 5. Live & Demo Dual-Engine Mode

To guarantee 100% demo reliability:
- **Live Mode (`--mode live`):** Configure Nebius/Tavily keys and a trusted,
  prebuilt Docker image. The current client falls back to fixtures without
  Nebius credentials; that does not constitute live inference.
- **Demo Mode (`--mode demo`, default):** Deterministic local fixtures for
  `pydantic_v2_migration`, `requests_timeout_kwarg`, and `paypal_webhook_signature`.
  Real pytest runs still take time; no live model/search claims should be made.

---

## 6. User Interfaces: Rich CLI & Embedded Web Dashboard

### 6.1 Rich CLI
- Built with Python `rich`.
- Animated live spinners, step status badges, unified color-coded diff views, and clean tabular evidence summaries.
- Entry commands:
  - `python -m aero_code.cli run --case pydantic_v2_migration --web`
  - `python -m aero_code.cli run --case pydantic_v2_migration --mode live`
  - `python -m aero_code.cli evaluate`

### 6.2 Embedded Web Dashboard
- Served locally by FastAPI on `http://127.0.0.1:8000`.
- Sleek, dark-mode visual interface with glassmorphism and real-time Server-Sent Events (SSE) updates.
- Real-time components:
  1. **ProofLoop Pipeline Stepper:** Visual progression cards for each state.
  2. **Live Activity Stream:** Real-time terminal output and agent reasoning steps.
  3. **Tavily Citations Panel:** Live search queries, documentation excerpts, and clickable source links.
  4. **Code Diff Viewer:** Side-by-side / unified diff viewer showing modified code.
  5. **Verification Audit Card:** Double-Verification results, execution timing, and Draft PR preview.

---

## 7. Sandbox Execution & Security

- **Subprocess Sandbox Adapter:** Creates an ephemeral directory via `tempfile.TemporaryDirectory()`, copies target files, strips all environment secrets (`NEBIUS_API_KEY`, `TAVILY_API_KEY`, `GITHUB_TOKEN`), and executes `pytest` using `subprocess.run` with a 45-second timeout.
- **Docker Sandbox Adapter:** CLI-based disposable Linux containers, 2 CPUs,
  2 GiB RAM, no additional swap/network, non-root execution, and a shared deadline
  capped at 60 seconds. Build the dependency image beforehand; verification never pulls it.
- Demo mode retains subprocess execution; live mode is Docker-first with
  explicitly enabled unavailable-only host fallback. See README for limits and exclusions.
- **Resource Limits:** Subprocess timeout kill switch prevents infinite loops or hanging tests.

---

## 8. Benchmark Evaluation Suite

Located in `benchmarks/`:
- `benchmarks/cases/pydantic_v2_migration/`: Deprecated `parse_obj` usage; a new
  regression test promotes the deprecation warning to an error and validates `model_validate`.
- `benchmarks/cases/requests_timeout_kwarg/`: Missing timeout; regression checks
  the actual HTTP call's bounded timeout without making an external request.
- `benchmarks/cases/paypal_webhook_signature/`: Missing/empty transmission header
  handling in a local fixture, not cryptographic signature validation.
- `benchmarks/evaluate.py`: Automated runner calculating:
  - Baseline Reproduction Rate (%)
  - Verified Repair Rate (%)
  - False Success Catch Rate (Target: 100%)

---

## 9. Testing & Quality Verification

Unit tests covering all core components:
1. `tests/test_git_guard.py`: Asserts Git Guard rejects test alterations and unauthorized file edits.
2. `tests/test_state_machine.py`: Asserts ProofLoop follows valid state transitions and respects retry caps.
3. `tests/test_tavily_search.py`: Asserts dynamic query synthesis and citation parsing.
4. `tests/test_sandbox_runner.py`: Asserts execution isolation, timeouts, and secret stripping.
