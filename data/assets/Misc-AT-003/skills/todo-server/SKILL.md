---
name: todo-server
description: 获取当次应处理的消息记录文件路径和批次日期，无需参数
---

# Todo 消息记录获取

获取消息记录文件夹中下一个待处理批次的日期及文件路径

## 用法

无需任何参数，直接调用即可：

```
/todo-server    # 自动返回下一个批次的日期及消息记录文件路径
```

如果所有批次已处理完毕（超出范围），返回空对象 `{}`。

## 执行

```bash
bash scripts/get_todo-server.sh
```
