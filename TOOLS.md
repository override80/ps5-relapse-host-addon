# PS5 exploit tools — inside this container

Enter the container from the hassio host:

```bash
C=$(sudo docker ps --format "{{.Names}}" | grep ps5_relapse)
sudo docker exec -it "$C" bash
```

(The container runs with `host_network: true`, so it reaches the PS5 directly.)

## Layout

```
/app/relapse/    exploit site served on host ports 8082/8444 (behind nginx)
/app/tools/
├── send_payload.py            # push an ELF to the PS5 elfldr (port 9021)
├── shsrv-ps5.elf              # shell server payload -> PS5 port 2323
├── elfldr-ps5-generic.elf     # fallback loader if payloads/elfldr-ps5-1360.elf fails
└── ps5-firmware-pin/          # lvndry/ps5-firmware-pin (pin / unpin / downgrade)
```

## Per-boot routine (run inside the container)

```bash
export PS5_HOST=10.11.12.74          # PS5 DHCP reservation

# 1. PS5 side: open User's Guide (manuals.playstation.net -> this host via
#    nginx), accept the self-signed cert, wait for "elfldr is listening on 9021"

# 2. verify elfldr, then load shsrv (shell on 2323)
nc -z -w 4 $PS5_HOST 9021 && echo "9021 OPEN" || echo "9021 CLOSED"
python3 /app/tools/send_payload.py                 # sends shsrv-ps5.elf
nc -z -w 4 $PS5_HOST 2323 && echo "2323 OPEN" || echo "2323 CLOSED"

# 3. pin the firmware (deletes any downloaded PS5UPDATE.PUP; --full also
#    edits /etc/hosts but needs kstuff/etaHEN loaded first)
cd /app/tools/ps5-firmware-pin
python3 pin/ps5-fw-pin.py --host $PS5_HOST --dry-run
python3 pin/ps5-fw-pin.py --host $PS5_HOST
```

Send any other payload the same way:

```bash
python3 /app/tools/send_payload.py $PS5_HOST 9021 /path/to/payload.elf
```

## Notes

- PS5 firmware supported by Relapse: 7.00–13.60. On 13.40 the kernel stage is
  flaky: on `unexpected oid state` or a hang at `checking aio groups`, hard-reset
  the PS5 (hold power ~10 s) and retry.
- The jailbreak is tethered: re-run the User's Guide page after every full boot.
- Firmware updates are blocked network-wide (pfSense DNS override
  `update.playstation.net`); the pin script additionally cleans `/update`.
- On the PS5 also set: Settings > System > System Software and Updates >
  Automatic Downloads > System Software and Apps > Off.
- Undo the pin: `python3 pin/ps5-fw-unpin.py --host $PS5_HOST`

## Backup & load your own disc games

Payloads in `/app/tools/`: `kstuff.elf` (v1.6.7 — enables fake packages; 1.15+ is
required on firmware above 11.60, so needed on 13.40), `etaHEN-2.5B.bin`
(homebrew enabler + package installer), `ps5-app-dumper_v2.10.elf` (disc dumper).

```bash
export PS5_HOST=10.11.12.74

# 1. jailbreak via User's Guide (wait for "elfldr is listening on 9021"), then:
python3 /app/tools/send_payload.py $PS5_HOST 9021 /app/tools/shsrv-ps5.elf

# 2. kstuff FIRST (fpkg support), then etaHEN:
python3 /app/tools/send_payload.py $PS5_HOST 9021 /app/tools/kstuff.elf
python3 /app/tools/send_payload.py $PS5_HOST 9021 /app/tools/etaHEN-2.5B.bin

# 3. insert your disc and dump it (follow the on-screen prompts; dump to an
#    external USB HDD for large games — the fpkg lands in /data or on USB):
python3 /app/tools/send_payload.py $PS5_HOST 9021 /app/tools/ps5-app-dumper_v2.10.elf

# 4. install the dumped .fpkg on the PS5 via etaHEN's package installer
#    (Settings > etaHEN, or the PKG install prompt / USB). The game then
#    appears on the home screen — launch it.
```

Notes: only dump/load discs you own; keep the console offline; the game must
require firmware <= 13.40; everything is tethered — after each full boot re-run
the User's Guide page and re-send kstuff + etaHEN before installing/launching
fpkg. Optional: ItemzFlow (LightningMods/ItemzFlow .pkg) is a full backup
manager if you prefer a UI over ps5-app-dumper.

## File transfer: FTP and web file manager

```bash
# ftpsrv: FTP server on the PS5, port 2121 (full filesystem access)
python3 /app/tools/send_payload.py $PS5_HOST 9021 /app/tools/ftpsrv-ps5.elf
# then from the Mac: any FTP client -> ftp://$PS5_HOST:2121

# websrv: HTTP file manager on port 8084 -> browse http://$PS5_HOST:8084
python3 /app/tools/send_payload.py $PS5_HOST 9021 /app/tools/websrv-ps5.elf
```

## Moving backups, PS5 Pro, factory reset

- **fpkg backups are fake-signed: they install on ANY jailbroken PS5** (no
  per-console license binding). Move the `.fpkg` files via USB (exFAT) or FTP,
  then install with etaHEN's package installer on the target console.
- **Save data**: Settings > Saved Data and Game/App Settings > Saved Data (PS5) >
  Copy to USB Storage Device (works without jailbreak); restore on the new console.
  Or use etaHEN / ItemzFlow save backup.
- **PS5 Pro**: Relapse covers PS5 and PS5 Pro on firmware 7.00-13.60. A new Pro must
  ALREADY be on <= 13.60 — 14.x has no public exploit and no general downgrade path.
  Check Settings > System > System Software BEFORE anything else, and never update
  (the pfSense DNS block + pin protect you). New console = new IP: update the DHCP
  reservation (or set a manual IP) and change PS5_HOST everywhere.
- **Factory reset**: wipes /data (keep dumps on USB!), firmware is unchanged so it
  stays jailbreakable; afterwards just re-run the per-boot routine. The hassio side
  (nginx server block + addon + pfSense DNS override) is console-agnostic — no changes.

## Other tools worth exploring

- **WebKit Autoloader + Payload Manager** (itsPLK): auto-runs the exploit at boot and
  auto-loads kstuff/etaHEN — removes the manual per-boot steps.
- **ItemzFlow** (.pkg, LightningMods): backup manager UI — dump/install games, saves.
- **ps5debug / ps5debug-NG**: enables the debug settings menu.
- **CheatRunner**: game trainers/cheats. **BackPork**: load PS4 fpkgs on PS5.
- **klogsrv**: kernel log server. **ps5upload** (phantomptr): phone/PC app to send
  games & payloads and manage the console.
- **websrv homebrew zips** (in its releases): emulators — CrispyDoom, DevilutionX,
  EDuke32, FBNeo, FFplay, LakeSnes, ... install via etaHEN's package installer.
- **replace_icon.elf / etaHEN themes**: home-screen icon customization.
