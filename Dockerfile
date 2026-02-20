FROM debian:bookworm-slim

RUN apt-get update \
  && apt-get install -y --no-install-recommends samba samba-common-bin python3 python3-pip ca-certificates tini \
  && pip3 install --no-cache-dir watchdog requests \
  && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /scans /run/samba /var/lib/samba/private /var/log/samba

COPY forwarder.py /app/forwarder.py
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 137/udp 138/udp 139/tcp 445/tcp

ENTRYPOINT ["/usr/bin/tini","--"]
CMD ["/entrypoint.sh"]
