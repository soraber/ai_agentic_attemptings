"""Credential-free provenance for new evaluation runs, including failed runs."""
import hashlib
import json
import os
import platform
import re
import sys
import time
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path


def digest(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def public_config(value):
    if isinstance(value, dict):
        return {key: public_config(item) for key, item in value.items()
                if not any(word in key.lower() for word in ('api_key', 'password', 'secret', 'access_token'))}
    if isinstance(value, (list, tuple)):
        return [public_config(item) for item in value]
    if isinstance(value, str):
        if value.startswith(('/', '~', 'file:')) or re.search(r'\b(?:hf_[A-Za-z0-9]{20,}|sk-(?:proj-)?[A-Za-z0-9_-]{20,})', value):
            return '<redacted>'
        return value
    if value is None or type(value) in (bool, int, float):
        return value
    raise ValueError('Manifest configuration must contain plain JSON-compatible values')


class RunManifest:
    def __init__(self, project_root, output_dir, configuration):
        self.root, self.output = Path(project_root).resolve(), Path(output_dir).resolve()
        if not self.output.is_relative_to(self.root/'output/runs/upgrade-v2'):
            raise ValueError('New provenance must use this project output/runs/upgrade-v2 tree')
        self.path = self.output/'run_manifest.json'
        self.configuration = public_config(configuration)
        self.document = None

    def inventory(self):
        result = {}
        for folder, suffixes in [('src', {'.py'}), ('config', {'.json'}),
                                 ('data', {'.json', '.jsonl', '.csv', '.sha256'})]:
            for path in sorted((self.root/folder).rglob('*')):
                if path.is_file() and path.suffix in suffixes and path.resolve().is_relative_to(self.root):
                    result[path.relative_to(self.root).as_posix()] = digest(path)
        for path in sorted(self.root.glob('*.ipynb')):
            notebook = json.loads(path.read_text())
            sources = [(cell.get('id'), cell.get('cell_type'), cell['source']) for cell in notebook['cells']]
            result[path.name+':sources'] = hashlib.sha256(json.dumps(sources, sort_keys=True).encode()).hexdigest()
        return result

    def __enter__(self):
        self.output.mkdir(parents=True, exist_ok=True)
        self.started = time.perf_counter()
        self.document = {'manifest_version':'upgrade-v2', 'status':'running',
            'started_at_utc':datetime.now(timezone.utc).isoformat(), 'project':self.root.name,
            'configuration':self.configuration, 'input_source_sha256':self.inventory(),
            'recorder_sha256':digest(__file__),
            'runtime':{'python':platform.python_version(), 'os':platform.system(),
                       'architecture':platform.machine(), 'logical_cpus':os.cpu_count()},
            'packages':{item.metadata['Name']:item.version for item in metadata.distributions()},
            'model_resolution_note':'Configured API aliases are not immutable provider snapshots; actual revisions belong in per-call usage when available.',
            'prompt_provenance':'Prompt definitions are fingerprinted in source files; dynamic context is fingerprinted through input datasets. Raw prompts are not exported here.'}
        with self.path.open('x') as handle:
            json.dump(self.document, handle, indent=2, sort_keys=True)
        return self

    def record(self, summary, model_metadata=None):
        self.document['summary_sha256'] = hashlib.sha256(json.dumps(summary, sort_keys=True, default=str).encode()).hexdigest()
        self.document['observed_model_metadata'] = public_config(model_metadata or {})

    def __exit__(self, exc_type, exc, traceback):
        self.document.update(status='failed' if exc_type else 'complete',
            error_type=exc_type.__name__ if exc_type else None,
            seconds=time.perf_counter()-self.started, finished_at_utc=datetime.now(timezone.utc).isoformat())
        self.document['input_source_sha256_after'] = self.inventory()
        self.document['sources_changed_during_run'] = (self.document['input_source_sha256'] != self.document['input_source_sha256_after'])
        torch = sys.modules.get('torch')
        if torch is not None and torch.cuda.is_available():
            self.document['runtime'].update(gpu=torch.cuda.get_device_name(0),
                peak_allocated_bytes=torch.cuda.max_memory_allocated(), peak_scope='process lifetime unless caller resets peak')
        self.path.write_text(json.dumps(self.document, indent=2, sort_keys=True)+'\n')
        return False
