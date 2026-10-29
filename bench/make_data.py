"""Generate synthetic VCF/FASTQ and compute ground-truth answers for every scripting task."""
import json, random, re, collections
from pathlib import Path
from Bio import SeqIO
from Bio.Seq import Seq

D = Path(__file__).parent / "data"
R = D / "raw"
random.seed(42)

# ---- synthetic VCF on lambda coordinates ----
lam = str(next(SeqIO.parse(R / "lambda.fa", "fasta")).seq)
rows = []
for pos in sorted(random.sample(range(100, len(lam) - 100), 400)):
    ref = lam[pos - 1]
    kind = random.random()
    if kind < 0.75:
        alt = random.choice([b for b in "ACGT" if b != ref])
    elif kind < 0.88:
        ins = "".join(random.choice("ACGT") for _ in range(random.randint(1, 5)))
        alt = ref + ins
    else:
        n = random.randint(1, 5)
        ref = lam[pos - 1 : pos + n]
        alt = ref[0]
    qual = round(random.uniform(3, 99), 1)
    dp = random.randint(2, 80)
    filt = random.choices(["PASS", "LowQual", "StrandBias"], [0.8, 0.12, 0.08])[0]
    rows.append(("NC_001416.1", pos, ".", ref, alt, qual, filt, dp))
with open(R / "calls.vcf", "w") as f:
    f.write("##fileformat=VCFv4.2\n##contig=<ID=NC_001416.1,length=%d>\n" % len(lam))
    f.write('##INFO=<ID=DP,Number=1,Type=Integer,Description="Total depth">\n')
    f.write('##FILTER=<ID=LowQual,Description="Low quality">\n##FILTER=<ID=StrandBias,Description="Strand bias">\n')
    f.write("#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n")
    for c, p, i, r, a, q, fl, dp in rows:
        f.write(f"{c}\t{p}\t{i}\t{r}\t{a}\t{q}\t{fl}\tDP={dp}\n")

# ---- synthetic FASTQ ----
with open(R / "reads.fastq", "w") as f:
    for i in range(500):
        s = random.randint(0, len(lam) - 151)
        seq = lam[s : s + 150]
        base_q = random.choice([12, 18, 25, 32, 36])
        quals = [max(2, min(41, int(random.gauss(base_q, 6)))) for _ in seq]
        f.write(f"@read{i}\n{seq}\n+\n{''.join(chr(q + 33) for q in quals)}\n")

# ---- ground truth ----
T = {}
cds = list(SeqIO.parse(R / "cds.fa", "fasta"))
gene = lambda rec: re.search(r"\[gene=([^\]]+)\]", rec.description).group(1)

T["gc_content"] = {gene(r): round(100 * (r.seq.upper().count("G") + r.seq.upper().count("C")) / len(r.seq), 2) for r in cds}
T["translate"] = {gene(r): len(r.seq.translate(to_stop=True)) for r in cds}

def orfs(s):
    best = (0, 0, 0, "+")
    for strand, seq in (("+", s), ("-", str(Seq(s).reverse_complement()))):
        n = len(seq)
        for frame in range(3):
            i = frame
            while i + 3 <= n:
                if seq[i : i + 3] == "ATG":
                    j = i
                    while j + 3 <= n and seq[j : j + 3] not in ("TAA", "TAG", "TGA"):
                        j += 3
                    if j + 3 <= n:  # complete ORF incl. stop
                        L = j + 3 - i
                        if L > best[0]:
                            if strand == "+":
                                best = (L, i + 1, j + 3, "+")
                            else:
                                best = (L, n - (j + 3) + 1, n - i, "-")
                    i = j + 3
                else:
                    i += 3
    return best
L, st, en, sd = orfs(lam)
T["longest_orf"] = {"start": st, "end": en, "strand": sd, "length": L}

types = collections.Counter(); cds_len = 0
for line in open(R / "lambda.gff3"):
    if line.startswith("#") or not line.strip():
        continue
    p = line.rstrip("\n").split("\t")
    if len(p) < 9:
        continue
    types[p[2]] += 1
    if p[2] == "CDS":
        cds_len += int(p[4]) - int(p[3]) + 1
T["gff_summary"] = {"counts": dict(types), "total_cds_bp": cds_len}

ts = {("A", "G"), ("G", "A"), ("C", "T"), ("T", "C")}
keep = [r for r in rows if r[6] == "PASS" and r[5] >= 30 and r[7] >= 10]
snv = [r for r in keep if len(r[3]) == 1 and len(r[4]) == 1]
nts = sum((r[3], r[4]) in ts for r in snv)
T["vcf_filter"] = {"kept": len(keep), "snv": len(snv), "indel": len(keep) - len(snv), "titv": round(nts / (len(snv) - nts), 3)}

means = []
for rec in SeqIO.parse(R / "reads.fastq", "fastq"):
    q = rec.letter_annotations["phred_quality"]
    means.append(sum(q) / len(q))
T["fastq_qc"] = {"reads": len(means), "pass_q20": sum(m >= 20 for m in means), "overall_mean_q": round(sum(means) / len(means), 2)}

k = collections.Counter(lam[i : i + 8] for i in range(len(lam) - 7))
top = k.most_common(1)[0]
T["kmer"] = {"kmer": top[0], "count": top[1], "ties": sorted(x for x, c in k.items() if c == top[1])}

json.dump(T, open(D / "truth.json", "w"), indent=1)
print(json.dumps(T, indent=1)[:2500])
