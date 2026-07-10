#!/bin/sh
# One-time bootstrap for the very first TLS certificate on a fresh VPS.
# After this succeeds, the `certbot` service in docker-compose.prod.yml
# renews the certificate automatically — this script is not part of the
# steady-state stack and is not run again.
#
# Why this is needed (chicken-and-egg): the Nginx :443 server block
# (nginx/prod/templates/app.conf.template) references
# /etc/letsencrypt/live/$DOMAIN/*.pem, so Nginx refuses to start at all
# until a certificate already exists there — but Certbot's http-01
# challenge needs Nginx serving :80 to succeed. This script breaks the
# cycle: it creates a throwaway self-signed cert so Nginx can start, asks
# Certbot for the real one over that now-running :80 listener, then
# reloads Nginx to pick up the real certificate.
#
# Cannot be exercised end-to-end in this project's CI/dev sandbox: it
# requires a real domain name with DNS already pointed at the VPS's
# public IP, which only exists once this is run on the actual VPS. Its
# steps were verified individually (syntax check with `sh -n`, and each
# docker/certbot/openssl invocation is a standard, widely-documented
# pattern) but not as a live end-to-end run.
set -eu

: "${DOMAIN:?Set DOMAIN in .env first}"
: "${LETSENCRYPT_EMAIL:?Set LETSENCRYPT_EMAIL in .env first}"

COMPOSE="docker compose -f docker-compose.prod.yml"

echo "== 1/4: creating a throwaway self-signed cert so nginx can start =="
$COMPOSE run --rm --entrypoint sh certbot -c "
    mkdir -p /etc/letsencrypt/live/${DOMAIN} &&
    openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
        -keyout /etc/letsencrypt/live/${DOMAIN}/privkey.pem \
        -out /etc/letsencrypt/live/${DOMAIN}/fullchain.pem \
        -subj '/CN=${DOMAIN}'
"

echo "== 2/4: starting nginx =="
$COMPOSE up -d nginx

echo "== 3/4: requesting the real certificate from Let's Encrypt =="
$COMPOSE run --rm --entrypoint certbot certbot certonly \
    --webroot -w /var/www/certbot \
    -d "$DOMAIN" \
    --email "$LETSENCRYPT_EMAIL" \
    --agree-tos --no-eff-email --non-interactive

echo "== 4/4: reloading nginx with the real certificate =="
$COMPOSE exec nginx nginx -s reload

echo "Done. The 'certbot' compose service will keep this certificate renewed."
