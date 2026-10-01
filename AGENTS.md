# AI-film repository conventions

- This is the standalone production project. Do not import code, assets, credentials or data from unrelated workspaces.
- Keep implemented features distinct from roadmap items. Never call templates verified model profiles or synthetic fixtures generated film assets.
- Preserve original screenplay text. Source units, semantic beats, shots, inputs, takes and reviews are separate records.
- Do not mark a shot accepted based on a prompt, successful upload or provider status. Require full-clip review evidence for all assigned beats and criteria.
- Preserve canonical asset versions. Changes must invalidate dependent outputs; do not silently discard references to satisfy model limits.
- Keep portable mode useful without credentials. Tool-specific limits require current official documentation or a dated direct verification.
- Execute routine planning and reversible implementation within user scope. Escalate material creative contradictions with a concrete recommendation, not routine choices.
- The CLI is single-writer per project. Preserve atomic state writes and the project lock in new mutations.
- Run `python3 -m unittest discover -s tests -v` and `python3 -m compileall -q aifilm` for core changes. Media tests need FFmpeg.
- Keep production projects/exports out of commits. Use synthetic fixtures for tests and clearly label them.
