---
name: osint-recon
description: "OSINT & recon: subdomains/cert transparency, GitHub dorking, breached-credential lookups, metadata, search dorks, active recon, tooling."
risk: offensive
when-to-use: "Use when: engagement start — subdomains, CT logs, GitHub dorking, breached-creds for your own data, search dorks. Not when: already deep in binary RE (skip to D/F) or targeting people (out of scope)."
---

# OSINT & Recon

## 0. Scope check

Target is your own (binary/game/machine), a lab, a CTF, or a sample you're allowed to analyze → proceed, no confirmation needed. Unauthorized third-party live targets (prod, SaaS, others' accounts) → stop; policy in README A5.

Passive (public records, search engines, certificate logs) needs no direct contact with the target; **active** recon (port scans, HTTP probes) touches the target — keep it on authorized scope.

## 1. Subdomain & infrastructure (passive)

```bash
# cert transparency — the biggest passive source
curl -s "https://crt.sh/?q=%25.example.com&output=json" | jq -r '.[].name_value' | sort -u
subfinder -d example.com -silent          # multi-source (CT, passive DNS, ...)
amass enum -passive -d example.com        # passive only
```
Cross-check with: `dnsx -l subs.txt` (resolve), SPF/DMARC records reveal mail infrastructure (`dig TXT example.com`), `whois` for org ownership, `shodan`/`censys` for exposed services on found IPs (authorized scope only).

## 2. GitHub dorking (secret/code search)

```
org:example "aws_access_key_id"
org:example filename:.env
org:example "BEGIN RSA PRIVATE KEY"
org:example "password" extension:sql
org:example token= AND (slack OR github OR api)
```
Follow with `trufflehog github --org example` (scans public repos for verified secrets) and `gitleaks detect --source <repo>`. API rate limits: `gh search code` is limited — use `github.com/search` with dorks via browser for volume.

## 3. Search dorks (Google/Bing)

| Dork | Finds |
|------|-------|
| `site:example.com filetype:pdf` | documents (metadata, internal info) |
| `site:s3.amazonaws.com example` | public buckets |
| `inurl:example.com intext:"password"` | login pages / configs |
| `site:pastebin.com example` | pastes with creds |
| `site:example.com inurl:admin OR inurl:phpmyadmin` | exposed admin panels |
| `intitle:"index of" "example.com"` | open directory listings |
| `site:example.com filetype:env OR filetype:sql` | config dumps |

## 4. Breached credentials & metadata

- Breach lookups (for authorized analysis of your own data, or incident response): haveibeenpwned (email API), dehashed/leakcheck (paid), local breach DBs in labs
- Never enter third-party emails into lookups without authorization — that's targeting a person
- Document metadata: `exiftool -a -u file.pdf` — creator, printer, GPS (photos), revision history; `pdftotext` for hidden layers; OLE extraction (`oleid`/`olevba`) for macros (malware skill M cross-ref)

## 5. Framework — passive → active

1. **Org profile:** whois, DNS (SPF/DMARC/NS), tech stacks from job postings, crt.sh
2. **People:** LinkedIn/social → job title → likely tech (permissions model), GitHub profile → personal repos with internal-ish names
3. **Code:** GitHub dorks → leaked keys, internal endpoints, staging URLs
4. **Enumerate:** subdomains → resolve → technology fingerprint (headers, favicon hash, JS)
5. **Prioritize:** staging/dev/test subdomains, old unpatched services, exposed admin/grafana/jenkins
6. **Hand off:** findings feed B (web/API), T (cloud), U (containers), or S (AI agents)

## 6. Toolchain

subfinder/amass/dnsx (passive DNS) · crt.sh API (CT) · nuclei (template scanning on authorized scope) · httpx (fingerprint) · trufflehog/gitleaks (secrets) · exiftool (metadata) · theHarvester (emails/domains) · shodan/censys (surface, authorized). Versions: TOOLS.md.

## 7. Anti-patterns

- Port-scanning everything found passively → violates scope; passive first, active only on authorized scope
- Stopping at subdomain list — resolve, fingerprint, then prioritize
- Dorking with plain keywords → use filetype/inurl/site operators
- Entering others' emails in breach lookups (targeting people, not systems)
- Trusting single-source results — cross-check crt.sh vs subfinder vs DNS
