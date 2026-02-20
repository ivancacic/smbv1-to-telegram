# smbv1-to-telegram

A single Docker container that accepts scans from older printers via an SMBv1 share and forwards new scans to a Telegram bot.

It is designed for situations where the printer only supports SMBv1 for Scan to Network Folder.

## How it works

1. The container runs Samba with SMBv1 enabled and exposes a share (default: `scans`).
2. Your printer scans to that share.
3. A watcher process detects new files and sends them to Telegram as a document.
4. Successfully sent files are moved to `_sent`, failures are moved to `_failed`.

## Security warning

SMBv1 is insecure.

Use at your own risk and lock it down:
- Restrict access to the printer IP only using `PRINTER_IP`
- Put the printer and this container on an isolated VLAN if possible
- Do not expose SMB ports to the internet

## Container image

Publish using GitHub Actions to GHCR:

`ghcr.io/<your_github_user>/smbv1-to-telegram:latest`

## Unraid setup

### 1. Create the scans folder

Create a folder on Unraid, for example:

`/mnt/user/scans`

### 2. Add the container

In the Unraid Docker tab, add a container using the image:

`ghcr.io/<your_github_user>/smbv1-to-telegram:latest`

#### Ports

Expose these ports:
- 137 UDP
- 138 UDP
- 139 TCP
- 445 TCP

#### Volume mapping

- Host path: `/mnt/user/scans`
- Container path: `/scans`

#### Required environment variables

- `TELEGRAM_BOT_TOKEN` your Telegram bot token
- `TELEGRAM_CHAT_ID` the target chat id (DM or group)

#### Recommended environment variables

- `PRINTER_IP` your printer IP address (example `192.168.1.50`)
- `SMB_USER` default `scanner`
- `SMB_PASS` set a strong password

#### Optional environment variables

- `SMB_SHARE` default `scans`
- `SMB_PATH` default `/scans`
- `ALLOW_CIDR` optional extra allowlist (example `192.168.1.0/24`)
- `WORKGROUP` default `WORKGROUP`
- `CAPTION_PREFIX` default `New scan`
- `SCANS_DIR` default `/scans`
- `SENT_DIR` default `/scans/_sent`
- `FAILED_DIR` default `/scans/_failed`

## Printer configuration

On the printer, set Scan to Network Folder:
- Host: Unraid server IP address
- Share: `scans` (or whatever you set in `SMB_SHARE`)
- Username: `SMB_USER`
- Password: `SMB_PASS`

If the printer asks for a subfolder path, leave it blank.

## How to find your Telegram chat id

1. Send a message to your bot (or add it to a group and send a message).
2. Open this URL in a browser, replacing the token:

`https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`

3. In the JSON, find `chat` then `id`. Use that number as `TELEGRAM_CHAT_ID`.

## Build locally

```bash
docker build -t smbv1-to-telegram:local .
docker run --rm -it \
  -e TELEGRAM_BOT_TOKEN=xxx \
  -e TELEGRAM_CHAT_ID=123 \
  -e PRINTER_IP=192.168.1.50 \
  -v "$(pwd)/scans:/scans" \
  -p 137:137/udp -p 138:138/udp -p 139:139 -p 445:445 \
  smbv1-to-telegram:local
