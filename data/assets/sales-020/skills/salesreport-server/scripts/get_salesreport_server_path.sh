#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_FILE="$SCRIPT_DIR/../../envs/data.json"
STATE_FILE="$SCRIPT_DIR/../.salesreport_server_call_count"

# 读取当前计数
if [ -f "$STATE_FILE" ]; then
    INDEX=$(cat "$STATE_FILE")
else
    INDEX=0
fi

# 读取 data.json 中的总条数
TOTAL=$(python3 -c "import json; data=json.load(open('$DATA_FILE')); print(len(data))")

# 如果已超出范围，返回空对象
if [ "$INDEX" -ge "$TOTAL" ]; then
    echo "{}"
    exit 0
fi

# 取出当前批次数据
RESULT=$(python3 -c "
import json
data = json.load(open('$DATA_FILE'))
item = data[$INDEX]
print(json.dumps(item, ensure_ascii=False))
")

# 计数器 +1
echo $((INDEX + 1)) > "$STATE_FILE"

echo "$RESULT"
