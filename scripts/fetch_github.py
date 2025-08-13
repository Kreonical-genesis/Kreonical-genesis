#!/usr/bin/env python3
import os
import sys
import json
import time
import requests

API = "https://api.github.com"

# Вместо передачи из командной строки — сразу тут укажи никнейм:
GITHUB_USERNAME = "kreonical-genesis"

def req(url, token=None, params=None):
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    r = requests.get(url, headers=headers, params=params)
    if r.status_code == 403 and "rate limit" in r.text.lower():
        reset = r.headers.get("X-RateLimit-Reset")
        if reset:
            wait = int(reset) - int(time.time())
            raise SystemExit(f"Rate limit exceeded. Reset in {wait} seconds.")
        raise SystemExit("Rate limited by GitHub API.")
    r.raise_for_status()
    return r.json()

def fetch_user(username, token=None):
    return req(f"{API}/users/{username}", token=token)

def fetch_repos(username, token=None):
    repos = []
    page = 1
    while True:
        data = req(f"{API}/users/{username}/repos", token=token, params={"per_page":100, "page":page, "sort":"pushed"})
        if not data:
            break
        repos.extend(data)
        if len(data) < 100:
            break
        page += 1
    return repos

def fetch_repo_languages(owner, repo, token=None):
    return req(f"{API}/repos/{owner}/{repo}/languages", token=token)

def fetch_events(username, token=None):
    return req(f"{API}/users/{username}/events/public", token=token)

def main():
    # Убираем проверку аргументов командной строки
    username = GITHUB_USERNAME

    # Путь для сохранения файла относительно корня проекта (скрипт в scripts)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, ".."))
    out_dir = os.path.join(project_root, "data")
    os.makedirs(out_dir, exist_ok=True)

    token = os.environ.get("GITHUB_TOKEN")  # опционально для повышения лимитов

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
        simple_repos.append({
            "name": repo_name,
            "full_name": r.get("full_name"),
            "html_url": r.get("html_url"),
            "description": r.get("description"),
            "language": r.get("language"),
            "stargazers_count": r.get("stargazers_count"),
            "forks_count": r.get("forks_count"),
            "open_issues_count": r.get("open_issues_count"),
            "pushed_at": r.get("pushed_at"),
            "created_at": r.get("created_at"),
            "updated_at": r.get("updated_at"),
            "license": r.get("license") and r.get("license").get("name"),
            "languages_bytes": langs
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
