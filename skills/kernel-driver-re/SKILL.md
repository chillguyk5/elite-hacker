---
name: kernel-driver-re
description: "Kernel/driver RE: Windows WDM/WDF IRP and IOCTL mapping, kernel debugging, rootkit technique identification, Linux LKM hooking."
risk: offensive
when-to-use: "Use when: Windows drivers (WDM/WDF), kernel debugging, rootkit identification, Linux LKMs. Not when: user-mode binaries (use D/F/G) or firmware/UEFI (use O)."
---

# Kernel & Driver RE

## 0. Scope check

Target is your own (binary/game/machine), a lab, a CTF, or a sample you're allowed to analyze → proceed, no confirmation needed. Unauthorized third-party live targets (prod, SaaS, others' accounts) → stop; policy in README A5.

## 1. Windows driver model (WDM/WDF)
A driver is a PE with `DRIVER_ENTRY` export. Entry: build a `DRIVER_OBJECT`, register dispatch routines:
```c
// IRP dispatch table: read/write/ioctl entry points
DriverObject->MajorFunction[IRP_MJ_CREATE]          = Create;
DriverObject->MajorFunction[IRP_MJ_DEVICE_CONTROL]  = DeviceControl;   // IOCTL handler
DriverObject->MajorFunction[IRP_MJ_READ]            = Read;
```
RE workflow:
1. Find `DRIVER_ENTRY` (entry point in PE header)
2. Follow where it writes `MajorFunction[]` — those offsets are the dispatch routines
3. For IOCTL analysis: find the device name (`IoCreateDevice`), then map `DeviceIoControl` codes from userland (same dwIoControlCode) to handler logic
4. Handler pattern: `IOCTL code → switch → copy in/out buffers (METHOD_BUFFERED/NEITHER)`

Key security-relevant patterns: unchecked `InputBufferLength` (overflow), `METHOD_NEITHER` without `ProbeForWrite` (arbitrary write), `ZwCreateFile` with paths, `MmMapIoSpace` (physical memory).

## 2. Kernel debugging
```
VM setup (VirtualBox/VMware/Hyper-V):
  target:  bcdedit /dbgsettings serial debugport:1 baudrate:115200
  target:  bcdedit /debug on
  host:    WinDbg → Kernel Debug → COM → com1, baud 115200
  target:  break on boot to connect (F8 → Disable Driver Signature or press break)
```
Commands: `kd> lm` (modules) · `!drvobj <addr>` (driver object + dispatch) · `!irp` · `bp driver!DispatchDeviceControl` · `!process 0 0` (process list) · `!pte`/`!pool` (memory)

## 3. Rootkit techniques (defensive identification)
| Technique | What it does | Where to look in RE |
|-----------|--------------|---------------------|
| SSDT hooking | patch kernel syscall table (patchguard kills this on x64) | `!pcr` / SSDT enumeration |
| IRP hooking | redirect IRP dispatch of another driver/device | compare MajorFunction against driver image |
| DKOM | hide processes/modules by unlinking list nodes | `!process`, `!module` anomalies |
| Minifilter | intercept file ops (`FltRegisterFilter`) | `fltmgr` loaded filters |
| WDF filter | driver stack insertion | `!devobj`, IRP_MJ_* chains |
| Callback registration | `PsSetCreateProcessNotifyRoutine` etc. | `!pstree` callback lists |

Detect via: comparing dispatch tables to the on-disk driver image, `!drvobj` counts, and unloaded-module markers. PatchGuard (x64) makes SSDT hooking fragile — modern rootkits prefer callbacks/minifilters.

## 4. Linux LKM (defensive)
LKM = ELF relocatable (`readelf -h` says "Relocatable"). Entry via `module_init`. Hooking techniques: syscall table overwrite (KASLR-off/`kallsyms`), `kprobes`/`ftrace`, `security_ops` hooking, `netfilter` (packet interception). Detection: `lsmod` anomalies, comparing `/proc/kallsyms` to memory, `kprobes` blacklist.

## 5. Kernel RE anti-patterns
- Looking for "main" in a driver → entry is `DRIVER_ENTRY` / `module_init`
- Ignoring IOCTL dispatch table → the real attack surface is `MajorFunction[IRP_MJ_DEVICE_CONTROL]`
- Forgetting PatchGuard on x64 → SSDT-hook detection is unrealistic
- Kernel debugging without serial parity settings → WinDbg never connects

---
