---
name: pcap-forensics
description: "Network forensics (defensive): beacon analysis, TLS fingerprinting (JA3/JA4), DNS tunneling, malware C2 pattern detection, IOC extraction, flow stats, Zeek/Suricata."
risk: defensive
when-to-use: "Use when: defensive network analysis — beacon detection, JA3/JA4, DNS tunneling, IOC extraction from captures. Not when: actively attacking/replaying a protocol (use K)."
---

# Network Forensics (PCAP)

Defensive counterpart to K (network-protocol-re).

## 1. Flow stats — find the needle

```bash
# top talkers / protocols (tshark)
tshark -r cap.pcap -q -z conv,ip         # conversations by bytes
tshark -r cap.pcap -q -z io,phs          # protocol hierarchy
tshark -r cap.pcap -q -z endpoints,ip    # endpoints
# flows to rare destinations / unusual ports
tshark -r cap.pcap -T fields -e ip.dst -e tcp.dport | sort | uniq -c | sort -rn | head -30
```
Look for: periodic small flows (beacons), long-lived TLS to uncommon ports, DNS to many unique domains, ICMP with payload.

## 2. Beacon analysis (C2 pattern)

```python
# beacon intervals: cluster per (dst, port) flow timestamps
import dpkt, collections
flows = collections.defaultdict(list)
for ts, pkt in dpkt.pcap.Reader(open("cap.pcap","rb")):
    ...  # key = (ip.dst, tcp.dport); append ts
# diff sorted timestamps per flow → look for stable interval (e.g. 60s ± jitter)
```
Tools: **RITA** (zeek-based beacon detection), `zeek` script `beacon.zeek` (built-in heuristics), or a quick pandas diff. Stable intervals + jitter + same-size payload = classic beacon.

## 3. TLS fingerprinting — JA3/JA4

TLS ClientHello structure fingerprints the client even without decryption:

```bash
zeek -r cap.pcap                          # generates ssl.log with ja3 if enabled
# or with suricata
suricata -r cap.pcap                      # adds JA3S/ja3 fields in eve.json
```
JA3 hash per (cipher suite, extensions, curves) — a unique hash indicates a non-standard client (malware, custom tooling). Track: unique ja3 across hosts, ja3 seen with unusual SNI, TLS to IPs without SNI.

## 4. DNS tunneling & DGA

```bash
# high-entropy subdomains → DGA/tunnel
tshark -r cap.pcap -Y "dns.qry.name" -T fields -e dns.qry.name | sort -u | \
  awk '{print length($0), $0}' | sort -rn | head -20
# unusual record types
tshark -r cap.pcap -Y "dns.qr == 0 && dns.qry.type != 1 && dns.qry.type != 2" -T fields -e dns.qry.name -e dns.qry.type
```
Signals: long labels, base32/hex-looking names, many unique names per client, large TXT responses, frequent `ANY` queries. Cross-check with `scapy` for TXT payload extraction (K4 parsing applies).

## 5. IOC extraction & hunting

```python
from scapy.all import rdpcap
pkts = rdpcap("cap.pcap")
iocs = set()
for p in pkts:
    if p.haslayer("IP"): iocs.add(p["IP"].dst)          # contact IPs
    if p.haslayer("DNS") and p["DNS"].qr: iocs.add(p["DNS"].an.rdata)  # resolved domains
    if p.haslayer("HTTP"): 
        host = p["HTTP"].Host
        if host: iocs.add(host.decode() if isinstance(host, bytes) else host)
```
Emit: IPs, domains, JA3 hashes, file hashes (from `tshark -Y "http.response"` + file carving), then pivot: check IOCs against VT, hunt same IOC in other captures.

## 6. TLS decryption — defensive side

- Key log file: `SSLKEYLOGFILE` (your own clients) — Wireshark prefer → TLS → pre-master-secret log
- Frida hook `SSL_write`/`SSL_read` (F1) on malware to decrypt its own traffic in the lab
- Zeek: `zeek -r cap.pcap` with `SSL::keys` if keylog available

## 7. Workflow (per incident)

1. Flow stats → find unusual flows (top talkers, rare ports, long TLS)
2. Beacon analysis → identify C2 candidates (RITA/zeek)
3. TLS/JA3 + DNS → fingerprint the client, spot tunneling/DGA
4. Extract IOCs → hunt/pivot; correlate with malware triage (M)
5. Report: timeline (host → first contact → persistence), IOC list, detection gaps (missing logging, no TLS visibility)

## 8. Toolchain

tshark/Wireshark · zeek (flow + beacon + ja3) · suricata (IDS + ja3) · RITA (beacon) · dpkt/scapy (python analysis) · Bro-aux/python scripts. Versions: TOOLS.md.

## 9. Anti-patterns

- Diving into packet 1 instead of flow stats first
- Ignoring TLS ClientHello — JA3 works without decryption
- Treating every domain as IOC — filter CDN/telemetry/well-known before reporting
- Missing beacon detection because the interval is irregular (look for jitter patterns, not perfect 60s)
- Forgetting that encrypted traffic still leaks timing/size (metadata analysis)
