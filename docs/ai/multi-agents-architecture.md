# Architecture AI — Reference to define the interaction with AI Multi-Agents

This document summarizes the entire multi-agent setup, the instructions, the skills, and the organizational rules used on the project.

**Before dispatching**: read the corresponding role description and include it in the agent's brief

## Multi-agent team

### Roles

Each role has a **detailed job description** in `docs/team/` (responsibilities, file scope, skills, end-of-task checklist). The lead MUST read the description before spawning the corresponding agent.

| Role                       | Description                                 | Responsibility                                                                            | File scope                                    |
| -------------------------- | ------------------------------------------- | ----------------------------------------------------------------------------------------- | --------------------------------------------- |
| **Lead dev** (main Claude) | [`docs/team/lead.md`](team/lead.md)         | Organization, review, integration, refocusing, architecture co-piloting with the user     | All (integration)                             |
| **Dev**                    | [`docs/team/dev.md`](team/dev.md)           | Code, implementation, fixes, self `/verif`                                                | `src/`, `tests/`                              |
| **PO**                     | [`docs/team/po.md`](team/po.md)             | Needs → specs, functional mapping, copy/content, `/sync-docs`                             | `docs/`                                       |
| **Designer**               | [`docs/team/designer.md`](team/designer.md) | UI/UX specs (wireframes, classes, JSX structure), a11y/design review — **NO integration** | — (specs communicated directly)               |
| **Tester**                 | [`docs/team/testeur.md`](team/testeur.md)   | QA + test development, challenges PO specs, acceptance, AC matrix                         | `tests/`                                      |
| **SEO** (occasional)       | —                                           | Meta, logo, semantic HTML, links — **allowed to code**                                    | `src/ui/layout.tsx`, `src/ui/config-page.tsx` |

### Organization rules

**Role separation:**

- The designer produces specs (wireframes, Tailwind classes, structure), the dev integrates. They challenge each other.
- The designer does NOT touch `main.ts`, `deno.json`, or any integration files.
- **No agent — not even the lead — ever commits or pushes.** Committing is exclusively the user's job. The team delivers a reviewed, verified working tree and signals it is ready; the user commits.
- **No intermediate `.md` artifacts in `docs/ai/`.** Specs, AC, UI specs, review/coverage reports are exchanged directly between roles (agent briefs and reports) — they are not persisted as `.md` files. Only real project documentation (README, CLAUDE.md, ADR) is written, via `/sync-docs`.

**Senior autonomous dev:**

- The dev runs `/verif` and self-reviews after each implementation, without being reminded.

**Pause during co-piloting:**

- When the user co-pilots on an architectural/specs decision, **ALL agents are paused**. Do not dispatch work based on unvalidated specs.

**Gating on co-piloting:**

- For significant arbitration (flow change, endpoint addition/removal, architectural changes), ask the user before validating. Don't decide alone.

**Non-negotiable API docs:**

- Every route must have API documentation with curl examples. Must have.

**Lead reviews quality:**

- The lead dev reviews structural quality (file size, anti-patterns, framework conformance), not just "it compiles and tests pass".

**Name the agents:**

- Each spawned agent has a clear name (`dev`, `po`, `designer`, `tester`, `seo`, etc.).

**Parallelize:**

- Always parallelize independent tasks. No sequential work when not necessary.

**Commit by the user only:**

- Agents don't commit or push. The lead doesn't either. They deliver, the lead reviews and verifies, then signals the user that the working tree is ready. The **user** commits and pushes.

## Typical feature process

1. The user expresses the need
2. The lead co-pilots with the user if needed (architecture, specs)
   → All agents paused during co-piloting
3. The PO defines the specs / functional mapping (communicated directly to the team)
4. The designer defines UI specs (wireframes, classes), communicated directly to the dev
5. The lead creates tasks with dependencies
6. The dev implements (based on PO + designer specs)
7. The tester challenges PO specs and defines the AC
8. The dev runs `/verif` on themselves
9. The lead reviews deliverables, refocuses on scope creep
10. The tester implements the tests (named after AC)
11. The designer reviews a11y / design
12. `/sync-docs` at end of session
13. The lead signals the working tree is ready — **the user commits and pushes** (never the lead)
