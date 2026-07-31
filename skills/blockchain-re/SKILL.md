---
name: blockchain-re
description: "Blockchain/smart-contract RE: EVM disassembly, bytecode decompilation, storage-slot layout recovery, reentrancy/overflow/access-control patterns."
risk: offensive
when-to-use: "Use when: EVM bytecode/smart contracts — disassembly, decompilation, storage layout, vulnerability patterns. Not when: traditional binaries (use D) or off-chain APIs (use B)."
---

# Blockchain / Smart-Contract RE

## 1. EVM model (context)
- Accounts (EOA/contract), each contract = bytecode + persistent **storage slots** (256-bit slots)
- Execution input = **calldata**: 4-byte function selector + ABI-encoded args
- OPCODES: stack machine; `SLOAD/SSTORE` = storage access, `CALL/DELEGATECALL` = external calls (reentrancy surface), `CALLDATALOAD` = inputs

## 2. Disassemble bytecode
```bash
# via evm disassembler (heimdall / evm-codes / py-evm)
python -m heimdall disassemble contract.bin > contract.opcodes
```
Selector identification: first 4 bytes of calldata → 4-byte hash of the signature (`keccak("transfer(address,uint256)")[:4]`). Database tools (4byte.directory, openchain selectors) resolve common ones; unknown → brute with a signature dictionary or analyze call targets.

## 3. Decompilers
| Tool | Notes |
|------|-------|
| heimdall-rs (rust) | modern, free, active |
| dedaub | online, decent pseudocode |
| panoramix | online, older but usable |
| Remix IDE (via Vyper/solidity metadata) | when source/metadata available |

Use decompiled pseudocode to reconstruct: function boundaries, storage layout, external call graph, state-changing conditions.

## 4. Storage layout recovery
Storage = simple key-value (256-bit slots). Deterministic Solidity layout (unless assembly): state variables in order; mappings/arrays via hashing (`keccak256(slot)`). Recover by:
- Trace `SSTORE`/`SLOAD` slot indices in decompiled code
- Read live state: `eth_getStorageAt(addr, slot, "latest")` — align slots with recovered variables
- Events (`LOGn` topics) reveal parameter usage and can leak values

## 5. Vulnerability patterns in bytecode
| Pattern | Bytecode evidence | Check |
|---------|-------------------|-------|
| Reentrancy | `CALL/DELEGATECALL` to external addr BEFORE state writes; no `CEI` (checks-effects-interactions) | follow CALL targets + write order |
| Integer overflow | `ADD/SUB` on storage-backed values without `require`/overflow checks | arithmetic near `SSTORE` |
| Access control | no `CALLER` (address(this).owner) comparison before privileged op | `ORIGIN/CALLER` usage |
| Uninitialized storage | `SSTORE` to slot not written by constructor | diff storage pre/post |
| Flash-loan/price oracle | reading spot price via external `CALL` | check oracle source |

Map findings back to functions (selector → recovered name) for the report. Verify live impact with `eth_call` on a fork (hardhat/anvil) before claiming.

## 6. Blockchain RE anti-patterns
- Reading bytecode linearly as if x86 → it's a stack machine; disassemble first
- Ignoring selectors → can't map functions; resolve signatures first
- Assuming storage layout matches source order when assembly/mappings are used
- Testing on mainnet instead of a fork snapshot (anvil/hardhat)


---
