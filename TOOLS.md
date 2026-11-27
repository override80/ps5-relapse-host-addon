# PS5 exploit tools — inside this container

Enter the container from the hassio host:

```bash
C=$(sudo docker ps --format '{{.Names}}' | grep ps5_relapse)
sudo docker exec -it "$C" bash
```

The container runs with `host_network: true`, so it reaches the PS5 directly.
Set the console IP once: `export PS5_HOST=10.11.12.74` (DHCP reservation; change if
the PS5 ever gets a different IP).

## Tool inventory (`/app/tools/`)

| File | What it does | Source |
|---|---|---|
| `send_payload.py` | push an ELF to elfldr on PS5 port 9021 (env: PS5_HOST/PS5_PORT/PS5_PAYLOAD) | this repo |
| `shsrv-ps5.elf` | telnet-like shell on PS5 port **2323** | ps5-payload-dev/shsrv |
| `kstuff.elf` (v1.6.7) | kernel patch enabling **fpkg** installs (1.15+ needed above FW 11.60) | EchoStretch/kstuff |
| `etaHEN-2.5B.bin` | homebrew enabler + package installer | etaHEN/etaHEN |
| `ps5-app-dumper_v2.10.elf` | dumps the inserted **disc** to a USB drive; web UI on PS5 :8081 | EchoStretch/ps5-app-dumper |
| `ftpsrv-ps5.elf` | FTP server on PS5 port **2121** (full filesystem) | ps5-payload-dev/ftpsrv |
| `websrv-ps5.elf` | HTTP **file manager** on PS5 port **8084** | ps5-payload-dev/websrv |
| `webkit-autoloader-installer_v0.8.4.elf` | installs the WebKit Autoloader pkg onto the console | itsPLK/ps5-webkit-autoloader |
| `pldmgr_v0.6.3.elf` | Payload Manager (web UI on :8084) to send payloads from a browser | itsPLK/ps5-payload-manager |
| `ps5debug-NG_v1.3.2.elf` | enables the debug settings menu | Pharaoh2k/ps5debug-NG |
| `CheatRunner_v0.18.1.elf` | game trainers/cheats | notmaj0r/CheatRunner |
| `ps5-backpork.elf` | load PS4 fpkgs on PS5 | BestPig/BackPork |
| `klogsrv-ps5.elf` | kernel log server | ps5-payload-dev/klogsrv |
| `elfldr-ps5-generic.elf` | fallback ELF loader if the bundled `elfldr-ps5-1360.elf` fails | ps5-payload-dev/elfldr |
| `ps5-firmware-pin/` | pin/unpin/downgrade scripts (talk to shsrv :2323) | lvndry/ps5-firmware-pin |

Not bundled (download when needed): ItemzFlow `.pkg` from
https://pkg-zone.com/details/ITEM00001 (backup manager UI), ps5upload phone/PC app
(github.com/phantomptr/ps5upload), websrv homebrew emulator zips (CrispyDoom,
DevilutionX, EDuke32, FBNeo, ... in ps5-payload-dev/websrv releases),
`replace_icon.elf` / `themes_ps.elf` (Master-s/PS5-Payloads releases).

## Per-boot routine

```bash
export PS5_HOST=10.11.12.74
# PS5: open User's Guide (manuals.playstation.net -> this host via nginx),
# accept the self-signed cert, wait for "elfldr is listening on 9021"
nc -z -w 4 $PS5_HOST 9021 && echo "9021 OPEN" || echo "9021 CLOSED"
python3 /app/tools/send_payload.py $PS5_HOST 9021 /app/tools/shsrv-ps5.elf
python3 /app/tools/send_payload.py $PS5_HOST 9021 /app/tools/kstuff.elf     # BEFORE etaHEN
python3 /app/tools/send_payload.py $PS5_HOST 9021 /app/tools/etaHEN-2.5B.bin
cd /app/tools/ps5-firmware-pin && python3 pin/ps5-fw-pin.py --host $PS5_HOST
```

13.40 kernel stage is flaky: on `unexpected oid state` or a hang at `checking aio
groups`, hard-reset the PS5 (hold power ~10 s) and retry.

## Backup & load your own disc games — exact folders

- **Dumping**: `ps5-app-dumper` writes **only to a USB drive plugged into the PS5**
  (exFAT). Send the elf, then open its web UI from any browser at
  `http://$PS5_HOST:8081`, pick the running title + destination drive, Start.
  The dump lands as a per-title folder at the **USB root** (e.g.
  `/<usb>/CUSAxxxxx/`). It does not stream over the network.
- **Installing a dumped .fpkg**: put the `.fpkg` at the **root of an exFAT USB**
  stick and use etaHEN's package installer (or ItemzFlow's PKG installer).
  On internal storage, folder-format PS5 dumps go to **`/data/etaHen/games/`**,
  PS4 FPKGs / PS5 DLC FPKGs go to **`/data/etaHen/pkgs/`** (move them there with
  websrv/ftpsrv/shsrv).
- **File manager for the exFAT USB**: `websrv-ps5.elf` (HTTP file manager on
  **:8084**) — browse/move/delete files on internal storage and mounted USB
  (`/mnt/...`). `ftpsrv-ps5.elf` gives the same over FTP on **:2121**.
  `shsrv` (shell on :2323) also works: `telnet $PS5_HOST 2323`.
- After installing, the game appears on the home screen — launch it.

```bash
python3 /app/tools/send_payload.py $PS5_HOST 9021 /app/tools/ps5-app-dumper_v2.10.elf
python3 /app/tools/send_payload.py $PS5_HOST 9021 /app/tools/websrv-ps5.elf
python3 /app/tools/send_payload.py $PS5_HOST 9021 /app/tools/ftpsrv-ps5.elf
```

## One-time: WebKit Autoloader + Payload Manager (auto-jailbreak at boot)

```bash
# once per console (after a successful jailbreak with kstuff+etaHEN loaded):
python3 /app/tools/send_payload.py $PS5_HOST 9021 /app/tools/webkit-autoloader-installer_v0.8.4.elf
# it installs the autoloader pkg on the console; afterwards the exploit auto-runs
# at boot (User's Guide page) and can auto-load payloads listed in
# /data/ps5_autoloader/autoload.txt (add kstuff.elf + etaHEN-2.5B.bin there)
python3 /app/tools/send_payload.py $PS5_HOST 9021 /app/tools/pldmgr_v0.6.3.elf
# Payload Manager web UI: http://$PS5_HOST:8084
```

## Other tools

```bash
python3 /app/tools/send_payload.py $PS5_HOST 9021 /app/tools/ps5debug-NG_v1.3.2.elf   # debug settings menu
python3 /app/tools/send_payload.py $PS5_HOST 9021 /app/tools/CheatRunner_v0.18.1.elf # trainers (needs a game running)
python3 /app/tools/send_payload.py $PS5_HOST 9021 /app/tools/ps5-backpork.elf        # PS4 fpkgs
python3 /app/tools/send_payload.py $PS5_HOST 9021 /app/tools/klogsrv-ps5.elf         # kernel logs
```

## Moving backups / PS5 Pro / factory reset

- fpkg backups are fake-signed: they install on **any** jailbroken PS5. Move `.fpkg`
  via USB (exFAT root) or FTP, install with etaHEN on the target console.
- Save data: Settings > Saved Data ... > Copy to USB (works without JB), or
  etaHEN/ItemzFlow save backup.
- PS5 Pro: Relapse covers PS5 + Pro on **7.00–13.60**; a new Pro must already be on
  ≤ 13.60 (14.x = no public exploit, no general downgrade). Never update it.
  New console = new IP -> update the DHCP reservation and PS5_HOST.
- Factory reset wipes /data (keep dumps on USB); firmware unchanged -> still
  jailbreakable; re-run the per-boot routine. The hassio side needs no changes.

## Firmware update protection (pfSense)

Console firmware updates are blocked at the DNS layer on pfSense:
**Services > DNS Resolver > Domain Overrides**: `update.playstation.net` ->
`127.0.0.2` (blocks every `*.update.playstation.net` host, PS3/PS4/PS5/Vita).
Game and controller updates use different hosts (`*.dl.playstation.net`, CDN) and
are NOT blocked. The pin script additionally deletes any downloaded
`/update/PS5UPDATE.PUP`. To disable the block: delete that domain override and
press Apply.
