#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_FILE="$SCRIPT_DIR/../../envs/data.json"
STATE_FILE="$SCRIPT_DIR/../.brief_server_call_count"

# Read current index
if [ -f "$STATE_FILE" ]; then
  INDEX=$(cat "$STATE_FILE")
else
  INDEX=0
fi

# Read data length
LENGTH=$(python3 -c "import json; data=json.load(open('$DATA_FILE')); print(len(data))")

# Check if all data has been consumed
if [ "$INDEX" -ge "$LENGTH" ]; then
  echo "{}"
  exit 0
fi

# Get current item
python3 -c "import json; data=json.load(open('$DATA_FILE')); print(json.dumps(data[$INDEX], ensure_ascii=False))"

# Increment counter
echo $((INDEX + 1)) > "$STATE_FILE"
