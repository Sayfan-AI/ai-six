# AI-6 Project

This is going to be an agentic AI project with one or more UIs.
Slack is going to be one of the UIs.
It is focused on tool use and management.

# Roadmap

## Capabilities

- [ ] MCP support (engine is MCP client, local tools can run as MCP server)
- [ ] Streaming
- [ ] Context window management (summarization)
- [x] Long term memory (On startup AI-6 reads context from persistent storage like file or DB, periodically checkpoints)
- [ ] Expose usage information (tokens)
## Tools

- [ ] AI-6 (recursive agent mesh)
- [ ] Slack tool
- [x] Kubectl
- [ ] [dOpus](https://github.com/Bloblblobl/dopus) integration
- [ ] aws
- [ ] Cloudflare
- [ ] Github
- [ ] Github actions

## Permission model

- [] Document the security model (OS user based, including access to remote services credentials and k8s clusters)
- [] Dedicated tool Support for defining OS model and permissions for AI-6 and specific tools

## Fully-autonomous AI software engineer
- [ ] Watch Github issues
- [ ] Respond to new issues assigned to it
- [ ] Create local branch
- [ ] Make changes + tests
- [ ] Run tests
- [ ] Open PR
- [ ] Watch for PR comments
- [ ] Make further changes based on PR comments
- [ ] Merge PR when approved
- [ ] Deploy and monitor
- [ ] Rollback if something goes wrong

# Meetings

## Project Meeting 5-apr-2025


- Discuss summarization when context window feels up.
- More file system tools
    - sed (for string replace and other edits on a file)
    - patch
- Support for Anthropic built-in text editor tool
  - https://docs.anthropic.com/en/docs/build-with-claude/tool-use/text-editor-tool  
- Streaming (display content as it is generated)
- Managing long-running processes (e.g. ollama serve)

- Support for multiple LLM providers
  - OpenAI
  - Ollama + Gemma 3 function calling (no tool use on Ollama)
  - Anthropic
  - Gemini 2.5 pro experimental (free tier)
  - Llamma 4 Scout
  

### Action Items

- [ ] Saar/Gigi - Multiple LLM Providers
- [ ] Saar - Research Ollama + Gemma 3 function calling
- [ ] Saar - look into making bot output nicer on slack (e.g. render markdown as markdown)
- [ ] Gigi - Look into MCP
- [ ] Gigi - Engine + Tool configuration

## Project Meeting 29-mar-2025

### Action Items

- [x] Gigi - Check out chainlit
- [x] Gigi - Issues
  - [x] AI-6 slack should ignore messages that mention other users
  - [x] AI-6 slack bot should leave the channel on app exit
  - [x] Bootstrap tool to restart itself (AI-6 runs new code after changes)
 

## Project Meeting 22-mar-2025

### Action Items

- [x] Gigi - Put this in the repo as planning.md
- [x] Gigi - Implement Slack UI
- [x] Gigi - Auto-discovery of tools
- [x] Saar - Local AI end to end

### Items for discussion

- MVP is done. should we do Github release or at least tag it? Give people (and us) some reference points to progress.
    - Just a tag!
- [MCP - Model Context Protocol](https://modelcontextprotocol.io)
- Multiple LLM providers
    - Engine receives multiple OpenAI instances + metadata on each one
    - AI-6 may swtich providers depending on task
    - User can always request specific provider
    - Default provider will be configured
- Local AI models
    - Lamma 3.2 works, but not great
    - Need to experiment with others and find at least one good model
- Tool configuration
    - Currently only env variables are available
    - Proposal
        - pass optional config file path via env variable
        - Each tool can have its own config file format and know how to parse it
        - All tool config files must be placed under a standard root directory
        - This way all tools can get permissions to read this directory only and not get access to arbitrary dirs
        - Subdirs based on tool hierarchy are recommended to avoid conflicts
        - If the config file is Python module the tool may import it dynamically (tool's business. AI-6 doesn't care)
        - It's possible to aggregate all config files into one big config file (one stop shop for users) and then some
          config helper will break it down into separate files expected by tools and update the environment.

### Code walk

## Project Meeting 16-mar-2025

### Action Items

- [x] Saar - look into local LLM
    - https://ollama.com
    - https://localai.io
    - LM Studio
- [x] Gigi - Work on slacker
- [x] Gigi - Create Github org and monorepo
    - Org :  [Sayfan-AI](https://github.com/Sayfan-AI)
    - Repo: [ai-six](https://github.com/Sayfan-AI/ai-six)
- [x] All - Think about automated actions vs human approval

### Current Status

- AI-6
    - Works end to end
    - The engine implements the agentic loop
    - An extensible tool system exists with one implemented tool (ls)
    - CLI frontend works
    - Everything is implemented in Python
- Slacker
    - Works

### Items for discussions

- Should we put this document in the ai-six repo? develop in the open? yes
- What tools should we implement next?
- Permissions
    - File access - root dir restrictions per tool (e.g. ls can be on everything, but rm only on some directories)
    - Prefer explicit whitelisting (default is no permissions)
    - Holistic approach - run ai6 as a specific user, it can't do more damage than its user permissions allow
    - Single user or perhaps optional users for specific tools.
- Voice UI
- Observability
    - tokens (input and output)
    - for Slack UI capture tool calls as messages on a thread
    - context window size?
- Inception - AI-6 launching AI-6 as a tool (parent doesn't see context of child, just final output)

- Non user input - Some server can listen to events and invoke AI-6 and based on the answer take some action

## Kickoff Meeting 8-mar-2025

### Action items this meeting

- [x] Pick a name (AI-6)
- [x] Schedule future meetings
- [x] Try "Code with Me"
- [x] Pick actions items for next meeting
- [x] Create #ai-6 slack channel

### Pick a name

- AI Whisperer
- AI-6 (MI-6 and SEAL Team 6)
- Xeno AI (sci-fi, non-human)
- Agent Smith (Matrix)
- AI Stein (Einstein)
- Tool AI

ChatGPT was very impressed with AI-6!
![image](https://hackmd.io/_uploads/BkrSARKjye.png)

### Architecture / Roadmap

- the core engine is responsible for the agentic loop
- the core engine is NOT responsible for tool saftey, security, etc
- plugin-in architecture where arbitrary tools can be added
- each plugin is resposible for interacting with the target tool
- generic (extensible) config file for all the tools and/or config file per tool
- external tool registry
- The core engine can run locally or in the cloud
- Support multiple LLM providers (local + managed)
- engine plugin API (programming language native, REST, gRPC)
- engine API - allow programmatic access to AI-6

Question: do we need an architecture document?
Answer: No! later.

### Self-hosted + managed LLM providers

- Support multiple providers (OpenAI, Anthropic, Gemini, etc)
- AI service access is easy, but can get expensive
- Free-tier of managed AI providers may be sufficient for development
- Local is ideal if performs well

### Programming languages

- Slack has support for Typescript, Python with supposedly good libraries
- Engine - options: Rust, Go and Python and possibly even ALL of them
- Tool plugins in engine language or any language (docker container, REST, gRPC)
- Frontend - Typescript

### Tools

- Kubernetes via kubectl
- Git
- Github
- Docker
- Shell (inside a Docker container) - super risky. maybe not?
- Any API (Youtube, Spotify, Facebook)
- Homebrew
- Tool discovery and request

Session persistence not needed. Tools can persist WIP themselves (e.g. in github PRs for a coding project)

### UI

- Slack
- CLI
- Web (can run on mobile too)

### Github repo structure

- Monorepo
- Separate repo for each component
- Hybrid
    - Monorepo for project-specific components
    - Separate repos for standalone libraries (e.g. slacker)
- Github organization (never done it)

Decision: start with Github organization + monorepo. Move to hybrid if needed

### MVP

- Simple UI - Slack + CLI
- Core (copy and extend k8s-ai)
- Initial built-in Tools (k8s + git)
- No plugins

Done!

# Reference

- [k8s-ai](https://github.com/the-gigi/) - A Simple Python CLI PoC of a Kubernetes AI agent
- [slacker](https://github.com/the-gigi/slacker) - Control Slack programmatically

# Resources

- [Building Agents with Model Context Protocol - Full Workshop](https://www.youtube.com/watch?v=kQmXtrmQ5Zg&t=2s)
- [A Deep Dive into MCP and the future of AI tooling](https://a16z.com/a-deep-dive-into-mcp-and-the-future-of-ai-tooling)
- [Building an Agentic System](https://gerred.github.io/building-an-agentic-system/introduction.html)
- [Anon Kode](https://github.com/dnakov/anon-kode)
- [OpenAI Agent SDK](https://platform.openai.com/docs/guides/agents-sdk)
- [OpenAI agents guide](https://platform.openai.com/docs/guides/agents)
- [Robasta.dev HolmesGPT](https://github.com/robusta-dev/holmesgpt/tree/master)
- [MCP-Agent](https://github.com/lastmile-ai/mcp-agent)
- [mcp-cli](https://github.com/chrishayuk/mcp-cli)
- [AI Agent framework on Kubernetes](https://github.com/kagent-dev/kagent)
- [Ollam + Gemma 3](https://www.youtube.com/watch?v=m2rG6zHoxBo)
- [Ollama API](https://github.com/ollama/ollama/blob/main/docs/api.md)