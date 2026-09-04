# Vendored agent skills

This directory is the canonical, repo-local copy of the `google-agents-cli-*` skills — vendored here so the knowledge travels with the repo instead of depending on a machine-level `agents-cli setup` (which installs to `~/.agents/skills`, outside version control).

- **Source**: [google/agents-cli](https://github.com/google/agents-cli), `skills/` directory
- **License**: Apache-2.0 (Google)
- **Vendored version**: 1.4.0 (all seven skills), 2026-09-04

## Layout

`.agents/skills/` is the [Agent Skills standard](https://geminicli.com/docs/cli/skills/) location — **Gemini CLI and Antigravity read it directly** from a clone of this repo, no extra step needed for either.

**Claude Code** only looks in `.claude/skills/` (project) or `~/.claude/skills/` (machine), and doesn't yet support the neutral `.agents/skills/` path — so it doesn't get these automatically from the repo. If you're working in this repo with Claude Code, install the skills globally instead:

```bash
uvx google-agents-cli setup        # or: npx skills add google/agents-cli
```

That installs to `~/.agents/skills/` and symlinks them into `~/.claude/skills/`, making them available across all your projects, not just this one.

## Refreshing

To pull newer skills from upstream into this repo's copy:

```bash
npx skills add google/agents-cli   # or: uvx google-agents-cli setup
# then, from the repo root:
rm -rf .agents/skills/google-agents-cli-*
for d in ~/.agents/skills/google-agents-cli-*/; do
  cp -r "$d" ".agents/skills/$(basename "$d")"
done
```
