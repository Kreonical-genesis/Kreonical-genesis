#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_github.py — сборка расширенного JSON профиля GitHub.
"""

import os, re, time, json, requests
from typing import Dict, Any, List, Optional

API = "https://api.github.com"
GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME", "kreonical-genesis")

BASE_HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "Kreonical-GitHubDashboard/1.0"
}
STAR_HEADERS = {
    "Accept": "application/vnd.github.star+json",
    "User-Agent": BASE_HEADERS["User-Agent"]
}

def req(url, token=None, params=None, headers=None, allow_404=False):
    h = dict(BASE_HEADERS)
    if headers: h.update(headers)
    if token: h["Authorization"] = f"token {token}"
    r = requests.get(url, headers=h, params=params, timeout=30)
    if r.status_code == 403 and "rate limit" in r.text.lower():
        reset = r.headers.get("X-RateLimit-Reset")
        if reset: raise SystemExit(f"Rate limit exceeded. Reset in {int(reset)-int(time.time())}s.")
        raise SystemExit("Rate limited by GitHub API.")
    if allow_404 and r.status_code == 404: return r
    r.raise_for_status()
    return r

def req_json(*a, **kw):
    r = req(*a, **kw)
    if kw.get("allow_404") and r.status_code == 404: return None
    return r.json()

def paginated_count(url, token=None, params=None, headers=None):
    params = dict(params or {}); params["per_page"] = 1
    r = req(url, token=token, params=params, headers=headers)
    m = re.search(r'[?&]page=(\d+)>;\s*rel="last"', r.headers.get("Link",""))
    if m: return int(m.group(1))
    try: return len(r.json())
    except: return 0

def fetch_user(u,t=None): return req_json(f"{API}/users/{u}", token=t)
def fetch_repos(u,t=None):
    repos=[]; p=1
    while True:
        part=req_json(f"{API}/users/{u}/repos", token=t, params={"per_page":100,"page":p,"sort":"pushed"})
        if not part: break
        repos+=part; 
        if len(part)<100: break
        p+=1
    return repos
def fetch_repo_languages(o,r,t=None): return req_json(f"{API}/repos/{o}/{r}/languages", token=t)
def fetch_repo_topics(o,r,t=None): return (req_json(f"{API}/repos/{o}/{r}/topics", token=t,
        headers={"Accept":"application/vnd.github.mercy-preview+json"}) or {}).get("names",[])
def fetch_contributors_top(o,r,t=None,limit=3):
    data=req_json(f"{API}/repos/{o}/{r}/contributors", token=t, params={"per_page":limit,"anon":"false"})
    return [{"login":c.get("login"),"avatar_url":c.get("avatar_url"),
             "html_url":c.get("html_url"),"contributions":c.get("contributions")}
            for c in (data or [])[:limit]]
def fetch_stargazers_recent(o,r,t=None,limit=8):
    data=req_json(f"{API}/repos/{o}/{r}/stargazers", token=t, params={"per_page":limit}, headers=STAR_HEADERS)
    result=[]
    for item in (data or []):
        u=item.get("user") or {}
        result.append({"login":u.get("login"),"avatar_url":u.get("avatar_url"),
                       "html_url":u.get("html_url"),"starred_at":item.get("starred_at")})
    return result
def fetch_pulls_count(o,r,t=None):
    return {"open":paginated_count(f"{API}/repos/{o}/{r}/pulls", token=t, params={"state":"open"}),
            "closed":paginated_count(f"{API}/repos/{o}/{r}/pulls", token=t, params={"state":"closed"})}
def fetch_releases_info(o,r,t=None):
    releases=paginated_count(f"{API}/repos/{o}/{r}/releases", token=t)
    latest=req_json(f"{API}/repos/{o}/{r}/releases/latest", token=t, allow_404=True)
    latest_clean=None
    if latest and isinstance(latest,dict) and latest.get("tag_name"):
        latest_clean={"tag_name":latest.get("tag_name"),"name":latest.get("name"),
                      "html_url":latest.get("html_url") or latest.get("url"),
                      "published_at":latest.get("published_at")}
    return {"releases_count":releases,"latest_release":latest_clean}
def fetch_repo_commit_activity(o,r,t=None):
    url=f"{API}/repos/{o}/{r}/stats/commit_activity"
    for _ in range(6):
        r=req(url, token=t)
        if r.status_code==202: time.sleep(1.5); continue
        try: return r.json()
        except: break
    return []
def aggregate_commit_activity(all_weeks):
    acc={}
    for weeks in all_weeks:
        for w in weeks:
            days=w.get("days") or [0]*7
            acc.setdefault(w["week"],[0]*7)
            acc[w["week"]]=[a+b for a,b in zip(acc[w["week"]],days)]
    sorted_weeks=sorted(acc.items(),key=lambda x:x[0])[-52:]
    return [{"week":w,"total":sum(d),"days":d} for w,d in sorted_weeks]
def fetch_events(u,t=None): return req_json(f"{API}/users/{u}/events/public", token=t)

def main():
    token=os.environ.get("GITHUB_TOKEN")
    user=fetch_user(GITHUB_USERNAME,token)
    repos_raw=fetch_repos(GITHUB_USERNAME,token)

    simple_repos=[]; all_weeks=[]
    for r in repos_raw:
        o=r["owner"]["login"]; n=r["name"]
        langs=fetch_repo_languages(o,n,token) or {}
        topics=r.get("topics") or fetch_repo_topics(o,n,token)
        contributors=fetch_contributors_top(o,n,token)
        stars=fetch_stargazers_recent(o,n,token)
        pulls=fetch_pulls_count(o,n,token)
        rel=fetch_releases_info(o,n,token)
        weeks=fetch_repo_commit_activity(o,n,token) or []
        if weeks: all_weeks.append(weeks)
        simple_repos.append({
            "name":n,"full_name":r.get("full_name"),"html_url":r.get("html_url"),
            "description":r.get("description"),"language":r.get("language"),
            "topics":topics,"stargazers_count":r.get("stargazers_count",0),
            "forks_count":r.get("forks_count",0),"open_issues_count":r.get("open_issues_count",0),
            "pushed_at":r.get("pushed_at"),"created_at":r.get("created_at"),
            "updated_at":r.get("updated_at"),"license":(r.get("license") and r.get("license",{}).get("name")),
            "languages_bytes":langs,"contributors":contributors,"stargazers_recent":stars,
            "pulls_count_open":pulls.get("open",0),"pulls_count_closed":pulls.get("closed",0),
            "releases_count":rel["releases_count"],"latest_release":rel["latest_release"]
        })

    commit_activity=aggregate_commit_activity(all_weeks)
    events=fetch_events(GITHUB_USERNAME,token) or []

    data={"user":user,"repos":simple_repos,"commit_activity":commit_activity,"events":events}
    outdir=os.path.join(os.path.dirname(__file__),"..","data")
    os.makedirs(outdir,exist_ok=True)
    outpath=os.path.join(outdir,f"{GITHUB_USERNAME}.json")
    with open(outpath,"w",encoding="utf-8") as f: json.dump(data,f,ensure_ascii=False,indent=2)
    print("Saved",outpath)

if __name__=="__main__": main()
