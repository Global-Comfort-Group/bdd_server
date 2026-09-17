# Production deployment config — copies of record

**These are copies, not the live files.** Editing anything here changes nothing on the
server. Captured from `10.100.100.88` on 17 September 2026.

## Why this directory exists

`/opt/bdd-git` on the production host is **not a git repository**. It is a plain
directory holding two separate checkouts side by side:

```
/opt/bdd-git/backend/    -> this repo (bdd_server)
/opt/bdd-git/frontend/   -> bdd_client
```

Everything at that top level therefore sits **outside both repositories** and existed in
exactly one place — a production server with no off-site backup — until these copies were
made. The application source was safe on GitHub; the knowledge of how to build, serve and
deploy it was not.

## ⚠️ The repo-root `docker-compose.yml` is STAGING, not production

This repository already tracks a `docker-compose.yml` at its root. **It is a different
file with a different job.** Do not confuse them:

| | repo root `docker-compose.yml` | `deploy/production/docker-compose.yml` |
|---|---|---|
| Services | 1 — `backend` only | 4 — `db`, `backend`, `frontend`, `nginx` |
| Container names | `bdd-backend-staging` | `bdd-*-local` |
| Env file | `.env.staging` | `./backend/.env` |
| Ports | publishes `8000:8000` | backend unpublished; nginx fronts 80/443 |
| Uploads | `./uploads` | `/opt/bdd-data/uploads` |

## Why the live compose file cannot simply live in this repo

`docker-compose.yml` uses **relative** paths — build contexts `./backend` and
`./frontend`, `env_file: ./backend/.env`, and mounts `./nginx/bdd.conf` and
`./certbot/...`. Those resolve against the compose project directory, which is
`/opt/bdd-git`.

Moving the live file into this repo, or symlinking it from a subdirectory, risks changing
how those paths resolve and would break the mounts. So the live file stays at
`/opt/bdd-git/docker-compose.yml` and this is a copy.

**That means this copy can drift.** Treat the server as authoritative and re-verify before
relying on anything here.

## Contents

| File | Live path on `.88` | What it is |
|---|---|---|
| `docker-compose.yml` | `/opt/bdd-git/docker-compose.yml` | The whole 4-container stack, healthcheck ordering, networks, bind mounts |
| `nginx-bdd.conf` | `/opt/bdd-git/nginx/bdd.conf` | Reverse proxy and TLS termination. **Route order is load-bearing** — see below |
| `deploy.sh` | `/opt/bdd-git/deploy.sh` | 479-line deploy: preflight → backup → pull → build → migrate → swap → verify, with rollback |
| `certbot-auth.sh` | `/opt/bdd-git/certbot/hooks/auth.sh` | Certificate renewal hook. **Its header comment is the renewal runbook** |
| `certbot-cleanup.sh` | `/opt/bdd-git/certbot/hooks/cleanup.sh` | Companion cleanup hook |

## `nginx-bdd.conf` — the route ordering matters

The location blocks are order-dependent. `/api/auth/` must be matched **before** `/api/`,
because NextAuth routes go to the frontend while everything else under `/api/` goes to the
backend:

```
/api/auth/       -> frontend:3000
/api/            -> backend:8000
/docs /redoc /openapi.json /files/  -> backend:8000
/                -> frontend:3000
```

Get that order wrong and **login breaks while everything else keeps working**, which is
the hardest kind of failure to spot.

## Certificate renewal is manual on this host

Read `certbot-auth.sh`'s header before touching certificates. In short: Let's Encrypt's
validators cannot reach this host's public IP, because the telecoms line filters inbound
traffic by source. HTTP-01 and TLS-ALPN-01 are therefore both impossible, and renewal uses
**DNS-01 with a TXT record added by hand at GoDaddy**.

The hook writes the challenge value to `pending.txt` and waits for an operator to create a
`proceed` file. It refuses to wait unless an `ARMED` file exists — without that guard the
nightly automatic attempt would hang for an hour every night.

These two hook files contain no secrets. That was verified by taking every value of 8+
characters from both `.env` files on the host and searching for each one in these files:
zero matches.

## What is deliberately NOT here

- **`.env` and `backend/.env`** — they hold live database credentials, `SECRET_KEY`, two
  Alibaba OSS keys, Resend and Google API keys. They must never enter a repository. They
  need their own protected storage.
- **The certificate and private key** — `certbot/conf/`. Sensitive, and reissuable via the
  procedure above.
- **`/opt/bdd-data/uploads`** — 1.1 GB of live user uploads. Data, not config.
- **`*.bak*` files and the prepared-but-unused Caddy migration** — no lasting value.
