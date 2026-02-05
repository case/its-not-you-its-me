# "It’s not you, it’s me"

Is a cloud thing erroring? Check its status page from wherever you are`*`.

`*` This is currently just for [Claude Code](https://code.claude.com/docs/en/overview), but it could easily be expanded to work with other tools if you are interested in contributing. See below.

## Background

This is a Claude Code [skill](https://code.claude.com/docs/en/skills) that lets you type `/status-page` to see if Claude is having any active incidents. I was ~~annoyed~~ inspired to make it while doing some work one morning, and repeatedly saw this:

```
API Error: 500 {"type":"error","error":{"type":"api_error","message":"Internal server error"},"request_id":"{a-real-hash}"}
```

https://status.claude.com/ showed an active incident at the time, so this would have saved a few steps.

It's also fun to make stuff like this. :)

## Installation

1. Clone this repo
2. Run `make install` - which simply uses `cp` to copy the needed files to `~/.claude/skills/status-page`
3. Restart Claude Code, so that it can discover the new skill

If the `status-page` directory already exists, installation will stop. You can run `make install-force` to write over the existing dir.

**Prerequisites:** `python3` must be installed and in your `PATH`, because this skill works by running the `check_status.py` script.

If you'd like to uninstall it for some reason, `make uninstall` is available.

## Usage

From within Claude Code:

- `/status-page` - shows if the Claude status page has any active incidents
- `/status-page gh` - check if GitHub has any active incidents

The output looks like this:

```
❯ /status-page

⏺ Bash(python3 ~/.claude/skills/status-page/scripts/check_status.py)
  ⎿  Running…

────────────────────────────────────────────────────────────────────────────────────────
 Bash command

   python3 ~/.claude/skills/status-page/scripts/check_status.py
   Check Claude status page

 Do you want to proceed?
 ❯ 1. Yes
 <snip>
 
⏺ No active incidents on Claude. The last incident was 2026-02-04 17:06 UTC (09:06 PST).
```

## Supported Services & status pages

- [Claude](https://status.claude.com/) from Anthropic
- [GitHub](https://www.githubstatus.com/)

## Codebase

This is written in Python 3, which has all the needed functionality in the stdlib. It has no third-party dependencies.

## Contribute

If you'd like to contribute, the code is sufficiently generalized that we could easily support other tools.

`make test` will run the tests.

Well-designed and implemented Pull Requests are accepted, as long as:

1. They include tests
2. The tests pass
3. They don't include anything malicious
4. They are authored and submitted by a person - LLM-assisted code is fine, but you need to review and curate it accordingly before submitting it.
