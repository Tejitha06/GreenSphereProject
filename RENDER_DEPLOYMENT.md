# Render Deployment Guide for Flask Backend

1. Make sure your backend entry point is at `ffend/backend/run.py` and your `app` object is exposed in that file.
2. The `Procfile` is set to use gunicorn: `web: gunicorn run:app`
3. The `.renderignore` file ensures secrets and unnecessary files are not uploaded.
4. The `render.yaml` provides service configuration (optional, but recommended for infrastructure-as-code).
5. Add your environment variables (like API keys) in the Render dashboard, not in `.env`.
6. Deploy by connecting your GitHub repo to Render and creating a new Web Service with root directory `ffend/backend`.

---

For custom domains, environment variables, or advanced settings, see the Render docs.
