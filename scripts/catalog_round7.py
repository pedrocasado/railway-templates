"""One additional local, unpublished round-seven Railway draft: BookWyrm."""
import json
import uuid
from catalog_round5 import ROOT, secret, ref, public, private
import catalog_round3 as base

LOCK = json.loads((ROOT / 'images.round7.lock.json').read_text())


def svc(name, **kwargs):
    if kwargs.get('image'):
        kwargs['image'] = LOCK[kwargs['image']]
    return base.svc(name, **kwargs)


def postgres(app):
    return svc('postgres', image='postgres:17', volume='/var/lib/postgresql/data', env={
        'POSTGRES_USER': app, 'POSTGRES_DB': app, 'POSTGRES_PASSWORD': secret(),
        'PGDATA': '/var/lib/postgresql/data/pgdata',
    })


def redis():
    return svc('redis', image='redis:7.4', volume='/data', env={
        'REDIS_PASSWORD': secret(),
        'REDIS_URL': 'redis://:' + ref('redis', 'REDIS_PASSWORD') + '@' + ref('redis', 'RAILWAY_PRIVATE_DOMAIN') + ':6379',
    }, command="sh -c 'exec redis-server --bind 0.0.0.0 :: --appendonly yes --maxmemory-policy noeviction --requirepass \"$REDIS_PASSWORD\"'")


def bookwyrm():
    return [postgres('bookwyrm'), redis(), svc('bookwyrm', dockerfile='templates/bookwyrm/Dockerfile', volume='/data', port=8080, health='/login', env={
        'DEBUG': 'false',
        'DOMAIN': ref('bookwyrm', 'RAILWAY_PUBLIC_DOMAIN'),
        'SECRET_KEY': secret(50),
        'POSTGRES_HOST': ref('postgres', 'RAILWAY_PRIVATE_DOMAIN'), 'POSTGRES_USER': 'bookwyrm',
        'POSTGRES_DB': 'bookwyrm', 'POSTGRES_PASSWORD': ref('postgres', 'POSTGRES_PASSWORD'), 'PGPORT': 5432,
        'REDIS_ACTIVITY_URL': 'redis://:' + ref('redis', 'REDIS_PASSWORD') + '@' + ref('redis', 'RAILWAY_PRIVATE_DOMAIN') + ':6379/0',
        'REDIS_BROKER_URL': 'redis://:' + ref('redis', 'REDIS_PASSWORD') + '@' + ref('redis', 'RAILWAY_PRIVATE_DOMAIN') + ':6379/1',
        'STATIC_ROOT': '/data/static', 'MEDIA_ROOT': '/data/images',
        'EMAIL_HOST': ('', 'SMTP server hostname. Leave empty to disable outbound email; set a real host for invitations and password resets.'),
        'EMAIL_PORT': 587, 'EMAIL_HOST_USER': ('', 'SMTP username. Required only when EMAIL_HOST is configured.'),
        'EMAIL_HOST_PASSWORD': ('', 'SMTP password. Required only when EMAIL_HOST is configured.'),
        'EMAIL_USE_TLS': 'true', 'EMAIL_USE_SSL': 'false',
        'UPLOAD_IMAGE_DIMENSIONS': '400,1200,2000',
    })]


CATALOG = {'bookwyrm': bookwyrm}


def generate():
    for name, factory in CATALOG.items():
        services = factory()
        config = {'services': {str(uuid.uuid5(uuid.NAMESPACE_URL, 'round7/' + name + '/' + s['name'])): s for s in services}}
        directory = ROOT / 'templates' / name
        directory.mkdir(parents=True, exist_ok=True)
        (directory / 'template.json').write_text(json.dumps(config, indent=2) + '\n')
        print(name, len(services))


if __name__ == '__main__':
    generate()
