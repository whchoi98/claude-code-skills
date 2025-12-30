# Claude Code Skills

Custom skills for Claude Code CLI.

## Structure

```
claude-code-skills/
├── skills/           # Skill definitions (.md files)
├── hooks/            # Custom hooks
└── README.md
```

## Usage

Skills can be invoked in Claude Code using `/skill-name` command.

## Skills

| Skill | Description |
|-------|-------------|
| [aws](skills/aws.md) | AWS 리소스 관리 (EC2, S3, IAM, CloudFormation, Lambda, EKS 등) |

## Installation

Copy skill files to your Claude Code configuration directory:

```bash
cp skills/*.md ~/.claude/skills/
```

## License

MIT
