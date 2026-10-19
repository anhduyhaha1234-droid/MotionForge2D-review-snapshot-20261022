#!/usr/bin/env bash
# Estimate token count for files or stdin.
# Uses the ~4 chars per token heuristic (conservative for English code).
# Helps the agent decide when compaction is needed and budget remaining.
#
# Usage:
#   echo "some text" | ./estimate-tokens.sh
#   ./estimate-tokens.sh file1.md file2.ts
#   ./estimate-tokens.sh --context-check 128000    # check against a context window size
#
# Output: structured token estimates per file and total.

set -euo pipefail

CHARS_PER_TOKEN=4
CONTEXT_WINDOW=0

if [ "${1:-}" = "--context-check" ]; then
  CONTEXT_WINDOW="${2:-128000}"
  shift 2
fi

estimate_tokens() {
  local chars="$1"
  echo $(( (chars + CHARS_PER_TOKEN - 1) / CHARS_PER_TOKEN ))
}

format_number() {
  local n="$1"
  if [ "$n" -ge 1000000 ]; then
    echo "$((n / 1000))K"
  elif [ "$n" -ge 1000 ]; then
    echo "$((n / 1000))K"
  else
    echo "$n"
  fi
}

TOTAL_CHARS=0
TOTAL_TOKENS=0
FILE_COUNT=0

echo "# Token Estimate"
echo ""

if [ $# -eq 0 ]; then
  content=$(cat)
  chars=${#content}
  tokens=$(estimate_tokens "$chars")
  lines=$(echo "$content" | wc -l | tr -d ' ')
  TOTAL_CHARS=$chars
  TOTAL_TOKENS=$tokens
  FILE_COUNT=1
  echo "| Source | Lines | Chars | Est. Tokens |"
  echo "|--------|-------|-------|-------------|"
  echo "| stdin | $lines | $chars | $tokens |"
else
  echo "| File | Lines | Chars | Est. Tokens |"
  echo "|------|-------|-------|-------------|"
  for file in "$@"; do
    if [ -f "$file" ]; then
      chars=$(wc -c < "$file" | tr -d ' ')
      lines=$(wc -l < "$file" | tr -d ' ')
      tokens=$(estimate_tokens "$chars")
      TOTAL_CHARS=$((TOTAL_CHARS + chars))
      TOTAL_TOKENS=$((TOTAL_TOKENS + tokens))
      FILE_COUNT=$((FILE_COUNT + 1))
      echo "| $(basename "$file") | $lines | $chars | $tokens |"
    elif [ -d "$file" ]; then
      dir_chars=0
      dir_lines=0
      dir_files=0
      while IFS= read -r -d '' f; do
        c=$(wc -c < "$f" | tr -d ' ')
        l=$(wc -l < "$f" | tr -d ' ')
        dir_chars=$((dir_chars + c))
        dir_lines=$((dir_lines + l))
        dir_files=$((dir_files + 1))
      done < <(find "$file" -type f \( -name '*.md' -o -name '*.ts' -o -name '*.js' -o -name '*.py' -o -name '*.go' -o -name '*.rs' -o -name '*.rb' -o -name '*.java' -o -name '*.json' -o -name '*.yaml' -o -name '*.yml' -o -name '*.toml' -o -name '*.txt' -o -name '*.sh' \) -print0)
      dir_tokens=$(estimate_tokens "$dir_chars")
      TOTAL_CHARS=$((TOTAL_CHARS + dir_chars))
      TOTAL_TOKENS=$((TOTAL_TOKENS + dir_tokens))
      FILE_COUNT=$((FILE_COUNT + dir_files))
      echo "| $file/ ($dir_files files) | $dir_lines | $dir_chars | $dir_tokens |"
    else
      echo "| $file | — | — | NOT FOUND |"
    fi
  done
fi

echo ""
echo "**Total**: $FILE_COUNT files, $TOTAL_CHARS chars, **~$TOTAL_TOKENS tokens**"

if [ "$CONTEXT_WINDOW" -gt 0 ]; then
  echo ""
  pct=$((TOTAL_TOKENS * 100 / CONTEXT_WINDOW))
  remaining=$((CONTEXT_WINDOW - TOTAL_TOKENS))
  echo "**Context window**: $CONTEXT_WINDOW tokens"
  echo "**Usage**: ${pct}% ($TOTAL_TOKENS / $CONTEXT_WINDOW)"
  echo "**Remaining**: ~$remaining tokens"
  echo ""
  if [ "$pct" -ge 85 ]; then
    echo "**WARNING: Context pressure HIGH (${pct}%).** Compaction recommended."
  elif [ "$pct" -ge 70 ]; then
    echo "**NOTE: Context usage moderate (${pct}%).** Monitor for growth."
  else
    echo "Context usage within safe limits (${pct}%)."
  fi
fi
