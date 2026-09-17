#!/bin/bash
# certbot manual-cleanup-hook for bdd.hotelsogo.com
#
# Deliberately does NOT remove the DNS record. Leaving it in place means the
# next renewal only requires the sysadmin to EDIT its value rather than create
# the record again - fewer steps and less to get wrong.
#
# It only clears the operator go-ahead flag so the next run starts clean.

rm -f /opt/bdd-git/certbot/hooks/proceed
exit 0
