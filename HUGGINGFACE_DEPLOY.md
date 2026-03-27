# 🚀 GitLab Compliance Checker - Hugging Face Spaces Deployment Guide

## Quick Deploy (5 minutes)

### Step 1: Create Hugging Face Account
If you don't have one:
👉 https://huggingface.co/join

### Step 2: Create New Space
1. Go to: https://huggingface.co/spaces
2. Click **"Create new Space"**
3. Fill in:
   - **Space name**: `gitlab-compliance-checker` (or your choice)
   - **License**: MIT
   - **SDK**: **Streamlit** ⭐ (Important!)
   - **Visibility**: Public or Private (your choice)
4. Click **"Create Space"**

### Step 3: Connect GitLab Repository

After creating the Space, you'll see options to add files. We'll push from GitLab:

```bash
cd /home/srilatha/gitlab-compliance-checker

# Add Hugging Face as remote
# Replace YOUR_USERNAME with your Hugging Face username
git remote add huggingface https://huggingface.co/spaces/YOUR_USERNAME/gitlab-compliance-checker

# Push to Hugging Face
git push -u huggingface newdemo
```

**Note:** Hugging Face will ask for credentials. Use:
- **Username**: Your Hugging Face username
- **Password**: Create a token at https://huggingface.co/settings/tokens

### Step 4: Add Environment Variables (GitLab Token)

1. Go to your Space page on Hugging Face
2. Click **"Settings"** tab
3. Scroll to **"Variables and secrets"**
4. Click **"New secret"**
5. Add these secrets:

| Name | Value |
|------|-------|
| `GITLAB_URL` | `https://gitlab.com` |
| `GITLAB_TOKEN` | `your_gitlab_personal_access_token` |

**To get GitLab token:**
1. https://gitlab.com/-/profile/personal_access_tokens
2. Create token with scopes: `api`, `read_api`, `read_user`
3. Copy the token
4. Paste in Hugging Face Secrets

### Step 5: Wait for Build 🕐

- Hugging Face will automatically build your app
- Takes 2-5 minutes
- You'll see "Building" → "Running" status
- Click **"Open App"** when ready!

---

## Your App URL

```
https://huggingface.co/spaces/YOUR_USERNAME/gitlab-compliance-checker
```

---

## Auto-Deploy on Push

Every time you push to the `newdemo` branch:

```bash
git push huggingface newdemo
```

Hugging Face will automatically rebuild and redeploy your app! 🎉

---

## Testing Your Deployed App

Once deployed, test all modes:

1. ✅ **Check Project Compliance** - Enter project URL
2. ✅ **User Profile Overview** - Enter username
3. ✅ **Team-wise Productivity** - Select team → Use "Ultra" mode
4. ✅ **Batch 2026 ICFAI** - Run batch (now 5-8x faster!)
5. ✅ **Batch 2026 RCTS** - Run batch

---

## Troubleshooting

### App Shows Error on Startup
- Check **"Logs"** tab in your Space
- Verify `requirements.txt` is correct
- Make sure `app.py` exists in root directory

### GitLab API Errors
- Verify GitLab token in Secrets is correct
- Check token has scopes: `api`, `read_api`, `read_user`
- Ensure token hasn't expired

### App is Slow
- Use "Ultra" mode for Team Productivity
- Batch modes are optimized (10 parallel workers)
- Check Hugging Face logs for any errors

---

## Upgrade Resources (If Needed)

If your app needs more resources:
1. Go to Space Settings
2. **"Hardware"** section
3. Choose upgrade (free tier is usually sufficient)

---

## Share Your App

Share the URL with your team:
```
https://huggingface.co/spaces/YOUR_USERNAME/gitlab-compliance-checker
```

Users will need their own GitLab tokens to use the app.

---

## Cost

**FREE!** Hugging Face Spaces free tier includes:
- ✅ Unlimited public spaces
- ✅ 16GB RAM
- ✅ 2 vCPU
- ✅ Auto-deploy on git push
- ✅ Community support

---

## Need Help?

- **Hugging Face Docs**: https://huggingface.co/docs/hub/spaces-sdks-streamlit
- **Streamlit Docs**: https://docs.streamlit.io
- **Check Logs**: Settings → Logs tab in your Space

---

**Happy Deploying! 🎊**

Your GitLab Compliance Checker will be live on Hugging Face in minutes!
