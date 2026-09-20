"""Create listing copy for the round-seven draft."""
import json
from catalog_round7 import ROOT, CATALOG

DETAILS = {
    'bookwyrm': ('BookWyrm', 'Other',
                 'Federated social reading catalog for tracking books, shelves and reviews.',
                 'Open the public URL and register the first account; BookWyrm starts in install mode and the first signup becomes the owner/administrator. Configure an SMTP server (EMAIL_HOST and friends) before relying on invitations, password resets or notification mail. Search the built-in OpenLibrary, Inventaire and bookwyrm.social connectors to add books, then build shelves and record reviews.',
                 'Federation is enabled by default: the instance publishes and consumes ActivityPub over its public domain and is joinable by other servers. A single private Redis instance backs both the activity/session cache (database 0) and the Celery broker and results (database 1), a deliberate simplification of upstream\u2019s two Redis services. The in-container nginx serves /static and /images from the one /data volume; upstream\u2019s optional Anubis bot challenge and response cache are not included. Outbound email, S3 media storage and reverse-proxy TLS are operator concerns. The image is digest-pinned at v0.9.3.',
                 'Register the first owner account, search and add a book, create a shelf, upload a cover image, follow an account on another instance, restart the stack, and confirm the user, book, shelf, uploaded cover and database all survive the restart.'),
}


def main():
    sources = json.loads((ROOT / 'sources.round7.lock.json').read_text())['candidates']
    metadata = {}
    for slug, (name, category, description, setup, limitations, workflow) in DETAILS.items():
        source = sources[slug]
        metadata[slug] = {'name': name, 'category': category, 'description': description,
                          'image': 'https://github.com/' + source['repository'].split('/')[0] + '.png'}
        rows = ['| Service | Access | Volume |', '| --- | --- | --- |']
        for service in CATALOG[slug]():
            mounts = ', '.join('`' + v['mountPath'] + '`' for v in service.get('volumeMounts', {}).values()) or 'None'
            rows.append(f"| `{service['name']}` | {'Public HTTPS' if service['networking']['serviceDomains'] else 'Private'} | {mounts} |")
        text = f'''# {name}

{description}

## Setup

{setup}

## Architecture

{chr(10).join(rows)}

Images are digest-pinned. Repository-backed adapters build from `orenaksakal/railway-templates`, branch `main`, using the repository root as Docker context. Volume-backed services support one replica. Railway terminates public HTTPS.

## Scope and limitations

{limitations}

## Validation

Release preparation is in progress. A gateway health endpoint establishes proxy readiness only. External integrations, resource sizing, full application workflows and disaster recovery require their own validation; no fixed hosting cost is claimed.

Acceptance workflow: {workflow}

## Backup and upgrades

Back up every listed volume plus generated application secrets. For database-backed products include a consistent database export. Test restoration separately before an image or schema upgrade; reverting a container image does not revert migrated data.

## Upstream and discovery

- [Official project](https://github.com/{source['repository']}); documentation snapshot `{source['revision']}` / `{source['commit']}`.
- {source['stars']:,} GitHub stars at research time; this is accumulated interest, not search volume.
- Marketplace searches: {', '.join('`' + q['query'] + '`' for q in source['marketplace'])}. No matching product found; unrelated alias hits are recorded in `sources.round7.lock.json`.
- Container snapshots and source revisions are tracked separately; floating tags are pinned by digest, not assumed to match the repository's latest release.

Upstream software retains its own license and trademarks. This community integration does not imply upstream endorsement.
'''
        (ROOT / 'templates' / slug / 'README.md').write_text(text)
    (ROOT / 'marketplace.round7.json').write_text(json.dumps(metadata, indent=2) + '\n')


if __name__ == '__main__':
    main()
