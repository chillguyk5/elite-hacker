---
name: cracking-patching
description: "Crack native binaries: DLL proxy, binary branch patching, license/trial/nag bypass, keygen serial algorithm reversal."
risk: offensive
when-to-use: "Use when: license/trial/nag bypass, keygen, DLL proxy, binary branch patching of a closed-source app you own/authorized. Not when: the app is server-validated (patch is pointless — check J6 first) or you lack a legitimate copy to test against."
---

# Cracking & Patching

## 0. Scope check

Target is your own (binary/game/machine), a lab, a CTF, or a sample you're allowed to analyze → proceed, no confirmation needed. Unauthorized third-party live targets (prod, SaaS, others' accounts) → stop; policy in README A5.

## 0a. Recon before patching
```
PE type (native/.NET) → packer (DIE: UPX/VMProtect/Themida) → protections
(anti-debug, integrity, signing, online verify) → license model
(trial days / serial / HW lock / online)
```
Packed → unpack first (UPX: `upx -d`; VMProtect/Themida: dynamic dump + Scylla). Patching a packed binary is wasted effort.

## 1. DLL Proxy (clean sideloading)
Drop a DLL with a system DLL's name into the app dir, forward all exports to the real DLL, run payload in DllMain.

Commonly proxied: `winhttp.dll` · `version.dll` · `winmm.dll` · `d3d11.dll` · `dxgi.dll` · `xinput1_3.dll` · `msasn1.dll`

**Export forwarding via .def** (no per-function wrappers — get original exports with `dumpbin /exports`):
```def
LIBRARY version
EXPORTS
  GetFileVersionInfoA = C:\Windows\System32\version.GetFileVersionInfoA
  VerQueryValueW = C:\Windows\System32\version.VerQueryValueW
```
Build: `cl /LD proxy.c proxy.def`

**Payload DllMain** (run on a separate thread — never call LoadLibrary of the real DLL inside DllMain; loader-lock deadlock):
```c
#include <windows.h>
void __declspec(noinline) payload(void) { /* hook / patch memory */ }
BOOL WINAPI DllMain(HINSTANCE h, DWORD reason, LPVOID) {
    if (reason == DLL_PROCESS_ATTACH) {
        DisableThreadLibraryCalls(h);
        CreateThread(NULL, 0, (LPTHREAD_START_ROUTINE)payload, NULL, 0, NULL);
    }
    return TRUE;
}
```

## 2. Binary Patch — license-check branch
Most license checks reduce to one branch after `cmp`/`test`:
```asm
call    check_license      ; EAX = 0 fail / 1 ok
test    eax, eax
je      show_nag_or_exit   ; ← target
; "registered" path
```
| Method | Original bytes | New bytes |
|--------|----------------|-----------|
| Invert branch | `74` (je) | `75` (jne) |
| Short NOP | `74 xx` | `90 90` |
| Long NOP (6B) | `0F 84 r4` | `90 90 90 90 90 90` |
| Force jump | `74` | `EB` (jmp) |

Read the CFG (IDA/x64dbg) to know whether the "ok" path is fall-through or the branch.

**File offset vs RVA:**
```
file_offset = RVA - section.VirtualAddress + section.PointerToRawData
```
```python
import pefile
pe = pefile.PE("target.exe")
print(pe.get_offset_from_rva(0x1234))
```
After patching: if integrity/self-checksum/signing exist → also patch the verifier (`CheckSumMappedFile`/`MapFileAndCheckSum`) or resign with a test cert: `signtool sign /f test.pfx target.exe`.

## 3. License / Trial / Nag — patch point per model
| Model | Patch point |
|-------|-------------|
| Day-based trial (registry/file timestamp) | time-compare function, or write expiry = `0x7FFFFFFF` |
| Nag screen | hook `MessageBoxW` → IDOK / patch caller |
| Offline serial | reverse algorithm → keygen (I4), or patch the compare branch |
| HW lock (MAC/HWID) | hook `GetAdaptersInfo`/`DeviceIoControl` → fixed value |
| Online verify | block host (hosts/firewall), or patch fail→ok branch |

Fast locate: search strings "trial"/"expired"/"register"/"license" → xref → the check region.

## 4. Keygen — reverse the serial algorithm
1. Find the validate function (xref from the Activate/Check button)
2. Read the algorithm: xor/rotate/modular/table; identify primitives via magic numbers (D1). Real RSA/EC → keygen infeasible, go back to patching
3. Write the forward path in Python, verify against a known-valid key
4. Invertible → write inverse; one-way hash → brute the weak part or patch

```python
# SKELETON — replace constants/ops with what you read in the binary
def make_serial(name: str, hwid: int) -> str:
    acc = 0x1337
    for i, ch in enumerate(name.upper()):
        acc = (acc * 0x101 + ord(ch) + i) & 0xFFFFFFFF
    acc ^= hwid
    acc = (acc * 0x5BD1E995) & 0xFFFFFFFF
    acc ^= acc >> 15
    return "-".join(f"{(acc >> (8*i)) & 0xFF:02X}" for i in range(4))
```
Verify with Appcall (D3) or a Frida hook on the validate function using the generated serial.

## 5. Cracking toolchain
CFF Explorer/PE-bear (PE) · DIE (packer) · `upx -d` · x64dbg + Scylla (patch/dump/IAT) · IDA/Ghidra (static) · Resource Hacker (dialogs) · `signtool` (resign) · dnSpy (E)

---
