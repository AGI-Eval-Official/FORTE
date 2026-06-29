# 参考文档：电商订单定价服务

## 项目概述

`order-pricing-service` 是一个电商订单定价服务，负责根据商品价格、客户等级和优惠券计算订单最终价格。

## 技术栈

- Python 3.11
- pytest 测试框架
- unittest.mock 用于依赖隔离
- dataclass 用于数据模型

## 核心类

| 类名 | 位置 | 职责 |
|------|------|------|
| `OrderPricingService` | `pricing_service/service.py` | 应用服务，编排订单定价和优惠券验证流程 |
| `Order` | `pricing_service/models.py` | 数据类，包含 order_id、customer_id、items |
| `OrderItem` | `pricing_service/models.py` | 数据类，包含 product_id、quantity |
| `Product` | `pricing_service/models.py` | 数据类，包含 product_id、name、unit_price |
| `Customer` | `pricing_service/models.py` | 数据类，包含 customer_id、name、tier |
| `Coupon` | `pricing_service/models.py` | 数据类，包含 code、discount_rate、min_order_amount、expiry_date、usage_limit、usage_count |
| `PricingResult` | `pricing_service/models.py` | 数据类，订单定价结果（subtotal、discount_rate、discount_amount、tax_amount、final_total、unavailable_items） |
| `CouponResult` | `pricing_service/models.py` | 数据类，优惠券应用结果 |

## 业务术语

| 术语 | 含义 |
|------|------|
| 客户等级折扣 | GOLD=15%, SILVER=10%, BRONZE=5%, STANDARD=0%，由 `TIER_DISCOUNT_RATES` 字典定义 |
| 折扣上限 | 最大折扣率 `MAX_DISCOUNT_RATE = 0.50`（50%），等级折扣和优惠券折扣均受此限制 |
| 优惠券验证 | 按顺序校验：是否存在 → 是否过期 → 是否超出使用次数 → 订单金额是否达到最低门槛 |
| 不可用商品 | 在 ProductRepository 中找不到的商品，计入 `unavailable_items` 但不中断计算 |

## 依赖接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `ProductRepository` | `find_by_id(product_id)` | 按 ID 查找商品，未找到返回 None |
| `CouponRepository` | `find_by_code(code)` | 按编码查找优惠券，未找到返回 None |
| `CouponRepository` | `save(coupon)` | 保存优惠券（更新使用次数） |
| `CustomerGateway` | `get_customer(customer_id)` | 查找客户信息，未找到返回 None |
| `TaxGateway` | `calculate_tax(amount)` | 根据金额计算税额 |

## 自定义异常

| 异常类 | 触发场景 |
|--------|----------|
| `InvalidCouponError` | 优惠券编码不存在 |
| `CouponExpiredError` | 优惠券已过期 |
| `CouponExhaustedError` | 优惠券使用次数已达上限 |
| `CouponNotApplicableError` | 订单金额低于优惠券最低门槛 |
| `CustomerNotFoundError` | 客户 ID 不存在 |

## 注意事项

- 运行测试：`pytest` 或 `python -m pytest`
