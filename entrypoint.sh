#!/bin/sh
set -eu

: "${SMB_USER:=scanner}"
: "${SMB_PASS:=ChangeMe123!}"
: "${SMB_SHARE:=scans}"
: "${SMB_PATH:=/scans}"
: "${PRINTER_IP:=}"
: "${ALLOW_CIDR:=}"
: "${WORKGROUP:=WORKGROUP}"

: "${TELEGRAM_BOT_TOKEN:=}"
: "${TELEGRAM_CHAT_ID:=}"

: "${SCANS_DIR:=/scans}"
: "${SENT_DIR:=/scans/_sent}"
: "${FAILED_DIR:=/scans/_failed}"
: "${CAPTION_PREFIX:=New scan}"

mkdir -p "$SMB_PATH" "$SENT_DIR" "$FAILED_DIR"

if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$TELEGRAM_CHAT_ID" ]; then
  echo "TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set"
  exit 1
fi

ALLOW_LINE=""
if [ -n "$PRINTER_IP" ] && [ -n "$ALLOW_CIDR" ]; then
  ALLOW_LINE="hosts allow = ${PRINTER_IP} ${ALLOW_CIDR}"
elif [ -n "$PRINTER_IP" ]; then
  ALLOW_LINE="hosts allow = ${PRINTER_IP}"
elif [ -n "$ALLOW_CIDR" ]; then
  ALLOW_LINE="hosts allow = ${ALLOW_CIDR}"
fi

cat > /etc/samba/smb.conf <<EOF
[global]
  workgroup = ${WORKGROUP}
  server role = standalone server
  map to guest = never
  log file = /var/log/samba/log.%m
  max log size = 1000

  server min protocol = NT1
  client min protocol = NT1
  ntlm auth = yes
  lanman auth = yes

  ${ALLOW_LINE}
  hosts deny = 0.0.0.0/0

[${SMB_SHARE}]
  path = ${SMB_PATH}
  browseable = yes
  read only = no
  guest ok = no
  create mask = 0664
  directory mask = 0775
  valid users = ${SMB_USER}
EOF

if ! id "$SMB_USER" >/dev/null 2>&1; then
  useradd -M -s /usr/sbin/nologin "$SMB_USER"
fi

printf "%s\n%s\n" "$SMB_PASS" "$SMB_PASS" | smbpasswd -a -s "$SMB_USER"
smbpasswd -e "$SMB_USER"

echo "Starting Samba"
nmbd -D
smbd -F --no-process-group &
SMBD_PID=$!

echo "Starting forwarder"
exec python3 /app/forwarder.py
