# AI-6 Project

This is going to be an agentic AI project with one or more UIs.
Slack is going to be one of the UIs.
It is focused on tool use and management.

# Roadmap

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

- [] Document the security model (OS user based)
- [] Support for defining OS model and permissions for AI-6 and specific tools 


# Meetings

## Project Meeting 22-mar-2025

### Action Items for next meeting
- [x] Gigi - Put this in the repo as planning.md
- [x] Gigi - Implement Slack UI
- [x] Gigi - Auto-discovery of tools
- [ ] Saar - Local AI end to end

### Status check


### Code walk


### Items for discussion

- MVP is done. should we do Github release or at least tag it? Give people (and us) some reference points to progress. 
- [MCP - Model Context Protocol](https://modelcontextprotocol.io)
- Local AI models
- Tool configuration
  - Currently only env variables are available
  - Proposal
    - pass optional config file path via env variable
    - Each tool can have its own config file format and know how to parse it
    - All tool config files must be placed under a standard root directory
    - This way all tools can get permissions to read this directory only and not get access to arbitrary dirs
    - Subdirs based on tool hierarchy are recommended to avoid conflicts
    - If the config file is Python module the tool may import it dynamically (tool's business. AI-6 doesn't care)

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