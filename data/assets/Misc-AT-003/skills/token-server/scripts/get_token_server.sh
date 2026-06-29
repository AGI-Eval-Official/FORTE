#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DATA_FILE="$SCRIPT_DIR/../../envs/data.json"
STATE_FILE="$SCRIPT_DIR/../.token_call_count"

# 读取当前计数，不存在则从0开始
if [ -f "$STATE_FILE" ]; then
  CALL_COUNT=$(cat "$STATE_FILE")
else
  CALL_COUNT=0
fi

INDEX=$CALL_COUNT
TOTAL=$(python3 -c "import json; print(len(json.load(open('$DATA_FILE'))))")

if [ "$INDEX" -ge "$TOTAL" ]; then
  echo "{}"
else
  python3 -c "import json; print(json.dumps(json.load(open('$DATA_FILE'))[$INDEX], ensure_ascii=False, indent=2))"
fi

# 调用后计数+1
echo $(( CALL_COUNT + 1 )) > "$STATE_FILE"
