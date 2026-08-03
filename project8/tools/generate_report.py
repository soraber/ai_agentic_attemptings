#!/usr/bin/env python3
import argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--summary",type=Path,default=ROOT/"output/project8_final_summary.json"); parser.add_argument("--output",type=Path,default=ROOT/"output/project8_report.pdf"); args=parser.parse_args()
    if not args.summary.exists(): raise SystemExit("Run P08-C08 before report generation.")
    summary=json.loads(args.summary.read_text());
    if summary.get("result_status")!="measured": raise SystemExit("Refusing placeholder results.")
    import matplotlib.pyplot as plt
    from PIL import Image as PILImage
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Image,Paragraph,SimpleDocTemplate,Spacer,Table,TableStyle
    assets=args.output.parent/"project8_report_assets"; assets.mkdir(parents=True,exist_ok=True); systems=["window","episodic","hybrid"]; labels=["Recent window","Episodic","Hybrid"]
    fig,axes=plt.subplots(1,2,figsize=(11,4.8)); axes[0].bar(labels,[summary[s]["exact_match_pct"] for s in systems],color=["#708c99","#d49a3a","#c84b31"]); axes[0].set_ylim(0,105); axes[0].set_ylabel("Exact match (%)"); axes[0].set_title("Memory Quality"); axes[1].bar(labels,[summary[s]["mean_context_tokens"] for s in systems],color=["#708c99","#d49a3a","#c84b31"]); axes[1].set_ylabel("Mean context tokens"); axes[1].set_title("Context Cost"); fig.tight_layout(); chart=assets/"quality_context_tradeoff.png"; fig.savefig(chart,dpi=180,facecolor="white",transparent=False); plt.close(fig)
    with PILImage.open(chart) as image: image.convert("RGB").save(chart)
    (assets/"procedure_diagram.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="210"><rect width="100%" height="100%" fill="white"/><text x="700" y="105" text-anchor="middle" font-family="Arial" font-size="25">Sessions -> Working + Episodic + Semantic / Temporal Stores -> Hybrid Retrieval -> Cited Answer / Abstain -> Delete</text></svg>\n',encoding="utf-8")
    styles=getSampleStyleSheet(); story=[Paragraph("Long-Term Memory Agent",styles["Title"]),Paragraph("Measured recent-window, episodic, and hybrid comparison",styles["Heading2"]),Spacer(1,10),Image(str(chart),width=7*inch,height=3.05*inch)]; data=[["Metric",*labels],["Exact match",*[f"{summary[s]['exact_match_pct']:.1f}%" for s in systems]],["Evidence recall",*[f"{summary[s]['mean_evidence_recall']:.2f}" for s in systems]],["Context tokens",*[f"{summary[s]['mean_context_tokens']:.1f}" for s in systems]]]; table=Table(data,colWidths=[2.1*inch,1.35*inch,1.35*inch,1.35*inch]); table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#1f4e5f")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),.5,colors.grey),("PADDING",(0,0),(-1,-1),7)])); story.extend([Spacer(1,12),table,Spacer(1,14),Paragraph("Deletion compliance",styles["Heading2"]),Paragraph(f"Verified deletion across events, derived facts, retrieval, and tombstones: {summary['deletion_compliance_pct']:.1f}%.",styles["BodyText"]),Paragraph("Limits",styles["Heading2"]),Paragraph("Offline lexical retrieval and deterministic lifecycle fixtures validate mechanics but do not substitute for the planned LoCoMo model-backed QA run or provider-level deletion guarantees.",styles["BodyText"])])
    def page(canvas,doc): canvas.saveState(); canvas.setFillColor(colors.white); canvas.rect(0,0,letter[0],letter[1],fill=1,stroke=0); canvas.setFillColor(colors.HexColor("#526971")); canvas.setFont("Helvetica",8); canvas.drawString(45,18,"Project 8 - measured artifact report"); canvas.drawRightString(letter[0]-45,18,f"Page {doc.page}"); canvas.restoreState()
    SimpleDocTemplate(str(args.output),pagesize=letter,leftMargin=45,rightMargin=45,topMargin=42,bottomMargin=38).build(story,onFirstPage=page,onLaterPages=page); print(f"Wrote {args.output}")


if __name__=="__main__": main()
