# Fedora Bare Metal Capacity Report (2026-03-01)

Dataset path: `docs/capacity/2026-03-01_ryzen9950x_fedora_baremetal/results/`  
Host context: AMD Ryzen 9 9950X, Fedora 43 kernel line (`Linux-6.18.13-200.fc43.x86_64-x86_64-with-glibc2.39`), Docker image `pqc-lab:pqc`.

## Summary at Concurrency 32

| Profile | throughput_mean (hs/s) | p99_mean (ms) | p99_9_mean (ms) | max_latency_max (ms) | stdev (throughput) |
|---|---:|---:|---:|---:|---:|
| `real_mlkem` | 20448.416666666668 | 4.150886683325247 | 5.501954901066526 | 10.33470600009423 | 516.1626657362963 |
| `real_hybrid_mlkem_frodo` | 4196.2444444444445 | 11.691517133276651 | 13.924699933493015 | 20.965293999779533 | 126.29568626984228 |
| `real_hybrid_mlkem_hqc` | 501.7833333333333 | 81.40327370335096 | 108.92138185370894 | 144.11443900007725 | 6.060275937978775 |

## Summary at Concurrency 64

| Profile | throughput_mean (hs/s) | p99_mean (ms) | p99_9_mean (ms) | max_latency_max (ms) | stdev (throughput) |
|---|---:|---:|---:|---:|---:|
| `real_mlkem` | 19409.744444444445 | 8.997011599979787 | 12.077744644004525 | 21.1617820000356 | 89.84904985173306 |
| `real_hybrid_mlkem_frodo` | 3862.677777777778 | 30.684607970006617 | 37.398128568986024 | 51.16468799997165 | 19.808684496489807 |
| `real_hybrid_mlkem_hqc` | 501.7444444444444 | 219.18432305997564 | 261.66285839007605 | 355.78545100008796 | 0.07698003589194573 |

## HQC Stress Point (Concurrency 128, Repeats 2)

| Profile | throughput_mean (hs/s) | p99_mean (ms) | p99_9_mean (ms) | max_latency_max (ms) |
|---|---:|---:|---:|---:|
| `real_hybrid_mlkem_hqc` | 504.58333333333337 | 555.5977815599906 | 734.4681208679735 | 1062.1774199998981 |

## Methodology

Method details (workload model, warmup/measurement protocol, repeat controls, limitations):  
`docs/capacity_methodology.md`

This campaign used burst handshakes with `duration=60s`, `warmup=10s`, percentiles `50,95,99,99.9`, and `repeats=3` at C32/C64 (plus one HQC stress run at C128 with `repeats=2`).

## Reproduce (Host-Specific)

These results are host-specific; use reproduction primarily for trend comparison on the same hardware/OS/runtime class.

```bash
# Run C=32 and C=64 for all three profiles (repeats=3)
for profile in real_mlkem real_hybrid_mlkem_frodo real_hybrid_mlkem_hqc; do
  for c in 32 64; do
    docker run --rm -v "$PWD":/work -w /work pqc-lab:pqc \
      python -m src.capacity.harness \
      --profile "profiles/${profile}.yaml" \
      --concurrency "$c" \
      --duration 60 \
      --warmup 10 \
      --repeats 3 \
      --percentiles "50,95,99,99.9" \
      --cpu-sample-interval 1.0 \
      --out "docs/capacity/2026-03-01_ryzen9950x_fedora_baremetal/results/repro_${profile}_c${c}_reps3.json"
  done
done

# Run HQC stress point (C=128, reps=2)
docker run --rm -v "$PWD":/work -w /work pqc-lab:pqc \
  python -m src.capacity.harness \
  --profile profiles/real_hybrid_mlkem_hqc.yaml \
  --concurrency 128 \
  --duration 60 \
  --warmup 10 \
  --repeats 2 \
  --percentiles "50,95,99,99.9" \
  --cpu-sample-interval 1.0 \
  --out docs/capacity/2026-03-01_ryzen9950x_fedora_baremetal/results/repro_real_hybrid_mlkem_hqc_c128_reps2_stress.json
```

## Helper: jq Extraction

```bash
jq -r '
  . as $r
  | [
      input_filename,
      $r.concurrency,
      ($r.repeats | length),
      $r.summary.throughput_mean,
      $r.summary.p99_mean,
      $r.summary.p99_9_mean,
      $r.summary.max_latency_max,
      $r.summary.throughput_stdev
    ] | @tsv
' docs/capacity/2026-03-01_ryzen9950x_fedora_baremetal/results/*.json
```
