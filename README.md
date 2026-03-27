---
title: GitLab Compliance Checker
emoji: 🔍
colorFrom: red
colorTo: blue
sdk: streamlit
sdk_version: 1.32.0
python_version: 3.11
app_file: app.py
pinned: false
license: mit
tags:
  - gitlab
  - compliance
  - analytics
  - streamlit
---

# GitLab Compliance Checker

A Streamlit web application to verify GitLab project best practices and check user profile README status.

## Features

- ✅ **Project Compliance Checker** - Verify GitLab projects follow best practices
- 👤 **User Profile Overview** - Analyze user contributions, projects, MRs, and issues
- 🏆 **Team-wise Productivity Leaderboard** - Compare team performance
- 📊 **Batch Analytics** - Process multiple users at once (ICFAI & RCTS batches)

## Usage

1. Enter your GitLab token in the sidebar
2. Select a mode from the menu
3. Enter the required information (project URL, username, etc.)
4. View the compliance/analytics report!

## Configuration

This app requires GitLab API access. Set these environment variables in your Hugging Face Space Secrets:

- `GITLAB_URL`: Your GitLab instance URL (e.g., `https://gitlab.com`)
- `GITLAB_TOKEN`: Your GitLab personal access token

### Getting a GitLab Token

1. Go to your GitLab profile → Access Tokens
2. Create a new token with scopes: `api`, `read_api`, `read_user`
3. Copy the token and add it to your Space Secrets

## Project Structure

```
gitlab-compliance-checker/
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
├── gitlab_utils/              # GitLab API utilities
│   ├── users.py
│   ├── projects.py
│   ├── commits.py
│   ├── merge_requests.py
│   ├── issues.py
│   ├── groups.py
│   └── batch.py
├── modes/                     # UI modes
│   ├── compliance_mode.py
│   ├── user_profile.py
│   ├── batch_mode.py
│   └── productivity_mode.py
└── ...
```

## Local Development

```bash
# Clone the repository
git clone https://huggingface.co/spaces/YOUR_USERNAME/gitlab-compliance-checker
cd gitlab-compliance-checker

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

## License

MIT License
