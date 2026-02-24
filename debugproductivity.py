#!/usr/bin/env python3
"""
Debug script to fetch and display productivity data from GitLab.

Usage:
    python3 debugproductivity.py <gitlab_url> <username>

Example:
    python3 debugproductivity.py https://code.swecha.org Kaveri_Mamidi

Or import as a module:
    from debugproductivity import get_user_productivity
    stats = get_user_productivity("Kaveri_Mamidi")
"""

import sys
import os
import warnings
import urllib3
from dotenv import load_dotenv

# Suppress SSL warnings for self-hosted GitLab
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from gitlab_utils.client import GitLabClient
from gitlab_utils import users, merge_requests, issues, projects, commits


def get_user_productivity(username, gitlab_url=None, gitlab_token=None):
    """
    Fetch productivity statistics for a given user from GitLab.

    Args:
        username (str): GitLab username to fetch data for
        gitlab_url (str, optional): GitLab URL. Defaults to env GITLAB_URL or https://code.swecha.org
        gitlab_token (str, optional): GitLab token. Defaults to env GITLAB_TOKEN

    Returns:
        dict: Productivity statistics containing:
            - username (str)
            - user_id (int)
            - projects_count (int)
            - commits (dict): total, morning, afternoon
            - merge_requests (dict): opened, closed, merged
            - issues (dict): opened, closed
        None: If user not found or error occurs
    """
    # Get credentials from environment if not provided
    if gitlab_url is None:
        gitlab_url = os.getenv("GITLAB_URL", "https://code.swecha.org")
    if gitlab_token is None:
        gitlab_token = os.getenv("GITLAB_TOKEN", "")

    if not gitlab_token:
        print("Error: GITLAB_TOKEN not found. Please set it in .env or pass as argument.")
        return None

    # Initialize client
    client = GitLabClient(gitlab_url, gitlab_token)
    if not client.client:
        print("Error: Failed to initialize GitLab client. Check URL and Token.")
        return None

    # Find user
    user_obj = users.get_user_by_username(client, username)
    if not user_obj:
        print(f"Error: User '{username}' not found.")
        return None

    user_id = user_obj['id']

    # Fetch Projects
    user_projects = projects.get_user_projects(client, user_id, username)
    all_projects = user_projects.get("all", [])

    # Fetch MRs
    mr_list, mr_stats = merge_requests.get_user_mrs(client, user_id)

    # Fetch Issues
    issue_list, issue_stats = issues.get_user_issues(client, user_id)

    # Fetch Commits
    commit_list, project_commit_counts, commit_stats = commits.get_user_commits(
        client, user_obj, all_projects
    )

    # Build and return stats dictionary
    stats = {
        "username": username,
        "user_id": user_id,
        "projects_count": len(all_projects),
        "commits": {
            "total": commit_stats.get("total", 0),
            "morning": commit_stats.get("morning_commits", 0),
            "afternoon": commit_stats.get("afternoon_commits", 0),
        },
        "merge_requests": {
            "opened": mr_stats.get("opened", 0),
            "closed": mr_stats.get("closed", 0),
            "merged": mr_stats.get("merged", 0),
        },
        "issues": {
            "opened": issue_stats.get("opened", 0),
            "closed": issue_stats.get("closed", 0),
        },
    }

    return stats


def print_productivity_stats(stats):
    """
    Pretty print productivity statistics.

    Args:
        stats (dict): Statistics dictionary from get_user_productivity()
    """
    if not stats:
        return

    print("\n" + "=" * 50)
    print(f"SUMMARY FOR: {stats['username']}")
    print("=" * 50)
    print(f"  User ID:        {stats['user_id']}")
    print(f"  Projects:       {stats['projects_count']}")
    print("-" * 50)
    print(f"  Total Commits:    {stats['commits']['total']}")
    print(f"  Morning Commits:  {stats['commits']['morning']} (09:30 AM - 12:30 PM)")
    print(f"  Afternoon Commits: {stats['commits']['afternoon']} (02:00 PM - 05:00 PM)")
    print("-" * 50)
    print(f"  MRs Opened:     {stats['merge_requests']['opened']}")
    print(f"  MRs Closed:     {stats['merge_requests']['closed']}")
    print(f"  MRs Merged:     {stats['merge_requests']['merged']}")
    print("-" * 50)
    print(f"  Issues Opened:  {stats['issues']['opened']}")
    print(f"  Issues Closed:  {stats['issues']['closed']}")
    print("=" * 50)


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 debugproductivity.py <gitlab_url> <username>")
        print("Example: python3 debugproductivity.py https://code.swecha.org Kaveri_Mamidi")
        sys.exit(1)

    # Get GitLab URL and username from command line args
    gitlab_url = sys.argv[1]
    username = sys.argv[2]

    # Get token from environment
    gitlab_token = os.getenv("GITLAB_TOKEN", "")

    if not gitlab_token:
        print("Error: GITLAB_TOKEN not found in environment.")
        print("Please set it in .env file or export GITLAB_TOKEN=your_token")
        sys.exit(1)

    print(f"GitLab URL: {gitlab_url}")
    print(f"Username: {username}")
    print("-" * 50)

    # Fetch productivity stats using the reusable function
    stats = get_user_productivity(username, gitlab_url, gitlab_token)

    if stats:
        print_productivity_stats(stats)
    else:
        print("Failed to fetch productivity data.")
        sys.exit(1)


if __name__ == "__main__":
    main()
