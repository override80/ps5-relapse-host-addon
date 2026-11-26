# PLAN — PS5 Relapse host as HA addon behind the nginx addon (no pfSense NAT/VIP)

Status: drafted for review. Supersedes the VIP+NAT section in CONTEXT.md.

## Architecture

```
PS5 (10.11.12.74)
  |  https://manuals.playstation.net  (SNI = manuals.playstation.net)
  |  pfSense DNS override: manuals.playstation.net -> 10.11.12.98   (only pfSense change; no VIP, no NAT)
  v
10.11.12.98:443  nginx addon (core_nginx_proxy, docker port mapping 443/80)
  |  full custom server block: /usr/share/hassio/share/nginx/nginx_proxy/ps5-relapse.conf
  |  (= /share/nginx_proxy/ps5-relapse.conf in the container; customize already enabled)
  |  server_name manuals.playstation.net, self-signed cert in /usr/share/hassio/ssl/
  v
proxy_pass http://10.11.12.98:8082  (host port, free — probed)
  v
Relapse addon container (host_network: true) -> app/relapse/serve_tls.py on 8082
  -> exploit page (index.html, src/, offsets/, payloads/)
```

- PS5 User's Guide loads manuals.playstation.net over HTTPS; nginx presents the
  self-signed cert; PS5 shows the untrusted-cert prompt -> user accepts (works,
  proven earlier on the Mac host).
- Port 80: the same server block also listens on 80 and proxies to 8082.
- `update.playstation.net` DNS block on pfSense stays (firmware update protection).

## Why a full server block (not a location)

The existing customization `/usr/share/hassio/share/nginx/nginx_proxy_default_custom.conf`
uses the `customize.default` glob (`nginx_proxy_default*.conf`), which is included
*inside* the main domain's 443 server block — i.e. extra `location`s for the main
domain (jellyfin, observer, ...). The PS5 sends SNI `manuals.playstation.net`,
which does NOT match the main domain block (that would fall to default_server -> 444).
So we need a full `server {}` in the `customize.servers` glob:
`/usr/share/hassio/share/nginx/nginx_proxy/*.conf` (host path
`/usr/share/hassio/share/nginx/nginx_proxy/`; the dir is root-only, use sudo).

## nginx addon changes (on hassio, via SSH as override + sudo)

1. Self-signed cert for the manuals domain into the ssl map
   (host `/usr/share/hassio/ssl/` = container `/ssl/`):
   ```bash
   openssl req -x509 -newkey rsa:2048 -nodes -days 365 \
     -subj "/CN=manuals.playstation.net" \
     -addext "subjectAltName=DNS:manuals.playstation.net" \
     -keyout /usr/share/hassio/ssl/manuals_privkey.pem \
     -out    /usr/share/hassio/ssl/manuals_fullchain.pem
   ```
2. Create `/usr/share/hassio/share/nginx/nginx_proxy/ps5-relapse.conf`
   (style matched to the existing nginx_proxy_default_custom.conf):
   ```nginx
   server {
       server_name manuals.playstation.net;
       listen 80;
       listen 443 ssl;
       ssl_certificate     /ssl/manuals_fullchain.pem;
       ssl_certificate_key /ssl/manuals_privkey.pem;

       location / {
           proxy_pass http://10.11.12.98:8082;
           proxy_set_header Host $host;
           proxy_redirect http:// https://;
           proxy_http_version 1.1;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection $connection_upgrade;
           proxy_set_header X-Forwarded-Host $http_host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```
3. `customize` is already enabled in the nginx addon options — nothing to change.
4. Restart the nginx addon (or reload) to pick up the new server block.

## Addon distribution: custom add-on from a GitHub repo (not local)

Mirror the reference repo (override80/homeassistant-osm-tile-server-addon):
the addon lives at the repo root with `config.json` + `repository.json`.

1. Create repo `override80/ps5-relapse-host-addon` (public, like the other
   addon repos) and push this folder's contents as the repo root:
   ```bash
   gh repo create override80/ps5-relapse-host-addon --public --description "..."
   cd ps5-exploit-host && git init && git add -A && git commit -m "1.0.0" \
     && git remote add origin git@github.com:override80/ps5-relapse-host-addon.git \
     && git push -u origin main
   ```
2. In HA: Settings > Add-ons > Add-on Store > ⋮ > Repositories >
   add `https://github.com/override80/ps5-relapse-host-addon` > Install.
3. HA builds the Dockerfile on the hassio host (arch **amd64**, qemux86-64 —
   config.json arch list already includes amd64).
4. Start the addon. `host_network: true` -> binds host 8082/8444 directly.

Staging copy stays at `hassio:/tmp/tools/new/ps5-exploit-host/` for reference.

## Addon files (repo root = ps5-exploit-host/)

```
├── config.json          # manifest: slug ps5_relapse_host, host_network: true, boot: auto
├── repository.json      # repo metadata (reference style)
├── Dockerfile           # python:3.9-slim + openssl; COPY app/ tools/ run.sh
├── run.sh               # entrypoint: cd /app/relapse, HTTP_PORT=8082, exec serve_tls.py
├── README.md / CHANGELOG.md
├── PLAN.md / CONTEXT.md
├── app/relapse/         # served root: index.html, src/, offsets/ (7.00-13.60),
│                        # payloads/ (kexp bin, elfldr elf), serve_tls.py
└── tools/               # send_payload.py, shsrv-ps5.elf, elfldr-ps5-generic.elf,
                         # ps5-firmware-pin/ (pin/unpin)
```

## pfSense change (single, needs approval — earlier attempt was denied)

- Update DNS host override `manuals` / `playstation.net` (id 7):
  10.11.12.119 (Mac) -> **10.11.12.98** (hassio).
- Keep domain override `update.playstation.net -> 127.0.0.2`.
- No VIP, no NAT rules.

## Install & verify sequence

1. nginx conf + cert on hassio (above), restart nginx addon.
2. Add the GitHub repo in HA, install + start the addon.
3. Verify addon: `nc -z 10.11.12.98 8082` -> OPEN.
4. pfSense DNS override retargeted; `dig @10.11.12.254 manuals.playstation.net` -> 10.11.12.98.
5. End-to-end from a LAN machine:
   `curl -k --resolve manuals.playstation.net:443:10.11.12.98 https://manuals.playstation.net/` -> PS5-Relapse page.
6. On the PS5: open User's Guide -> accept cert -> exploit runs ->
   `elfldr is listening on port 9021`.

## Per-boot routine (unchanged)

PS5 boots -> wait 30-60 s -> User's Guide -> accept cert -> wait for 9021 ->
from a LAN machine:
```bash
nc -z -w 4 10.11.12.74 9021 && echo OPEN || echo CLOSED
python3 tools/send_payload.py 10.11.12.74 9021 tools/shsrv-ps5.elf
nc -z -w 4 10.11.12.74 2323 && echo OPEN || echo CLOSED
cd tools/ps5-firmware-pin && python3 pin/ps5-fw-pin.py --host 10.11.12.74
```
PS5: disable Automatic Downloads (System > System Software and Updates).
13.40 is flaky: on `unexpected oid state` / hang at `checking aio groups`,
hard-reset (hold power ~10 s) and retry.

## Rollback

- pfSense: set manuals override back to 10.11.12.119 (or delete it), delete
  update.playstation.net override if desired.
- hassio: remove /usr/share/hassio/share/nginx/nginx_proxy/ps5-relapse.conf,
  remove /usr/share/hassio/ssl/manuals_*.pem, restart nginx addon, remove the
  addon repo + addon in HA.
- PS5: `python3 pin/ps5-fw-unpin.py --host 10.11.12.74`.
