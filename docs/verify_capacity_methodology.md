# Verify Capacity Methodology (Phase 1)

## Why Verify Before Sign
- Verification is often the dominant operation on service edges and gateways.
- Measuring verify first provides an operational baseline before introducing sign-path variability.
- This phase isolates verify behavior under concurrency so scaling trends can be reviewed early.

## Why a Pre-Generated Signature Pool
- Signing work is excluded from the benchmark loop so verify throughput and latency are not contaminated.
- The pool stores only public verification material (`public_key`, `message`, `signature`).
- No private keys are stored in pool artifacts.

## What Phase 1 Measures
- Verify-only operations over a fixed pool.
- Concurrency effects via bounded worker execution.
- Throughput and tail latency (`p50`, `p95`, `p99`, `max`).
- Backpressure proxy via `requests_in_flight_max`.
- Error counts surfaced as `worker_errors`.

## What Phase 1 Does Not Claim
- No cryptographic security claim is made by benchmark throughput numbers.
- Mock provider runs are harness validation only and are not evidence of cryptographic correctness.
- Results are host/runtime specific and not portable as absolute constants.

## Interpreting Results
- `LINEAR`: Verify throughput scales close to concurrency increase while tails stay stable.
- `CONTENTION`: Throughput gains flatten and tail latencies rise as workers contend for shared resources.
- `QUEUEING`: In-flight pressure rises (`requests_in_flight_max`) and tail latencies widen sharply, signaling saturation.

## Concurrency Sweep Notes
- `c64` and `c128` are not first-knee discovery points; they are queueing-wall and tail-latency characterization runs after `c8/c16/c32`.
- `c12` and `c24` are refinement points for industrial operating-window sizing.
- `c12` refines the peak or near-peak region.
- `c24` refines the transition from contention toward stable queueing behavior.
