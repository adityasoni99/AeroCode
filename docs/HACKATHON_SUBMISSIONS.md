# AeroCode release and hackathon submission guide

Checked: **November 2, 2026**. Dates are event deadlines, not the internal
engineering targets formerly listed in the roadmap. Recheck the event's Rules,
Schedule, Resources, and submission form before entering; event terms can change.

## 1. Release status

| Tag | Contents | Submission meaning |
| --- | --- | --- |
| `v0.1.0-mvp` | Original ProofLoop foundation | Historical snapshot, not a submission receipt |
| `v0.2.0-paypal` | PayPal-style fixture and guardrails | No real PayPal API/signature integration demonstrated |
| `v0.2.5-agentic` | Docker sandbox adapter | Does not include the subsequent dashboard fixes |
| `v0.2.6-verified` | Docker + dashboard fixes, tests, and corrected docs | Current validated base; not automatic hackathon eligibility |
| `v0.3.0-kiro` | Planned IDE/MCP milestone | Not created; existing AeroCode is not eligible for Kiroween as-is |
| `v0.4.0-codegeist` | Planned Atlassian milestone | Not created; requires a working Forge application |

Validation of `v0.2.6-verified`: **110 passed, 1 skipped** with real Docker and
Chromium enabled. The skip requires Windows symlink privileges; junction exclusion
passed. All three seeded benchmark repairs also verified through Docker, with no
sandbox containers left behind.

Tests use deterministic demo patches. They do not verify live Nebius/Tavily calls,
real PayPal transactions/signature verification, hosted deployment, or GitHub
patch-branch publication. Evidence Reports are JSON/Markdown, not signed proofs.
Do not claim those integrations in a submission until they work and are demonstrated.

## 2. Sequence by verified deadline

### 1. PayPal AI Hackathon: November 12, 2026

- [Official event](https://paypalaihackathon.devpost.com/)
- [Rules](https://paypalaihackathon.devpost.com/rules)
- The [Devpost directory](https://devpost.com/hackathons) lists **October 1 to
  November 12, 2026**, not November 8. Exact cutoff/timezone and existing-project
  terms still need confirmation on the Rules/Schedule tabs: direct event access
  was blocked during this review, so do not rely solely on search summaries.
- **Current blocker:** a PayPal-looking benchmark is not meaningful PayPal
  platform integration. Build and test a real PayPal Sandbox workflow with AI
  as a central part of the experience; retain genuine verification and error
  handling, and keep all credentials out of the public repository and video.
- Read the exact accepted APIs/SDKs, payment flows, video limit, and judging
  criteria before choosing the implementation.
- **Tag:** use `v0.2.6-verified` as the development base, not the old
  `v0.2.0-paypal` as a claim of readiness. After completing the real integration,
  create a new immutable release such as **`v0.2.7-paypal`**. That tag is proposed,
  not created by this release.
- Document the prior work and what was added during the event. Obtain organizer
  confirmation if reuse or entry in multiple events is ambiguous.

### 2. Kiroween 2026: December 4, 2026 at 2 PM Pacific

- [Official event](https://kiroween.devpost.com/)
- [Rules](https://kiroween.devpost.com/rules)
- Deadline in IST: **December 5 at 3:30 AM**. This is not November 28.
- **Eligibility blocker:** the event overview explicitly only accepts new
  projects built during **October 30 to December 4, 2026**, excluding projects
  started before October 30. AeroCode has October 28 MVP design/history.
  Retagging, renaming, or adding a Kiro feature does not reset that history.
- Do not submit this repository as a newly created Kiroween project. Proceed only
  with a genuinely new eligible project or written organizer guidance.
- If entering with an eligible new project: build using Kiro, choose an appropriate
  category, preserve actual specs/hooks/steering under the root `/.kiro` directory
  (do not ignore it), provide a public GitHub repository/license and working app URL,
  and explain how Kiro helped. The public YouTube demo must be **under 3 minutes**.
- **Tag:** reserve **`v0.3.0-kiro`** for the future AeroCode IDE milestone.
  An eligible separate project needs its own release/tag and truthful creation history;
  this AeroCode tag is not a workaround for entry restrictions.

### 3. Codegeist 2026: December 22, 2026 at 12 PM Pacific

- [Official event](https://codegeist2026.devpost.com/)
- [Rules](https://codegeist2026.devpost.com/rules)
- [Atlassian deadline announcement](https://community.developer.atlassian.com/t/heads-up-developers-codegeist-2026-is-officially-open/103506)
- Deadline in IST: **December 23 at 1:30 AM**. December 15 is only our internal target.
- **Required build:** an app on **Atlassian Forge**, integrated with at least one
  Atlassian product/platform capability such as Jira, Confluence, Bitbucket,
  Teamwork Graph, or Rovo. Adding Python Jira/Bitbucket clients alone is insufficient.
- Recommended fit: **Apps for Software Teams**. Demonstrate issue intake,
  repair/verification evidence, and a reviewable result in an Atlassian workflow.
- Provide a working **Forge installation link** and all testing instructions,
  a public YouTube demo **under 5 minutes**, category selection, and an explanation
  of the required technology integration.
- Select MCP/Rovo/Teamwork Graph/Marketplace bonus prizes only when the specific
  qualifying Forge modules/integrations and requested evidence are implemented.
  A standalone Python MCP server does not alone prove the Forge MCP bonus requirement.
- **Tag:** create **`v0.4.0-codegeist`** only after Forge deployment, installation,
  integration tests, and the end-to-end judge workflow pass.
- Confirm existing-project and multi-event reuse terms on the official rules
  before reusing AeroCode; disclose the baseline and event-period work.

### Agentic event: identify before assigning a deadline

The roadmap's "Agentic AI Hackathon, November 16, 2026" could not be tied to a
verified currently open event.

The [Agentic AI Unleashed: AWS & NVIDIA](https://nvidia-aws.devpost.com/) page is
an **ended October 13 to November 4, 2025** event, not a November 2026 opportunity.
It required NVIDIA NIM inference/retrieval and AWS deployment; Docker/OpenShell
hardening alone would not satisfy those requirements.

Use `v0.2.6-verified` as the agentic development base. Do not submit
`v0.2.5-agentic` to an unidentified event or assume OpenShell is mandatory.
Choose an open event, verify its actual required services, then create a new
release matching the additional work.

### Original Nebius/NVIDIA target

The [Nebius x NVIDIA Global AI Hackathon](https://nebiusglobalaihackathon.devpost.com/)
page currently says **the hackathon has ended**. Its visible schedule metadata
is not a verified upcoming submission cutoff, so it is not included in the open
submission sequence.

The overview requires a working system on Nebius Token Factory or AI Cloud with
an NVIDIA open-source model, a working demo/test build, public licensed repository,
and public YouTube video no longer than 3 minutes. It also asks for significant
updates to be disclosed for preexisting work. Keep these as historical requirements,
not a claim that offline fixture tests establish sponsor usage or entry eligibility.

## 3. Complete process for each eligible event

1. **Verify eligibility before building.**
   - Open the official event Rules/Schedule, not just a directory card.
   - Record deadline with timezone, team/country restrictions, accepted technologies,
     existing-project rules, and any ban/restriction on multiple submissions.
   - Join/register and invite teammates. Save written organizer guidance for uncertainty.
   - Define the event-period delta from the existing release; do not conceal prior work.
2. **Build the required sponsor workflow.**
   - Use the sponsor's sandbox/developer environment, not real customer payments/data.
   - Exercise success, invalid input, network/API errors, timeouts, and retry paths.
   - Distinguish fixture outputs, live service responses, and mock PR results visibly.
   - For Codegeist, install the actual Forge app on a clean developer site.
3. **Freeze a verified release.**
   - Update README, architecture/current limitations, setup steps, and this guide.
   - Run unit/integration/browser tests; enable real Docker checks when claiming isolation.
   - Review changes for credentials, third-party data, and unintended files.
   - Verify repository owner identity, commit, and create a new annotated tag.
     Never move an already published tag to include later work.
4. **Publish judge access and evidence.**
   - Push only after approval. For this release, the user requested **no push**.
   - Example for the approved local release, when publication is authorized:
     ```powershell
     git push origin main
     git push origin v0.2.6-verified
     ```
   - Create a GitHub release describing the validated features, test command/results,
     known limitations, and sponsor integration delta.
   - Use the immutable tag URL, e.g.
     `https://github.com/adityasoni99/AeroCode/tree/v0.2.6-verified`.
   - Provide a working hosted demo/test build or installation link when required.
     `localhost` is not accessible to judges.
   - Record the event-specific video within its limit. Use permitted assets,
     show the complete workflow, and never expose credentials.
   - Check every public link in a signed-out/private browser session.
5. **Submit, then verify the submission.**
   - Fill the Devpost form: problem, solution, architecture, used technologies,
     sponsor integration, new work, repository/tag, app/install URL, and video.
   - Select only categories/bonuses for which you have evidence.
   - Supply judge-only access instructions in the private submission fields,
     not committed files.
   - Explicitly press **Submit** before the cutoff; a saved draft or Git tag is not entry.
   - Confirm the submission status and retain the confirmation URL/receipt.
   - Preserve the submitted tag and deployment; do not break judge access during review.

## 4. Supporting documents

- [README](../README.md): current implementation, setup, tests, and limitations.
- [ROADMAP](../ROADMAP.md): remaining engineering work and internal targets.
- [Demo script](DEMO_VIDEO_SCRIPT.md): truthful offline demo outline.
- [Original blueprint](../aero_code_complete_blueprint_architecture.md): historical intent.

No organizer registration, GitHub push, hosted deployment, video upload, or Devpost
submission is performed automatically by creating `v0.2.6-verified`.
