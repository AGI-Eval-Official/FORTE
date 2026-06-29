---
name: memory-archive-server
description: 获取本周记忆归档任务当次应处理的数据上下文，无需参数
---

# 记忆归档上下文获取

获取本周记忆归档任务当次应处理的数据上下文，用于直接输出更新后的周报内容和 facts 内容。

## 用法

无需任何参数，直接调用即可：

```
/memory_archive_server    # 自动返回下一批记忆归档上下文
```

如果所有数据已读完（超出范围），返回空对象 `{}`。

## 执行

```bash
bash scripts/get_memory_archive_server_path.sh
```
