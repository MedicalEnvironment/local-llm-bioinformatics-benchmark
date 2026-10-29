# Worked examples: what the models actually wrote

Real answers copied verbatim from `bench/results/` by `bench/make_results_md.py` (long scripts are shortened). They show the three outcomes that matter in practice: correct, silently wrong, and crashed.

## 1. Correct: VCF filtering (Qwen3.5-122B-A10B, HPC)

Task: keep PASS records with QUAL ≥ 30 and DP ≥ 10, count SNVs and indels, compute Ts/Tv. The input `calls.vcf` deliberately has only 8 columns.

```python
#!/usr/bin/env python3
import sys

def main():
    if len(sys.argv) != 2:
        return
    
    vcf_file = sys.argv[1]
    
    kept = 0
    snv = 0
    indel = 0
    transitions = 0
    transversions = 0
    
    with open(vcf_file, 'r') as f:
        for line in f:
            if line.startswith('#'):
                continue
            
            parts = line.strip().split('\t')
            if len(parts) < 8:
                continue
            
            ref = parts[3]
            qual = parts[5]
            filter_field = parts[6]
            info = parts[7]
            
            # Check FILTER is PASS
            if filter_field != 'PASS':
                continue
            
            # Check QUAL >= 30
            try:
                qual_val = float(qual)
                if qual_val < 30:
                    continue
            except ValueError:
                continue
# ... 57 more lines
```

Output when run on `calls.vcf`:

```
kept=207 snv=151 indel=56 titv=0.525
```

Correct answer: `kept=207 snv=151 indel=56 titv=0.525` → **pass**.

## 2. Silently wrong: the same task (Qwen3.5-9B, laptop)

This script ran without any error, so a user would likely trust it. It skips every line with fewer than 9 columns (this VCF validly has 8, as it has no sample columns) and also reads QUAL from column 8 (INFO) instead of column 6, so nothing is kept.

```python
#!/usr/bin/env python3
import sys
import re

def parse_vcf_line(line):
    """Parse a VCF record line."""
    if line.startswith('#'):
        return None
    
    parts = line.split('\t')
    if len(parts) < 9:
        return None
    
    chrom = parts[0]
    pos = parts[1]
    ref = parts[3]
    alt = parts[4]
    filter_val = parts[6]
    qual = float(parts[7])
    info = parts[8]
    
    # Parse INFO field for DP
    dp = None
    if info:
        dp_match = re.search(r'DP=(\d+)', info)
        if dp_match:
            dp = int(dp_match.group(1))
    
    return {
        'chrom': chrom,
# ... 71 more lines
```

Output:

```
kept=0 snv=0 indel=0 titv=0.000
```

Correct answer: `kept=207 ...` → **fail**. Nothing in the output signals a problem; only checking against a known answer catches it.

## 3. Silently wrong in a subtler way: GC content (Qwen3.5-9B, laptop)

Every GC percentage is correct, but an off-by-one slice drops the first letter of each gene name.

Output (first lines):

```
P53	56.85
RCA1	41.22
FTR	41.53
BB	56.08
NS	64.56
RAF	46.15
```

Expected: `TP53 56.85`, `BRCA1 41.22`, ... → **fail**.

## 4. Crashed: an invented library function (Qwen3.5-9B, HPC)

The model called `pandas.read_vcf`, which does not exist. A crash is the easy failure: it is obvious.

Error output:

```
Traceback (most recent call last):
  File "/tmp/tmp32dvg7l9/s.py", line 5, in <module>
    vcf = pd.read_vcf(vcf_file)
          ^^^^^^^^^^^
AttributeError: module 'pandas' has no attribute 'read_vcf'. Did you mean: 'read_fwf'?
```

## 5. Documentation fixes recall: the same question with and without RAG (Gemma-4-E4B, laptop)

Question: *In `seqkit rmdup`, which option removes duplicates by sequence content rather than by ID?* Correct: `-s` / `--by-seq`.

- From memory (closed-book): `ANSWER: default behavior` → **fail**
- With the seqkit manual excerpt pasted in (RAG): `ANSWER: -s or --by-seq` → **pass**

## 6. A scoring artefact: right answer, wrong format (gpt-oss-20b, Azure)

The scorer only reads a final line that starts with exactly `ANSWER:`. This answer is correct (CFTR is at 7q31.2) but wrote `Answer:`, so it was scored as wrong. It is the only such case found when every failure was checked by hand.

```
Answer: 7q31.2
```

