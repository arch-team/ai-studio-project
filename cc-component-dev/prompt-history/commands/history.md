---
description: Display and search Claude Code prompt history (like Linux history command)
argument-hint: [count or filter description]
allowed-tools: Read, AskUserQuestion
---

Read the prompt history from `~/.claude/history.jsonl` and display it to the user.

**File to read**: `~/.claude/history.jsonl` (expand ~ to user home directory)

## History File Format

Each line in the file is a JSON object with these fields:
- `display`: The prompt content
- `timestamp`: Unix timestamp in milliseconds
- `project`: Absolute project path
- `sessionId`: Session ID (optional, newer records have this)

## Instructions

1. **Read the history file** using Read tool with path `/Users/$USER/.claude/history.jsonl` or detect home directory

2. **Parse and process** each JSON line to extract:
   - Prompt content (`display`)
   - Timestamp (convert to human-readable: `YYYY-MM-DD HH:MM`)
   - Project path (extract last directory name as project identifier)

3. **Apply filters based on user arguments** ($ARGUMENTS):
   - If argument is a number (e.g., "50"): Show that many recent records
   - If argument contains keywords like "搜索", "search", "查找": Filter by keyword after it
   - If argument mentions a project name: Filter by project path containing that name
   - If argument mentions time ("今天", "today", "本周", "this week"): Filter by time range
   - If no argument: Show last 20 records by default

4. **Display format** (IMPORTANT: Keep each record on ONE line):

   Use a markdown table format:
   ```
   | # | 时间 | 项目 | Prompt |
   |---|------|------|--------|
   | 4295 | 01-18 01:09 | cc-component-dev | 重新问题澄清 |
   | 4294 | 01-18 01:08 | cc-component-dev | 继续 |
   | 4293 | 01-18 01:05 | ai-studio-project | Implement the following plan... ⋯ |
   ```

5. **For long prompts** (>60 characters):
   - Truncate to first 60 characters
   - Add ` ⋯` suffix to indicate truncation
   - Replace newlines with spaces to keep single line

6. **After displaying the table**, use AskUserQuestion to ask:
   ```
   "输入序号可展开查看完整 prompt，或输入 'q' 退出"
   ```

   Options:
   - Show specific record number
   - "q" or "退出" to exit

7. **When user selects a record number**:
   - Display the FULL prompt content for that record
   - Show all metadata (time, project path, session ID)
   - Ask if user wants to re-execute this prompt

## User Arguments

$ARGUMENTS

## Examples

- `/history` → Show last 20 records in table format
- `/history 50` → Show last 50 records
- `/history 搜索 git` → Search for "git" in prompts
- `/history ai-studio` → Filter by project name containing "ai-studio"
- `/history 今天` → Show today's records only
