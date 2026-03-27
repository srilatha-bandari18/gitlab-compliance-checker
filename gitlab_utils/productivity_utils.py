from gitlab_utils import users, projects, commits, merge_requests, issues
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Thread-safe cache for user data
_user_cache = {}
_user_cache_lock = threading.Lock()

def get_user_productivity(client, username):
    """
    Fetches productivity stats for a single user (full detailed mode).
    Used for individual user profile view.
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

def get_team_productivity_optimized(client, team_name, members, progress_callback=None):
    """
    Optimized detailed mode with parallel processing and reduced pagination.
    Faster than original detailed mode but still fetches all metrics.
    
    Optimizations:
    - Parallel processing (5 concurrent workers)
    - Reduced commit pagination (10 pages instead of 20)
    - Reduced MR/Issues pagination (5 pages instead of 10)
    - Skip project discovery, fetch projects directly
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

    max_workers = min(5, len(members))
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_member = {
            executor.submit(_get_user_productivity_optimized, client, member): member 
            for member in members
        }
        
        completed = 0
        total = len(members)
        
        for future in as_completed(future_to_member):
            member = future_to_member[future]
            stats = future.result()
            completed += 1
            
            if progress_callback:
                progress_callback(completed, total, member)
            
            if stats:
                team_stats["total_commits"] += stats["commits_count"]
                team_stats["total_mrs_opened"] += stats["mrs_opened"]
                team_stats["total_mrs_closed"] += stats["mrs_closed"]
                team_stats["total_mrs_merged"] += stats["mrs_merged"]
                team_stats["total_issues_opened"] += stats["issues_opened"]
                team_stats["total_issues_closed"] += stats["issues_closed"]
                team_stats["member_stats"].append(stats)

    return team_stats

def _get_user_productivity_optimized(client, username):
    """
    Optimized single user productivity fetch.
    Balanced between speed and completeness.
    """
    try:
        user_obj = users.get_user_by_username(client, username)
        if not user_obj:
            return None

        user_id = user_obj['id']
        author_name = user_obj.get('name')
        
        # Fetch projects directly (skip heavy event discovery)
        try:
            projects_data = client._get_paginated(
                f"/users/{user_id}/projects",
                params={"simple": "true", "order_by": "last_activity_at", "sort": "desc"},
                per_page=50,
                max_pages=2
            )
            all_projects = projects_data[:10]  # Use top 10 most recent projects
        except Exception:
            all_projects = []
        
        # Get commits from recent projects with reduced pagination
        commit_total = 0
        seen_shas = set()
        
        for project in all_projects:
            try:
                pid = project.get('id')
                commits_data = client._get_paginated(
                    f"/projects/{pid}/repository/commits",
                    params={"author": author_name or username},
                    per_page=100,
                    max_pages=10  # Reduced from 20
                )
                
                if commits_data:
                    for c in commits_data:
                        sha = c.get('id')
                        if sha not in seen_shas:
                            seen_shas.add(sha)
                            commit_total += 1
            except Exception:
                pass
        
        # Get MRs with reduced pagination
        mr_stats = {"opened": 0, "closed": 0, "merged": 0}
        try:
            mrs_authored = client._get_paginated(
                "/merge_requests",
                params={"author_id": user_id, "scope": "all"},
                per_page=100,
                max_pages=5  # Reduced from 10
            )
            for mr in mrs_authored:
                state = mr.get("state")
                if state == "merged":
                    mr_stats["merged"] += 1
                elif state == "closed":
                    mr_stats["closed"] += 1
                elif state == "opened":
                    mr_stats["opened"] += 1
        except Exception:
            pass
        
        # Get issues with reduced pagination
        issue_stats = {"opened": 0, "closed": 0}
        try:
            issues_data = client._get_paginated(
                "/issues",
                params={"author_id": user_id, "scope": "all"},
                per_page=100,
                max_pages=5  # Reduced from 10
            )
            for issue in issues_data:
                state = issue.get("state")
                if state == "opened":
                    issue_stats["opened"] += 1
                elif state == "closed":
                    issue_stats["closed"] += 1
        except Exception:
            pass

        return {
            "username": username,
            "commits_count": commit_total,
            "mrs_opened": mr_stats.get("opened", 0),
            "mrs_closed": mr_stats.get("closed", 0),
            "mrs_merged": mr_stats.get("merged", 0),
            "issues_opened": issue_stats.get("opened", 0),
            "issues_closed": issue_stats.get("closed", 0),
        }
    except Exception as e:
        print(f"Error fetching optimized productivity for {username}: {e}")
        return None

def get_team_productivity_ultra_fast(client, team_name, members):
    """
    Ultra-fast version - ONLY fetches MRs and Issues (no commits).
    Fastest possible option for team leaderboard.
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
    
    max_workers = min(10, len(members))  # More workers since each request is lighter

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_member = {}

        for member in members:
            future = executor.submit(_get_user_productivity_ultra_fast, client, member)
            future_to_member[future] = member

        for future in as_completed(future_to_member):
            member = future_to_member[future]
            stats = future.result()
            if stats:
                team_stats["total_mrs_opened"] += stats["mrs_opened"]
                team_stats["total_mrs_closed"] += stats["mrs_closed"]
                team_stats["total_mrs_merged"] += stats["mrs_merged"]
                team_stats["total_issues_opened"] += stats["issues_opened"]
                team_stats["total_issues_closed"] += stats["issues_closed"]
                team_stats["member_stats"].append(stats)

    return team_stats

def _get_user_productivity_ultra_fast(client, username):
    """
    Ultra-fast version that ONLY fetches MRs and Issues (no commits, no projects).
    This is the fastest possible option for team leaderboard.
    """
    try:
        user_obj = users.get_user_by_username(client, username)
        if not user_obj:
            return None

        user_id = user_obj['id']
        
        # Get MRs - single API call, minimal pagination
        mr_stats = {"opened": 0, "closed": 0, "merged": 0}
        try:
            mrs_authored = client._get_paginated(
                "/merge_requests",
                params={"author_id": user_id, "scope": "all"},
                per_page=100,
                max_pages=1  # Only 1 page!
            )
            for mr in mrs_authored:
                state = mr.get("state")
                if state == "merged":
                    mr_stats["merged"] += 1
                elif state == "closed":
                    mr_stats["closed"] += 1
                elif state == "opened":
                    mr_stats["opened"] += 1
        except Exception:
            pass
        
        # Get issues - single API call
        issue_stats = {"opened": 0, "closed": 0}
        try:
            issues_data = client._get_paginated(
                "/issues",
                params={"author_id": user_id, "scope": "all"},
                per_page=100,
                max_pages=1  # Only 1 page!
            )
            for issue in issues_data:
                state = issue.get("state")
                if state == "opened":
                    issue_stats["opened"] += 1
                elif state == "closed":
                    issue_stats["closed"] += 1
        except Exception:
            pass

        return {
            "username": username,
            "commits_count": 0,  # Skip commits for speed
            "mrs_opened": mr_stats.get("opened", 0),
            "mrs_closed": mr_stats.get("closed", 0),
            "mrs_merged": mr_stats.get("merged", 0),
            "issues_opened": issue_stats.get("opened", 0),
            "issues_closed": issue_stats.get("closed", 0),
        }
    except Exception as e:
        print(f"Error fetching ultra-fast productivity for {username}: {e}")
        return None

def _get_user_productivity_fast(client, username):
    """
    Fast version that skips project discovery and uses minimal pagination.
    """
    try:
        user_obj = users.get_user_by_username(client, username)
        if not user_obj:
            return None

        user_id = user_obj['id']
        author_name = user_obj.get('name')
        
        # Skip heavy project discovery - just get user's top projects directly
        try:
            projects_data = client._get_paginated(
                f"/users/{user_id}/projects",
                params={"simple": "true", "order_by": "last_activity_at", "sort": "desc"},
                per_page=20,
                max_pages=1  # Only 1 page of projects
            )
            all_projects = projects_data[:5]  # Use top 5 most recent
        except Exception:
            all_projects = []
        
        # Get commits from only top projects
        commit_total = 0
        seen_shas = set()
        
        for project in all_projects:
            try:
                pid = project.get('id')
                commits_data = client._get_paginated(
                    f"/projects/{pid}/repository/commits",
                    params={"author": author_name or username},
                    per_page=50,
                    max_pages=2  # Only 2 pages per project
                )
                
                if commits_data:
                    for c in commits_data:
                        sha = c.get('id')
                        if sha not in seen_shas:
                            seen_shas.add(sha)
                            commit_total += 1
            except Exception:
                pass
        
        # Get MRs
        mr_stats = {"opened": 0, "closed": 0, "merged": 0}
        try:
            mrs_authored = client._get_paginated(
                "/merge_requests",
                params={"author_id": user_id, "scope": "all"},
                per_page=100,
                max_pages=1
            )
            for mr in mrs_authored:
                state = mr.get("state")
                if state == "merged":
                    mr_stats["merged"] += 1
                elif state == "closed":
                    mr_stats["closed"] += 1
                elif state == "opened":
                    mr_stats["opened"] += 1
        except Exception:
            pass
        
        # Get issues
        issue_stats = {"opened": 0, "closed": 0}
        try:
            issues_data = client._get_paginated(
                "/issues",
                params={"author_id": user_id, "scope": "all"},
                per_page=100,
                max_pages=1
            )
            for issue in issues_data:
                state = issue.get("state")
                if state == "opened":
                    issue_stats["opened"] += 1
                elif state == "closed":
                    issue_stats["closed"] += 1
        except Exception:
            pass

        return {
            "username": username,
            "commits_count": commit_total,
            "mrs_opened": mr_stats.get("opened", 0),
            "mrs_closed": mr_stats.get("closed", 0),
            "mrs_merged": mr_stats.get("merged", 0),
            "issues_opened": issue_stats.get("opened", 0),
            "issues_closed": issue_stats.get("closed", 0),
        }
    except Exception as e:
        print(f"Error fetching fast productivity for {username}: {e}")
        return None
