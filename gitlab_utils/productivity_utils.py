from gitlab_utils import users, projects, commits, merge_requests, issues

def get_user_productivity(client, username):
    """
    Fetches productivity stats for a single user.
    """
    try:
        user_obj = users.get_user_by_username(client, username)
        if not user_obj:
            return None

        user_id = user_obj['id']

        # Fetch data using existing utilities
        user_projects = projects.get_user_projects(client, user_id, username)
        all_projects = user_projects.get("all", [])

        _, _, commit_stats = commits.get_user_commits(client, user_obj, all_projects)
        _, mr_stats = merge_requests.get_user_mrs(client, user_id)
        _, issue_stats = issues.get_user_issues(client, user_id)

        return {
            "username": username,
            "commits_count": commit_stats.get("total", 0),
            "mrs_opened": mr_stats.get("opened", 0),
            "mrs_closed": mr_stats.get("closed", 0),
            "mrs_merged": mr_stats.get("merged", 0),
            "issues_opened": issue_stats.get("opened", 0),
            "issues_closed": issue_stats.get("closed", 0),
        }
    except Exception as e:
        print(f"Error fetching productivity for {username}: {e}")
        return None

def get_team_productivity(client, team_name, members):
    """
    Aggregates productivity stats for a team.
    """
    team_stats = {
        "team_name": team_name,
        "total_commits": 0,
        "total_mrs_opened": 0,
        "total_mrs_closed": 0,
        "total_mrs_merged": 0,
        "total_issues_opened": 0,
        "total_issues_closed": 0,
        "member_stats": []
    }

    for member in members:
        stats = get_user_productivity(client, member)
        if stats:
            team_stats["total_commits"] += stats["commits_count"]
            team_stats["total_mrs_opened"] += stats["mrs_opened"]
            team_stats["total_mrs_closed"] += stats["mrs_closed"]
            team_stats["total_mrs_merged"] += stats["mrs_merged"]
            team_stats["total_issues_opened"] += stats["issues_opened"]
            team_stats["total_issues_closed"] += stats["issues_closed"]
            team_stats["member_stats"].append(stats)

    return team_stats
