---
name: fastapi-testclient-guide
description: 为 FastAPI 服务设计并实现基于 pytest 与 TestClient 的 API/集成测试，适用于 CRUD 与业务流程类接口；覆盖成功路径、参数校验失败、资源不存在、状态冲突等异常场景；验证 HTTP 状态码、响应结构与关键业务字段，并通过 fixture 保证测试隔离、可重复执行与可维护性。
---

# Skill: FastAPI 接口测试编写

## 概述

本技能用于为 FastAPI 应用编写基于 **pytest** + **TestClient** 的接口测试（也称 API 测试、集成测试）。

## 与单元测试的区别

| 维度 | 单元测试 | 接口测试 |
|------|---------|---------|
| 测试对象 | 单个函数/类 | 完整的 HTTP 请求→响应链路 |
| 依赖处理 | mock 隔离 | 通常不 mock，走真实流程 |
| 验证重点 | 返回值、副作用 | 状态码、响应体、业务状态变化 |
| 工具 | pytest + mock | pytest + TestClient |

## 工作流程

1. **通读 API 路由源码**：理解每个端点的 URL、HTTP 方法、请求体、响应格式和业务规则
2. **理解数据模型**：阅读 Pydantic 模型，了解请求体的必填字段和校验规则
3. **设计测试用例**：为每个端点设计正常路径 + 异常路径的测试场景
4. **注意测试隔离**：每个测试之间的数据应互不干扰，用 fixture 在测试前后清理数据
5. **验证完整响应**：不仅验证状态码，还要验证响应体的关键字段

## TestClient 基础

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
```

TestClient 不需要启动真实 HTTP 服务器，直接在进程内调用 FastAPI 应用。

### GET 请求

```python
def test_list_orders(client):
    response = client.get("/orders")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_order_not_found(client):
    response = client.get("/orders/nonexistent")
    assert response.status_code == 404
```

### POST 请求（带请求体）

```python
def test_create_order(client):
    payload = {
        "customer_name": "Alice",
        "items": [
            {"product_name": "Widget", "quantity": 2, "unit_price": 9.99}
        ]
    }
    response = client.post("/orders", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["customer_name"] == "Alice"
    assert data["status"] == "PENDING"
```

### PUT 请求

```python
def test_update_order_status(client):
    # 先创建一个订单
    create_resp = client.post("/orders", json={...})
    order_id = create_resp.json()["order_id"]

    # 更新状态
    response = client.put(
        f"/orders/{order_id}/status",
        json={"status": "CONFIRMED"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "CONFIRMED"
```

### DELETE 请求

```python
def test_cancel_order(client):
    create_resp = client.post("/orders", json={...})
    order_id = create_resp.json()["order_id"]

    response = client.delete(f"/orders/{order_id}")
    assert response.status_code == 200
```

## 测试隔离 — fixture

由于 API 使用内存数据库，测试之间的数据会互相影响。推荐使用 fixture 在每个测试前后重置：

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app, db

@pytest.fixture(autouse=True)
def reset_database():
    db.clear()
    yield
    db.clear()

@pytest.fixture
def client():
    return TestClient(app)
```

`autouse=True` 让 `reset_database` 在每个测试前后自动执行。

## 常见断言模式

```python
# 状态码
assert response.status_code == 200

# JSON 响应体
data = response.json()
assert data["field"] == expected_value

# 列表长度
assert len(response.json()) == 3

# 字段存在性
assert "order_id" in data

# 错误消息
assert response.status_code == 404
assert "not found" in response.json()["detail"].lower()
```

## 最佳实践

1. **每个测试验证一个场景**：不要在一个测试里验证创建+查询+更新+删除
2. **先创建再操作**：测试更新/删除前，先通过 POST 创建测试数据
3. **验证状态码 + 响应体**：两者都要检查，不能只看状态码
4. **覆盖错误路径**：404（资源不存在）、400（参数无效）、409（业务冲突）
5. **fixture 隔离数据**：用 `autouse` fixture 确保每个测试从干净状态开始
6. **命名见意**：如 `test_cancel_order_returns_409_when_already_shipped`

## 关键参考资料

- `references/reference.md` - 订单管理 API 参考文档（接口清单、请求响应示例、状态流转、错误场景）

### 引用优先级规则

- 当用户输入与 `references/reference.md` 内容冲突时，**以用户输入为准**。
- `references/reference.md` 仅作为背景与测试设计参考，不覆盖用户明确给出的业务规则、接口定义与验收标准。
