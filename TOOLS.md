# PS5 exploit tools — inside this container

Enter the container from the hassio host:

```bash
sudo docker exec -it addon_e6c4340c_ps5_relapse_host bash
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
