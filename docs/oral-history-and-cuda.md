# Jensen Huang oral history and CUDA archive

The [interview index](../data/archive_index.csv) describes what to look for in original recordings. It uses publisher-provided chapter times where available. The [technical milestone series](../data/technology_milestones.csv) links to dated publications and announcements. These sources answer different questions about how the company developed.

## Three reading routes

1. **Founding and setbacks.** Start with the Computer History Museum’s oral history, recorded August 9, 2024. Compare Huang’s later account with his description of NVIDIA’s first months in a 2009 Stanford eCorner talk and the RIVA 128 chapter of Acquired’s 2023 interview. [Museum recording and catalog](../sources/evidence.md#clm-036) · [Stanford and Acquired](../sources/evidence.md#clm-037)
2. **Software and workloads.** Read the 2008 CUDA authors’ paper and the 2012 AlexNet paper. Then compare NVIDIA’s twentieth-anniversary retrospective and the GTC keynote section beginning at 00:06:02. The papers establish the model and experimental method. The anniversary materials provide the issuer’s interpretation. [CUDA and AlexNet sources](../sources/evidence.md#clm-015) · [NVIDIA anniversary sources](../sources/evidence.md#clm-039)
3. **Systems and organizational choices.** Use Acquired’s networking chapter at 00:39:31 alongside the dated Mellanox completion notice, then follow the DGX-1, Hopper and Blackwell announcements. The 2026 earnings release records initial Vera Rubin shipments at a different stage from product introductions. [Mellanox and Arm evidence](../sources/evidence.md#clm-016) · [System announcements](../sources/evidence.md#clm-038) · [Reported initial shipments](../sources/evidence.md#clm-039)

The repository publishes original descriptions, source hyperlinks and officially provided locators. Video, caption and transcript files remain with their publishers.

## Worked MLPerf comparison

The [comparison dataset](../data/benchmark_comparison.csv) contains four Dell results for two systems in MLPerf Inference v6.1. Each pair matches the division, availability class, Llama 2 70B 99.9 workload and accelerator count.

| System | Offline throughput | Server throughput |
|---|---:|---:|
| Dell XE9785L · 8 × NVIDIA B300-SXM-270GB | 113,101 tokens/s | 106,898 tokens/s |
| Dell XE9785L · 8 × AMD Instinct MI355X | 103,792 tokens/s | 103,932 tokens/s |
| Difference relative to the MI355X system | 8.97% | 2.85% |

Offline submits the samples as a single query. Server generates requests over time and evaluates throughput subject to workload-specific latency requirements. The observed gap depends on which scenario is compared. The source records different software stacks. Accelerator speed, purchase cost, and energy consumption each require separate evidence. [Pinned results and MLPerf rules](../sources/evidence.md#clm-040)

Download the upstream pinned `summary.csv` using the link in the evidence record and run the independent audit. It checks the file checksum, exact result locator, platform, workload and reported throughput. Published benchmark results retain the terms governing MLPerf material. [MLCommons Results Messaging Guidelines](https://github.com/mlcommons/policies/blob/master/MLPerf_Results_Messaging_Guidelines.adoc)

```sh
python3 scripts/verify_upstream.py --mlperf /path/to/summary.csv
```
