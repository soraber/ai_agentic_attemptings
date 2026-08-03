#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def write_procedure_diagram(path: Path) -> None:
    labels = [
        "Evidence\nlogs + metrics + traces",
        "Diagnose + verify\nstructured evidence refs",
        "Plan + policy\nPydantic + allowlist",
        "Human approval\nLangGraph interrupt",
        "Execute + validate\nSQLite idempotency",
        "Compensate / close\nsaga + JSONL traces",
    ]
    width, height = 1500, 250
    box_width, gap, left = 205, 40, 22
    boxes: list[str] = []
    arrows: list[str] = []
    for index, label in enumerate(labels):
        x = left + index * (box_width + gap)
        lines = label.split("\n")
        boxes.append(
            f'<rect x="{x}" y="65" width="{box_width}" height="112" rx="6" '
            'fill="#f7fafc" stroke="#1f4e5f" stroke-width="3"/>'
        )
        boxes.append(
            f'<text x="{x + box_width / 2}" y="108" text-anchor="middle" '
            'font-family="Arial" font-size="19" font-weight="700" fill="#15262d">'
            f'{lines[0]}</text>'
        )
        boxes.append(
            f'<text x="{x + box_width / 2}" y="142" text-anchor="middle" '
            'font-family="Arial" font-size="15" fill="#37515b">'
            f'{lines[1]}</text>'
        )
        if index < len(labels) - 1:
            x1 = x + box_width + 5
            x2 = x + box_width + gap - 5
            arrows.append(
                f'<line x1="{x1}" y1="121" x2="{x2}" y2="121" '
                'stroke="#c84b31" stroke-width="4" marker-end="url(#arrow)"/>'
            )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}"><defs><marker id="arrow" markerWidth="10" '
        'markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" '
        'fill="#c84b31"/></marker></defs><rect width="100%" height="100%" fill="white"/>'
        + "".join(arrows + boxes)
        + "</svg>\n"
    )
    path.write_text(svg, encoding="utf-8")


def build_charts(summary: dict, assets: Path) -> list[Path]:
    import matplotlib.pyplot as plt
    from PIL import Image as PILImage

    assets.mkdir(parents=True, exist_ok=True)
    colors = ["#6b8793", "#c84b31"]
    outputs: list[Path] = []

    quality_metrics = ["root_cause_accuracy_pct", "remediation_accuracy_pct", "controlled_completion_pct"]
    quality_labels = ["Root cause", "Remediation", "Controlled completion"]
    x = range(len(quality_metrics))
    fig, ax = plt.subplots(figsize=(10, 5.4))
    ax.bar([value - 0.18 for value in x], [summary["baseline"][key] for key in quality_metrics], 0.36, label="Baseline", color=colors[0])
    ax.bar([value + 0.18 for value in x], [summary["durable"][key] for key in quality_metrics], 0.36, label="Durable", color=colors[1])
    ax.set_xticks(list(x), quality_labels)
    ax.set_ylim(0, 105)
    ax.set_ylabel("Percent")
    ax.set_title("Task Quality and Controlled Completion")
    ax.legend(frameon=False)
    fig.tight_layout()
    quality_path = assets / "quality_metrics.png"
    fig.savefig(quality_path, dpi=180, facecolor="white", transparent=False)
    plt.close(fig)
    with PILImage.open(quality_path) as image:
        image.convert("RGB").save(quality_path)
    outputs.append(quality_path)

    labels = ["Crash recovery", "No duplicate effects", "Unsafe plans blocked"]
    baseline = [
        summary["baseline"]["crash_recovery_pct"],
        100 - summary["baseline"]["cases_with_duplicate_effects_pct"],
        summary["policy_challenge"]["baseline_block_rate_pct"],
    ]
    durable = [
        summary["durable"]["crash_recovery_pct"],
        100 - summary["durable"]["cases_with_duplicate_effects_pct"],
        summary["policy_challenge"]["durable_block_rate_pct"],
    ]
    fig, ax = plt.subplots(figsize=(10, 5.4))
    ax.bar([value - 0.18 for value in x], baseline, 0.36, label="Baseline", color=colors[0])
    ax.bar([value + 0.18 for value in x], durable, 0.36, label="Durable", color=colors[1])
    ax.set_xticks(list(x), labels)
    ax.set_ylim(0, 105)
    ax.set_ylabel("Percent")
    ax.set_title("Recovery and Safety Controls")
    ax.legend(frameon=False)
    fig.tight_layout()
    safety_path = assets / "recovery_safety.png"
    fig.savefig(safety_path, dpi=180, facecolor="white", transparent=False)
    plt.close(fig)
    with PILImage.open(safety_path) as image:
        image.convert("RGB").save(safety_path)
    outputs.append(safety_path)

    fig, ax = plt.subplots(figsize=(8, 5.4))
    systems = ["Baseline", "Durable"]
    latency = [summary["baseline"]["mean_workflow_latency_ms"], summary["durable"]["mean_workflow_latency_ms"]]
    ax.bar(systems, latency, color=colors)
    ax.set_ylabel("Mean workflow latency (ms)")
    ax.set_title("Reliability Overhead")
    ax.text(0.02, 0.96, f"Planner calls: {summary['planner_usage']['model_calls']}\nEstimated cost: ${summary['planner_usage']['estimated_cost_usd']:.4f}", transform=ax.transAxes, va="top")
    fig.tight_layout()
    tradeoff_path = assets / "latency_cost_tradeoff.png"
    fig.savefig(tradeoff_path, dpi=180, facecolor="white", transparent=False)
    plt.close(fig)
    with PILImage.open(tradeoff_path) as image:
        image.convert("RGB").save(tradeoff_path)
    outputs.append(tradeoff_path)
    return outputs


def build_pdf(summary: dict, output_path: Path, chart_paths: list[Path]) -> None:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    styles = getSampleStyleSheet()
    title = ParagraphStyle("P4Title", parent=styles["Title"], alignment=TA_CENTER, textColor=colors.HexColor("#1f4e5f"))
    doc = SimpleDocTemplate(str(output_path), pagesize=letter, rightMargin=45, leftMargin=45, topMargin=42, bottomMargin=42)

    def draw_page(canvas, document) -> None:
        page_width, page_height = letter
        canvas.saveState()
        canvas.setFillColor(colors.white)
        canvas.rect(0, 0, page_width, page_height, fill=1, stroke=0)
        canvas.setStrokeColor(colors.HexColor("#c7d3d7"))
        canvas.line(45, 28, page_width - 45, 28)
        canvas.setFillColor(colors.HexColor("#526971"))
        canvas.setFont("Helvetica", 8)
        canvas.drawString(45, 16, "Project 4 - measured artifact report")
        canvas.drawRightString(page_width - 45, 16, f"Page {document.page}")
        canvas.restoreState()

    story = [
        Paragraph("Durable Incident-Response Agent", title),
        Paragraph("Measured comparison of a stateless loop and a checkpointed, approval-gated workflow", styles["Heading2"]),
        Spacer(1, 10),
        Paragraph(
            f"Mode: {summary['planner_mode']} | Held-out incidents: {summary['test_incidents']} | "
            f"Repetitions: {summary['evaluation_repetitions']} | Seed: {summary['seed']}",
            styles["BodyText"],
        ),
        Spacer(1, 12),
        Image(str(chart_paths[0]), width=7.0 * inch, height=3.78 * inch),
        Spacer(1, 8),
        Paragraph("Interpretation", styles["Heading2"]),
        Paragraph(
            "Diagnosis and remediation scores test task quality. Controlled completion additionally "
            "credits explicit policy blocks, operator rejection, and successful compensation instead "
            "of treating every non-execution as an undifferentiated failure.",
            styles["BodyText"],
        ),
        PageBreak(),
        Image(str(chart_paths[1]), width=6.5 * inch, height=3.2 * inch),
        Spacer(1, 8),
    ]
    table_data = [["Metric", "Baseline", "Durable"]]
    for label, key in [
        ("Crash recovery", "crash_recovery_pct"),
        ("Cases with duplicate effects", "cases_with_duplicate_effects_pct"),
        ("Failed actions compensated", "failed_actions_compensated_pct"),
    ]:
        table_data.append([label, f"{summary['baseline'][key]:.1f}%", f"{summary['durable'][key]:.1f}%"])
    table = Table(table_data, colWidths=[3.2 * inch, 1.5 * inch, 1.5 * inch])
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e5f")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#b9c7cc")), ("PADDING", (0, 0), (-1, -1), 7)]))
    story.extend([table, Spacer(1, 8), Image(str(chart_paths[2]), width=5.8 * inch, height=3.2 * inch), Paragraph("Limits", styles["Heading2"]), Paragraph("The action tools are simulations, the benchmark is controlled, and deterministic mode validates workflow mechanics rather than general model intelligence. API conclusions require the recorded model configuration and repeated held-out evaluation.", styles["BodyText"])])
    doc.build(story, onFirstPage=draw_page, onLaterPages=draw_page)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Project 4 charts and report")
    parser.add_argument("--summary", type=Path, default=ROOT / "output/project4_final_summary.json")
    parser.add_argument("--output", type=Path, default=ROOT / "output/project4_report.pdf")
    args = parser.parse_args()
    if not args.summary.exists():
        raise SystemExit("Measured summary is absent. Run notebook cell P04-C08 before generating a report.")
    summary = json.loads(args.summary.read_text(encoding="utf-8"))
    if summary.get("result_status") != "measured":
        raise SystemExit("Refusing to report non-measured or placeholder results.")
    assets = args.output.parent / "project4_report_assets"
    assets.mkdir(parents=True, exist_ok=True)
    write_procedure_diagram(assets / "procedure_diagram.svg")
    charts = build_charts(summary, assets)
    build_pdf(summary, args.output, charts)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
