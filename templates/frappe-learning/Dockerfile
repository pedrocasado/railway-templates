FROM ghcr.io/frappe/crm:v1.83.0@sha256:d32697412d4ccd3b7042a8d757000375a1daa6be76347a267d5261a1809eab3b

USER frappe
WORKDIR /home/frappe/frappe-bench
ENV FRAPPE_APP=lms TEMPLATE_RELEASE=v2.63.0

# CORRIGIDO: Adicionado o caminho correto do repositório /frappe/frappe.git
RUN git clone --depth 1 --filter=blob:none --sparse --branch v16.36.0 https://github.com /tmp/frappe-ui \
    && git -C /tmp/frappe-ui sparse-checkout set ui \
    && rm -rf apps/frappe/ui \
    && cp -a /tmp/frappe-ui/ui apps/frappe/ui \
    && rm -rf /tmp/frappe-ui

RUN git clone --no-checkout https://github.com apps/payments && git -C apps/payments checkout 9885a6e500104f1f160add47d55b370773e67a81

RUN git clone --no-checkout https://github.com apps/lms \
    && git -C apps/lms checkout 2ee61568603d0b081e9d98c8bf39b18f4464e3b5 \
    && ls -1 apps > sites/apps.txt \
    && env/bin/pip install -q -e apps/payments -e apps/lms \
    && (cd apps/lms && (yarn install --frozen-lockfile || npm install)) \
    && cp -a sites /home/frappe/sites-template

# Alterando para root para configurar pastas, permissões e o link simbólico do volume do Railway
USER root
RUN mkdir -p /logs && chown frappe:frappe /logs \
    && mkdir -p /data && chown frappe:frappe /data \
    && rm -rf /home/frappe/frappe-bench/sites \
    && ln -s /data /home/frappe/frappe-bench/sites

# Voltando para o usuário frappe para realizar o build diretamente no volume permanente
USER frappe
RUN cp -a /home/frappe/sites-template/. /home/frappe/frappe-bench/sites/ 2>/dev/null || true

# Configura o socketio e compila os assets incluindo o framework base (frappe) para gerar os bundles de css/js
RUN bench set-config -g socketio_port 9000 \
    && bench build --production --apps frappe,lms \
    && env/bin/python -c "import lms"

# Configurações finais do Railway de execução
USER root
COPY shared/round6-frappe/start.py /opt/railway/start.py
COPY shared/round6-frappe/nginx.conf /opt/railway/nginx.conf
COPY --chmod=755 shared/round6-frappe/entrypoint.sh /opt/railway/entrypoint.sh

EXPOSE 8080
ENTRYPOINT ["/opt/railway/entrypoint.sh"]