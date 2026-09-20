"""Create marketplace-compliant listing copy for the round-seven draft."""
import json
from catalog_round7 import ROOT, CATALOG

DETAILS = {
    'bookwyrm': dict(
        name='BookWyrm',
        category='Other',
        description='Federated social reading catalog for tracking books, shelves and reviews.',
        intro='BookWyrm v0.9.3 is a self-hosted, federated social reading catalog for tracking what you have read, are reading and want to read, with shelves, reviews and ActivityPub federation. The stack pairs the official BookWyrm image with a persistent PostgreSQL database, an authenticated private Redis service, and an in-container nginx that serves static and media files from a single volume.',
        status='This is an unpublished draft prepared locally; it has not yet been deployment-tested on Railway. The validation scope below states exactly what has and has not been checked.',
        about='The template defines 3 services with pinned container digests, generated deployment secrets, explicit service references, and persistent volumes for stateful dependencies. The BookWyrm adapter builds from `main`. Railway terminates HTTPS for the public endpoint; PostgreSQL and Redis are private with no public TCP proxies. The adapter runs migrations, initial data, theme compilation and static collection on boot, then supervises gunicorn, a Celery worker, Celery beat and nginx. Filesystem-backed services should remain single-replica.',
        use_cases=[
            'Track books across to-read, reading and read shelves.',
            'Write and share reviews and ratings with your own instance.',
            'Follow readers and instances over ActivityPub federation.',
        ],
        required_input='none; generated secrets and service references supply the template defaults. Configure SMTP variables only if you need invitations, password resets or notification email.',
        first_use='Open the BookWyrm domain and register the first account; the instance starts in install mode and the first signup becomes the owner/administrator. Add books from the built-in OpenLibrary, Inventaire and bookwyrm.social connectors, then create shelves and record reviews. Configure an SMTP host before relying on outbound email.',
        scope='Federation is enabled by default, so the instance is joinable by other servers over its public domain; restrict federation from the admin UI for a private catalog. A single private Redis instance backs both the activity/session cache (database 0) and the Celery broker and results (database 1), a deliberate simplification of upstream\u2019s two Redis services. The in-container nginx serves /static and /images from the one /data volume; upstream\u2019s optional Anubis bot challenge and response cache are not included. Outbound email, S3 media storage and reverse-proxy TLS are operator concerns. The image is digest-pinned at v0.9.3.',
        backups='Back up a consistent PostgreSQL export plus the complete /data volume (static, images and exports) and the generated SECRET_KEY. Test restoration into an isolated project before depending on a backup. Reverting the container image does not revert database migrations.',
        validation='Static catalog validation (service references, image pins, exposure, one-volume limits, variable descriptions, adapter existence and shell syntax) and a `docker build --check` of the adapter passed locally. A fresh Railway startup, the functional BookWyrm workflow, restart and volume-preserving redeploy, and backup/restore have not yet been performed. No deployment cost or revenue estimate has been measured.',
        why='Railway keeps the services, networking, environment references, deployment logs and volumes together in one project, and this template supplies the tested service configuration. Railway resources and volume storage are billed separately from external SMTP and other service providers.',
        upstream='https://github.com/bookwyrm-social/bookwyrm/tree/v0.9.3',
    ),
}


def source_label(service):
    if service['source'].get('image'):
        return service['source']['image'].split('@')[0]
    return service['build']['dockerfilePath']


def main():
    sources = json.loads((ROOT / 'sources.round7.lock.json').read_text())['candidates']
    metadata = {}
    for slug, d in DETAILS.items():
        source = sources[slug]
        metadata[slug] = {'name': d['name'], 'category': d['category'], 'description': d['description'],
                          'image': 'https://github.com/' + source['repository'].split('/')[0] + '.png'}
        rows = ['| Service | Source | Persistent path |', '| --- | --- | --- |']
        for service in CATALOG[slug]():
            mounts = ', '.join('`' + v['mountPath'] + '`' for v in service.get('volumeMounts', {}).values()) or 'None'
            rows.append(f"| {service['name']} | `{source_label(service)}` | {mounts} |")
        bullets = '\n'.join('- ' + c for c in d['use_cases'])
        text = f'''# Deploy and Host {d['name']} on Railway

{d['intro']}

{d['status']}

## About Hosting {d['name']}

{d['about']}

## Common Use Cases

{bullets}

## Dependencies for {d['name']} Hosting

### Deployment Dependencies

{chr(10).join(rows)}

Required input before deployment: {d['required_input']}

## First Use

{d['first_use']}

## Scope and Limitations

{d['scope']}

## Backups and Upgrades

{d['backups']}

## Validation Scope

{d['validation']}

## Why Deploy {d['name']} on Railway?

{d['why']} Railway resources and volume storage are billed separately; no fixed hosting cost is claimed.

## Support and Upstream

[Upstream source and release]({d['upstream']}). This is an independent community integration; upstream licenses, trademarks and paid-feature restrictions remain in effect. Report issues with redacted logs and image versions; never share credentials.
'''
        (ROOT / 'templates' / slug / 'README.md').write_text(text)
    (ROOT / 'marketplace.round7.json').write_text(json.dumps(metadata, indent=2) + '\n')


if __name__ == '__main__':
    main()
