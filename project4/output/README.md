# Output Contract

This directory intentionally contains no placeholder metrics. Notebook cell
`P04-C10` and `tools/generate_report.py` create the final artifacts after execution.

Expected files:

```text
project4_final_summary.json
project4_representative_samples.json
project4_traces.jsonl
project4_report.pdf
project4_report_assets/procedure_diagram.svg
project4_report_assets/quality_metrics.png
project4_report_assets/recovery_safety.png
project4_report_assets/latency_cost_tradeoff.png
```

`project4_final_summary.json` is the source of truth for report metrics. The report
generator must read saved values and must not contain hard-coded results.
