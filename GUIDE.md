# PS5 Relapse jailbreak — comprehensive guide (day-to-day)

Everything about the setup on this network: what was done, how, current status,
how to use it daily, backup/load of your own discs, and what is still optional.
Companion files: `TOOLS.md` (per-tool commands), `PLAN.md` (design), `CONTEXT.md`
(network/cert notes).

---

## 1. What this is

A tethered jailbreak of a PS5 (firmware 13.40) using the public **Relapse** exploit
chain (WebKit bug + `aio_multi_wait` kernel UAF; supports FW 7.00–13.60, PS5 & Pro).
The exploit page is served from a **Home Assistant add-on on the hassio server**
(10.11.12.98), fronted by the **nginx add-on** under the hostname
`manuals.playstation.net` (what the PS5 User's Guide loads). pfSense DNS points
that hostname at hassio and blocks Sony firmware update servers.

```
PS5 (10.11.12.74)
  │  User's Guide → https://manuals.playstation.net  (SNI manuals.playstation.net)
  │  pfSense DNS host override: manuals.playstation.net → 10.11.12.98
  ▼
hassio:443 nginx addon (core_nginx_proxy)
  │  custom server block /usr/share/hassio/share/nginx/nginx_proxy/ps5-relapse.conf
  │  self-signed cert /usr/share/hassio/ssl/manuals_{fullchain,privkey}.pem
  ▼  proxy_pass http://10.11.12.98:8082
Relapse add-on container (host_network) → /app/relapse (exploit site) on host :8082
```

## 2. Status quo (what is running right now)

| Component | State | Where |
|---|---|---|
| Add-on `ps5_relapse_host` | installed, **started**, `boot: auto`, v1.4.0 | hassio; repo `github.com/override80/ps5-relapse-host-addon`; staging copy `/tmp/tools/new/ps5-exploit-host/` |
| Container | `app_e6c4340c_ps5_relapse_host`, host ports **8082**/8444 | `sudo docker ps` on hassio |
| nginx server block | `/usr/share/hassio/share/nginx/nginx_proxy/ps5-relapse.conf` | hassio (host path) = `/share/nginx_proxy/` in container |
| Self-signed cert | `/usr/share/hassio/ssl/manuals_fullchain.pem` + `manuals_privkey.pem` (CN=manuals.playstation.net) | hassio |
| pfSense host override | id 7: `manuals.playstation.net → 10.11.12.98` | Services → DNS Resolver → Host Overrides |
| pfSense update block | id 0: domain override `update.playstation.net → 127.0.0.2` | Services → DNS Resolver → Domain Overrides |
| PS5 | 10.11.12.74 (DHCP reservation, MAC b4:1f:4d:f2:84:f8), FW 13.40 | pfSense DHCP static mapping `ps5` |

Verified working: `curl -k --resolve manuals.playstation.net:443:10.11.12.98 https://manuals.playstation.net/`
returns the PS5-Relapse page; port 80 also proxied.

## 3. Day-to-day routine (jailbreak is tethered — redo after every full boot)

1. PS5 boots → **wait 30–60 s idle** (13.40 kernel stage is much more reliable then).
2. PS5: **Settings → Guide and Tips, Health and Safety, Other Information → User's Guide**
   → accept the self-signed certificate prompt → wait for
   **`elfldr is listening on port 9021`** in the on-screen log.
3. From the hassio host, inside the add-on container:
   ```bash
   C=$(sudo docker ps --format '{{.Names}}' | grep ps5_relapse)
   sudo docker exec -it "$C" bash
   export PS5_HOST=10.11.12.74
   nc -z -w 4 $PS5_HOST 9021 && echo "9021 OPEN" || echo "9021 CLOSED"
   python3 /app/tools/send_payload.py $PS5_HOST 9021 /app/tools/shsrv-ps5.elf   # shell :2323
   python3 /app/tools/send_payload.py $PS5_HOST 9021 /app/tools/kstuff.elf     # fpkg support — BEFORE etaHEN
   python3 /app/tools/send_payload.py $PS5_HOST 9021 /app/tools/etaHEN-2.5B.bin
   cd /app/tools/ps5-firmware-pin && python3 pin/ps5-fw-pin.py --host $PS5_HOST
   ```
4. PS5: **Settings → System → System Software and Updates → Automatic Downloads →
   System Software and Apps → Off** (once). If an update screen ever appears, press ✕.

Troubleshooting: `unexpected oid state` / hang at `checking aio groups` / kernel panic
→ hard-reset the PS5 (hold power ~10 s) and retry. If the guide shows 404, the add-on
is down (`ha apps info e6c4340c_ps5_relapse_host` on hassio; restart if needed).

## 4. Backing up your own disc games

Only dump discs you own. Keep the console offline.

1. Plug an **exFAT USB drive** into the PS5.
2. Send the dumper and drive it from a browser:
   ```bash
   python3 /app/tools/send_payload.py $PS5_HOST 9021 /app/tools/ps5-app-dumper_v2.10.elf
   # open http://$PS5_HOST:8081 on PC/phone, pick the running title + the USB drive, Start
   ```
   The dump lands as a **per-title folder at the USB root** (dumper is USB-only,
   no network transfer).
3. Move files around with the file managers (below) or by unplugging the USB.

**Folder map:**

| What | Where |
|---|---|
| Disc dumps (output of ps5-app-dumper) | USB root, per-title folder (exFAT drive in the PS5) |
| `.fpkg` to install | **USB root** → etaHEN package installer (or ItemzFlow PKG installer) |
| Folder-format PS5 game dumps (internal) | `/data/etaHen/games/` |
| PS4 FPKG / PS5 DLC FPKG (internal) | `/data/etaHen/pkgs/` |
| USB mounts on the console | `/mnt/...` (visible via websrv/ftpsrv/shsrv) |

## 5. Loading backups

1. Jailbroken with **kstuff + etaHEN** loaded (kstuff 1.15+ is required for fpkg on
   FW > 11.60 — we ship v1.6.7).
2. Put the `.fpkg` at the **USB root** (exFAT) → on the PS5 use etaHEN's package
   installer (Settings → etaHEN / PKG prompt). Or place folder dumps in
   `/data/etaHen/games` via FTP/websrv.
3. The game appears on the home screen → launch. Game must require FW ≤ 13.40.
4. fpkg backups are fake-signed → they install on **any** jailbroken PS5, so moving
   to a PS5 Pro later = copy the files (USB/FTP) + install there.
5. Save data: Settings → Saved Data and Game/App Settings → Saved Data (PS5) →
   Copy to USB (works without jailbreak); restore on the new console. Or
   etaHEN/ItemzFlow save backup.

## 6. File transfer / file manager

```bash
python3 /app/tools/send_payload.py $PS5_HOST 9021 /app/tools/websrv-ps5.elf  # HTTP file manager :8084
python3 /app/tools/send_payload.py $PS5_HOST 9021 /app/tools/ftpsrv-ps5.elf  # FTP :2121 (full fs)
# shsrv shell: telnet $PS5_HOST 2323
```

## 7. Tools reference (all in `/app/tools/`, see TOOLS.md for details)

| Tool | Use |
|---|---|
| `webkit-autoloader-installer_v0.8.4.elf` | one-time: installs WebKit Autoloader pkg → exploit auto-runs at boot; add kstuff+etaHEN to `/data/ps5_autoloader/autoload.txt` |
| `pldmgr_v0.6.3.elf` | Payload Manager web UI on :8084 (send payloads from browser) |
| `ps5debug-NG_v1.3.2.elf` | debug settings menu |
| `CheatRunner_v0.18.1.elf` | game trainers (game must be running) |
| `ps5-backpork.elf` | load PS4 fpkgs on PS5 |
| `klogsrv-ps5.elf` | kernel log server |
| ItemzFlow `.pkg` | backup manager UI — download from https://pkg-zone.com/details/ITEM00001, install via etaHEN |
| ps5upload | phone/PC app to push games/payloads: github.com/phantomptr/ps5upload |
| websrv homebrew zips | emulators (CrispyDoom, DevilutionX, EDuke32, FBNeo, FFplay, LakeSnes…) in ps5-payload-dev/websrv releases |
| `replace_icon.elf` / `themes_ps.elf` | home-screen icons/themes (Master-s/PS5-Payloads releases) |

## 8. pfSense rules (and how to disable)

- **Firmware update block**: Services → DNS Resolver → **Domain Overrides**, id 0:
  `update.playstation.net → 127.0.0.2`. Blocks every `*.update.playstation.net`
  (PS3/PS4/PS5/Vita system updates). Game/controller content (store/CDN hosts)
  is NOT blocked — verified. Disable: delete the entry → Apply.
- **Exploit redirect**: Services → DNS Resolver → **Host Overrides**, id 7:
  `manuals` / `playstation.net → 10.11.12.98`.
- The pin script additionally removes any downloaded `/update/PS5UPDATE.PUP`.

## 9. PS5 Pro / factory reset

- Pro must already be on FW ≤ 13.60 (14.x = no public exploit, no general downgrade).
  Never update it. New console → new IP → update DHCP reservation + `PS5_HOST`.
- Factory reset wipes `/data` (keep dumps on USB); FW unchanged → still jailbreakable;
  re-run the day-to-day routine. hassio side needs no changes.

## 10. Optional / left to do

- Install WebKit Autoloader + Payload Manager (removes manual per-boot steps).
- Install ItemzFlow pkg; ps5debug-NG; CheatRunner; BackPork; emulators; themes.
- `--full` pin (edits console `/etc/hosts`) — needs kstuff/etaHEN loaded first.
- Consider updating 13.40 → 13.60 via USB (more stable per scene reports;
  one-way; still exploitable) — see `tools/ps5-firmware-pin/upgrade/README.md`.
- Rollback: delete pfSense overrides (ids 0 and 7), remove nginx conf + cert,
  uninstall add-on, `ps5-fw-unpin.py` on the PS5.

## 11. Safety notes

Dump/load only games you own. Stay offline (PSN requires FW 14.10 anyway).
Never confirm an update screen. The jailbreak is tethered and can crash the console —
expect occasional hard resets on 13.40.

## 12. AdGuard Home note (decision: PS5 stays on pfSense DNS)

- AdGuard Home (hassio, 10.11.12.98:53) has `upstream_dns: [10.11.12.254]`, so its
  clients still pass through the pfSense overrides above — the `update.playstation.net`
  block holds for AdGuard-listed devices too (verified: update hosts → 0.0.0.0 via AdGuard).
- BUT AdGuard's parental controls block the `playstation` service, so via AdGuard
  `manuals.playstation.net` → 0.0.0.0 and the exploit page would NOT load.
- **Decision: keep the PS5 on pfSense DNS (plain DHCP, no AdGuard mapping).**
  Do not add the PS5 to the AdGuard client list. If ever needed, add per-client
  allow rules in AdGuard instead:
  `@@||playstation.net^$client=10.11.12.74` and `@@||playstation.com^$client=10.11.12.74`.
- Never change AdGuard's upstream away from 10.11.12.254, or the pfSense overrides
  stop applying to AdGuard clients.
