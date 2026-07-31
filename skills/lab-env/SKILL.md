---
name: lab-env
description: "Lab environment: isolation model (VMs, network, snapshots), toolchain bootstrap by platform (winget/pipx/cargo), smoke tests, safe-hands rules."
risk: offensive
when-to-use: "Use when: fresh machine/VM — isolation setup, toolchain bootstrap, smoke tests. Not when: mid-engagement with tools already installed (skip to the relevant skill)."
---

# Lab Environment & Toolchain

## 1. Isolation model

| Work | Host | Network |
|------|------|---------|
| Static RE (no detonation) | host or VM | none needed |
| Dynamic user-mode (x64dbg, Frida, CE) | VM, snapshotted | host-only or NAT |
| Malware detonation / sandbox | dedicated VM (FlareVM/REMnux) | **no internet egress** — FakeNet-NG/INetSim only |
| Kernel debugging | VM + debugger VM (serial/network) | host-only |
| Cloud / k8s attacks | host or VM | internet |

Rules: disposable snapshots, no host mounts or shared clipboard when detonating, one analysis per VM, revert after each sample.

## 2. Toolchain bootstrap

Tool versions and alternatives: **TOOLS.md** (collection root). If a tool fails to build/run, check its entry there before debugging.

### Windows (winget)
```powershell
winget search dnspy        # find exact package ids before installing
winget install --id dnSpyEx.dnSpy -e
winget install --id Ghidra.Ghidra -e
winget install --id Microsoft.PowerShell -e
```
x64dbg / Cheat Engine / IDA / WinDbg: download manually (no reliable winget ids) — verify signatures.

### Python tooling (pipx/pip)
```bash
pipx install frida-tools            # frida CLI + frida-ps
pip install capa pyyaml                             # FLARE capa
pip install scapy boofuzz mitmproxy                # network
pip install unblob                                   # firmware
pipx install yara-python || pip install yara-python  # YARA bindings
```

### Rust tooling (cargo)
```bash
cargo install il2cpp_dumper          # Unity metadata > v39
cargo install heimdall               # EVM disassembler/decompiler
```

### Linux (apt + others)
```bash
sudo apt install binutils gdb strace ltrace radare2 tcpdump wireshark-common
sudo apt install binwalk
pipx install unblob
```

## 3. Smoke tests (5 min sanity)

After installing, verify each critical tool actually runs:

```bash
frida --version && frida-ps -U                # device attached?
ghidra --version || ghidraRun                 # launch check
x64dbg --help                                 # or open once manually
upx --version; capa --version; yara --version
wasm2wat --version                            # wabt
anvil --version                               # foundry EVM fork
docker version                                # for k8s/container labs
```

Windows equivalents: run each GUI once, verify `dnSpyEx` opens a test .NET assembly, `x64dbg` attaches to notepad, `dumpbin /exports` on a system DLL.

## 4. Lab quickstarts

### Windows RE VM
1. Fresh Windows install → snapshot "clean"
2. Install: winget id list above + x64dbg, WinDbg, ScyllaHide, Cheat Engine, IDA (if licensed), Procmon
3. Disable Defender real-time (lab) → snapshot "tools"

### Malware VM
1. Windows + FlareVM (`Invoke-Expression (New-Object Net.WebClient).DownloadString('https://raw.githubusercontent.com/mandiant/flare-vm/main/install.ps1')`)
2. FakeNet-NG configured, no egress; snapshot "detonate"
3. Linux: REMnux OVA or `remnux` docker images

### Kernel debug pair
- Target: `bcdedit /dbgsettings serial debugport:1 baudrate:115200` + `/debug on`
- Host: WinDbg → COM1 @ 115200 (parity settings must match)

### Mobile lab
- Android emulator (rooted) + adb + frida-server matching host frida major
- iOS: jailbroken device + frida-server + ssh

### EVM lab
```bash
anvil &                              # local fork of mainnet: anvil --fork-url <rpc>
cast call 0xADDR "balanceOf(address)(uint256)" 0xUSER --rpc-url http://127.0.0.1:8545
```

## 5. Anti-patterns

- Installing tools ad-hoc per task → bootstrap once per VM, snapshot
- Winget guessing ids → `winget search` first
- Detonating on the host (no VM) "just this once"
- Frida host/device version mismatch (silent attach failures)
- Forgetting network isolation → sample phones home
- Testing cloud/k8s moves against a target's prod instead of a lab replica
