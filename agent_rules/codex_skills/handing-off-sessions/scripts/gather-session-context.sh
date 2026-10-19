#!/usr/bin/env bash
# Gather session context for handoff document generation.
# Sources shared git-snapshot.sh and detect-project.sh for consistent output.
# Outputs structured markdown the agent can paste directly into a handoff.
#
# Usage:
#   ./gather-session-context.sh                    # current directory
#   ./gather-session-context.sh /path/to/project   # specified directory

set -euo pipefail

DIR="${1:-.}"
cd "$DIR" 2>/dev/null || { echo "ERROR: Cannot access $DIR"; exit 1; }

# --- Git snapshot (inlined for skill portability) ---
git_snapshot() {
  local dir="${1:-.}"
  local orig_dir="$(pwd)"
  cd "$dir" 2>/dev/null || return 1
  GIT_IS_REPO=false GIT_BRANCH="" GIT_LAST_COMMIT="" GIT_LAST_COMMIT_HASH=""
  GIT_DIRTY_COUNT=0 GIT_MODIFIED="" GIT_STAGED="" GIT_UNTRACKED="" GIT_RECENT_COMMITS="" GIT_STASH_COUNT=0
  if ! git rev-parse --is-inside-work-tree &>/dev/null; then cd "$orig_dir"; return 1; fi
  GIT_IS_REPO=true
  GIT_BRANCH=$(git branch --show-current 2>/dev/null || echo "detached")
  GIT_LAST_COMMIT=$(git log -1 --format='%h %s' 2>/dev/null || echo "none")
  GIT_LAST_COMMIT_HASH=$(git rev-parse --short HEAD 2>/dev/null || echo "none")
  GIT_DIRTY_COUNT=$(git status --short 2>/dev/null | wc -l | tr -d ' ')
  GIT_MODIFIED=$(git diff --name-only 2>/dev/null)
  GIT_STAGED=$(git diff --cached --name-only 2>/dev/null)
  GIT_UNTRACKED=$(git ls-files --others --exclude-standard 2>/dev/null)
  GIT_RECENT_COMMITS=$(git log --oneline -5 2>/dev/null)
  GIT_STASH_COUNT=$(git stash list 2>/dev/null | wc -l | tr -d ' ')
  cd "$orig_dir"
}
format_git_snapshot() {
  if [ "$GIT_IS_REPO" != "true" ]; then echo "_Not a git repository._"; return; fi
  echo "- **Branch**: $GIT_BRANCH"
  echo "- **Last commit**: $GIT_LAST_COMMIT"
  echo "- **Dirty files**: $GIT_DIRTY_COUNT"
  if [ "$GIT_STASH_COUNT" -gt 0 ]; then echo "- **Stashes**: $GIT_STASH_COUNT"; fi
  if [ -n "$GIT_STAGED" ]; then echo ""; echo "**Staged:**"; echo "$GIT_STAGED" | while read -r f; do [ -n "$f" ] && echo "- \`$f\`"; done; fi
  if [ -n "$GIT_MODIFIED" ]; then echo ""; echo "**Modified (unstaged):**"; echo "$GIT_MODIFIED" | while read -r f; do [ -n "$f" ] && echo "- \`$f\`"; done; fi
  if [ -n "$GIT_UNTRACKED" ]; then
    echo ""; echo "**Untracked:**"
    local count=$(echo "$GIT_UNTRACKED" | wc -l | tr -d ' ')
    echo "$GIT_UNTRACKED" | head -15 | while read -r f; do [ -n "$f" ] && echo "- \`$f\`"; done
    if [ "$count" -gt 15 ]; then echo "- _...and $((count - 15)) more_"; fi
  fi
  if [ -n "$GIT_RECENT_COMMITS" ]; then echo ""; echo "**Recent commits:**"; echo "$GIT_RECENT_COMMITS" | while read -r line; do [ -n "$line" ] && echo "- $line"; done; fi
}

# --- Project detection (inlined for skill portability) ---
detect_project() {
  local dir="${1:-.}"
  local orig_dir="$(pwd)"
  cd "$dir" 2>/dev/null || return 1
  PROJECT_TYPE="" PKG_MGR="" TEST_RUNNER="" LINTER="" TYPE_CHECKER="" BUILDER="" FRAMEWORK=""
  if [ -f "package.json" ]; then
    PROJECT_TYPE="node"
    if [ -f "pnpm-lock.yaml" ]; then PKG_MGR="pnpm"
    elif [ -f "bun.lockb" ] || [ -f "bun.lock" ]; then PKG_MGR="bun"
    elif [ -f "yarn.lock" ]; then PKG_MGR="yarn"
    else PKG_MGR="npm"; fi
    if [ -f "tsconfig.json" ]; then PROJECT_TYPE="typescript"; fi
  elif [ -f "Cargo.toml" ]; then PROJECT_TYPE="rust"; PKG_MGR="cargo"
  elif [ -f "go.mod" ]; then PROJECT_TYPE="go"; PKG_MGR="go"
  elif [ -f "pyproject.toml" ] || [ -f "setup.py" ] || [ -f "requirements.txt" ]; then
    PROJECT_TYPE="python"
    if [ -f "poetry.lock" ]; then PKG_MGR="poetry"
    elif [ -f "Pipfile.lock" ]; then PKG_MGR="pipenv"
    elif [ -f "uv.lock" ]; then PKG_MGR="uv"
    else PKG_MGR="pip"; fi
  elif [ -f "Gemfile" ]; then PROJECT_TYPE="ruby"; PKG_MGR="bundler"
  elif [ -f "build.gradle" ] || [ -f "build.gradle.kts" ] || [ -f "pom.xml" ]; then
    PROJECT_TYPE="java"
    if [ -f "build.gradle" ] || [ -f "build.gradle.kts" ]; then PKG_MGR="gradle"; else PKG_MGR="maven"; fi
  fi
  case "$PROJECT_TYPE" in
    node|typescript)
      if [ -f "vitest.config.ts" ] || [ -f "vitest.config.js" ]; then TEST_RUNNER="$PKG_MGR run test"
      elif [ -f "jest.config.js" ] || [ -f "jest.config.ts" ] || ([ -f "package.json" ] && grep -q '"jest"' package.json 2>/dev/null); then TEST_RUNNER="$PKG_MGR test"
      elif [ -f "package.json" ] && grep -q '"test"' package.json 2>/dev/null; then TEST_RUNNER="$PKG_MGR test"; fi ;;
    rust) TEST_RUNNER="cargo test" ;; go) TEST_RUNNER="go test ./..." ;;
    python)
      if [ -f "pytest.ini" ] || [ -f "conftest.py" ] || ([ -f "pyproject.toml" ] && grep -q "pytest" pyproject.toml 2>/dev/null); then TEST_RUNNER="python -m pytest"
      elif [ -d "tests" ] || [ -d "test" ]; then TEST_RUNNER="python -m pytest"
      else TEST_RUNNER="python -m unittest discover"; fi ;;
    ruby) TEST_RUNNER="bundle exec rspec" ;;
    java) if [ "$PKG_MGR" = "gradle" ]; then TEST_RUNNER="./gradlew test"; else TEST_RUNNER="mvn test"; fi ;;
  esac
  case "$PROJECT_TYPE" in
    node|typescript) if [ -f "package.json" ] && grep -q '"build"' package.json 2>/dev/null; then BUILDER="$PKG_MGR run build"; fi ;;
    rust) BUILDER="cargo build" ;; go) BUILDER="go build ./..." ;;
    java) if [ "$PKG_MGR" = "gradle" ]; then BUILDER="./gradlew build"; else BUILDER="mvn package"; fi ;;
  esac
  cd "$orig_dir"
}

HAS_GIT_SNAPSHOT=true
HAS_DETECT_PROJECT=true

echo "# Session Context"
echo "_Gathered: $(date -u +%Y-%m-%dT%H:%M:%SZ)_"
echo ""

# --- Environment ---
echo "## Environment"
echo "- **CWD**: $(pwd)"
echo "- **OS**: $(uname -s) $(uname -r) ($(uname -m))"
echo "- **Shell**: ${SHELL:-unknown}"
echo "- **User**: ${USER:-unknown}"
if command -v node &>/dev/null; then echo "- **Node**: $(node --version 2>/dev/null)"; fi
if command -v python3 &>/dev/null; then echo "- **Python**: $(python3 --version 2>/dev/null)"; fi
if command -v go &>/dev/null; then echo "- **Go**: $(go version 2>/dev/null | awk '{print $3}')"; fi
if command -v rustc &>/dev/null; then echo "- **Rust**: $(rustc --version 2>/dev/null)"; fi
echo ""

# --- Git state ---
echo "## Git State"
if [ "$HAS_GIT_SNAPSHOT" = "true" ]; then
  git_snapshot "."
  format_git_snapshot
else
  if git rev-parse --is-inside-work-tree &>/dev/null; then
    echo "- **Branch**: $(git branch --show-current 2>/dev/null || echo 'detached')"
    echo "- **Last commit**: $(git log -1 --format='%h %s' 2>/dev/null || echo 'none')"
    echo "- **Dirty files**: $(git status --short 2>/dev/null | wc -l | tr -d ' ')"
  else
    echo "_Not a git repository._"
  fi
fi
echo ""

# --- Project detection ---
echo "## Project Detection"
if [ "$HAS_DETECT_PROJECT" = "true" ]; then
  detect_project "."
  echo "- **Type**: ${PROJECT_TYPE:-unknown}"
  echo "- **Package manager**: ${PKG_MGR:-not detected}"
  if [ -n "$FRAMEWORK" ]; then echo "- **Framework**: $FRAMEWORK"; fi
  if [ -n "$TEST_RUNNER" ]; then echo "- **Test runner**: $TEST_RUNNER"; fi
  if [ -n "$BUILDER" ]; then echo "- **Builder**: $BUILDER"; fi
else
  if [ -f "package.json" ]; then echo "- **Type**: Node.js"
  elif [ -f "Cargo.toml" ]; then echo "- **Type**: Rust"
  elif [ -f "go.mod" ]; then echo "- **Type**: Go"
  elif [ -f "pyproject.toml" ] || [ -f "requirements.txt" ]; then echo "- **Type**: Python"
  else echo "- **Type**: Unknown"; fi
fi
echo ""

# --- Recently modified files ---
echo "## Recently Modified Files (last 10)"
echo ""
echo "| File | Modified | Size |"
echo "|------|----------|------|"
if [ "$(uname)" = "Darwin" ]; then
  find . -maxdepth 4 -type f \
    -not -path '*/node_modules/*' -not -path '*/.git/*' \
    -not -path '*/dist/*' -not -path '*/build/*' -not -path '*/__pycache__/*' \
    -not -path '*/target/*' -not -path '*/.next/*' \
    \( -name '*.ts' -o -name '*.js' -o -name '*.py' -o -name '*.go' -o -name '*.rs' \
    -o -name '*.rb' -o -name '*.java' -o -name '*.md' -o -name '*.json' \
    -o -name '*.yaml' -o -name '*.yml' -o -name '*.toml' -o -name '*.sh' \) 2>/dev/null \
    | head -50 \
    | xargs -I{} stat -f "%m %N %z" {} 2>/dev/null \
    | sort -rn | head -10 \
    | while read -r ts file size; do
        modified=$(date -r "$ts" +%Y-%m-%d 2>/dev/null || echo "unknown")
        echo "| \`$file\` | $modified | ${size}B |"
      done
else
  find . -maxdepth 4 -type f \
    -not -path '*/node_modules/*' -not -path '*/.git/*' \
    -not -path '*/dist/*' -not -path '*/build/*' -not -path '*/__pycache__/*' \
    -not -path '*/target/*' -not -path '*/.next/*' \
    \( -name '*.ts' -o -name '*.js' -o -name '*.py' -o -name '*.go' -o -name '*.rs' \
    -o -name '*.rb' -o -name '*.java' -o -name '*.md' -o -name '*.json' \
    -o -name '*.yaml' -o -name '*.yml' -o -name '*.toml' -o -name '*.sh' \) \
    -printf '%T@ %p %s\n' 2>/dev/null \
    | sort -rn | head -10 \
    | while read -r ts file size; do
        modified=$(date -d "@${ts%.*}" +%Y-%m-%d 2>/dev/null || echo "unknown")
        echo "| \`$file\` | $modified | ${size}B |"
      done
fi
echo ""

# --- Directory structure (top 2 levels) ---
echo "## Project Structure (top 2 levels)"
echo '```'
if command -v tree &>/dev/null; then
  tree -L 2 -d --noreport -I 'node_modules|.git|dist|build|__pycache__|target|.next|.turbo|coverage' 2>/dev/null || ls -d */ 2>/dev/null
else
  find . -maxdepth 2 -type d \
    -not -path '*/node_modules*' -not -path '*/.git*' \
    -not -path '*/dist*' -not -path '*/build*' -not -path '*/__pycache__*' \
    -not -path '*/target*' -not -path '*/.next*' \
    2>/dev/null | sort | head -30
fi
echo '```'
