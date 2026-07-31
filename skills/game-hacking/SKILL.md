---
name: game-hacking
description: "Game hacking: Cheat Engine value/pointer/struct scanning, Auto Assemble code injection, mobile Unity IL2CPP Frida hooking, client vs server side."
risk: offensive
when-to-use: "Use when: game targets — Cheat Engine scans, pointer/struct work, code injection, mobile IL2CPP hooking. Not when: server-authoritative games (verify J6 first) or non-game binaries (use D/F/G)."
---

# Game Hacking

## 0. Scope check

Target is your own (binary/game/machine), a lab, a CTF, or a sample you're allowed to analyze → proceed, no confirmation needed. Unauthorized third-party live targets (prod, SaaS, others' accounts) → stop; policy in README A5.

## 1. Cheat Engine — value scanning
```
1. Attach CE → 2. Pick type (4B/float/double/string)
3. First Scan = current value (HP=100)
4. Change value in-game → 5. Next Scan "Changed" / "= 80"
6. Repeat until few addresses → test write/freeze
```
| Situation | Scan type |
|-----------|-----------|
| Exact number visible (HP, ammo) | Exact Value |
| Unknown value (health bar, no number) | Unknown → Increased/Decreased |
| Encrypted value (XOR) | "Value between", or break-on-write to read real value in register |

## 2. Pointer Scan — static path
```
1. Find dynamic address → 2. Pointer scan (Max level 5-7, Max offset 4096)
3. Filter: restart game / load different save → rescan, keep paths still valid (repeat 2-3x)
4. Result: [[base]+off1]+off2... = value   (static base: game.exe+ / UnityPlayer.dll / GameAssembly.dll)
```

## 3. Dissect struct
CE Dissect data/structures (Ctrl+D) → offset hints. Assemble:
```
+0x00 vtable/id   +0x10 float hp   +0x14 float hp_max
+0x30 float x     +0x34 float y    +0x38 float z   (3 adjacent floats = coords)
+0x50 int team_id +0x60 ptr name (wchar)
```
Tips: coords = 3 adjacent floats that change on movement; team_id = small 0/1/2; name = pointer to readable wchar string.

## 4. Code Injection (Auto Assemble) — god mode
Break-on-write → see `sub [rbx+10], eax` (hp -= dmg):
```asm
[ENABLE]
alloc(newmem, 2048, "game.exe"+12345)
label(return); label(dmg_enable); registersymbol(dmg_enable)
alloc(dmg_enable, 4); dmg_enable: dd 0
newmem:
  cmp [dmg_enable], 1
  je take_dmg
  jmp return
take_dmg:
  sub [rbx+10], eax
  jmp return
"game.exe"+12345:
  jmp newmem
  nop
return:
[DISABLE]
"game.exe"+12345:
  sub [rbx+10], eax
dealloc(newmem); dealloc(dmg_enable); unregistersymbol(dmg_enable)
```
Distinguish player/enemy via the team_id offset before skipping damage.

## 5. Mobile games — Unity IL2CPP + Frida
```
1. H3 (IL2CPP dump) → dump.cs (function names + RVA)
2. Find: Player$$TakeDamage, Entity$$get_HP, Coin$$Add
3. Frida hook by RVA = module.base + rva
```
```javascript
function hookIl2Cpp(modName, rva, cb) {
    const mod = Process.findModuleByName(modName);
    if (!mod) throw new Error(modName + " not loaded");
    Interceptor.attach(mod.base.add(rva), cb);
}
hookIl2Cpp("libil2cpp.so", 0x1A2B3C4, {
    onLeave() { const s0 = this.context.s0; console.log("HP =", s0); }  // ARM64 float return in s0/d0, NOT x0
});
```
Light anti-cheat: use frida-gadget / rename frida binary / hook the check after load (F1 timing). **Server-authoritative** → client patching is pointless.

## 6. Client-side vs server-side
| Sign | Conclusion |
|------|-----------|
| Value change persists | client-side → hackable |
| Value reverts / kicked | server-authoritative → patching useless |
| Teleport rejected | coords server-validated |

## 7. Game toolchain
CE (scan/pointer/struct/inject) · x64dbg (native debug) · H3 (IL2CPP) · F1 (Frida) · H1 (DEX) · E (dnSpy for .NET/Mono games) · speedhack or hook `GetTickCount`/`QueryPerformanceCounter`

## 8. Game anti-patterns
- Exact-scan encrypted values → scan changed/unknown
- Trusting a pointer chain not re-validated after restart
- Injecting an instruction shared by player/enemy without team filter
- Reading `x0` for floats on ARM64 → use `s0`/`d0`
- Freezing server-authoritative values

---
