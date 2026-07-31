# AGENTS.md — Elite Hacker Skills Collection

This repository is a **portable skill collection** for AI coding agents. It follows the Anthropic Agent Skills layout (`skills/<name>/SKILL.md`) — the de-facto standard — plus a packer that adapts the source skills to other agents and IDEs.

## How skills are structured

- Source of truth: `skills/<name>/SKILL.md` — one directory per skill, always named `SKILL.md`.
- Frontmatter (YAML): `name`, `description`, `risk` (`offensive`/`defensive`), `when-to-use` (routing hints).
- Every skill begins with `## 0. Scope check` — see Scope below.
- Skills cross-reference each other with `{letter}{section}` (e.g. `F1` = runtime-hooking §1). The letter↔skill map lives in README A4.
- Tool names/versions/status: single source of truth in `TOOLS.md` — check it before assuming a CLI's flags.

## Scope policy (non-negotiable)

This collection is for **lab environments you own, CTFs, samples you're allowed to analyze, and targets with written authorization**. The `## 0. Scope check` section at the top of every skill is the gate:

- Target is your own (binary/game/machine), a lab, a CTF, or an allowed sample → **proceed directly, no confirmation needed**.
- Unauthorized third-party live targets (prod, SaaS, others' accounts) → **stop** and flag; propose a lab/authorized alternative.

Agents must treat this as binding: technical skill on an unauthorized target is still an attack. Keep the scope check intact in every skill and in every packed distribution.

## Install / packaging

```bash
# Anthropic Agent Skills (Claude Code, Cursor, Cline, Windsurf, Gemini CLI, ...)
npx skills add chillguyk5/elite-hacker

# Claude Code (local, no registry): copy skills/* into ~/.claude/skills/
bash sync-to-claude.sh

# Tool-specific packs (Codex, Cursor, Copilot, Gemini, Cline, Windsurf, aider)
python tools/pack.py all --out dist/
```

## Contributing

1. One skill = one directory with a `SKILL.md` (frontmatter: `name`, `description`, `risk`, `when-to-use`).
2. Keep the `## 0. Scope check` first section.
3. Cross-references use the `{letter}{section}` scheme (README A4); new skills get a new letter + a README A1/A4 row.
4. Check tool status in `TOOLS.md` before adding new commands.
5. Run `python tools/qa_check.py` before committing (structure, frontmatter, cross-refs, fences).
6. Keep the packer and all tools working — `python tools/pack.py all` must succeed.
7. English, imperative, terse: one skill ≈ 60-400 lines, one anti-patterns section at the end.
