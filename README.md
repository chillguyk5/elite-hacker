# Elite Hacker — Offensive Security & Reverse Engineering Skills

A collection of self-contained offensive security + reverse engineering skills for AI coding agents. Each skill is an independent `SKILL.md` in `skills/` (Anthropic Agent Skills layout), loadable individually.

## Install

### Any agent (Anthropic Agent Skills registry — Claude Code, Cursor, Cline, Windsurf, Gemini CLI, ...)

```bash
npx skills add chillguyk5/elite-hacker          # whole collection
npx skills add chillguyk5/elite-hacker --skill web-api-pentest   # single skill
```

### Claude Code (local, no registry)

Copy each skill directory from `skills/` into `~/.claude/skills/` (one dir per skill) so agent discovery picks them up. Re-sync anytime with:

```bash
bash sync-to-claude.sh
```

### Other CLIs and IDEs (packed distributions)

The repo ships a packer that generates tool-specific layouts — each pack contains the same 23 skills plus `AGENTS.md`, `README.md`, `TOOLS.md`:

```bash
python tools/pack.py all          # → dist/{codex,cursor,copilot,gemini,cline,windsurf,aider}
python tools/pack.py codex        # one target only (--out <dir> to relocate)
```

| Tool / IDE | Pack location | Layout |
|------------|---------------|--------|
| Codex CLI | `dist/codex` | `.agents/skills/<name>/SKILL.md` (verified on 0.145.0) + `AGENTS.md` |
| Cursor | `dist/cursor` | `.cursor/skills/<name>/SKILL.md` + `AGENTS.md` |
| GitHub Copilot | `dist/copilot` | `.github/skills/<name>/SKILL.md` + `AGENTS.md` |
| Gemini CLI | `dist/gemini` | `.gemini/skills/<name>/SKILL.md` + `AGENTS.md` |
| Cline | `dist/cline` | `cline_docs/skills/<name>/SKILL.md` + `AGENTS.md` |
| Windsurf | `dist/windsurf` | `.windsurf/skills/<name>/SKILL.md` + `AGENTS.md` |
| aider | `dist/aider` | single `.aider.skills.md` (23 sections) + `AGENTS.md` |

Copy the matching `dist/<tool>/` contents into the tool's home directory (e.g. `~/.agents/`, `~/.cursor/`, `.github/` at repo root, `~/.gemini/`). Verify the tool's current skill-path conventions when in doubt — Codex 0.145+ scans `~/.agents/skills` (not `~/.codex/skills`), and its default 2% skills context budget may hide skills on machines with many installed; raise `skills_context_budget` (root-level key in `~/.codex/config.toml`) if needed.

## Skills

- **web-api-pentest** - Web/API pentest: recon, auth bypass, quota/money bugs, injection/SSRF, exploit chains, AI-gateway playbook.
- **ai-agent-pentest** - AI/agent pentest: prompt injection (direct/indirect), tool-abuse/function-call smuggling, RAG poisoning, MCP attacks, OWASP LLM Top 10.
- **web-client-re** - Deobfuscate obfuscated/minified JavaScript (Babel AST, string-array, control-flow flattening), reverse WASM (wasm2wat/wasm-decompile), automate browsers via DevTools Protocol.
- **binary-re** - Reverse native binaries: symbol/struct recovery from stripped binaries, IDAPython/IDALib scripting, Ghidra scripting and headless batch analysis.
- **dotnet-re** - Reverse .NET assemblies: dnSpyEx decompile/edit/debug, de4dot/de4dotEx deobfuscation, dnlib programmatic patching, Harmony runtime hooks.
- **runtime-hooking** - Runtime instrumentation: Frida hooks (native/ObjC/Java, module-load timing), Unicorn offline emulation of code fragments with environment simulation.
- **dynamic-debug** - Dynamic debugging: x64dbg, WinDbg with Time Travel Debugging, anti-debug bypass, static-dynamic coordination, unpack dump + IAT fix.
- **mobile-re** - Mobile RE: Android DEX dumping from packed apps, iOS app decryption (uncrack), Unity IL2CPP symbol extraction for IDA/Ghidra.
- **cracking-patching** - Crack native binaries: DLL proxy, binary branch patching, license/trial/nag bypass, keygen serial algorithm reversal.
- **game-hacking** - Game hacking: Cheat Engine value/pointer/struct scanning, Auto Assemble code injection, mobile Unity IL2CPP Frida hooking, client vs server side.
- **network-protocol-re** - Network/protocol RE: traffic capture, TLS keylog decryption, custom binary protocol parsing, replay and fuzzing, MITM with cert-pinning bypass.
- **osint-recon** - OSINT & recon: subdomains/cert transparency, GitHub dorking, breached-creds lookups, metadata, search dorks, active recon, tooling.
- **cloud-sec** - Cloud security (AWS/GCP/Azure): misconfiguration discovery, IAM over-privilege, SSRF-to-IMDS, storage bucket enumeration, serverless, lab tooling.
- **container-k8s-sec** - Container & Kubernetes security: image analysis, Docker escape (lab), k8s RBAC abuse, service-account tokens, kubelet API, supply chain/SBOM.
- **elf-linux-re** - ELF/Linux RE: readelf/objdump/radare2 analysis, stripped symbol recovery, LD_PRELOAD runtime hooking, Linux malware persistence basics.
- **malware-analysis** - Malware analysis: lab setup (FlareVM/REMnux), static triage, sandbox detonation, YARA rules, persistence mapping, safety practices.
- **kernel-driver-re** - Kernel/driver RE: Windows WDM/WDF IRP and IOCTL mapping, kernel debugging, rootkit technique identification, Linux LKM hooking.
- **firmware-re** - Firmware/UEFI RE: binwalk/unblob extraction, UEFITool firmware volume parsing, DXE/SMM analysis, bootkits, IoT and console firmware.
- **anti-analysis** - Anti-analysis & packers: anti-VM/anti-debug/anti-emulation bypass, unpacking workflow (OEP + IAT), VMProtect/Themida/Enigma, API-hash reconstruction.
- **blockchain-re** - Blockchain/smart-contract RE: EVM disassembly, bytecode decompilation, storage-slot layout recovery, reentrancy/overflow/access-control patterns.
- **pcap-forensics** - Network forensics (defensive): beacon analysis, TLS fingerprinting (JA3/JA4), DNS tunneling, C2 pattern detection, IOC extraction, Zeek/Suricata.
- **lab-env** - Lab environment & toolchain: isolation model, winget/pipx/cargo bootstrap, smoke tests, VM quickstarts (Windows RE, malware, kernel debug, mobile, EVM).
- **offensive-methodology** - Offensive methodology: round output format, pentest report template, attack trees, anti-patterns, cross-capability combos for chaining skills.

Tool versions / maintenance status: **[TOOLS.md](TOOLS.md)**.

## Capability routing

## A1. Ability Matrix — route by target type

| # | Capability | Use when | Section |
|---|------------|----------|---------|
| 1 | **Web/API Pentest** | Web app, API gateway, OAuth, subscription/payment | B |
| 2 | **AI/Agent Pentest** | LLM apps, agents, RAG, MCP servers, prompt injection | S |
| 3 | **Web Client-Side RE** | Obfuscated/minified JS, WASM modules, browser logic | C |
| 4 | **RE Static — Native Binary** | Stripped binary, need symbols/structs, IDA/Ghidra/IDAPython | D |
| 5 | **RE Static — .NET** | Managed assembly (EXE/DLL .NET, Unity Mono games) | E |
| 6 | **RE Dynamic** | Runtime hooking, offline emulation, arg/return tracing | F |
| 7 | **Dynamic Debug** | Prove runtime behavior, anti-debug, crash dumps, TTD | G |
| 8 | **Mobile** | Android/iOS apps, packed DEX, Unity IL2CPP | H |
| 9 | **Cracking & Patching** | License/trial bypass, DLL proxy, keygen, binary patch | I |
| 10 | **Game Hacking** | PC/mobile games: Cheat Engine, pointer scan, struct, hooks | J |
| 11 | **Network/Protocol** | Traffic capture, TLS decryption, custom protocols, fuzzing, MITM | K |
| 12 | **OSINT/Recon** | Engagement start: subdomains, CT logs, GitHub dorking, dorks | V |
| 13 | **Cloud Security** | AWS/GCP/Azure: buckets, IAM, SSRF→IMDS, serverless | T |
| 14 | **Container/K8s** | Docker images, escape (lab), k8s RBAC, SA tokens | U |
| 15 | **ELF/Linux RE** | Linux binaries, shared objects, Linux malware | L |
| 16 | **Malware Analysis** | Suspicious samples: triage, sandbox, YARA, persistence | M |
| 17 | **Kernel & Driver RE** | Windows drivers (WDM/WDF), rootkits, kernel debugging | N |
| 18 | **Firmware & UEFI RE** | UEFI modules, firmware images, bootkits, IoT/console | O |
| 19 | **Anti-Analysis & Packers** | VMProtect/Themida, custom packers, anti-VM/anti-emulation | P |
| 20 | **Blockchain / Smart-Contract RE** | EVM bytecode, contract decompilation, storage analysis | Q |
| 21 | **Network Forensics** | Defensive: beacons, JA3/JA4, DNS tunneling, IOCs | W |
| 22 | **Lab Environment** | Fresh machine: isolation, toolchain bootstrap, smoke tests | X |
| 23 | **Methodology** | Output format, reporting, attack trees, anti-patterns | R |

## A2. Decision Flow

```
What is the target?
├── URL / API / web app ──────────────→ B (Web/API Pentest)
├── LLM app / AI agent / MCP ─────────→ S (AI/Agent Pentest)
├── Cloud account (AWS/GCP/Azure) ────→ T (Cloud Security)
├── Container / k8s cluster ──────────→ U (Container/K8s)
├── Any target, start of engagement ──→ V (OSINT/Recon) → route
├── Web JS bundle / WASM ─────────────→ C (Client-Side RE)
├── EXE/DLL (native) ─────────────────→ PE type check
│   ├── .NET managed ────────────────→ E (.NET/dnSpyEx)
│   └── native, packed? ─────────────→ unpack (I/P) → D (RE static) → F/G (dynamic)
├── ELF / .so / Linux binary ─────────→ L (ELF/Linux RE)
├── Mobile app (APK/IPA) ─────────────→ H (Mobile) → F (Frida)
├── Game ─────────────────────────────→ J (Game Hacking) + H (Unity/IL2CPP)
├── Network packets / TLS / protocol ─→ K (Network/Protocol) / W (PCAP forensics, defensive)
├── Packed/protected binary ──────────→ P (Anti-Analysis) → unpack → D/F
├── Driver / kernel / rootkit ────────→ N (Kernel & Driver RE)
├── Firmware / UEFI image ────────────→ O (Firmware & UEFI RE)
├── Malware sample ───────────────────→ M (Malware Analysis)
├── Smart-contract / EVM bytecode ────→ Q (Blockchain RE)
└── Closed-source app with license ───→ I (Cracking/Patching)

Fresh machine / no toolchain → X (Lab Environment) first.
```

## A3. Combined Workflow (all RE/offensive branches)

```
Binary target
  → IDA/MCP available? → symbol/struct recovery (D1-D2) — white-box
  → Android mobile? → DEX dump (H1) → jadx/apktool → Frida (F1)
  → iOS mobile? → iOS dump 砸壳 (H2) → IDA/Hopper → Frida (F1)
  → Unity IL2CPP? → IL2CPP dump (H3) → IDA + symbol recovery
  → .NET? → dnSpyEx edit C#/IL (E) → de4dotEx if obfuscated
  → No IDA / batch / firmware? → Ghidra headless (D4)
  → Need offline emulation? → Unicorn (F2)
  → Need runtime proof? → x64dbg/WinDbg breakpoints (G) → patch/hook/keygen
  → License bypass? → DLL proxy / binary patch / keygen (I)
  → Game? → CE scan → pointer → struct → AA inject / Frida hook (J)
  → Custom network protocol? → capture → decrypt TLS → parse → fuzz/replay (K)
  → Linux ELF? → readelf/objdump/radare2 (L) → hook via LD_PRELOAD
  → Suspicious sample? → sandbox triage + YARA (M)
  → Packed/protected? → anti-analysis + unpack (P)
  → Driver/kernel? → IRP/IOCTL mapping + kernel debug (N)
  → Firmware? → binwalk/UEFITool extract → Ghidra (O)
  → EVM bytecode? → disassemble → decompile → storage layout (Q)
  → LLM app/agent? → injection → tool abuse → MCP (S)
  → Cloud account? → buckets → IAM → IMDS chain (T)
  → Container/pod → image analysis → SA token → RBAC → API (U)
  → Malicious traffic? → beacons → JA3 → IOCs (W)
```

## A4. Cross-skill reference scheme (letter.section)

Skills reference each other as `{capability-letter}{section-number}` — e.g. `F1` = runtime-hooking §1 (Frida), `G3` = dynamic-debug §3 (anti-debug bypass), `I1` = cracking-patching §1 (DLL proxy), `P4` = anti-analysis §4 (API-hash reconstruction).

| Letter | Skill | `#1` = | `#2` = | `#3` = | `#4` = |
|--------|-------|--------|--------|--------|--------|
| B | web-api-pentest | Mindset | Phase Map | Exploit chains | New-API playbook |
| C | web-client-re | JS deobfuscation | WASM RE | DevTools automation | — |
| D | binary-re | Symbol recovery | Structure recovery | IDAPython/IDALib | Ghidra/headless |
| E | dotnet-re | dnSpyEx | Obfuscation/de4dot | dnlib patch | Harmony hooks |
| F | runtime-hooking | Frida | Unicorn emulation | — | — |
| G | dynamic-debug | x64dbg | WinDbg/TTD | Anti-debug bypass | Static↔dynamic |
| H | mobile-re | DEX dump | iOS decrypt | IL2CPP dump | — |
| I | cracking-patching | DLL proxy | Binary patch | License/trial/nag | Keygen |
| J | game-hacking | CE scan | Pointer scan | Struct dissect | Code injection |
| K | network-protocol-re | Capture | Filtering | TLS decrypt | Protocol RE |
| L | elf-linux-re | ELF structure | Tooling | Symbol recovery | LD_PRELOAD |
| M | malware-analysis | Lab setup | Static triage | Sandbox | YARA |
| N | kernel-driver-re | WDM/WDF | Kernel debug | Rootkit techniques | Linux LKM |
| O | firmware-re | Extraction | UEFI modules | Bootkits | IoT/console |
| P | anti-analysis | Anti-analysis classes | Unpacking | Commercial protectors | API hashing |
| Q | blockchain-re | EVM model | Disassemble | Decompilers | Storage layout |
| R | offensive-methodology | Output format | Report template | Anti-patterns | Continue flow |
| S | ai-agent-pentest | Prompt injection | Tool abuse | RAG/poisoning | MCP attacks |
| T | cloud-sec | Attack surface | Buckets | IAM | SSRF→IMDS |
| U | container-k8s-sec | Image analysis | Docker escape | k8s from inside | k8s from outside |
| V | osint-recon | Subdomains | GitHub dorking | Search dorks | Breach/metadata |
| W | pcap-forensics | Flow stats | Beacons | TLS/JA3 | DNS tunnel/IOC |
| X | lab-env | Isolation | Bootstrap | Smoke tests | VM quickstarts |

## A5. Operating notes

Skills run as-is on live targets; keep noise low, revert state after proof, and report impact with evidence.

---

## A6. Agent usage — how to run these skills with an AI coding agent

Skills are markdown instructions loaded into an agent context. Scale the agent setup to the task, and **load only the skills a phase needs** (all 23 skills ≈ 3,000 lines — too much for one context).

| Task size | Setup |
|-----------|-------|
| Single skill, small task (hook one function, patch one binary, decompile one contract) | **Main loop only** — load the one skill directly; no subagents |
| Single skill, long task (fuzz a protocol, RE a large binary, full engagement) | **1 subagent** with that skill — keeps dump/disassembly noise out of the main context |
| Multi-skill chain (mobile app → dump → Frida → API pentest) | **Orchestrator (main loop) + 1 subagent per phase**, each loading the 1-2 skills of its phase; orchestrator holds intermediate results and routes via A2 |

### Recommended agent roles (capability bundles)

| Role | Skills | Used for |
|------|--------|----------|
| RE workstation | D (binary-re), F (runtime-hooking), G (dynamic-debug) | native/ELF/.NET reverse engineering |
| Mobile | H (mobile-re), F (runtime-hooking) | Android/iOS, Unity IL2CPP |
| Web | B (web-api-pentest), C (web-client-re), R (offensive-methodology) | web/API engagements |
| Cloud/native | T (cloud-sec), U (container-k8s-sec), V (osint-recon) | cloud, k8s, recon phases |
| Defensive | W (pcap-forensics), M (malware-analysis) | IR, malware, network forensics |
| All roles | X (lab-env) once, at bootstrap | toolchain + isolation |

### Operational notes

1. **Bootstrap once:** run X (lab-env) in a fresh session/machine first — agents are only as reliable as the installed toolchain; smoke tests in X §3.
2. **Tool versions live in TOOLS.md** — check it before assuming a tool's CLI/flags; pin personal-repo tools (e.g. `panda-dex-dumper`) to a commit in lab-env.
3. **MCP over exports:** prefer tool MCP servers (e.g. `ida-pro` MCP in D) over file-export workflows — direct tool access beats exported dumps.
4. **Each subagent gets one outcome contract:** target + skill + expected output (report/PoC/symbols) + files it may touch. The orchestrator verifies, never the subagent itself.
5. **Output contract:** each subagent returns a PoC with raw evidence (response/log/diff) + next steps; the orchestrator verifies, never the subagent itself.

## Contributing

- One skill = one directory with a `SKILL.md` (frontmatter: `name`, `description`, `risk`, `when-to-use`).
- Cross-references use the `{letter}{section}` scheme documented in A4.
- Check tool status in TOOLS.md before adding new commands.
- Run the QA check before committing: `python .qa_check.py`.
