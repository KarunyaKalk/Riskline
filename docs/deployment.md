# Hosting Guide: GitHub Pages Frontend + Render Backend

This guide details hosting the **Riskline** React frontend on **GitHub Pages** and the FastAPI backend + PostgreSQL + Redis stack on **Render**.

---

## 1. Render Backend Blueprint Setup (Automatic)

The codebase includes a native Render Blueprint specification file: [`render.yaml`](../render.yaml).

### Steps to Deploy Backend on Render:
1. Log in to [Render Dashboard](https://dashboard.render.com).
2. Click **New +** -> **Blueprint**.
3. Connect your GitHub repository `KarunyaKalk/Riskline`.
4. Render will automatically detect `render.yaml` and provision:
   - **`riskline-backend`**: Python FastAPI Web Service.
   - **`riskline-db`**: PostgreSQL Instance (with `pgvector` extension enabled).
   - **`riskline-redis`**: Managed Redis Instance.
5. Once deployed, copy your backend live URL: `https://riskline-backend.onrender.com`.

---

## 2. GitHub Pages Frontend Deployment (Automated CI/CD)

The repository includes a automated GitHub Actions workflow: [`.github/workflows/deploy-gh-pages.yml`](../.github/workflows/deploy-gh-pages.yml).

### Steps to Deploy Frontend to GitHub Pages:
1. Go to your GitHub Repository Settings (`https://github.com/KarunyaKalk/Riskline/settings/pages`).
2. Under **Build and deployment** -> **Source**, select **`gh-pages`** branch (or **GitHub Actions**).
3. Every push to the `main` branch automatically builds the production React application and publishes it to:
   **`https://karunyakalk.github.io/Riskline/`**

### Custom API Base URL:
If your Render backend URL differs from `https://riskline-backend.onrender.com`, update `VITE_API_BASE_URL` in `.github/workflows/deploy-gh-pages.yml`:
```yaml
env:
  VITE_API_BASE_URL: https://YOUR-RENDER-APP.onrender.com/api/v1
```

---

## 3. CORS Configuration
The backend automatically permits CORS credentials from GitHub Pages. In `render.yaml`:
```yaml
envVars:
  - key: CORS_ORIGINS
    value: https://karunyakalk.github.io,http://localhost:5173
```
