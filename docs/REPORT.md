# Local and Private LLMs for Bioinformatics: Benchmark Report

29 October 2026

## Summary

Open-weights LLMs running entirely on hardware we control can already write correct bioinformatics scripts, solve lab calculations and answer documentation questions; model size is what separates "usually right" from "reliably right". Across eight benchmark runs (five models, three machines, 53 scored items each), the best two models scored **50/53**: Qwen3.5-122B-A10B on two RTU HPC L40S GPUs and Qwen3.5-35B-A3B on a single 16 GB Azure T4.

- **Scripting is where size pays off.** Only Qwen3.5-122B-A10B passed all 7 executed scripts. Every smaller model produced at least one script that ran cleanly but printed a wrong answer (off-by-one coordinates, wrong VCF column, invented API).
- **Retrieval-augmented generation (RAG) closes the knowledge gap.** With the relevant documentation pasted into the prompt, every run scored 18/18 except one whose two misses were answers cut off by a length limit. Without it (closed-book), scores ranged from 7/18 to 16/18.
- **Hardware sets speed far more than answers.** Qwen3.5-9B scored 43–46/53 on all three machines, a spread consistent with run-to-run noise; generation speed ranged from 29 tokens/s (Azure T4) to 82 tokens/s (HPC L40S).
- **Mixture-of-experts (MoE) models are the practical sweet spot.** Qwen3.5-35B-A3B and gpt-oss-20b activate only ~3–4 B parameters per token, so they run at 43–55 tokens/s on a 16 GB GPU while scoring 48–50/53.

Recommendation: use a MoE model of 20–35 B total parameters for day-to-day scripting help, pair any model with RAG over our own documentation, and always test generated scripts on data with a known answer. The RTU HPC can serve a 120 B-class model privately when maximum accuracy is needed.

## Background and goals

The goal was to find out whether LLMs that run on hardware we control are good enough for routine bioinformatics help, and how much hardware that takes. Cloud chat services are convenient, but sending unpublished sequences, sample metadata or patient-derived data to a third party raises data-protection and contract questions. A model on a laptop, a university HPC node or a VM in our own Azure subscription keeps the data in place.

### Questions this study answers

1. Can a local model write a bioinformatics script that is not just runnable but **correct**?
2. Can it handle the short quantitative reasoning common in wet-lab and genetics work?
3. How reliable is its built-in knowledge of tool options and gene facts, and does supplying documentation (RAG) fix the gaps?
4. What does each level of accuracy cost in GPU memory, speed and money, on a laptop, a cloud VM and the RTU HPC?

### What the literature and model documentation lead us to expect

- **Scale and capability.** Scaling-law studies (Kaplan et al., 2020; Hoffmann et al., 2022) show that loss falls predictably with parameters and training data, and that larger models are markedly better at rare facts. We therefore expected closed-book recall of niche facts, such as a seqkit option or a cytogenetic sub-band, to improve most with model size.
- **Mixture-of-experts (MoE).** MoE models (Shazeer et al., 2017; Fedus et al., 2022; Jiang et al., 2024, Mixtral) store many "expert" sub-networks but route each token through only a few. Total parameters set knowledge and memory footprint; active parameters set speed. Qwen3.5-35B-A3B (≈3 B active), gpt-oss-20b (≈3.6 B active), Qwen3.5-122B-A10B (≈10 B active) and gpt-oss-120b (≈5 B active) are all MoE models, which is why they run at small-model speed.
- **Quantisation.** Storing weights in about 4 bits instead of 16 cuts memory roughly fourfold. Studies of post-training quantisation (Frantar et al., 2023, GPTQ; Dettmers et al., 2023) and llama.cpp's own K-quant measurements report only small quality losses at 4–5 bits for models of this size. All models here used 4-bit GGUF files (Q4_K_M, Unsloth dynamic Q4_K_XL, or the native MXFP4 that gpt-oss is released in).
- **Retrieval-augmented generation.** Lewis et al. (2020) showed that putting retrieved passages into the prompt improves factual accuracy and lets a model answer from sources it never memorised. For tool documentation that changes between versions, this is also the only way to keep answers current.
- **Test-time reasoning ("thinking").** Models that write a hidden chain of reasoning before answering (Wei et al., 2022; reasoning-tuned models such as Qwen3.5 and gpt-oss) solve more multi-step problems, at the cost of many more generated tokens and therefore time.
- **Code generation is judged by execution, not appearance.** Code benchmarks such as HumanEval (Chen et al., 2021) score functional correctness by running the code against tests. We follow the same principle with bioinformatics-specific tasks, because a script that runs without error can still print a wrong number. Existing biomedical QA benchmarks (for example BioASQ and the GeneTuring gene-knowledge tests) motivated the gene-location questions.

### Models tested

| Model | Publisher, licence | Total / active parameters | File (quantisation) | Size |
| --- | --- | --- | --- | --- |
| Gemma-4-E4B-it | Google, Apache 2.0 | ≈8 B / ≈4 B effective | Unsloth QAT UD-Q4_K_XL | 4.2 GB |
| Qwen3.5-9B | Alibaba Qwen, Apache 2.0 | 9 B dense | Unsloth Q4_K_M | 5.7 GB |
| gpt-oss-20b | OpenAI, Apache 2.0 | 21 B / ≈3.6 B (MoE) | ggml-org MXFP4 | 12.1 GB |
| Qwen3.5-35B-A3B | Alibaba Qwen, Apache 2.0 | 35 B / ≈3 B (MoE) | Unsloth Q4_K_M | 22.0 GB |
| Qwen3.5-122B-A10B | Alibaba Qwen, Apache 2.0 | 122 B / ≈10 B (MoE) | Unsloth Q4_K_M (3 files) | 76.6 GB |

All files came from Hugging Face (repositories `unsloth/*-GGUF` and `ggml-org/gpt-oss-20b-GGUF`), and each download was checked against the SHA-256 published by Hugging Face. Gemma-4-12B was started on the laptop but abandoned after 2 items because it ran at only 13 tokens/s; it is not included in the results.

## Experimental design and data

Each model answered the same 53 items under identical settings, and every item was scored automatically against an answer key computed independently of any model. No patient, clinical or otherwise private data were used: all inputs are public reference records from NCBI and public tool manuals, plus synthetic files generated from them with a fixed random seed. All data were downloaded on 15 October 2026 and frozen; every machine received byte-identical copies.

### Data sources: what, from where, and how

| File | What it contains | Where it came from | How it was obtained | Used by |
| --- | --- | --- | --- | --- |
| `lambda.fa` | Enterobacteria phage lambda complete genome, 48,502 bp, one record | NCBI RefSeq [NC_001416.1](https://www.ncbi.nlm.nih.gov/nuccore/NC_001416.1) | NCBI E-utilities `efetch`, `db=nuccore`, `rettype=fasta` | Longest ORF, k-mer count; template for the synthetic VCF and FASTQ |
| `lambda.gff3` | NCBI annotation of the same genome: 308 features of 13 types, including 92 genes, 73 CDS, 23 mRNA and 23 exons | NCBI RefSeq NC_001416.1 | NCBI Sequence Viewer GFF3 export (`report=gff3`) | GFF feature summary |
| `cds.fa` | Coding sequences of 6 human genes: TP53 (NM_000546.6), BRCA1 (NM_007294.4), CFTR (NM_000492.4), HBB (NM_000518.5), INS (NM_000207.3), BRAF (NM_004333.6) | NCBI RefSeq mRNA records | `efetch`, `rettype=fasta_cds_na`; headers keep NCBI's `[gene=…]` tags | GC content, CDS translation |
| `gene_summaries.json` | NCBI Gene records (name, aliases, chromosome, cytogenetic band, curated summary) for TP53, BRCA1, CFTR, HBB, INS, BRAF, EGFR, TNF | [NCBI Gene](https://www.ncbi.nlm.nih.gov/gene/) IDs 7157, 672, 1080, 3043, 3630, 673, 1956, 7124 | `efetch`, `db=gene`, `rettype=docsum`, JSON | Answer key for the 8 gene-location questions; source of `genes.txt` |
| `calls.vcf` | 400 synthetic variant calls on lambda coordinates (VCF 4.2, 8 columns, no samples) | Generated locally by `make_data.py` from `lambda.fa` | Python, `random.seed(42)` (details below) | VCF filtering + Ts/Tv |
| `reads.fastq` | 500 synthetic 150 bp reads, Phred+33 | Generated locally by `make_data.py` from `lambda.fa` | Python, same seed | FASTQ quality summary |
| `samtools*.txt`, `bcftools.txt` | Manual pages for samtools (main page plus view, sort, markdup, depth, faidx) and bcftools | [htslib.org/doc](https://www.htslib.org/doc/) | HTML downloaded, converted to plain text by `docs2txt.py` (scripts, styles and navigation stripped) | RAG corpus for the 10 tool-flag questions |
| `seqkit.txt` | SeqKit usage manual (all subcommands) | [bioinf.shenwei.me/seqkit/usage](https://bioinf.shenwei.me/seqkit/usage/) | Same HTML-to-text conversion | RAG corpus |
| `genes.txt` | One paragraph per gene: name, NCBI Gene ID, chromosome, cytogenetic location, aliases, summary | Built from `gene_summaries.json` | Templated text, one paragraph per gene | RAG corpus for the 8 gene-location questions |

The exact download commands are in [EXPERIMENT_RECORD.md](EXPERIMENT_RECORD.md); the raw HTML is kept beside each converted text file, and SHA-256 checksums of every file are in [MANIFEST.sha256](MANIFEST.sha256).

### How the synthetic files were generated

Real variant calls and reads were not needed: the point is to check whether a generated script computes a known answer, so the data only has to be realistic in format and contain edge cases. `make_data.py` uses one fixed seed (42), so rerunning it reproduces both files byte for byte.

- **VCF (400 records).** Positions are sampled without replacement from lambda coordinates 100–48,402, and the REF base is the real genome base at that position. 75% are SNVs (random different ALT base), 13% insertions of 1–5 bp and 12% deletions of 1–5 bp. QUAL is uniform on 3–99 (one decimal), INFO `DP` is uniform on 2–80, and FILTER is PASS (80%), LowQual (12%) or StrandBias (8%). The file deliberately has only 8 columns (no FORMAT or sample columns), which caught scripts that assume a 10-column VCF.
- **FASTQ (500 reads).** Each read is a 150 bp forward-strand substring of lambda at a random start. Each read gets a quality level drawn from {12, 18, 25, 32, 36}; per-base qualities are Gaussian around that level (SD 6), clipped to 2–41 and encoded as Phred+33. This puts reads on both sides of the Q20 threshold.

### The 53 items

- **Scripting (7 items).** The model writes a complete Python 3 script (standard library plus Biopython, NumPy and pandas). The harness runs the script in an isolated interpreter (`python -I`, 120 s timeout) on the real input file, and its stdout must match the answer key. Tasks: GC content per gene, CDS translation length, longest ORF across six frames (coordinates, strand, length), GFF feature counts plus total CDS length, VCF filter (PASS, QUAL ≥ 30, DP ≥ 10) with SNV/indel counts and Ts/Tv ratio, FASTQ mean quality and Q20 pass count, most frequent 8-mer.
- **Reasoning (10 items).** Short quantitative lab and genetics problems with a single numeric answer: Punnett probability, serial dilution, Wallace-rule primer Tm, Hardy–Weinberg carrier frequency, picomoles of plasmid, sequencing read pairs for 30× coverage, peptide length from an mRNA, qPCR 2^−ΔΔCt fold change, Bayes positive predictive value, expected EcoRI sites.
- **Retrieval, closed-book (18 items).** Factual questions answered from the model's own memory: 10 command-line options for samtools, bcftools and seqkit, and 8 human gene cytogenetic locations.
- **Retrieval with RAG (the same 18 items).** The same questions, with the five most relevant documentation excerpts pasted into the prompt.

### How answer keys were made

- **Scripts:** `make_data.py` computes every answer directly with Biopython and plain Python, independent of any model, and stores it in `truth.json`. For example, the VCF key is kept = 207, SNV = 151, indel = 56, Ts/Tv = 0.525; the longest ORF is 15,505–18,903 on the + strand, 3,399 bp including the stop codon.
- **Reasoning:** worked by hand and fixed in `tasks.py` (Wallace Tm is computed from the primer). A numeric answer within 1% of the key passes.
- **Tool options:** checked against the downloaded manuals (for example `bcftools view -v/--types snps`, `seqkit rmdup -s/--by-seq`). Each key is a regular expression that accepts the short or long form.
- **Gene locations:** taken verbatim from the NCBI Gene `maplocation` field (for example HBB 11p15.4, TNF 6p21.33). Questions for BRCA1 and TNF explicitly ask for band and sub-band, so the less specific 6p21.3 is scored as wrong.

### The RAG pipeline

The documentation corpus was split into 499 chunks: one chunk per gene, and roughly 1,200-character chunks with 300 characters of overlap for the manuals. Chunks and questions were embedded with Google's EmbeddingGemma-300M (Q8_0, run locally in llama.cpp) using its recommended `title:`/`task: search result` prefixes. For each question, the five chunks with the highest cosine similarity were stored once in `rag_index.json` and reused by every model, so all models saw identical context. Retrieval alone found a chunk containing the correct answer for all 18 questions (hit@5 = 18/18), so RAG scores measure whether the model read the context correctly.

### Generation and scoring settings

| Setting | Value |
| --- | --- |
| Inference engine | llama.cpp release b11639 (official CUDA 12.8 build), `llama-server` OpenAI-compatible API |
| Sampling | temperature 0.6, top-p 0.95, seed 1 |
| Context window | 16,384 tokens, flash attention on, automatic GPU/CPU placement (`--fit on`) |
| Thinking | Model default (on for Qwen3.5 and gpt-oss), reasoning budget 6,144 tokens |
| Max output | 8,192 tokens per answer |
| Answer format | Scripts in one fenced code block; reasoning and retrieval end with a final `ANSWER:` line |
| Runs | One run per item per model |
| Speed test | `llama-bench`: 512-token prompt and 128-token generation, 3 repetitions |

The `ANSWER:` line is parsed exactly, and the scorer is strict: an answer that is right in the explanation but wrong on the final line fails, and so does a final line written as `Answer:` instead of `ANSWER:` (this affected one gpt-oss-20b item; see Error analysis).

## Compute environments

The same benchmark code, llama.cpp build (b11639) and data ran on three machines, so differences in scores reflect the models, and differences in speed reflect the hardware.

| | Laptop | Azure VM | RTU HPC node |
| --- | --- | --- | --- |
| Where | Local, offline-capable | Group subscription, resource group `rg-llm-bench-neu`, North Europe | RTU "Rudens" cluster, login via ui-1.hpc.rtu.lv, batch queue |
| GPU | NVIDIA RTX 4060 Laptop, 8 GB | NVIDIA Tesla T4, 16 GB (2018, Turing) | NVIDIA L40S, 48 GB each (2023, Ada); 1 GPU for the 9B run, 2 for the 122B run |
| CPU / RAM | AMD Ryzen 7 7435HS, 15 GB | 4 vCPU (AMD EPYC), 28 GB | 2× AMD EPYC 9654 (192 cores), 1.5 TB; job allocation 8 cores per GPU |
| VM size or node | – | Standard_NC4as_T4_v3 | wn73 (9B), wn75 (122B) |
| OS / driver | Ubuntu 26.04 | Ubuntu 24.04 (Microsoft `ubuntu-hpc` image), driver 580 | CentOS 7, driver 550, Torque 6.1 + Moab scheduler |
| How llama.cpp ran | Official binaries | Official binaries | Official binaries inside a Debian 13 container (`python:3.12-slim-trixie`), run with Apptainer 1.1.6 from node-local `/scratch` |
| Storage | Local NVMe | 256 GB Premium SSD | BeeGFS home (models, results), NVMe `/scratch` (container) |
| Models run | Qwen3.5-9B, Gemma-4-E4B | Qwen3.5-9B, Gemma-4-E4B, gpt-oss-20b, Qwen3.5-35B-A3B | Qwen3.5-9B, Qwen3.5-122B-A10B |
| Cost | Existing hardware | About $0.53/hour for the VM, roughly $3–4 for the whole run | Charged to the group's HPC allocation |

### Software stack

- **Inference:** llama.cpp b11639, official CUDA 12.8 release from the ggml-org GitHub repository, SHA-256 verified. The same binary ran everywhere. On the HPC, CentOS 7's C library (glibc 2.17) is too old for it, so it ran inside a stock Debian 13 container that provides glibc 2.41. The OpenMP runtime (`libgomp1`) came from the official Debian archive and was checked against the archive's published SHA-256.
- **Harness:** `run.py` starts `llama-server` on a free local port, sends each prompt through its OpenAI-compatible API, executes generated scripts in an isolated interpreter, scores the answers and records timings and peak GPU memory. Results are written after every item, so an interrupted run resumes where it stopped.
- **Python environment:** Python 3.12–3.14 with Biopython, NumPy and pandas, the only third-party libraries the generated scripts were allowed to use.
- **Model placement:** `--fit on` lets llama.cpp put as many layers as fit on the GPU and the rest in system RAM. Only Qwen3.5-35B-A3B on the T4 needed this (22 GB model, 16 GB GPU): its expert weights partly ran from CPU memory.
- **Isolation:** every server bound to 127.0.0.1 only. The Azure VM's firewall allowed SSH from one IP address only, with key-based login. HPC jobs ran on the GPUs the scheduler assigned (`CUDA_VISIBLE_DEVICES` from `PBS_GPUFILE`) on a per-job port, because the nodes are shared with other users.

## Results

Two models tied for the top score of 50/53: Qwen3.5-122B-A10B (HPC, 2× L40S) and Qwen3.5-35B-A3B (Azure, one T4). The same Qwen3.5-9B model scored 43–46 on every machine, a spread consistent with run-to-run noise, while its speed varied almost threefold.

| Run | Machine | Scripting /7 | Reasoning /10 | Closed-book /18 | RAG /18 | **Total /53** | Speed in run (tokens/s) | Peak VRAM | Time for 53 items |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Qwen3.5-122B-A10B | HPC 2× L40S | **7** | **10** | 15 | **18** | **50** | 55 | 72.9 GB | 32 min |
| Qwen3.5-35B-A3B | Azure T4 | 6 | **10** | **16** | **18** | **50** | 43 | 14.3 GB | 60 min |
| gpt-oss-20b | Azure T4 | 6 | **10** | 14 | **18** | 48 | 55 | 11.3 GB | 8 min |
| Qwen3.5-9B | HPC 1× L40S | 6 | 9 | 13 | **18** | 46 | 82 | 6.1 GB | 28 min |
| Qwen3.5-9B | Azure T4 | 5 | **10** | 13 | **18** | 46 | 29 | 5.7 GB | 82 min |
| Qwen3.5-9B | Laptop | 5 | 9 | 13 | 16¹ | 43 | 41 | 6.6 GB | 50 min |
| Gemma-4-E4B | Azure T4 | 5 | 8 | 10 | **18** | 41 | 58 | 3.1 GB | 10 min |
| Gemma-4-E4B | Laptop | 3 | 9 | 7 | **18** | 37 | 68 | 3.8 GB | 10 min |

¹ The laptop runs used an earlier 4,096-token output limit on retrieval answers, which cut off four of the 9B model's answers (two RAG, two closed-book) before their final line; both RAG misses are among them. All other runs used 8,192 tokens.

Scores reflect one correction made after the runs: the answer key for sorting by read name in samtools now also accepts `-N`, which raised Gemma-4-E4B on Azure from 40 to 41 (see Scorer artefacts). "Speed in run" is the median generation speed across the 53 answers.

The same table, machine-readable, is in `bench/results/summary.csv`.

### Speed benchmark (llama-bench, tokens per second)

| Run | Prompt processing (512 tokens) | Generation (128 tokens) |
| --- | --- | --- |
| Qwen3.5-9B, HPC 1× L40S | 7,167 | 107 |
| Qwen3.5-122B-A10B, HPC 2× L40S | 2,539 | 63 |
| Gemma-4-E4B, Azure T4 | 2,116 | 64 |
| gpt-oss-20b, Azure T4 | 1,421 | 61 |
| Qwen3.5-9B, Azure T4 | 1,078 | 34 |
| Qwen3.5-35B-A3B, Azure T4 (part in CPU RAM) | 656 | 48 |

### What the numbers show

- **Accuracy rises with total parameters, speed follows active parameters.** On the same L40S hardware, the 122B MoE model generates 63 tokens/s against 107 for the dense 9B: a model 13 times larger is only 1.7 times slower, because only about 10 B of its parameters are used per token.
- **The "thinking" budget dominates wall-clock time.** Qwen3.5 models generated 100,000–150,000 tokens per run, mostly hidden reasoning. gpt-oss-20b produced about 22,000 and finished all 53 items in 8 minutes at a near-top score.
- **RAG is close to perfect for every model**, including the 4 B-class Gemma (but see Limitations on how easy these RAG questions are). Closed-book recall is the main differentiator between models.
- **Memory is the hard limit.** The 122B model needs about 73 GB of GPU memory, which only the HPC provides. Qwen3.5-35B-A3B fits a 16 GB GPU by keeping part of its experts in CPU RAM, at the cost of slower prompt processing (656 tokens/s).

## Error analysis

Most failures were not crashes but plausible-looking wrong answers, which is the main risk of using these models without checks. Of 13 failed scripts across the eight runs, 9 ran to completion (exit code 0) and printed a confident but wrong result; only 4 crashed. Item-by-item results for every run are in [RESULTS_BY_ITEM.md](RESULTS_BY_ITEM.md), and verbatim examples in [EXAMPLES.md](EXAMPLES.md).

### Scripting failures

| Failure | Runs affected | What went wrong |
| --- | --- | --- |
| Longest ORF off by one | Qwen3.5-9B (T4), Qwen3.5-35B-A3B, gpt-oss-20b; Gemma-4-E4B printed nothing (laptop) or crashed (T4) | Reported the correct length (3,399 bp) but coordinates 15,505–18,902, 15,505–18,901 or 15,504–18,902 instead of 15,505–18,903: a 0-based vs 1-based or stop-codon-inclusion slip. |
| VCF filter: wrong column layout | Qwen3.5-9B (laptop, T4) | Assumed sample columns are always present and read QUAL from the wrong column: the laptop script skipped every line and printed kept = 0 instead of 207; the T4 script read FILTER (`PASS`) as QUAL and crashed. |
| VCF filter: invented API | Qwen3.5-9B (HPC) | Called `pandas.read_vcf`, which does not exist. |
| GC content: lost first letter of gene names | Qwen3.5-9B (laptop) | Off-by-one string slice turned `TP53` into `P53`; every GC value was right. Gemma-4-E4B (laptop) printed UNKNOWN for every gene name instead. |
| Translation: wrong record label | Gemma-4-E4B (T4); Gemma-4-E4B (laptop) printed nothing | Printed the FASTA ID instead of the gene name from the `[gene=…]` tag; the lengths were correct. |
| k-mer count: wrong library call | Gemma-4-E4B (laptop) | Called Biopython's `SeqIO.parse()` without its required format argument and crashed. |

Only Qwen3.5-122B-A10B passed all seven. The six-frame ORF coordinate convention was the hardest task: only 3 of 8 runs got it right (the 122B and the 9B on the HPC and laptop).

### Reasoning failures

- **mRNA peptide length:** Qwen3.5-9B (laptop) answered 7 instead of 5 by misreading where the first stop codon falls. On the HPC the same model thought until it hit the 8,192-token limit.
- **mRNA peptide length, Gemma:** both Gemma-4-E4B runs also answered 7 instead of 5.
- **Wallace-rule Tm:** Gemma-4-E4B (T4) counted 7 A+T and 7 G+C in an 18-mer (should be 9 and 9) and answered 42 °C instead of 54 °C. Base counting is a known weakness of tokenised models.

### Retrieval failures (closed-book)

| Question | Correct (source) | Typical wrong answer | Models wrong |
| --- | --- | --- | --- |
| TNF location (band and sub-band) | 6p21.33 (NCBI Gene) | 6p21.3, the older, less specific band | All 8 runs |
| HBB location | 11p15.4 (NCBI Gene) | 11p15.5, the band of neighbouring INS | 7 of 8 runs; only the 122B was right |
| seqkit rmdup by sequence | `-s` / `--by-seq` (seqkit manual) | `-S`, `-c`, `--seq` | 5 runs |
| bcftools view, SNPs only | `-v snps` / `--types snps` (bcftools manual) | `-t snps` (`-t` is `--targets`) | 4 runs, including the 122B |
| EGFR location | 7p11.2 | 7q31.3 or 7p13 | Qwen3.5-9B on all machines |
| BRAF location | 7q34 | 7p34 (122B, wrong arm); 7q31.2 or 7q14 (Gemma) | Qwen3.5-122B-A10B, both Gemma runs |

Gemma-4-E4B also invented samtools options (`-n`, `-r`, `-f` answered wrongly) closed-book; with the manual excerpt supplied, all of them were answered correctly.

### Scorer artefacts

Every failure was checked by hand, and an independent review re-derived all answer keys from the raw files. Three issues were found:

1. **Incomplete key, corrected.** `samtools sort` sorts by read name with `-n` and also `-N` (lexicographic), as the supplied manual states. The key first accepted only `-n`. It now accepts both; all stored answers were rescored by `bench/rescore.py` (answers are not regenerated). One item changed: Gemma-4-E4B on Azure, RAG 17 to 18, total 40 to 41.
2. **Right answer, wrong format, not changed.** One gpt-oss-20b answer was correct (CFTR 7q31.2) but ended with `Answer:` instead of `ANSWER:`; with a case-insensitive parser gpt-oss-20b scores 49/53.
3. **Arguable answers, not changed.** Both Gemma runs selected SNPs with `-i 'TYPE="snp"'`, a valid bcftools filter expression but not the type option the question asks for. TNF's 6p21.3 is not false, only less specific than the sub-band the question asked for.

The retrieval scorer is also lenient: an accepted option anywhere on the final line passes, so a hedged answer that lists several options would pass.

## Discussion and limitations

The results match the expectations from the literature: knowledge scales with total parameters, speed with active parameters, and retrieval removes most of the knowledge gap. The practical consequence is that a mid-sized MoE model plus RAG over our own documentation gives near-top accuracy on hardware we already have or can rent cheaply.

- **Correctness needs verification, whatever the model.** Every model below 122 B produced at least one script that ran and printed a wrong number. Generated code must be tested on inputs with a known answer before it touches real data, exactly as this benchmark does.
- **RAG is the cheapest accuracy gain.** It moved Gemma-4-E4B from 7–10/18 to 18/18 on factual questions. It needs only a small embedding model (300 M parameters) and a document index.
- **"Thinking" trades time for accuracy unevenly.** Qwen3.5 thinks at length (up to 8,000 tokens on one item), which explains its long run times. gpt-oss-20b reached 48/53 with about one-sixth of the tokens, making it the most efficient model per answer.
- **The HPC makes 100 B-class models usable privately.** Two L40S GPUs held the 122B model entirely in GPU memory at 55–63 tokens/s, fast enough for interactive use.

### Limitations

- **One run per item.** With temperature 0.6, a single run can flip an item either way; differences of one or two points between runs are within noise. The 9B model's 43–46 range across machines is a direct estimate of that noise.
- **Small task set.** 53 items cover typical tasks but not large codebases, multi-file pipelines, workflow languages (Nextflow, Snakemake) or long documents.
- **Automatic scoring has edges.** One correct answer failed on formatting and less-specific gene bands count as wrong, while hedged retrieval answers listing several options would pass. One incomplete key was found and corrected after the runs (see Scorer artefacts).
- **The RAG questions are easy in this form.** For the gene questions, the pasted passage states the cytogenetic band verbatim, so they test copying from context more than understanding. Retrieval quality (hit@5) was measured by whether a retrieved chunk contains the answer pattern, which is weak evidence for short options such as `-n`. RAG over our own, larger documentation is untested.
- **Same harness, slightly different versions.** The laptop runs were made with an earlier `run.py` (same prompts and scorers, before the portability changes) and a 4,096-token retrieval limit. Python package versions were not pinned. Generation is not bit-identical across GPUs.
- **Ground truth from one source.** Gene locations follow NCBI Gene; other databases (Ensembl, older literature) sometimes give different band resolution.
- **Models not yet run on the HPC.** gpt-oss-120b, Qwen3.5-27B and Gemma-4-31B were downloaded but not benchmarked before this report.
- **Laptop run settings differed slightly** (4,096-token output limit), as noted under Results.

## Operational lessons and cost

Setting up took longer than running the benchmarks; most delays came from cloud capacity, network policy and HPC node quirks, not from the models. These notes should save the next run several hours.

### Azure

- **GPU quota existed only in North Europe** for the subscription used: 16 vCPUs of NCasT4_v3 (T4). Every other European region checked had zero GPU quota; A10, A100 and H100 families need a quota request.
- **Capacity is not guaranteed even with quota.** NC16as_T4_v3 (110 GB RAM, which would have run gpt-oss-120b) and NC8as_T4_v3 failed with `AllocationFailed` in all three zones; only NC4as_T4_v3 could be allocated.
- **Failed deployments leave billable public IPs** behind; seven had to be deleted by hand. Deleting the whole resource group after the run is the simplest clean-up.
- **The Microsoft `ubuntu-hpc` image** ships a working NVIDIA driver (580), so no driver installation or reboot was needed.
- **VPNs change the source IP.** With Cloudflare WARP active, SSH left from a different address than web traffic, so the IP-restricted firewall rule blocked it.

### RTU HPC

- **Too many short SSH connections triggered a block** on ui-2.hpc.rtu.lv for the rest of the day. ui-1 worked; an SSH `ControlMaster` configuration (one shared connection) avoids the problem.
- **CentOS 7 is too old for current binaries** (glibc 2.17), hence the container.
- **Singularity 3.4.1 hung on compute nodes**, and node wn74 kept a stuck container process that blocked new containers. Unpacking the image with Apptainer 1.1.6 into node-local `/scratch` works; wn74 should be reported to hpc@rtu.lv.
- **Apptainer resets `LD_LIBRARY_PATH`** inside the container; pass it as `APPTAINERENV_LD_LIBRARY_PATH`.
- **Node wn71 carried a scheduler reservation**, so a job pinned to it stayed queued; check `checkjob <id>` and pin to a free node.
- **Hugging Face downloads can stall** (from 40 MB/s to 1.6 MB/s); restarting the connection with resume restored the speed.

### Cost

| Item | Cost |
| --- | --- |
| Azure NC4as_T4_v3 VM, about 6 hours | about $3–4 (pay-as-you-go list price about $0.53/hour, plus disk and IP) |
| RTU HPC, about 1 GPU-hour (122B, 32 min on 2 GPUs) plus 0.5 GPU-hours (9B) | Charged to the group's Moab allocation |
| Laptop | No marginal cost |

## Reproducing the study

See the repository [README](../README.md) and the per-environment guides in `env/laptop`, `env/azure` and `env/hpc`. A full rerun of the T4 queue takes about 3 hours and $2; the 122B job takes about 35 minutes on two L40S GPUs.

## Recommendations and next steps

1. **Default assistant: Qwen3.5-35B-A3B or gpt-oss-20b**, with RAG. Both run on a single 16 GB GPU (T4 or better), scored 48–50/53, and keep all data in our infrastructure. gpt-oss-20b is about 7× faster per run; Qwen3.5-35B-A3B recalls more facts.
2. **Highest accuracy: Qwen3.5-122B-A10B on two HPC L40S GPUs**, the only model with every script correct. Suitable for batch use through PBS, or interactive use through an SSH tunnel to a running job.
3. **Add RAG over our own documentation** (tool manuals, SOPs, pipeline READMEs). Here it brought every model to 18/18 on factual questions when answers were not cut off; on our own, larger documents this still needs testing.
4. **Treat generated scripts as drafts.** Test on a small input with a known answer; 9 of the 13 failed scripts ran without error.
5. **Laptops are adequate for small models** (Qwen3.5-9B, Gemma-4-E4B). Repository-scale or agentic coding was not tested here; given the small models' scripting error rate, we would not expect them to be reliable for it.

Next steps:

- [ ] Run gpt-oss-120b, Qwen3.5-27B and Gemma-4-31B on the HPC (already downloaded and verified).
- [ ] Repeat each item 3–5 times to separate real differences from sampling noise.
- [ ] Add workflow tasks (Nextflow, Snakemake), longer scripts and a larger RAG corpus from our own documentation.
- [ ] Report the stuck container process on node wn74 to hpc@rtu.lv.
- [ ] Request A10 or A100 quota in a second Azure region so larger models can run in the cloud.

## References and sources

**Data and documentation used in the benchmark** (downloaded 15 October 2026)

- NCBI RefSeq, Enterobacteria phage lambda complete genome [NC_001416.1](https://www.ncbi.nlm.nih.gov/nuccore/NC_001416.1), FASTA and GFF3.
- NCBI RefSeq transcripts NM_000546.6 (TP53), NM_007294.4 (BRCA1), NM_000492.4 (CFTR), NM_000518.5 (HBB), NM_000207.3 (INS), NM_004333.6 (BRAF), via [NCBI E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25501/).
- [NCBI Gene](https://www.ncbi.nlm.nih.gov/gene/) records 7157, 672, 1080, 3043, 3630, 673, 1956, 7124.
- samtools and bcftools manual pages, [htslib.org/doc](https://www.htslib.org/doc/).
- SeqKit usage documentation, [bioinf.shenwei.me/seqkit/usage](https://bioinf.shenwei.me/seqkit/usage/).

**Software and models**

- llama.cpp release [b11639](https://github.com/ggml-org/llama.cpp/releases/tag/b11639), ggml-org.
- Model files from Hugging Face: [unsloth/Qwen3.5-9B-GGUF](https://huggingface.co/unsloth/Qwen3.5-9B-GGUF), [unsloth/Qwen3.5-35B-A3B-GGUF](https://huggingface.co/unsloth/Qwen3.5-35B-A3B-GGUF), [unsloth/Qwen3.5-122B-A10B-GGUF](https://huggingface.co/unsloth/Qwen3.5-122B-A10B-GGUF), [unsloth/gemma-4-E4B-it-qat-GGUF](https://huggingface.co/unsloth/gemma-4-E4B-it-qat-GGUF), [ggml-org/gpt-oss-20b-GGUF](https://huggingface.co/ggml-org/gpt-oss-20b-GGUF), [ggml-org/embeddinggemma-300M-GGUF](https://huggingface.co/ggml-org/embeddinggemma-300M-GGUF).

**Literature** (cited from memory, not re-checked for this report)

- Chen, M. et al. (2021). Evaluating large language models trained on code (HumanEval). arXiv:2107.03374.
- Dettmers, T. et al. (2023). QLoRA: efficient finetuning of quantized LLMs. NeurIPS.
- Fedus, W., Zoph, B., Shazeer, N. (2022). Switch Transformers. JMLR.
- Frantar, E. et al. (2023). GPTQ: accurate post-training quantization for generative pre-trained transformers. ICLR.
- Hoffmann, J. et al. (2022). Training compute-optimal large language models (Chinchilla). NeurIPS.
- Jiang, A. Q. et al. (2024). Mixtral of experts. arXiv:2401.04088.
- Kaplan, J. et al. (2020). Scaling laws for neural language models. arXiv:2001.08361.
- Lewis, P. et al. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. NeurIPS.
- Shazeer, N. et al. (2017). Outrageously large neural networks: the sparsely-gated mixture-of-experts layer. ICLR.
- Wei, J. et al. (2022). Chain-of-thought prompting elicits reasoning in large language models. NeurIPS.
