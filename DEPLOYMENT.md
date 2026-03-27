# 🚀 Deploy to Streamlit Cloud - Complete Guide

## Step-by-Step Deployment Instructions

### **Step 1: Push Your Code to GitLab/GitHub**

First, commit and push your changes:

```bash
cd /home/srilatha/gitlab-compliance-checker

# Check git status
git status

# Add all changes
git add .

# Commit
git commit -m "Prepare for Streamlit Cloud deployment"

# Push to newdemo branch
git push origin newdemo
```

---

### **Step 2: Go to Streamlit Cloud**

1. Open **https://streamlit.io/cloud**
2. Click **"Sign Up"** or **"Login"**
3. Login with your **GitHub** or **GitLab** account

---

### **Step 3: Create a New App**

1. Click **"+ New App"** button
2. Choose your repository:
   - **GitHub**: Select from your GitHub repos
   - **GitLab**: Connect your GitLab account and select repo

3. Configure your app:

| Setting | Value |
|---------|-------|
| **Main file path** | `app.py` |
| **Branch** | `newdemo` |
| **Python version** | `3.11` |

---

### **Step 4: Add Secrets (IMPORTANT!)**

In Streamlit Cloud dashboard for your app:

1. Click on your app name
2. Go to **"Settings"** → **"Secrets"**
3. Click **"Add Secret"**
4. Add these secrets:

```toml
# GitLab Configuration
GITLAB_URL = "https://gitlab.com"
GITLAB_TOKEN = "your_actual_gitlab_token_here"
```

**To get a GitLab token:**
1. Go to https://gitlab.com/-/profile/personal_access_tokens
2. Click **"Add new token"**
3. Give it a name (e.g., "Streamlit Compliance Checker")
4. Set expiration date
5. Select scopes: **`api`**, **`read_api`**, **`read_user`**
6. Click **"Create personal access token"**
7. **Copy the token immediately** (you won't see it again!)
8. Paste it in Streamlit Secrets

---

### **Step 5: Deploy!**

1. Click **"Save"** in the Secrets section
2. Go back to **"Settings"**
3. Click **"Restart App"**
4. Wait for deployment to complete (~2-5 minutes)
5. Click **"Open App"** to view your deployed app!

---

## **Advanced Configuration (Optional)**

### **Custom Domain**
In Settings → Custom Domain, you can add your own domain

### **Environment Variables**
For additional config, add in Settings → Environment Variables

### **Auto-Redeploy**
- Enabled by default
- Automatically redeploys when you push to `newdemo` branch
- Can be disabled in Settings

---

## **Troubleshooting**

### **App Won't Start**
1. Check **logs** in Streamlit Cloud dashboard
2. Verify `requirements.txt` has all dependencies
3. Make sure `app.py` exists in the root directory

### **GitLab API Errors**
1. Verify your **GitLab token** is correct in Secrets
2. Check token has proper **scopes** (api, read_api, read_user)
3. Ensure token hasn't **expired**

### **Import Errors**
```bash
# If you see "Module not found" errors:
# Make sure requirements.txt includes all packages
# Check for typos in package names
```

### **Performance Issues**
If the app is slow:
1. The batch modes are optimized (10 parallel workers)
2. Team productivity has Ultra mode for fast loading
3. Consider reducing pagination in gitlab_utils if needed

---

## **App URL**

Once deployed, your app will be available at:
```
https://your-repo-name-streamlit-app.streamlit.app
```

Example:
```
https://gitlab-compliance-checker-streamlit-app.streamlit.app
```

---

## **Sharing Your App**

1. Click **"Share"** button in Streamlit Cloud
2. Copy the public URL
3. Share with your team!

**Note:** Users will need their own GitLab tokens to use the app.

---

## **Cost**

Streamlit Cloud has a **FREE tier** that includes:
- ✅ 1 active app
- ✅ Unlimited compute hours
- ✅ Automatic deployments
- ✅ Community support

Perfect for this tool! 🎉

---

## **Need Help?**

- **Streamlit Docs**: https://docs.streamlit.io
- **Community Forum**: https://discuss.streamlit.io
- **GitLab API Docs**: https://docs.gitlab.com/ee/api/

---

## **Quick Checklist**

- [ ] Code pushed to `newdemo` branch
- [ ] `requirements.txt` is up to date
- [ ] GitLab token created with proper scopes
- [ ] Secrets added in Streamlit Cloud
- [ ] App deployed and running
- [ ] Tested all modes (Compliance, User Profile, Team Productivity, Batch)

**Done! Your app is live! 🎊**
