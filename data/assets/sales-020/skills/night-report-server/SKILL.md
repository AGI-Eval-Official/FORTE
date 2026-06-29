---
name: night-report-server
description: 大象消息晚报数据获取服务，每次调用返回当次应处理的日期和大象消息记录文件路径
---

# 大象消息晚报数据获取

每次调用此 skill，会返回当次应处理的日期和对应的大象消息记录文件路径。如果返回空对象 `{}`，说明所有数据已处理完毕。

## 用法

无需任何参数，直接调用即可：

```
/night-report-server     # 调用此 skill 获取当次应处理的大象消息记录文件路径和日期
```

如果所有数据已处理完毕，返回空对象 `{}`。

## 执行

```bash
bash scripts/get_night-report-server_path.sh
```
