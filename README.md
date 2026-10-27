# Repeated custom-header verification

OllamaJS base `c276d078eee37a0df003b9ee2120ec70327f32e9`, source `1a01bafe326af583a6b410604fd198695c6ee4e7`, tree `f5e7f5ec4286a58f9e1a444181aaeee2574a5f2c`.

Repeated `HeadersInit` tuple entries lost earlier values; mixed-case duplicates could change order. Repeated Set-Cookie values in Headers objects also lost earlier entries. The change groups repeated names and reads their native combined value, retaining singleton tuple casing/raw values, plain-record behavior, and reserved defaults.

- Linux Node 16.20.2/18.20.8/20.20.2: normal configured npm ci/build; Node 20 coverage dependency install, lint, and coverage all exit 0. Baseline 47 tests; candidate 63.
- Windows matching runtime build matrix and functional coverage checks pass; Windows install commands include --no-audit/--no-fund and are additional coverage, not literal Linux CI argv.
- Sixteen new regressions: baseline 14 fail/2 pass -> candidate 16 pass.
- The same actual local npm-pack tarball is independently installed in Windows and Linux. All 19 shipped files match; all four ESM/CJS Node/browser public exports make real local HTTP list/stream-generate calls: baseline 8 pass/40 fail -> candidate 48 pass on each OS.
- Independent actual public HTTP cases: baseline 42/66 -> candidate 66/66. Sixty synthetic Config.fetch auth-control calls cover 30 comparisons, with no new environment-token injection in the tested cases. No real cloud/model requests.

VALIDATION.md explains exact commands, source/package bindings, compiler limits, network recovery, and observer boundaries. This is local verification; hosted checks and maintainer acceptance are tracked separately on the PR.

Raw payload is copied byte-for-byte through an explicit allowlist. RAW-MANIFEST.json records length/SHA256/Git blob for every other file. Large third-party PR/comment dumps, runtime archives, old candidate artifacts, and environment/credential dumps are excluded. The two package tgz files contain MIT-licensed OllamaJS package code; LICENSE is included.

AI assistance: implementation and verification used OpenAI Codex.
