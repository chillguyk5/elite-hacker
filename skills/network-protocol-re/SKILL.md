---
name: network-protocol-re
description: "Network/protocol RE: traffic capture, TLS keylog decryption, custom binary protocol parsing, replay and fuzzing, MITM with cert-pinning bypass."
risk: offensive
when-to-use: "Use when: traffic capture, TLS decryption, custom binary protocols, replay/fuzzing, MITM with pinning bypass. Not when: passive/defensive traffic analysis (use W) or LLM-app traffic only (use S)."
---

# Network & Protocol RE

## 0. Scope check

Target is your own (binary/game/machine), a lab, a CTF, or a sample you're allowed to analyze → proceed, no confirmation needed. Unauthorized third-party live targets (prod, SaaS, others' accounts) → stop; policy in README A5.

## 1. Capture — tool selection
| Situation | Tool |
|-----------|------|
| Interactive GUI | Wireshark |
| CLI / scripting | tshark |
| Linux server | tcpdump |
| App bypassing system stack (some games/apps) | hook send/recv via Frida (F1) |

Npcap (Windows, enable loopback to capture localhost); libpcap (Linux/macOS).

## 2. Filtering — BPF & display filters
```bash
tcpdump -i eth0 'host 10.0.0.5 and port 8443' -w cap.pcap
tshark -r cap.pcap -Y "tcp.stream eq 3"
# useful: ip.addr==x · tcp.port==x · tls · http.request.uri contains "login"
```

## 3. TLS decryption — read plaintext
```bash
set SSLKEYLOGFILE=C:\tmp\sslkeys.log    # for clients honoring it (browser, curl...)
```
Wireshark: Preferences → Protocols → TLS → (Pre)-Master-Secret log filename → that file.
Clients that ignore keylog (games, custom TLS apps) → Frida-hook `SSL_set_keys`/`PRF`, or hook `SSL_read`/`SSL_write` to grab plaintext directly (F1).

## 4. Protocol RE — unknown (binary/custom) protocols
**Step 1 — observe multiple samples:** repeat behavior, diff packets → constant parts (magic/version/type) vs variable parts (length/payload/counter).

**Step 2 — framing:**
| Type | Sign |
|------|------|
| Length-prefix | first 2/4 bytes = length of the rest |
| Delimiter | ends with `\n`/`\r\n`/`\0` |
| Fixed-size | all packets same length |
| Magic header | constant leading bytes (`0xAA 0x55`, `XYZ\0`) |

**Step 3 — endianness:** `00 1C` = 28 (BE) or `1C 00` (LE)? Cross-check against the real payload length.

**Step 4 — probing parser:**
```python
import struct
def parse(data: bytes):
    magic, ver, mtype, length = struct.unpack(">2sBBH", data[:6])   # adjust endian/format
    return data[6:6+length]
```
**Step 5 — "random-looking" payload:** try zlib decompress / known-plaintext XOR before concluding encryption; find keys by hooking the encrypt/decrypt point (F1).

## 5. Replay & fuzz
```python
from scapy.all import rdpcap, send, IP, TCP, Raw
p = rdpcap("cap.pcap")[42]
p[Raw].load = b"\x00\x1c" + b"A"*28
p[IP].dst = "10.0.0.5"
del p[IP].chksum; del p[TCP].chksum
send(p)
```
TCP replay needs correct seq/ack → recreate with a custom client using the parsed protocol, or use `tcpreplay`.

**Custom-protocol fuzzing — boofuzz:**
```python
import boofuzz as fuzz
sess = fuzz.Session(target=fuzz.Target(connection=fuzz.SocketConnection("10.0.0.5", 8443)))
fuzz.s_static(b"\xAA\x55")                 # magic
fuzz.s_byte(1, name="ver"); fuzz.s_byte(1, name="type")
fuzz.s_size("payload", length=2, endian="big")
fuzz.s_string("A"*10, name="payload")
sess.connect(...); sess.fuzz()
```
Watch for server crash/hang → parser bug (overflow/null-deref); combine with G (dynamic-debug) attached to the server.

## 6. MITM — HTTP(S) & cert pinning
```bash
mitmproxy -p 8080
mitmdump -w flow.mitm -s addon.py
```
```python
def response(flow):
    if "license" in flow.request.pretty_url:
        flow.response.text = '{"valid": true}'
```
Install mitmproxy's CA on the machine/client. **Cert pinning** → bypass with objection / Frida ssl-pinning-bypass (`TrustManager.checkServerTrusted`, `SSL_CTX_set_verify`, OkHttp `CertificatePinner`), or patch the binary (I), or hook the verify to return true (F1).

## 7. Network toolchain
Wireshark/tshark/tcpdump (capture) · Npcap (Win loopback) · Wireshark + SSLKEYLOGFILE (TLS) · Frida (dump keys/plaintext) · scapy (build/replay) · boofuzz (fuzz) · mitmproxy/mitmdump (MITM) · objection/Frida (pinning bypass)


---
