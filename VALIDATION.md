# Validation and limits

## Reproduction and source

Check out the exact base commit, apply source/candidate.diff, and use the official runtimes in RUNTIMES.json. The 44-file candidate manifest binds Git blob/mode, canonical LF bytes, and the original Windows checkout bytes. Windows CRLF bridges are explicit; raw logs are not normalized. No complete source archive is needed: the exact Git SHA and per-file manifests identify the public source.

The production change is confined to normalizeHeaders. Single tuple entries are passed through verbatim; only repeated case-insensitive name groups are canonicalized. Headers objects use get(key) to preserve native combined Set-Cookie values. Record headers/default filtering and the API-key injection code are unchanged. Repeated authorization entries can naturally alter their old lossy combined value; the tests do not claim universal equality of every duplicate credential-selection case. Tested cases add no new env bearer injection, and single-header controls preserve prior behavior.

## Required local Linux commands

For Node 16/18/20, each base/candidate source gets normal npm ci and npm run build. Node 20 additionally runs literal npm i -D @vitest/coverage-v8@^2.1.6, npm run lint, and npm test -- --coverage. The caret is preserved as a direct argv token. Coverage/Vitest resolve 2.1.9 on both sides. These normal dependency installs create the recorded package.json/lock overlay; it is not a committed source change. All other tracked bytes/modes match. Local Node 20 build precedes its test dependency install in the same per-version workdir; upstream separates build and test jobs. No hosted Ubuntu execution is claimed.

The final isolated nonroot Linux run has36 commands with real exit 0 and no forced command termination. Its default npm config is fetch-timeout 300000/retries 2/maxsockets 15/audit true; the same bounded process-only recovery for base/candidate uses 60000/1/3 and verbose logging, with audit still true. CLI argv remains the configured command. Successful npm install exit codes are not a security-audit clean claim.

## Installation artifacts and independent runtime

The package archives are normal npm pack outputs from untouched canonical package.json/lock sources and actual builds. The same Windows-built tgz is normally installed into separate consumers on Windows and Linux; each of 19 installed files equals its archive member. The package source utility matches the frozen Git blob and shipped declarations are unchanged. Actual ESM/CJS package imports select both Node and browser public exports. Browser-export checks run on Node; no real-browser or model inference claim is made.

## Compiler checks

On the additional Windows check, the optional default tsc --noEmit has the same 19 pre-existing Node-type/ES-library configuration diagnostics. Both sources pass matched supplemental checks with @types/node@20 and --lib es2020,dom. No source compiler configuration is changed. Required builds and declaration generation pass.

## Recovery and retained boundaries

Two earlier Linux coverage-install harness attempts exceeded their 600-second outer cap and are not passing evidence. Those attempts included no-audit flags. One early tmpfs export via docker cp failed before its container was stopped; its per-command RAM logs were lost, while host progress/timeout and diagnostic snapshots remain privately retained. None is used to claim final gates passed.

The final run streams original bytes to host backup and exports its per-command files through docker exec tar. The export is byte/manifest verified before only the owned container is stopped. During stalls in its two coverage npm processes, an own loopback-only inspector with no published port was opened for read-only diagnostics. The first client used an invalid stdin filename; a later evaluation returned no permitted value, and the candidate evaluation timed out. Clients disconnected, the npm processes subsequently completed normally, and no source/fake exit/skip was introduced. These observation actions are retained in diagnostics; their causal effect and the original stall cause remain unconfirmed. Temporary container cleanup exit 137 after completed commands is separate from the 36 actual command exit 0 results.

Earlier two-line normalization and a too-broad temporary Map annotation are superseded; every claimed final candidate result binds canonical utility SHA b39d98ea534017f679d671bb261a18388d200347897369fef8f14e8ef4007b6e. No paid API, external model, CLA signature, merge, release, or branch deletion is involved.

## Driver provenance

The drivers retain their original absolute evidence/workspace paths; adapt those paths for another machine. scripts/linux-gates.py is the nonexecuted template parsed by the final driver to construct its runner; its older command defaults are superseded by the final driver. Only linux/receipt.json and the final raw payload bind the accepted Linux run.

The baseline14-fail/2-pass negative regression run was performed on Windows only. Linux baseline coverage ran its original47 tests; final Linux candidate ran63 tests, including all16 new regressions. No Linux negative-run count is claimed.
