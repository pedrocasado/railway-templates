FROM ghcr.io/frappe/crm:v1.83.0@sha256:d32697412d4ccd3b7042a8d757000375a1daa6be76347a267d5261a1809eab3b
USER frappe
WORKDIR /home/frappe/frappe-bench
ENV FRAPPE_APP=lms TEMPLATE_RELEASE=v2.63.0
RUN git clone --no-checkout https://github.com/frappe/payments.git apps/payments && git -C apps/payments checkout 9885a6e500104f1f160add47d55b370773e67a81
RUN git clone --no-checkout https://github.com/frappe/lms.git apps/lms \
    && git -C apps/lms checkout 2ee61568603d0b081e9d98c8bf39b18f4464e3b5 \
    && ls -1 apps > sites/apps.txt \
    && env/bin/pip install -q -e apps/payments -e apps/lms \
    && (cd apps/lms && (yarn install --frozen-lockfile || npm install)) \
    && bench build --production \
    && env/bin/python -c "import lms" \
    && cp -a sites /home/frappe/sites-template
USER root
COPY shared/round6-frappe/start.py /opt/railway/start.py
COPY shared/round6-frappe/nginx.conf /opt/railway/nginx.conf
COPY --chmod=755 shared/round6-frappe/entrypoint.sh /opt/railway/entrypoint.sh
RUN mkdir -p /logs && chown frappe:frappe /logs \
    && rm -rf /home/frappe/frappe-bench/sites \
    && ln -s /data /home/frappe/frappe-bench/sites
EXPOSE 8080
ENTRYPOINT ["/opt/railway/entrypoint.sh"]
