#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_github.py — сборка расширенного JSON профиля GitHub.
Запускать локально/в CI. Результат сохраняется в /data/{username}.json,
который читает github.js на GitHub Pages.

Что добавлено:
- per-repo:
  • languages_bytes
  • topics (если есть)
  • contributors (топ-3: login, avatar_url, html_url, contributions)
  • stargazers_recent (последние N со starred_at, login, avatar_url, html_url)
  • pulls_count_open / pulls_count_closed
  • releases_count + latest_release (tag_name, name, html_url, published_at)
- global:
  • events (как и раньше)
  • commit_activity (агрегировано по всем репозиториям: 52 недели × 7 дней)
"""

import os
import re
import time
import json
import math
from typing import Dict, Any, List, Optional

import requests

API = "https://api.github.com"

# Укажи свой ник; можно переопределить через переменную окружения GITHUB_USERNAME
GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME", "kreonical-genesis")

# Базовые заголовки (для обычных REST-эндпоинтов)
BASE_HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "Kreonical-GitHubDashboard/1.0"
}

# Для stargazers со временем "starred_at" нужен спец. Accept
STAR_HEADERS = {
    "Accept": "application/vnd.github.star+json",
    "User-Agent": BASE_HEADERS["User-Agent"],
}

# ==========================
# ВСПОМОГАТЕЛЬНЫЕ ЗАПРОСЫ
# ==========================

def req(url: str, token: Optional[str] = None, params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None, allow_404: bool = False) -> requests.Response:
    """HTTP GET с токеном и защитой от rate limit. allow_404=True — не падать на 404 (вернуть r)."""
    h = dict(BASE_HEADERS)
    if headers:
        h.update(headers)
    if token:
        h["Authorization"] = f"token {token}"
    r = requests.get(url, headers=h, params=params, timeout=30)
    # Rate limit
    if r.status_code == 403 and "rate limit" in r.text.lower():
        reset = r.headers.get("X-RateLimit-Reset")
        if reset:
            wait = max(0, int(reset) - int(time.time()))
            raise SystemExit(f"Rate limit exceeded. Reset in {wait} seconds.")
        raise SystemExit("Rate limited by GitHub API.")
    if allow_404 and r.status_code == 404:
        return r
    r.raise_for_status()
    return r

def req_json(url: str, token: Optional[str] = None, params: Optional[Dict[str, Any]] = None,
             headers: Optional[Dict[str, str]] = None, allow_404: bool = False):
    r = req(url, token=token, params=params, headers=headers, allow_404=allow_404)
    # Если 404 разрешён, вернём None (например, latest release может отсутствовать)
    if allow_404 and r.status_code == 404:
        return None
    return r.json()

def paginated_count(url: str, token: Optional[str] = None, params: Optional[Dict[str, Any]] = None,
                    headers: Optional[Dict[str, str]] = None) -> int:
    """Получить количество элементов для list-эндпоинта, используя пер-пейдж=1 + Link: rel=last."""
    params = dict(params or {})
    params["per_page"] = 1
    r = req(url, token=token, params=params, headers=headers)
    link = r.headers.get("Link", "")
    # Если есть ссылка на последнюю страницу — достанем номер страницы
    m = re.search(r'[?&]page=(\d+)>;\s*rel="last"', link)
    if m:
        try:
            return int(m.group(1))
        except Exception:
            pass
    # Иначе считаем количество по фактическому списку (он и так из 1 элемента)
    try:
        data = r.json()
        if isinstance(data, list):
            return len(data)
    except Exception:
        pass
    return 0

# ==========================
# ЗАПРОСЫ ПО ПОЛЬЗОВАТЕЛЮ/РЕПО
# ==========================

def fetch_user(username: str, token: Optional[str] = None):
    return req_json(f"{API}/users/{username}", token=token)

def fetch_repos(username: str, token: Optional[str] = None) -> List[Dict[str, Any]]:
    """Список публичных репозиториев пользователя (все страницы)."""
    repos: List[Dict[str, Any]] = []
    page = 1
    while True:
        part = req_json(
            f"{API}/users/{username}/repos",
            token=token,
            params={"per_page": 100, "page": page, "sort": "pushed"}
        )
        if not part:
            break
        repos.extend(part)
        if len(part) < 100:
            break
        page += 1
    return repos

def fetch_repo_languages(owner: str, repo: str, token: Optional[str] = None) -> Dict[str, int]:
    return req_json(f"{API}/repos/{owner}/{repo}/languages", token=token)

def fetch_repo_topics(owner: str, repo: str, token: Optional[str] = None) -> List[str]:
    # Темы обычно уже приходят в /repos, но на всякий случай отдельный вызов:
    data = req_json(f"{API}/repos/{owner}/{repo}/topics", token=token,
                    headers={"Accept": "application/vnd.github.mercy-preview+json"})
    return (data or {}).get("names", [])

def fetch_contributors_top(owner: str, repo: str, token: Optional[str] = None, limit: int = 3):
    """Топ-контрибьюторы (login, avatar_url, html_url, contributions)."""
    data = req_json(f"{API}/repos/{owner}/{repo}/contributors",
                    token=token, params={"per_page": limit, "anon": "false"})
    result = []
    for c in (data or [])[:limit]:
        result.append({
            "login": c.get("login"),
            "avatar_url": c.get("avatar_url"),
            "html_url": c.get("html_url"),
            "contributions": c.get("contributions")
        })
    return result

def fetch_stargazers_recent(owner: str, repo: str, token: Optional[str] = None, limit: int = 8):
    """Последние поставившие звёздочку (нужно спец. Accept, чтобы получить starred_at)."""
    data = req_json(f"{API}/repos/{owner}/{repo}/stargazers", token=token,
                    params={"per_page": limit}, headers=STAR_HEADERS)
    result = []
    # При STAR_HEADERS элементы имеют вид {"starred_at": "...", "user": {...}}
    for item in (data or []):
        u = item.get("user") or {}
        result.append({
            "login": u.get("login"),
            "avatar_url": u.get("avatar_url"),
            "html_url": u.get("html_url"),
            "starred_at": item.get("starred_at")
        })
    return result

def fetch_pulls_count(owner: str, repo: str, token: Optional[str] = None) -> Dict[str, int]:
    """Количество PR по состояниям (open/closed)."""
    open_count = paginated_count(f"{API}/repos/{owner}/{repo}/pulls", token=token,
                                 params={"state": "open"})
    closed_count = paginated_count(f"{API}/repos/{owner}/{repo}/pulls", token=token,
                                   params={"state": "closed"})
    return {"open": open_count, "closed": closed_count}

def fetch_releases_info(owner: str, repo: str, token: Optional[str] = None) -> Dict[str, Any]:
    """Количество релизов + последний релиз (если есть)."""
    releases_count = paginated_count(f"{API}/repos/{owner}/{repo}/releases", token=token)
    latest = req_json(f"{API}/repos/{owner}/{repo}/releases/latest", token=token, allow_404=True)
    latest_clean = None
    if latest and isinstance(latest, dict) and latest.get("tag_name"):
        latest_clean = {
            "tag_name": latest.get("tag_name"),
            "name": latest.get("name"),
            "html_url": latest.get("html_url"),
            "published_at": latest.get("published_at"),
        }
    return {"releases_count": releases_count, "latest_release": latest_clean}

def fetch_repo_commit_activity(owner: str, repo: str, token: Optional[str] = None,
                               retries: int = 6, delay: float = 1.5):
    """
    /stats/commit_activity может вернуть 202 (готовится).
    Подождём и попробуем ещё несколько раз.
    Возвращает список из 52 недель: [{week: unix, total: int, days: [7 ints]}, ...]
    """
    url = f"{API}/repos/{owner}/{repo}/stats/commit_activity"
    for i in range(retries):
        r = req(url, token=token, headers=None)
        if r.status_code == 202:
            time.sleep(delay)
            continue
        r.raise_for_status()
        try:
            data = r.json()
            if isinstance(data, list):
                return data
        except Exception:
            pass
        break
    return []  # если так и не удалось

# ==========================
# АГРЕГАЦИЯ HEATMAP ПО ВСЕМ РЕПО
# ==========================

def aggregate_commit_activity(all_repo_weeks: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    Суммируем commit_activity по одинаковым неделям (ключ — 'week' unix).
    На выход: отсортированный список недель с суммой days[7] и total.
    """
    acc: Dict[int, List[int]] = {}  # week_unix -> days[7]
    for weeks in all_repo_weeks:
        for w in weeks:
            week_unix = int(w.get("week", 0))
            days = w.get("days", [0,0,0,0,0,0,0]) or [0]*7
            if week_unix not in acc:
                acc[week_unix] = [0]*7
            acc[week_unix] = [a+b for a, b in zip(acc[week_unix], days)]

    # Сортировка по неделям, берём последние 52 (если вдруг больше)
    sorted_weeks = sorted(acc.items(), key=lambda x: x[0])
    if len(sorted_weeks) > 52:
        sorted_weeks = sorted_weeks[-52:]

    result = []
    for week_unix, days in sorted_weeks:
        result.append({
            "week": week_unix,
            "total": sum(days),
            "days": days
        })
    return result

# ==========================
# EVENTS
# ==========================

def fetch_events(username: str, token: Optional[str] = None):
    """Последние публичные события пользователя (обычно ~30)."""
    return req_json(f"{API}/users/{username}/events/public", token=token)

# ==========================
# MAIN
# ==========================

def main():
    token = os.environ.get("GITHUB_TOKEN")  # опционально: увеличит лимиты API
    username = GITHUB_USERNAME

    # Пути проекта: скрипт лежит в /scripts, JSON пишем в /data
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, ".."))
    out_dir = os.path.join(project_root, "data")
    os.makedirs(out_dir, exist_ok=True)

    print(f"[i] Fetching GitHub data for: {username} (token={'yes' if token else 'no'})")

    # --- Пользователь и список репозиториев ---
    user = fetch_user(username, token=token)
    repos_raw = fetch_repos(username, token=token)

    simple_repos: List[Dict[str, Any]] = []
    all_repo_weeks: List[List[Dict[str, Any]]] = []

    for r in repos_raw:
        try:
            repo_name = r["name"]
            owner = r["owner"]["login"]
        except Exception:
            # если что-то очень странное в данных репозитория — пропустим
            continue

        # Языки (байты)
        try:
            langs = fetch_repo_languages(owner, repo_name, token=token)
        except Exception as e:
            print(f"[!] languages failed for {repo_name}: {e}")
            langs = {}

        # Топики (иногда уже есть в r['topics'], но подстрахуемся)
        topics = r.get("topics") or []
        if not topics:
            try:
                topics = fetch_repo_topics(owner, repo_name, token=token)
            except Exception:
                topics = []

        # Контрибьюторы (топ-3)
        contributors = []
        try:
            contributors = fetch_contributors_top(owner, repo_name, token=token, limit=3)
        except Exception as e:
            print(f"[!] contributors failed for {repo_name}: {e}")

        # Последние stargazers (до 8)
        stargazers_recent = []
        try:
            stargazers_recent = fetch_stargazers_recent(owner, repo_name, token=token, limit=8)
        except Exception as e:
            print(f"[!] stargazers failed for {repo_name}: {e}")

        # PR counts
        pulls_counts = {"open": 0, "closed": 0}
        try:
            pulls_counts = fetch_pulls_count(owner, repo_name, token=token)
        except Exception as e:
            print(f"[!] pulls count failed for {repo_name}: {e}")

        # Releases count + latest
        rel_info = {"releases_count": 0, "latest_release": None}
        try:
            rel_info = fetch_releases_info(owner, repo_name, token=token)
        except Exception as e:
            print(f"[!] releases info failed for {repo_name}: {e}")

        # Commit activity для heatmap (накапливаем для агрегации)
        try:
            weeks = fetch_repo_commit_activity(owner, repo_name, token=token)
            if weeks:
                all_repo_weeks.append(weeks)
        except Exception as e:
            print(f"[!] commit_activity failed for {repo_name}: {e}")

        # Собираем минимально нужные поля для фронта
        simple_repos.append({
            "name": repo_name,
            "full_name": r.get("full_name"),
            "html_url": r.get("html_url"),
            "description": r.get("description"),
            "language": r.get("language"),
            "topics": topics,
            "stargazers_count": r.get("stargazers_count", 0),
            "forks_count": r.get("forks_count", 0),
            "open_issues_count": r.get("open_issues_count", 0),
            "pushed_at": r.get("pushed_at"),
            "created_at": r.get("created_at"),
            "updated_at": r.get("updated_at"),
            "size": r.get("size"),
            "default_branch": r.get("default_branch"),
            "license": (r.get("license") and r.get("license", {}).get("name")) or None,

            # Новые поля:
            "languages_bytes": langs,
            "contributors": contributors,
            "stargazers_recent": stargazers_recent,
            "pulls_count_open": pulls_counts.get("open", 0),
            "pulls_count_closed": pulls_counts.get("closed", 0),
            "releases_count": rel_info.get("releases_count", 0),
            "latest_release": rel_info.get("latest_release")
        })

    # События пользователя (для вкладки «Активность»)
    events = []
    try:
        events = fetch_events(username, token=token) or []
    except Exception as e:
        print(f"[!] events failed: {e}")

    # Агрегированная heatmap за год (по всем репозиториям)
    commit_activity = aggregate_commit_activity(all_repo_weeks)

    # Финальный payload
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
        "events": events[:50],            # немного ограничим
        "commit_activity": commit_activity  # для heatmap
    }

    # Запись файла
    out_path = os.path.join(out_dir, f"{username}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"[✓] Saved to {out_path}")

if __name__ == "__main__":
    main()
