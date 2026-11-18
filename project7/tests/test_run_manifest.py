import importlib.util
import json
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[2]/'tools'
spec = importlib.util.spec_from_file_location('run_manifest', TOOLS/'run_manifest.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_manifest_preserves_provenance_and_redacts_secrets(tmp_path):
    root = tmp_path/'project'
    (root/'src').mkdir(parents=True)
    (root/'src/planner.py').write_text('PROMPT = "authored prompt"\n')
    output = root/'output/runs/upgrade-v2/test'
    with module.RunManifest(root, output, {'model':'fixture', 'api_key':'must-not-appear',
         'max_output_tokens':32, 'cache_path':'/private/example'}) as manifest:
        manifest.record({'success':1})
    result = json.loads((output/'run_manifest.json').read_text())
    assert result['status']=='complete' and result['seconds'] >= 0
    assert result['configuration']=={'model':'fixture','max_output_tokens':32,'cache_path':'<redacted>'}
    assert 'src/planner.py' in result['input_source_sha256']
    assert not result['sources_changed_during_run']
    assert str(tmp_path) not in (output/'run_manifest.json').read_text()
    with pytest.raises(FileExistsError):
        with module.RunManifest(root,output,{}): pass


def test_failed_run_saves_error_type_not_sensitive_message(tmp_path):
    output=tmp_path/'output/runs/upgrade-v2/failure'
    with pytest.raises(RuntimeError):
        with module.RunManifest(tmp_path,output,{}):
            raise RuntimeError('private exception text')
    raw=(output/'run_manifest.json').read_text()
    assert json.loads(raw)['status']=='failed' and 'private exception text' not in raw
    with pytest.raises(ValueError):
        module.RunManifest(tmp_path,tmp_path/'output/runs/upgrade-v1/old',{})


def test_all_wrapped_notebooks_keep_disabled_evaluation_disabled():
    import ast
    import asyncio
    import inspect
    for project in range(4,9):
        builder_path=TOOLS.parent/f'project{project}/tools/build_notebook.py'
        spec=importlib.util.spec_from_file_location('builder',builder_path)
        builder=importlib.util.module_from_spec(spec); spec.loader.exec_module(builder)
        cell=next(c for c in builder.CELLS if c['id']==f'P0{project}-C08')
        source=''.join(cell['source'])
        tree=ast.parse(source)
        assert len([n for n in ast.walk(tree) if isinstance(n,ast.With) and 'RunManifest' in ast.unparse(n.items[0])])==1
        gate=next(n for n in tree.body if isinstance(n,ast.If) and 'RUN_FULL_EVAL' in ast.unparse(n.test))
        namespace={'RUN_FULL_EVAL':False}
        result=eval(compile(ast.Module(body=[gate],type_ignores=[]),'<disabled-cell>','exec',flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT),namespace)
        if inspect.isawaitable(result):
            asyncio.run(result)
