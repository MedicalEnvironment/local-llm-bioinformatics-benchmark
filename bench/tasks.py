"""Benchmark task definitions: prompts + scorers."""
import re

FMT = ("Reply with a single complete Python 3 script in one ```python code block. "
       "Only the standard library plus biopython, numpy and pandas are available. "
       "The script must print exactly the requested output to stdout and nothing else.")

SCRIPT_TASKS = [
    dict(id="gc_content", files=["cds.fa"], prompt=
         "Write a script that takes a multi-record nucleotide FASTA path as sys.argv[1]. Each header contains a tag like "
         "[gene=TP53]. For each record, in file order, print `GENE<TAB>GC` where GC is the percentage of G+C bases over "
         "the full sequence length (case-insensitive), rounded to 2 decimals."),
    dict(id="translate", files=["cds.fa"], prompt=
         "Write a script that takes a FASTA of coding sequences (CDS) as sys.argv[1]. Each header contains a tag like "
         "[gene=TP53]. Translate each CDS from its first base with the standard genetic code, stopping at the first stop "
         "codon. For each record, in file order, print `GENE<TAB>LENGTH` where LENGTH is the protein length in amino acids, "
         "excluding the stop."),
    dict(id="longest_orf", files=["lambda.fa"], prompt=
         "Write a script that takes a single-record genome FASTA as sys.argv[1]. Find the longest open reading frame on "
         "either strand (all 6 frames): it begins with ATG and ends at the first in-frame stop codon (TAA, TAG, TGA), and "
         "it must include that stop codon. Print one line `START END STRAND LENGTH`: START < END are 1-based inclusive "
         "coordinates on the forward strand, STRAND is + or -, LENGTH is in nucleotides including the stop codon."),
    dict(id="gff_summary", files=["lambda.gff3"], prompt=
         "Write a script that takes a GFF3 file as sys.argv[1]. Ignore lines starting with '#' and blank lines. Count "
         "features by type (column 3) and print `TYPE<TAB>COUNT` lines sorted alphabetically by type. Then print a final "
         "line `total_cds_bp<TAB>N` where N is the sum of (end - start + 1) over every CDS line."),
    dict(id="vcf_filter", files=["calls.vcf"], prompt=
         "Write a script that takes an uncompressed VCF as sys.argv[1]. Keep records where FILTER is PASS, QUAL >= 30 and "
         "the INFO field DP >= 10. Among kept records, an SNV has REF and ALT both of length 1; everything else is an "
         "indel. Compute the transition/transversion ratio over kept SNVs (transitions are A<->G and C<->T). Print exactly "
         "one line: `kept=N snv=N indel=N titv=X` with titv rounded to 3 decimals."),
    dict(id="fastq_qc", files=["reads.fastq"], prompt=
         "Write a script that takes a 4-line-per-record FASTQ (Phred+33) as sys.argv[1]. For each read compute its mean "
         "base quality. Print exactly one line: `reads=N pass_q20=N mean_q=X` where pass_q20 counts reads whose mean "
         "quality is >= 20 and mean_q is the mean of the per-read means, rounded to 2 decimals."),
    dict(id="kmer", files=["lambda.fa"], prompt=
         "Write a script that takes a single-record genome FASTA as sys.argv[1]. Count all overlapping 8-mers on the "
         "forward strand only (uppercase sequence). Print the most frequent 8-mer and its count as `KMER COUNT`."),
]


def score_script(tid, out, T):
    t = T[tid]
    lines = [l.strip() for l in out.strip().splitlines() if l.strip()]
    try:
        if tid == "gc_content":
            got = {a: float(b) for a, b in (l.split("\t") for l in lines)}
            return got.keys() == t.keys() and all(abs(got[k] - t[k]) <= 0.011 for k in t)
        if tid == "translate":
            got = {a: int(b) for a, b in (l.split("\t") for l in lines)}
            return got == t
        if tid == "longest_orf":
            s, e, sd, L = lines[0].split()
            return (int(s), int(e), sd, int(L)) == (t["start"], t["end"], t["strand"], t["length"])
        if tid == "gff_summary":
            got = dict(l.split("\t") for l in lines)
            tot = int(got.pop("total_cds_bp"))
            return {k: int(v) for k, v in got.items()} == t["counts"] and tot == t["total_cds_bp"]
        if tid == "vcf_filter":
            d = dict(kv.split("=") for kv in lines[0].split())
            return (int(d["kept"]), int(d["snv"]), int(d["indel"])) == (t["kept"], t["snv"], t["indel"]) and abs(float(d["titv"]) - t["titv"]) < 0.0011
        if tid == "fastq_qc":
            d = dict(kv.split("=") for kv in lines[0].split())
            return int(d["reads"]) == t["reads"] and int(d["pass_q20"]) == t["pass_q20"] and abs(float(d["mean_q"]) - t["overall_mean_q"]) < 0.011
        if tid == "kmer":
            k, c = lines[0].split()
            return k in t["ties"] and int(c) == t["count"]
    except Exception:
        return False
    return False


# primer for Wallace rule
_PRIMER = "AGCGTACCTGAATCGGTA"
_WALLACE = 2 * sum(_PRIMER.count(b) for b in "AT") + 4 * sum(_PRIMER.count(b) for b in "GC")

REASON_TASKS = [
    ("punnett", "Two genes assort independently. A cross is made between AaBb and Aabb parents. What is the probability that an offspring has genotype aabb?", 0.125),
    ("dilution", "A culture has 2e8 cells/mL. You make four sequential 1:10 dilutions, then plate 100 uL of the final dilution. Assuming every cell forms a colony, how many colonies do you expect?", 2000),
    ("wallace", f"Using the Wallace rule Tm = 2(A+T) + 4(G+C), what is the Tm in degrees C of the primer 5'-{_PRIMER}-3'?", _WALLACE),
    ("hardy_weinberg", "An autosomal recessive disease affects 1 in 2500 newborns in a population in Hardy-Weinberg equilibrium. What fraction of the population are heterozygous carriers? Give the exact decimal.", 0.0392),
    ("pmol", "How many picomoles of plasmid are in 5 ug of a 3000 bp double-stranded plasmid, assuming an average mass of 650 g/mol per base pair?", 2.564),
    ("coverage", "You want 30x mean coverage of a 3.1 Gb genome using 2x150 bp paired-end reads. How many million read pairs do you need? Give the number in millions.", 310),
    ("mrna", "An mRNA reads 5'-GGCAUGGCUUCAGGAUGCUAAGCAUGA-3'. Translation starts at the first AUG. How many amino acids long is the resulting peptide?", 5),
    ("ddct", "qPCR results: control sample target Ct 25.0, reference Ct 18.0; treated sample target Ct 23.0, reference Ct 18.5. Using the 2^-ddCt method with 100% efficiency, what is the fold change of the target in treated vs control?", 5.657),
    ("bayes", "A screening test has 99% sensitivity and 95% specificity. Disease prevalence is 1%. What is the probability that a person who tests positive actually has the disease? Give a decimal.", 0.1667),
    ("ecori", "Assume a random genome with equal base frequencies. How many EcoRI sites (GAATTC) do you expect in a 48,502 bp linear double-stranded genome? Note GAATTC is palindromic. Give the number to 2 decimals.", 11.84),
]
REASON_SUFFIX = "\n\nThink it through, then end your reply with one final line of the form `ANSWER: <number>` (a plain decimal number, no units)."


def score_reason(text, want):
    m = re.findall(r"ANSWER:\s*\**\s*([-+0-9.eE/,]+)", text)
    if not m:
        return False
    s = m[-1].replace(",", "").rstrip(".")
    try:
        v = eval(s, {"__builtins__": {}}) if "/" in s else float(s)
    except Exception:
        return False
    return abs(v - want) <= 0.01 * abs(want) + 1e-9


RETR_TASKS = [
    ("sam_mapq", "In `samtools view`, which option skips alignments with MAPQ below a given value?", r"(^|[\s`])-q\b|--min-MQ"),
    ("sam_reqflag", "In `samtools view`, which option outputs only alignments that have all bits of a given FLAG set?", r"(^|[\s`])-f\b|--require-flags"),
    ("sam_threads", "In `samtools sort`, which option sets the number of additional threads?", r"-@|--threads"),
    ("sam_byname", "In `samtools sort`, which option sorts by read name instead of coordinate?", r"(^|[\s`])-[nN]\b"),  # -N (lexicographic) is also documented
    ("markdup_rm", "In `samtools markdup`, which option removes duplicate reads instead of just marking them?", r"(^|[\s`])-r\b|--remove"),
    ("depth_all", "In `samtools depth`, which option outputs all positions, including those with zero depth?", r"(^|[\s`])-aa?\b"),
    ("bcf_snps", "With `bcftools view`, which option and value select only SNPs?", r"-v\s*snps|--types[ =]snps"),
    ("bcf_norm", "Which bcftools subcommand left-aligns and normalizes indels?", r"\bnorm\b"),
    ("seqkit_rmdup", "In `seqkit rmdup`, which option removes duplicates by sequence content rather than by ID?", r"(^|[\s`])-s\b|--by-seq"),
    ("seqkit_stats", "Which seqkit subcommand prints simple statistics (number of sequences, lengths, etc.) of FASTA/Q files?", r"\bstats\b"),
    ("loc_TP53", "What is the cytogenetic location of the human TP53 gene?", r"17p13\.1"),
    ("loc_BRCA1", "What is the cytogenetic location of the human BRCA1 gene (band and sub-band)?", r"17q21\.31"),
    ("loc_CFTR", "What is the cytogenetic location of the human CFTR gene?", r"7q31\.2"),
    ("loc_HBB", "What is the cytogenetic location of the human HBB gene?", r"11p15\.4"),
    ("loc_INS", "What is the cytogenetic location of the human INS (insulin) gene?", r"11p15\.5"),
    ("loc_BRAF", "What is the cytogenetic location of the human BRAF gene?", r"7q34"),
    ("loc_EGFR", "What is the cytogenetic location of the human EGFR gene?", r"7p11\.2"),
    ("loc_TNF", "What is the cytogenetic location of the human TNF gene (band and sub-band)?", r"6p21\.33"),
]
RETR_SUFFIX = "\n\nAnswer concisely. End with one final line of the form `ANSWER: <answer>`."


def score_retr(text, pat):
    m = re.findall(r"ANSWER:\s*(.+)", text)
    return bool(m) and re.search(pat, m[-1]) is not None
