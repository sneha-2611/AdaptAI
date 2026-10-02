# 🚀 AdaptAI Cloud Hosting & Deployment Guide

This project is pre-configured for **1-click cloud deployment** on **Render**, **Railway**, and **Vercel**.

---

## Option 1: Deploy on Render (Recommended & Free)

Render provides a 100% free web service tier that works seamlessly with Flask, SQLite, and Gunicorn.

### Step 1: Push code to GitHub
Run these commands in your PowerShell / Terminal:
```powershell
# If you haven't linked your GitHub repository yet:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

### Step 2: Deploy on Render
1. Go to **[https://dashboard.render.com](https://dashboard.render.com)** and sign in with GitHub.
2. Click **New +** $\to$ **Web Service**.
3. Select your repository.
4. Render will automatically detect the settings from `render.yaml` or fill them in as:
   * **Name:** `adaptai`
   * **Environment:** `Python 3`
   * **Build Command:** `pip install -r requirements.txt`
   * **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT`
   * **Instance Type:** `Free`
5. Click **Deploy Web Service**!
6. In about 60 seconds, you will receive a live public URL (e.g. `https://adaptai.onrender.com`).

---

## Option 2: Deploy on Railway (Fastest)

1. Go to **[https://railway.app](https://railway.app)**.
2. Click **New Project** $\to$ **Deploy from GitHub repo**.
3. Select this repository.
4. Railway will automatically detect the `Procfile` and deploy it instantly with a public `.up.railway.app` URL.

---

## Option 3: Deploy on Vercel

The project includes `vercel.json` for Vercel deployment:
1. Install Vercel CLI (optional) or connect your GitHub repository at **[https://vercel.com](https://vercel.com)**.
2. Click **Add New Project** $\to$ Import your GitHub repository.
3. Vercel will read `vercel.json` and deploy it serverless.

---

## Production Files Included in this Repo:
* `Procfile`: Gunicorn WSGI startup configuration.
* `render.yaml`: Blueprint configuration for Render.
* `runtime.txt`: Standard Python 3.11/3.13 runtime specifier.
* `vercel.json`: Serverless routing configuration.
* `requirements.txt`: Includes production `gunicorn>=21.2.0`, `flask`, `python-dotenv`, `requests`.
* `test_pipeline.py`: Automated CI verification test script (14/14 tests passing).
