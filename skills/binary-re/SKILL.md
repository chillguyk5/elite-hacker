---
name: binary-re
description: "Reverse native binaries: symbol/struct recovery from stripped binaries, IDAPython/IDALib scripting, Ghidra scripting and headless batch analysis."
risk: offensive
when-to-use: "Use when: native PE/ELF binaries (stripped or not), need symbols/structs, IDA/Ghidra scripting, headless batch. Not when: .NET (use E), managed/Java (use H), or firmware blobs (use O)."
---

# RE Static - Native Binary

## 0. IDA Access — choose method (shared by D1-D3)

**Option A — IDA Pro MCP (preferred if connected):** if an `ida-pro` MCP server is active, query IDA directly via MCP tools, no exported files.

**Option B — IDA-NO-MCP exported data:** if MCP is absent, check current dir for `decompile/` with `.c` files. If missing, direct the user: install [IDA-NO-MCP](https://github.com/P4nda0s/IDA-NO-MCP), copy `INP.py` to IDA plugins, press Ctrl-Shift-E to export, then open the export dir.

### Export directory structure (shared D1-D2)
```
./
├── decompile/              # decompiled C, one file per function: 0x401000.c
├── decompile_failed.txt    # failed functions
├── decompile_skipped.txt   # skipped functions
├── strings.txt             # (address, length, type, content)
├── imports.txt             # (address:function_name)
├── exports.txt             # (address:function_name)
└── memory/                 # 1MB memory hexdump chunks
```

### Function file format (decompile/*.c)
```c
/*
 * func-name: sub_401000
 * func-address: 0x401000
 * callers: 0x402000, 0x403000    // functions calling this one
 * callees: 0x404000, 0x405000    // functions called by this one
 */
int __fastcall sub_401000(int a1, int a2) { /* decompiled */ }
```

## 1. Symbol Recovery — rename stripped functions

### Step 1 — Internal characteristics
- **String constants:** strings used reveal purpose
- **Magic numbers:**
  - MD5: `0x67452301`, `0xEFCDAB89`, `0x98BADCFE`, `0x10325476`
  - CRC32: `0xEDB88320`
  - Base64: `ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/`
  - AES S-Box: `0x63, 0x7C, 0x77, 0x7B...`
  - Zlib: `0x78`, `0x9C`
- **Code structure:** loop patterns, bitwise ops, distinctive algorithm flow

### Step 2 — Cross-reference analysis

**Paired function patterns:**
```c
// malloc/free, new/delete, alloc/dealloc
xx = sub_A(0x100);        // alloc: size in, pointer out
sub_B(xx);                // free: same pointer in

// mutex_lock/mutex_unlock
sub_A(lock_ptr); sub_B(lock_ptr);     // same lock object

// open/close, CreateFile/CloseHandle
fd = sub_A("/path", 0); sub_B(fd);    // same handle

// pthread_create/pthread_join
sub_A(&tid, 0, func, arg); sub_B(tid, &ret);
```

**Argument pattern recognition:**
```c
sub_XXX(2, 1, 0);         // socket: domain=2(AF_INET), type=1(SOCK_STREAM)
sub_XXX(fd, &var, 16);   // connect/bind: addr struct, len=16 IPv4
sub_XXX(dst, src, n);     // memcpy/memmove: dst, src, count
sub_XXX(ptr, 0, 0x100);   // memset: ptr, byte value, count
ret = sub_XXX(fd, buf, n); // read/write: returns byte count
if (sub_XXX(s1, s2) == 0)  // strcmp: 0 when equal
```

**Return value patterns:**
```c
if ((fd = sub_XXX(...)) == -1) goto error;  // file/socket, -1 = error
if (!(ptr = sub_XXX(size))) goto error;      // alloc, NULL = fail
if (sub_XXX(...) != 0) goto error;           // 0 = success
len = sub_XXX(str); sub_YYY(dst, src, len);  // strlen → fed to memcpy
```

**Callers:** symboled caller (exports.txt) → infer callee purpose; trace up the chain to a symboled function.

### Step 3 — Search
- Local reasoning first (signature, paired calls, imports, structure)
- Uncertain → Web Search: magic + "algorithm"; code patterns; unique strings

### Output format
```
## Symbol Recovery Analysis: <addr>
### Function Characteristics     ### Cross-Reference Analysis
### Inference Result
- **Suggested symbol name**: <name>
- **Confidence**: High / Medium / Low
- **Reasoning**: <why>
### Similar Open Source Implementation: <link if found>
```

## 2. Structure Recovery — rebuild structs from decompile

### Steps 1-4 — Collect memory access patterns
```c
*(a1 + 0x10)           // offset 0x10
*(_DWORD *)(a1 + 8)    // offset 0x8, DWORD
*(_QWORD *)(a1 + 0x20) // offset 0x20, QWORD
*(*a1 + 0x10)          // first field of a1 is a pointer (nested)
*(a1 + 8 * i)          // array, element 8 bytes
```
Record: `offset=0x08, size=4, access=read, type=DWORD`

**Callers:** `sub_401000(v1)` → v1 struct ptr; `sub_401000(&v2)` → v2 is struct; `sub_401000(malloc(0x40))` → size ~0x40.
Init before call: `*v1=0; *(v1+8)=callback;` → offset 0x08 is a function pointer.

**Callees:** callee `return *(a1+0x18);` → offset 0x18; `another_func(a1+0x20)` → nested struct at 0x20.

### Step 5 — Aggregate & infer
- Merge all offsets, sort
- Size = max(offset) + last_field_size
- Infer types: called as fn → function pointer; passed to strlen/printf → string ptr; compared to constants → enum/flags; ++/-- → counter
- Patterns: offset 0 = fn table → vtable (C++); next/prev → linked list; refcount → ref-counted object

### Output format
```c
/*
 * Structure Recovery Analysis — Source: <addr>, scope: <n callers/callees>
 * Functions using this struct: 0x401000(init) 0x401100(field) 0x401200(destruct)
 */
// Estimated size: 0x48 bytes — Confidence: High / Medium / Low
struct suggested_name {
    /* 0x00 */ void *vtable;        // called via (*(*this))()
    /* 0x08 */ int refcount;        // has ++/-- ops
    /* 0x0C */ int flags;           // AND with 0x1, 0x2
    /* 0x10 */ char *name;          // passed to strlen/printf
    /* 0x18 */ void *data;
    /* 0x20 */ size_t size;
    /* 0x28 */ struct node *next;   // linked list
    /* 0x30 */ struct node *prev;
    /* 0x38 */ callback_fn handler; // callback
    /* 0x40 */ void *user_data;
};
```

## 3. IDAPython / IDALib — script reference

**IDAPython** = inside IDA GUI; **IDALib** = headless (IDA 9.0+).

### Common API
```python
idc.get_reg_value('rax'); idaapi.set_reg_val("rax", 1234)   # registers
idc.read_dbg_byte(addr); idc.read_dbg_memory(addr, size)
idc.read_dbg_dword(addr); idc.read_dbg_qword(addr)
idc.patch_dbg_byte(addr, val); idc.add_bpt(0x409437)
idc.get_qword(addr); idc.patch_qword(addr, val); idc.patch_byte(addr, val)
idc.get_bytes(addr, size); idc.get_strlit_contents
GetDisasm(addr); idc.next_head(ea); idc.create_insn(addr)
ida_funcs.add_func(addr); idc.del_items(addr)
idc.get_name_ea(0, '_sub_6051')
ida_funcs.get_func(ea)
for func in idautils.Functions(): print("0x%x, %s" % (func, idc.get_func_name(func)))
```

### Key snippets

**Byte pattern search**
```python
def find_bytes_list(bytes_pattern):
    ea = -1; result = []
    while True:
        ea = idc.find_bytes(bytes_pattern, ea + 1)
        if ea == ida_idaapi.BADADDR: break
        result.append(ea)
    return result
# find_bytes_list("55 ??")
```

**Appcall — call debuggee functions** (legacy API; verify behavior on your IDA version — older Appcall flows break on IDA 9.x, prefer IDALib or x64dbg when it misbehaves)
```python
passwd = ida_idd.Appcall.byref("MyFirstGuess")
res = ida_idd.Appcall.check_passwd(passwd)
print("Good" if res.value == 0 else "Bad")

loadlib = Appcall.proto("kernel32_LoadLibraryA", "int __stdcall loadlib(const char *fn);")
hmod = loadlib("dll_to_inject.dll")
```

**Cross references / basic blocks**
```python
[ref.frm for ref in idautils.XrefsTo(ea)]
f_blocks = idaapi.FlowChart(idaapi.get_func(fn), flags=idaapi.FC_PREDS)
for b in f_blocks: print(hex(b.start_ea))          # .succs()/.preds() to walk
```

**Debug memory + 64-bit strings**
```python
def patch_dbg_mem(addr, data):
    for i in range(len(data)): idc.patch_dbg_byte(addr + i, data[i])

def dbg_read_cstr_64(objectAddr):
    result = ''; i = 0
    while True:
        b = idc.read_dbg_byte(objectAddr + i)
        if b == 0: break
        result += chr(b); i += 1
    return result
```

**Callees by instruction**
```python
def ida_get_callees(func_addr):
    callees = []
    for head in idautils.Heads(func_addr, idaapi.get_func(func_addr).end_ea):
        if idaapi.is_call_insn(head):
            callees.append(idc.get_operand_value(head, 0))
    return callees
```

**Import checks**
```python
def ida_is_import_function(addr):
    for i in range(ida_nalt.get_import_module_qty()):
        def cb(ea, n, o): return not (ea == addr)
        if not ida_nalt.enum_import_names(i, cb): return True
    return False
```

**Type / struct members**
```python
def extract_struct_members(type_name):
    fields = []
    tif = ida_typeinf.tinfo_t()
    if tif.get_named_type(None, type_name):
        for it in tif.iter_struct():
            fields.append({"offset": it.offset//8, "size": it.type.get_size(), "type": it.type._print()})
    return fields
```

**Hex-Rays decompile**
```python
dec = ida_hexrays.decompile(func_addr)
print(str(dec))
```

**OLLVM breakpoints (real-block merge point)**
```python
ollvm_tail = 0x405D4B
f_blocks = idaapi.FlowChart(idaapi.get_func(0x401F60), flags=idaapi.FC_PREDS)
for block in f_blocks:
    for succ in block.succs():
        if succ.start_ea == ollvm_tail: idc.add_bpt(block.start_ea)
```

**Firmware: create functions from x86 prologues**
```python
for h in find_bytes_list("55 8B"):
    idc.del_items(h); idc.create_insn(h); ida_funcs.add_func(h)
```

**NOP function (ARM/x86)**
```python
def nop_func(addr_func, arch='arm'):
    func = ida_funcs.get_func(addr_func)
    nop = [0x1F,0x20,0x03,0xD5] if arch=='arm' else [0x90]
    ea = func.start_ea
    while ea < func.end_ea:
        insn = ida_ua.insn_t(); length = ida_ua.decode_insn(insn, ea)
        for i in range(0, length, len(nop)):
            for j in range(len(nop)):
                if i+j < length: idc.patch_byte(ea+i+j, nop[j])
        ea += length
```

### IDALib (headless, IDA 9.0+)
```bash
cd idalib/python && pip install . && python py-activate-idalib.py
```
```python
import idapro                    # MUST be the first import
ida.open_database("samples/patch.so", True)
for func in idautils.Functions(): print(hex(func), idc.get_func_name(func))
ida.close_database(save=True)
```
Batch decompile to JSON: loop `ida_hexrays.decompile(func)` → `str(dec)` → json; parallelize with `multiprocessing.Pool` running `decompile.py` per file.

## 4. Ghidra Scripting & Headless

Use when no IDA / need free batch / firmware. If you have IDA, prefer D3.

### Headless batch
```bash
analyzeHeadless <proj_dir> <proj> -import <binary> -postScript MyScript.py -scriptPath <dir> -deleteProject
```

### Python (Jython) — core API
```python
# Largest functions first (main logic)
fm = currentProgram.getFunctionManager()
funcs = sorted(fm.getFunctions(True), key=lambda f: f.getBody().getNumAddresses(), reverse=True)
for f in funcs[:20]:
    println("%08x %6d %s" % (f.getEntryPoint().getOffset(), f.getBody().getNumAddresses(), f.getName()))

# Decompile one function
from ghidra.app.decompiler import DecompInterface
from ghidra.util.task import ConsoleTaskMonitor
decomp = DecompInterface(); decomp.openProgram(currentProgram)
res = decomp.decompileFunction(getFunctionAt(toAddr(0x00401000)), 60, ConsoleTaskMonitor())
if res.decompileCompleted(): println(res.getDecompiledFunction().getC())
decomp.dispose()

# Rename functions from referenced strings (USER_DEFINED source)
from ghidra.program.model.symbol.SourceType import USER_DEFINED
for func in currentProgram.getFunctionManager().getFunctions(True):
    if "license" in func.getName().lower(): func.setName("check_" + func.getName(), USER_DEFINED)
```

Java scripts for large binaries (Jython is slow). Feed decompiled C into D1/D2 (those steps are IDA-independent). Export symbols to IDA if the workflow needs to continue there.

---
