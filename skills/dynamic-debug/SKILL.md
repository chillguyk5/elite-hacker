---
name: dynamic-debug
description: "Dynamic debugging: x64dbg, WinDbg with Time Travel Debugging, anti-debug bypass, static-dynamic coordination, unpack dump + IAT fix."
risk: offensive
when-to-use: "Use when: proving runtime behavior — x64dbg/WinDbg breakpoints, anti-debug bypass, crash dumps, TTD, unpack dumps. Not when: quick static checks (use D) or hooking at scale (use F)."
---

# Dynamic Debug

## 1. x64dbg (native user-mode, Windows)

Attach: `File → Attach/Open`. Keys: `F9 run · F8 step over · F7 step into · F4 run to cursor · F2 bp · Ctrl+F9 run to return · Alt+F9 run to user code`.

### Breakpoints
| Type | Use when | Command |
|------|----------|---------|
| Software (int3) | normal stop points | `bp addr` / F2 |
| Hardware (DR0-3) | anti-int3, data watch | Debug → Hardware BP |
| Memory (page guard) | catch who writes region X | `bpm addr, w` |
| Conditional | stop on condition | `bp addr, "eax==0"` |

**Catch "who writes to X":** hardware/memory BP write on X → stops at the exact writing instruction → Call Stack to trace the deciding function.

### Tracing & scripting
- **Run trace**: per-step log with registers, filtered, stop on expression — walk obfuscation without manual stepping
- Script `.txt`:
```
bp 0x140001234
run
cmt $cip, "license check here"
log "eax = {x:eax}"
run
```

### Dump + fix IAT after unpack
Scylla → IAT Autosearch → Get Imports → fix invalid entries → Dump → Fix Dump. Plugins: **ScyllaHide** (patches user-mode anti-debug), **x64dbgpy** (Python scripting).

## 2. WinDbg (kernel + user + .NET + TTD)

```
.attach / .open            attach / open dump
lm                         list modules
!analyze -v                analyze crash dump
bp/bu/bm module!Func       breakpoint (resolved / unresolved / wildcard)
g / p / t                  go / step over / step into
r                          registers
dt module!Struct addr      dump struct by type
db/dd/dq addr L n          dump bytes/dwords/qwords
eb/ed addr val             edit memory
k                          call stack
```

**.NET (SOS):** `!clrstack` · `!dumpheap -type X` · `!bpmd module method` · `!name2ee module type`

**Time Travel Debugging (TTD):** record execution → step backward `g-` · query `!tt "Start" "End"` — catch one-shot branches without re-running.

## 3. Anti-debug — detect & bypass

| Technique | Bypass |
|-----------|--------|
| `IsDebuggerPresent` / PEB.BeingDebugged | patch PEB byte / hook return 0 |
| `NtQueryInformationProcess(ProcessDebugPort)` | hook return 0 |
| Hardware BP detection (DR != 0) | clear DR / hook `NtGetContextThread` |
| Timing (`rdtsc`/`QPC`) | hook timers / avoid tracing that region |
| TLS callbacks / int3 self-check | bp `LdrpCallInitRoutine` / module entry |
| SEH/VEH exception anti-debug | pass exceptions to app (`Shift+F9` x64dbg) |

**ScyllaHide** auto-patches most user-mode anti-debug.

## 4. Static ↔ Dynamic coordination

```
IDA/Ghidra: candidate check / interesting function → RVA
  ↓
x64dbg/WinDbg: bp by RVA (ASLR: bp_running = module_base_live + RVA,
  or by symbol `game.exe+0x1234`)
  ↓
Trigger behavior → bp hit → read registers/args/stack → confirm
  ↓
Decide: patch file / runtime hook / keygen / drop
```

## 5. Debug anti-patterns
- Manual stepping through obfuscation → run-trace with filters
- bp by absolute VA with ASLR on → use RVA/symbol
- Forgetting to pass exceptions to the app (SEH anti-debug)
- Using x64dbg for kernel/.NET dumps → WinDbg
- Tracing the whole process without filters → unreadable logs


---
