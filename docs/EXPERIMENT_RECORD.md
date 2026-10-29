# Experiment record

What was done, when, with which versions, and the exact commands used to obtain the data. Results files in
`bench/results/` are the primary record; this file explains how they came to be.

## Timeline

| Date (2026) | Step |
| --- | --- |
| 15 Oct | Laptop set up: llama.cpp b11639 (CUDA 12.8 build), Python venv. Benchmark designed (`tasks.py`), data downloaded and frozen, synthetic files and answer keys generated (`make_data.py`), RAG index built with EmbeddingGemma-300M (`run.py embed`). |
| 15 Oct | Laptop runs (made with the `run.py` of that day: same prompts and scorers, before the 29 Oct portability changes, which only added path, port and multi-GPU options): `laptop-qwen3.5-9b` and `laptop-gemma4-e4b` (originally named without the `laptop-` prefix; renamed for clarity) (53 items each; retrieval output limit 4,096 tokens at the time). A `gemma4-12b` run was stopped after 2 items (13 tokens/s, CPU offload) and is excluded. |
| 15 Oct | Retrieval output limit raised to 8,192 tokens in `run.py` for all later runs. |
| 29 Oct | Azure: resource group `rg-llm-bench-neu` (North Europe). NC16as/NC8as T4 sizes failed with AllocationFailed in all zones; NC4as_T4_v3 created. Runs `t4-qwen3.5-9b`, `t4-gemma4-e4b`, `t4-gpt-oss-20b`, `t4-qwen3.5-35b-a3b`, then `llama-bench` for each. |
| 29 Oct | RTU HPC: harness ported (`LLAMA_BIN`, `LLM_PORT`, multi-GPU VRAM accounting), container approach set up. First jobs on wn74 hung (Singularity); switched to Apptainer sandbox on `/scratch`, fixed `APPTAINERENV_LD_LIBRARY_PATH`. Runs `hpc-qwen3.5-9b` (wn73, 1x L40S) and `hpc-qwen3.5-122b-a10b` (wn75, 2x L40S), each followed by `llama-bench`. |
| 29 Oct | Results collected, `summary.csv` generated, report written. Azure resource group deleted after the run. |
| 29 Oct | Independent cold review of the repository re-derived every answer key from the raw files. It found the `samtools sort` read-name key accepted only `-n`, although the manual also documents `-N`. Key corrected in `tasks.py`; all stored answers rescored with `bench/rescore.py` (no answers regenerated). One item changed: `t4-gemma4-e4b` `rag:sam_byname`, total 40 to 41; its earlier score is kept as `ok_before_rescore`. All other items, including every script output, rescored identically. |

## Exact data download commands (15 Oct 2026)

```bash
D=bench/data; mkdir -p $D/raw $D/docs; cd $D/raw
E=https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi
curl -s "$E?db=nuccore&id=NC_001416.1&rettype=fasta&retmode=text" -o lambda.fa
curl -s "https://www.ncbi.nlm.nih.gov/sviewer/viewer.cgi?db=nuccore&report=gff3&id=NC_001416.1" -o lambda.gff3
curl -s "$E?db=nuccore&id=NM_000546.6,NM_007294.4,NM_000492.4,NM_000518.5,NM_000207.3,NM_004333.6&rettype=fasta_cds_na&retmode=text" -o cds.fa
curl -s "$E?db=gene&id=7157,672,1080,3043,3630,673,1956,7124&rettype=docsum&retmode=json" -o gene_summaries.json
cd ../docs
for p in samtools bcftools; do curl -s "https://www.htslib.org/doc/$p.html" -o $p.html; done
for p in view sort markdup depth faidx; do curl -s "https://www.htslib.org/doc/samtools-$p.html" -o samtools-$p.html; done
curl -sL "https://bioinf.shenwei.me/seqkit/usage/" -o seqkit.html
python3 ../../docs2txt.py .          # HTML -> .txt
```

`genes.txt` was written from `gene_summaries.json`, one paragraph per gene:
`Gene {name} ({description}), NCBI Gene ID {id}. Chromosome {chromosome}, cytogenetic location {maplocation}. Aliases: {otheraliases}. Summary: {summary}`.

`calls.vcf`, `reads.fastq` and `truth.json` come from `python bench/make_data.py` (seed 42). Online sources
change over time; the committed files and `MANIFEST.sha256` are the frozen versions used.

## Software versions

| Component | Version / source | Verification |
| --- | --- | --- |
| llama.cpp | b11639, commit a0e6dc738, `llama-b11639-bin-ubuntu-cuda-12.8-x64.tar.gz` + cudart tarball from GitHub releases | SHA-256 in `env/laptop/llama_sums.txt` |
| Model files | Hugging Face repos listed in `env/*/list.txt` | SHA-256 in `env/*/sums.txt` (Hugging Face LFS hashes) |
| Embedding model (RAG index only) | `ggml-org/embeddinggemma-300M-GGUF`, `embeddinggemma-300M-Q8_0.gguf` | SHA-256 `b5ce9d77a3fc4b3b39ccb5643c36777911cc4eb46a66962eadfa3f5f60490d63` |
| HPC container | `docker://python:3.12-slim-trixie` (Debian 13, glibc 2.41, Python 3.12.16) | Official Docker Hub image |
| HPC libgomp | Debian trixie `libgomp1_14.2.0-19_amd64.deb` | SHA-256 from the Debian Packages index (`env/hpc/getgomp.py`) |
| Apptainer / Singularity (HPC) | Apptainer 1.1.6 (jobs), Singularity 3.4.1 (login-node setup) | Cluster modules |
| Azure image | `microsoft-dsvm:ubuntu-hpc:2404:latest` (NVIDIA driver 580.178) | Marketplace |
| HPC driver | NVIDIA 550.54.15 | `pbsnodes` |
| Python libraries | Not pinned at install time. Recorded afterwards: laptop Python 3.14.4, numpy 2.5.4, pandas 3.0.6, biopython 1.88; HPC Python 3.12.16, numpy 2.5.4, pandas 3.1.0, biopython 1.88; Azure (VM since deleted) installed the same day from PyPI | |

## Run settings (all runs)

`llama-server -c 16384 -fa on --fit on --reasoning-budget 6144`; requests with temperature 0.6, top-p 0.95,
seed 1, max 8,192 output tokens (4,096 for retrieval in the two laptop runs). `llama-bench -p 512 -n 128 -r 3
-fa on -fitt 512`.

## Result file format

`bench/results/<run>.json`: `items` maps `section:task` to a record with `content` (final answer),
`reasoning` (thinking text), `finish` (`stop` or `length`), `wall` (seconds), `gen_tokens`, `tg_tps`,
`pp_tps`, `ok` (scored), and for scripts `code`, `stdout`, `stderr`, `rc`. Run-level fields: `vram_peak_mib`,
`vram_base_mib`, `offload_lines` (llama.cpp placement log). `<run>.bench.json` is raw `llama-bench` JSON.
`<run>.progress` is the console log of the run.

## Integrity

`docs/MANIFEST.sha256` lists SHA-256 for every committed data, code and result file.
Check with `sha256sum -c docs/MANIFEST.sha256` from the repository root.
