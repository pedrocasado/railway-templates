# BookWyrm

Federated social reading catalog for tracking books, shelves and reviews.

## Setup

Open the public URL and register the first account; BookWyrm starts in install mode and the first signup becomes the owner/administrator. Configure an SMTP server (EMAIL_HOST and friends) before relying on invitations, password resets or notification mail. Search the built-in OpenLibrary, Inventaire and bookwyrm.social connectors to add books, then build shelves and record reviews.

## Architecture

| Service | Access | Volume |
| --- | --- | --- |
| `postgres` | Private | `/var/lib/postgresql/data` |
| `redis` | Private | `/data` |
| `bookwyrm` | Public HTTPS | `/data` |

Images are digest-pinned. Repository-backed adapters build from `orenaksakal/railway-templates`, branch `main`, using the repository root as Docker context. Volume-backed services support one replica. Railway terminates public HTTPS.

## Scope and limitations

Federation is enabled by default: the instance publishes and consumes ActivityPub over its public domain and is joinable by other servers. A single private Redis instance backs both the activity/session cache (database 0) and the Celery broker and results (database 1), a deliberate simplification of upstream’s two Redis services. The in-container nginx serves /static and /images from the one /data volume; upstream’s optional Anubis bot challenge and response cache are not included. Outbound email, S3 media storage and reverse-proxy TLS are operator concerns. The image is digest-pinned at v0.9.3.

## Validation

Release preparation is in progress. A gateway health endpoint establishes proxy readiness only. External integrations, resource sizing, full application workflows and disaster recovery require their own validation; no fixed hosting cost is claimed.

Acceptance workflow: Register the first owner account, search and add a book, create a shelf, upload a cover image, follow an account on another instance, restart the stack, and confirm the user, book, shelf, uploaded cover and database all survive the restart.

## Backup and upgrades

Back up every listed volume plus generated application secrets. For database-backed products include a consistent database export. Test restoration separately before an image or schema upgrade; reverting a container image does not revert migrated data.

## Upstream and discovery

- [Official project](https://github.com/bookwyrm-social/bookwyrm); documentation snapshot `v0.9.3` / `3557c58c3f676813ae261ab5049ec65bb1574c42`.
- 2,780 GitHub stars at research time; this is accumulated interest, not search volume.
- Marketplace searches: `BookWyrm`, `Bookwyrm`. No matching product found; unrelated alias hits are recorded in `sources.round7.lock.json`.
- Container snapshots and source revisions are tracked separately; floating tags are pinned by digest, not assumed to match the repository's latest release.

Upstream software retains its own license and trademarks. This community integration does not imply upstream endorsement.
