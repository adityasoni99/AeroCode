# Aero-Code Demo Video Script (2.5 Minutes)

> **YouTube Presentation & Hackathon Submission Guide**
> Target Length: 2 minutes 30 seconds
> Screen Recording: Terminal + Web Dashboard

**Release note (November 2, 2026):** record `v0.2.6-verified` or a later validated
release. Follow [the submission guide](HACKATHON_SUBMISSIONS.md) for each event's
video limit and eligibility. The script below describes the offline demo:
fixtures are deterministic, citations are cached, and a PR without a token is
a mock record. Do not call it live inference or show a mock as a real GitHub PR.

---

## 🎬 Scene Breakdown

### Scene 1: The Problem (0:00 - 0:30)
- **Visual:** Split screen showing an LLM making a fake test pass by deleting existing assertions or editing `pyproject.toml`.
- **Narration:**
  > "AI coding agents can produce plausible changes that do not fix the bug. Developers still need to detect weakened tests, missed edge cases, and regressions.
  > 
  > Welcome to **Aero-Code**, featuring **ProofLoop™** — a bounded engineering workflow backed by reproducible Double-Verification test evidence."

---

### Scene 2: The ProofLoop™ Engine Architecture (0:30 - 1:00)
- **Visual:** Mermaid architecture diagram and Aero-Code Web Dashboard opening at `http://127.0.0.1:8000`.
- **Narration:**
  > "Aero-Code has nine visible pipeline stages. Live inference is configured for **NVIDIA Nemotron** on **Nebius Token Factory**, with contextual research through **Tavily**. This recording uses deterministic offline fixtures.
  >
  > Aero-Code enforces the **Double-Verification Rule**:
  > 1. A new regression test MUST reproduce the bug and fail on unpatched code.
  > 2. The patch MUST make that regression test pass.
  > 3. Zero regressions: 100% of existing baseline tests must remain green.
  > 4. Git Guard ensures baseline tests and build files can never be altered by the LLM."

---

### Scene 3: Live Demo — Pydantic V2 Migration (1:00 - 2:00)
- **Visual:** Start `aero-code web`, select the Pydantic preset, and click Run ProofLoop.
  The browser dashboard updates in real time over Server-Sent Events (SSE).
- **Narration:**
  > "Let's watch ProofLoop tackle a real-world issue: a breaking API migration in Pydantic V2 where `.parse_obj()` was deprecated.
  >
  > Notice the pipeline stepper:
  > - **Investigator** identifies the relevant API symbol.
  > - **Contextual Researcher** displays cached official migration guidance in demo mode.
  > - **Patch Engineer** applies the deterministic fixture patch and adds a regression test that treats deprecated API warnings as errors.
  > - **Git Guard** validates that existing tests and pyproject.toml remain untouched.
  > - **Sandbox Verifier** executes pytest in a disposable workspace. The unpatched code fails the test; the patch passes it; baseline tests stay green.
  >
  > The Double-Verification Matrix turns all green: **VERIFIED**."

---

### Scene 4: Pull Request & Conclusion (2:00 - 2:30)
- **Visual:** Completed verification matrix, patch, citations, and the event log's
  clearly identified mock PR result. For a Docker-focused video, also show the
  passing real-container integration test output.
- **Narration:**
  > "Finally, Aero-Code generates a structured Evidence Report. Bug reproduction, patch success, and protected tests are verified before the publication stage. In this offline demo, the PR result is a mock; live publication remains a separate integration task.
  >
  > Aero-Code: make generated fixes easier to challenge and verify.
  > Built with Nebius Token Factory, NVIDIA Nemotron, and Tavily AI.
  > Check out the open-source code on GitHub under the Apache-2.0 license."

---

## 📋 Production Checklist for Recording

1. Launch web dashboard:
   ```bash
   aero-code web
   ```
2. Have terminal on the left half of the screen (running `aero-code evaluate` or `aero-code run`).
3. Have web dashboard on the right half (showing live stepper transitions, log stream, and Double-Verification Matrix).
4. Audio: Clean microphone input with upbeat background audio ducked at 15%.
5. Video resolution: 1080p 60fps, exported in MP4 format.
6. Use only music/assets you have permission to include; a silent demo is acceptable.
7. Show 110 passing tests (1 Windows symlink privilege skip) only when presenting
   the November 2 verified release; rerun tests for later releases.
8. Sponsor-required live API use must be recorded separately with valid credentials
   hidden. A PayPal-style header fixture is not a real PayPal payment/signature demo.
