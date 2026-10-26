"""One Frappe site and its processes, with one persistent Railway volume."""
import json
import os
from pathlib import Path
import re
import shutil
import signal
import socket
import subprocess
import sys
import time

BENCH = Path('/home/frappe/frappe-bench')
DATA = Path('/data')

def required(name):
    value = os.environ.get(name, '')
    if not value:
        raise SystemExit(f'{name} is required')
    return value

def run(*args):
    result = subprocess.run(args, cwd=BENCH)
    if result.returncode:
        raise SystemExit(f"{args[0]} failed (exit {result.returncode}); arguments suppressed")

def assets_ready(path):
    manifest = path / 'assets.json'
    if not manifest.is_file():
        return False
    try:
        data = json.loads(manifest.read_text())
    except json.JSONDecodeError:
        return False
    return all(data.get(name) for name in ('website.bundle.css', 'login.bundle.css', 'frappe-web.bundle.js'))

def atomic_json(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, indent=2) + '\n')
    temp.chmod(0o600)
    temp.replace(path)

def main():
    os.umask(0o077)
    app = required('FRAPPE_APP')
    site = os.environ.get('FRAPPE_SITE_NAME', 'site.localhost')
    if app not in ('lms', 'insights', 'builder') or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9.-]+', site):
        raise SystemExit('Invalid app or site name')
    origin = required('PUBLIC_URL').rstrip('/')
    if not re.fullmatch(r'https?://[a-zA-Z0-9.:-]+', origin):
        raise SystemExit('PUBLIC_URL must be an HTTP(S) origin')
    db_host = required('DB_HOST')
    db_port = int(os.environ.get('DB_PORT', '3306'))
    for attempt in range(90):
        try:
            with socket.create_connection((db_host, db_port), timeout=2):
                break
        except OSError:
            time.sleep(2)
    else:
        raise SystemExit('Database did not become reachable within 180 seconds')

    # Assets belong to the image; site configuration and uploads belong to the volume.
    template = Path('/home/frappe/sites-template')
    for name in ('assets', 'apps.txt'):
        source, destination = template / name, DATA / name
        if source.is_dir():
            # This directory contains only image-built assets, not user uploads.
            # Replace it on restart so existing app symlinks do not break copytree.
            if destination.is_symlink():destination.unlink()
            elif destination.exists():shutil.rmtree(destination)
            shutil.copytree(source, destination, symlinks=True, dirs_exist_ok=True)
        elif source.exists():
            shutil.copy2(source, destination)
    # The base image stores the built Frappe bundles outside sites. Without this map,
    # pages request /website.bundle.css and the login script never loads.
    baked = BENCH / 'assets'
    if not assets_ready(DATA / 'assets') and assets_ready(baked):
        destination = DATA / 'assets'
        if destination.is_symlink():
            destination.unlink()
        elif destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(baked, destination, symlinks=True)
    common = DATA / 'common_site_config.json'
    config = json.loads(common.read_text()) if common.exists() else {}
    config.update(db_host=db_host, db_port=db_port,
                  redis_cache=required('REDIS_URL'), redis_queue=required('REDIS_URL'),
                  redis_socketio=required('REDIS_URL'), socketio_port=9000,
                  default_site=site, serve_default_site=True)
    atomic_json(common, config)
    marker = DATA / '.template-release'
    release = required('TEMPLATE_RELEASE')
    site_config = DATA / site / 'site_config.json'
    if not site_config.exists():
        # Never force-create over a partial/existing site or database.
        run('bench', 'new-site', site, '--db-host', db_host, '--db-port', str(db_port),
            '--db-root-password', required('DB_ROOT_PASSWORD'),
            '--admin-password', required('ADMIN_PASSWORD'),
            '--mariadb-user-host-login-scope=%', '--install-app', app, '--set-default')
        marker.write_text(release)
    elif not marker.exists() or marker.read_text() != release:
        if os.environ.get('ALLOW_MIGRATION') != 'true':
            raise SystemExit('Existing site needs migration. Back up database + /data, then set ALLOW_MIGRATION=true for this release.')
        run('bench', '--site', site, 'migrate')
        marker.write_text(release)
    run('bench', '--site', site, 'set-config', 'host_name', origin)
    if app == 'insights':
        run('bench', '--site', site, 'set-config', 'server_script_enabled', '1')
    run('bench', '--site', site, 'enable-scheduler')
    run('bench', '--site', site, 'set-maintenance-mode', 'off')
    # Drop a cached asset map from an earlier boot. Otherwise pages keep linking /website.bundle.css.
    run('bench', '--site', site, 'clear-cache')
    port = int(os.environ.get('PORT', '8080'))
    nginx = Path('/opt/railway/nginx.conf').read_text().replace('__SITE__', site).replace('__PORT__', str(port))
    Path('/tmp/frappe-nginx.conf').write_text(nginx)
    commands = [
        ['env/bin/gunicorn', '--chdir', str(BENCH / 'sites'), '--bind', '127.0.0.1:8000',
         '--workers', os.environ.get('WEB_WORKERS', '2'), '--threads', '4', '--timeout', '120',
         '--worker-class', 'gthread', '--preload', 'frappe.app:application'],
        ['node', 'apps/frappe/socketio.js'],
        ['bench', 'worker', '--queue', 'short,default,long'],
        ['bench', 'schedule'],
        ['nginx', '-c', '/tmp/frappe-nginx.conf', '-g', 'daemon off;'],
    ]
    children = []
    stopping = False
    def stop(signum, frame):
        nonlocal stopping
        stopping = True
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    status = 0
    try:
        for command in commands:
            children.append(subprocess.Popen(command, cwd=BENCH, start_new_session=True))
        while not stopping:
            for child in children:
                if child.poll() is not None:
                    print(f'Required process exited: {child.args[0]}', file=sys.stderr)
                    status, stopping = 1, True
                    break
            time.sleep(0.5)
    finally:
        for child in children:
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGTERM)
        deadline = time.monotonic() + 30
        for child in children:
            try:
                child.wait(timeout=max(0.1, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
    return status

if __name__ == '__main__':
    sys.exit(main())
