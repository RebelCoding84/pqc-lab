# PQC Deployment Landscape Analysis
## PQC Lab Capacity Benchmark Interpretation

This document interprets the benchmark results produced in the PQC Lab capacity campaigns.  
The goal is not to compare absolute performance numbers, but to understand infrastructure behavior under different post-quantum cryptographic families.

Benchmarks were executed on dedicated local hardware using a containerized execution model.

---

## 1. Knee Point Analysis

The knee point represents the concurrency level where throughput growth stops scaling linearly and latency begins increasing disproportionately.

Observations:

- ML-KEM shows near-linear scaling until medium concurrency.
- Hybrid schemes introduce earlier saturation due to additional computation.
- Classic McEliece reaches throughput stability earlier but maintains predictable scaling.

Interpretation:

The knee point indicates the safe operational concurrency range for production deployment before tail latency risk increases.

---

## 2. Latency Wall

Latency wall refers to the region where tail latency (p99/p99.9) increases rapidly while throughput remains mostly constant.

Observed behavior:

- ML-KEM latency increases gradually.
- HQC introduces visible tail expansion under high concurrency.
- McEliece exhibits sharp latency growth despite stable throughput.

Interpretation:

This suggests serialization and memory pressure rather than raw CPU exhaustion.

---

## 3. CPU Saturation Characteristics

CPU utilization analysis shows:

- ML-KEM primarily CPU-bound.
- Hybrid modes increase sustained CPU load.
- McEliece reaches high process CPU usage while system CPU remains stable.

Interpretation:

McEliece workload shifts bottlenecks away from arithmetic operations toward data handling overhead.

---

## 4. Memory and Network Dominance

Classic McEliece introduces significantly larger key material.

Observed effects:

- Increased cache pressure
- Higher latency variance
- Reduced scaling efficiency under concurrency

Interpretation:

Infrastructure planning must consider memory bandwidth and serialization overhead, not only CPU performance.

---

## 5. Deployment Implications

The combined dataset demonstrates a realistic PQC deployment spectrum:

| Role | Algorithm |
|------|-----------|
| Default PQC | ML-KEM |
| Conservative fallback | FrodoKEM |
| Hybrid transition | HQC |
| Extreme fallback | Classic McEliece |

Organizations may not deploy McEliece as default, but must understand infrastructure impact if regulatory fallback capability is required.

---

## 6. Key Engineering Insight

PQC migration is not only a cryptographic problem but an infrastructure scaling problem.

Performance bottlenecks shift depending on algorithm family:

- CPU-bound → lattice schemes
- Memory/serialization-bound → code-based schemes

---

## 7. Conclusion

The PQC Lab benchmark demonstrates that post-quantum readiness requires capacity modeling across multiple cryptographic families.

Trend comparison is more meaningful than absolute performance values.

The dataset provides an engineering baseline for evaluating PQC deployment risk.