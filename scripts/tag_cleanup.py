#!/usr/bin/env python3
"""
Tag cleanup helper script for CI/CD.
Removes old build and dev tags according to project policy.
"""

import subprocess
import re
import sys
from datetime import datetime, timedelta
from typing import List, Tuple

def get_all_tags() -> List[Tuple[str, str]]:
    """Get all tags with their creation dates."""
    try:
        result = subprocess.run(
            ['git', 'for-each-ref', '--format=%(refname:short)|%(creatordate:iso8601)', 'refs/tags'],
            capture_output=True,
            text=True,
            check=True
        )
        tags = []
        for line in result.stdout.strip().split('\n'):
            if '|' in line:
                tag, date_str = line.split('|', 1)
                tags.append((tag, date_str))
        return tags
    except subprocess.CalledProcessError:
        return []

def is_build_tag(tag: str) -> bool:
    """Check if tag is a build tag (contains .b followed by number)."""
    return bool(re.search(r'\\.b\\d+$', tag))

def is_dev_tag(tag: str) -> bool:
    """Check if tag is a dev tag (contains -dev)."""
    return '-dev' in tag

def is_old_tag(date_str: str, days: int = 30) -> bool:
    """Check if tag is older than specified days."""
    try:
        tag_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        cutoff_date = datetime.now().astimezone() - timedelta(days=days)
        return tag_date < cutoff_date
    except Exception:
        return False

def main():
    dry_run = sys.argv[1].lower() == 'true' if len(sys.argv) > 1 else True

    all_tags = get_all_tags()
    if not all_tags:
        print("No tags found.")
        return

    tags_to_delete = []
    for tag, date_str in all_tags:
        should_delete = False
        reason = ""
        if is_build_tag(tag) and is_old_tag(date_str, 7):
            should_delete = True
            reason = "old build tag (>7 days)"
        elif is_dev_tag(tag) and is_old_tag(date_str, 30):
            should_delete = True
            reason = "old dev tag (>30 days)"
        if should_delete:
            tags_to_delete.append((tag, reason))

    if not tags_to_delete:
        print("No tags need cleanup.")
        return

    print(f"Found {len(tags_to_delete)} tags for cleanup:")
    for tag, reason in tags_to_delete:
        print(f"  - {tag} ({reason})")

    if dry_run:
        print("\\nDry run mode - no tags were actually deleted.")
        return

    deleted_count = 0
    for tag, reason in tags_to_delete:
        try:
            subprocess.run(['git', 'tag', '-d', tag], check=True, capture_output=True)
            subprocess.run(['git', 'push', 'origin', '--delete', tag], check=True, capture_output=True)
            print(f"Deleted {tag} ({reason})")
            deleted_count += 1
        except subprocess.CalledProcessError as e:
            print(f"Failed to delete {tag}: {e}")

    print(f"\\nDeleted {deleted_count} tags.")

if __name__ == '__main__':
    main()