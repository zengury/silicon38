# Caveman Analysis: manastone

## What is manastone?

Manastone = robot agent. Lets you talk to robot, robot talks back. Like Siri for robot body.

## What is the problem?

1. **Install confusing.** User runs `install.sh` but doesn't know what they get. Pi brand visible. Manastone hidden behind Pi.
2. **Too many ways to use.** CLI, TUI, daemon, MCP, Pi agent. New user lost.
3. **Brand leak.** Pi shows up in package names, config paths, docs. Manastone not standalone.

## Minimum Viable Version

One command install. One command run. No Pi mention.

- `curl https://manastone.dev/install | bash` -> installs everything, no extra steps.
- `manastone start` -> starts agent, connects to robot, opens chat.
- `manastone diagnose` -> runs health check, prints plain-English result.

That's it. No pack selection, no config editing, no Pi setup.

## Complexity Assessment

### Justified complexity

- Robot-specific ontology packs (X2 vs G1). Different hardware needs different config.
- Safety checks. Robot can hurt people. Must be thorough.
- Diagnostics engine. Helps fix broken robots.

### Unnecessary complexity

- **Pi brand everywhere.** Package.json says `@mariozechner/pi-coding-agent`. Config paths reference Pi. Docs say "Pi + Runtime integrated". User doesn't care about Pi. Manastone should be the only name.
- **Multiple install paths.** `--pack=x2`, `--pack=g1`, `--pack=dev`. User shouldn't choose. Auto-detect robot or default to safe mode.
- **Config file required.** `~/.manastone/config.yaml`. New user has no config. Should work out of box with defaults.
- **Daemon vs CLI vs TUI.** Too many entry points. One command `manastone` should do the right thing.
- **Bootstrap README mentions ARCHITECTURE sections.** User doesn't care about internal docs.

## What to fix first

1. **Brand isolation.** Rename all Pi references to Manastone. Package names, config paths, docs, code comments.
2. **Single install command.** `install.sh` without flags. Auto-detect robot or install generic.
3. **Zero-config startup.** `manastone start` works without config file.
4. **One entry point.** `manastone` CLI dispatches to TUI, daemon, or diagnose based on context.

## So what?

Without these fixes: new users bounce off. They see Pi, get confused, leave. Manastone looks like a side project, not a product.

With fixes: user installs, runs, talks to robot. 5 minutes. That's the goal.