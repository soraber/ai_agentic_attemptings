#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", type=Path, default=ROOT / "output/project5_final_summary.json")
    parser.add_argument("--output", type=Path, default=ROOT / "output/project5_report.pdf")
    args = parser.parse_args()
    if not args.summary.exists():
        raise SystemExit("Run notebook cell P05-C08 before report generation.")
    summary = json.loads(args.summary.read_text(encoding="utf-8"))
    if summary.get("result_status") != "measured":
        raise SystemExit("Refusing to report placeholder results.")

    import matplotlib.pyplot as plt
    from PIL import Image as PILImage
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    assets = args.output.parent / "project5_report_assets"
    assets.mkdir(parents=True, exist_ok=True)
    metrics = ["result_hash_accuracy_pct", "unsafe_block_rate_pct", "repair_success_pct"]
    labels = ["Result accuracy", "Unsafe blocked", "Repair success"]
    x = range(3)
    fig, ax = plt.subplots(figsize=(10, 5.2))
    ax.bar([i - 0.18 for i in x], [summary["baseline"][key] for key in metrics], 0.36, label="One-shot", color="#708c99")
    ax.bar([i + 0.18 for i in x], [summary["governed"][key] for key in metrics], 0.36, label="Governed", color="#c84b31")
    ax.set_xticks(list(x), labels); ax.set_ylim(0, 105); ax.set_ylabel("Percent"); ax.legend(frameon=False); ax.set_title("Quality, Repair, and Governance")
    fig.tight_layout()
    chart = assets / "quality_repair_safety.png"
    fig.savefig(chart, dpi=180, facecolor="white", transparent=False); plt.close(fig)
    with PILImage.open(chart) as image:
        image.convert("RGB").save(chart)

    procedure = assets / "procedure_diagram.svg"
    procedure.write_text("""<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="220"><rect width="100%" height="100%" fill="white"/><g font-family="Arial" text-anchor="middle">""" + "".join(f'<rect x="{20+i*230}" y="60" width="190" height="90" fill="#f5f8f9" stroke="#1f4e5f"/><text x="{115+i*230}" y="112" font-size="18">{label}</text>' for i, label in enumerate(["Schema retrieval", "Typed plan", "SQLGlot policy", "Read-only query", "Repair", "Metrics"])) + "</g></svg>\n", encoding="utf-8")

    styles = getSampleStyleSheet()
    story = [Paragraph("Governed Text-to-SQL Analyst", styles["Title"]), Paragraph("Measured one-shot versus governed comparison", styles["Heading2"]), Spacer(1, 10), Image(str(chart), width=7 * inch, height=3.64 * inch)]
    data = [["Metric", "One-shot", "Governed"]] + [[label, f"{summary['baseline'][key]:.1f}%", f"{summary['governed'][key]:.1f}%"] for label, key in zip(labels, metrics)]
    table = Table(data, colWidths=[3.0 * inch, 1.5 * inch, 1.5 * inch])
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e5f")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, -1), 0.5, colors.grey), ("PADDING", (0, 0), (-1, -1), 7)]))
    story.extend([Spacer(1, 12), table, Spacer(1, 14), Paragraph("Interpretation", styles["Heading2"]), Paragraph("Result hashes measure semantic execution on a fixed synthetic snapshot. Safety results cover the included PII, region, ambiguity, and stored-instruction cases; they are not production certification.", styles["BodyText"])])

    def page(canvas, doc):
        canvas.saveState(); canvas.setFillColor(colors.white); canvas.rect(0, 0, letter[0], letter[1], fill=1, stroke=0); canvas.setFillColor(colors.HexColor("#526971")); canvas.setFont("Helvetica", 8); canvas.drawString(45, 18, "Project 5 - measured artifact report"); canvas.drawRightString(letter[0]-45, 18, f"Page {doc.page}"); canvas.restoreState()

    SimpleDocTemplate(str(args.output), pagesize=letter, leftMargin=45, rightMargin=45, topMargin=42, bottomMargin=38).build(story, onFirstPage=page, onLaterPages=page)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
