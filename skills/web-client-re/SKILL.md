---
name: web-client-re
description: "Deobfuscate obfuscated/minified JavaScript (Babel AST, string-array, control-flow flattening), reverse WASM (wasm2wat/wasm-decompile), automate browsers via DevTools Protocol."
risk: offensive
when-to-use: "Use when: obfuscated/minified JS bundles, eval packers, WASM modules, browser-side auth logic. Not when: server-side API logic (use B) or .NET/native binaries (use E/D)."
---

# Web Client-Side RE

## 0. Scope check

Target is your own (binary/game/machine), a lab, a CTF, or a sample you're allowed to analyze → proceed, no confirmation needed. Unauthorized third-party live targets (prod, SaaS, others' accounts) → stop; policy in README A5.

## 1. JavaScript Deobfuscation

Obfuscated/minified JS (webpack bundles, eval-based packers, string-array ciphers, control-flow flattening).

### Workflow
```
1. Identify packer pattern:
   - webpack: `!function(e){var t={}...}([function(e,t){...}])`
   - eval/Function(): `eval(atob(...))` / `new Function(...)`
   - string-array: `var _0x1a2b=['xxx','yyy']` + decode loop
   - control-flow flattening: big switch on state var
2. Beautify + auto-deobfuscate (tools below)
3. Read result; for eval packers: run in controlled env (Node with stubs) to materialize code
4. Trace from entry: where obfuscated code touches DOM/network/storage
```

### Tools
| Task | Tool |
|------|------|
| Parse/transform AST | Babel (`@babel/parser`, `@babel/traverse`) |
| One-shot deobfuscate | webcrack, deobfuscator.io, jsnice |
| Beautify | prettier, js-beautify |
| Run + inspect | Node with stubs, Chrome DevTools |

### Babel-based deobfuscation skeleton
```javascript
const parser = require("@babel/parser");
const traverse = require("@babel/traverse").default;
const generate = require("@babel/generator").default;
const fs = require("fs");

const ast = parser.parse(fs.readFileSync("target.js", "utf8"));

// 1) inline string-array decode: replace calls of the decoder
const decoderNames = new Set();
traverse(ast, {
  FunctionDeclaration(path) {
    if (path.node.id && /^_0x/.test(path.node.id.name)) decoderNames.add(path.node.id.name);
  },
  CallExpression(path) {
    if (path.node.callee.name && decoderNames.has(path.node.callee.name)
        && path.node.arguments.every(a => a.type === "StringLiteral")) {
      // evaluate the decode function in a VM and substitute the literal
      // (requires an interpreter or manual port of the decode loop)
    }
  }
});
fs.writeFileSync("clean.js", generate(ast).code);
```
Real string-array decoders need an interpreter (run decoder with captured args in a sandbox) — skeleton shows the AST shape to look for.

### Control-flow flattening
Big `switch(dispatcher)` returning next block id. Strategy: recover real edges by running each case once (dynamic trace with Node/CDP), or use static dataflow on the dispatcher arithmetic. Prefer dynamic: instrument `switch` cases and record block ids → rebuild linear CFG.

## 2. WASM Reverse Engineering

WASM (`.wasm`) from web games / obfuscated logic. Binary format → readable text via WABT.

### Workflow
```
wasm2wat target.wasm -o target.wat        # binary → text (WABT)
wasm-decompile target.wasm -o target.dcmp  # pseudo-C (WABT)
# or load in Ghidra with WASM plugin, or radare2
```
- `wat`: 4-line tables (`(func $f (param i32) (result i32) local.get 0 i32.const 1 i32.add)`), `memory`, `export`, `import`
- Watch: string constants via `data` segments; function boundaries are explicit (no prologue scanning)
- Imported functions (`env.*`) reveal host API used — the attack surface (fetch, atob, crypto)

### Toolchain
`wat2wasm`/`wasm2wat`/`wasm-decompile` (WABT) · `wasm-objdump` · Ghidra WASM extension · `wabt` Node bindings for scripting · `wasm-decompile` for pseudo-C

## 3. Browser Automation / DevTools Protocol

Automate browser to exercise client logic, extract secrets, or hook runtime state.

```python
# Chrome DevTools Protocol via websocket (or use playwright/puppeteer wrappers)
import asyncio, json, websockets

async def eval_js(cdp_url, expr):
    async with websockets.connect(cdp_url) as ws:
        await ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate",
                                  "params": {"expression": expr, "returnByValue": True}}))
        res = json.loads(await ws.recv())
        return res.get("result", {}).get("result", {}).get("value")
```

Useful: `Runtime.evaluate` (read globals), `Debugger.setBreakpointByUrl` (pause on obfuscated code), `Network.getResponseBody` (capture payloads), `Page.addScriptToEvaluateOnNewDocument` (pre-inject hooks). Playwright/Puppeteer make this ergonomic — use them when available.

### Anti-pattern (client-side)
- `eval`-packer: paste into `node -e` unmodified → crashes on DOM refs; stub `document`/`window` first
- Assume beautified = readable → still need string-array decode
- Skip WASM because "it's compiled" → wasm2wat is cheap and structure is explicit
- Fuzz the whole bundle instead of tracing entry → wasted time

---
