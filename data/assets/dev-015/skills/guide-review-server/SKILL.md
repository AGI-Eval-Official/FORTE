---
name: guide-review-server
description: 获取新手指南每日 review 任务当次应处理的 memory 文件路径，无需参数
---

# 新手指南 review 数据获取

获取新手指南每日 review 任务当次应处理的 memory 文件路径和说明。

## 用法

无需任何参数，直接调用即可：

```
/guide-review-server    # 自动返回下一条待 review 的 memory 文件
```

如果所有 memory 已读完（超出范围），返回空对象 `{}`。

## 执行

```bash
bash scripts/get_guide-review-server_path.sh
```
