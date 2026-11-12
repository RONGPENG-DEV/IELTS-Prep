# English learning skills

Use the existing checkout; cloud tasks are isolated, so do not create worktrees unless requested.

Five repository-local skills live under `.agents/skills/` (relative links into `vendor/`). Read the selected SKILL.md when requested. Use explicit user intent to select one skill; do not apply all coaches at once.

- language-learning: general language learning plans.
- english-coach: conversational English corrections.
- english-practice: Chinese interview leading to English speaking notes.
- shadowing-practice: shadowing plans and practice scripts.
- immersion-reader: static English reading lessons.

Run `bash scripts/setup-skills.sh` once in a fresh checkout. Use the root `.venv/bin/python` for immersion-reader scripts. Follow `vendor/english-immersion-reader/AGENTS.md` before creating reading lessons. Keep generated lessons, private transcripts, databases, and learner history out of Git.

For immersion-reader, resolve the skill symlink to the vendor repository; run commands in `vendor/english-immersion-reader`. Its online Edge TTS implementation clears proxy variables. Do not run online synthesis in this cloud until it supports preserving the supplied proxy and TLS trust. Static compilation and TTS dry-run are available. Browser UI and online audio are not covered by setup validation.

Claude-only slash commands may not exist in Codex; invoke skills by name. Skills do not imply audio input or pronunciation scoring capability. Use `~/.english-practice/` for the upstream speaking template and learning history; do not invent a learner profile.
