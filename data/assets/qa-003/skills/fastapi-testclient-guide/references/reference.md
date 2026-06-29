# 参考文档：订单管理 API

## 项目概述

`order-api` 是一个电商订单管理的 REST API 服务，提供订单的增删改查和状态管理功能。

## 技术栈

- Python 3.11
- FastAPI
- Pydantic（请求/响应模型校验）
- 内存数据库（dict 存储，无持久化）
- pytest + FastAPI TestClient

## API 接口

| 方法 | 路径 | 说明 | 成功状态码 |
|------|------|------|-----------|
| GET | `/orders` | 查询订单列表，支持 `?status=` 筛选 | 200 |
| GET | `/orders/{order_id}` | 查询单个订单 | 200 |
| POST | `/orders` | 创建订单 | 201 |
| PUT | `/orders/{order_id}/status` | 更新订单状态 | 200 |
| DELETE | `/orders/{order_id}` | 取消订单 | 200 |

## 请求/响应模型

### 创建订单 `POST /orders`

请求体：
```json
{
  "customer_name": "Alice",
  "items": [
    {"product_name": "Widget", "quantity": 2, "unit_price": 9.99}
  ]
}
```

响应体：
```json
{
  "order_id": "a1b2c3d4",
  "customer_name": "Alice",
  "status": "PENDING",
  "items": [
    {"product_name": "Widget", "quantity": 2, "unit_price": 9.99, "subtotal": 19.98}
  ],
  "total_amount": 19.98,
  "created_at": "2025-01-01T12:00:00"
}
```

### 更新状态 `PUT /orders/{order_id}/status`

请求体：
```json
{"status": "CONFIRMED"}
```

### 取消订单 `DELETE /orders/{order_id}`

响应体：
```json
{"message": "Order cancelled", "order_id": "a1b2c3d4"}
```

## 订单状态流转

```
PENDING → CONFIRMED → SHIPPED → DELIVERED
   ↓          ↓
CANCELLED  CANCELLED
```

| 当前状态 | 允许流转到 |
|---------|-----------|
| PENDING | CONFIRMED, CANCELLED |
| CONFIRMED | SHIPPED, CANCELLED |
| SHIPPED | DELIVERED |
| DELIVERED | （终态） |
| CANCELLED | （终态） |

## 错误场景

| 场景 | 状态码 | 说明 |
|------|--------|------|
| 订单不存在 | 404 | GET/PUT/DELETE 一个不存在的 order_id |
| 请求体无效 | 400 | 创建订单时 customer_name 为空或 items 为空 |
| 请求体字段类型错误 | 422 | Pydantic 校验失败（如 quantity 传了字符串） |
| 非法状态流转 | 409 | 如尝试将 SHIPPED 订单设为 CONFIRMED |
| 取消非 PENDING 订单 | 409 | DELETE 一个状态不是 PENDING 的订单 |

## 注意事项

- 运行测试：`pytest` 或 `python -m pytest`
