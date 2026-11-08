# REA (vendored guide)

Source: [morluto/rea](https://github.com/morluto/rea) at commit `b81da90`, MIT © 2026 morluto (`LICENSE`). Imported at the owner's request on 2026-11-08 for the `marich` agent.

- `reverse-engineer-anything/` is REA's own agent skill (`SKILL.md` and `references/`), copied unchanged. Marich reads it by section when a job needs binary, app or runtime analysis.
- `DISCLAIMER.md` is REA's responsible-use policy. Marich follows it on every job.
- The REA MCP server itself (`npx rea-agents setup`, Ghidra and friends) is **not** installed here. The cloud session's classifier refuses `npx` packages, and its network blocks most hosts. The owner can install REA on their own computer; without it, Marich works from files, frames, audio and public pages.
