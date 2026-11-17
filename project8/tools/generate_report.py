#!/usr/bin/env python3
"""Render measured results without assuming which memory strategy wins."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEMS = ["window", "episodic", "hybrid"]
LABELS = ["Recent window", "Episodic", "Hybrid"]


def report_values(summary):
    if summary.get("result_status") != "measured":
        raise ValueError("Refusing placeholder results")
    scores = [100 * summary[s]["mean_token_f1"] for s in SYSTEMS]
    # Historical "tokens" were whitespace-word counts, not tokenizer measurements.
    words = [summary[s].get("mean_context_words", summary[s].get("mean_context_tokens")) for s in SYSTEMS]
    if any(value is None for value in words):
        raise ValueError("Context word measurements are missing")
    best = [label for label, score in zip(LABELS, scores) if score == max(scores)]
    interpretation = f"Highest observed token F1: {', '.join(best)} ({max(scores):.1f}%). This is a descriptive ranking, not a significance claim."
    if "model_calls" in summary:
        interpretation += f" This evaluation recorded {summary['model_calls']} model calls; estimated API cost was ${summary.get('estimated_cost_usd', 0):.3f}. Local GPU usage is not free merely because API cost is zero."
    else:
        interpretation += " This is a deterministic lifecycle fixture, not a natural-language model benchmark."
    return scores, words, interpretation


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", type=Path, default=ROOT / "output/project8_final_summary.json")
    parser.add_argument("--output", type=Path, default=ROOT / "output/project8_report.pdf")
    args = parser.parse_args()
    summary = json.loads(args.summary.read_text())
    scores, words, interpretation = report_values(summary)
    import matplotlib.pyplot as plt
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    assets = args.output.parent / "project8_report_assets"
    assets.mkdir(parents=True, exist_ok=True)
    chart = assets / "quality_context_tradeoff.png"
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    palette = ["#527c89", "#bb8b23", "#a84454"]
    axes[0].bar(LABELS, scores, color=palette)
    axes[0].set(ylabel="Token F1 (%)", ylim=(0, 100), title="Answer Overlap")
    axes[1].bar(LABELS, words, color=palette)
    axes[1].set(ylabel="Mean context words", title="Context Size")
    fig.tight_layout()
    fig.savefig(chart, dpi=180, facecolor="white")
    plt.close(fig)
    styles = getSampleStyleSheet()
    data = [["Metric", *LABELS], ["Exact match (%)", *[f"{summary[s]['exact_match_pct']:.1f}" for s in SYSTEMS]],
            ["Token F1 (%)", *[f"{value:.1f}" for value in scores]],
            ["Context words", *[f"{value:.1f}" for value in words]]]
    table = Table(data, colWidths=[145, 120, 120, 120])
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e6edef")),
                               ("GRID", (0, 0), (-1, -1), .4, colors.grey),
                               ("PADDING", (0, 0), (-1, -1), 6)]))
    deletion = summary.get("deletion_compliance_pct")
    deletion_text = (f"Deletion fixture checks passed for {deletion:.1f}% of requested cases."
                     if deletion is not None else "No lifecycle deletion measurement was supplied.")
    story = [Paragraph("Long-Term Memory Agent", styles["Title"]),
             Paragraph(f"Evaluation: {summary.get('evaluation_mode', 'deterministic lifecycle fixtures')}", styles["BodyText"]),
             Spacer(1, 12), Image(str(chart), width=505, height=207), table,
             Paragraph("Interpretation", styles["Heading2"]), Paragraph(interpretation, styles["BodyText"]),
             Paragraph("Deletion And Limits", styles["Heading2"]),
             Paragraph(deletion_text + " Retrieved evidence and cited evidence are separate metrics; valid citation IDs do not establish claim support. Compact subsets, answer-overlap metrics, and authored lifecycle cases limit generalization. These checks do not verify provider retention or backup deletion.", styles["BodyText"])]
    SimpleDocTemplate(str(args.output), pagesize=letter, leftMargin=45, rightMargin=45,
                      topMargin=40, bottomMargin=40).build(story)
    print(f"Wrote {args.output.name}")


if __name__ == "__main__":
    main()
