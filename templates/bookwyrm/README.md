# Deploy and Host BookWyrm on Railway

BookWyrm v0.9.3 is a self-hosted, federated social reading catalog for tracking what you have read, are reading and want to read, with shelves, reviews and ActivityPub federation. The stack pairs the official BookWyrm image with a persistent PostgreSQL database, an authenticated private Redis service, and an in-container nginx that serves static and media files from a single volume.

This is an unpublished draft prepared locally; it has not yet been deployment-tested on Railway. The validation scope below states exactly what has and has not been checked.

## About Hosting BookWyrm

The template defines 3 services with pinned container digests, generated deployment secrets, explicit service references, and persistent volumes for stateful dependencies. The BookWyrm adapter builds from `main`. Railway terminates HTTPS for the public endpoint; PostgreSQL and Redis are private with no public TCP proxies. The adapter runs migrations, initial data, theme compilation and static collection on boot, then supervises gunicorn, a Celery worker, Celery beat and nginx. Filesystem-backed services should remain single-replica.

## Common Use Cases

- Track books across to-read, reading and read shelves.
- Write and share reviews and ratings with your own instance.
- Follow readers and instances over ActivityPub federation.

## Dependencies for BookWyrm Hosting

### Deployment Dependencies

| Service | Source | Persistent path |
| --- | --- | --- |
| postgres | `postgres:17` | `/var/lib/postgresql/data` |
| redis | `redis:7.4` | `/data` |
| bookwyrm | `templates/bookwyrm/Dockerfile` | `/data` |

Required input before deployment: none; generated secrets and service references supply the template defaults. Configure SMTP variables only if you need invitations, password resets or notification email.

## First Use

Open the BookWyrm domain and register the first account; the instance starts in install mode and the first signup becomes the owner/administrator. Add books from the built-in OpenLibrary, Inventaire and bookwyrm.social connectors, then create shelves and record reviews. Configure an SMTP host before relying on outbound email.

## Scope and Limitations

Federation is enabled by default, so the instance is joinable by other servers over its public domain; restrict federation from the admin UI for a private catalog. A single private Redis instance backs both the activity/session cache (database 0) and the Celery broker and results (database 1), a deliberate simplification of upstream’s two Redis services. The in-container nginx serves /static and /images from the one /data volume; upstream’s optional Anubis bot challenge and response cache are not included. Outbound email, S3 media storage and reverse-proxy TLS are operator concerns. The image is digest-pinned at v0.9.3.

## Backups and Upgrades

Back up a consistent PostgreSQL export plus the complete /data volume (static, images and exports) and the generated SECRET_KEY. Test restoration into an isolated project before depending on a backup. Reverting the container image does not revert database migrations.

## Validation Scope

Static catalog validation (service references, image pins, exposure, one-volume limits, variable descriptions, adapter existence and shell syntax) and a `docker build --check` of the adapter passed locally. A fresh Railway startup, the functional BookWyrm workflow, restart and volume-preserving redeploy, and backup/restore have not yet been performed. No deployment cost or revenue estimate has been measured.

## Why Deploy BookWyrm on Railway?

Railway keeps the services, networking, environment references, deployment logs and volumes together in one project, and this template supplies the tested service configuration. Railway resources and volume storage are billed separately from external SMTP and other service providers. Railway resources and volume storage are billed separately; no fixed hosting cost is claimed.

## Support and Upstream

[Upstream source and release](https://github.com/bookwyrm-social/bookwyrm/tree/v0.9.3). This is an independent community integration; upstream licenses, trademarks and paid-feature restrictions remain in effect. Report issues with redacted logs and image versions; never share credentials.
