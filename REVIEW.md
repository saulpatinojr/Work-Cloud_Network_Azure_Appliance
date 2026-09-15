# Review — human-resolvable blockers

This file tracks **only** items that an engineer cannot resolve independently. Every entry
requires external input: an approval, a credential, an account, an access grant, or a decision
that belongs to a named owner outside the engineering task itself.

Anything an engineer can solve without external input belongs in [`TODO.md`](TODO.md), not here.
Application-level blockers live in the core repository's `REVIEW.md`.

**Last reviewed:** 2026-09-15

| ID | Blocker | Owner | Status |
|---|---|---|---|
| [R-001](#r-001--security-review-before-the-first-byo-api-deploy) | Security review of the bring-your-own AI key path and the Anthropic/OpenAI firewall egress | Security | Open — before the first `byo-api` deploy |
| [R-002](#r-002--required-reviewers-on-the-hub-environment) | `hub` environment required reviewers for prod applies | Repository admin | Open |

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
