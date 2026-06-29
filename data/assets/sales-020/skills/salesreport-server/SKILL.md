---
name: salesreport-server
description: 获取当次应处理的销售数据文件路径和批次日期，无需参数
---

# 歪马配送销售数据获取

获取销售数据文件中下一个待处理批次的日期及文件路径

## 用法

无需任何参数，直接调用即可：

```
/salesreport-server    # 自动返回下一个批次的日期及销售数据文件路径
```

如果所有批次已处理完毕（超出范围），返回空对象 `{}`。

## 执行

```bash
bash scripts/get_salesreport-server_path.sh
```
