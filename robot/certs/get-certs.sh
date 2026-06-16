#!/bin/bash
# Check if the cert is missing or older than 60 days
if [[ ! -f /etc/morph/certs/fullchain.pem ]] || [[ $(find /etc/morph/certs/fullchain.pem -mtime +60) ]]; then
    curl -H "X-MORPH-KEY: ${ROBOT_AUTH_KEY}" \
         https://certs.76500000.xyz \
         -o /tmp/certs.json
    
    # Use jq to parse the JSON and decode the Base64 back into .pem files
    cat /tmp/certs.json | jq -r '.cert' | base64 -d > /etc/morph/certs/fullchain.pem
    cat /tmp/certs.json | jq -r '.key' | base64 -d > /etc/morph/certs/privkey.pem
fi