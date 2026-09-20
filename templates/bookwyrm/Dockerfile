FROM ghcr.io/bookwyrm-social/bookwyrm:v0.9.3@sha256:593acc3dae084371939cbdc847f887db481551c03ff5b91bb85ae2f446f42b3f
RUN apt-get update \
    && apt-get install -y --no-install-recommends nginx \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f /etc/nginx/sites-enabled/default
COPY templates/bookwyrm/nginx.conf /etc/nginx/conf.d/bookwyrm.conf
COPY --chmod=755 templates/bookwyrm/entrypoint.sh /railway-entrypoint.sh
ENTRYPOINT ["/railway-entrypoint.sh"]
