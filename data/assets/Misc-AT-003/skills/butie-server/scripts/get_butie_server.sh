#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_FILE="$SCRIPT_DIR/../../envs/data.json"
STATE_FILE="$SCRIPT_DIR/../.butie_server_call_count"

# 初始化计数器
if [ ! -f "$STATE_FILE" ]; then
    echo "0" > "$STATE_FILE"
fi

INDEX=$(cat "$STATE_FILE")

# 获取data.json中的数据条数
TOTAL=$(python3 -c "import json; print(len(json.load(open('$DATA_FILE', encoding='utf-8'))))" 2>/dev/null)

if [ -z "$TOTAL" ]; then
    echo "{}"
    exit 0
fi

if [ "$INDEX" -ge "$TOTAL" ]; then
    echo "{}"
    exit 0
fi

# 获取对应索引的数据
RESULT=$(python3 -c "
import json
data = json.load(open('$DATA_FILE', encoding='utf-8'))
index = int('$INDEX')
if index < len(data):
    print(json.dumps(data[index], ensure_ascii=False))
else:
    print('{}')
")

# 计数器+1
echo $((INDEX + 1)) > "$STATE_FILE"

echo "$RESULT"
