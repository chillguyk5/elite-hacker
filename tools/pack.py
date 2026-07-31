#!/usr/bin/env python3
"""Pack the elite-hacker skill collection into tool/IDE-specific distributions.

Source of truth: skills/<name>/SKILL.md (Anthropic Agent Skills layout).
Outputs: dist/<tool>/ with skill files placed where each tool discovers them.

Targets:
  codex        Codex CLI (~/.agents/skills/<name>/SKILL.md — verified on 0.145.0;
               legacy ~/.codex/skills is plugin-only) + AGENTS.md
  cursor       Cursor (.cursor/skills/<name>/SKILL.md) + AGENTS.md
  copilot      GitHub Copilot (.github/skills/<name>/SKILL.md) + AGENTS.md
  gemini       Gemini CLI (~/.gemini/skills/<name>/SKILL.md) + AGENTS.md
  cline        Cline (cline_docs/skills/<name>/SKILL.md) + AGENTS.md
  windsurf     Windsurf (.windsurf/skills/<name>/SKILL.md) + AGENTS.md
  aider        aider (.aider.skills.md — concatenated, one file)
  all          every target above

Usage:
  python tools/pack.py all [--out dist] [--overwrite]
  python tools/pack.py codex --out dist
"""
import argparse, json, os, re, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = os.path.join(ROOT, "skills")

DOTDIR = {
    "codex": ".agents/skills",
    "cursor": ".cursor/skills",
    "copilot": ".github/skills",
    "gemini": ".gemini/skills",
    "cline": "cline_docs/skills",
    "windsurf": ".windsurf/skills",
}
AGENTS = {t: "AGENTS.md" for t in DOTDIR}  # copied as-is into each pack


def skills_list():
    return sorted(
        d for d in os.listdir(SKILLS)
        if os.path.isdir(os.path.join(SKILLS, d))
        and os.path.isfile(os.path.join(SKILLS, d, "SKILL.md"))
    )


def validate(skill_dir):
    """Cheap per-skill sanity; full structural QA lives in tools/qa_check.py."""
    p = os.path.join(SKILLS, skill_dir, "SKILL.md")
    text = open(p, encoding="utf-8").read()
    if text.count("```") % 2:
        raise SystemExit(f"ERROR: {skill_dir} unbalanced code fences")
    fm = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not fm:
        raise SystemExit(f"ERROR: {skill_dir} bad frontmatter")
    for f in ("name", "description", "risk", "when-to-use"):
        if not re.search(rf"^{f}:", fm.group(1), re.M):
            raise SystemExit(f"ERROR: {skill_dir} missing frontmatter {f}")


def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(content)


def pack_dotdir(tool, out):
    """Anthropic-style SKILL.md per dir + AGENTS.md, under tool-specific dir."""
    dest = os.path.join(out, tool)
    for name in skills_list():
        validate(name)
        src = os.path.join(SKILLS, name, "SKILL.md")
        dst = os.path.join(dest, DOTDIR[tool], name, "SKILL.md")
        write_file(dst, open(src, encoding="utf-8").read())
    # root manifest for the tool's own docs/AGENTS discovery
    for fname in ("AGENTS.md", "README.md", "TOOLS.md"):
        write_file(os.path.join(dest, fname),
                   open(os.path.join(ROOT, fname), encoding="utf-8").read())
    if os.path.exists(os.path.join(ROOT, "skills.json")):
        shutil.copy(os.path.join(ROOT, "skills.json"), os.path.join(dest, "skills.json"))
    print(f"[{tool}] {len(skills_list())} skills -> {os.path.relpath(dest, ROOT)}")


def pack_aider(out):
    """aider: single concatenated markdown file with per-skill H1 headers."""
    parts = []
    for name in skills_list():
        validate(name)
        text = open(os.path.join(SKILLS, name, "SKILL.md"), encoding="utf-8").read()
        # strip frontmatter; make each skill an H1 section
        text = re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.S).lstrip()
        parts.append(f"# Skill: {name}\n\n{text}\n\n---\n")
    dest = os.path.join(out, "aider")
    write_file(os.path.join(dest, ".aider.skills.md"), "\n".join(parts))
    write_file(os.path.join(dest, "AGENTS.md"),
               open(os.path.join(ROOT, "AGENTS.md"), encoding="utf-8").read())
    print(f"[aider] {len(skills_list())} skills -> .aider.skills.md ({len(parts)} sections)")


def main():
    ap = argparse.ArgumentParser(description="Pack elite-hacker skills for tools/IDEs")
    ap.add_argument("target", choices=["all", *DOTDIR.keys(), "aider"],
                    help="pack target or 'all'")
    ap.add_argument("--out", default=os.path.join(ROOT, "dist"),
                    help="output directory (default: <repo>/dist)")
    ap.add_argument("--overwrite", action="store_true",
                    help="replace existing dist/<target>")
    args = ap.parse_args()

    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)

    targets = list(DOTDIR.keys()) + ["aider"] if args.target == "all" else [args.target]
    for t in targets:
        dest = os.path.join(out, t)
        if os.path.exists(dest) and not args.overwrite:
            print(f"[{t}] SKIP: {os.path.relpath(dest, ROOT)} exists (use --overwrite)")
            continue
        if t == "aider":
            pack_aider(out)
        else:
            pack_dotdir(t, out)
    print("done.")


if __name__ == "__main__":
    main()
