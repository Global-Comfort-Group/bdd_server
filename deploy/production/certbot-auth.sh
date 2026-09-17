#!/bin/bash
# certbot manual-auth-hook for bdd.hotelsogo.com
#
# WHY MANUAL: Let's Encrypt's validators cannot reach 103.16.169.123 - the
# Radius Telecoms line filters inbound traffic by source (added Aug 2026 after
# an SSH brute-force campaign, and it is working as intended). HTTP-01 and
# TLS-ALPN-01 are therefore both impossible. DNS-01 with a hand-added TXT
# record at GoDaddy is the chosen route. A scoped DNS API key was declined
# because GoDaddy keys are all-or-nothing over the whole domain.
#
# HOW IT WORKS: this hook writes the challenge value to pending.txt for a human
# to add at GoDaddy, then waits for an operator to confirm by creating
# "proceed". It does not query DNS itself - the box has no dig/nslookup/host.
#
# ARMING: it refuses to wait unless "ARMED" exists. Without that guard the
# nightly automatic renewal (which starts attempting around 14 Nov) would hang
# for an hour every single night. Armed runs are deliberate, operator-driven.
#
# TO RENEW (roughly every 90 days, next due ~10 December 2026):
#   sudo touch   /opt/bdd-git/certbot/hooks/ARMED
#   sudo certbot renew --config-dir /opt/bdd-git/certbot/conf \
#        --work-dir /opt/bdd-git/certbot/work \
#        --logs-dir /opt/bdd-git/certbot/logs --force-renewal
#   # read the value:  sudo cat /opt/bdd-git/certbot/hooks/pending.txt
#   # sysadmin EDITS the existing _acme-challenge.bdd TXT record at GoDaddy
#   # verify it published, then:
#   sudo touch   /opt/bdd-git/certbot/hooks/proceed
#   # afterwards:
#   sudo rm -f   /opt/bdd-git/certbot/hooks/ARMED

D=/opt/bdd-git/certbot/hooks
rm -f "$D/proceed"

{
  echo "RECORD NAME : _acme-challenge.${CERTBOT_DOMAIN}"
  echo "RECORD TYPE : TXT"
  echo "RECORD VALUE: ${CERTBOT_VALIDATION}"
  echo "TTL         : 600"
  echo "REQUESTED AT: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
  echo ""
  echo "Edit the existing _acme-challenge.bdd TXT record at GoDaddy to this"
  echo "value, wait for it to publish, then run:"
  echo "  sudo touch $D/proceed"
} > "$D/pending.txt"
chmod 644 "$D/pending.txt"

if [ ! -f "$D/ARMED" ]; then
  echo "NOT ARMED - refusing to wait. This is an unattended renewal attempt." >&2
  echo "bdd.hotelsogo.com needs a MANUAL DNS-01 renewal. See $D/auth.sh header." >&2
  exit 1
fi

# Armed: wait up to 60 minutes. GoDaddy takes 5-15 minutes to publish.
for i in $(seq 1 360); do
  if [ -f "$D/proceed" ]; then
    sleep 5
    exit 0
  fi
  sleep 10
done

echo "auth hook timed out after 60 minutes waiting for $D/proceed" >&2
exit 1
