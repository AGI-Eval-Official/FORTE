---
name: pitfall-guide-server
description: 获取当次应处理的避坑指南数据上下文，无需参数
---

# 避坑指南上下文获取

获取当日避坑指南任务当次应处理的数据上下文，用于整理当日坑点并输出更新后的避坑指南内容。

## 用法

无需任何参数，直接调用即可：

```
/pitfall-guide-server    # 自动返回下一批避坑指南数据上下文
```

如果所有数据已读完（超出范围），返回空对象 `{}`。

## 执行

```bash
bash scripts/get_pitfall-guide-server_path.sh
```
