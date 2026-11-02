# Aero-Code (ProofLoop) MVP Implementation Plan

> **Historical plan, not a current status report.** The original October 28
> instructions, expected failures, code samples, and unchecked steps are preserved
> as design history. Do not re-execute them against the implemented repository.
> As of November 2, 2026, `v0.2.6-verified` adds Docker and dashboard hardening:
> 110 tests passed with Docker/Chromium enabled, with one Windows symlink skip.
> See [README](../../../README.md), [ROADMAP](../../../ROADMAP.md), and
> [submission guidance](../../HACKATHON_SUBMISSIONS.md) for current behavior,
> commands, limitations, and event eligibility.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and verify the complete Aero-Code (ProofLoop) Hackathon MVP featuring deterministic multi-agent bug repair, live Tavily research, Nebius Token Factory inference with NVIDIA Nemotron, Git Guard test immutability verification, an isolated sandbox runner, a Rich CLI, and a real-time web dashboard for video demonstration.

**Architecture:** A clean modular Python package (`aero_code`) driven by an explicit state machine with an in-memory event bus. The pipeline reproduces bugs, retrieves documentation via Tavily, writes patches using Nemotron, enforces test immutability via Git Guard, validates fixes in an isolated tempdir sandbox, and broadcasts live progress over Server-Sent Events to a modern dark-mode dashboard.

**Tech Stack:** Python 3.11, Pydantic v2, FastAPI, Uvicorn, OpenAI SDK (configured for Nebius Token Factory), Tavily Python SDK, Rich, Pytest.

**Spec:** `docs/superpowers/specs/2026-10-28-aero-code-mvp-design.md`

## Global Constraints
- Python 3.11+
- Nebius Token Factory endpoint: `https://api.tokenfactory.nebius.com/v1/`
- Primary LLM: `nvidia/Nemotron-3.5-Lightning`
- Escalation LLM: `nvidia/Nemotron-3-Ultra-550b-a55b`
- All state, tool calls, and evidence reports strictly typed with Pydantic v2
- Baseline test files must remain strictly immutable (Git Guard policy)
- Double-Verification Rule: Regression test must fail on unpatched code and pass on patched code
- Sandbox runner must strip credentials (`NEBIUS_API_KEY`, `TAVILY_API_KEY`, `GITHUB_TOKEN`)
- High-fidelity demo mode with seeded benchmark cases must work offline without API keys

---

### Task 1: Project Scaffolding, Packaging & Pydantic Data Models

**Files:**
- Create: `pyproject.toml`
- Create: `aero_code/__init__.py`
- Create: `aero_code/config.py`
- Create: `aero_code/schemas/__init__.py`
- Create: `aero_code/schemas/issues.py`
- Create: `aero_code/schemas/patch.py`
- Create: `aero_code/schemas/research.py`
- Create: `aero_code/schemas/report.py`
- Create: `aero_code/state.py`
- Test: `tests/test_schemas_and_state.py`

**Interfaces:**
- Produces:
  - `Settings` in `aero_code/config.py`
  - `IssueReport`, `TracebackFrame` in `aero_code/schemas/issues.py`
  - `PatchProposal`, `FileDiff` in `aero_code/schemas/patch.py`
  - `TavilyCitation`, `ResearchResult` in `aero_code/schemas/research.py`
  - `EvidenceReport`, `VerificationVerdict` in `aero_code/schemas/report.py`
  - `ProofLoopState`, `ProofLoopEvent`, `ProofLoopEventBus` in `aero_code/state.py`

- [ ] **Step 1: Write the failing test for schemas, settings, and state machine models**

```python
# tests/test_schemas_and_state.py
import pytest
from aero_code.config import Settings
from aero_code.schemas.issues import IssueReport
from aero_code.schemas.patch import PatchProposal, FileDiff
from aero_code.schemas.research import ResearchResult, TavilyCitation
from aero_code.schemas.report import EvidenceReport, VerificationVerdict
from aero_code.state import ProofLoopState, ProofLoopPhase, ProofLoopEventBus

def test_settings_defaults():
    s = Settings()
    assert s.nebius_base_url == "https://api.tokenfactory.nebius.com/v1/"
    assert s.primary_model == "nvidia/Nemotron-3.5-Lightning"

def test_schemas_instantiation():
    issue = IssueReport(
        issue_id="ISSUE-101",
        title="Pydantic parse_obj deprecated",
        description="AttributeError when calling UserModel.parse_obj()",
        traceback="AttributeError: type object 'UserModel' has no attribute 'parse_obj'",
        target_package="pydantic",
        package_version="2.6.1"
    )
    assert issue.issue_id == "ISSUE-101"

    diff = FileDiff(file_path="app/models.py", old_content="UserModel.parse_obj()", new_content="UserModel.model_validate()")
    patch = PatchProposal(diffs=[diff], regression_test_code="def test_regression(): pass")
    assert len(patch.diffs) == 1

def test_event_bus():
    bus = ProofLoopEventBus()
    events = []
    bus.subscribe(lambda e: events.append(e))
    bus.publish("TEST_EVENT", {"detail": "hello"})
    assert len(events) == 1
    assert events[0].event_type == "TEST_EVENT"
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_schemas_and_state.py -v`
Expected: FAIL with ModuleNotFoundError: No module named 'aero_code'

- [ ] **Step 3: Write minimal implementation**
Write `pyproject.toml`, `aero_code/config.py`, `aero_code/schemas/*.py`, `aero_code/state.py`.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_schemas_and_state.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add pyproject.toml aero_code/ tests/test_schemas_and_state.py
git commit -m "feat: add project scaffolding, Pydantic schemas, and event bus"
```

---

### Task 2: Git Guard Policy & Test Immutability Verifier

**Files:**
- Create: `aero_code/verifier/__init__.py`
- Create: `aero_code/verifier/git_guard.py`
- Test: `tests/test_git_guard.py`

**Interfaces:**
- Consumes: `PatchProposal`, `FileDiff` from `aero_code.schemas.patch`
- Produces: `GitGuardResult` and `GitGuard.validate(patch: PatchProposal, baseline_test_files: set[str]) -> GitGuardResult`

- [ ] **Step 1: Write the failing test for Git Guard**

```python
# tests/test_git_guard.py
from aero_code.schemas.patch import PatchProposal, FileDiff
from aero_code.verifier.git_guard import GitGuard, GitGuardViolation

def test_git_guard_allows_valid_patch_and_new_regression_test():
    guard = GitGuard()
    patch = PatchProposal(
        diffs=[FileDiff(file_path="src/service.py", old_content="old", new_content="new")],
        regression_test_code="def test_fix_regression(): assert True",
        regression_test_file="tests/test_issue_101_regression.py"
    )
    result = guard.validate(patch, baseline_test_files={"tests/test_baseline.py"})
    assert result.is_valid is True
    assert len(result.violations) == 0

def test_git_guard_rejects_modification_of_existing_tests():
    guard = GitGuard()
    patch = PatchProposal(
        diffs=[
            FileDiff(file_path="tests/test_baseline.py", old_content="assert x == 1", new_content="assert True")
        ],
        regression_test_code="def test_fix_regression(): assert True",
        regression_test_file="tests/test_issue_101_regression.py"
    )
    result = guard.validate(patch, baseline_test_files={"tests/test_baseline.py"})
    assert result.is_valid is False
    assert any("immutable baseline test" in v.lower() for v in result.violations)

def test_git_guard_rejects_modification_of_build_configs():
    guard = GitGuard()
    patch = PatchProposal(
        diffs=[FileDiff(file_path="pyproject.toml", old_content="version = 1", new_content="version = 2")],
        regression_test_code="def test_fix_regression(): assert True"
    )
    result = guard.validate(patch, baseline_test_files=set())
    assert result.is_valid is False
    assert any("config file" in v.lower() for v in result.violations)
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_git_guard.py -v`
Expected: FAIL with ModuleNotFoundError: No module named 'aero_code.verifier'

- [ ] **Step 3: Write minimal Git Guard implementation**
Implement `aero_code/verifier/git_guard.py` enforcing:
- Reject any edit touching `tests/` except designated `tests/test_*_regression.py`
- Reject changes to protected configs: `pyproject.toml`, `setup.py`, `requirements.txt`, `.github/*`
- Require `regression_test_file` to match `tests/test_*_regression.py`

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_git_guard.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add aero_code/verifier/ tests/test_git_guard.py
git commit -m "feat: implement Git Guard immutability verifier"
```

---

### Task 3: Isolated Subprocess Sandbox Verifier

**Files:**
- Create: `aero_code/verifier/sandbox/__init__.py`
- Create: `aero_code/verifier/sandbox/base.py`
- Create: `aero_code/verifier/sandbox/subprocess.py`
- Create: `aero_code/verifier/sandbox/docker.py`
- Test: `tests/test_sandbox_runner.py`

**Interfaces:**
- Consumes: `PatchProposal`
- Produces: `SandboxExecutionResult` (exit_code, stdout, stderr, duration_ms, passed) and `SubprocessSandboxAdapter`

- [ ] **Step 1: Write the failing test for sandbox runner**

```python
# tests/test_sandbox_runner.py
import os
import tempfile
from pathlib import Path
from aero_code.verifier.sandbox.subprocess import SubprocessSandboxAdapter
from aero_code.schemas.patch import PatchProposal, FileDiff

def test_sandbox_copies_and_executes_pytest():
    with tempfile.TemporaryDirectory() as src_dir:
        src_path = Path(src_dir)
        (src_path / "src").mkdir()
        (src_path / "tests").mkdir()
        (src_path / "src" / "math_lib.py").write_text("def add(a, b): return a + b\n")
        (src_path / "tests" / "test_add.py").write_text("from src.math_lib import add\ndef test_add(): assert add(1, 2) == 3\n")

        adapter = SubprocessSandboxAdapter(timeout_seconds=15)
        res = adapter.run_test_suite(repo_root=str(src_path), test_target="tests/test_add.py")
        assert res.exit_code == 0
        assert res.passed is True

def test_sandbox_strips_api_keys():
    adapter = SubprocessSandboxAdapter(timeout_seconds=5)
    env = adapter._build_clean_env({"NEBIUS_API_KEY": "secret-key", "PATH": "some-path"})
    assert "NEBIUS_API_KEY" not in env
    assert "TAVILY_API_KEY" not in env
    assert "GITHUB_TOKEN" not in env
    assert "PATH" in env
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_sandbox_runner.py -v`
Expected: FAIL with ModuleNotFoundError: No module named 'aero_code.verifier.sandbox'

- [ ] **Step 3: Implement SubprocessSandboxAdapter and BaseSandboxAdapter**
In `aero_code/verifier/sandbox/base.py`, define `SandboxExecutionResult` and abstract `BaseSandboxAdapter`.
In `aero_code/verifier/sandbox/subprocess.py`, create ephemeral temp copy, apply patch diffs, execute `python -m pytest` with timeout and stripped environment.
In `aero_code/verifier/sandbox/docker.py`, create Docker fallback wrapper.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_sandbox_runner.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add aero_code/verifier/sandbox/ tests/test_sandbox_runner.py
git commit -m "feat: implement isolated subprocess sandbox adapter"
```

---

### Task 4: Nebius Token Factory Client & NVIDIA Nemotron Prompts

**Files:**
- Create: `aero_code/llm/__init__.py`
- Create: `aero_code/llm/client.py`
- Create: `aero_code/llm/prompts.py`
- Test: `tests/test_nebius_client.py`

**Interfaces:**
- Consumes: `Settings` from `aero_code.config`
- Produces: `NebiusNemotronClient.generate_patch(...)`, `NebiusNemotronClient.generate_investigation(...)`

- [ ] **Step 1: Write the failing test for Nebius client (with mock & live mode support)**

```python
# tests/test_nebius_client.py
from aero_code.llm.client import NebiusNemotronClient
from aero_code.config import Settings

def test_nebius_client_demo_mode():
    client = NebiusNemotronClient(mode="demo")
    resp = client.investigate(
        issue_title="Pydantic parse_obj error",
        traceback="AttributeError: 'UserModel' has no attribute 'parse_obj'"
    )
    assert resp.implicated_symbol == "parse_obj"
    assert "pydantic" in resp.root_cause.lower()

def test_nebius_client_escalation_model():
    client = NebiusNemotronClient(mode="demo")
    patch = client.generate_patch(
        issue_title="Pydantic parse_obj error",
        source_code="class UserModel:\n    pass",
        research_context="Use model_validate in Pydantic v2",
        escalate=True
    )
    assert patch.regression_test_code != ""
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_nebius_client.py -v`
Expected: FAIL with ModuleNotFoundError: No module named 'aero_code.llm'

- [ ] **Step 3: Implement Nebius Token Factory client & system prompts**
Implement `NebiusNemotronClient` using `openai.OpenAI(base_url="https://api.tokenfactory.nebius.com/v1/")`.
Support `mode="live"` when `NEBIUS_API_KEY` is present and `mode="demo"` for offline benchmark fallback.
Implement prompts in `aero_code/llm/prompts.py` tailored for `nvidia/Nemotron-3.5-Lightning` and `nvidia/Nemotron-3-Ultra-550b-a55b`.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_nebius_client.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add aero_code/llm/ tests/test_nebius_client.py
git commit -m "feat: implement Nebius Token Factory client for Nemotron models"
```

---

### Task 5: Tavily Contextual Research Client & Query Synthesis

**Files:**
- Create: `aero_code/tools/__init__.py`
- Create: `aero_code/tools/tavily_client.py`
- Create: `aero_code/agents/__init__.py`
- Create: `aero_code/agents/researcher.py`
- Test: `tests/test_tavily_search.py`

**Interfaces:**
- Consumes: `IssueReport` from `aero_code.schemas.issues`
- Produces: `ResearchResult` and `ResearcherAgent.research_issue(issue: IssueReport) -> ResearchResult`

- [ ] **Step 1: Write the failing test for dynamic Tavily research**

```python
# tests/test_tavily_search.py
from aero_code.tools.tavily_client import TavilySearchClient
from aero_code.agents.researcher import ResearcherAgent
from aero_code.schemas.issues import IssueReport

def test_dynamic_query_synthesis():
    agent = ResearcherAgent(tavily_client=TavilySearchClient(mode="demo"))
    query = agent.synthesize_query(
        package="pydantic",
        version="2.6.1",
        error="AttributeError: parse_obj"
    )
    assert "pydantic" in query
    assert "2.6.1" in query
    assert "parse_obj" in query

def test_research_execution_returns_citations():
    agent = ResearcherAgent(tavily_client=TavilySearchClient(mode="demo"))
    issue = IssueReport(
        issue_id="ISSUE-1",
        title="AttributeError in parse_obj",
        description="Calling parse_obj fails",
        traceback="AttributeError: type object 'UserModel' has no attribute 'parse_obj'",
        target_package="pydantic",
        package_version="2.6.1"
    )
    result = agent.research_issue(issue)
    assert len(result.citations) > 0
    assert result.citations[0].url.startswith("http")
    assert "model_validate" in result.summary.lower()
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_tavily_search.py -v`
Expected: FAIL with ModuleNotFoundError: No module named 'aero_code.tools.tavily_client'

- [ ] **Step 3: Implement Tavily client and ResearcherAgent**
Implement `TavilySearchClient` with dynamic search method and offline demo fixtures.
Implement `ResearcherAgent` to extract package, version, and error symbol from `IssueReport` and generate citations.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_tavily_search.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add aero_code/tools/tavily_client.py aero_code/agents/researcher.py tests/test_tavily_search.py
git commit -m "feat: implement dynamic Tavily research agent and citations"
```

---

### Task 6: Investigator & Patch Engineer Agents

**Files:**
- Create: `aero_code/agents/investigator.py`
- Create: `aero_code/agents/patch_engineer.py`
- Test: `tests/test_agents.py`

**Interfaces:**
- Consumes: `NebiusNemotronClient`, `IssueReport`, `ResearchResult`
- Produces: `InvestigationReport` from `investigator.py`, `PatchProposal` from `patch_engineer.py`

- [ ] **Step 1: Write the failing test for Investigator and Patch Engineer**

```python
# tests/test_agents.py
from aero_code.agents.investigator import InvestigatorAgent
from aero_code.agents.patch_engineer import PatchEngineerAgent
from aero_code.llm.client import NebiusNemotronClient
from aero_code.schemas.issues import IssueReport
from aero_code.schemas.research import ResearchResult, TavilyCitation

def test_investigator_extracts_root_cause():
    llm = NebiusNemotronClient(mode="demo")
    investigator = InvestigatorAgent(llm_client=llm)
    issue = IssueReport(
        issue_id="ISSUE-1",
        title="Pydantic parse_obj error",
        description="UserModel.parse_obj does not exist",
        traceback="AttributeError: 'UserModel' has no attribute 'parse_obj'",
        target_package="pydantic",
        package_version="2.6.1"
    )
    inv = investigator.analyze(issue)
    assert inv.implicated_symbol == "parse_obj"

def test_patch_engineer_synthesizes_patch_and_regression_test():
    llm = NebiusNemotronClient(mode="demo")
    engineer = PatchEngineerAgent(llm_client=llm)
    patch = engineer.create_patch(
        issue_title="Pydantic error",
        source_code="data = UserModel.parse_obj(payload)",
        research_context="Replaced with model_validate in Pydantic v2"
    )
    assert len(patch.diffs) > 0
    assert "def test_" in patch.regression_test_code
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_agents.py -v`
Expected: FAIL with ModuleNotFoundError: No module named 'aero_code.agents.investigator'

- [ ] **Step 3: Implement InvestigatorAgent and PatchEngineerAgent**
Implement `investigator.py` to parse tracebacks and pinpoint symbols.
Implement `patch_engineer.py` to prompt Nemotron for unified diffs and non-vacuous regression tests.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_agents.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add aero_code/agents/ tests/test_agents.py
git commit -m "feat: implement Investigator and Patch Engineer agents"
```

---

### Task 7: Evidence Report Generator & GitHub Integration

**Files:**
- Create: `aero_code/verifier/report_generator.py`
- Create: `aero_code/tools/github_client.py`
- Test: `tests/test_report_generator.py`

**Interfaces:**
- Consumes: `ProofLoopState`, `VerificationVerdict`
- Produces: `EvidenceReport`, Markdown report string, and `GitHubClient.create_draft_pr(...)`

- [ ] **Step 1: Write the failing test for Report Generator**

```python
# tests/test_report_generator.py
from aero_code.verifier.report_generator import EvidenceReportGenerator
from aero_code.schemas.report import EvidenceReport, VerificationVerdict
from aero_code.schemas.research import TavilyCitation
from aero_code.schemas.patch import PatchProposal, FileDiff

def test_evidence_report_markdown_and_json():
    gen = EvidenceReportGenerator()
    report = gen.generate(
        run_id="aero-proof-20261028-001",
        repository="owner/repo",
        baseline_commit="a1b2c3d4",
        patch_commit="e5f6g7h8",
        model_used="nvidia/Nemotron-3.5-Lightning",
        citations=[TavilyCitation(title="Pydantic Docs", url="https://docs.pydantic.dev/migration", snippet="Use model_validate")],
        patch=PatchProposal(diffs=[FileDiff(file_path="app.py", old_content="old", new_content="new")]),
        baseline_test_passed=False,
        patched_test_passed=True,
        baseline_suite_passed=True,
        git_guard_passed=True,
        verdict=VerificationVerdict.VERIFIED
    )
    assert report.verdict == VerificationVerdict.VERIFIED
    md = gen.to_markdown(report)
    assert "Double-Verification Matrix" in md
    assert "https://docs.pydantic.dev/migration" in md
    assert "VERIFIED" in md
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_report_generator.py -v`
Expected: FAIL with ModuleNotFoundError: No module named 'aero_code.verifier.report_generator'

- [ ] **Step 3: Implement ReportGenerator and GitHubClient**
Implement `report_generator.py` to format structured JSON and GitHub PR-ready Markdown tables.
Implement `github_client.py` to create draft pull requests (with mock mode when `GITHUB_TOKEN` is unset).

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_report_generator.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add aero_code/verifier/report_generator.py aero_code/tools/github_client.py tests/test_report_generator.py
git commit -m "feat: implement Evidence Report generator and GitHub PR client"
```

---

### Task 8: ProofLoop Deterministic State Machine Orchestrator

**Files:**
- Create: `aero_code/orchestrator/__init__.py`
- Create: `aero_code/orchestrator/loop.py`
- Test: `tests/test_state_machine.py`

**Interfaces:**
- Consumes: All agents, verifier, sandbox, event bus, and schemas
- Produces: `ProofLoopOrchestrator.run(issue: IssueReport, repo_dir: str) -> EvidenceReport`

- [ ] **Step 1: Write the failing test for the ProofLoop state machine**

```python
# tests/test_state_machine.py
import tempfile
from pathlib import Path
from aero_code.orchestrator.loop import ProofLoopOrchestrator
from aero_code.schemas.issues import IssueReport
from aero_code.schemas.report import VerificationVerdict
from aero_code.state import ProofLoopEventBus

def test_proofloop_full_run():
    bus = ProofLoopEventBus()
    states_visited = []
    bus.subscribe(lambda e: states_visited.append(e.event_type))

    orchestrator = ProofLoopOrchestrator(mode="demo", event_bus=bus, max_retries=2)
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo = Path(tmp_dir)
        (repo / "src").mkdir()
        (repo / "tests").mkdir()
        (repo / "src" / "service.py").write_text("def run():\n    return 'deprecated_call'\n")
        (repo / "tests" / "test_baseline.py").write_text("def test_ok(): assert True\n")

        issue = IssueReport(
            issue_id="ISSUE-DEMO",
            title="Service failure",
            description="Deprecated call should be modern_call",
            traceback="AttributeError: deprecated_call",
            target_package="demo-pkg",
            package_version="1.0.0"
        )

        report = orchestrator.run(issue=issue, repo_dir=str(repo))
        assert report.verdict in (VerificationVerdict.VERIFIED, VerificationVerdict.INCONCLUSIVE)
        assert "PHASE_CHANGE" in states_visited
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_state_machine.py -v`
Expected: FAIL with ModuleNotFoundError: No module named 'aero_code.orchestrator'

- [ ] **Step 3: Implement ProofLoopOrchestrator**
Implement deterministic transition:
`INTAKE` $\to$ `INVESTIGATE` $\to$ `RESEARCH` $\to$ `REPRODUCE_BASELINE` $\to$ `GENERATE_PATCH` $\to$ `GIT_GUARD` $\to$ `SANDBOX_EXECUTE` $\to$ (`EVIDENCE_REPORT` $\to$ `PUBLISH_PR`).
Enforce retry budget and escalation model on failed sandbox runs.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_state_machine.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add aero_code/orchestrator/ tests/test_state_machine.py
git commit -m "feat: implement ProofLoop deterministic state machine orchestrator"
```

---

### Task 9: Curated Seeded Benchmark Cases & Evaluation Suite

**Files:**
- Create: `benchmarks/__init__.py`
- Create: `benchmarks/cases/pydantic_v2_migration/repo/...`
- Create: `benchmarks/cases/pydantic_v2_migration/issue.json`
- Create: `benchmarks/cases/requests_timeout_kwarg/repo/...`
- Create: `benchmarks/cases/requests_timeout_kwarg/issue.json`
- Create: `benchmarks/evaluate.py`
- Test: `tests/test_benchmarks.py`

**Interfaces:**
- Produces: `BenchmarkSuite.run_all()` calculating reproduction rate, repair rate, and catch rate.

- [ ] **Step 1: Write test for benchmark runner**

```python
# tests/test_benchmarks.py
from benchmarks.evaluate import BenchmarkSuite

def test_benchmark_suite_loading():
    suite = BenchmarkSuite()
    cases = suite.load_cases()
    assert len(cases) >= 2
    assert any(c.case_id == "pydantic_v2_migration" for c in cases)
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_benchmarks.py -v`
Expected: FAIL with ModuleNotFoundError: No module named 'benchmarks'

- [ ] **Step 3: Implement benchmark cases and evaluate.py**
Create the seeded bug directories with real python files and issues.
Implement `benchmarks/evaluate.py` to evaluate cases and compute metrics.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_benchmarks.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add benchmarks/ tests/test_benchmarks.py
git commit -m "feat: add curated benchmark cases and evaluation runner"
```

---

### Task 10: Real-Time Web Dashboard (FastAPI + Modern Dark-Mode SSE UI)

**Files:**
- Create: `aero_code/web/__init__.py`
- Create: `aero_code/web/server.py`
- Create: `aero_code/web/static/index.html`
- Create: `aero_code/web/static/styles.css`
- Create: `aero_code/web/static/app.js`
- Test: `tests/test_web_server.py`

**Interfaces:**
- Consumes: `ProofLoopEventBus`, `ProofLoopOrchestrator`
- Produces: FastAPI app at `/` with SSE stream at `/api/stream` and run trigger at `/api/run`

- [ ] **Step 1: Write failing test for web dashboard API**

```python
# tests/test_web_server.py
from fastapi.testclient import TestClient
from aero_code.web.server import create_app
from aero_code.state import ProofLoopEventBus

def test_dashboard_index_and_status():
    bus = ProofLoopEventBus()
    app = create_app(event_bus=bus)
    client = TestClient(app)
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Aero-Code" in resp.text
    
    status_resp = client.get("/api/status")
    assert status_resp.status_code == 200
    assert "status" in status_resp.json()
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_web_server.py -v`
Expected: FAIL with ModuleNotFoundError: No module named 'aero_code.web'

- [ ] **Step 3: Implement FastAPI server and modern UI static files**
Implement `aero_code/web/server.py` with SSE streaming.
Create `index.html`, `styles.css` (sleek dark mode, glassmorphism, responsive cards, glowing status pulses), and `app.js` (EventSource listener updating pipeline stepper, diff viewer, and Tavily citations in real time).

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_web_server.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add aero_code/web/ tests/test_web_server.py
git commit -m "feat: implement real-time web dashboard with SSE streaming"
```

---

### Task 11: Rich CLI Interface & Execution Commands

**Files:**
- Create: `aero_code/cli.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Commands:
  - `python -m aero_code.cli run --case <case_id> [--web] [--live]`
  - `python -m aero_code.cli evaluate`
  - `python -m aero_code.cli web`

- [ ] **Step 1: Write failing test for CLI commands**

```python
# tests/test_cli.py
from click.testing import CliRunner
from aero_code.cli import cli

def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "run" in result.output
    assert "evaluate" in result.output

def test_cli_list_cases():
    runner = CliRunner()
    result = runner.invoke(cli, ["cases"])
    assert result.exit_code == 0
    assert "pydantic_v2_migration" in result.output
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_cli.py -v`
Expected: FAIL with ModuleNotFoundError: No module named 'aero_code.cli'

- [ ] **Step 3: Implement Rich CLI**
Implement Click/Typer CLI with `rich.console`, `rich.panel`, `rich.table`, and animated spinners.
Support `--web` flag to automatically open web browser alongside CLI output.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_cli.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add aero_code/cli.py tests/test_cli.py
git commit -m "feat: implement Rich CLI runner and commands"
```

---

### Task 12: Documentation, Demo Video Guide, License & Final Verification

**Files:**
- Create: `README.md`
- Create: `LICENSE` (Apache-2.0)
- Create: `.env.example`
- Create: `docs/DEMO_VIDEO_SCRIPT.md`

- [ ] **Step 1: Create Apache-2.0 LICENSE file**
Add official Apache-2.0 license required by hackathon guidelines.

- [ ] **Step 2: Create comprehensive `.env.example`**
Include `NEBIUS_API_KEY`, `NEBIUS_BASE_URL`, `TAVILY_API_KEY`, `GITHUB_TOKEN`.

- [ ] **Step 3: Create hackathon-compliant `README.md`**
Include:
- System overview & architecture diagram
- Nebius Token Factory & NVIDIA Nemotron integration details
- Tavily search implementation (for $3,000 bonus track)
- Quickstart instructions (`run --case pydantic_v2_migration --web`)
- Double-Verification Rule explanation
- Benchmark evaluation results table

- [ ] **Step 4: Create `docs/DEMO_VIDEO_SCRIPT.md`**
Provide a step-by-step 2.5-minute script and narration guide for the YouTube demo video.

- [ ] **Step 5: Run full test suite across the entire project**
Run: `pytest tests/ -v`
Expected: All tests pass 100%.

- [ ] **Step 6: Commit and tag initial MVP**
```bash
git add README.md LICENSE .env.example docs/
git commit -m "docs: complete hackathon README, Apache license, and demo video script"
git tag v0.1.0-mvp
```
