---
name: anti-analysis
description: "Anti-analysis & packers: anti-VM/anti-debug/anti-emulation bypass, unpacking workflow (OEP + IAT), VMProtect/Themida/Enigma, API-hash reconstruction."
risk: offensive
when-to-use: "Use when: packed/protected binaries — VMProtect/Themida/Enigma, anti-VM/anti-debug bypass, API-hash reconstruction. Not when: unpacked clean binaries (use D/G directly) or .NET-only obfuscation (use E)."
---

# Anti-Analysis & Packers

## 1. Anti-analysis classes (detect → bypass)
| Class | Detection | Bypass |
|-------|-----------|--------|
| Anti-VM | CPUID hypervisor bit, MAC OUI, HWID, `vmware`/`vbox` services, timing `rdtsc` | patch checks (G/F), spoof CPUID/MAC, TitanHide/ScyllaHide |
| Anti-debug | PEB/`IsDebuggerPresent`, `NtQuery*`, hardware BP, timing, exception tricks | ScyllaHide, manual patch (G3) |
| Anti-emulation | unsupported instructions, weird timing, deep `cpuid` levels | emulate with the real instruction semantics (F2), patch the check |
| Anti-sandbox | user interaction checks (GetCursorPos, window titles), uptime, process lists | script real input / patch checks |
| Anti-dump | erase PE header at runtime, garbage the section table after load | dump from a "clean" run point, rebuild headers (G1 Scylla) |

## 2. General unpacking approach
```
1. Identify packer (DIE) → packer-specific tool if known (upx -d, de4dot...)
2. Find OEP (Original Entry Point):
   - tail-jump: after decryption loop, jmp to OEP — watch for a far jump to a clean .text region
   - memory breakpoint on section with execute (hardware/guarded)
   - `!pagetable`/memory-map breakpoints on the unpacked section first write/execute
3. Dump the decrypted image (Scylla / procdump) + fix IAT (Scylla IAT autosearch)
4. If import reconstruction fails: the stub hashes imports — find the API-hash loop and map hashes (P4)
```
Prefer Unicorn (F2) for auto-unpacking: run the stub, intercept the tail-jump, dump memory image programmatically.

## 3. Commercial protectors
| Protector | Characteristics | Approach |
|-----------|-----------------|----------|
| VMProtect | virtualization of selected funcs, mutation, import protection | unpack core, then devirtualize handlers (heavy); or patch around virtualized checks |
| Themida/WinLicense | code encryption, anti-debug native, VM | dedicated unpack scripts (x64dbg), or dynamic dump at OEP |
| Enigma | mutation, anti-debug | scripted OEP + IAT |
| Obsidium/ASProtect | legacy | standard OEP/IAT flow |

Reality check: full devirtualization is a research project. Practical: identify what the protector is protecting (license check, string table) and bypass at the *behavioral* level — patch the result of the check or hook the decrypted logic after unpack.

## 4. Custom packers & API hashing
Stubs often resolve APIs by **hashing** (e.g. `hash("LoadLibraryA")` → loop over PEB LdrData → compute hash → match). To reconstruct:
```c
// Generic example only — find the stub's compare value first, then
// reproduce its exact hash (often ROR13 or a custom mix), e.g.:
uint32_t hash_api(const char* s) {
    uint32_t h = 0; while (*s) h = (h >> 13) | (h << 19) + *s++;
    return h;
}
```
Map all matched hashes by running the hash over every exported name (`PeExport` / `dumpbin /exports` / `capa`). Tools: **capa** (behavior signatures), **unpac.me** (online unpacking), x64dbg scripts.

## 5. Anti-analysis toolchain
DIE (identify) · x64dbg + Scylla + ScyllaHide + TitanHide · Unicorn (auto-unpack) · capa (capabilities) · unpac.me (online unpack — upload only samples you own/are authorized for) · `upx -d` · de4dotEx (E/.NET) · Procmon (behavior) · FakeNet-NG (network)

## 6. Anti-analysis anti-patterns
- Fighting the VM detector instead of patching one check → waste hours; patch the branch
- Trying full devirtualization on a 50k-function VMProtect binary in one session → split: unpack core, patch behavior
- Dumping too early/late → broken imports or packed again; dump exactly at OEP
- Missing the API-hash loop → IAT empty; reconstruct hashes (P4)

---
