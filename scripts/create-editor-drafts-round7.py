"""Save the round-seven unpublished editor draft; creates no projects or deployments."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from catalog_round7 import ROOT, CATALOG

spec = importlib.util.spec_from_file_location('editor_round4', ROOT / 'scripts/create-editor-drafts-round4.py')
editor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(editor)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', required=True)
    parser.add_argument('--template', choices=CATALOG)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    subprocess.run([sys.executable, str(ROOT / 'scripts/validate-round7.py')], check=True)
    if not shutil.which('railway') or not (Path.home() / '.railway/config.json').exists():
        parser.exit(1, 'Railway CLI login is required. Install the CLI and run railway login, then retry. Local drafts are ready.\n')
    subprocess.run(['railway', 'api', 'query { __typename }', '--compact'],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    os.umask(0o077)
    directory = ROOT / '.local/round7'
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / 'drafts.json'
    receipts = json.loads(path.read_text()) if path.exists() else {}
    metadata = json.loads((ROOT / 'marketplace.round7.json').read_text())

    def save():
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps(receipts, indent=2) + '\n')
        temporary.replace(path)

    for name in [args.template] if args.template else CATALOG:
        config = json.loads((ROOT / 'templates' / name / 'template.json').read_text())
        meta = {**metadata[name], 'readme': (ROOT / 'templates' / name / 'README.md').read_text()}
        if name not in receipts:
            if args.verify_only:
                raise RuntimeError(name + ': no draft receipt exists')
            created = editor.api(
                'mutation($input:TemplateCreateV2Input!){templateCreateV2(input:$input){id code status}}',
                {'input': {'metadata': meta, 'serializedConfig': config, 'workspaceId': args.workspace}},
            )['templateCreateV2']
            receipts[name] = {'templateId': created['id'], 'workspaceId': args.workspace, 'verified': False}
            save()
        receipt = receipts[name]
        if receipt['workspaceId'] != args.workspace:
            raise RuntimeError('Workspace does not match the saved receipt')

        def read():
            live = editor.api(editor.READ, {'id': receipt['templateId']})['template']
            if live['status'] != 'UNPUBLISHED':
                raise RuntimeError(name + ': expected an unpublished draft')
            actual = live['serializedConfig']
            return live, json.loads(actual) if isinstance(actual, str) else actual

        def matches(live, actual):
            return editor.normalized_config(actual) == editor.normalized_config(config) and all(live.get(k) == v for k, v in meta.items())

        live, actual = read()
        if not matches(live, actual):
            if args.verify_only:
                raise RuntimeError(name + ': saved draft differs from local sources')
            receipt['verified'] = False
            save()
            staged = editor.api(
                'mutation($id:String!,$patch:TemplatePatch!){templateChangeSetStage(templateId:$id,patch:$patch,merge:false){id}}',
                {'id': receipt['templateId'], 'patch': {'config': editor.configuration_patch(config, actual), 'metadata': meta}},
            )['templateChangeSetStage']
            applied = editor.api(
                'mutation($id:String!){templateChangeSetApply(changeSetId:$id){status}}', {'id': staged['id']},
            )['templateChangeSetApply']
            if applied['status'] != 'APPLIED':
                raise RuntimeError(name + ': changes were not applied')
            live, actual = read()
        if not matches(live, actual):
            raise RuntimeError(name + ': read-back verification failed')
        (directory / (name + '-readback.json')).write_text(json.dumps(live, indent=2) + '\n')
        receipt.update(status=live['status'], verified=True, templateCode=live['code'],
                       configHash=hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest(),
                       url='https://railway.com/workspace/templates/' + live['id'])
        save()
        print(name, live['status'], 'configuration and metadata verified', receipt['url'], flush=True)


if __name__ == '__main__':
    main()
