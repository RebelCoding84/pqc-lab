# VM diagnostics for SLH-DSA / SPHINCS+-SHA2-128f-simple run

- Run ID: `single-vm-slhdsa-verify-20260601_025239`
- Topology: single-node VM local benchmark
- VM name: `pqc-fedora-vm-baseline`
- Hypervisor: KVM/libvirt
- CPU mode: host-passthrough
- VM resources: 8 vCPU, 16 GiB RAM
- Guest topology: 1 socket × 8 cores × 1 thread
- Explicit vCPU pinning: no
- LOADGEN VM used: no

## Interpretation

This run represents the default KVM/libvirt VM baseline. The guest receives host-passthrough CPU features, but the vCPUs are not explicitly pinned to dedicated host cores. Therefore, throughput and tail latency represent a scheduler-managed VM configuration rather than an optimized pinned-core VM configuration.

## Source files

- `environment/libvirt_dominfo.txt`
- `environment/libvirt_vcpuinfo.txt`
- `environment/libvirt_dumpxml.xml`
- `environment/lscpu.txt`
