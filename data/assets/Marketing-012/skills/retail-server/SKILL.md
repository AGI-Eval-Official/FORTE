---
name: retail-server
description: 获取零售行业情报每日更新任务当次应处理的情报文件路径，无需参数
---

# 零售行业情报获取

获取零售行业情报每日更新任务当次应处理的情报文件路径和说明。

## 用法

无需任何参数，直接调用即可：

```
/retail-server    # 自动返回下一条零售行业情报
```

如果所有情报已读完（超出范围），返回空对象 `{}`。

## 执行

```bash
bash scripts/get_retail-server_path.sh
```
