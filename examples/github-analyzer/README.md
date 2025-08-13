# GitHub User Analyzer Agent

This example demonstrates how to create a specialized AI agent that analyzes GitHub user activity and generates comprehensive reports. The agent uses the GitHub CLI (`gh`) tool to gather information about users, repositories, and contributions.

## What This Agent Does

The GitHub Analyzer Agent is designed to:
- Analyze any GitHub user's profile and activity
- Generate detailed reports on repositories, contributions, and coding patterns
- Provide insights into a user's technologies, languages, and project involvement
- Answer follow-up questions about the analyzed user

## Setup

1. **Install GitHub CLI**: Make sure you have `gh` CLI installed and authenticated:
   ```bash
   # Install gh CLI (if not already installed)
   brew install gh  # macOS
   # or follow: https://cli.github.com/
   
   # Authenticate with GitHub
   gh auth login
   ```

2. **Configure Environment**: Copy and edit the `.env` file if you need API keys for premium models:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys (optional)
   ```

3. **Run the Agent**: Use `uv run` to execute the analyzer:
   ```bash
   uv run github_analyzer.py <github_username>
   ```

## Example Session

Here's an actual session analyzing the user `the-gigi`:

```bash
$ uv run github_analyzer.py the-gigi

🔍 Starting GitHub analysis for user: the-gigi
============================================================
Invoking tool gh on server /Users/gigi/git/ai-six/py/backend/mcp_tools/github_mcp_server.sh with args: {'args': "api graphql -f query='query ($login: String!) { user(login: $login) { login name bio company location websiteUrl createdAt twitterUsername avatarUrl followers { totalCount } following { totalCount } pinnedItems(first: 6, types: REPOSITORY) { nodes { ... on Repository { nameWithOwner stargazerCount description primaryLanguage { name } } } } repositories(first: 100, ownerAffiliations: OWNER, orderBy: {field: UPDATED_AT, direction: DESC}, privacy: PUBLIC) { totalCount nodes { name nameWithOwner isArchived isFork stargazerCount forkCount updatedAt pushedAt createdAt diskUsage primaryLanguage { name } languages(first: 20, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name } } } licenseInfo { key spdxId name } } } repositoriesContributedTo(first: 100, includeUserRepositories: false, contributionTypes: [COMMIT, ISSUE, PULL_REQUEST, REPOSITORY], orderBy: {field: STARGAZERS, direction: DESC}) { totalCount nodes { nameWithOwner stargazerCount primaryLanguage { name } isArchived } } starredRepositories(first: 20, orderBy: {field: STARRED_AT, direction: DESC}) { totalCount nodes { nameWithOwner stargazerCount primaryLanguage { name } description } } contributionsCollection { contributionCalendar { totalContributions } totalCommitContributions totalIssueContributions totalPullRequestContributions totalPullRequestReviewContributions restrictedContributionsCount } } }' -F login='the-gigi'"}
Tool gh completed successfully
Invoking tool gh on server /Users/gigi/git/ai-six/py/backend/mcp_tools/github_mcp_server.sh with args: {'args': 'api users/the-gigi/events/public?per_page=300'}
Tool gh completed successfully
Invoking tool gh on server /Users/gigi/git/ai-six/py/backend/mcp_tools/github_mcp_server.sh with args: {'args': 'api users/the-gigi'}
Tool gh completed successfully
Invoking tool gh on server /Users/gigi/git/ai-six/py/backend/mcp_tools/github_mcp_server.sh with args: {'args': 'api users/the-gigi/repos?per_page=100&type=owner&sort=updated'}
Tool gh completed successfully
Invoking tool gh on server /Users/gigi/git/ai-six/py/backend/mcp_tools/github_mcp_server.sh with args: {'args': 'api users/the-gigi/starred?per_page=100'}
Tool gh completed successfully
Invoking tool gh on server /Users/gigi/git/ai-six/py/backend/mcp_tools/github_mcp_server.sh with args: {'args': 'api users/the-gigi/orgs'}
Tool gh completed successfully
Invoking tool gh on server /Users/gigi/git/ai-six/py/backend/mcp_tools/github_mcp_server.sh with args: {'args': 'api users/the-gigi/followers?per_page=1'}
Tool gh completed successfully
Invoking tool gh on server /Users/gigi/git/ai-six/py/backend/mcp_tools/github_mcp_server.sh with args: {'args': 'api users/the-gigi/following?per_page=1'}
Tool gh completed successfully
Invoking tool gh on server /Users/gigi/git/ai-six/py/backend/mcp_tools/github_mcp_server.sh with args: {'args': 'api users/the-gigi/events/public?per_page=300'}
Tool gh completed successfully

User Profile Summary
- Username: the-gigi (Gigi Sayfan)
- Joined: 2012-02-05 (13+ years on GitHub)
- Public repos/gists: 109 repos, 45 gists
- Followers/Following: 109 / 0
- Public orgs: none visible
- Profile details: no bio/location listed; email visible (the.gigi@gmail.com)
- Recent profile activity: active and steadily committing across multiple projects

Repository Analysis
- Most active recently (last 2–3 weeks):
  - Sayfan-AI/ai-six (org repo; Agentic AI focused on ubiquitous tool use)
    - Frequent push activity with agent module refactors, MCP (Model Context Protocol) integration and discovery, GitHub CLI tool in bash, Slack frontend/channel management cleanup, AWS and kubectl tools, CI via GitHub Actions, and multiple version tags (v0.10.0, v0.11.0).
    - Clear push cadence with iterative improvements and tooling additions.
  - PacktPublishing/Design-Multi-Agent-AI-Systems-using-MCP-and-A2A (contributor)
    - Copied "ai-six" (v0.8.0) into chapter 4 and "k8s-ai" into chapter 3; opened an issue to add self as contributor; member event recorded.
  - the-gigi/dotfiles
    - Shell and workflow enhancements (e.g., tagging alias/functions), robustness improvements.
  - the-gigi/quote-service
    - Modernization, dependency bumps, released v1.0.0.
  - the-gigi/gigi-zone
    - Gemini OpenAI compatibility fixes.
  - the-gigi/k8s-ai
    - README fixes and improvements.
- Notable/popular owned repos (by stars)
  - delinkcious (Go) — 71★, 66 forks (A Delicious-like link manager)
  - conman (Python) — 38★, 9 forks (distributed config via etcd)

💭 Ask a follow-up question (or 'quit' to exit): quit
```

## Configuration

The agent uses a minimal configuration that includes only the GitHub CLI MCP tool:

```json
{
  "default_model_id": "devstral:24b",
  "mcp_tools_dirs": ["${HOME}/git/ai-six/py/backend/mcp_tools"],
  "memory_dir": "${HOME}/git/ai-six/memory/github-analyzer",
  "checkpoint_interval": 3,
  "provider_config": {
    "ollama": {
      "model": "qwen2.5-coder:32b"
    }
  }
}
```

## How It Works

1. **Agent Initialization**: Creates an AI agent with a specialized system prompt for GitHub analysis
2. **GitHub CLI Integration**: Uses the `gh` MCP tool to execute GitHub CLI commands
3. **Structured Analysis**: Follows a systematic approach to gather user information using GraphQL and REST API calls
4. **Interactive Session**: Allows follow-up questions for deeper analysis
5. **Memory Persistence**: Maintains conversation history for context

## Key Features Demonstrated

- **Advanced GitHub API Usage**: Uses both GraphQL and REST endpoints to gather comprehensive data
- **Real-time Analysis**: Shows actual tool invocations and API calls being made
- **Structured Output**: Organizes findings into clear categories (profile, repositories, activity)
- **Comprehensive Data Gathering**: Collects information about repos, stars, followers, recent activity, and more

## Customization

You can modify the agent's behavior by:
- Editing the system prompt in `github_analyzer.py` to focus on different analysis aspects
- Changing the analysis focus areas (e.g., focus more on code quality, collaboration patterns)
- Adding additional tools to the configuration for enhanced analysis
- Modifying the output format and structure

This example demonstrates how to create domain-specific AI agents that leverage command-line tools for specialized analysis tasks, showing the power of combining AI reasoning with real-world tool integration.