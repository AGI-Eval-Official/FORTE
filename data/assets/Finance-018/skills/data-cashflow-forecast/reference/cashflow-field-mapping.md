# cashflow-field-mapping

## 1. 目标

定义资金预测任务中的通用字段语义映射规则，确保不同来源表格可统一进入计算流程。

本文件只包含跨任务稳定规则，不包含任务专属字段或固定文件路径。

## 2. 标准语义字段

### 2.1 余额表（balance）

必需语义字段：

- `balance_amount`（账户余额）

可选语义字段：

- `account_status`（账户状态）
- `account_name`（账户名称）
- `currency`（币种）

### 2.2 付款计划表（payment）

必需语义字段：

- `payment_date`（付款日期）
- `payment_amount`（付款金额）

可选语义字段：

- `payee`（收款方）
- `payment_purpose`（用途）

### 2.3 回款计划表（receipt）

必需语义字段：

- `receipt_date`（回款日期）
- `receipt_amount`（回款金额）

可选语义字段：

- `payer`（付款方）
- `business_type`（业务类型）

## 3. 常见同义字段词典

### 3.1 余额语义

- `balance_amount`: 余额, 可用余额, 账户余额, 当前余额, balance, available_balance
- `account_status`: 状态, 账户状态, 账户标识, acct_status, status
- `account_name`: 账户名称, 户名, 账号名称, account_name
- `currency`: 币种, 货币, currency, ccy

### 3.2 付款语义

- `payment_date`: 日期, 付款日期, 计划付款日, 预计付款日, payment_date, date
- `payment_amount`: 金额, 付款金额, 应付金额, 支出金额, payment_amount, amount
- `payee`: 收款方, 对方户名, 收款单位, payee
- `payment_purpose`: 用途, 支付用途, 摘要, 备注, purpose, memo

### 3.3 回款语义

- `receipt_date`: 日期, 回款日期, 预计到账日, 到账日期, receipt_date, date
- `receipt_amount`: 金额, 回款金额, 收入金额, 到账金额, receipt_amount, amount
- `payer`: 付款方, 回款方, 客户名称, payer
- `business_type`: 业务类型, 收款类型, 科目, biz_type

## 4. 映射优先级

按以下顺序进行字段识别：

1. 任务输入参数显式指定的字段映射（最高优先）
2. 本文件中的同义字段词典
3. 基于列值特征推断（日期格式、金额分布等）

若同一语义命中多个候选列：

- 优先选择列名匹配度更高者
- 若仍冲突，使用数据类型一致性（日期列/数值列）决策
- 无法决策时返回冲突列表并停止自动计算

## 5. 最低校验要求

进入计算前必须满足：

- 余额表存在 `balance_amount`
- 付款表存在 `payment_date` 与 `payment_amount`
- 回款表存在 `receipt_date` 与 `receipt_amount`

否则应返回结构化缺失信息，不进行滚动预测。

## 6. 输出侧字段命名建议

内部计算统一使用语义字段，最终输出再映射为任务要求列名。

推荐输出语义字段：

- `date`
- `opening_balance_wan`
- `receipt_amount_wan`
- `payment_amount_wan`
- `closing_balance_wan`
- `alert_level`（值域以用户要求等级标识为准；未指定时使用默认示例标识）
