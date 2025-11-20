#!/usr/bin/env python3
"""
Skill Packager - Creates a distributable .skill file of a skill folder

Usage:
    python utils/package_skill.py <path/to/skill-folder> [output-directory]

Example:
    python utils/package_skill.py skills/public/my-skill
    python utils/package_skill.py skills/public/my-skill ./dist
"""

import sys
import zipfile
import fnmatch
from pathlib import Path
from quick_validate import validate_skill


def read_skillignore(skill_path):
    """
    Read .skillignore file and return list of patterns to exclude.

    Args:
        skill_path: Path to skill directory

    Returns:
        List of patterns to exclude (empty list if no .skillignore file)
    """
    skillignore_path = skill_path / ".skillignore"
    if not skillignore_path.exists():
        return []

    try:
        patterns = []
        content = skillignore_path.read_text()
        for line in content.splitlines():
            line = line.strip()
            # Skip empty lines and comments
            if line and not line.startswith("#"):
                patterns.append(line)
        return patterns
    except Exception:
        return []


def should_exclude(file_path, skill_path, exclude_patterns):
    """
    Check if a file should be excluded based on .skillignore patterns.

    Args:
        file_path: Path to file (absolute)
        skill_path: Path to skill directory (absolute)
        exclude_patterns: List of gitignore-style patterns

    Returns:
        True if file should be excluded, False otherwise
    """
    if not exclude_patterns:
        return False

    # Get relative path from skill directory
    try:
        rel_path = file_path.relative_to(skill_path)
    except ValueError:
        # If we can't get relative path, include it
        return False

    rel_path_str = str(rel_path)

    for pattern in exclude_patterns:
        # Handle directory patterns (ending with /)
        if pattern.endswith("/"):
            if rel_path_str.startswith(pattern) or (rel_path_str + "/").startswith(
                pattern
            ):
                return True

        # Handle file patterns
        if fnmatch.fnmatch(rel_path_str, pattern) or fnmatch.fnmatch(
            file_path.name, pattern
        ):
            return True

        # Handle patterns with wildcards in path components
        if "/" in pattern:
            pattern_parts = pattern.split("/")
            rel_parts = rel_path_str.split("/")

            # Check if pattern matches any part of the path
            for i in range(len(rel_parts) - len(pattern_parts) + 1):
                test_path = "/".join(rel_parts[i : i + len(pattern_parts)])
                if fnmatch.fnmatch(test_path, pattern):
                    return True

    return False


def package_skill(skill_path, output_dir=None):
    """
    Package a skill folder into a .skill file.

    Args:
        skill_path: Path to skill folder
        output_dir: Optional output directory for .skill file (defaults to current directory)

    Returns:
        Path to created .skill file, or None if error
    """
    skill_path = Path(skill_path).resolve()

    # Validate skill folder exists
    if not skill_path.exists():
        print(f"❌ Error: Skill folder not found: {skill_path}")
        return None

    if not skill_path.is_dir():
        print(f"❌ Error: Path is not a directory: {skill_path}")
        return None

    # Validate SKILL.md exists
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        print(f"❌ Error: SKILL.md not found in {skill_path}")
        return None

    # Run validation before packaging
    print("🔍 Validating skill...")
    valid, message = validate_skill(skill_path)
    if not valid:
        print(f"❌ Validation failed: {message}")
        print("   Please fix validation errors before packaging.")
        return None
    print(f"✅ {message}\n")

    # Determine output location
    skill_name = skill_path.name
    if output_dir:
        output_path = Path(output_dir).resolve()
        output_path.mkdir(parents=True, exist_ok=True)
    else:
        output_path = Path.cwd()

    skill_filename = output_path / f"{skill_name}.skill"

    # Read exclusion patterns from .skillignore
    exclude_patterns = read_skillignore(skill_path)
    if exclude_patterns:
        print(f"📋 Using .skillignore with {len(exclude_patterns)} exclusion patterns")

    # Create .skill file (zip format)
    try:
        with zipfile.ZipFile(skill_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
            files_added = 0
            files_excluded = 0

            # Walk through the skill directory
            for file_path in skill_path.rglob("*"):
                if file_path.is_file():
                    # Check if file should be excluded
                    if should_exclude(file_path, skill_path, exclude_patterns):
                        files_excluded += 1
                        continue

                    # Calculate the relative path within the zip
                    arcname = file_path.relative_to(skill_path.parent)
                    zipf.write(file_path, arcname)
                    print(f"  Added: {arcname}")
                    files_added += 1

            if files_excluded > 0:
                print(f"  Excluded: {files_excluded} files (per .skillignore)")

        print(f"\n✅ Successfully packaged skill to: {skill_filename}")
        print(f"   📊 Packaged {files_added} files")
        return skill_filename

    except Exception as e:
        print(f"❌ Error creating .skill file: {e}")
        return None


def main():
    if len(sys.argv) < 2:
        print("Usage: package_skill.py <path/to/skill-folder> [output-directory]")
        print("\n⚠️  IMPORTANT: This script must be run from skill-creator directory!")
        print("   First run: cd .agent/skills/skill-creator")
        print(
            "   Then run: uv run --no-active scripts/package_skill.py <path/to/skill-folder>"
        )
        print("\nComplete examples:")
        print("  cd .agent/skills/skill-creator")
        print("  uv run --no-active scripts/package_skill.py skills/public/my-skill")
        print("  cd .agent/skills/skill-creator")
        print(
            "  uv run --no-active scripts/package_skill.py skills/public/my-skill ./dist"
        )
        sys.exit(1)

    skill_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"📦 Packaging skill: {skill_path}")
    if output_dir:
        print(f"   Output directory: {output_dir}")
    print()

    result = package_skill(skill_path, output_dir)

    if result:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
