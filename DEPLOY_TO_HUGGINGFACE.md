# 🚀 Deploy to Hugging Face Spaces - Simple Guide

## Your app is ready! Code is pushed to: `newdemo` branch

---

## 📋 Step-by-Step (5 minutes)

### **Step 1: Create Hugging Face Account**
Go to: https://huggingface.co/join
- Sign up (free)
- Verify your email

---

### **Step 2: Create New Space**
1. Go to: https://huggingface.co/spaces
2. Click **"Create new Space"**
3. Fill in:
   ```
   Space name: gitlab-compliance-checker
   License: MIT
   SDK: Streamlit ⭐ (IMPORTANT!)
   Visibility: Public (or Private)
   ```
4. Click **"Create Space"**

---

### **Step 3: Push Your Code to Hugging Face**

After creating the Space, Hugging Face will show you a Git URL.

**Copy the Git URL** (it looks like):
```
https://huggingface.co/spaces/YOUR_USERNAME/gitlab-compliance-checker
```

Then run these commands:

```bash
cd /home/srilatha/gitlab-compliance-checker

# Add Hugging Face as remote (replace YOUR_USERNAME)
git remote add huggingface https://huggingface.co/spaces/YOUR_USERNAME/gitlab-compliance-checker

# Push to Hugging Face
git push -u huggingface newdemo
```

**When asked for password:**
1. Go to: https://huggingface.co/settings/tokens
2. Create a new token (role: Write)
3. Copy the token
4. Use it as password in Git

---

### **Step 4: Add GitLab Token Secret**

1. Go to your Space page on Hugging Face
2. Click **"Settings"** tab
3. Scroll to **"Variables and secrets"**
4. Click **"New secret"**
5. Add:

| Name | Value |
|------|-------|
| `GITLAB_URL` | `https://gitlab.com` |
| `GITLAB_TOKEN` | `your_actual_gitlab_token` |

**Get GitLab Token:**
1. https://gitlab.com/-/profile/personal_access_tokens
2. Create token with scopes: ✅ `api`, ✅ `read_api`, ✅ `read_user`
3. Copy the token
4. Paste in Hugging Face Secrets

---

### **Step 5: Wait for Build ⏳**

- Hugging Face will automatically build (2-5 minutes)
- You'll see: "Building" → "Running"
- Click **"Open App"** when ready!

---

## 🎉 Your App is Live!

**URL:** `https://huggingface.co/spaces/YOUR_USERNAME/gitlab-compliance-checker`

---

## 🧪 Test All Features

1. ✅ **Check Project Compliance**
2. ✅ **User Profile Overview** 
3. ✅ **Team-wise Productivity** (use "Ultra" mode - fastest!)
4. ✅ **Batch 2026 ICFAI** (now 5-8x faster!)
5. ✅ **Batch 2026 RCTS**

---

## 🔄 Update Your App

Whenever you make changes:

```bash
git push huggingface newdemo
```

Hugging Face will auto-redeploy! 🚀

---

## 💰 Cost: FREE!

Hugging Face Spaces free tier:
- ✅ Unlimited public spaces
- ✅ 16GB RAM
- ✅ 2 vCPU
- ✅ Auto-deploy on git push

---

## 📱 Share Your App

Share this URL with your team:
```
https://huggingface.co/spaces/YOUR_USERNAME/gitlab-compliance-checker
```

---

## ❓ Need Help?

**Check Logs:**
- Go to Space Settings → Logs tab
- See any errors

**Common Issues:**
- App won't start → Check logs
- GitLab API errors → Verify token in Secrets
- Slow loading → Use "Ultra" mode for teams

---

**Done! Your GitLab Compliance Checker is live on Hugging Face! 🎊**
