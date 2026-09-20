"""Round-seven static validation using the shared round-five structural checks."""
import json
import re
import subprocess
import uuid
from catalog_round7 import ROOT, CATALOG


def main():
    metadata = json.loads((ROOT / 'marketplace.round7.json').read_text())
    sources = json.loads((ROOT / 'sources.round7.lock.json').read_text())['candidates']
    assert set(CATALOG) == set(metadata) == set(sources) and len(CATALOG) == 1
    count = 0
    for slug, factory in CATALOG.items():
        expected = {'services': {str(uuid.uuid5(uuid.NAMESPACE_URL, 'round7/' + slug + '/' + s['name'])): s for s in factory()}}
        assert json.loads((ROOT / 'templates' / slug / 'template.json').read_text()) == expected
        services = {s['name']: s for s in expected['services'].values()}
        assert len(services) == len(expected['services'])
        assert [s['name'] for s in services.values() if s['networking']['serviceDomains']] == [slug]
        for service in services.values():
            if service['source'].get('image'):
                assert re.search(r'@sha256:[a-f0-9]{64}$', service['source']['image'])
            else:
                dockerfile = ROOT / service['build']['dockerfilePath']
                assert dockerfile.exists()
                assert service['variables']['RAILWAY_DOCKERFILE_PATH']['defaultValue'] == str(dockerfile.relative_to(ROOT))
                for image in re.findall(r'^FROM (\S+)', dockerfile.read_text(), re.M):
                    assert image == 'scratch' or '@sha256:' in image
            assert len(service.get('volumeMounts', {})) <= 1
            assert not service['networking'].get('tcpProxies')
            if service['networking']['serviceDomains']:
                assert service['deploy'].get('healthcheckPath')
            for key, setting in service['variables'].items():
                assert setting['description']
                for token in re.findall(r'\$\{\{(.*?)\}\}', setting.get('defaultValue', '')):
                    if token.startswith('secret('):
                        assert re.fullmatch(r'secret\(\d+, "[A-Za-z0-9_-]+"\)', token)
                    else:
                        owner, var = token.split('.', 1)
                        assert owner in services
                        assert var.startswith('RAILWAY_') or var in services[owner]['variables']
        for query in sources[slug]['marketplace']:
            assert query['complete']
            assert not query['results']
        assert not sources[slug]['archived']
        assert (ROOT / 'templates' / slug / 'README.md').exists()
        for script in (ROOT / 'templates' / slug).glob('*.sh'):
            subprocess.run(['bash', '-n', str(script)], check=True)
        count += len(services)
        print(slug, len(services), 'services: pins, references, exposure and research validated')
    print('PASS:', len(CATALOG), 'templates /', count, 'services')


if __name__ == '__main__':
    main()
