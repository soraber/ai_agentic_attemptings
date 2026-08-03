#!/usr/bin/env python3
from __future__ import annotations

import argparse, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--summary", type=Path, default=ROOT/"output/project6_final_summary.json"); parser.add_argument("--output", type=Path, default=ROOT/"output/project6_report.pdf"); args = parser.parse_args()
    if not args.summary.exists(): raise SystemExit("Run P06-C08 before report generation.")
    summary = json.loads(args.summary.read_text())
    if summary.get("result_status") != "measured": raise SystemExit("Refusing placeholder results.")
    import matplotlib.pyplot as plt
    from PIL import Image as PILImage
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    assets = args.output.parent/"project6_report_assets"; assets.mkdir(parents=True, exist_ok=True)
    keys = ["verified_repair_rate_pct", "hidden_pass_rate_pct", "rollback_success_pct"]; labels = ["Verified repair", "Hidden tests", "Rollback"]
    x = range(3); fig, ax = plt.subplots(figsize=(10, 5.2)); ax.bar([i-.18 for i in x], [summary["one_shot"][k] for k in keys], .36, label="One-shot", color="#708c99"); ax.bar([i+.18 for i in x], [summary["repair_loop"][k] for k in keys], .36, label="Repair loop", color="#c84b31"); ax.set_xticks(list(x), labels); ax.set_ylim(0,105); ax.set_ylabel("Percent"); ax.legend(frameon=False); ax.set_title("Verified Repair and Recovery"); fig.tight_layout()
    chart=assets/"repair_quality.png"; fig.savefig(chart,dpi=180,facecolor="white",transparent=False); plt.close(fig)
    with PILImage.open(chart) as image: image.convert("RGB").save(chart)
    (assets/"procedure_diagram.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="210"><rect width="100%" height="100%" fill="white"/><text x="700" y="105" text-anchor="middle" font-family="Arial" font-size="26">Map -> Localize -> Patch policy -> Public tests -> Hidden tests -> Accept / Rollback</text></svg>\n',encoding="utf-8")
    styles=getSampleStyleSheet(); story=[Paragraph("Test-Driven Code-Repair Agent",styles["Title"]),Paragraph("Measured one-shot versus bounded repair-loop comparison",styles["Heading2"]),Spacer(1,10),Image(str(chart),width=7*inch,height=3.64*inch)]
    data=[["Metric","One-shot","Repair loop"]]+[[label,f"{summary['one_shot'][key]:.1f}%",f"{summary['repair_loop'][key]:.1f}%"] for label,key in zip(labels,keys)]; table=Table(data,colWidths=[3*inch,1.5*inch,1.5*inch]); table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#1f4e5f")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),.5,colors.grey),("PADDING",(0,0),(-1,-1),7)])); story.extend([Spacer(1,12),table,Spacer(1,14),Paragraph("Limits",styles["Heading2"]),Paragraph("QuixBugs is compact. Passing public and generated hidden tests does not prove correctness in large dependency-heavy repositories, and subprocess limits are not a hardened sandbox.",styles["BodyText"])])
    def page(canvas,doc): canvas.saveState(); canvas.setFillColor(colors.white); canvas.rect(0,0,letter[0],letter[1],fill=1,stroke=0); canvas.setFillColor(colors.HexColor("#526971")); canvas.setFont("Helvetica",8); canvas.drawString(45,18,"Project 6 - measured artifact report"); canvas.drawRightString(letter[0]-45,18,f"Page {doc.page}"); canvas.restoreState()
    SimpleDocTemplate(str(args.output),pagesize=letter,leftMargin=45,rightMargin=45,topMargin=42,bottomMargin=38).build(story,onFirstPage=page,onLaterPages=page); print(f"Wrote {args.output}")


if __name__ == "__main__": main()
