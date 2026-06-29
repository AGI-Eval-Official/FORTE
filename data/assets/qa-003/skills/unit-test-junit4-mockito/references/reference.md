# 参考文档：电商订单退款单元测试（JUnit 4 + Mockito）

## 业务背景

本项目是一个电商订单交易服务，退款子系统负责处理批量退款请求以及对失败订单的重处理。

## 核心类

| 类名 | 职责 |
|------|------|
| `OrderBatchRefundProcessor` | 应用层处理器，编排批量退款流程 |
| `RefundOrder` | 域实体，持有退款详情（orderId、amount、status、email） |
| `RefundStatusEnum` | 状态枚举：`PENDING`、`PROCESSING`、`REFUNDED`、`REFUND_FAILED` |
| `BatchRefundResult` | 值对象，汇总批处理结果（成功/失败/跳过计数 + 失败订单 ID 列表） |
| `ReprocessingResult` | 值对象，汇总重处理结果（恢复/仍失败/跳过计数 + totalAttempts） |
| `RefundEvent` | 域事件值对象，记录退款过程中的关键事件 |

## 业务术语

| 术语 | 含义 |
|------|------|
| 退款资格校验 | 由 `RefundPolicyService` 判定订单是否符合退款条件 |
| 动态重试 | 退款网关调用的最大重试次数由 `RefundPolicyService.getMaxRetries()` 动态决定，而非硬编码常量 |
| 重处理翻倍 | 对失败订单进行重处理时，重试预算为正常值的 2 倍 |
| 域事件发布 | 退款流程中的关键节点会通过 `RefundEventPublisher` 发布 `RefundEvent` |

## 技术栈

- Java + JUnit 4 + Mockito
- 被测类通过构造函数注入 6 个依赖（均为接口）
- 运行测试：项目根目录执行 `mvn test` 或 IDE 直接运行测试类
