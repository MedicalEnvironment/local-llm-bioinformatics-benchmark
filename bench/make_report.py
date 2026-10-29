"""Build the progress-report PDF from benchmark results."""
import json
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle)

F = "/usr/share/fonts/truetype/noto/"
pdfmetrics.registerFont(TTFont("Sans", F + "NotoSans-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Sans-Bold", F + "NotoSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Sans-Italic", F + "NotoSans-Italic.ttf"))
pdfmetrics.registerFont(TTFont("Mono", F + "NotoSansMono-Regular.ttf"))
pdfmetrics.registerFontFamily("Sans", normal="Sans", bold="Sans-Bold", italic="Sans-Italic", boldItalic="Sans-Bold")

INK, MUTED, RULE, ACCENT = colors.HexColor("#1f2933"), colors.HexColor("#5f6b7a"), colors.HexColor("#d9dee5"), colors.HexColor("#2457a6")
PASS, FAIL, WAIT = colors.HexColor("#1e7b46"), colors.HexColor("#b3261e"), colors.HexColor("#8a6d00")
TINT = colors.HexColor("#f3f6fa")

S = dict(
    title=ParagraphStyle("t", fontName="Sans-Bold", fontSize=20, leading=24, textColor=INK, spaceAfter=2),
    sub=ParagraphStyle("s", fontName="Sans", fontSize=10, leading=14, textColor=MUTED),
    h1=ParagraphStyle("h1", fontName="Sans-Bold", fontSize=13, leading=17, textColor=ACCENT, spaceBefore=11, spaceAfter=5),
    body=ParagraphStyle("b", fontName="Sans", fontSize=9.5, leading=13.5, textColor=INK, spaceAfter=5),
    bullet=ParagraphStyle("bl", fontName="Sans", fontSize=9.5, leading=13.5, textColor=INK, leftIndent=12, bulletIndent=2, spaceAfter=3),
    cell=ParagraphStyle("c", fontName="Sans", fontSize=8.5, leading=11, textColor=INK),
    cellb=ParagraphStyle("cb", fontName="Sans-Bold", fontSize=8.5, leading=11, textColor=INK),
    small=ParagraphStyle("sm", fontName="Sans", fontSize=8, leading=11, textColor=MUTED),
    callout=ParagraphStyle("co", fontName="Sans", fontSize=10, leading=14.5, textColor=INK),
)
P = lambda t, s="body": Paragraph(t, S[s])
B = lambda t: Paragraph(t, S["bullet"], bulletText="•")
C = lambda t, s="cell": Paragraph(t, S[s])


def table(rows, widths, header=True, zebra=True):
    t = Table(rows, colWidths=widths, repeatRows=1 if header else 0)
    st = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
          ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5), ("LINEBELOW", (0, 0), (-1, -1), 0.4, RULE)]
    if header:
        st += [("BACKGROUND", (0, 0), (-1, 0), TINT), ("LINEBELOW", (0, 0), (-1, 0), 0.8, MUTED)]
    if zebra:
        st += [("BACKGROUND", (0, i), (-1, i), colors.HexColor("#fafbfc")) for i in range(2, len(rows), 2)]
    t.setStyle(TableStyle(st))
    return t


def callout(flow):
    t = Table([[flow]], colWidths=[170 * mm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), TINT), ("LINEBEFORE", (0, 0), (0, -1), 3, ACCENT),
                           ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                           ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    return t


def tag(ok):
    return '<font color="#1e7b46"><b>Pass</b></font>' if ok else '<font color="#b3261e"><b>Fail</b></font>'


res = json.load(open(Path(__file__).parent / "results/qwen3.5-9b.json"))["items"]
def cnt(p):
    v = [r["ok"] for k, r in res.items() if k.startswith(p)]
    return sum(v), len(v)
SP, SN = cnt("script:"); RP, RN = cnt("reason:"); NDONE = len(res)
LABEL = {
    "script:gc_content": ("GC content per gene (6 human CDS)", "Values correct; off-by-one dropped first letter of every gene name"),
    "script:translate": ("Translate CDS, report protein length", "All 6 lengths match canonical proteins"),
    "script:longest_orf": ("Longest ORF, 6 frames (lambda genome)", "Exact: gene J, 15505–18903 (+)"),
    "script:gff_summary": ("GFF3 feature counts + total CDS bp", "Exact"),
    "script:vcf_filter": ("VCF filter (PASS, QUAL, DP) + Ts/Tv", "Required at least 9 columns and read QUAL from wrong column; printed kept=0 (true: 207)"),
    "script:fastq_qc": ("FASTQ per-read mean quality, Q20 pass", "Exact"),
    "script:kmer": ("Most frequent 8-mer (lambda genome)", "Exact"),
    "reason:punnett": ("Dihybrid cross probability", ""),
    "reason:dilution": ("Serial dilution to colony count", ""),
    "reason:wallace": ("Primer Tm (Wallace rule)", ""),
    "reason:hardy_weinberg": ("Hardy–Weinberg carrier frequency", ""),
    "reason:pmol": ("Plasmid mass (µg) to pmol", ""),
    "reason:coverage": ("Sequencing depth to read pairs needed", ""),
    "reason:mrna": ("mRNA to peptide length", ""),
    "reason:ddct": ("qPCR fold change (ddCt)", ""),
    "reason:bayes": ("Screening test PPV (Bayes)", ""),
    "reason:ecori": ("Expected EcoRI sites", ""),
}

story = []
story += [P("Local LLM Pilot — Progress Update", "title"),
          P("Feasibility of running a local language model for bioinformatics scripting, reasoning and information retrieval<br/>"
            "15 October 2026 &nbsp;·&nbsp; " + f"<b>Status: preliminary — 1 of 4 models partly evaluated ({NDONE} of 53 items); full run in progress</b>", "sub"),
          Spacer(1, 10)]

story.append(callout(P(
    "<b>Bottom line.</b> Setup is done and feasibility is confirmed: a 9-billion-parameter model (Qwen3.5-9B) runs fully "
    "offline on the existing laptop at about 35–40 tokens/s, with no data leaving the machine. Early quality is promising "
    f"({SP} of {SN} scripting tasks, {RP} of {RN} reasoning problems), but both scripting failures were <b>silent</b> — plausible output, "
    "no error — so generated code must be checked. Information retrieval, the other three models and any comparison with a "
    "commercial model are still pending.", "callout")))

story.append(P("1. What has been set up", "h1"))
story.append(table([
    [C("Component", "cellb"), C("Detail", "cellb")],
    [C("Hardware"), C("Laptop: NVIDIA RTX 4060 Laptop GPU (8 GB VRAM), AMD Ryzen 7 7435HS (8 cores), 15 GB RAM, Ubuntu 26.04")],
    [C("Inference engine"), C("llama.cpp build b11639, official CUDA 12.8 release (open source, MIT licence). Checksums verified; no admin rights or system changes needed")],
    [C("Models downloaded"), C("Qwen3.5-9B (verified, tested) · Gemma-4-E4B and Gemma-4-12B (verified, not yet tested) · gpt-oss-20b (verified, not yet tested) · EmbeddingGemma-300M for document search")],
    [C("Privacy"), C("Verified: the server listens only on 127.0.0.1 (this machine) and makes no outbound connections. Internet was used only for the one-time downloads")],
    [C("Access"), C("Browser chat UI at http://127.0.0.1:9931/ and an OpenAI-compatible API on the same port, so existing scripts and tools can use it")],
], [38 * mm, 132 * mm]))

story.append(P("2. How quality is measured", "h1"))
story.append(P(
    "53 test items per model, scored automatically against answers computed independently (cross-checked with Biopython and known "
    "biology, e.g. canonical protein lengths). Test data is real where possible: the phage lambda genome and annotation and six human "
    "coding sequences (TP53, BRCA1, CFTR, HBB, INS, BRAF) from NCBI, plus a synthetic VCF (400 variants) and FASTQ (500 reads) with "
    "known answers."))
story.append(table([
    [C("Area", "cellb"), C("Items", "cellb"), C("How it is scored", "cellb")],
    [C("Scripting"), C("7"), C("Model writes a Python script; it is executed on the data and its output must match exactly")],
    [C("Reasoning"), C("10"), C("Quantitative lab/genetics problems with a single numeric answer (±1%)")],
    [C("Retrieval"), C("18 × 2"), C("Tool options (samtools, bcftools, seqkit) and gene locations, asked without context and again with "
                                     "retrieved passages from the manuals and NCBI summaries (RAG)")],
], [28 * mm, 18 * mm, 124 * mm]))

story.append(P(f"3. Preliminary results — Qwen3.5-9B ({NDONE} of 53 items)", "h1"))
rows = [[C("Task", "cellb"), C("Result", "cellb"), C("Time", "cellb"), C("Note", "cellb")]]
for k, (lab, note) in LABEL.items():
    if k not in res:
        continue
    r = res[k]
    rows.append([C(lab), C(tag(r["ok"])), C(f"{r['wall']:.0f} s"), C(note)])
story.append(table(rows, [58 * mm, 14 * mm, 14 * mm, 84 * mm]))
story.append(Spacer(1, 6))
wall = [res[k]["wall"] for k in LABEL if k in res]
tps = [res[k]["tg_tps"] for k in LABEL if k in res]
story.append(table([
    [C("Summary", "cellb"), C("Value", "cellb")],
    [C("Scripting"), C(f"<b>{SP} / {SN}</b> passed")],
    [C("Reasoning"), C(f"<b>{RP} / {RN}</b> passed" + (f" ({10 - RN} remaining items not yet run)" if RN < 10 else ""))],
    [C("Retrieval (closed-book vs RAG)"), C("Not yet run")],
    [C("Generation speed"), C(f"{min(tps):.0f}–{max(tps):.0f} tokens/s, fully on GPU (~6 GB of 8 GB VRAM)")],
    [C("Time per answer"), C(f"{min(wall):.0f}–{max(wall):.0f} s with thinking enabled (median {sorted(wall)[len(wall)//2]:.0f} s)")],
], [58 * mm, 112 * mm], zebra=False))

story.append(KeepTogether([P("4. Findings and risks", "h1"),
    B("<b>Silent errors are the main risk.</b> Both failed scripts ran without errors and printed plausible output. One computed every "
      "GC value correctly but truncated each gene name (“P53”, “RCA1”); the other read the wrong VCF column and reported zero variants "
      "kept instead of 207. Generated code needs review or a quick test against known data before use."),
    B("<b>Overthinking slows simple tasks.</b> With its reasoning step on, the model spent up to ~6,700 tokens (about 3 minutes) on "
      "tasks a person would solve in seconds. Turning reasoning off or capping it should make answers near-instant; the effect on "
      "accuracy has not yet been measured."),
    B("<b>The hardware is adequate, but 8 GB of VRAM is the ceiling.</b> The 9B model runs fully on the GPU; a 12B model is expected to just fit (not yet tested). Larger models "
      "need partial CPU offload and will be slower."),
    B("<b>Small sample.</b> Each item was run once; with this few items, a single pass or fail changes a score noticeably."),
]))

story.append(KeepTogether([P("5. Remaining work", "h1"),
    table([
        [C("Step", "cellb"), C("Effort", "cellb"), C("Why it matters", "cellb")],
        [C(f"Finish Qwen3.5-9B ({53 - NDONE} items incl. retrieval)"), C("~45–60 min machine time (running now)"), C("Retrieval is one of the three goals; closed-book vs RAG is the key comparison")],
        [C("Run Gemma-4-E4B, Gemma-4-12B, gpt-oss-20b"), C("~45–60 min each (queued; all downloads done)"), C("Identify the best model for this hardware")],
        [C("Measure reasoning on vs off"), C("~20 min"), C("Quantify the speed/accuracy trade-off for everyday use")],
        [C("Repeat runs (3×)"), C("Machine time only"), C("Reduce noise from single runs")],
        [C("Optional: same tests on a commercial model"), C("API key; under $1"), C("Shows the gap to cloud models; sends only public/synthetic test data")],
    ], [56 * mm, 50 * mm, 64 * mm]),
]))
story.append(Spacer(1, 4))
story.append(P("Test harness, data, per-item model responses and generated scripts are kept in ~/llm/bench on the test machine.", "small"))


def footer(c, d):
    c.saveState(); c.setFont("Sans", 7.5); c.setFillColor(MUTED)
    c.drawString(20 * mm, 12 * mm, "Local LLM pilot · progress update · preliminary")
    c.drawRightString(190 * mm, 12 * mm, f"Page {d.page}"); c.restoreState()


out = Path.home() / "llm/reports/local-llm-progress-2026-10-15.pdf"
out.parent.mkdir(exist_ok=True)
SimpleDocTemplate(str(out), pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=16 * mm, bottomMargin=18 * mm,
                  title="Local LLM Pilot — Progress Update", subject="Local LLM feasibility for bioinformatics").build(
    story, onFirstPage=footer, onLaterPages=footer)
print(out)
