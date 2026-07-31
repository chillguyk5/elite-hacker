# Tool Matrix (2026-07)

Single source of truth for tool versions / maintenance status. When a skill names a tool, check here for the recommended build and fallback. Status: **active** (maintained), **legacy** (maintained / works but old), **dead** (unmaintained — use the recommended alternative).

## Static analysis / disassemblers

| Tool | Status | Notes / recommended build | Fallback |
|------|--------|---------------------------|----------|
| IDA Pro | active | 9.x; IDAPython + IDALib (headless, 9.0+) | Ghidra |
| Ghidra | active | NSA, free; Jython scripting + headless `analyzeHeadless` | — |
| radare2 / rizin | active | rizin is the active fork of radare2 | the other |
| dnSpy | dead | original repo archived 2020 | **dnSpyEx** (active fork, v6.6.x) |
| dnSpyEx | active | github.com/dnSpyEx/dnSpy — drop-in dnSpy replacement | ILSpy (read-only) |
| ILSpy | active | read-only decompiler; CLI: `ilspycmd` | dnSpyEx |
| dotPeek | active | JetBrains free decompiler | dnSpyEx |
| de4dot | dead | last release ~2021; only handles legacy obfuscators (ConfuserEx, old Eazfuscator/Dotfuscator, old .NET Reactor) | **de4dotEx** (fork), manual dnlib |
| de4dotEx | active | github.com/tsautier/de4dotEx — maintained fork, improved unpacking | dnlib (manual) |
| dnlib | active | programmatic assembly read/write (patch) | Mono.Cecil |
| HxD / 010 Editor | active | hex editors | CFF Explorer |
| CFF Explorer / PE-bear | active | PE parsing/edit | pefile (Python) |

## Dynamic / debugging

| Tool | Status | Notes | Fallback |
|------|--------|-------|----------|
| x64dbg | active | 64-bit debugger; ScyllaHide plugin for anti-debug | OllyDbg (32-bit legacy) |
| WinDbg | active | WinDbg (new UI) + Time Travel Debugging; SOS for .NET | x64dbg (user-mode) |
| ScyllaHide | active | anti-anti-debug plugin | TitanHide |
| Frida | active | 16.x (2025+); API is stable across recent versions; iOS jailbreak counterpart: frida-server | objection (wrapper) |
| Unicorn | active | CPU emulation framework (bindings: Python/Rust/Go) | Qiling (framework wrapper) |
| Cheat Engine | active | 7.5+; Auto Assemble, pointer scan | — |
| Scylla | active | import reconstruction / dump fixing | — |

## Unpacking / malware

| Tool | Status | Notes | Fallback |
|------|--------|-------|----------|
| UPX | active | `upx -d` for UPX-packed | manual OEP/IAT |
| DIE (Detect It Easy) | active | packer/protector identification | PEiD (legacy) |
| capa | active | FLARE capability signatures | — |
| unpac.me | active | online unpacking service — **upload only samples you own/are authorized for** | local x64dbg dump |
| Procmon | active | Sysinternals process monitor | — |
| FakeNet-NG | active | network simulation for malware | INetSim |
| CAPE sandbox | active | open-source (Cuckoo successor) | ANY.RUN (SaaS) |
| YARA | active | 4.x; `yara` CLI + `yara-python` | — |

## Mobile

| Tool | Status | Notes | Fallback |
|------|--------|-------|----------|
| jadx | active | DEX → Java decompiler | CFR / jadx-gui |
| apktool | active | resource + smali decode/rebuild | — |
| Il2CppDumper (Perfare) | legacy | supports Unity ≤ 2021 (metadata v29) | **il2cpp_dumper (Rust)** for newer metadata |
| Il2CppDumper (roytu v39) | active | Unity 6.x (metadata v39) | Rust `il2cpp_dumper` when metadata version outruns v39 |
| il2cpp_dumper (Rust) | active | crates.io/cargo; handles newer metadata versions | — |
| frida-ios-dump | active | iOS decryption (jailbreak); pin a recent commit | — |
| objection | active | mobile runtime exploration wrapper | Frida scripts |
| class-dump | legacy | Objective-C header extraction; still works | Ghidra/IDA auto-analysis |

## Network

| Tool | Status | Notes | Fallback |
|------|--------|-------|----------|
| Wireshark / tshark | active | 4.x | — |
| tcpdump / Npcap | active | libpcap for Windows | — |
| mitmproxy / mitmdump | active | 11.x; Python addons | BetterCap |
| scapy | active | packet crafting/replay (Python) | tcpreplay |
| boofuzz | active | protocol fuzzing framework | — |
| Zeek / Suricata | active | network analysis / IDS for pcap + live | — |

## Firmware / blockchain

| Tool | Status | Notes | Fallback |
|------|--------|-------|----------|
| binwalk | active | firmware extraction | unblob |
| unblob | active | better for complex/custom images | binwalk |
| UEFITool / uefiextract | active | firmware volume parsing | uefi-firmware-parser |
| heimdall-rs | active | EVM disassembler/decompiler (Rust) | evm-codes / py-evm |
| Foundry (anvil/cast) | active | local EVM fork testing (`anvil`) | hardhat |

## Cloud / containers (new skills)

| Tool | Status | Notes | Fallback |
|------|--------|-------|----------|
| prowler | active | AWS/Azure/GCP security assessment | ScoutSuite (legacy) |
| cloudfox | active | cloud attack-path tooling (AWS/Azure/GCP) | — |
| pacu | active | AWS exploitation framework | — |
| kubectl / kube-hunter | active | k8s enumeration; kube-hunter for clusters | kube-bench (CIS checks) |
| grype / trivy | active | image/SBOM vulnerability scanning | syft (SBOM only) |
| nuclei | active | template-based vulnerability scanner (recon) | — |
| amass / subfinder | active | subdomain enumeration | — |
| theHarvester | active | email/domain OSINT | — |

## Notes

- **IDA MCP:** the binary-re skill supports an `ida-pro` MCP server — the strongest integration path when available.
- **Version pinning:** for tools installed from personal repos (e.g. `panda-dex-dumper`, `frida-ios-dump`), pin a specific commit in your lab setup rather than trusting `main`.
- **Last checked:** 2026-07. Re-verify a tool's status if your run is older than ~6 months.
