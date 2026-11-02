# Aero-Code (ProofLoop™) Engineering Roadmap

This document outlines the sequenced development milestones and technical deliverables for Aero-Code across upcoming hackathons and open-source releases.

**Status checked November 2, 2026:** milestone dates below are internal targets,
not event deadlines. The verified release is `v0.2.6-verified`; the full local
suite with Docker and Chromium enabled recorded **110 passed, 1 skipped**.
See [the submission guide](docs/HACKATHON_SUBMISSIONS.md) for current event rules,
eligibility blockers, and the publication process. No Devpost submission is
recorded as completed here.

---

## 🧭 Milestone Summary

- [x] **v0.1.0-mvp — ProofLoop Foundation** *(Completed)*
  - Pydantic v2 data models & deterministic state machine orchestrator
  - Configurable Nebius Token Factory & NVIDIA Nemotron clients
  - Tavily dynamic search & contextual citation extraction
  - Git Guard test & build configuration immutability engine
  - Subprocess sandbox verifier with credential stripping
  - Curated seeded benchmark suite (`pydantic_v2_migration`, `requests_timeout_kwarg`)
  - Real-time FastAPI SSE Web Dashboard & Rich CLI
  - Historical pre-hardening baseline: 25 passing tests

---

## 🚀 Upcoming Milestones (In Priority Order)

### Phase 1: Repository Publication & CI Automation (Immediate)
- [x] Push local `main` branch and tags to GitHub repository `https://github.com/adityasoni99/AeroCode.git`.
- [x] Add `.github/workflows/ci.yml` running pytest across Python 3.11 and 3.12.
- [x] Add optional Chromium tests and install their runtime in CI.
- [ ] Add pre-commit hook enforcing Black, Flake8, and Git Guard rule validation.

---

### Phase 2: PayPal Track (Internal Target: Nov 8, 2026)
> *Goal: Mission-critical code verification for financial APIs and webhook resilience.*
- [x] **PayPal SDK Benchmark Case:**
  - Create `benchmarks/cases/paypal_webhook_signature/` with PayPal-style header handling.
  - Verify missing/empty header rejection in deterministic demo repairs.
  - This local fixture does not implement cryptographic PayPal signature verification.
- [x] **Payment Anomaly Detection & Guardrails:**
  - Add compliance rule to `GitGuard` flagging edits touching secret credential variables or SSL verification bypass (`verify=False`).
- [x] **Historical Release Tag:** `v0.2.0-paypal`.
- [ ] Integrate and demonstrate meaningful PayPal Sandbox API functionality with AI.
- [ ] Submit an eligible entry to [PayPal AI Hackathon](https://paypalaihackathon.devpost.com/).
  The Devpost directory lists November 12, 2026, not November 8. Confirm the exact
  cutoff/timezone and reuse rules on the event Rules/Schedule tabs before submitting.

---

### Phase 3: Agentic Sandbox Hardening (Internal Target: Nov 16, 2026)
> *Goal: Zero-trust isolated container execution for untrusted code.*
- [x] **Native Docker Sandbox Adapter:**
  - Complete disposable container lifecycle in `aero_code/verifier/sandbox/docker.py`.
  - Enforce resource limits (2 vCPU, 2GB RAM max, 60s hard timeout) and network isolation.
  - Live mode is Docker-first, with explicit unavailable-only subprocess fallback;
    demo mode preserves offline subprocess execution.
  - Mocked lifecycle tests run without Docker; real-container integration tests are opt-in.
  - All real Docker checks passed after Windows/WSL2 installation and restart.
- [x] **Dashboard Flow Hardening:** correct presets, non-vacuous verification,
  thread-safe/replayable SSE, error handling, repeat runs, mobile and keyboard checks.
- [ ] **NVIDIA OpenShell Integration Spike:**
  - Evaluate NVIDIA OpenShell runtime for agent filesystem isolation.
- [x] **Release Tag:** `v0.2.5-agentic` (Docker sandbox hardening).
- [x] **Verified Follow-up Release:** `v0.2.6-verified` (Docker + UI + documentation).
- [ ] Identify a currently open, eligible agentic hackathon and its required services.
  No November 16 event was verified. The AWS/NVIDIA Agentic AI Unleashed page is
  for an ended 2025 event; Docker/OpenShell work alone is not an entry requirement.

---

### Phase 4: Kiro IDE & Model Context Protocol (Internal Target: Nov 28, 2026)
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
- [ ] **Future Release Tag:** `v0.3.0-kiro` after implementation and validation.
- **Eligibility blocker:** [Kiroween 2026](https://kiroween.devpost.com/) closes
  December 4 at 2 PM Pacific and only accepts projects started during October 30
  to December 4. AeroCode's October 28 MVP cannot be made eligible by retagging.
  Use a genuinely new project or obtain written organizer guidance before proceeding.

---

### Phase 5: Codegeist 2026 (Internal Target: Dec 15, 2026)
> *Goal: "Build with context. Ship with confidence" for enterprise teams.*
- [ ] **Atlassian Jira Issue Intake:**
  - Implement `aero_code/tools/jira_client.py` to ingest Jira bug tickets and extract reproduction tracebacks.
- [ ] **Bitbucket Pull Request & Verification Checks:**
  - Implement `aero_code/tools/bitbucket_client.py` to open draft PRs with the Double-Verification Evidence Report attached as build status checks.
- [ ] **Forge Application:** deploy an Atlassian Forge app integrating at least
  one Atlassian product/platform capability; Python API clients alone are insufficient.
- [ ] Provide a working Forge installation link and a public demo video under 5 minutes.
- [ ] **Future Release Tag:** `v0.4.0-codegeist` after implementation and validation.
- [ ] Submit to [Codegeist 2026](https://codegeist2026.devpost.com/) by
  **December 22, 2026 at 12 PM Pacific** (December 23 at 1:30 AM IST).
