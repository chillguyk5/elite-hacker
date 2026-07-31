---
name: elf-linux-re
description: "ELF/Linux RE: readelf/objdump/radare2 analysis, stripped symbol recovery, LD_PRELOAD runtime hooking, Linux malware persistence basics."
risk: offensive
when-to-use: "Use when: ELF binaries/.so on Linux — readelf/objdump/r2 analysis, LD_PRELOAD hooking, Linux malware. Not when: Windows PE (use D/G) or mobile ARM (use H)."
---

# ELF / Linux RE

## 0. Scope check

Target is your own (binary/game/machine), a lab, a CTF, or a sample you're allowed to analyze → proceed, no confirmation needed. Unauthorized third-party live targets (prod, SaaS, others' accounts) → stop; policy in README A5.

## 1. ELF structure basics
```
ELF header (ehdr)  → ELF64_Ehdr (e_ident magic \x7fELF, class, endianness)
Program headers    → PHDR table: PT_LOAD segments, PT_DYNAMIC, PT_INTERP, PT_GNU_STACK
Section headers    → SHDR table (can be stripped): .text .rodata .data .bss .dynsym .dynstr
```
Two symbol concepts: **dynsym** (exported, survives `strip`) and **symtab** (full, removed by strip/`-s`).

```bash
readelf -h target          # header, entry point
readelf -l target          # program headers (segments)
readelf -S target          # section headers
readelf -s target          # symbols (strip removes symtab; dynsym remains)
readelf -d target          # dynamic section (NEEDED libs, RPATH, RUNPATH)
readelf -r target          # relocations
objdump -d -M intel target # disassembly
```

## 2. Tooling
`readelf`/`objdump`/`nm`/`strip` (binutils) · `file` · `strings` · `radare2`/`rizin` (`r2 -A`, `aaa`, `pdf @ main`) · Ghidra (excellent ELF loader) · IDA · `ltrace`/`strace` (runtime)

radare2 quick: `r2 -A ./bin`, then `afl` (list funcs), `s main`, `pdf` (print disasm), `axt @ sym.check` (xrefs).

## 3. Symbol recovery in stripped ELF
- `readelf -s` shows only `.dynsym` → exported API names; internal functions are `sub_*`
- Shared objects export what other libs call — map by linkage against known APIs (D1 patterns apply)
- Ghidra auto-names imported thunks; use `strings` + xrefs to recover intent
- Compare with a non-stripped build of the same library (version match) → diff symbol tables

## 4. Runtime hooking — LD_PRELOAD
Intercept libc/lib functions without ptrace:

```c
// hook.c — override open()
#define _GNU_SOURCE
#include <stdio.h>
#include <dlfcn.h>
#include <fcntl.h>

typedef int (*open_fn)(const char *, int, ...);
int open(const char *path, int flags, ...) {
    static open_fn real = NULL;
    if (!real) real = (open_fn)dlsym(RTLD_NEXT, "open");
    fprintf(stderr, "[hook] open(%s)\n", path);
    return real(path, flags);
}
```
```bash
gcc -shared -fPIC -o hook.so hook.c
LD_PRELOAD=./hook.so ./target
```
Useful for: logging file/config access, secrets in argv, bypassing simple checks. `LD_PRELOAD` is ignored for setuid binaries and under some hardening (Yama).

## 5. Linux malware basics (defensive RE)
- **Static:** `file`, entropy, `strings` for persistence paths, `readelf -d` NEEDED, suspicious exports
- **Dynamic:** `strace -f`, `ltrace`, network via tcpdump; use a disposable VM
- **Persistence patterns:** cron, `~/.config/autostart`, systemd units, `LD_PRELOAD` in `/etc/ld.so.preload`, `rc.local`, `.bashrc`
- **Escalation-relevant artifacts:** setuid copies, polkit agents, SUID bash, Writable PATH dirs

## 6. ELF anti-patterns
- Reading `.symtab` after `strip` → nothing; use dynsym + xrefs
- Forgetting `-mintel`/`att` default → confused by AT&T syntax; pick `objdump -d -M intel`
- Assuming `strings` output is all data — filter with context (address, section)
- LD_PRELOAD on setuid → silently ignored, wonder why hook never fires

---
