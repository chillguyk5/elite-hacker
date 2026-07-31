---
name: runtime-hooking
description: "Runtime instrumentation: Frida hooks (native/ObjC/Java, module-load timing), Unicorn offline emulation of code fragments with environment simulation."
risk: offensive
when-to-use: "Use when: runtime instrumentation — Frida hooks (native/ObjC/Java), Unicorn offline emulation of code fragments. Not when: static-only analysis (use D/E) or kernel debugging (use N)."
---

# RE Dynamic - Hooking & Emulation

## 1. Frida Script Generator

Modern API, no `--no-pause`.

```bash
frida -U -f com.example.app -l hook.js      # spawn + hook
frida -U com.example.app -l hook.js         # attach running
frida -U -p 1234 -l hook.js                 # attach by PID
```

### Module & symbol
```javascript
const mod = Process.getModuleByName("libssl.so");
const ptr = mod.getExportByName("SSL_read");
Process.enumerateModules(); mod.enumerateExports(); mod.enumerateImports();
const addr = Module.findGlobalExportByName("open");   // static lookup; Module.getExportByName(null,...) was removed in Frida 17.x
```

### Interceptor
```javascript
Interceptor.attach(ptr, {
    onEnter(args) { console.log("arg0:", args[0].toInt32(), args[1].readUtf8String()); },
    onLeave(retval) { console.log("ret:", retval.toInt32()); }
});
Interceptor.replace(ptr, new NativeCallback(function (a0, a1) {
    return 0;
}, "int", ["pointer", "int"]));
```

### NativeFunction & Memory
```javascript
const open = new NativeFunction(Module.findGlobalExportByName("open"), "int", ["pointer","int"]);
const fd = open(Memory.allocUtf8String("/etc/hosts"), 0);

ptr(addr).readByteArray(size); ptr(addr).readUtf8String(); ptr(addr).readU32(); ptr(addr).readPointer();
ptr(addr).writeByteArray(bytes); ptr(addr).writeU32(0x41414141);
// note: on Frida 17.x a trailing "??" makes the pattern invalid ("invalid match pattern");
// keep the wildcard mid-pattern, e.g.:
Memory.scan(mod.base, mod.size, "48 89 5C 24 ?? 48 89 6C", {
    onMatch(address, size) { console.log("found at:", address); }, onComplete() {}
});
```

### ObjC / Java
```javascript
if (ObjC.available) {
    Interceptor.attach(ObjC.classes.ClassName["- methodName:"].implementation, {
        onEnter(args) { console.log(new ObjC.Object(args[0]).toString()); }
    });
}
if (Java.available) {
    Java.perform(function () {
        const A = Java.use("android.app.Activity");
        A.onCreate.implementation = function (bundle) { console.log("onCreate"); return this.onCreate(bundle); };
    });
}
```

### Timing: hook native module on load (important)
Never assume a `.so` is loaded. Hook `android_dlopen_ext`/`dlopen`, install hooks in `onLeave` (after constructors). Dedupe by module base.

```javascript
function hookModuleLoad(moduleName, callback) {
    const dlopen = Module.findGlobalExportByName("android_dlopen_ext")
        || Module.findGlobalExportByName("dlopen");
    if (!dlopen) throw new Error("dlopen not found");
    const hooked = new Set();
    Interceptor.attach(dlopen, {
        onEnter(args) {
            this.path = args[0].isNull() ? null : args[0].readCString();
            this.shouldHook = this.path && this.path.indexOf(moduleName) !== -1;
        },
        onLeave(retval) {
            if (!this.shouldHook || retval.isNull()) return;
            const mod = Process.findModuleByName(moduleName);
            if (!mod) return;
            const key = mod.base.toString();
            if (hooked.has(key)) return;
            hooked.add(key); callback(mod);
        }
    });
}
function hookNowOrOnLoad(moduleName, callback) {
    const mod = Process.findModuleByName(moduleName);
    if (mod) return callback(mod);
    hookModuleLoad(moduleName, callback);
}
```
Polling (`setInterval`) only as a last-resort fallback.

### Do NOT blindly hook init/constructors
Don't advise hooking `.init`/`.init_array`/constructors/`JNI_OnLoad` blindly (crashes before target logic runs). Order:
1. Stable exported function after module load
2. `RegisterNatives`/`dlsym`/first business function
3. `JNI_OnLoad` only if anti-debug/registration happens there
4. Constructors only with strong evidence; prefer hooking the **dispatcher** (`call_constructors`/`call_array`) to log the sequence before patching

### Guidelines & logging
1. Modern API (`Process.getModuleByName`, `mod.getExportByName`)
2. No `--no-pause`; hook by event, not polling
3. Readable pointer/buffer output; wrap risky hooks in `try/catch`
4. Binary data → `hexdump(args[0], {length: 64, header: true, ansi: false})`

## 2. Unicorn Emulation Debugger

Emulate a code fragment/function offline — no full binary run. Use to: decode data by emulating the algorithm, bypass environment deps (JNI/syscalls/libc), trace suspicious logic without the real device.

### Principles
1. **Load raw** — don't parse ELF/PE headers; map bytes into memory (only map needed segments when code references absolute addresses)
2. **Identify deps** — hook external calls (JNI/syscall/libc/imports) and simulate responses
3. **Use callbacks heavily** — `UC_HOOK_CODE/BLOCK/MEM_*/INTR`
4. **Iterative fix** — crash → read callback → map/hook/fix regs → rerun
5. **Minimal trace** — block-level over instruction-level; counters/summaries

### Environment simulation
| Type | Examples | Strategy |
|------|----------|----------|
| libc | malloc/free/memcpy/strlen/printf | hook + implement in Python (bump allocator) |
| JNI | GetStringUTFChars/FindClass/GetMethodID | fake JNIEnv table + RET stubs, hook stubs |
| Syscalls | read/write/mmap/ioctl | `UC_HOOK_INTR`, dispatch by number |
| C++ runtime | operator new/__cxa_throw | hook + simulate |
| Library | pthread_mutex_lock/dlopen | return success/stub |

Hook pattern: `UC_HOOK_CODE` — when PC hits a known import address, run the Python simulation, then set PC=LR.

### Callback types
`UC_HOOK_CODE` (import intercept / narrow trace) · `UC_HOOK_BLOCK` (preferred trace) · `UC_HOOK_MEM_UNMAPPED` (auto-map) · `UC_HOOK_MEM_READ|WRITE` (data-range trace) · `UC_HOOK_INTR` (syscalls)

### Iterative loop
```
Run → crash → read fault (addr? read/write/fetch?) →
  unmapped fetch → map code page
  unmapped rw → map data / init ptr / hook
  import stub → add simulation
  infinite loop → code-hook counter, stop past threshold
→ Fix → Re-run
```

### Architecture quick ref
| Arch | Const | Mode | SP | LR | Args | Return | Syscall |
|------|-------|------|----|----|------|--------|---------|
| ARM64 | `UC_ARCH_ARM64` | LE | SP | X30 | X0-X7 | X0 | X8+SVC#0 |
| ARM32 | `UC_ARCH_ARM` | THUMB/ARM | SP | LR | R0-R3 | R0 | R7+SVC#0 |
| x86-64 | `UC_ARCH_X86` | 64 | RSP | stack | RDI,RSI,RDX,RCX,R8,R9 | RAX | RAX+syscall |
| x86-32 | `UC_ARCH_X86` | 32 | ESP | stack | stack | EAX | EAX+int0x80 |
| MIPS32 | `UC_ARCH_MIPS` | MIPS32+BE | $sp | $ra | $a0-$a3 | $v0 | $v0+syscall |

---
