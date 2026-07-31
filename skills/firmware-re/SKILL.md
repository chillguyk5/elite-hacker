---
name: firmware-re
description: "Firmware/UEFI RE: binwalk/unblob extraction, UEFITool firmware volume parsing, DXE/SMM analysis, bootkits, IoT and console firmware."
risk: offensive
when-to-use: "Use when: firmware images, UEFI modules, bootkits, IoT/console firmware. Not when: plain userland binaries (use D) or kernel drivers (use N)."
---

# Firmware & UEFI RE

## 1. Firmware extraction
```bash
binwalk firmware.bin                       # signatures: filesystems, kernel, squashfs...
binwalk -e firmware.bin                    # extract
# or FirmwareModKit / unblob (better for complex images)
```
Pipeline: `binwalk/unblob` → identify filesystem (squashfs/cpio/jffs2) → mount/extract → find binaries → Ghidra/IDA. For custom formats, hexdump the header and parse fields manually (K4 framing applies).

## 2. UEFI modules
UEFI firmware = **firmware volumes** containing DXE drivers/PEI modules. Anatomy:
```
BIOS image → FV (Firmware Volume) → FFS files (DXE driver, PEI, NV vars, FFS header)
```
```
UEFITool (GUI) / uefiextract (CLI)   # parse FV, list modules
uefi-firmware-parser -i bios.bin     # automated parse
# Extract a DXE driver → it's a PE → load in Ghidra/IDA directly
```
DXE driver entry: `DXE_ENTRY_POINT` protocol registration via `gBS->InstallProtocolInterface` or `gST->ConOut` usage — follow `EFI_BOOT_SERVICES` calls (`gBS->`, `gRT->`) to map functionality. NVRAM variables readable via `getvar`/`setvar` (UEFI shell) — settings/toggles often live there.

## 3. Bootkits (context)
Bootkit = code executed before/at boot. Classes: MBR/VBR (legacy), UEFI DXE/SMM (e.g. LoJax, BlackLotus), bootloader (grub/Windows Boot Manager). SMM/SMM-Modules = highest privilege (System Management Mode), extracted from FV (often `SMM` section), analyzed like DXE but entry via SMM handler table (`EFI_SMM_SW_DISPATCH`). Secure Boot bypass path: revoked cert / CVE in bootloader → check SB policy, db/dbx.

## 4. IoT / console touchpoints
- Router/AP: `binwalk -e` → squashfs → dropbear telnetd backdoors, admin creds in `/etc`, web UI CGI binaries
- Game console/embedded: custom headers, encrypted blobs → identify crypto (D1 magic) → find keys in bootloader/OTP, emulate decrypt with F2
- MCU/SoC firmware: raw binary → Ghidra manual base address (find vector table / reset vector)

## 5. Firmware anti-patterns
- Running binwalk once and stopping → nested archives need recursive extraction
- Forgetting FV-in-FV nesting → UEFI modules hide in nested firmware volumes
- Treating a DXE driver as userland PE → it uses UEFI protocol pointers, not Win32 APIs
- Ignoring NVRAM/secure variables → settings and boot policy live there

---
