#!/usr/bin/env python3
"""QA check for elite-hacker skill collection: structure, cross-refs, routing."""
import os, re, sys, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = os.path.join(ROOT, "skills")
errors, warnings = [], []

def err(msg): errors.append(msg)
def warn(msg): warnings.append(msg)

# --- 1. Directory / frontmatter structure ---
dirs = sorted(os.listdir(SKILLS))
skill_ids = set()
for d in dirs:
    p = os.path.join(SKILLS, d)
    if not os.path.isdir(p):
        continue
    sm = os.path.join(p, "SKILL.md")
    if not os.path.exists(sm):
        err(f"{d}: missing SKILL.md"); continue
    text = open(sm, encoding="utf-8").read()
    # frontmatter
    if not text.startswith("---"):
        err(f"{d}: missing frontmatter")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        err(f"{d}: frontmatter not closed"); continue
    fm = m.group(1)
    for field in ("name", "description", "risk", "when-to-use"):
        if not re.search(rf"^{field}:", fm, re.M):
            err(f"{d}: missing frontmatter field '{field}'")
    name_m = re.search(r"^name:\s*(\S+)", fm, re.M)
    if name_m:
        sid = name_m.group(1)
        skill_ids.add(sid)
        if sid != d:
            err(f"{d}: frontmatter name '{sid}' != dir name")

# --- 2. Cross-reference validity: Xn refs and (X) refs ---
LETTERS = {c: s for s in os.listdir(SKILLS) for c in [""]}  # placeholder
ALLOWED = {}  # letter -> set of section numbers
def sec_nums(s):
    return {int(n) for n in re.findall(r"^## (\d+)\.", s, re.M)}

for d in dirs:
    p = os.path.join(SKILLS, d, "SKILL.md")
    if not os.path.exists(p): continue
    text = open(p, encoding="utf-8").read()
    nums = sec_nums(text)
    if not nums: err(f"{d}: no numbered sections")
    ALLOWED[d] = nums

# letter map from README A4 table (letter -> skill dir) — parse README
readme = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
letter_map = {}
for m in re.finditer(r"\|\s*([A-Z])\s*\|\s*([a-z0-9-]+)\s*\|", readme):
    if m.group(1) in "ABCDEFGHIJKLMNOPQRSTUVWX" and m.group(2) in set(os.listdir(SKILLS)):
        letter_map[m.group(1)] = m.group(2)

for d in dirs:
    p = os.path.join(SKILLS, d, "SKILL.md")
    if not os.path.exists(p): continue
    text = open(p, encoding="utf-8").read()
    body = text
    # numbered refs like F1, G3 (word boundary, followed by non-letter)
    for m in re.finditer(r"(?<![A-Za-z0-9])([A-Z])(\d+)(?![A-Za-z0-9])", body):
        let, num = m.group(1), int(m.group(2))
        if let == "A":
            continue  # README sections A1-A6, not a skill
        if let not in letter_map:
            warn(f"{d}: ref to unknown letter '{let}'"); continue
        # known false-positive contexts:
        if let == "F" and num in (4, 7, 8, 9):
            continue  # function keys (x64dbg F4/F7/F8/F9, Windows boot F8)
        if d == "runtime-hooking" and let in ("X", "R") and num in (0, 7, 8, 9, 30, 86):
            continue  # ARM64/ARM32 registers X0/X7/X8/X30, R0/R7/R8/R9, UC_ARCH_X86
        if d == "web-api-pentest" and let in ("P", "C") and 0 <= num <= 9:
            continue  # P0-P7 phase map and C1-C5 attack-tree labels
        target = letter_map[let]
        tnums = ALLOWED.get(target, set())
        if num not in tnums:
            warn(f"{d}: ref {let}{num} -> '{target}' has no section {num} (sections: {sorted(tnums)})")
    # bare letter refs like (F), (I) — must be known letters
    for m in re.finditer(r"\(([A-Z])\)", body):
        let = m.group(1)
        if let not in letter_map and let != "X":
            warn(f"{d}: bare letter ref '({let})' unknown")
        # cross-file refs like (E/.NET)
    # intra-file self refs like (P4) in anti-analysis — skip (already covered)

# --- 3. README matrix / legend consistency ---
for row_letter in "BCDEFGHIJKLMNOPQRSTUVWX":
    if row_letter not in letter_map:
        warn(f"README A4: letter {row_letter} not mapped to a skill")
# every skill dir appears in letter_map
for d in dirs:
    if d not in letter_map.values():
        err(f"README: skill '{d}' missing from A4 letter map")

# --- 4. Code fences balanced in every md ---
for f in glob.glob(os.path.join(ROOT, "**/*.md"), recursive=True):
    text = open(f, encoding="utf-8").read()
    if text.count("```") % 2 != 0:
        err(f"{os.path.relpath(f, ROOT)}: unbalanced ``` fences ({text.count('```')})")

# --- 5. No stale references ---
for f in glob.glob(os.path.join(ROOT, "skills/*/SKILL.md")):
    text = open(f, encoding="utf-8").read()
    if "Authorization gate" in text:
        err(f"{f}: stale 'Authorization gate' text")

print(f"skills dirs: {len(dirs)}, letters mapped: {len(letter_map)}")
print(f"\nERRORS ({len(errors)}):")
for e in errors: print("  -", e)
print(f"\nWARNINGS ({len(warnings)}):")
for w in warnings: print("  -", w)
sys.exit(1 if errors else 0)
