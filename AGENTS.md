# AGENTS.md — Elite Hacker Skills Collection

This repository is a **portable skill collection** for AI coding agents. It follows the Anthropic Agent Skills layout (`skills/<name>/SKILL.md`) — the de-facto standard — plus a packer that adapts the source skills to other agents and IDEs.

## How skills are structured

- Source of truth: `skills/<name>/SKILL.md` — one directory per skill, always named `SKILL.md`.
- Frontmatter (YAML): `name`, `description`, `risk` (`offensive`/`defensive`), `when-to-use` (routing hints).
- Skills are self-contained and loadable per phase; cross-reference each other with `{letter}{section}` (e.g. `F1` = runtime-hooking §1). The letter↔skill map lives in README A4.
- Tool names/versions/status: single source of truth in `TOOLS.md` — check it before assuming a CLI's flags.

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
2. Cross-references use the `{letter}{section}` scheme (README A4); new skills get a new letter + a README A1/A4 row.
3. Check tool status in `TOOLS.md` before adding new commands.
4. Run `python tools/qa_check.py` before committing (structure, frontmatter, cross-refs, fences).
5. Keep the packer and all tools working — `python tools/pack.py all` must succeed.
6. English, imperative, terse: one skill ≈ 60-400 lines, one anti-patterns section at the end.
