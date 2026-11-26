# PS5 Relapse Exploit Host add-on.
# python:3.9-slim + openssl (for the optional self-signed cert).
# host_network: true -> binds host ports 8082/8444 directly.
# nginx addon (core_nginx_proxy) proxies manuals.playstation.net -> host:8082.
FROM python:3.9-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends openssl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY app/ /app/
COPY tools/ /app/tools/
COPY run.sh /addon-run.sh
RUN chmod +x /addon-run.sh

EXPOSE 8082 8444

ENTRYPOINT ["/addon-run.sh"]
