#!/usr/bin/env bash
set -euo pipefail

# Universal Python Skill Runner
# Usage: run_python_skill.sh <skill-name> <script-name> [args...]
# Example: run_python_skill.sh html-to-markdown convert.py input.html -o output.md
#
# Environment Variables:
#   SKILL_DIR    Base directory containing skills (default: .agent/skills/)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print usage
usage() {
  echo "Usage: $0 <skill-name> <script-name> [args...]"
  echo ""
  echo "Arguments:"
  echo "  skill-name    Name of the skill directory (e.g., html-to-markdown)"
  echo "  script-name   Name of the Python script in scripts/ (e.g., convert.py)"
  echo "  args...       Additional arguments to pass to the Python script"
  echo ""
  echo "Environment Variables:"
  echo "  SKILL_DIR     Base directory containing skills (default: .agent/skills/)"
  echo ""
  echo "Examples:"
  echo "  $0 html-to-markdown convert.py input.html"
  echo "  $0 document-skills/docx convert.py document.docx"
  echo "  $0 document-skills/pdf split.py input.pdf --pages 1-5"
  echo "  $0 office-skills/excel/advanced analyze.py data.xlsx --sheet summary"
  echo "  SKILL_DIR=/custom/skills $0 html-to-markdown convert.py input.html"
  echo "  $0 skill-creator init_skill.py my-skill --path skills/"
  echo "  $0 python-whatsnew-extractor fetch_whatsnew.py 3.13"
  echo ""
  echo "Default skill path: .agent/skills/"
}

# Function to print error and exit
error() {
  echo -e "${RED}Error: $1${NC}" >&2
  exit 1
}

# Function to print success message
success() {
  echo -e "${GREEN}✓ $1${NC}"
}

# Check minimum arguments
if [[ $# -lt 2 ]]; then
  error "Insufficient arguments"
  usage
  exit 1
fi

# Parse arguments
SKILL_NAME="$1"
SCRIPT_NAME="$2"
shift 2 # Remove first two arguments, keep the rest for Python script

# Validate skill name (allow subdirectories)
if [[ ! "$SKILL_NAME" =~ ^[a-z0-9/-]+$ ]]; then
  error "Invalid skill name '$SKILL_NAME'. Must contain only lowercase letters, numbers, hyphens, and forward slashes for subdirectories."
fi

# Validate script name
if [[ ! "$SCRIPT_NAME" =~ ^[a-zA-Z0-9_-]+\.py$ ]]; then
  error "Invalid script name '$SCRIPT_NAME'. Must be a Python file ending in .py"
fi

# Determine skill directory
if [[ -n "${SKILL_DIR:-}" ]]; then
  # Use SKILL_DIR from environment if set
  SKILL_FULL_PATH="$SKILL_DIR/$SKILL_NAME"
  echo -e "${YELLOW}Using custom skill directory: $SKILL_DIR${NC}"
else
  # Default to .agent/skills/ relative to project root
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
  SKILL_FULL_PATH="$PROJECT_ROOT/.agent/skills/$SKILL_NAME"
fi

# Normalize path (remove redundant slashes, resolve . and ..)
SKILL_FULL_PATH="$(realpath -m "$SKILL_FULL_PATH")"

# Check if skill directory exists
if [[ ! -d "$SKILL_FULL_PATH" ]]; then
  error "Skill directory not found: $SKILL_FULL_PATH"
fi

# Check if pyproject.toml exists (required for uv)
if [[ ! -f "$SKILL_FULL_PATH/pyproject.toml" ]]; then
  error "pyproject.toml not found in skill directory: $SKILL_FULL_PATH"
fi

# Check if script exists
SCRIPT_PATH="$SKILL_FULL_PATH/scripts/$SCRIPT_NAME"
if [[ ! -f "$SCRIPT_PATH" ]]; then
  error "Script not found: $SCRIPT_PATH"
fi

# Check if script is executable
if [[ ! -x "$SCRIPT_PATH" ]]; then
  echo -e "${YELLOW}Warning: Script $SCRIPT_NAME is not executable. Making it executable...${NC}"
  chmod +x "$SCRIPT_PATH"
fi

# Check if uv is available
if ! command -v uv &>/dev/null; then
  error "uv is not installed or not in PATH. Please install uv first."
fi

# Change to skill directory and run the script
echo -e "${GREEN}Running skill '$SKILL_NAME' with script '$SCRIPT_NAME'...${NC}"
echo -e "${GREEN}Skill path: $SKILL_FULL_PATH${NC}"

# Store current directory
ORIGINAL_DIR="$(pwd)"

# Change to skill directory and execute
#cd "$SKILL_FULL_PATH"

# Run the script with uv, passing all remaining arguments
if uv run --project $SKILL_FULL_PATH --no-active "$SKILL_FULL_PATH/scripts/$SCRIPT_NAME" "$@"; then
  success "Script executed successfully"
  EXIT_CODE=0
else
  EXIT_CODE=$?
  echo -e "${RED}Script failed with exit code $EXIT_CODE${NC}" >&2
fi

# Return to original directory
cd "$ORIGINAL_DIR"

exit $EXIT_CODE
