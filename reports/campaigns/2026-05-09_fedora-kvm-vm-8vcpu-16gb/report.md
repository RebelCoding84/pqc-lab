# Fedora KVM VM PQC Capacity Baseline — Ryzen 9 9950X

## Report status

Local draft.

This report was generated from local VM benchmark outputs and has not yet been reviewed for publication.

## Purpose

This report documents the first Fedora KVM VM baseline campaign for PQC key-exchange and hybrid key-exchange capacity testing.

The goal is not simply to prove whether a VM is slower than bare metal. The goal is to measure how virtualization, vCPU scheduling, and container execution affect:

- throughput
- P99 latency
- P99.9 latency
- maximum observed latency
- failure count
- practical knee point
- comparison against prior bare metal Ryzen 9 9950X results

## Tested profiles

The first VM campaign includes:

1. ML-KEM-768
2. Hybrid ML-KEM + FrodoKEM-976-SHAKE
3. Hybrid ML-KEM + HQC-256

Classic McEliece, ML-DSA, and SLH-DSA are intentionally excluded from this first VM campaign.

## Source data

VM campaign data:

```text
reports/campaigns/2026-05-09_fedora-kvm-vm-8vcpu-16gb/
```

Summary tables:

```text
reports/campaigns/2026-05-09_fedora-kvm-vm-8vcpu-16gb/summaries/vm_summary.tsv
reports/campaigns/2026-05-09_fedora-kvm-vm-8vcpu-16gb/summaries/baremetal_summary.tsv
reports/campaigns/2026-05-09_fedora-kvm-vm-8vcpu-16gb/summaries/vm_vs_baremetal_comparison.tsv
reports/campaigns/2026-05-09_fedora-kvm-vm-8vcpu-16gb/summaries/knee_summary.tsv
```

## Notes

The benchmark harness currently reports `environment.type` as `bare_metal_container` inside JSON output.

For this campaign, the actual execution environment is:

```text
Fedora KVM VM container
```

This distinction is documented in this report.

## Test environment

### Host system

| Field | Value |
|---|---|
| Host OS | Fedora 43 Workstation |
| Host CPU | AMD Ryzen 9 9950X |
| Host RAM | 64 GB DDR5 |
| Hypervisor | KVM / libvirt / QEMU |
| VM manager | virt-manager |
| Host tuning profile | latency-performance |
| Host network path | libvirt NAT via virbr0 |

### Virtual machine

| Field | Value |
|---|---|
| VM name | pqc-fedora-vm-baseline |
| Guest OS | Fedora Linux 43 Server Edition |
| Guest kernel | 6.19.14-200.fc43.x86_64 |
| vCPU allocation | 8 |
| CPU mode | host-passthrough |
| CPU topology | 1 socket × 8 cores × 1 thread |
| Guest RAM | 16 GB |
| Guest disk | 78 GB root filesystem |
| Filesystem | XFS on LVM |
| Disk bus | VirtIO |
| Network | libvirt NAT |
| VM IP during campaign | 192.168.122.194 |
| SELinux | enforcing |
| Root login | disabled |
| User | rebel, administrative privileges enabled |

### Container runtime

| Field | Value |
|---|---|
| Runtime | Podman with Docker-compatible CLI |
| Podman version | 5.8.2 |
| Docker compatibility package | podman-docker |
| Container image | localhost/pqc-lab:pqc |
| Container base OS | Ubuntu 24.04.4 LTS |
| Python inside container | 3.11.14 |
| PQC provider | liboqs |
| Reported git commit in benchmark JSON | 6e9718f |

### Benchmark method

| Field | Value |
|---|---|
| Workload model | burst handshake model |
| Warmup | 10 seconds |
| Measurement duration | 60 seconds |
| Repeats | 3 per concurrency, except ML-KEM c128 with 2 repeats |
| Percentiles | p50, p95, p99, p99.9 |
| CPU sample interval | 1.0 second |
| Output format | JSON per profile/concurrency |
| Summary formats | TSV and CSV |



## Results

### VM summary

This table summarizes the measured VM-side throughput and latency behavior for all tested profiles.

| profile | concurrency | runs_or_repeats | throughput_hs_per_sec | p99_ms | p99_9_ms | max_ms | failures |
| --- | --- | --- | --- | --- | --- | --- | --- |
| hybrid_frodo | 1 | 3 | 252.85 | 4.003505 | 4.368667 | 5.363045 | 0 |
| hybrid_frodo | 8 | 3 | 1800.422222 | 4.790273 | 5.195357 | 13.342693 | 0 |
| hybrid_frodo | 32 | 3 | 1280.655556 | 57.300876 | 72.809304 | 106.917732 | 0 |
| hybrid_frodo | 64 | 3 | 1373.755556 | 120.809104 | 155.194467 | 224.021963 | 0 |
| hybrid_hqc | 1 | 3 | 34.55 | 29.306331 | 29.843378 | 30.958258 | 0 |
| hybrid_hqc | 8 | 3 | 257.761111 | 31.352268 | 35.021408 | 47.966705 | 0 |
| hybrid_hqc | 32 | 3 | 257.066667 | 194.586705 | 232.1276 | 317.979792 | 0 |
| hybrid_hqc | 64 | 3 | 257.044444 | 443.4154 | 538.194143 | 699.960969 | 0 |
| mlkem | 1 | 3 | 24488.4 | 0.056417 | 0.063074 | 0.566245 | 0 |
| mlkem | 8 | 3 | 13308.088889 | 1.430671 | 1.92138 | 3.912923 | 0 |
| mlkem | 32 | 3 | 11971.394444 | 8.676724 | 11.992793 | 24.667666 | 0 |
| mlkem | 64 | 3 | 11830.016667 | 17.691419 | 24.257066 | 45.453393 | 0 |
| mlkem | 128 | 2 | 11832.15 | 35.44538 | 48.706059 | 101.814896 | 0 |


### VM vs bare metal comparison

This table compares the Fedora KVM VM results against prior Ryzen 9 9950X bare metal results where matching concurrency points exist.

| profile | concurrency | baremetal_throughput | vm_throughput | vm_throughput_penalty_pct | baremetal_p99_ms | vm_p99_ms | p99_amplification_x |
| --- | --- | --- | --- | --- | --- | --- | --- |
| hybrid_frodo | 1 | 264.566667 | 252.85 | 4.428625 | 3.810851 | 4.003505 | 1.050554 |
| hybrid_frodo | 8 | 1908.066667 | 1800.422222 | 5.641545 | 5.034122 | 4.790273 | 0.951561 |
| hybrid_frodo | 32 | 4219.733333 | 1280.655556 | 69.650794 | 11.203837 | 57.300876 | 5.114397 |
| hybrid_hqc | 1 | 34.977778 | 34.55 | 1.222999 | 29.345941 | 29.306331 | 0.99865 |
| hybrid_hqc | 8 | 260.294444 | 257.761111 | 0.973257 | 31.132396 | 31.352268 | 1.007062 |
| hybrid_hqc | 32 | 502.433333 | 257.066667 | 48.835666 | 71.584167 | 194.586705 | 2.718293 |
| mlkem | 1 | 28450.244444 | 24488.4 | 13.92552 | 0.03152 | 0.056417 | 1.789879 |
| mlkem | 8 | 39352.872222 | 13308.088889 | 66.182675 | 0.433633 | 1.430671 | 3.299265 |
| mlkem | 32 | 20551.188889 | 11971.394444 | 41.748409 | 4.11187 | 8.676724 | 2.110165 |
| mlkem | 128 | 19625.744444 | 11832.15 | 39.711077 | 17.951108 | 35.44538 | 1.974551 |


### Knee point summary

This table summarizes the practical throughput peak and heuristic tail-latency knee point.

| environment | profile | peak_throughput_c_all | peak_throughput_c_ge8 | tail_knee_all | tail_knee_ge8 |
| --- | --- | --- | --- | --- | --- |
| fedora_baremetal_ryzen9950x | hybrid_frodo | c32 | c32 |  |  |
| fedora_baremetal_ryzen9950x | hybrid_hqc | c32 | c32 |  |  |
| fedora_baremetal_ryzen9950x | mlkem | c8 | c8 |  |  |
| fedora_kvm_vm_8vcpu_16gb | hybrid_frodo | c8 | c8 | c8→c32 | c8→c32 |
| fedora_kvm_vm_8vcpu_16gb | hybrid_hqc | c8 | c8 | c8→c32 | c8→c32 |
| fedora_kvm_vm_8vcpu_16gb | mlkem | c1 | c8 | c1→c8 | c8→c32 |


Note: bare metal P99.9 values were not available in the current imported bare metal summary data. Therefore, P99.9 amplification is intentionally not used as a primary comparison metric in this draft.

## Findings and interpretation

### 1. The VM baseline completed successfully

All VM-side benchmark runs completed with zero recorded failures.

The VM campaign produced usable data for:

- ML-KEM-768
- Hybrid ML-KEM + FrodoKEM-976-SHAKE
- Hybrid ML-KEM + HQC-256

This confirms that the Fedora KVM VM, Podman container runtime, liboqs provider, and benchmark harness were functional for the first VM capacity campaign.

### 2. ML-KEM remains high-throughput, but VM scaling is limited

ML-KEM reached high absolute throughput in the VM, but scaling behavior was limited under higher concurrency.

Key VM observations:

- c1: approximately 24,488 handshakes/s
- c8: approximately 13,308 handshakes/s
- c32-c128: approximately 11,800-12,000 handshakes/s

The practical observation is that additional concurrency beyond c8 did not increase throughput. Instead, it primarily increased tail latency.

VM-side ML-KEM P99.9 latency increased from approximately 1.92 ms at c8 to approximately 11.99 ms at c32, 24.26 ms at c64, and 48.71 ms at c128.

### 3. Hybrid Frodo shows a clear VM knee point shift

Hybrid ML-KEM + Frodo behaved well at c1 and c8 in the VM, but changed behavior sharply at c32.

Key VM observations:

- c1: approximately 253 handshakes/s
- c8: approximately 1,800 handshakes/s
- c32: approximately 1,281 handshakes/s
- c64: approximately 1,374 handshakes/s

The VM throughput peak occurred at c8, while the imported bare metal data peaked at c32.

This suggests a practical knee point shift for the Frodo hybrid profile:

| Metric | Observation |
|---|---|
| Bare metal peak | c32 |
| VM peak | c8 |
| VM tail knee | c8 to c32 |

At c32, the VM showed a throughput penalty of approximately 69.7% compared with bare metal, while P99 latency increased by approximately 5.1x.

### 4. Hybrid HQC reaches its VM capacity ceiling early

Hybrid ML-KEM + HQC was the heaviest profile in this campaign.

Key VM observations:

- c1: approximately 34.55 handshakes/s
- c8: approximately 257.76 handshakes/s
- c32: approximately 257.07 handshakes/s
- c64: approximately 257.04 handshakes/s

The VM reached its practical throughput ceiling at c8. Additional concurrency at c32 and c64 did not increase throughput, but strongly increased tail latency.

VM-side HQC P99.9 latency increased from approximately 35.02 ms at c8 to approximately 232.13 ms at c32 and 538.19 ms at c64.

This is a clear queueing and saturation pattern.

### 5. Virtualization impact is profile-dependent

The most important conclusion is that virtualization does not affect all PQC profiles equally.

| Profile | VM behavior |
|---|---|
| ML-KEM | High absolute throughput, but large VM penalty at c8 and rising tail latency under concurrency |
| Hybrid Frodo | Near bare metal behavior at c1/c8, but sharp degradation at c32 |
| Hybrid HQC | Near bare metal behavior at c1/c8, but scaling stops at c8 and tail latency grows heavily after that |

This means PQC migration planning should not only compare algorithms cryptographically. It should also measure how each algorithm profile behaves under real deployment conditions such as virtualization, vCPU scheduling, container runtime, and burst concurrency.

### 6. Practical capacity planning conclusion

For this 8 vCPU Fedora KVM VM:

| Profile | Practical VM operating region | Risk region |
|---|---|---|
| ML-KEM | c8-c32 depending on latency target | c64/c128 tail-latency growth |
| Hybrid Frodo | c8 | c32 and above |
| Hybrid HQC | c8 | c32 and above |

The key operational point is:

> Additional concurrency beyond the practical knee point does not necessarily increase capacity. It may mainly increase P99/P99.9 latency and timeout risk.

### 7. Reporting limitation

The current imported bare metal summary data does not include P99.9 values. Therefore, this draft uses:

- throughput penalty %
- P99 amplification
- maximum latency comparison
- practical knee point shift

P99.9 amplification should be calculated only after matching bare metal runs are available with the same percentile settings.

### 8. Draft conclusion

This first VM campaign provides evidence that heavier hybrid PQC profiles can shift the practical capacity knee point earlier in virtualized environments.

In this dataset, Hybrid Frodo and Hybrid HQC both peaked at c32 on bare metal but reached their practical VM throughput peak at c8. Beyond that point, additional concurrency primarily increased tail latency rather than throughput.

This finding is relevant for:

- API gateway sizing
- authentication service capacity planning
- TLS/PQC handshake burst planning
- timeout and SLO/SLA risk assessment
- virtualized and hybrid infrastructure design
- PQC migration planning for critical services

