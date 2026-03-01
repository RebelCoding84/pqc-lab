# PQC Capacity Benchmark – Executive Summary (Ryzen 9950X Baseline)

## 1. Context
These benchmarks evaluate post-quantum KEM handshake capacity in a reproducible engineering environment. Runs are executed in a containerized workflow (`pqc-lab:pqc`) with Pixi-managed dependencies to reduce configuration drift and preserve comparability across repeated measurements.

## 2. Test Environment
- CPU: AMD Ryzen 9 9950X
- OS: Fedora Linux
- Execution: Docker container (`pqc-lab:pqc`)
- Measurement: burst handshake workload
- Concurrency sweep and repeatability runs

## 3. Key Findings
- ML-KEM provides high throughput with minimal CPU saturation.
- Hybrid ML-KEM+Frodo significantly increases compute cost.
- Hybrid ML-KEM+HQC reaches CPU saturation at moderate concurrency.
- Tail latency (P99/P99.9) grows rapidly under hybrid workloads.
- Results are repeatable across runs.

## 4. Engineering Interpretation
The measurements indicate two operating regimes. In the lower-concurrency region, throughput increases nearly proportionally with worker count, which is consistent with a compute-limited but scalable path. At higher concurrency, hybrid profiles transition toward saturation: CPU utilization approaches limits, queueing delay rises, and tail latency expands faster than median latency. This marks a shift from mostly CPU-bound scaling behavior to a scheduler-contention regime where runnable work exceeds efficient core scheduling capacity.

## 5. Scope and Limitations
- Results are host-specific and should be interpreted as a baseline for this hardware/OS combination, not as universal constants.
- The harness isolates KEM handshake computation and does not include network transport, TLS record processing, or end-to-end service effects.
- The dataset is intended for comparative engineering analysis across algorithms and profiles within a controlled setup.

## 6. Practical Implications
- For authentication systems, prefer ML-KEM-only profiles where policy allows, especially for high-request-rate paths.
- For hybrid deployments, budget additional CPU headroom and set stricter concurrency controls.
- Use P99/P99.9 targets, not only average throughput, when defining peak-load capacity limits.
- Validate production sizing with the same profile mix and concurrency envelope expected in live traffic.
