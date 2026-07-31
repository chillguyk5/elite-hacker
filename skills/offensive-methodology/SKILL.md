---
name: offensive-methodology
description: "Offensive methodology: round output format, pentest report template, attack trees, anti-patterns, cross-capability combos for chaining skills."
risk: offensive
when-to-use: "Use when: orchestrating multi-skill engagements — output format, report template, attack trees, cross-skill combos. Not when: single narrow task (load that skill directly)."
---

# Offensive Methodology

## 1. Output format (per round)

1. **Round goal** (one line)
2. **Hypothesis**
3. **PoC** (full command/payload)
4. **Result** (raw/summary)
5. **Impact**
6. **Next** (1-3 steps)

Bug table: `ID | Severity | Live? | Free money/Admin? | Condition`

## 2. Report template

```markdown
## Meta
- Target: / Date: / Version/Fingerprint: / Auth level achieved: / Tester:

## Executive summary (3-5 bullets)

## Asset inventory
| Asset | Value | Notes |   (Accounts / API keys / Sessions / Admin OSINT)

## Vulnerabilities
### VULN-XX — Title
- Severity: Critical/High/Medium/Low   - Live: Yes/No/Conditional
- Endpoint:  - Auth required:
- Description:  - PoC:  - Impact:  - Remediation:  - Source ref: (file:line)

## Exploit chains
1. 2.

## Dead ends (do not retest blindly)
| Path | Why dead |

## Recommendations (priority)
1. 2.

## Appendix
- Commands log  - Timeline
```

## 3. Anti-patterns (Web/API)

- Stop at "Invalid parameters" without trying the JSON-file form
- Treating an SPA 200 HTML as an open API (check pprof/.env fallbacks)
- Treating `success:true` mass-assign as escalation (re-read self)
- Treating `root_init:false` as uninitialized when `status:true` (JSON zero-value)
- Bruting without tracking 429
- Reporting free credit from merely listing models

## 4. When the user says "continue" / "bug X"

1. Read state: auth? quota? role? payment on?
2. Pick the highest-ROI still-open chain (web-api-pentest §6 decision matrix / §7 ROI priority)
3. Execute the PoC immediately — no essays unless asked
4. Update the bug table + dead ends

## 5. Cross-map — capability combos

| Situation | Combo |
|-----------|-------|
| Stripped binary + need runtime PoC | D1 (symbols) → G (bp proof) → I (patch/keygen) |
| Mobile app calling custom API | H1/H2 (dump) → F1 (hook crypto/TLS) → K (capture) → B (API pentest) |
| Unity game with light anti-cheat | H3 (IL2CPP) → F1 (hook by RVA, timing-aware) |
| Obfuscated .NET + online license | E (dnSpy → de4dot) → K (block online verify) → I |
| Unknown protocol + server crash | K4 (parse) → K5 (fuzz) → G (attach server) |
| Firmware blob + crypto routine | O (extract) → D4 (Ghidra) → F2 (Unicorn emulate) → D1 |
| Packed sample + need IAT | P (unpack, OEP) → G1 (Scylla dump + IAT) |
| Linux ELF + LD_PRELOAD hook | L4 → F1 (Frida on Linux) |
| Malware sample → C2 intel | M2 (triage) → M3 (sandbox) → K (beacon analysis) |
| Driver → IOCTL surface | N1 (dispatch map) → G2 (kernel debug) |
| Smart-contract reentrancy | Q3 (decompile) → Q4 (storage) → Q5 (CALL-order proof) |
| Web JS auth logic | C1 (deobfuscate) → C3 (DevTools automate) → B |
