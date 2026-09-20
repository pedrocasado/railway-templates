#!/bin/bash
set -euo pipefail
umask 022
: "${DOMAIN:?}" "${SECRET_KEY:?}" "${POSTGRES_HOST:?}" "${POSTGRES_PASSWORD:?}"

mkdir -p /data/static /data/images
chmod 755 /data

echo "Waiting for PostgreSQL at ${POSTGRES_HOST}:5432 ..."
for _ in $(seq 1 90); do
    if (exec 3<>"/dev/tcp/${POSTGRES_HOST}/5432") 2>/dev/null; then
        exec 3>&- 3<&- || true
        break
    fi
    sleep 2
done

cd /app
python manage.py migrate --noinput
python manage.py initdb
python manage.py compile_themes
python manage.py collectstatic --noinput

celery -A celerywyrm worker --pool=threads --concurrency="${CELERY_CONCURRENCY:-4}" -l info \
    -Q high_priority,medium_priority,low_priority,streams,images,suggested_users,email,connectors,lists,inbox,imports,import_triggered,broadcast,misc &
worker=$!
celery -A celerywyrm beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler &
beat=$!
gunicorn bookwyrm.wsgi:application &
web=$!
nginx -g 'daemon off;' &
proxy=$!

stop() { kill -TERM "$worker" "$beat" "$web" "$proxy" 2>/dev/null || true; wait 2>/dev/null || true; }
trap 'stop; exit 0' TERM INT
set +e
wait -n "$worker" "$beat" "$web" "$proxy"
code=$?
stop
if [ "$code" -eq 0 ]; then code=1; fi
exit "$code"
