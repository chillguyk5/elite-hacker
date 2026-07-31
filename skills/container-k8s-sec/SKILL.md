---
name: container-k8s-sec
description: "Container & Kubernetes security: image analysis, Docker escape (lab), k8s RBAC abuse, service-account tokens, kubelet API, supply chain/SBOM."
risk: offensive
when-to-use: "Use when: container images, Docker runtime, Kubernetes RBAC/API abuse, supply-chain/SBOM. Not when: plain cloud IAM/buckets (use T) or host binaries (use D/F/G)."
---

# Container & Kubernetes Security

## 0. Scope check

Target is your own (binary/game/machine), a lab, a CTF, or a sample you're allowed to analyze → proceed, no confirmation needed. Unauthorized third-party live targets (prod, SaaS, others' accounts) → stop; policy in README A5.

## 1. Container images — static analysis

```bash
# enumerate layers & extract
docker pull <image> && docker history <image> --no-trunc
docker run --rm -it --entrypoint sh <image>        # inspect at runtime
skopeo inspect docker://<image>                    # metadata without pulling
# scan for CVEs and secrets
grype <image>                                      # vulnerabilities
trivy image --scanners vuln,secret <image>         # vulns + embedded secrets
# SBOM (supply chain)
syft <image> -o spdx-json > sbom.json
```
High-value findings in images: hardcoded keys/endpoints, `USER root` + writable dirs, exposed ports, suspicious entrypoints, base images with known RCEs.

## 2. Docker escape (lab-only unless authorized)

Escape primitives depend on privileges given to the container:

| Primitive | Technique |
|-----------|-----------|
| `--privileged` | device access → `nsenter`/`cgroups` escape; `docker run --privileged` on host |
| Capabilities (SYS_ADMIN, SYS_PTRACE) | mount host filesystem via `capsh`/`nsenter`; ptrace into host processes |
| Docker socket mounted | `ls -la /var/run/docker.sock` → spawn a privileged host container |
| HostPID / HostNetwork | read host processes (`ps aux` shows host), network interception |
| CVEs in runtime | dirty-pipe-style escapes (2022-era) — patch levels matter; check `uname -r` |

**Rule: escape attempts happen only in a lab cluster/VM you own** — never against shared production infrastructure.

## 3. Kubernetes — enumeration from inside

Assumed: you have a pod (from an app RCE, SSRF to kubelet, or a misconfigured CI). Kubernetes API is the target — the pod's `serviceaccount` token is the credential:

```bash
TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
APISRV=https://kubernetes.default.svc
# what can this identity do?
curl -sk -H "Authorization: Bearer $TOKEN" $APISRV/apis/rbac.authorization.k8s.io/v1/namespaces/default/rolebindings
curl -sk -H "Authorization: Bearer $TOKEN" $APISRV/apis/rbac.authorization.k8s.io/v1/clusterrolebindings
# can I create pods / exec into others? can I read secrets?
curl -sk -H "Authorization: Bearer $TOKEN" $APISRV/api/v1/namespaces/kube-system/secrets
# full permission probe
kube-hunter --remote $APISRV   # or: kubectl auth can-i --list (if kubectl present)
```
Escalation paths: write `RoleBinding/ClusterRoleBinding` (bind yourself to `cluster-admin`), read secrets (token for `kube-system` service accounts), `pods/exec` into privileged pods, `deployments/patch` to inject sidecars. If the kubelet port 10250 is reachable: `curl -k https://<node>:10250/pods` (anonymous auth check).

## 4. Kubernetes — enumeration from outside (authorized)

```bash
# exposed control plane?
nc -zv <host> 6443 10250 10255 2379        # API, kubelet, kubelet-ro, etcd
# anonymous API access
curl -sk https://<host>:6443/version
# scan cluster config
kube-bench run --targets master,node      # CIS baseline
```
Exposed etcd (2379) without TLS/auth = full cluster compromise: read `--from /registry/secrets` keys. Misconfigured Ingress/NetworkPolicies allow cross-namespace lateral.

## 5. Supply chain

- Base images: untagged/latest, from unknown registries, stale with CVEs
- SBOM diffing: `syft` baseline vs release — detect unexpected dependency changes
- Registries: anonymous pull allowed? (probe `docker pull` without auth)
- CI/CD: secrets in pipelines, privileged builds, cache poisoning

## 6. Methodology

1. Scope: **your own cluster/lab or written authorization** (k8s attacks touch many tenants — blast radius is high)
2. From app code: find container runtime access (docker.sock, kubelet, k8s API token in env)
3. Enumerate identity: RBAC → secrets → pod control
4. Prove: read one secret or create/exec one pod in a sandbox namespace; clean up after
5. Report: initial primitive → RBAC path → impact; include `kubectl auth can-i` output

## 7. Toolchain

docker/skopeo/`docker history` · grype/trivy/syft · kubectl + raw curl (token probing) · kube-hunter/kube-bench · `kubeletctl` (kubelet API) · k9s (cluster nav) · falco (defensive: runtime detection). Versions: TOOLS.md.

## 8. Anti-patterns

- Escaping in a shared/prod cluster "to prove a point" — lab-only
- Stopping at "pod RCE" — the pod is a foothold, the API is the target
- Ignoring the serviceaccount token mounted in every pod
- Forgetting cleanup (created namespaces/roles persist and confuse incident teams)
- Assuming namespaces are a security boundary (they are not)
