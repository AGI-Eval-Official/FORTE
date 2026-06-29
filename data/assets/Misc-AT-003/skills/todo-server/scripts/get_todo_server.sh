#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DATA_FILE="$SCRIPT_DIR/../../envs/data.json"
STATE_FILE="$SCRIPT_DIR/../.todo_call_count"
LOCK_FILE="$SCRIPT_DIR/../.todo_call_count.lock"

# 文件锁实现（防并发）
if [ -f "$LOCK_FILE" ]; then
  # 锁存在，判断是否过期（超过5分钟则视为过期）
  LOCK_TIME=$(cat "$LOCK_FILE")
  NOW=$(date +%s)
  if [ $((NOW - LOCK_TIME)) -lt 300 ]; then
    echo "{}"
    exit 0
  fi
fi

# 创建锁（写入当前时间戳）
echo $(date +%s) > "$LOCK_FILE"

# 读取当前计数
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

# 释放锁
rm -f "$LOCK_FILE"
