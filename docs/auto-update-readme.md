# Auto-Update README Workflow | 自动更新 README 工作流

This document explains how the automatic README update system works.

本文档说明自动更新 README 系统的工作原理。

## Overview | 概述

The system automatically syncs the project list in README.md with your GitHub star list at https://github.com/stars/onewesong/lists/own

系统会自动将 README.md 中的项目列表与 GitHub 星标列表 https://github.com/stars/onewesong/lists/own 保持同步。

## File Structure | 文件结构

```
.github/
└── workflows/
    └── update-readme.yml    # GitHub Action workflow
scripts/
└── update_readme.py         # Python update script
docs/
└── auto-update-readme.md    # This documentation
```

## How It Works | 工作原理

### 1. Trigger Conditions | 触发条件

The workflow runs under these conditions:

工作流在以下条件下运行：

| Trigger | Description |
|---------|-------------|
| ⏰ Schedule | Daily at UTC 00:00 (Beijing 08:00) / 每天 UTC 0:00（北京时间 8:00） |
| 🔘 Manual | Click "Run workflow" in Actions tab / 在 Actions 页面点击 "Run workflow" |
| 📝 Script Update | When `scripts/update_readme.py` is modified / 当脚本文件被修改时 |

### 2. Update Process | 更新流程

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Action Triggered                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  1. Fetch Star List                                         │
│     - Scrape https://github.com/stars/onewesong/lists/own   │
│     - Extract all repository names                          │
│     爬取星标列表页面，提取所有仓库名称                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Get Repository Details                                  │
│     - Call GitHub API for each repo                         │
│     - Fetch: description, pushed_at, topics                 │
│     调用 GitHub API 获取每个仓库的详细信息                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Generate Project List                                   │
│     - Sort by last update time (newest first)               │
│     - Categorize: Current (< 1 year) vs Legacy (> 1 year)   │
│     - Assign emoji to each project                          │
│     按更新时间排序，分类为当前项目和早期作品                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Update README.md                                        │
│     - Replace "Current Projects" section                    │
│     - Replace "Legacy Work" section                         │
│     替换 README 中的项目列表部分                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  5. Commit & Push (if changed)                              │
│     - Auto-commit with bot account                          │
│     - Push to master branch                                 │
│     如果有变更，自动提交并推送                                │
└─────────────────────────────────────────────────────────────┘
```

### 3. What Gets Updated | 更新内容

| Scenario | Will Update? |
|----------|--------------|
| Add new project to star list / 新增项目到星标列表 | ✅ Yes |
| Remove project from star list / 从星标列表移除项目 | ✅ Yes |
| Project description changes / 项目描述变化 | ✅ Yes |
| Project update time changes / 项目更新时间变化 | ✅ Yes (re-sort) |
| Project becomes legacy (>1 year inactive) / 项目变为早期作品 | ✅ Yes |

### 4. Emoji Assignment | Emoji 分配

Emojis are assigned in this priority order:

Emoji 按以下优先级分配：

1. **Specific repo mapping** - Check `REPO_EMOJI_MAP` in script / 检查脚本中的特定映射
2. **Topic matching** - Match repo topics with `EMOJI_MAP` / 匹配仓库 topics
3. **Keyword matching** - Match name/description keywords / 匹配名称/描述关键词
4. **Default** - Use 🔧 if no match / 无匹配时使用默认

#### Current Emoji Mappings | 当前 Emoji 映射

```python
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
```

## Manual Trigger | 手动触发

1. Go to repository's **Actions** tab / 进入仓库的 Actions 页面
2. Select **"Update README with Star List"** workflow / 选择工作流
3. Click **"Run workflow"** button / 点击运行按钮
4. Select branch (default: master) and click **"Run workflow"** / 选择分支并运行

## Customization | 自定义

### Add Emoji for New Project | 为新项目添加 Emoji

Edit `scripts/update_readme.py`:

```python
REPO_EMOJI_MAP = {
    # ... existing mappings ...
    "your-new-repo": "🎯",  # Add your mapping
}
```

### Change Schedule | 修改运行时间

Edit `.github/workflows/update-readme.yml`:

```yaml
on:
  schedule:
    - cron: '0 0 * * *'  # UTC time, modify as needed
```

Cron format: `minute hour day month weekday`

### Change Legacy Cutoff | 修改早期作品判定时间

Edit `scripts/update_readme.py`:

```python
# Change 365 to your preferred number of days
current, legacy = generate_project_list(repos_data, legacy_cutoff_days=365)
```

## Troubleshooting | 故障排除

### Workflow not running / 工作流未运行

- Check if GitHub Actions is enabled for the repository
- Verify the workflow file syntax is correct
- Check the Actions tab for any error messages

### Projects not updating / 项目未更新

- Ensure the star list URL is accessible
- Check if GitHub API rate limit is exceeded
- Verify the README.md section markers are intact:
  - `## Current Projects | 当前项目`
  - `### Legacy Work | 早期作品`
  - `## GitHub Activity`

### Wrong emoji assigned / Emoji 分配错误

- Add specific mapping in `REPO_EMOJI_MAP`
- Check if repo topics are set correctly on GitHub
