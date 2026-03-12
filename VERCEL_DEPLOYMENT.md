# Vercel Deployment Guide for Flask + Static Frontend

1. Make sure your backend entry point is at `ffend/backend/app.py` and your frontend static files are in `ffend/`.
2. The `vercel.json` file is configured to route `/api/*` to your Flask backend and all other routes to your frontend.
3. The `.vercelignore` file ensures unnecessary files are not uploaded.
4. The `vercel-build.config` and `Procfile` help with build and run commands.
5. Add your environment variables (like API keys) in the Vercel dashboard, not in `.env`.
6. Deploy by running:

```
vercel --prod
```

or connect your GitHub repo to Vercel for automatic deployments.

---

For custom domains, environment variables, or advanced routing, see the Vercel docs.
