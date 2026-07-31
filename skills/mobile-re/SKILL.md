---
name: mobile-re
description: "Mobile RE: Android DEX dumping from packed apps, iOS app decryption (uncrack), Unity IL2CPP symbol extraction for IDA/Ghidra."
risk: offensive
when-to-use: "Use when: Android/iOS apps — packed DEX, iOS decryption, Unity IL2CPP symbol extraction. Not when: desktop binaries (use D/F/G) or server-side APIs (use B)."
---

# Mobile RE

## 1. Android DEX Dumper (packed apps)

Dump DEX from a running Android app's memory. Needs the `panda-dex-dumper` binary (from P4nda0s/reverse-skills: `skills/rev-dex-dumper/panda-dex-dumper` — clone the repo to obtain it).

```bash
# 1. Push tool
adb push panda-dex-dumper /data/local/tmp/
adb shell chmod +x /data/local/tmp/panda-dex-dumper

# 2. Resolve package (if unknown — foreground app)
adb shell dumpsys activity top | grep 'ACTIVITY' | tail -1 | awk '{print $2}' | cut -d/ -f1

# 3. Run (needs root — ptrace attach)
adb shell "cd /data/local/tmp && ./panda-dex-dumper -p $(adb shell pidof <pkg>)"

# 4. Pull + clean up
adb pull /data/local/tmp/panda/ ./
adb shell rm -rf /data/local/tmp/panda/ /data/local/tmp/panda-dex-dumper
```

Guidelines: verify `adb devices` first; wait for the app past the splash screen (packer decrypts DEX only after class-loader init); empty `pidof` → `adb shell monkey -p <pkg> -c android.intent.category.LAUNCHER 1`; packed apps usually produce several DEX — pull everything.

## 2. iOS App Decryption (砸壳)

Dump the decrypted binary from a jailbroken device via frida-ios-dump (`https://github.com/P4nda0s/frida-ios-dump`).

Prereq: jailbreak + SSH, frida-server (`/usr/sbin/frida-server -D &`), host `pip3 install frida frida-tools`.

```bash
# Install (TypeScript agent must be compiled first)
git clone https://github.com/P4nda0s/frida-ios-dump.git && cd frida-ios-dump
pip3 install -r requirements.txt
npm install --ignore-scripts && npx frida-compile dump.ts -o dist/dump.js

# Resolve bundle id
frida-ps -H <ip> -a

# Dump (app MUST be running)
python3 dump.py -H <ip> -u mobile -P alpine <bundle_id>

# Verify decryption: cryptid must be 0
otool -l dumped_app/Payload/<App>.app/<Bin> | grep -A4 LC_ENCRYPTION_INFO
```

Troubleshooting: `cryptid 1` → dump failed, app must be running; frida-server major version must match host frida; anti-jailbreak apps terminate → bypass detection first.

Output → static analysis (IDA/Ghidra) · `class-dump <bin> > headers.h` · string search · combine with F1 (Frida) / D1 (symbols).

## 3. Unity IL2CPP Symbol Dump

Unity IL2CPP compiles C# to native; C# names survive in `global-metadata.dat`. Recover the native-address ↔ C#-name mapping.

Files: iOS `Frameworks/UnityFramework.framework/UnityFramework` + `Data/Managed/Metadata/global-metadata.dat`; Android `lib/{arch}/libil2cpp.so` + `assets/bin/Data/...`.

Tool: **roytu/Il2CppDumper** (branch `v39`) for Unity 6 (metadata v39); the Perfare original supports only v29 (Unity ≤2021). For metadata newer than v39 (recent Unity releases), use the actively-maintained Rust **il2cpp_dumper** (`cargo install il2cpp_dumper`). Tool versions: TOOLS.md.

```bash
git clone -b v39 https://github.com/roytu/Il2CppDumper.git && cd Il2CppDumper
DOTNET_ROLL_FORWARD=LatestMajor dotnet build -c Release
DOTNET_ROLL_FORWARD=LatestMajor dotnet run --project Il2CppDumper/Il2CppDumper.csproj -c Release --framework net8.0 -- "$BINARY" "$METADATA" output_dir
# Exit 134 (Console.ReadKey) is normal; macOS SIGKILL → codesign -s -
```

Output: `script.json` (decimal Address — convert to hex for IDA) · `dump.cs` (RVA/VA + classes) · `il2cpp.h` (structs) · `ida_py3.py` (IDA rename). Import: IDA `File → Script file → ida_py3.py`; Ghidra via `ghidra.py`.

---
