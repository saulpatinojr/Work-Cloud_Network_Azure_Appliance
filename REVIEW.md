# Review — human-resolvable blockers

This file tracks **only** items that an engineer cannot resolve independently. Every entry
requires external input: an approval, a credential, an account, an access grant, or a decision
that belongs to a named owner outside the engineering task itself.

Anything an engineer can solve without external input belongs in [`TODO.md`](TODO.md), not here.
Application-level blockers live in the core repository's `REVIEW.md`.

**Last reviewed:** 2026-09-18

| ID | Blocker | Owner | Status |
|---|---|---|---|
| [R-001](#r-001--security-review-before-the-first-byo-api-deploy) | Security review of the bring-your-own AI key path and the Anthropic/OpenAI firewall egress | Security | Open — before the first `byo-api` deploy |
| [R-002](#r-002--required-reviewers-on-the-hub-environment) | `hub` environment required reviewers for prod applies | Repository admin | Open |

| [R-003](#r-003--live-azure-beta-acceptance-sign-off) | 0.8 beta exit — live Azure acceptance sign-off | Product owner | Open — deploy done 2026-08-28, acceptance outstanding |
| [R-004](#r-004--the-dev-environment-has-no-protection-against-out-of-band-deletion) | Dev environment deleted out of band; no protection against a repeat | Azure subscription owner | Open |
| [R-005](#r-005--repoint-core_repo-at-the-new-core-repository) | Set `CORE_REPO` to `Work-Cloud_Network_Core` once the core repository is live | Repository admin | Open — until then `230` polls the archived repository |
---

## R-001 — Security review before the first `byo-api` deploy

**Problem**
`ai_mode: byo-api` stores admin-entered Anthropic/OpenAI API keys AES-256-GCM encrypted in the
application database and opens Azure Firewall egress to `api.anthropic.com` and `api.openai.com`.
The implementation lives in the core repository and is complete and tested; CBTS engineering
standards require a human security review before it carries customer traffic.

**Required owner**
Security.

**Required action**
Complete the core repository's `REVIEW.md` → R-011 (it lists the exact files and questions), then
record the outcome here.

**Impact if unresolved**
`byo-api` cannot be offered to a customer from this appliance. `saas` is unaffected.

---

## R-002 — Required reviewers on the `hub` environment

**Problem**
`210-deploy`'s prod `apply` job runs under the `hub` GitHub environment, whose required
reviewers are the human approval gate for production changes — the same gate the core used. A
freshly created repository has no environments and therefore no gate.

**Required owner**
Repository admin.

**Required action**
Create the `dev`, `prod` and `hub` environments; give `hub` the same required reviewers the core
repository's `hub` environment has; register the OIDC federated credential for the prod deploy
identity against subject `environment:hub` of this repository.

**Impact if unresolved**
Prod deploys either fail OIDC or, worse, run without human approval.

---

## R-003 — Live Azure beta acceptance sign-off

> Transferred 2026-09-15 from the core repository's `REVIEW.md` → R-008 (core T-507).

**Problem**
The repository is at `0.8.0b0`. Code, Terraform, workflows, and the changelog are aligned on
`main`, but the beta exit gate is live Azure execution: prerequisite validation, dev deploy,
Entra redirect update, runtime validation, and customer-like beta acceptance.

**Why it blocks progress**
Acceptance is a product judgement, not an engineering result. No amount of further engineering
work moves the release posture past `0.8 beta` without someone accepting the live evidence.

**Required owner**
Product owner (with the AWS/Azure account owners for the deploy windows).

**Required action**
1. ~~Schedule the live dev deploy window (workflows 100 → 200 → 211).~~ **Done 2026-08-28** —
   though not as a scheduled window: the dev environment had been deleted out of band (see R-004
   and `the core's CNA-0.90-updates.md` §5), so it was rebuilt from nothing via `000` → `100` → `210`.
   Run `33169632082`, all jobs green.
2. **Review the deployment evidence artifacts produced by the workflow run.** These now exist:
   `.deployment-catalog/dev/33169632082.json` records `health_status: healthy`, 100% origin
   health, and passing canary, staged-promotion, certificate and private-endpoint checks.
   **Check the two Foundry markers read `passed`** — since `TODO.md` → T-104 (2026-09-23),
   `foundry_private_dns_validation` and `foundry_managed_identity_inference` are set by `210`
   itself from a probe run inside the environment, and a run cannot reach `healthy` (or the
   catalog) while either is anything else. The `33169632082` entry predates that and still
   carries them as `required`: its `healthy` verdict does not cover the AI Foundry / Copilot path,
   so accept against a `210` run made after the change.
3. Accept or reject the customer-like beta acceptance run, and record the decision.
   Note the acceptance run has not happened yet: the rebuilt environment has an empty database,
   so there is no discovery, finding, or deliverable in it to accept against.

**Impact if unresolved**
The platform stays in beta indefinitely and cannot be offered to a client engagement, regardless
of code readiness.

**References**
- `.github/workflows/100-validate-prereqs.yml`, `200-build-images.yml`,
  `210-deploy.yml`
- `scripts/ci/evaluate_deployment_evidence.py`
- [`CHANGELOG.md`](CHANGELOG.md) → `[0.8.0-beta]`

**Recommended next step**
Book the deploy window. core R-007 no longer blocks it — see that item; provider registration is now
asserted by workflow `100-validate-prereqs.yml`, which should be run first regardless.

---

---

## R-004 — The dev environment has no protection against out-of-band deletion

> Transferred 2026-09-15 from the core repository's `REVIEW.md` → R-010 (core T-507).

**Problem**
The entire Azure dev environment — workload resource group *and* the `-tfstate` resource group
holding the Terraform state — was deleted from `sub-cbtssandbox-ops-tst` around **2026-07-21**,
outside CI. No teardown workflow ran in that window (`330-teardown` last ran 2026-07-01), so the
deletion was performed directly against the subscription, consistent with a sandbox cost sweep.

It was rebuilt on 2026-08-28 (`the core's CNA-0.90-updates.md` §5), but nothing prevents a repeat, and the
rebuild was not cheap: the state loss meant a from-scratch provision, six previously-unknown gaps
in the deploy identity's least-privilege role set, a soft-deleted Key Vault to recover and import,
and roughly half a day of a pre-demo schedule.

**Why it needs an owner**
Whether the sweep is intentional policy is not an engineering question. If the sandbox is *meant*
to be swept, the environment should not be treated as durable and the demo/engagement plan has to
budget a rebuild each time. If it is not meant to be swept, the environment needs protecting. Only
the subscription owner can say which.

**Required owner**
Azure subscription owner (`sub-cbtssandbox-ops-tst`), with whoever administers the sandbox
sweep policy.

**Required action**
1. Establish whether a sweep policy exists for this subscription, what it targets, and on what
   schedule.
2. If the environment should persist: apply a `CanNotDelete` resource lock to
   `rg-cna-dev-scus` and `rg-cna-dev-scus-tfstate` at minimum — the state RG especially, since
   losing it is what turned a redeploy into a rebuild — or request an exclusion from the sweep.
3. If the environment is legitimately ephemeral: record that in the demo/engagement runbook so a
   rebuild is planned rather than discovered, and consider whether the tfstate backend should live
   in a subscription that is not swept.

**Impact if unresolved**
The next sweep repeats the same half-day recovery, at whatever moment it happens to land. The
permission gaps are now codified in `scripts/Initialize-CnaGitHubSecrets.ps1`, so a second rebuild
would be materially faster — but it would still be a rebuild, with a fresh, empty database.

**References**
- [`the core's CNA-0.90-updates.md`](the core's CNA-0.90-updates.md) → §5 (the full rebuild record)
- [`TODO.md`](TODO.md) → T-105 (the drift check that detected this and told no one)
- `.deployment-catalog/dev/33169632082.json` (the rebuild's evidence)

**Recommended next step**
Ask the sandbox administrator the one question that decides everything else: is
`sub-cbtssandbox-ops-tst` swept on a schedule, and can these two resource groups be excluded?

---

---

## R-005 — Repoint `CORE_REPO` at the new core repository

**Problem**
The core moved from `Work-Cloud_Network_Assessment` to `Work-Cloud_Network_Core` (core `TODO.md`
T-509). `230-image-update` reads the build manifest from the repository named by the `CORE_REPO`
variable through the GitHub App; while the variable still names the original repository, this
appliance keeps polling a manifest that will never change again, and the dispatch from the new
core's `200-build-images` reaches this repository only if the App is installed on the new core.

**Why it needs an owner**
Repository variables and GitHub App installations are settings only the repository admin can write.

**Required owner**
Repository admin.

**Required action**
1. Wait until the core's `REVIEW.md` R-013 steps 1 – 4 are done (secrets and variables, App
   installation, and the first `200` run on `Work-Cloud_Network_Core`).
2. *Settings → Secrets and variables → Actions → Variables*: set `CORE_REPO` to `Work-Cloud_Network_Core`.
3. Run `230 · Image Update` once from *Run workflow* (`force: false`) and confirm the *Fetch the
   manifest* step reads from the new repository.
4. Do the same in the sibling appliance.

**Impact if unresolved**
No new image set ever reaches this appliance: `dev` stops auto-updating and no `update-available`
issue is opened for `prod`.

**References**
- `.github/workflows/230-image-update.yml` (`vars.CORE_REPO`)
- `README.md` → *Configuration*
- Core `REVIEW.md` R-013 / `TODO.md` T-509
