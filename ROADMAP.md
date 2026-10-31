# Aero-Code (ProofLoop™) Engineering Roadmap

This document outlines the sequenced development milestones and technical deliverables for Aero-Code across upcoming hackathons and open-source releases.

---

## 🧭 Milestone Summary

- [x] **v0.1.0-mvp — ProofLoop Foundation** *(Completed)*
  - Pydantic v2 data models & deterministic state machine orchestrator
  - Nebius Token Factory & NVIDIA Nemotron (30b primary & 550b escalation)
  - Tavily dynamic search & contextual citation extraction
  - Git Guard test & build configuration immutability engine
  - Subprocess sandbox verifier with credential stripping
  - Curated seeded benchmark suite (`pydantic_v2_migration`, `requests_timeout_kwarg`)
  - Real-time FastAPI SSE Web Dashboard & Rich CLI
  - 23/23 unit and integration tests passing

---

## 🚀 Upcoming Milestones (In Priority Order)

### Phase 1: Repository Publication & CI Automation (Immediate)
- [ ] Push local `main` branch and tags to GitHub repository `https://github.com/adityasoni99/AeroCode.git`.
- [ ] Add `.github/workflows/ci.yml` running pytest across Python 3.11 and 3.12.
- [ ] Add pre-commit hook enforcing Black, Flake8, and Git Guard rule validation.

---

### Phase 2: PayPal AI Hackathon Track (Target: Nov 8, 2026)
> *Goal: Mission-critical code verification for financial APIs and webhook resilience.*
- [ ] **PayPal SDK Benchmark Case:**
  - Create `benchmarks/cases/paypal_webhook_signature/` reproducing signature header deprecations.
  - Test ProofLoop repairing the webhook validation without bypassing signature checks.
- [ ] **Payment Anomaly Detection & Guardrails:**
  - Add compliance rule to `GitGuard` flagging edits touching secret credential variables or SSL verification bypass (`verify=False`).
- [ ] **Release Tag:** `v0.2.0-paypal` & submit to PayPal AI Hackathon.

---

### Phase 3: Agentic Sandbox Hardening (Target: Nov 16, 2026)
> *Goal: Zero-trust isolated container execution for untrusted code.*
- [ ] **Native Docker Sandbox Adapter:**
  - Complete disposable container lifecycle in `aero_code/verifier/sandbox/docker.py`.
  - Enforce resource limits (2 vCPU, 2GB RAM max, 60s hard timeout) and network isolation.
- [ ] **NVIDIA OpenShell Integration Spike:**
  - Evaluate NVIDIA OpenShell runtime for agent filesystem isolation.
- [ ] **Release Tag:** `v0.2.5-agentic` & submit to Agentic AI Hackathon.

---

### Phase 4: Kiroween IDE & Model Context Protocol (Target: Nov 28, 2026)
> *Goal: Deep developer workflow integration and IDE companion tools.*
- [ ] **Model Context Protocol (MCP) Server:**
  - Create `aero_code/mcp/server.py` exposing ProofLoop tools over standard JSON-RPC:
    - `run_proofloop(issue_id, repo_path)`
    - `verify_patch(patch_diff, repo_path)`
    - `evaluate_benchmarks()`
  - Enable one-click integration with Kiro IDE, Cursor, and VS Code.
- [ ] **Interactive Web UI Enhancements:**
  - Side-by-side Monaco code editor diff viewer.
  - Benchmark suite runner tab in Web UI.
- [ ] **Release Tag:** `v0.3.0-kiro` & submit to Kiroween 2026.

---

### Phase 5: Codegeist 2026 (Atlassian Ecosystem) (Target: Dec 15, 2026)
> *Goal: "Build with context. Ship with confidence" for enterprise teams.*
- [ ] **Atlassian Jira Issue Intake:**
  - Implement `aero_code/tools/jira_client.py` to ingest Jira bug tickets and extract reproduction tracebacks.
- [ ] **Bitbucket Pull Request & Verification Checks:**
  - Implement `aero_code/tools/bitbucket_client.py` to open draft PRs with the Double-Verification Evidence Report attached as build status checks.
- [ ] **Release Tag:** `v0.4.0-codegeist` & submit to Codegeist 2026.
