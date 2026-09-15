# TODO — engineering work queue

The authoritative engineering backlog for the Azure appliance. Application work belongs
in the core repository's `TODO.md`; this file covers deployment, operations and this repository.

Items requiring external input — an approval, an account, a credential, an access grant — belong
in [`REVIEW.md`](REVIEW.md), not here. Completed work is recorded in [`CHANGELOG.md`](CHANGELOG.md).

**Last reviewed:** 2026-09-15

| Phase | Theme | Items |
|---|---|---|
| [Phase 1](#phase-1--bring-up) | Bring-up | T-101 – T-102 |

---

## Phase 1 — Bring-up

### T-101 — Verify the first `saas` apply is a pure re-addressing

- **Priority:** High
- **Description:** The import from the core added `count` to the AI module, the four Foundry role
  assignments and the Foundry private endpoint, each with a `moved` block. On an environment that
  already exists (dev), the first `210-deploy` plan must show only those `moved` annotations plus
  three in-place Container App env updates (`CNA_AI_MODE`, `CNA_APPLIANCE_CLOUD`,
  `CNA_AI_ENGINE_DEFAULT`) — no create, no destroy.
- **Recommended action:** Run `210-deploy` for dev in `saas` mode, stop at the plan artifact, and
  read it line by line before approving. A destroy of `module.ai` means a `moved` block is missing.
- **Status:** Open

### T-102 — Add this repository to the shared project board

- **Priority:** Low
- **Description:** `230-image-update`'s `update-available` issues should land on the one project
  board shared with the core and the sibling appliance.
- **Dependencies:** The core repository's `REVIEW.md` → R-012 (token decision).
- **Recommended action:** Add a SHA-pinned `actions/add-to-project` workflow on `issues: opened` and
  `pull_request: opened`, identical in both appliances.
- **Status:** Blocked on the core's R-012
