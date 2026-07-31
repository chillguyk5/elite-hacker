---
name: dotnet-re
description: "Reverse .NET assemblies: dnSpy decompile/edit/debug, de4dot deobfuscation, dnlib programmatic patching, Harmony runtime hooks."
risk: offensive
when-to-use: "Use when: .NET assembly (EXE/DLL), Unity Mono games, .NET obfuscators (ConfuserEx/Reactor). Not when: native binaries (use D) or IL2CPP games (use H3 + F)."
---

# RE Static - .NET

Managed assembly (.NET EXE/DLL, Unity Mono games). Detect: `file` says ".NET assembly", PE has CLR header, imports `mscoree.dll`.

## 1. dnSpyEx — decompile / edit / debug

The original dnSpy is unmaintained since 2020 — use the **dnSpyEx** fork (drop-in, v6.6+).
- Open file → namespace/class/method tree; switch decompiler to IL for raw opcodes
- **Search Ctrl+Shift+K**: strings/types/methods — fastest path to license logic
- **Analyze Ctrl+Shift+R**: "Used By / Uses / Derived" = .NET xrefs
- **Edit Method (C#)** → edit directly (e.g. `CheckLicense() → return true;`) → Compile → **Save Module** (back up first!)
- **Debug**: Start/Attach, breakpoint managed methods, watch variables — see runtime serial/HWID

## 2. Obfuscation & de4dot

**de4dot is unmaintained (~2021)** — works for legacy obfuscators below; for newer protections try **de4dotEx** (maintained fork) or manual dnlib reversing. Tool versions: TOOLS.md.

| Protector | Fix |
|-----------|-----|
| ConfuserEx (`[ConfusedByConfuserEx]`) | de4dot / de4dotEx |
| .NET Reactor (native stub + encrypted strings) | de4dotEx / dedicated unpacker; newer Reactor versions resist de4dot |
| Eazfuscator (string encryption) | de4dot string decrypt |
| Dotfuscator (rename + CF) | de4dot rename |
| Virtualization (logic → VM bytecode) | de4dot can't fix — reverse dispatcher manually |

```bash
de4dot.exe target.exe -o target-clean.exe
de4dot.exe target.exe -p confuserex -o target-clean.exe
```

## 3. Programmatic patch with dnlib
```csharp
using dnlib.DotNet; using dnlib.DotNet.Emit;
var mod = ModuleDefMD.Load("target.exe");
var m = mod.Find("MyApp.License", true).FindMethod("Check");
m.Body.Instructions.Clear();
m.Body.Instructions.Add(Instruction.Create(OpCodes.Ldc_I4_1));
m.Body.Instructions.Add(Instruction.Create(OpCodes.Ret));
mod.Write("target-patched.exe");
```

## 4. Harmony — runtime patch (no file modification)
```csharp
using HarmonyLib;
var harmony = new Harmony("com.lab.bypass");
harmony.Patch(AccessTools.Method(typeof(License), "Check"),
    prefix: new HarmonyMethod(typeof(Patches), nameof(Patches.CheckPrefix)));

static class Patches {
    static bool CheckPrefix(ref bool __result) {
        __result = true;    // force true
        return false;       // skip original
    }
}
```
Load via DLL proxy (I1) or game mod loader.

## 5. .NET toolchain
dnSpyEx (decompile/edit/debug) · ILSpy (read-only) · de4dot/de4dotEx (deobfuscate) · dnlib (patch) · Harmony/HarmonyX (runtime mod) · ildasm (IL) · `sn -Vr *,<token>` (strong-name bypass, lab)

---
