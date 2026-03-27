from gitlab_utils import users, projects, commits, groups, merge_requests, issues
import concurrent.futures
import dateutil.parser
from datetime import datetime, timezone, timedelta

def process_single_user(client, username):
    """
    Worker function to process a single user - OPTIMIZED for speed.
    Uses the existing helper functions from gitlab_utils module.
    """
    username = username.strip()
    result = {
        "username": username,
        "status": "Success",
        "error": None,
        "data": {}
    }

    if not username:
        return None

    try:
        # 1. Get User
        user_obj = users.get_user_by_username(client, username)
        if not user_obj:
            result["status"] = "Not Found"
            result["error"] = "User not found"
            print(f"❌ User not found: {username}")
            return result

        user_id = user_obj['id']
        result["data"]["user"] = user_obj
        print(f"✅ Found user: {username} (ID: {user_id})")

        # 2. Projects - Use existing helper function
        try:
            projs = projects.get_user_projects(client, user_id, username)
            result["data"]["projects"] = projs
            print(f"  📁 Projects: {len(projs.get('personal', []))} personal, {len(projs.get('contributed', []))} contributed")
        except Exception as e:
            print(f"  ❌ Error fetching projects: {e}")
            result["data"]["projects"] = {"personal": [], "contributed": [], "all": []}

        # 3. Commits - Use existing helper function with limited projects
        all_projs_list = result["data"]["projects"].get("all", [])[:5]
        
        try:
            all_commits, commit_counts, commit_stats = commits.get_user_commits(client, user_obj, all_projs_list)
            result["data"]["commit_stats"] = commit_stats
            print(f"  💻 Commits: {commit_stats.get('total', 0)} total, {commit_stats.get('morning_commits', 0)} morning, {commit_stats.get('afternoon_commits', 0)} afternoon")
        except Exception as e:
            print(f"  ❌ Error fetching commits: {e}")
            result["data"]["commit_stats"] = {"total": 0, "morning_commits": 0, "afternoon_commits": 0}
            commit_counts = {}

        # Refine Contributed
        verified_contributed = []
        for p in result["data"]["projects"].get("contributed", []):
            if p['id'] in commit_counts and commit_counts[p['id']] > 0:
                verified_contributed.append(p)
        result["data"]["projects"]["contributed"] = verified_contributed

        # 4. Groups - Use existing helper function
        try:
            user_groups = groups.get_user_groups(client, user_id)
            result["data"]["groups"] = user_groups
            print(f"  👥 Groups: {len(user_groups)}")
        except Exception as e:
            print(f"  ❌ Error fetching groups: {e}")
            result["data"]["groups"] = []

        # 5. MRs - Use existing helper function
        try:
            user_mrs, mr_stats = merge_requests.get_user_mrs(client, user_id)
            result["data"]["mrs"] = user_mrs
            result["data"]["mr_stats"] = mr_stats
            print(f"  🔀 MRs: {mr_stats.get('total', 0)} total, {mr_stats.get('merged', 0)} merged")
        except Exception as e:
            print(f"  ❌ Error fetching MRs: {e}")
            result["data"]["mr_stats"] = {"total": 0, "merged": 0, "opened": 0, "closed": 0}

        # 6. Issues - Use existing helper function
        try:
            user_issues, issue_stats = issues.get_user_issues(client, user_id)
            result["data"]["issues"] = user_issues
            result["data"]["issue_stats"] = issue_stats
            print(f"  ⚠️  Issues: {issue_stats.get('total', 0)} total, {issue_stats.get('opened', 0)} opened")
        except Exception as e:
            print(f"  ❌ Error fetching Issues: {e}")
            result["data"]["issue_stats"] = {"total": 0, "opened": 0, "closed": 0}

    except Exception as e:
        result["status"] = "Error"
        result["error"] = str(e)
        print(f"❌ Error processing user {username}: {e}")

    return result

def process_batch_users(client, usernames):
    """
    Parallel processing of users - OPTIMIZED with 10 workers.
    """
    results = []
    clean_usernames = [u.strip() for u in usernames if u.strip()]

    # Use 10 parallel workers for faster processing
    max_workers = min(10, len(clean_usernames))
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_user = {executor.submit(process_single_user, client, u): u for u in clean_usernames}

        for future in concurrent.futures.as_completed(future_to_user):
            try:
                res = future.result()
                if res:
                    results.append(res)
            except Exception as e:
                u = future_to_user[future]
                results.append({"username": u, "status": "Crash", "error": str(e)})

    return results
