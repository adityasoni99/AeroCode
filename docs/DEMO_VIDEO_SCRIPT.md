# Aero-Code Demo Video Script (2.5 Minutes)

> **YouTube Presentation & Hackathon Submission Guide**
> Target Length: 2 minutes 30 seconds
> Screen Recording: Terminal + Web Dashboard

---

## 🎬 Scene Breakdown

### Scene 1: The Problem (0:00 - 0:30)
- **Visual:** Split screen showing an LLM making a fake test pass by deleting existing assertions or editing `pyproject.toml`.
- **Narration:**
  > "Autonomous coding agents are revolutionizing software development. But here is the dirty secret: most agents cheat. When tests fail, they often delete existing assertions, weaken test thresholds, or claim code is fixed when it actually breaks production in subtle ways.
  > 
  > Welcome to **Aero-Code**, featuring **ProofLoop™** — the first deterministic software engineering agent backed by a cryptographic-grade Double-Verification Engine."

---

### Scene 2: The ProofLoop™ Engine Architecture (0:30 - 1:00)
- **Visual:** Mermaid architecture diagram and Aero-Code Web Dashboard opening at `http://127.0.0.1:8000`.
- **Narration:**
  > "Aero-Code operates on a strict 9-phase state machine. It is powered by **NVIDIA Nemotron** models running on **Nebius Token Factory**, dynamic search via the **Tavily AI API**, and an immutable **Git Guard** policy.
  >
  > Aero-Code enforces the **Double-Verification Rule**:
  > 1. A new regression test MUST reproduce the bug and fail on unpatched code.
  > 2. The patch MUST make that regression test pass.
  > 3. Zero regressions: 100% of existing baseline tests must remain green.
  > 4. Git Guard ensures baseline tests and build files can never be altered by the LLM."

---

### Scene 3: Live Demo — Pydantic V2 Migration (1:00 - 2:00)
- **Visual:** Terminal running `aero-code run --case pydantic_v2_migration --web`.
  The browser dashboard updates in real time over Server-Sent Events (SSE).
- **Narration:**
  > "Let's watch ProofLoop tackle a real-world issue: a breaking API migration in Pydantic V2 where `.parse_obj()` was deprecated.
  >
  > Notice the pipeline stepper:
  > - **Investigator** pinpoints the exact line and symbol from the stack trace.
  > - **Contextual Researcher** queries Tavily dynamically with the package version, retrieving the official migration guide.
  > - **Patch Engineer** writes the minimal patch along with an isolated regression test.
  > - **Git Guard** validates that existing tests and pyproject.toml remain untouched.
  > - **Sandbox Verifier** executes pytest in an isolated environment. The unpatched code fails the test; the patch passes it; baseline tests stay completely green.
  >
  > The Double-Verification Matrix turns all green: **VERIFIED**."

---

### Scene 4: Pull Request & Conclusion (2:00 - 2:30)
- **Visual:** The generated Markdown Evidence Report and Draft GitHub Pull Request showing full citation audit trails.
- **Narration:**
  > "Finally, Aero-Code generates a cryptographically auditable Evidence Report and publishes a verified Pull Request. Every single claim is backed by reproducible sandbox test outputs and Tavily documentation links.
  >
  > Aero-Code: Software engineering agents you can actually trust in production.
  > Built with Nebius Token Factory, NVIDIA Nemotron, and Tavily AI.
  > Check out the open-source code on GitHub under the Apache-2.0 license."

---

## 📋 Production Checklist for Recording

1. Launch web dashboard:
   ```bash
   aero-code run --case pydantic_v2_migration --web
   ```
2. Have terminal on the left half of the screen (running `aero-code evaluate` or `aero-code run`).
3. Have web dashboard on the right half (showing live stepper transitions, log stream, and Double-Verification Matrix).
4. Audio: Clean microphone input with upbeat background audio ducked at 15%.
5. Video resolution: 1080p 60fps, exported in MP4 format.
