"""Wrap only a generated evaluation block, preserving its existing control flow."""
import ast
import textwrap


def wrap(source, project):
    source = textwrap.dedent(source).strip('\n').replace('output/runs/upgrade-v1', 'output/runs/upgrade-v2')
    tree = ast.parse(source)
    gate = next(n for n in tree.body if isinstance(n, ast.If) and 'RUN_FULL_EVAL' in ast.unparse(n.test))
    assignment = next(n for n in gate.orelse if isinstance(n, ast.Assign)
                      and any(isinstance(t, ast.Name) and t.id == 'result_dir' for t in n.targets))
    lines = source.splitlines()
    after = assignment.end_lineno
    if after < len(lines) and 'result_dir.mkdir(' in lines[after]:
        after += 1
    header = ["from runpy import run_path", "RunManifest = run_path(str(PROJECT_ROOT.parent / 'tools/run_manifest.py'))['RunManifest']"]
    body = lines[after:gate.end_lineno]
    body = ['    '+line if line else line for line in body]
    body.append("        run_manifest.record(summary, {name: getattr(globals().get(name), 'model_revision', None) for name in ('source_planner', 'local_backend', 'embedding_retriever')})")
    return '\n'.join(header+lines[:assignment.end_lineno]
        +["    with RunManifest(PROJECT_ROOT, result_dir, config.model_dump()) as run_manifest:"]
        +body+lines[gate.end_lineno:])+'\n'
