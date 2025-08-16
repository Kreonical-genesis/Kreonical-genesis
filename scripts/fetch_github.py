#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_github.py — сборщик данных профиля и репозиториев GitHub в один JSON
Запускать локально (или в CI), результат кладётся в /data/{username}.json —
его читает github.js на GitHub Pages.
"""
import os
import json
import time
import requests
from typing import Dict, Any, List, Optional

API = "https://api.github.com"
GITHUB_USERNAME = "kreonical-genesis"

BASE_HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "Kreonical-Vitrine-Script"
}

def req(url: str, token: Optional[str] = None, params: Optional[Dict[str, Any]] = None) -> requests.Response:
    headers = dict(BASE_HEADERS)
    if token:
        headers["Authorization"] = f"token {token}"
    r = requests.get(url, headers=headers, params=params, timeout=30)
    if r.status_code == 403 and "rate limit" in r.text.lower():
        reset = r.headers.get("X-RateLimit-Reset")
        if reset:
            wait = int(reset) - int(time.time())
            raise SystemExit(f"Rate limit exceeded. Reset in {wait} seconds.")
        raise SystemExit("Rate limited by GitHub API.")
    r.raise_for_status()
    return r

def req_json(url: str, token: Optional[str] = None, params: Optional[Dict[str, Any]] = None):
    return req(url, token, params).json()

def fetch_user(username: str, token: Optional[str] = None):
    return req_json(f"{API}/users/{username}", token=token)

def fetch_repos(username: str, token: Optional[str] = None) -> List[Dict[str, Any]]:
    repos: List[Dict[str, Any]] = []
    page = 1
    while True:
        data = req_json(
            f"{API}/users/{username}/repos",
            token=token,
            params={"per_page": 100, "page": page, "sort": "pushed"}
        )
        if not data:
            break
        repos.extend(data)
        if len(data) < 100:
            break
        page += 1
    return repos

def fetch_repo_languages(owner: str, repo: str, token: Optional[str] = None) -> Dict[str, int]:
    return req_json(f"{API}/repos/{owner}/{repo}/languages", token=token)

def head_count(url: str, token: Optional[str] = None) -> int:
    headers = dict(BASE_HEADERS)
    if token:
        headers["Authorization"] = f"token {token}"
    r = requests.get(url, headers=headers, params={"per_page": 1}, timeout=30)
    if r.status_code == 404:
        return 0
    r.raise_for_status()
    link = r.headers.get("Link", "")
    if 'rel="last"' in link:
        import re
        m = re.search(r"[?&]page=(\\d+)>; rel=\"last\"", link)
        if m:
            return int(m.group(1))
    items = r.json()
    if isinstance(items, list):
        return len(items)
    return 0

def fetch_events(username: str, token: Optional[str] = None):
    return req_json(f"{API}/users/{username}/events/public", token=token)

def main():
    username = GITHUB_USERNAME
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, ".."))
    out_dir = os.path.join(project_root, "data")
    os.makedirs(out_dir, exist_ok=True)

    token = os.environ.get("GITHUB_TOKEN")
    print(f"Fetching GitHub data for: {username} (token={'yes' if token else 'no'})")

    user = fetch_user(username, token=token)
    repos = fetch_repos(username, token=token)

    simple_repos = []
    for r in repos:
        repo_name = r["name"]
        owner = r["owner"]["login"]
        langs = {}
        try:
            langs = fetch_repo_languages(owner, repo_name, token=token)
        except Exception as e:
            print(f"Warning: couldn't fetch languages for {repo_name}: {e}")
        topics = r.get("topics", [])
        releases_count = 0
        contributors_count = 0
        try:
            releases_count = head_count(f"{API}/repos/{owner}/{repo_name}/releases", token=token)
        except Exception as e:
            print(f"Warning: couldn't fetch releases count for {repo_name}: {e}")
        try:
            contributors_count = head_count(f"{API}/repos/{owner}/{repo_name}/contributors", token=token)
        except Exception as e:
            print(f"Warning: couldn't fetch contributors count for {repo_name}: {e}")

        simple_repos.append({
            "name": repo_name,
            "full_name": r.get("full_name"),
            "html_url": r.get("html_url"),
            "description": r.get("description"),
            "language": r.get("language"),
            "topics": topics,
            "stargazers_count": r.get("stargazers_count"),
            "forks_count": r.get("forks_count"),
            "open_issues_count": r.get("open_issues_count"),
            "pushed_at": r.get("pushed_at"),
            "created_at": r.get("created_at"),
            "updated_at": r.get("updated_at"),
            "size": r.get("size"),
            "default_branch": r.get("default_branch"),
            "license": r.get("license") and r.get("license").get("name"),
            "languages_bytes": langs,
            "releases_count": releases_count,
            "contributors_count": contributors_count
        })

    events = []
    try:
        events = fetch_events(username, token=token)
    except Exception as e:
        print(f"Warning: couldn't fetch events: {e}")

    payload = {
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "user": {
            "login": user.get("login"),
            "name": user.get("name"),
            "avatar_url": user.get("avatar_url"),
            "bio": user.get("bio"),
            "blog": user.get("blog"),
            "company": user.get("company"),
            "location": user.get("location"),
            "public_repos": user.get("public_repos"),
            "followers": user.get("followers"),
            "following": user.get("following"),
            "created_at": user.get("created_at"),
            "html_url": user.get("html_url"),
        },
        "repos": simple_repos,
        "events": events[:50]
    }

    out_file = os.path.join(out_dir, f"{username}.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"Saved to {out_file}")

if __name__ == "__main__":
    main()
