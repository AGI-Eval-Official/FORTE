---
name: pytest-unit-testing
description: 为 Python 业务模块编写 pytest 单元测试的技能。当用户提出“给 Python 项目补/写单元测试”“用 pytest 覆盖主流程与异常路径”“使用 fixture、parametrize、pytest.raises”“对外部依赖进行 mock 隔离”“在 tests 目录产出可运行测试集”等需求时触发。即使用户不提技能名，只要意图是提升 Python 服务的测试覆盖与可靠性，也应触发。
---

# Skill: pytest 单元测试编写

## 概述

本技能用于为 Python 应用编写基于 **pytest** 的单元测试，结合 `unittest.mock` 进行依赖隔离，重点覆盖订单总价计算、客户等级折扣与优惠券校验等典型业务场景。

## Reference 路由

- 默认先读取 `references/reference.md` 作为领域规则与数据模型基线。
- 当任务涉及业务规则、依赖接口、异常类型、折扣参数或测试输入设计时，必须以 `references/reference.md` 为准。
- 若用户需求与参考文档冲突，优先按用户明确要求执行，并在测试中通过注释或命名体现差异。

## 工作流程

编写测试的推荐步骤：

1. **先读 reference 再读源码**：先读取 `references/reference.md`，再完整阅读被测类及其依赖接口和数据模型，理清分支路径和调用关系后再动手写测试
2. **识别需要 mock 的依赖**：被测类 `__init__` 中注入的所有外部依赖都需要用 `MagicMock` 或 `mock.patch` 模拟
3. **设计 `@pytest.fixture` 共享夹具**：把多个测试共用的 mock 对象、被测实例和测试数据放在 fixture 中，通过参数注入复用
4. **按分支逐个编写 `def test_` 函数**：每个测试函数覆盖一条业务分支，遵循 Arrange → Act → Assert 三段式
5. **用 `@pytest.mark.parametrize` 减少重复**：对于同一逻辑、不同输入的场景，用参数化测试覆盖多组数据

## pytest 基础

### fixture — 测试夹具

```python
@pytest.fixture
def mock_repo():
    repo = MagicMock()
    repo.find_by_id.return_value = Product("P001", "Widget", 100.0)
    return repo

@pytest.fixture
def service(mock_repo, mock_gateway):
    return MyService(mock_repo, mock_gateway)

def test_normal_case(service, mock_repo):
    result = service.do_something("P001")
    assert result.value == 100.0
    mock_repo.find_by_id.assert_called_once_with("P001")
```

fixture 函数名出现在测试函数的参数中，pytest 会自动注入。

### parametrize — 参数化测试

```python
@pytest.mark.parametrize("tier, expected_rate", [
    ("GOLD", 0.15),
    ("SILVER", 0.10),
    ("BRONZE", 0.05),
    ("STANDARD", 0.0),
])
def test_tier_discount(service, tier, expected_rate):
    customer = Customer("C001", "Alice", tier)
    # ... assert discount rate matches expected_rate
```

一个测试函数覆盖多组输入，避免写 N 个几乎相同的测试。

### pytest.raises — 异常验证

```python
def test_invalid_input_raises_error(service):
    with pytest.raises(ValueError, match="must not be None"):
        service.process(None)

def test_expired_coupon_raises_error(service):
    with pytest.raises(CouponExpiredError):
        service.apply_coupon("ORD-001", "EXPIRED_CODE", 100.0)
```

## unittest.mock 基础

### MagicMock — 模拟对象

```python
from unittest.mock import MagicMock

mock_repo = MagicMock()
mock_repo.find_by_id.return_value = Product("P001", "Widget", 100.0)
mock_repo.find_by_id.side_effect = KeyError("not found")
```

### mock.patch — 装饰器/上下文管理器

```python
from unittest.mock import patch

@patch("pricing_service.service.TaxGateway")
def test_with_patch(MockTaxGateway):
    MockTaxGateway.return_value.calculate_tax.return_value = 8.0
    # ...
```

### 调用断言

```python
mock.assert_called_once_with("expected_arg")
mock.assert_called_with("last_call_arg")
mock.assert_not_called()
assert mock.call_count == 3
```

## 最佳实践

1. **一个测试验证一个行为**：每个 `def test_` 函数聚焦一条分支逻辑
2. **Arrange → Act → Assert**：三段式结构清晰可读
3. **命名见意**：如 `test_calculate_order_total_gold_tier_applies_15_percent_discount`
4. **fixture 复用**：共享的 mock 对象和被测实例放在 fixture 中
5. **parametrize 覆盖数据变体**：同一逻辑的多组输入用参数化而非复制粘贴
6. **覆盖边界场景**：None 输入、空列表、零值、异常路径
7. **验证 mock 调用**：用 `assert_called_once_with` 确认依赖被正确调用
8. **优先用 `pytest.raises` 而非 try/except**：更简洁、更 Pythonic
