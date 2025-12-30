# Claude Code Skills

Custom skills for Claude Code CLI.

## Structure

```
claude-code-skills/
├── skills/
│   └── <skill-name>/
│       ├── SKILL.md          # Main skill definition (required)
│       ├── reference/        # Additional reference docs (optional)
│       └── scripts/          # Utility scripts (optional)
├── hooks/                    # Custom hooks
├── scripts/
│   └── sync-skills.sh        # Deploy skills to ~/.claude/skills/
└── README.md
```

## Skills

| Skill | Description |
|-------|-------------|
| [aws](skills/aws/SKILL.md) | AWS 리소스 관리 (MCP, Steampipe, CLI) |

## Installation

### Sync All Skills

```bash
./scripts/sync-skills.sh
```

### Sync Specific Skill

```bash
./scripts/sync-skills.sh aws
```

### Manual Copy

```bash
cp skills/aws/SKILL.md ~/.claude/skills/aws.md
```

## Creating a New Skill

1. Create skill directory:
   ```bash
   mkdir -p skills/<skill-name>/{reference,scripts}
   ```

2. Create `SKILL.md` with the skill definition

3. (Optional) Add reference docs and utility scripts

4. Sync to Claude Code:
   ```bash
   ./scripts/sync-skills.sh <skill-name>
   ```

## Skill File Guidelines

- Keep `SKILL.md` under 500 lines for optimal performance
- Use `reference/` for detailed documentation (loaded on-demand)
- Use `scripts/` for utility scripts that can be executed

## License

MIT
