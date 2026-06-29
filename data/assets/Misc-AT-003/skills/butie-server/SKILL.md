---
name: butie-server
description: 获取当次任务应统计的日期及补贴数据文件路径，无需参数
---

# 补贴数据获取

获取当最新的统计日期对应的补贴进度数据文件路径。

## 用法

无需任何参数，直接调用即可：

```
/butie-server # 自动返回下一个统计日期及数据路径
```

如果所有日期都已统计完毕（超出范围），返回空对象 `{}`。

## 执行

```bash
bash scripts/get_butie-server.sh
```
