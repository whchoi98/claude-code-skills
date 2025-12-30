#!/bin/bash
# Sync skills from repo to Claude Code skills directory
# Usage: ./scripts/sync-skills.sh [skill_name]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
SKILLS_SRC="$REPO_ROOT/skills"
SKILLS_DEST="$HOME/.claude/skills"

# Create destination directory if not exists
mkdir -p "$SKILLS_DEST"

sync_skill() {
    local skill_name="$1"
    local skill_dir="$SKILLS_SRC/$skill_name"

    if [[ ! -d "$skill_dir" ]]; then
        echo "Error: Skill '$skill_name' not found in $SKILLS_SRC"
        return 1
    fi

    if [[ ! -f "$skill_dir/SKILL.md" ]]; then
        echo "Error: SKILL.md not found in $skill_dir"
        return 1
    fi

    # Copy SKILL.md as skill_name.md
    cp "$skill_dir/SKILL.md" "$SKILLS_DEST/${skill_name}.md"
    echo "Synced: $skill_name -> $SKILLS_DEST/${skill_name}.md"
}

# If specific skill name provided, sync only that skill
if [[ -n "$1" ]]; then
    sync_skill "$1"
else
    # Sync all skills
    echo "Syncing all skills to $SKILLS_DEST..."
    for skill_dir in "$SKILLS_SRC"/*/; do
        if [[ -d "$skill_dir" ]]; then
            skill_name=$(basename "$skill_dir")
            if [[ -f "$skill_dir/SKILL.md" ]]; then
                sync_skill "$skill_name"
            fi
        fi
    done
fi

echo "Done!"
