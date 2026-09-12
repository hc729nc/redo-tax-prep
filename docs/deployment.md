# Deploying a live, shared instance

This app is packaged as a single Docker image (see [`../Dockerfile`](../Dockerfile)):
one process serves both the API and the built frontend, and uses SQLite + local
file storage on a persistent volume. These steps use [Railway](https://railway.app)
(free tier, persistent volumes, no CLI needed - deploys straight from GitHub),
but any host that supports a Dockerfile + a persistent volume works the same way.

## Before you deploy

This app now has **real, public-facing user accounts** (email + password) so
different people's tax data stays private to them - every tax return is scoped to
the account that created it, and every API route checks that before returning
anything. A daily per-user usage cap (chat messages and uploads) protects against
runaway Anthropic API costs from a single account, but there's no email
verification, so a determined person could still create multiple accounts. This is
appropriate for a small public demo, not a production identity system - don't
point this at a large audience without revisiting that.

## Steps

1. **Push your latest code to GitHub** (if you haven't already):
   ```
   git push
   ```

2. **Go to [railway.app](https://railway.app) and sign in with GitHub.**

3. **New Project → Deploy from GitHub repo → select your `redo-tax-prep` repo.**
   Railway will detect the `Dockerfile` at the repo root automatically and build it.

4. **Add a persistent volume** (Settings → Volumes → New Volume). Mount it at
   `/data`. Without this, SQLite and uploaded files disappear on every redeploy.

5. **Set environment variables** (Settings → Variables):
   | Variable | Value |
   |---|---|
   | `ANTHROPIC_API_KEY` | your key from console.anthropic.com |
   | `SECRET_KEY` | a random value - generate with `python -c "import secrets; print(secrets.token_hex(32))"` |
   | `COOKIE_SECURE` | `true` |
   | `DATABASE_URL` | `sqlite:////data/synthia.db` |
   | `STORAGE_ROOT` | `/data/uploads` |

   (`ALLOWED_ORIGINS` isn't needed - the frontend is served same-origin by the
   same process, so CORS doesn't come into play.)

6. **Generate a public domain**: Settings → Networking → Generate Domain.

7. Railway redeploys automatically on every push to your main branch after this.

## Updating the live site

Just `git push` - Railway rebuilds and redeploys from the Dockerfile automatically.
Your data (SQLite DB + uploaded files) persists across deploys as long as the
volume stays attached.
