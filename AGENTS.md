# AGENTS.md — AeroCode AI Agent Rules

This file contains standing instructions for all AI coding agents (GitHub Copilot, Antigravity, Cursor, etc.) operating in this repository.

---

## 1. Git Authorship — CRITICAL

**All commits MUST be authored under the repository owner's identity.**

The configured git identity for this repo is:
```
user.name  = adityasoni99
user.email = aditya.ece.111006@gmail.com
```

**Before making any commit**, verify the git user identity is correct:
```bash
git config user.name   # must output: adityasoni99
git config user.email  # must output: aditya.ece.111006@gmail.com
```

If it is wrong (e.g., an AI agent identity or a different email), fix it before committing:
```bash
git config user.name "adityasoni99"
git config user.email "aditya.ece.111006@gmail.com"
```

**Why this matters:** GitHub Copilot analytics, contribution graphs, and hackathon submission attribution all track commit author email. Every commit must show the owner's identity so that all work is correctly attributed on GitHub.

**If commits were made with the wrong author**, amend them before pushing:
```bash
# Amend the last commit's author
git commit --amend --author="adityasoni99 <aditya.ece.111006@gmail.com>" --no-edit

# For multiple commits (last N), rewrite all history at once:
git filter-branch --env-filter '
export GIT_AUTHOR_NAME="adityasoni99"
export GIT_AUTHOR_EMAIL="aditya.ece.111006@gmail.com"
export GIT_COMMITTER_NAME="adityasoni99"
export GIT_COMMITTER_EMAIL="aditya.ece.111006@gmail.com"
' --tag-name-filter cat -- --all
# Then force-push: git push origin main --force --tags
```

---

## 2. Branch Strategy

- All development happens on `main`.
- Feature branches are optional but should be named `feat/<description>`.
- Each hackathon phase is tagged before submission:
  - `v0.1.0-mvp` — ProofLoop MVP
  - `v0.2.0-paypal` — PayPal AI Hackathon
  - `v0.2.5-agentic` — Agentic AI Hackathon
  - `v0.3.0-kiro` — Kiroween IDE Hackathon
  - `v0.4.0-codegeist` — Codegeist 2026

---

## 3. Testing Requirements

- **All tests must pass before committing**: run `.venv\Scripts\pytest tests\ -v` (Windows) or `.venv/bin/pytest tests/ -v` (Linux/macOS).
- Never commit with failing tests.
- New features must include corresponding tests in `tests/`.

---

## 4. Project Layout (Quick Reference)

```
aero_code/
  orchestrator/   — ProofLoop deterministic state machine
  verifier/       — Git Guard + Sandbox runner
  tools/          — Nebius LLM client, Tavily search
  agents/         — Investigator + PatchEngineer agents
  schemas/        — Pydantic v2 data models
  web/            — FastAPI SSE dashboard
  mcp/            — (Phase 4) Model Context Protocol server
benchmarks/
  cases/          — Seeded bug benchmark cases
tests/            — Pytest unit + integration tests
docs/             — Architecture, plans, specs
```

---

## 5. Environment

- Python 3.11+ required.
- Virtual environment: `.venv/` (use `.venv\Scripts\activate` on Windows).
- Copy `.env.example` to `.env` and populate API keys before running live mode.
- Demo mode (no API keys needed) is the default for tests.
