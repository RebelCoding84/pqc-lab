# OQS Opt-In Setup (`pqc-real`)

## Why OQS Is Opt-In
- Real liboqs/liboqs-python tooling is heavier than the default repo baseline.
- Keeping OQS in an opt-in environment preserves fast default local workflows and CI.

## Why Default CI Remains Untouched
- The default environment and default tasks stay unchanged.
- OQS bootstrap and real ML-DSA verify tasks are scoped to the `pqc-real` feature/environment only.

## Commands
Run from repository root:

```bash
pixi run --environment pqc-real bootstrap-oqs
pixi run --environment pqc-real preflight-real-mldsa
pixi run --environment pqc-real run-real-verify-first2
```

## Notes
- The bootstrap installs `liboqs` under `.vendor/liboqs` and installs `liboqs-python` into the active `pqc-real` Python environment.
- The first real verify runs are intentionally `c1` and `c8` only.
- `c16` and `c32` are the next contention-discovery steps after `c1` and `c8`.
- Interpret results primarily from each report JSON `summary` object, not only top-level fields.
- These points establish baseline trends before expanding further to `c64/c128`.
- These tools are for prototyping and evaluation workflows only.
- Capacity benchmark results and OQS runtime availability are not a production security claim.
