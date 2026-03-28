import streamlit as st
import requests
import gitlab
from gitlab import Gitlab, GitlabAuthenticationError, GitlabConnectionError

def safe_api_call(func, *args, **kwargs):
    """
    Safe wrapper for GitLab API calls with retry logic.
    Returns an empty list (or None result if not a list) on failure and prevents crashes.
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except (gitlab.exceptions.GitlabAuthenticationError,
                gitlab.exceptions.GitlabConnectionError,
                requests.exceptions.ConnectionError,
                requests.exceptions.RequestException,
                TimeoutError,
                ConnectionResetError) as e:
            if attempt < max_retries - 1:
                print(f"Safe API Call Attempt {attempt+1} failed: {e}. Retrying...")
                continue
            print(f"Safe API Call failed after {max_retries} attempts: {e}")
            return []
        except Exception as e:
            print(f"Unexpected Error in safe_api_call: {e}")
            return []
    return []

class GitLabClient:
    def __init__(self, base_url, private_token):
        self.base_url = base_url.rstrip("/")
        self.api_base = f"{self.base_url}/api/v4"
        self.headers = {"PRIVATE-TOKEN": private_token}
        # Initialize official python-gitlab client for access to full API
        try:
            self.client = Gitlab(
                url=self.base_url,
                private_token=private_token,
                timeout=30,
                ssl_verify=True
            )
            # auth() verifies credentials
            self.client.auth()
            # Store user info safely
            self.current_user = self.client.user
        except GitlabAuthenticationError as e:
            st.error("🔑 Authentication failed! Please check your GitLab token.")
            st.error(f"Error: {str(e)}")
            print(f"Authentication Error: {e}")
            self.client = None
            self.current_user = None
        except GitlabConnectionError as e:
            st.error("🌐 Connection failed! Cannot reach GitLab server.")
            st.error(f"URL: {base_url}")
            st.error(f"Error: {str(e)}")
            print(f"Connection Error: {e}")
            self.client = None
            self.current_user = None
        except AttributeError as e:
            # Handle version incompatibility (e.g., 'annotations' attribute missing)
            st.error("⚠️ GitLab server version incompatibility detected.")
            st.error(f"URL: {base_url}")
            st.error(f"Error: {str(e)}")
            st.info("💡 Your GitLab server may be very old. Contact your administrator.")
            print(f"AttributeError (version mismatch): {e}")
            self.client = None
            self.current_user = None
        except Exception as e:
            st.error("❌ Unable to connect to GitLab. Please check network or token.")
            st.error(f"URL: {base_url}")
            st.error(f"Error details: {str(e)}")
            print(f"Warning: python-gitlab init failed: {e}")
            self.client = None
            self.current_user = None

    def _request(self, method, endpoint, params=None):
        url = f"{self.api_base}{endpoint}"
        def make_request():
            response = requests.request(
                method,
                url,
                headers=self.headers,
                params=params,
                timeout=30, # Increased to 30s to handle slow project/commit fetches
            )
            response.raise_for_status()
            if response.status_code == 204:
                return None
            return response.json()

        return safe_api_call(make_request)

    def _get(self, endpoint, params=None):
        return self._request("GET", endpoint, params=params)

    def _get_paginated(self, endpoint, params=None, per_page=100, max_pages=10):
        all_items = []
        base_params = dict(params or {})

        for page in range(1, max_pages + 1):
            page_params = {**base_params, "per_page": per_page, "page": page}

            # Using safe_api_call indirectly via _get -> _request
            batch = self._get(endpoint, params=page_params)

            if not isinstance(batch, list) or not batch:
                break

            all_items.extend(batch)

            if len(batch) < per_page:
                break

        return all_items
