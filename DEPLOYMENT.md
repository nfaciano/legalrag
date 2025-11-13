# LegalRAG Deployment Guide

## Quick Deploy (30 minutes)

### Step 1: Push to GitHub

```bash
cd C:\Users\nickf\OneDrive\Desktop\RagLaw
git add .
git commit -m "Ready for deployment"
git push
```

### Step 2: Deploy Backend to Railway

1. Go to https://railway.app
2. Click "Start a New Project" → "Deploy from GitHub repo"
3. Select `legalrag` repository
4. Railway will auto-detect it's a Python project
5. Click "Add variables" and set:
   - `GROQ_API_KEY` = `your_groq_api_key_here` (get from https://console.groq.com)
   - `FRONTEND_URL` = (leave blank for now, add after Vercel deploy)
6. Click "Deploy"
7. Wait 2-3 minutes
8. Go to "Settings" → "Networking" → "Generate Domain"
9. **Copy your backend URL** (e.g., `legalrag-production.up.railway.app`)

### Step 3: Deploy Frontend to Vercel

1. Go to https://vercel.com
2. Click "Add New..." → "Project"
3. Import your `legalrag` GitHub repository
4. Vercel will auto-detect it's a Vite app
5. **IMPORTANT:** Click "Configure Project"
6. Set "Root Directory" to: `frontend`
7. Add environment variable:
   - Name: `VITE_API_BASE_URL`
   - Value: `https://YOUR-RAILWAY-URL` (paste the Railway URL from Step 2)
8. Click "Deploy"
9. Wait 2-3 minutes
10. **Copy your frontend URL** (e.g., `legalrag.vercel.app`)

### Step 4: Update Railway CORS

1. Go back to Railway dashboard
2. Click on your deployment → "Variables"
3. Add new variable:
   - `FRONTEND_URL` = `https://YOUR-VERCEL-URL` (paste from Step 3)
4. Railway will auto-redeploy

### Step 5: Test It!

1. Go to your Vercel URL: `https://legalrag.vercel.app`
2. Upload a PDF
3. Search with AI Answer enabled
4. Should work end-to-end!

## Troubleshooting

**CORS errors:**
- Make sure `FRONTEND_URL` is set in Railway
- Check Railway logs for CORS errors
- Make sure URL doesn't have trailing slash

**Upload fails:**
- Check Railway logs
- Make sure `GROQ_API_KEY` is set
- Verify backend is running (visit `https://your-railway-url.app/`)

**Search returns no results:**
- Check if documents were uploaded successfully
- Look at browser console for errors
- Verify API URL is set correctly in Vercel

## URLs After Deployment

- **Frontend:** https://legalrag.vercel.app (or similar)
- **Backend:** https://legalrag-production.up.railway.app
- **API Docs:** https://legalrag-production.up.railway.app/docs

## Costs

- Railway: $5/month free credit (effectively free)
- Vercel: Free tier (more than enough)
- **Total: $0/month**

## Update Code Later

**Backend:**
```bash
git add legalrag/
git commit -m "Update backend"
git push
```
Railway auto-deploys on push.

**Frontend:**
```bash
git add frontend/
git commit -m "Update frontend"
git push
```
Vercel auto-deploys on push.

## Share Your App

Send this to your lawyer:
```
Check out what I built for legal research:
https://legalrag.vercel.app

Try uploading a deposition and asking questions about it.
The AI searches the entire document and gives you answers with exact page citations.
```

---

**You're live! 🚀**
