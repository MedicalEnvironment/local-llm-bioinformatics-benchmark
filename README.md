<h1 align="center">Local LLMs for Bioinformatics</h1>

<p align="center"><strong>Can open-source AI models, running only on hardware we control, do real bioinformatics work?</strong><br>
A reproducible benchmark on a laptop, an Azure GPU and the RTU HPC cluster.</p>

<p align="center">
<img src="docs/figures/badge-licence.svg" alt="Licence: MIT"> <img src="docs/figures/badge-models.svg" alt="Models: 5 open-weights"> <img src="docs/figures/badge-runs.svg" alt="Runs: 8 on 3 machines"> <img src="docs/figures/badge-items.svg" alt="Items: 53 auto-scored"> <img src="docs/figures/badge-data.svg" alt="Data: public NCBI + synthetic"> <img src="docs/figures/badge-inference.svg" alt="Inference: llama.cpp b11639">
</p>

<p align="center">
<a href="#results">Results</a> ·
<a href="#how-correctness-was-decided">How it was scored</a> ·
<a href="docs/QUESTIONS.md">The 53 questions</a> ·
<a href="docs/EXAMPLES.md">Real answers</a> ·
<a href="docs/REPORT.md">Full report</a> ·
<a href="#rerunning">Rerun it</a>
</p>

<p align="center"><img src="docs/figures/scores-light.svg#gh-light-mode-only" alt="Stacked bar chart of each run's score by section, out of 53. Qwen3.5-122B on 2× L40S and Qwen3.5-35B on a T4 both score 50; Gemma-4-E4B on a laptop scores 37."><img src="docs/figures/scores-dark.svg#gh-dark-mode-only" alt="Stacked bar chart of each run's score by section, out of 53. Qwen3.5-122B on 2× L40S and Qwen3.5-35B on a T4 both score 50; Gemma-4-E4B on a laptop scores 37."></p>

> **In short.** Five open-source models answered the same 53 bioinformatics tasks (write a script, do a lab
> calculation, recall a tool option or gene location), and every answer was checked automatically against keys
> fixed in advance. The largest model (Qwen3.5-122B, RTU HPC) got every script right and scored 50/53; a
> mid-size model on one cloud GPU also scored 50/53. Smaller models often wrote scripts that ran but printed
> wrong numbers. Giving the models the relevant documentation fixed nearly all factual errors. No data left our
> own machines. Each item was asked once, so small score differences are within noise.

## Contents

| If you want to... | Go to |
| --- | --- |
| See what we found | [Results](#results) |
| Know how answers were judged right or wrong | [How correctness was decided](#how-correctness-was-decided) |
| See every question and its correct answer | [docs/QUESTIONS.md](docs/QUESTIONS.md) |
| See which model got which question right | [docs/RESULTS_BY_ITEM.md](docs/RESULTS_BY_ITEM.md) |
| See real model answers: correct, silently wrong, crashed | [docs/EXAMPLES.md](docs/EXAMPLES.md) |
| Read the full write-up, background and limitations | [docs/REPORT.md](docs/REPORT.md) |
| Know where the data came from and which versions ran | [docs/EXPERIMENT_RECORD.md](docs/EXPERIMENT_RECORD.md) |
| Rerun it on a laptop, Azure or the RTU HPC | [Rerunning](#rerunning) |

**Who this is for.** The results, scoring and report need no programming background. Rerunning the benchmark
needs basic Linux shell use; the Azure and HPC guides also assume SSH, and Terraform or PBS respectively.

## What was tested

| Aspect | Details |
| --- | --- |
| **Models** | Qwen3.5-122B-A10B, Qwen3.5-35B-A3B, gpt-oss-20b, Qwen3.5-9B, Gemma-4-E4B (4-bit files, 4–77 GB) |
| **Machines** | Laptop (RTX 4060, 8 GB GPU memory) · Azure VM (Tesla T4, 16 GB) · RTU HPC nodes (1–2× NVIDIA L40S, 48 GB each) |
| **Scripting (7)** | Write a Python script: GC content, translation, longest ORF, GFF summary, VCF filtering, FASTQ quality, k-mer counting. The script is actually run. |
| **Calculations (10)** | Short lab and genetics problems: dilutions, Hardy–Weinberg, qPCR fold change, primer Tm, coverage, ... |
| **Facts (18, asked twice)** | samtools/bcftools/seqkit options and human gene cytogenetic locations; once from memory, once with the relevant manual or NCBI excerpt pasted in (RAG) |
| **Data** | Public NCBI records, public tool manuals, and synthetic VCF/FASTQ generated from them with a fixed seed; no patient or private data |
| **Engine** | llama.cpp b11639, the same build on every machine; temperature 0.6, one run per item |

## Results

| Model | Machine | Scripting /7 | Calculations /10 | Facts from memory /18 | Facts with docs (RAG) /18 | Total /53 | Speed (tokens/s)† |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Qwen3.5-122B-A10B | RTU HPC, 2x L40S | 7 | 10 | 15 | 18 | **50** | 55 |
| Qwen3.5-35B-A3B | Azure, 1x T4 | 6 | 10 | 16 | 18 | **50** | 43 |
| gpt-oss-20b | Azure, 1x T4 | 6 | 10 | 14 | 18 | 48 | 55 |
| Qwen3.5-9B | RTU HPC, 1x L40S | 6 | 9 | 13 | 18 | 46 | 82 |
| Qwen3.5-9B | Azure, 1x T4 | 5 | 10 | 13 | 18 | 46 | 29 |
| Qwen3.5-9B | Laptop | 5 | 9 | 13 | 16* | 43 | 41 |
| Gemma-4-E4B | Azure, 1x T4 | 5 | 8 | 10 | 18 | 41 | 58 |
| Gemma-4-E4B | Laptop | 3 | 9 | 7 | 18 | 37 | 68 |

\* The laptop runs used an older 4,096-token limit on fact answers. It cut off four of the 9B model's answers before they finished (two from memory, two with docs); every miss in this cell is one of those.
† Median generation speed during the benchmark run. Raw speed tests (`llama-bench`) are in the report.

What this means:

- **Only the largest model wrote every script correctly.** Most failed scripts did not crash; they ran and
  printed a plausible but wrong number. Generated code must be tested on data with a known answer.
- **Giving the model the documentation (RAG) fixed nearly all factual errors**: every run scored 18/18, except the laptop 9B run, whose two misses were answers cut off by the older length limit. The gene questions are easy in this form, because the pasted passage states the answer; see the report's limitations.
- **Hardware changed speed far more than quality**: the same 9B model scored 43–46 on three machines, a spread consistent with run-to-run noise.
- **A 35B "mixture-of-experts" model on one 16 GB GPU had the same total (50/53) as the 122B model** in this single run, although only the 122B passed every script.

<p align="center"><img src="docs/figures/accuracy-vs-speed-light.svg#gh-light-mode-only" alt="Scatter of total score against generation speed for each run. The 122B and 35B models score highest; the 9B on an L40S is fastest at about 82 tokens per second."><img src="docs/figures/accuracy-vs-speed-dark.svg#gh-dark-mode-only" alt="Scatter of total score against generation speed for each run. The 122B and 35B models score highest; the 9B on an L40S is fastest at about 82 tokens per second."></p>

## How correctness was decided

No model and no person judged answers during the runs. Every correct answer was fixed **before** any model
ran, from primary sources or our own reference code, and a program compared each answer with it.

| Section | What the model had to produce | How it was checked | Where the correct answer came from |
| --- | --- | --- | --- |
| Scripting | A Python script in a code block | The script is run on the real input file (isolated Python, 2-minute limit). It must exit without error and print exactly the right result: counts, coordinates and lengths must match exactly; decimals within rounding (e.g. GC% ±0.011). | Computed by `bench/make_data.py` with Biopython, independently of any model (`bench/data/truth.json`) |
| Calculations | A final line `ANSWER: <number>` | The number must be within 1% of the key | Worked by hand; fixed in `bench/tasks.py` |
| Facts: gene locations | A final line `ANSWER: <band>` | Must contain the exact NCBI band, e.g. `11p15.4` | NCBI Gene `maplocation` field (`bench/data/raw/gene_summaries.json`) |
| Facts: tool options | A final line `ANSWER: <option>` | Must contain the option; short or long form accepted (`-s` or `--by-seq`) | The official manuals in `bench/data/docs/` |

Only the final `ANSWER:` line counts, so a correct explanation with a wrong final line fails. After the runs,
every failure was inspected by hand, and an independent cold review re-derived every answer key from the raw
files. Three scoring issues were found:

1. **An answer key was incomplete (corrected).** `samtools sort` sorts by read name with `-n` and also with `-N`
   (lexicographic). The key first accepted only `-n`; it now accepts both, and all stored answers were rescored with
   `bench/rescore.py`. This changed one item (Gemma-4-E4B on Azure, 40 to 41). Changed items keep their earlier score
   as `ok_before_rescore`.
2. **A correct answer in the wrong format (not changed).** gpt-oss-20b gave CFTR 7q31.2 correctly but wrote `Answer:`
   instead of `ANSWER:`; with a case-insensitive parser it would score 49.
3. **Arguable answers (not changed).** Both Gemma runs selected SNPs with `-i 'TYPE="snp"'`, a valid bcftools filter
   expression, rather than the `-v snps` option the question asks for. Several models gave TNF as 6p21.3 rather
   than the requested sub-band 6p21.33.

The scorer is also lenient in one way: an accepted option anywhere on the final line passes, so a hedged answer
naming several options would pass too. With one run per item, differences of 1–2 points between models can be
chance.

The exact scoring code is `score_script`, `score_reason` and `score_retr` in [bench/tasks.py](bench/tasks.py).

<details>
<summary><strong>Glossary</strong>: RAG, mixture-of-experts, quantisation, tokens/s and other terms</summary>

| Term | Meaning |
| --- | --- |
| Section names | Scripting = `script`; Calculations = reasoning = `reason`; Facts from memory = closed-book = `closed`; Facts with docs = RAG = `rag` (the second name is used in the report, the third in result files). |
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

</details>

<details>
<summary><strong>Repository layout</strong></summary>

```
bench/                 benchmark: run.py (runs a model through all items), tasks.py (items + scorers),
                       make_data.py (synthetic data + correct answers), summarise.py,
                       rescore.py (re-apply scorers to stored answers),
                       make_questions_md.py / make_results_md.py / make_figures.py (regenerate docs/)
bench/data/            frozen inputs: NCBI records, tool manuals, synthetic VCF/FASTQ, truth.json
bench/results/         one JSON per run with every answer, generated script, script output and timing;
                       file prefix = machine (laptop-, t4- = Azure, hpc- = RTU HPC); summary.csv
env/laptop/            laptop guide, model list and checksums, download script
env/azure/terraform/   Terraform for the Azure GPU VM (resource group, network, IP-restricted firewall, auto-shutdown)
env/azure/             Azure guide, setup and run scripts
env/hpc/               RTU HPC guide, setup script, PBS job script, submitter
docs/                  REPORT.md, QUESTIONS.md, RESULTS_BY_ITEM.md, EXAMPLES.md, EXPERIMENT_RECORD.md, MANIFEST.sha256
docs/figures/          README charts and badges, generated by make_figures.py
```

</details>

## Rerunning

| Where | Needs | Guide |
| --- | --- | --- |
| Laptop | Linux, NVIDIA GPU with 8 GB+, Python 3.12+ | [env/laptop/README.md](env/laptop/README.md) |
| Azure | Subscription with T4 (or larger) GPU quota, Azure CLI, Terraform optional | [env/azure/README.md](env/azure/README.md) |
| RTU HPC | RTU HPC account and allocation, SSH key, PBS basics | [env/hpc/README.md](env/hpc/README.md) |

Summarise results: `python bench/summarise.py bench/results/hpc-qwen3.5-122b-a10b.json`.
Rescore stored answers after changing a key in `bench/tasks.py`: `python bench/rescore.py`.
Regenerate the tables and figures in `docs/`: `python bench/make_questions_md.py`, `python bench/make_results_md.py`,
`python bench/make_figures.py`. Check file integrity: `sha256sum -c docs/MANIFEST.sha256`.

Model files are not included (4–77 GB each); the guides download them from Hugging Face and verify their checksums.

## Citing

If you use this benchmark, please cite it with GitHub's **Cite this repository** button (from [CITATION.cff](CITATION.cff)).

## Licence

Code and documentation in this repository: [MIT](LICENSE). Third-party material keeps its own terms: NCBI
records (public domain, US government work), the samtools/bcftools and SeqKit manuals in `bench/data/docs/`
(their projects' licences), and the model weights (see each model's Hugging Face page; all models used
are Apache 2.0).
