# Executive Summary: Fedora Bare Metal Capacity Campaign (Ryzen 9 9950X)

## What was measured
This campaign measured post-quantum key-exchange handshake capacity using `src.capacity.harness` in burst workload mode on Fedora bare metal (containerized runtime: `pqc-lab:pqc`). Primary campaign points used `repeats=3`, `duration=60s`, `warmup=10s`, and latency percentiles including `p99.9` (`50,95,99,99.9`). Profiles measured:
- `real_mlkem`
- `real_hybrid_mlkem_frodo`
- `real_hybrid_mlkem_hqc`

An additional stress point was executed for HQC hybrid at `concurrency=128` with `repeats=2`.

## Key findings
- ML-KEM knee region appears between concurrency `32` and `64`: throughput does not increase and tail latency rises sharply (`p99` and `p99.9` both increase materially).
- Hybrid ML-KEM + Frodo shows higher latency than ML-KEM at both `C=32` and `C=64`, with throughput flattening/declining at `C=64`.
- Hybrid ML-KEM + HQC shows clear saturation at `C=32/C=64`, and queue-collapse behavior at stress `C=128`: throughput remains effectively flat while `p99`, `p99.9`, and `max` latency expand dramatically.

## What we can claim
- On this host and runtime, ML-KEM sustains the highest throughput and lowest tail latency among tested profiles.
- On this host and runtime, both hybrid profiles have significantly higher tail latency than ML-KEM at equivalent concurrency.
- HQC hybrid demonstrates a saturation boundary where additional concurrency does not raise throughput but substantially worsens tail behavior.
- Trend-level conclusions are repeatable within this campaign design (`repeats=3` for main points).

## What we cannot claim
- These numbers are not universal constants for all hardware, kernels, container runtimes, or cloud instances.
- Results do not represent end-to-end application or network behavior; they cover harnessed handshake capacity only.
- This campaign is not a cryptographic security proof and does not replace protocol/security validation.
