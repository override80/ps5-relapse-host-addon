# PS5 Relapse Exploit Host (Home Assistant add-on)

Serves the [Relapse-Exploit](https://github.com/ntfargo/Relapse-Exploit) chain
(PS5 firmware 7.00–13.60) so the PS5 User's Guide loads the exploit page via a
`manuals.playstation.net` DNS override pointing at the hassio host.

- Addon binds host ports **8082** (HTTP) / 8444 (HTTPS) — `host_network: true`.
- The **nginx addon** (`core_nginx_proxy`) owns 80/443 and serves a custom
  server block for `manuals.playstation.net` (self-signed cert in `/ssl/`),
  proxying to `http://<hassio>:8082`. See `PLAN.md` for the full design and
  `CONTEXT.md` for network details, routines and rollback.
- `tools/` bundles the payload tooling: `send_payload.py`, `shsrv-ps5.elf`,
  a fallback `elfldr-ps5-generic.elf`, and `ps5-firmware-pin/`.

## Install

```bash
ssh hassio 'sudo cp -r /tmp/tools/new/ps5-exploit-host /addons/'
# HA UI: Settings > Add-ons > Add-on Store > ⋮ > Check for updates
# -> Local add-ons -> PS5 Relapse Exploit Host -> Install -> Start
```

Verify: `nc -z <hassio-ip> 8082` and
`curl -k --resolve manuals.playstation.net:443:<hassio-ip> https://manuals.playstation.net/`
should return the `PS5-Relapse` page.

## Tools inside the container

The payload tools ship in the image at `/app/tools/` — see **`/app/TOOLS.md`**
inside the container for the full `docker exec` workflow:

```bash
sudo docker exec -it addon_e6c4340c_ps5_relapse_host bash
# then: nc -z -w 4 $PS5_HOST 9021; python3 /app/tools/send_payload.py; ...
```
