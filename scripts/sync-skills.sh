#!/bin/bash
# Sync skills from repo to Claude Code skills directory
# Usage: ./scripts/sync-skills.sh [skill_name]
#
# New structure: ~/.claude/skills/<skill_name>/
#   ├── SKILL.md
#   └── reference/
#       └── *.md

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
    local dest_dir="$SKILLS_DEST/$skill_name"

    if [[ ! -d "$skill_dir" ]]; then
        echo "Error: Skill '$skill_name' not found in $SKILLS_SRC"
        return 1
    fi

    if [[ ! -f "$skill_dir/SKILL.md" ]]; then
        echo "Error: SKILL.md not found in $skill_dir"
        return 1
    fi

    # Create skill directory
    mkdir -p "$dest_dir"

    # Copy SKILL.md
    cp "$skill_dir/SKILL.md" "$dest_dir/SKILL.md"
    echo "Synced: $skill_name/SKILL.md"

    # Copy reference directory if exists
    if [[ -d "$skill_dir/reference" ]]; then
        mkdir -p "$dest_dir/reference"
        cp -r "$skill_dir/reference/"* "$dest_dir/reference/" 2>/dev/null || true
        echo "Synced: $skill_name/reference/ ($(ls -1 "$skill_dir/reference" 2>/dev/null | wc -l) files)"
    fi

    # Copy scripts directory if exists
    if [[ -d "$skill_dir/scripts" ]]; then
        mkdir -p "$dest_dir/scripts"
        cp -r "$skill_dir/scripts/"* "$dest_dir/scripts/" 2>/dev/null || true
        echo "Synced: $skill_name/scripts/"
    fi

    echo "  -> $dest_dir/"
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
