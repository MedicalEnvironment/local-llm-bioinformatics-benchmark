# Local and private LLMs for bioinformatics: a three-environment benchmark

> **In short.** We gave five open-source AI models the same 53 bioinformatics tasks (write a script, do a lab calculation, recall a tool option or gene location) on a laptop, an Azure GPU and the RTU HPC, and checked every answer automatically against keys fixed in advance. The largest model (Qwen3.5-122B, HPC) got every script right and scored 50/53; a mid-size model on one cloud GPU also scored 50/53. Smaller models often wrote scripts that ran but printed wrong numbers. Giving any model the relevant documentation fixed nearly all factual errors. No data left our own machines.

Can open-source AI language models (LLMs), running only on hardware we control, write correct
bioinformatics scripts, solve lab calculations and answer questions about tools and genes, without
sending any data to an outside service? This repository holds the test, its frozen input data, every raw
result, and the code to rerun it on a laptop, an Azure cloud GPU and the RTU HPC cluster.

**Who this is for.** The results, scoring and report need no programming background. Rerunning the
benchmark needs basic Linux shell use; the Azure and HPC guides also assume SSH, and Terraform or PBS
respectively.

| If you want to... | Read |
| --- | --- |
| Know what we found | [Results](#results) below, then [docs/REPORT.md](docs/REPORT.md) |
| Know how answers were judged right or wrong | [How correctness was decided](#how-correctness-was-decided) |
| See every question and its correct answer | [docs/QUESTIONS.md](docs/QUESTIONS.md) |
| See which model got which question right | [docs/RESULTS_BY_ITEM.md](docs/RESULTS_BY_ITEM.md) |
| See real model answers: correct, silently wrong, crashed | [docs/EXAMPLES.md](docs/EXAMPLES.md) |
| Know where the data came from and which versions ran | [docs/EXPERIMENT_RECORD.md](docs/EXPERIMENT_RECORD.md) |
| Rerun it | [Rerunning](#rerunning) |

## What was tested

Five models, from small (4 GB file) to very large (77 GB), each answered the same **53 items**:

- **Scripting (7):** write a Python script for a common task (GC content, translation, longest ORF, GFF
  summary, VCF filtering, FASTQ quality, k-mer counting). The script is actually run.
- **Calculations (10):** short lab and genetics problems (dilutions, Hardy–Weinberg, qPCR fold change, ...).
- **Facts (18, asked twice):** command-line options of samtools, bcftools and seqkit, and cytogenetic
  locations of human genes. Asked once from memory ("closed-book") and once with the relevant manual or
  NCBI excerpt pasted into the question ("RAG").

They ran on three machines: a laptop (RTX 4060, 8 GB GPU memory), an Azure VM (Tesla T4, 16 GB) and RTU
HPC nodes (one or two NVIDIA L40S, 48 GB each). All inputs are public NCBI records, public tool manuals, or
synthetic files generated from them; no patient or private data were used.

## Results

29 October 2026; 53 items per run; each item asked once.

| Model | Machine | Scripting /7 | Calculations /10 | Facts from memory /18 | Facts with docs (RAG) /18 | Total /53 | Speed (tokens/s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Qwen3.5-122B-A10B | RTU HPC, 2x L40S | 7 | 10 | 15 | 18 | **50** | 55 |
| Qwen3.5-35B-A3B | Azure, 1x T4 | 6 | 10 | 16 | 18 | **50** | 43 |
| gpt-oss-20b | Azure, 1x T4 | 6 | 10 | 14 | 18 | 48 | 55 |
| Qwen3.5-9B | RTU HPC, 1x L40S | 6 | 9 | 13 | 18 | 46 | 82 |
| Qwen3.5-9B | Azure, 1x T4 | 5 | 10 | 13 | 18 | 46 | 29 |
| Qwen3.5-9B | Laptop | 5 | 9 | 13 | 16* | 43 | 41 |
| Gemma-4-E4B | Azure, 1x T4 | 5 | 8 | 10 | 17 | 40 | 58 |
| Gemma-4-E4B | Laptop | 3 | 9 | 7 | 18 | 37 | 68 |

\* The laptop runs used an older 4,096-token answer limit, which cut off four answers before they finished.

What this means:

- **Only the largest model wrote every script correctly.** Most failed scripts did not crash; they ran and
  printed a plausible but wrong number. Generated code must be tested on data with a known answer.
- **Giving the model the documentation (RAG) fixes most factual errors**: every model scored 17–18/18.
- **Hardware changes speed, not quality**: the same 9B model scored 43–46 on all three machines.
- **A 35B "mixture-of-experts" model on one 16 GB GPU matched the 122B model's total score.**

## How correctness was decided

No model and no person judged answers during the runs. Every correct answer was fixed **before** any model
ran, from primary sources or our own reference code, and a program compared each answer with it.

| Section | What the model had to produce | How it was checked | Where the correct answer came from |
| --- | --- | --- | --- |
| Scripting | A Python script in a code block | The script is run on the real input file (isolated Python, 2-minute limit). It must exit without error and print exactly the right result: counts, coordinates and lengths must match exactly; decimals within rounding (e.g. GC% ±0.011). | Computed by `bench/make_data.py` with Biopython, independently of any model (`bench/data/truth.json`) |
| Calculations | A final line `ANSWER: <number>` | The number must be within 1% of the key | Worked by hand; fixed in `bench/tasks.py` |
| Facts: gene locations | A final line `ANSWER: <band>` | Must contain the exact NCBI band, e.g. `11p15.4` | NCBI Gene `maplocation` field (`bench/data/raw/gene_summaries.json`) |
| Facts: tool options | A final line `ANSWER: <option>` | Must contain the option; short or long form accepted (`-s` or `--by-seq`) | The official manuals in `bench/data/docs/` |

The scorer is deliberately strict: only the final `ANSWER:` line counts, so a correct explanation with a
wrong final line fails. After the runs, every failure was inspected by hand. One correct answer failed only
on formatting (`Answer:` instead of `ANSWER:`, gpt-oss-20b), and the TNF location answer 6p21.3 was scored
wrong because the question asked for the more specific sub-band (6p21.33). Both are noted in the report, so
scores are, if anything, slight underestimates. With one run per item, differences of 1–2 points between
models can be chance.

The exact scoring code is `score_script`, `score_reason` and `score_retr` in [bench/tasks.py](bench/tasks.py).

## Glossary

| Term | Meaning |
| --- | --- |
| LLM | Large language model: the AI model that reads a prompt and writes an answer. |
| Open-weights model | A model whose files can be downloaded and run on your own hardware, so prompts and data never leave it. |
| Parameters (e.g. 9B, 122B) | The model's learned numbers, in billions. More parameters usually means more knowledge and more memory needed. |
| Mixture-of-experts (MoE), e.g. 35B-A3B | A model that contains many sub-networks but uses only a few per word: 35B total, about 3B active. It knows like a big model and runs at the speed of a small one. |
| Quantisation, GGUF, Q4_K_M, MXFP4 | Storing the model's numbers in about 4 bits instead of 16, so it needs about a quarter of the memory with little quality loss. GGUF is the file format; Q4_K_M and MXFP4 are 4-bit schemes. |
| VRAM / GPU memory | Memory on the graphics card. The model must (mostly) fit in it to run fast. |
| Tokens/s | Generation speed. A token is about three-quarters of a word. |
| Thinking / reasoning | Some models write hidden working-out before answering. It improves hard answers but takes time. |
| Closed-book | The model answers from what it learned in training, with no documents. |
| RAG (retrieval-augmented generation) | The most relevant passages from our documents are found automatically and pasted into the question. |
| llama.cpp | The open-source program used to run every model, the same version on every machine. |
| HPC, PBS, node | RTU's computing cluster; PBS is its job scheduler; a node is one server in it. |

## Repository layout

```
bench/                 benchmark: run.py (runs a model through all items), tasks.py (items + scorers),
                       make_data.py (synthetic data + correct answers), summarise.py,
                       make_questions_md.py / make_results_md.py (regenerate the docs/ tables)
bench/data/            frozen inputs: NCBI records, tool manuals, synthetic VCF/FASTQ, truth.json
bench/results/         one JSON per run with every answer, generated script, script output and timing;
                       file prefix = machine (laptop-, t4- = Azure, hpc- = RTU HPC); summary.csv
env/laptop/            laptop guide, model list and checksums, download script
env/azure/terraform/   Terraform for the Azure GPU VM (resource group, network, IP-restricted firewall, auto-shutdown)
env/azure/             Azure guide, setup and run scripts
env/hpc/               RTU HPC guide, setup script, PBS job script, submitter
docs/                  REPORT.md, QUESTIONS.md, RESULTS_BY_ITEM.md, EXAMPLES.md, EXPERIMENT_RECORD.md, MANIFEST.sha256
```

## Rerunning

- **Laptop** (any Linux PC with an NVIDIA GPU, 8 GB+): [env/laptop/README.md](env/laptop/README.md)
- **Azure** (needs GPU quota in your subscription): [env/azure/README.md](env/azure/README.md)
- **RTU HPC** (needs an RTU HPC account and allocation): [env/hpc/README.md](env/hpc/README.md)

Summarise results: `python bench/summarise.py bench/results/hpc-qwen3.5-122b-a10b.json`.
Check file integrity: `sha256sum -c docs/MANIFEST.sha256`.

Model files are not included (4–77 GB each); the guides download them from Hugging Face and verify their
checksums.

## Licence

Code and documentation in this repository: [MIT](LICENSE). Third-party material keeps its own terms: NCBI
records (public domain, US government work), the samtools/bcftools and SeqKit manuals in `bench/data/docs/`
(their projects' licences), and the model weights (see each model's Hugging Face page; all models used
are Apache 2.0).
