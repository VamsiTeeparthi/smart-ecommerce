# Deploy for free: Neon (database) + Render (backend) + Vercel (frontend)

## 1. Push to GitHub
Create a GitHub repo and push the whole `smart-ecommerce` folder (it contains `backend/` and `frontend/`).

## 2. Neon (database)
1. Sign up at https://neon.com and create a project.
2. Click **Connect** and copy the connection string (`postgresql://...?sslmode=require`).

## 3. Render (backend)
New > Web Service > connect your repo, then:
- Root Directory: `backend`
- Runtime: Python 3
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Instance Type: Free
- Environment variables:
  - `DATABASE_URL` = your Neon connection string
  - `SECRET_KEY` = a long random string
  - `CORS_ORIGINS` = `http://localhost:5173` (update after step 4)
  - `PYTHON_VERSION` = `3.12.3` (if the build picks a wrong Python)

Check `https://YOUR-BACKEND.onrender.com/api/health` returns `{"status":"ok"}`.

## 4. Vercel (frontend)
New Project > import the repo, then:
- Root Directory: `frontend`
- Framework: Vite
- Environment variable: `VITE_API_URL` = `https://YOUR-BACKEND.onrender.com` (no `/api`, no trailing slash)

## 5. Connect them
Back in Render, set `CORS_ORIGINS` to your Vercel URL (e.g. `https://your-app.vercel.app`) and redeploy.

## 6. Change demo passwords
Log in as admin@example.com / admin123 and replace the demo credentials before sharing publicly.
