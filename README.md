# Local and private LLMs for bioinformatics: a three-environment benchmark

Can open-weights LLMs, running only on hardware we control, write correct bioinformatics scripts, solve
lab calculations and answer documentation questions? This repository holds the benchmark, its frozen data,
every raw result, and the infrastructure code to rerun it on a laptop, an Azure GPU VM and the RTU HPC.

Full write-up: [docs/REPORT.md](docs/REPORT.md). How the data were obtained and which versions ran:
[docs/EXPERIMENT_RECORD.md](docs/EXPERIMENT_RECORD.md).

## Results (29 October 2026, 53 items per run, one run each)

| Model | Machine | Scripting /7 | Reasoning /10 | Closed-book /18 | RAG /18 | Total /53 | tokens/s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Qwen3.5-122B-A10B | RTU HPC, 2x L40S | 7 | 10 | 15 | 18 | **50** | 55 |
| Qwen3.5-35B-A3B | Azure, 1x T4 | 6 | 10 | 16 | 18 | **50** | 43 |
| gpt-oss-20b | Azure, 1x T4 | 6 | 10 | 14 | 18 | 48 | 55 |
| Qwen3.5-9B | RTU HPC, 1x L40S | 6 | 9 | 13 | 18 | 46 | 82 |
| Qwen3.5-9B | Azure, 1x T4 | 5 | 10 | 13 | 18 | 46 | 29 |
| Qwen3.5-9B | Laptop, RTX 4060 8 GB | 5 | 9 | 13 | 16* | 43 | 41 |
| Gemma-4-E4B | Azure, 1x T4 | 5 | 8 | 10 | 17 | 40 | 58 |
| Gemma-4-E4B | Laptop, RTX 4060 8 GB | 3 | 9 | 7 | 18 | 37 | 68 |

\* Laptop runs used an older 4,096-token output limit that cut off four answers.

Main findings: scripting correctness improves with model size (only the 122B passed all scripts); RAG brings
every model to 17-18/18 on factual questions; MoE models give near-top accuracy on a 16 GB GPU; hardware
changes speed, not answers.

## Repository layout

```
bench/                 harness (run.py), tasks and scorers (tasks.py), data generator (make_data.py)
bench/data/            frozen inputs: NCBI records, tool manuals, synthetic VCF/FASTQ, truth.json
bench/results/         per-item JSON for every run, llama-bench output, rag_index.json, summary.csv
env/laptop/            model list + checksums, llama.cpp URLs + checksums, download script, guide
env/azure/terraform/   Terraform: resource group, VNet, IP-restricted NSG, T4 VM, auto-shutdown
env/azure/             setup and queue scripts, model list, guide
env/hpc/               setup script, PBS job (bench.pbs), submitter, libgomp fetcher, SSH config, guide
docs/                  report, experiment record, SHA-256 manifest
```

## Quick start

- **Laptop:** [env/laptop/README.md](env/laptop/README.md)
- **Azure:** [env/azure/README.md](env/azure/README.md) (`terraform apply`, copy harness, run queue, `terraform destroy`)
- **RTU HPC:** [env/hpc/README.md](env/hpc/README.md) (`setup_hpc.sh`, download, `submit.sh`)

Rescore or summarise existing results: `python bench/summarise.py bench/results/<run>.json`.

## Data and privacy

No patient or private data are used. Inputs are public NCBI records (phage lambda NC_001416.1, six human
RefSeq CDS, eight NCBI Gene records), public samtools/bcftools/seqkit manuals, and synthetic files generated
from them with a fixed seed. Model weights are not included; they are downloaded from Hugging Face and
verified against the checksums in `env/*/sums.txt`.
