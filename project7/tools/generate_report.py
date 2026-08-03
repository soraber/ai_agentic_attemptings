#!/usr/bin/env python3
import argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--summary",type=Path,default=ROOT/"output/project7_final_summary.json"); parser.add_argument("--output",type=Path,default=ROOT/"output/project7_report.pdf"); args=parser.parse_args()
    if not args.summary.exists(): raise SystemExit("Run P07-C08 before report generation.")
    summary=json.loads(args.summary.read_text())
    if summary.get("result_status")!="measured": raise SystemExit("Refusing placeholder results.")
    import matplotlib.pyplot as plt
    from PIL import Image as PILImage
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Image,Paragraph,SimpleDocTemplate,Spacer,Table,TableStyle
    assets=args.output.parent/"project7_report_assets"; assets.mkdir(parents=True,exist_ok=True); keys=["benign_success_pct","attack_success_pct","trace_complete_pct"]; labels=["Benign success","Attack success","Trace complete"]; x=range(3)
    fig,ax=plt.subplots(figsize=(10,5.2)); ax.bar([i-.18 for i in x],[summary["undefended"][k] for k in keys],.36,label="Undefended",color="#708c99"); ax.bar([i+.18 for i in x],[summary["defended"][k] for k in keys],.36,label="Defended",color="#c84b31"); ax.set_xticks(list(x),labels); ax.set_ylim(0,105); ax.set_ylabel("Percent"); ax.legend(frameon=False); ax.set_title("Protocol Utility, Security, and Traceability"); fig.tight_layout(); chart=assets/"attack_benign_matrix.png"; fig.savefig(chart,dpi=180,facecolor="white",transparent=False); plt.close(fig)
    with PILImage.open(chart) as image: image.convert("RGB").save(chart)
    (assets/"procedure_diagram.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="210"><rect width="100%" height="100%" fill="white"/><text x="700" y="105" text-anchor="middle" font-family="Arial" font-size="25">Agent Card -> A2A task -> Contract -> Taint / Scope Policy -> MCP Tool -> Artifact + Trace</text></svg>\n',encoding="utf-8")
    styles=getSampleStyleSheet(); title_style=ParagraphStyle("ProjectTitle",parent=styles["Title"],fontSize=19,leading=23,spaceAfter=14); subtitle_style=ParagraphStyle("ProjectSubtitle",parent=styles["Heading2"],fontSize=13,leading=16,spaceBefore=0,spaceAfter=10); story=[Paragraph("Secure Interoperable Agent Gateway",title_style),Paragraph("Measured undefended versus defended protocol workflow",subtitle_style),Image(str(chart),width=7*inch,height=3.64*inch)]; data=[["Metric","Undefended","Defended"]]+[[label,f"{summary['undefended'][key]:.1f}%",f"{summary['defended'][key]:.1f}%"] for label,key in zip(labels,keys)]; table=Table(data,colWidths=[3*inch,1.5*inch,1.5*inch]); table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#1f4e5f")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),.5,colors.grey),("PADDING",(0,0),(-1,-1),7)])); story.extend([Spacer(1,12),table]); review=summary.get("policy_review",{}); accuracy=review.get("accuracy_pct");
    if accuracy is not None: story.extend([Spacer(1,12),Paragraph("Structured policy review",styles["Heading2"]),Paragraph(f"Recommendation accuracy: {accuracy:.1f}% across {review['cases']} held-out cases ({review['model_calls']} model calls). Recommendations were scored but could not authorize tools.",styles["BodyText"])])
    story.extend([Spacer(1,14),Paragraph("Limits",styles["Heading2"]),Paragraph("The experiment uses local protocol envelopes and synthetic credentials. It measures control logic, not internet transport, production identity infrastructure, or resistance to every prompt-injection strategy.",styles["BodyText"])])
    def page(canvas,doc): canvas.saveState(); canvas.setFillColor(colors.white); canvas.rect(0,0,letter[0],letter[1],fill=1,stroke=0); canvas.setFillColor(colors.HexColor("#526971")); canvas.setFont("Helvetica",8); canvas.drawString(45,18,"Project 7 - measured artifact report"); canvas.drawRightString(letter[0]-45,18,f"Page {doc.page}"); canvas.restoreState()
    SimpleDocTemplate(str(args.output),pagesize=letter,leftMargin=45,rightMargin=45,topMargin=42,bottomMargin=38).build(story,onFirstPage=page,onLaterPages=page); print(f"Wrote {args.output.name}")


if __name__=="__main__": main()
