#!/usr/bin/env python3
"""
Auto-update README.md with projects from GitHub star list.
Fetches repos from https://github.com/stars/onewesong/lists/own
"""

import os
import re
import json
import requests
from datetime import datetime, timezone
from bs4 import BeautifulSoup

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
STAR_LIST_URL = "https://github.com/stars/onewesong/lists/own"
README_PATH = "README.md"
OWNER = "onewesong"

# Specific repo name to emoji mapping (highest priority)
REPO_EMOJI_MAP = {
    "open-next-router": "🚇",
    "one-api-nginx": "🌐",
    "codex-viz": "📊",
    "better-git-of-theseus": "📈",
    "shorturl": "🔗",
    "mock-server": "🎭",
    "open-playcode": "💻",
    "ai-wiki": "📚",
    "code-switch": "🔄",
    "openries": "🌍",
    "goforeach": "⚡",
}

# Emoji mapping for project categories (fallback)
EMOJI_MAP = {
    "api-gateway": "🚇",
    "llm-gateway": "🌐",
    "llm": "🤖",
    "dashboard": "📊",
    "analytics": "📊",
    "shorturl": "🔗",
    "url-shortener": "🔗",
    "mock": "🎭",
    "editor": "💻",
    "playcode": "💻",
    "wiki": "📚",
    "glossary": "📚",
    "switch": "🔄",
    "translation": "🌍",
    "chrome-extension": "🌍",
    "git": "📈",
    "cli": "⚡",
    "concurrent": "⚡",
    "ai": "🤖",
}

DEFAULT_EMOJI = "🔧"


def get_headers():
    """Get headers for GitHub API requests."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "README-Updater",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    return headers


def fetch_star_list_repos():
    """Fetch repos from the star list page by scraping."""
    try:
        response = requests.get(STAR_LIST_URL, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        repos = []
        # Skip list of non-repo paths
        skip_owners = {"stars", "login", "settings", "orgs", "features", "contact", "about", "pricing", "security", "site"}
        skip_names = {"stargazers", "forks", "issues", "pulls", "actions", "projects", "wiki", "security", "pulse", "community"}
        
        # Find all repo links in the star list
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            # Skip URLs with query params or special characters
            if "?" in href or "%" in href or "#" in href:
                continue
            # Match repo links like /owner/repo
            if href.startswith("/") and href.count("/") == 2 and not href.startswith("//"):
                parts = href.strip("/").split("/")
                if len(parts) == 2 and parts[0] and parts[1]:
                    owner, name = parts
                    # Skip non-repo links
                    if owner.lower() in skip_owners:
                        continue
                    if name.lower() in skip_names:
                        continue
                    # Skip if name starts with special chars
                    if name.startswith(".") or name.startswith("-"):
                        continue
                    full_name = f"{owner}/{name}"
                    if full_name not in repos:
                        repos.append(full_name)
        
        return repos
    except Exception as e:
        print(f"Error fetching star list: {e}")
        return []


def get_repo_details(full_name):
    """Get repository details from GitHub API."""
    url = f"https://api.github.com/repos/{full_name}"
    try:
        response = requests.get(url, headers=get_headers(), timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching {full_name}: {e}")
        return None


def get_commit_count(full_name, default_branch):
    """Get the total commit count for the repository's default branch."""
    url = f"https://api.github.com/repos/{full_name}/commits"
    params = {"sha": default_branch, "per_page": 1}
    try:
        response = requests.get(url, headers=get_headers(), params=params, timeout=10)
        response.raise_for_status()
        link = response.links.get("last")
        if link:
            return int(link["url"].split("page=")[-1].split("&", 1)[0])
        return len(response.json())
    except Exception as e:
        print(f"Error fetching commit count for {full_name}: {e}")
        return 0


def get_emoji_for_repo(repo_data):
    """Get an appropriate emoji for the repo based on topics and name."""
    name = repo_data.get("name", "")
    topics = repo_data.get("topics", []) or []
    description = (repo_data.get("description") or "").lower()
    
    # Check specific repo name first (highest priority)
    if name in REPO_EMOJI_MAP:
        return REPO_EMOJI_MAP[name]
    
    # Check topics
    for topic in topics:
        if topic.lower() in EMOJI_MAP:
            return EMOJI_MAP[topic.lower()]
    
    # Check name and description keywords
    name_lower = name.lower()
    for keyword, emoji in EMOJI_MAP.items():
        if keyword in name_lower or keyword in description:
            return emoji
    
    return DEFAULT_EMOJI


def extract_bilingual_description(description):
    """Extract or create bilingual description."""
    if not description:
        return "", ""
    
    # Check if already bilingual (contains |)
    if "|" in description:
        parts = description.split("|", 1)
        en = parts[0].strip()
        zh = parts[1].strip() if len(parts) > 1 else ""
        return en, zh
    
    # Return as-is if not bilingual
    return description.strip(), ""


def generate_project_list(repos_data, legacy_cutoff_days=365):
    """Generate markdown project list from repo data."""
    current_projects = []
    legacy_projects = []
    
    now = datetime.now(timezone.utc)
    
    for repo in repos_data:
        if not repo:
            continue
            
        full_name = repo.get("full_name", "")
        name = repo.get("name", "")
        description = repo.get("description") or ""
        url = repo.get("html_url", f"https://github.com/{full_name}")
        pushed_at = repo.get("pushed_at", "")
        stars = repo.get("stargazers_count", 0) or 0
        commits = get_commit_count(full_name, repo.get("default_branch", ""))
        
        emoji = get_emoji_for_repo(repo)
        en_desc, zh_desc = extract_bilingual_description(description)
        
        # Format description
        if zh_desc:
            desc_text = f"{en_desc} | {zh_desc}"
        else:
            desc_text = en_desc
        
        line = f"- {emoji} [{name}]({url}) - {desc_text}"
        sort_key = (-commits, -stars, name.lower())
        
        # Check if legacy (not updated in over a year)
        if pushed_at:
            try:
                pushed_date = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
                days_since_update = (now - pushed_date).days
                if days_since_update > legacy_cutoff_days:
                    legacy_projects.append((sort_key, line))
                else:
                    current_projects.append((sort_key, line))
            except Exception as e:
                print(f"  Warning: Could not parse date {pushed_at}: {e}")
                current_projects.append((sort_key, line))
        else:
            current_projects.append((sort_key, line))
    
    # Sort by commit count (most commits first), then stars, then name
    current_projects.sort(key=lambda x: x[0])
    legacy_projects.sort(key=lambda x: x[0])
    
    return [p[1] for p in current_projects], [p[1] for p in legacy_projects]


def update_readme(current_projects, legacy_projects):
    """Update the README.md file with new project list."""
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Define the section markers
    current_start = "## Current Projects | 当前项目"
    legacy_start = "### Legacy Work | 早期作品"
    github_activity = "## GitHub Activity"
    
    # Build new content
    new_current = current_start + "\n\n" + "\n".join(current_projects)
    new_legacy = legacy_start + "\n\n" + "\n".join(legacy_projects) if legacy_projects else ""
    
    # Find and replace sections using regex
    # Pattern to match from "## Current Projects" to before "## GitHub Activity"
    pattern = r"(## Current Projects \| 当前项目\n\n).*?((?=\n## GitHub Activity))"
    
    if legacy_projects:
        replacement = f"## Current Projects | 当前项目\n\n" + "\n".join(current_projects) + f"\n\n### Legacy Work | 早期作品\n\n" + "\n".join(legacy_projects) + "\n"
    else:
        replacement = f"## Current Projects | 当前项目\n\n" + "\n".join(current_projects) + "\n"
    
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)
    
    print(f"✅ Updated README with {len(current_projects)} current and {len(legacy_projects)} legacy projects")


def main():
    print("🔍 Fetching star list repos...")
    repo_names = fetch_star_list_repos()
    
    if not repo_names:
        print("⚠️ No repos found in star list, skipping update")
        return
    
    print(f"📦 Found {len(repo_names)} repos: {repo_names}")
    
    print("📡 Fetching repo details...")
    repos_data = []
    for name in repo_names:
        print(f"  - {name}")
        data = get_repo_details(name)
        if data:
            repos_data.append(data)
    
    print("📝 Generating project list...")
    current, legacy = generate_project_list(repos_data)
    
    print("✏️ Updating README...")
    update_readme(current, legacy)
    
    print("🎉 Done!")


if __name__ == "__main__":
    main()
