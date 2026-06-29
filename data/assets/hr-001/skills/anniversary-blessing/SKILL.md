---
name: anniversary-blessing
description: 根据 birthday_state.json 中的状态、署名人与员工名单，生成生日祝福发送结果。当 status 为 confirmed 时，按员工性别套用固定模板生成祝福消息，并给出状态更新结果；当 status 不为 confirmed 时，跳过发送。
---

# anniversary-blessing

## 输入要求

输入文件需提供以下字段：

- `status`：当前处理状态
- `sender_name`：署名人
- `employees`：员工列表
- `employees[].name`：员工姓名
- `employees[].gender`：员工性别，取值为 `male`、`female` 或 `unknown`
- `employees[].im_id`：大象私聊 ID

## 处理规则

1. 仅当 `status` 为 `confirmed` 时，才生成生日祝福消息；否则跳过发送。
2. 生成的每条消息末尾都必须追加署名 `——sender_name`；若未提供 `sender_name`，默认使用 `——丽芳`。
3. 当题目要求输出 `使用的skill` 字段时，该字段值固定为 `anniversary-blessing`。
4. 输出给用户的结构化字段，以用户题目中的字段要求为准；若与本 skill 的自然语言描述冲突，优先执行用户题目要求。

## 消息模板

- `male`：`{name}，祝你生日快乐！愿你今天被惊喜和好运包围，工作顺顺利利，生活开开心心。——{sender_name}`
- `female`：`{name}，祝你生日快乐！愿你新的一岁明朗又从容，工作顺利，生活处处有小确幸。——{sender_name}`
- `unknown`：`{name}，祝你生日快乐！愿你新的一岁平安顺遂，工作生活都如意。——{sender_name}`

## 输出规则

当题目要求输出发送明细时，每位员工占 1 行，格式固定为：

`姓名（im_id）：祝福内容`

当 `status` 为 `confirmed` 时，状态更新结果应表示为：`birthday_state.json 中的 status 已更新为 sent`。
当 `status` 不为 `confirmed` 时，状态更新结果应表示为：`birthday_state.json 保持原状态不变`。
