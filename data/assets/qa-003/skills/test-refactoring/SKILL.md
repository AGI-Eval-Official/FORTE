---
name: test-refactoring
description: 将已有但质量较差的 pytest 测试重构为专业、可维护的测试代码，包含参数化改造、fixture 提取、异常断言规范化（pytest.raises）与按模块拆分测试文件，并确保测试语义与覆盖场景不缩水。用户只要提到“pytest 测试重构”“测试重复代码太多”“提取 fixture”“参数化测试”“测试文件太乱需要拆分”等需求，都应优先使用本技能。
---

# Skill: Pytest 测试重构 — 参数化改造与 Fixture 提取

## 概述

本技能用于将已有但质量较差的 pytest 测试代码重构为专业、可维护的测试代码，主要包括参数化改造、fixture 提取、异常测试规范化等。

## Reference 路由

- 默认按用户当前仓库和测试代码开展重构，不假设固定项目结构。
- 当需要了解示例项目背景、模块命名或最小可运行测试命令时，读取 `references/reference.md`。
- `references/reference.md` 仅作为示例上下文（如 `payment-utils`、`pytest tests/`）；如果用户提供的内容与 reference 有冲突，必须以用户提供内容为准，不得被 reference 覆盖。
- 若用户未提供足够上下文，可先参考 `references/reference.md` 给出初始重构方案，再在读取真实代码后立即按真实项目修正。

## 工作流程

### Phase 1：评估现状

1. **通读现有测试**：了解所有测试用例覆盖了哪些场景
2. **识别代码坏味道**：
   - 重复的测试数据构造（同一个字典出现多次）
   - 多个测试仅输入值不同、结构完全一样（应参数化）
   - 手动 try/except 做异常断言（应用 pytest.raises）
   - 所有测试堆在一个文件里
3. **通读被测源码**：理解各函数的签名和行为，确保重构不改变测试语义

### Phase 2：参数化改造

将多个仅输入值不同的测试函数合并为一个参数化测试：

```python
# 改造前：4 个重复函数
def test_discount_10():
    assert apply_discount(100, 10) == 90.0
def test_discount_50():
    assert apply_discount(100, 50) == 50.0

# 改造后：1 个参数化函数
@pytest.mark.parametrize("price,discount,expected", [
    (100.0, 10, 90.0),
    (100.0, 50, 50.0),
    (100.0, 0, 100.0),
    (100.0, 100, 0.0),
])
def test_apply_discount(price, discount, expected):
    assert apply_discount(price, discount) == expected
```

### Phase 3：Fixture 提取

将重复构造的测试数据提取为 conftest.py 中的 fixture：

```python
# conftest.py
import pytest

@pytest.fixture
def valid_coupon():
    return {
        'code': 'SAVE10',
        'discount': 10,
        'expiry_date': '2099-12-31',
        'min_purchase': 50
    }

@pytest.fixture
def expired_coupon():
    return {
        'code': 'OLD10',
        'discount': 10,
        'expiry_date': '2020-01-01',
        'min_purchase': 50
    }
```

### Phase 4：异常测试规范化

将手动 try/except 替换为 `pytest.raises`：

```python
# 改造前
def test_discount_invalid():
    try:
        apply_discount(100, -10)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

# 改造后
def test_discount_invalid():
    with pytest.raises(ValueError):
        apply_discount(100, -10)
```

### Phase 5：文件拆分

按被测模块拆分测试文件，每个模块对应一个测试文件，以下为拆分示例：
- `test_price_calculator.py` — 价格计算相关测试
- `test_coupon_validator.py` — 优惠券校验相关测试
- `conftest.py` — 共享 fixture

### Phase 6：验证

运行全部测试，确保重构后所有测试仍然通过且覆盖面不缩水。

## 重构原则

1. **语义不变**：重构只改形式不改含义，每个原始测试场景都必须保留
2. **覆盖面不缩水**：参数化会减少函数数量但不减少测试场景数
3. **逐步推进**：每完成一个重构步骤就运行一次测试
4. **最小依赖**：fixture 只提取真正被多处使用的数据

## 识别参数化候选

满足以下条件的测试组适合参数化：
- 3 个以上测试函数结构相同，仅输入值和期望值不同
- 测试的是同一个函数的不同输入组合
- 每组输入可以用元组表示

## 注意事项

- `@pytest.mark.parametrize` 的参数名必须与测试函数的形参对应
- fixture 通过函数参数名自动注入，不需要显式导入
- `pytest.raises` 可作为上下文管理器使用，更简洁
- 拆分文件后注意 import 路径的正确性
