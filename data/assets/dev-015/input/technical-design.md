# 评测平台技术方案设计

**项目**：评测平台  
**文档版本**：v1.0  
**日期**：2026-05-08  
**作者**：研发工程师

---

## 一、需求概述

本次需求为从零构建一个 AI 模型评测平台，核心能力包括：模型管理、评测集管理、评测实验三大模块。平台需支持将模型与评测集组合执行评测实验，并提供统计分析和结果导出能力。

关键约束：
- 数据库使用内嵌型数据库（SQLite），无需外部数据库服务
- API Key 加密存储，接口返回时脱敏
- 评测执行引擎需支持最大 10000 条数据、最大 20 并发、最大 300 秒超时
- 软删除机制，数据可恢复

---

## 二、技术栈选型

### 2.1 选型结论

| 层次 | 技术选型 | 版本 |
|------|---------|------|
| 后端框架 | Python + FastAPI | Python 3.11 / FastAPI 0.110+ |
| ORM | SQLAlchemy | 2.0+ |
| 数据库 | SQLite（内嵌） | 3.x |
| 异步任务 | Python asyncio + asyncio.Semaphore | 标准库 |
| HTTP 客户端 | httpx（异步） | 0.27+ |
| 加密 | cryptography（AES-256-GCM） | 42+ |
| 数据校验 | Pydantic v2 | 2.x |
| 前端框架 | React + TypeScript | React 18 / TS 5 |
| 前端 UI 组件库 | Ant Design | 5.x |
| 前端构建工具 | Vite | 5.x |
| 前端 HTTP 客户端 | Axios | 1.x |

### 2.2 选型理由

**FastAPI**：原生支持 async/await，与异步评测执行引擎天然契合；自动生成 OpenAPI 文档；Pydantic 集成使请求/响应校验简洁；社区活跃，性能优秀。

**SQLite + SQLAlchemy**：满足"内嵌型数据库"约束，无需额外部署；SQLAlchemy 2.0 的异步支持（aiosqlite）可与 FastAPI 无缝集成；SQLite 在 10000 条数据规模下性能完全满足需求。

**asyncio 原生并发控制**：评测执行引擎的并发需求（最大 20）规模较小，使用 `asyncio.Semaphore` + `asyncio.gather` 即可实现可靠的并发限制，无需引入 Celery 等重量级任务队列。评测任务在后台协程中运行，通过任务取消机制（`asyncio.Task.cancel()`）支持取消操作。

**httpx**：原生异步 HTTP 客户端，支持超时配置，与 asyncio 生态完美契合，替代 requests 的异步方案。

**AES-256-GCM**：对称加密，性能好，GCM 模式提供认证加密（防篡改），适合 API Key 这类短文本的加密存储。密钥通过环境变量注入，不硬编码在代码中。

**React + Ant Design**：Ant Design 提供开箱即用的 Table、Form、Modal 等组件，与评测平台的列表/表单/弹窗交互高度匹配，可大幅减少前端开发工作量。

---

## 三、系统整体架构

### 3.1 分层结构

```
┌─────────────────────────────────────────────────────────┐
│                      前端层（React）                      │
│   模型管理页 │ 评测集管理页 │ 评测实验页 │ 实验详情页      │
└─────────────────────────┬───────────────────────────────┘
                          │ HTTP/REST (JSON)
┌─────────────────────────▼───────────────────────────────┐
│                    API 层（FastAPI）                      │
│   Router: /api/v1/models                                 │
│   Router: /api/v1/datasets                               │
│   Router: /api/v1/experiments                            │
└──────────┬──────────────┬──────────────┬────────────────┘
           │              │              │
┌──────────▼──┐  ┌────────▼──┐  ┌───────▼──────────────┐
│  模型服务层  │  │ 评测集服务 │  │    评测实验服务层      │
│ ModelService│  │ DatasetSvc │  │  ExperimentService   │
└──────────┬──┘  └────────┬──┘  └───────┬──────────────┘
           │              │              │
           │              │    ┌─────────▼──────────────┐
           │              │    │    评测执行引擎          │
           │              │    │  EvaluationEngine      │
           │              │    │  (asyncio + Semaphore) │
           │              │    └─────────┬──────────────┘
           │              │              │ httpx 异步调用
           │              │              ▼
           │              │         外部模型端点
           │              │
┌──────────▼──────────────▼──────────────────────────────┐
│                   数据访问层（SQLAlchemy）                │
│   ModelRepo │ DatasetRepo │ ExperimentRepo │ ResultRepo │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│                   SQLite（内嵌数据库）                    │
└─────────────────────────────────────────────────────────┘
```

### 3.2 模块划分

**后端模块结构：**

```
app/
├── main.py                  # FastAPI 应用入口
├── config.py                # 配置管理（环境变量、加密密钥等）
├── database.py              # 数据库连接、Session 管理
├── models/                  # SQLAlchemy ORM 模型
│   ├── model.py             # 模型表
│   ├── dataset.py           # 评测集表
│   ├── dataset_item.py      # 评测集数据条目表
│   ├── experiment.py        # 评测实验表
│   ├── experiment_result.py # 逐条评测结果表
│   └── audit_log.py         # 操作日志表
├── schemas/                 # Pydantic 请求/响应 Schema
│   ├── model.py
│   ├── dataset.py
│   └── experiment.py
├── routers/                 # API 路由层
│   ├── models.py
│   ├── datasets.py
│   └── experiments.py
├── services/                # 业务逻辑层
│   ├── model_service.py
│   ├── dataset_service.py
│   └── experiment_service.py
├── engine/                  # 评测执行引擎
│   └── evaluation_engine.py
└── utils/
    ├── crypto.py            # AES-256-GCM 加解密工具
    ├── pagination.py        # 分页工具
    └── audit.py             # 操作日志工具
```

---

## 四、核心模块详细设计

### 4.1 评测执行引擎

#### 4.1.1 整体流程

```
发起评测实验
     │
     ▼
ExperimentService.start_experiment()
     │ 更新实验状态为 RUNNING
     │ 创建后台 asyncio.Task
     ▼
EvaluationEngine.run(experiment_id)
     │
     ├─ 从数据库加载评测集所有条目（分批加载，每批 500 条）
     │
     ├─ 创建 asyncio.Semaphore(concurrency)  ← 并发控制
     │
     ├─ 为每条数据创建协程 _evaluate_single_item()
     │
     ├─ asyncio.gather(*tasks, return_exceptions=True)
     │
     └─ 所有任务完成后，更新实验状态为 COMPLETED
          （若任务被取消，状态更新为 CANCELLED）
```

#### 4.1.2 并发控制

使用 `asyncio.Semaphore` 实现并发限制，确保同时执行的请求数不超过用户配置的并发数（1-20）：

```python
async def run(self, experiment: Experiment):
    semaphore = asyncio.Semaphore(experiment.concurrency)
    
    async def _evaluate_with_semaphore(item: DatasetItem):
        async with semaphore:
            return await self._evaluate_single_item(experiment, item)
    
    tasks = [
        asyncio.create_task(_evaluate_with_semaphore(item))
        for item in dataset_items
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
```

**设计要点：**
- `asyncio.Semaphore` 是协程安全的，无需额外加锁
- `return_exceptions=True` 确保单条失败不会中断整体 gather
- 每批 500 条分批加载，避免一次性将 10000 条数据全部加载到内存

#### 4.1.3 超时处理

每条请求使用 `httpx.AsyncClient` 的 `timeout` 参数控制超时，超时后抛出 `httpx.TimeoutException`，由异常处理逻辑捕获并标记该条为失败：

```python
async def _evaluate_single_item(
    self, experiment: Experiment, item: DatasetItem
) -> ExperimentResult:
    start_time = time.monotonic()
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(experiment.timeout_seconds)
        ) as client:
            response = await client.post(
                experiment.model.endpoint_url,
                json={"input": item.input_text},
                headers={"Authorization": f"Bearer {decrypted_api_key}"},
            )
            response.raise_for_status()
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            return ExperimentResult(
                status=ResultStatus.SUCCESS,
                actual_output=response.json().get("output", ""),
                response_time_ms=elapsed_ms,
            )
    except httpx.TimeoutException:
        return ExperimentResult(
            status=ResultStatus.FAILED,
            error_message="请求超时",
        )
    except Exception as e:
        return ExperimentResult(
            status=ResultStatus.FAILED,
            error_message=str(e),
        )
```

**设计要点：**
- 使用 `time.monotonic()` 计算响应时间，避免系统时钟跳变影响
- `httpx.AsyncClient` 在 `async with` 块内创建，确保连接在超时或异常后正确释放，不出现连接泄漏
- 超时异常和其他异常分别捕获，便于区分错误类型

#### 4.1.4 失败重试策略

根据 PRD 和 PM 回复，本期**不实现自动重试**。原因：
1. PRD 明确"如模型端点不可达或返回错误，该条标记为'失败'并记录错误信息，继续执行下一条"，未提及重试
2. 自动重试可能导致对模型端点的额外压力，且在超时场景下会显著延长总执行时间
3. 用户可通过重新发起实验（选择相同模型和评测集）来处理失败情况

若后续需要引入重试，可在 `_evaluate_single_item` 中集成 `tenacity` 库，配置指数退避策略，仅对网络错误（非 4xx 业务错误）重试。

#### 4.1.5 任务取消机制

每个评测实验对应一个 `asyncio.Task`，存储在内存字典 `_running_tasks: Dict[int, asyncio.Task]` 中。取消时调用 `task.cancel()`，协程内部通过捕获 `asyncio.CancelledError` 来更新实验状态：

```python
# 全局任务注册表（进程内）
_running_tasks: Dict[int, asyncio.Task] = {}

async def run(self, experiment_id: int):
    try:
        # ... 执行评测 ...
        await self._update_status(experiment_id, ExperimentStatus.COMPLETED)
    except asyncio.CancelledError:
        # 保留已执行的结果，仅更新状态
        await self._update_status(experiment_id, ExperimentStatus.CANCELLED)
        raise  # 必须重新抛出，让 asyncio 正确处理取消

def cancel_experiment(self, experiment_id: int) -> bool:
    task = _running_tasks.get(experiment_id)
    if task and not task.done():
        task.cancel()
        return True
    return False
```

**注意**：`_running_tasks` 是进程内内存状态，若进程重启则丢失。由于使用单进程部署（内嵌 SQLite 不支持多进程写入），此方案可行。进程重启后，数据库中状态为 `RUNNING` 的实验将在启动时被检测并标记为 `FAILED`（启动恢复逻辑）。

### 4.2 API Key 加密存储

采用 AES-256-GCM 对称加密：

```python
# utils/crypto.py
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os, base64

class ApiKeyCrypto:
    def __init__(self, secret_key: bytes):
        # secret_key 为 32 字节，从环境变量 ENCRYPTION_KEY 读取（base64 编码）
        self.aesgcm = AESGCM(secret_key)
    
    def encrypt(self, plaintext: str) -> str:
        nonce = os.urandom(12)  # GCM 推荐 96-bit nonce
        ciphertext = self.aesgcm.encrypt(nonce, plaintext.encode(), None)
        # 存储格式：base64(nonce + ciphertext)
        return base64.b64encode(nonce + ciphertext).decode()
    
    def decrypt(self, encrypted: str) -> str:
        data = base64.b64decode(encrypted)
        nonce, ciphertext = data[:12], data[12:]
        return self.aesgcm.decrypt(nonce, ciphertext, None).decode()
    
    @staticmethod
    def mask(plaintext: str) -> str:
        """脱敏：保留后 4 位，其余替换为 *"""
        if len(plaintext) <= 4:
            return "****"
        return "*" * (len(plaintext) - 4) + plaintext[-4:]
```

所有涉及模型信息的接口（列表、详情、编辑回显）在 Pydantic Schema 的 `model_validator` 中统一处理脱敏，避免遗漏。

### 4.3 软删除与数据一致性

所有主表（模型、评测集、评测实验）均包含 `deleted_at` 字段（nullable datetime）。软删除时设置 `deleted_at = now()`，查询时统一过滤 `WHERE deleted_at IS NULL`。

**软删除对唯一索引的影响**：模型名称和评测集名称有唯一性约束，软删除后若允许创建同名记录，普通唯一索引会冲突。解决方案：**不在数据库层面对名称建唯一索引**，改为在 Service 层查询时加 `deleted_at IS NULL` 条件进行唯一性校验。这样软删除的记录不参与唯一性检查，逻辑清晰且无需复杂的部分索引。

**外键策略**：SQLite 默认不启用外键约束，需在连接时执行 `PRAGMA foreign_keys = ON`。评测实验表通过 `model_id` 和 `dataset_id` 关联模型和评测集，逐条结果表通过 `experiment_id` 关联实验。外键约束仅用于数据完整性保障，删除操作在 Service 层通过业务逻辑（检查进行中实验）控制，不依赖数据库级联删除。

**软删除后关联数据展示**：评测实验详情需展示关联模型和评测集名称。由于实验创建时已记录 `model_id` 和 `dataset_id`，即使模型/评测集被软删除，JOIN 查询仍可获取其名称，并在响应中附加 `is_deleted: true` 标记，前端展示时加"已删除"标注。

**删除前校验的并发安全**：在 Service 层使用数据库事务 + `SELECT FOR UPDATE`（SQLite 通过 `BEGIN IMMEDIATE` 实现写锁）来保证"检查进行中实验 → 执行软删除"的原子性，避免并发场景下的竞态条件。

### 4.4 响应时间统计（P50/P90/P99）

统计仅包含成功条目的响应时间（与 PM 确认一致）。在实验完成时，从 `experiment_result` 表中查询所有成功条目的 `response_time_ms`，在 Python 层计算百分位数（使用 `statistics.quantiles` 或简单排序取位）并写入 `experiment` 表的统计字段（`avg_response_ms`、`p50_ms`、`p90_ms`、`p99_ms`）。

预计算并缓存统计结果的好处：详情页查询时直接读取，无需每次聚合计算，满足 < 2 秒的性能要求。

---

## 五、接口设计

### 5.1 统一规范

**Base URL**：`/api/v1`

**统一响应格式**：
```json
{
  "code": 0,
  "message": "success",
  "data": { ... }
}
```

**统一错误响应格式**：
```json
{
  "code": 40001,
  "message": "模型名称已存在",
  "data": null
}
```

**错误码规范**：

| 错误码 | 含义 |
|--------|------|
| 0 | 成功 |
| 40001 | 参数校验失败（通用） |
| 40002 | 资源名称已存在 |
| 40003 | 资源不存在 |
| 40004 | 操作不允许（如删除有进行中实验的模型） |
| 40005 | 文件格式错误 |
| 40006 | 文件大小超限 |
| 40301 | 无操作权限 |
| 50001 | 服务器内部错误 |

**分页参数**：所有列表接口统一使用 `page`（从 1 开始）和 `page_size` 参数，响应中包含 `total` 字段。

---

### 5.2 接口总览

#### 模型管理（5 个接口）

| 编号 | HTTP 方法 | 路径 | 描述 |
|------|-----------|------|------|
| M1 | GET | `/api/v1/models` | 获取模型列表（支持搜索、筛选、分页） |
| M2 | POST | `/api/v1/models` | 创建模型 |
| M3 | GET | `/api/v1/models/{model_id}` | 获取模型详情（含关联实验历史最近 10 条） |
| M4 | PUT | `/api/v1/models/{model_id}` | 编辑模型（名称不可修改） |
| M5 | DELETE | `/api/v1/models/{model_id}` | 删除模型（软删除，有进行中实验时拒绝） |

#### 评测集管理（7 个接口）

| 编号 | HTTP 方法 | 路径 | 描述 |
|------|-----------|------|------|
| D1 | GET | `/api/v1/datasets` | 获取评测集列表（支持搜索、分页） |
| D2 | POST | `/api/v1/datasets` | 创建评测集（含 JSON 文件上传） |
| D3 | GET | `/api/v1/datasets/{dataset_id}` | 获取评测集详情（含关联实验历史最近 10 条） |
| D4 | PUT | `/api/v1/datasets/{dataset_id}` | 编辑评测集基本信息（名称/版本号/描述） |
| D5 | DELETE | `/api/v1/datasets/{dataset_id}` | 删除评测集（软删除，有进行中实验时拒绝） |
| D6 | POST | `/api/v1/datasets/{dataset_id}/items/import` | 导入评测集数据（支持追加/覆盖模式） |
| D7 | GET | `/api/v1/datasets/{dataset_id}/items` | 分页查询评测集数据条目 |

#### 评测实验（6 个接口）

| 编号 | HTTP 方法 | 路径 | 描述 |
|------|-----------|------|------|
| E1 | GET | `/api/v1/experiments` | 获取评测实验列表（支持搜索、状态筛选、分页） |
| E2 | POST | `/api/v1/experiments` | 发起评测实验 |
| E3 | GET | `/api/v1/experiments/{experiment_id}` | 获取评测实验详情（含统计指标） |
| E4 | POST | `/api/v1/experiments/{experiment_id}/cancel` | 取消评测实验 |
| E5 | GET | `/api/v1/experiments/{experiment_id}/results` | 分页查询逐条评测结果（支持状态筛选） |
| E6 | GET | `/api/v1/experiments/{experiment_id}/results/export` | 导出评测结果为 JSON 文件 |

> 以下各节对其中核心接口给出完整的请求/响应定义和示例，其余接口遵循相同的规范格式。

---

### 5.3 接口一：创建模型

**POST** `/api/v1/models`

**描述**：创建一个新的 AI 模型记录。

**请求头**：
```
Content-Type: application/json
X-User-Id: {用户ID}
```

**请求体**：
```json
{
  "name": "GPT-4o",
  "model_type": "LLM",
  "version": "v1.0.0",
  "description": "OpenAI GPT-4o 模型",
  "endpoint_url": "https://api.openai.com/v1/chat/completions",
  "api_key": "sk-xxxxxxxxxxxxxxxx"
}
```

**字段说明**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 模型名称，最长 100 字符，全局唯一（软删除记录不参与唯一性校验） |
| model_type | string | 是 | 枚举值：`LLM` / `CLASSIFICATION` / `REGRESSION` / `OTHER` |
| version | string | 否 | 格式 vX.Y.Z，如 v1.0.0 |
| description | string | 否 | 最长 500 字符 |
| endpoint_url | string | 否 | 模型端点 URL |
| api_key | string | 否 | API Key，加密存储 |

**成功响应** `200 OK`：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "name": "GPT-4o",
    "model_type": "LLM",
    "version": "v1.0.0",
    "description": "OpenAI GPT-4o 模型",
    "endpoint_url": "https://api.openai.com/v1/chat/completions",
    "api_key_masked": "************xxxx",
    "status": "ACTIVE",
    "created_by": "user_001",
    "created_at": "2026-05-08T10:00:00Z",
    "updated_at": "2026-05-08T10:00:00Z"
  }
}
```

**错误响应示例**：

名称重复（`400`）：
```json
{
  "code": 40002,
  "message": "模型名称已存在",
  "data": null
}
```

参数校验失败（`400`）：
```json
{
  "code": 40001,
  "message": "version 格式错误，应为 vX.Y.Z（如 v1.0.0）",
  "data": null
}
```

---

### 5.4 接口二：发起评测实验

**POST** `/api/v1/experiments`

**描述**：创建并立即发起一个评测实验，实验创建后异步执行评测任务。

**请求头**：
```
Content-Type: application/json
X-User-Id: {用户ID}
```

**请求体**：
```json
{
  "name": "GPT-4o vs 分类任务-v1",
  "model_id": 1,
  "dataset_id": 3,
  "description": "测试 GPT-4o 在分类任务上的表现",
  "concurrency": 5,
  "timeout_seconds": 30
}
```

**字段说明**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 实验名称，最长 100 字符，允许重名 |
| model_id | integer | 是 | 关联模型 ID，必须为未删除且状态为 ACTIVE 的模型 |
| dataset_id | integer | 是 | 关联评测集 ID，必须为未删除的评测集 |
| description | string | 否 | 最长 500 字符 |
| concurrency | integer | 否 | 并发数，默认 5，范围 1-20 |
| timeout_seconds | integer | 否 | 单条超时秒数，默认 30，范围 5-300 |

**成功响应** `200 OK`：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 10,
    "name": "GPT-4o vs 分类任务-v1",
    "model_id": 1,
    "model_name": "GPT-4o",
    "dataset_id": 3,
    "dataset_name": "分类任务评测集-v1",
    "description": "测试 GPT-4o 在分类任务上的表现",
    "concurrency": 5,
    "timeout_seconds": 30,
    "status": "RUNNING",
    "created_by": "user_001",
    "created_at": "2026-05-08T10:05:00Z",
    "completed_at": null
  }
}
```

**错误响应示例**：

模型不存在或已删除（`400`）：
```json
{
  "code": 40003,
  "message": "模型不存在",
  "data": null
}
```

模型已禁用（`400`）：
```json
{
  "code": 40004,
  "message": "该模型已禁用，无法发起评测实验",
  "data": null
}
```

---

### 5.5 接口三：获取评测实验详情

**GET** `/api/v1/experiments/{experiment_id}`

**描述**：获取评测实验的详情，包含基本信息、统计指标和分页的逐条结果。

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| experiment_id | integer | 实验 ID |

**查询参数**：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | integer | 否 | 1 | 逐条结果页码 |
| page_size | integer | 否 | 50 | 每页条数，最大 100 |
| result_status | string | 否 | - | 筛选逐条结果状态：`SUCCESS` / `FAILED` |

**成功响应** `200 OK`：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 10,
    "name": "GPT-4o vs 分类任务-v1",
    "model_id": 1,
    "model_name": "GPT-4o",
    "model_deleted": false,
    "dataset_id": 3,
    "dataset_name": "分类任务评测集-v1",
    "dataset_deleted": false,
    "description": "测试 GPT-4o 在分类任务上的表现",
    "concurrency": 5,
    "timeout_seconds": 30,
    "status": "COMPLETED",
    "created_by": "user_001",
    "created_at": "2026-05-08T10:05:00Z",
    "completed_at": "2026-05-08T10:12:30Z",
    "statistics": {
      "total_count": 1000,
      "success_count": 987,
      "failed_count": 13,
      "avg_response_ms": 342,
      "p50_ms": 310,
      "p90_ms": 520,
      "p99_ms": 890,
      "note": "响应时间统计仅包含成功条目"
    },
    "results": {
      "total": 1000,
      "page": 1,
      "page_size": 50,
      "items": [
        {
          "seq": 1,
          "input": "请对以下文本进行情感分类：...",
          "expected_output": "正面",
          "actual_output": "正面",
          "response_time_ms": 312,
          "status": "SUCCESS",
          "error_message": null
        },
        {
          "seq": 2,
          "input": "...",
          "expected_output": "负面",
          "actual_output": null,
          "response_time_ms": null,
          "status": "FAILED",
          "error_message": "请求超时"
        }
      ]
    }
  }
}
```

**错误响应示例**：

实验不存在（`400`）：
```json
{
  "code": 40003,
  "message": "评测实验不存在",
  "data": null
}
```

---

### 5.6 接口四：取消评测实验

**POST** `/api/v1/experiments/{experiment_id}/cancel`

**描述**：取消正在执行中的评测实验，已执行的逐条结果保留。

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| experiment_id | integer | 实验 ID |

**请求头**：
```
X-User-Id: {用户ID}
```

**请求体**：无

**成功响应** `200 OK`：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 10,
    "status": "CANCELLED"
  }
}
```

**错误响应示例**：

实验不在执行中状态（`400`）：
```json
{
  "code": 40004,
  "message": "只有执行中的实验可以取消",
  "data": null
}
```

无操作权限（`403`）：
```json
{
  "code": 40301,
  "message": "无操作权限，只有实验发起人或管理员可以取消",
  "data": null
}
```

---

### 5.7 接口五：上传评测集数据

**POST** `/api/v1/datasets/{dataset_id}/items/import`

**描述**：向评测集导入数据，支持追加模式和覆盖模式。

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| dataset_id | integer | 评测集 ID |

**请求头**：
```
Content-Type: multipart/form-data
X-User-Id: {用户ID}
```

**请求体（multipart/form-data）**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | file | 是 | JSON 文件，最大 50MB |
| mode | string | 是 | 导入模式：`append`（追加）/ `overwrite`（清空重新导入） |

**JSON 文件格式**：
```json
[
  {"input": "请对以下文本进行情感分类：今天天气真好", "expected_output": "正面"},
  {"input": "这个产品质量太差了", "expected_output": "负面"},
  {"input": "一般般吧"}
]
```

**成功响应** `200 OK`：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "dataset_id": 3,
    "imported_count": 1000,
    "total_count": 2500,
    "mode": "append"
  }
}
```

**错误响应示例**：

文件过大（`400`）：
```json
{
  "code": 40006,
  "message": "文件大小超限，最大支持 50MB",
  "data": null
}
```

JSON 格式错误（`400`）：
```json
{
  "code": 40005,
  "message": "第 3 行缺少 input 字段",
  "data": null
}
```

---

## 六、数据模型设计

### 6.1 模型表（`model`）

```sql
CREATE TABLE model (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            VARCHAR(100)  NOT NULL,           -- 模型名称（唯一性在 Service 层校验）
    model_type      VARCHAR(20)   NOT NULL,           -- LLM / CLASSIFICATION / REGRESSION / OTHER
    version         VARCHAR(20),                      -- 版本号，格式 vX.Y.Z
    description     VARCHAR(500),                     -- 描述
    endpoint_url    TEXT,                             -- 模型端点 URL
    api_key_enc     TEXT,                             -- AES-256-GCM 加密后的 API Key
    status          VARCHAR(20)   NOT NULL DEFAULT 'ACTIVE',  -- ACTIVE / DISABLED
    created_by      VARCHAR(100)  NOT NULL,           -- 创建人用户 ID
    updated_by      VARCHAR(100),                     -- 最后修改人用户 ID
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at      DATETIME                          -- 软删除时间，NULL 表示未删除
);

-- 索引
CREATE INDEX idx_model_name ON model(name) WHERE deleted_at IS NULL;
CREATE INDEX idx_model_created_at ON model(created_at);
CREATE INDEX idx_model_status ON model(status) WHERE deleted_at IS NULL;
```

**字段说明**：
- `api_key_enc`：存储 AES-256-GCM 加密后的密文（base64 编码），格式为 `base64(nonce[12字节] + ciphertext)`
- `deleted_at`：软删除标记，非 NULL 表示已删除；唯一性校验在 Service 层通过 `WHERE deleted_at IS NULL` 过滤实现
- `idx_model_name` 使用部分索引（SQLite 3.8.9+ 支持），仅对未删除记录建索引，提升唯一性校验查询效率

### 6.2 评测集表（`dataset`）

```sql
CREATE TABLE dataset (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            VARCHAR(100)  NOT NULL,           -- 评测集名称
    version         VARCHAR(20),                      -- 版本号
    description     VARCHAR(500),                     -- 描述
    item_count      INTEGER       NOT NULL DEFAULT 0, -- 数据条数（冗余字段，避免 COUNT 查询）
    created_by      VARCHAR(100)  NOT NULL,
    updated_by      VARCHAR(100),
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at      DATETIME
);

-- 索引
CREATE INDEX idx_dataset_name ON dataset(name) WHERE deleted_at IS NULL;
CREATE INDEX idx_dataset_created_at ON dataset(created_at);
```

**字段说明**：
- `item_count`：冗余字段，在导入/清空数据时同步更新，避免列表页每次 COUNT 查询
- 唯一性策略与模型表相同，在 Service 层校验

### 6.3 评测集数据条目表（`dataset_item`）

```sql
CREATE TABLE dataset_item (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_id      INTEGER       NOT NULL REFERENCES dataset(id),
    seq             INTEGER       NOT NULL,            -- 序号（在该评测集内从 1 开始）
    input_text      TEXT          NOT NULL,            -- 评测输入
    expected_output TEXT,                              -- 期望输出（可为空）
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_dataset_item_dataset_id ON dataset_item(dataset_id);
CREATE UNIQUE INDEX idx_dataset_item_seq ON dataset_item(dataset_id, seq);
```

**字段说明**：
- `seq`：在同一评测集内的序号，追加导入时从当前最大 seq + 1 开始递增
- `(dataset_id, seq)` 联合唯一索引，保证序号在评测集内唯一，同时支持按序号分页查询
- 深翻页优化：使用 `WHERE dataset_id = ? AND seq > ?` 的游标分页替代 `OFFSET`，避免深翻页全表扫描

### 6.4 评测实验表（`experiment`）

```sql
CREATE TABLE experiment (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    name                VARCHAR(100)  NOT NULL,        -- 实验名称（允许重名）
    model_id            INTEGER       NOT NULL REFERENCES model(id),
    dataset_id          INTEGER       NOT NULL REFERENCES dataset(id),
    description         VARCHAR(500),
    concurrency         INTEGER       NOT NULL DEFAULT 5,
    timeout_seconds     INTEGER       NOT NULL DEFAULT 30,
    status              VARCHAR(20)   NOT NULL DEFAULT 'PENDING',
    -- 统计字段（实验完成时预计算写入）
    total_count         INTEGER,
    success_count       INTEGER,
    failed_count        INTEGER,
    avg_response_ms     INTEGER,
    p50_ms              INTEGER,
    p90_ms              INTEGER,
    p99_ms              INTEGER,
    -- 元数据
    created_by          VARCHAR(100)  NOT NULL,
    created_at          DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at        DATETIME,
    deleted_at          DATETIME
);

-- 索引
CREATE INDEX idx_experiment_status ON experiment(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_experiment_model_id ON experiment(model_id);
CREATE INDEX idx_experiment_dataset_id ON experiment(dataset_id);
CREATE INDEX idx_experiment_created_at ON experiment(created_at);
CREATE INDEX idx_experiment_created_by ON experiment(created_by);
```

**状态枚举**：`PENDING`（待执行）/ `RUNNING`（执行中）/ `COMPLETED`（已完成）/ `FAILED`（失败）/ `CANCELLED`（已取消）

**字段说明**：
- 统计字段（`total_count` 等）在实验完成时一次性写入，详情页直接读取，无需实时聚合
- `model_id` 和 `dataset_id` 保留外键引用，即使关联记录被软删除，JOIN 查询仍可获取名称

### 6.5 逐条评测结果表（`experiment_result`）

```sql
CREATE TABLE experiment_result (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_id       INTEGER       NOT NULL REFERENCES experiment(id),
    dataset_item_id     INTEGER       NOT NULL REFERENCES dataset_item(id),
    seq                 INTEGER       NOT NULL,         -- 对应评测集中的序号
    input_text          TEXT          NOT NULL,         -- 快照：执行时的 input（防止评测集数据变更影响历史）
    expected_output     TEXT,                           -- 快照：执行时的 expected_output
    actual_output       TEXT,                           -- 模型返回的输出
    response_time_ms    INTEGER,                        -- 响应时间（ms），失败时为 NULL
    status              VARCHAR(20)   NOT NULL,         -- SUCCESS / FAILED
    error_message       TEXT,                           -- 失败时的错误信息
    created_at          DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_result_experiment_id ON experiment_result(experiment_id);
CREATE INDEX idx_result_exp_status ON experiment_result(experiment_id, status);
CREATE INDEX idx_result_exp_seq ON experiment_result(experiment_id, seq);
```

**字段说明**：
- `input_text` 和 `expected_output` 存储快照，避免评测集数据被修改后影响历史结果展示
- `(experiment_id, seq)` 索引支持按序号游标分页
- `(experiment_id, status)` 复合索引支持按状态筛选的分页查询

### 6.6 操作日志表（`audit_log`）

```sql
CREATE TABLE audit_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    operator        VARCHAR(100)  NOT NULL,            -- 操作人用户 ID
    action          VARCHAR(50)   NOT NULL,            -- CREATE / UPDATE / DELETE
    resource_type   VARCHAR(50)   NOT NULL,            -- model / dataset / experiment
    resource_id     INTEGER       NOT NULL,            -- 操作的资源 ID
    detail          TEXT,                              -- 操作详情（JSON 格式，记录变更前后值）
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 索引（仅用于运维查询，不需要高频访问）
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at);
CREATE INDEX idx_audit_log_resource ON audit_log(resource_type, resource_id);
```

**字段说明**：
- 日志保留 180 天，通过定时任务（APScheduler）每天清理 `created_at < NOW() - 180 days` 的记录
- `detail` 字段存储 JSON，记录变更前后的关键字段值，供运维排查使用
- 本期不提供前端查看入口，仅作后端审计存储

### 6.7 索引设计总结

| 表 | 索引 | 用途 |
|----|------|------|
| model | `idx_model_name`（部分索引） | 名称唯一性校验、名称搜索 |
| model | `idx_model_created_at` | 按创建时间排序 |
| model | `idx_model_status`（部分索引） | 按状态筛选 |
| dataset | `idx_dataset_name`（部分索引） | 名称唯一性校验、名称搜索 |
| dataset | `idx_dataset_created_at` | 按创建时间排序 |
| dataset_item | `idx_dataset_item_dataset_id` | 按评测集查询条目 |
| dataset_item | `idx_dataset_item_seq`（唯一） | 游标分页、序号唯一性 |
| experiment | `idx_experiment_status`（部分索引） | 按状态筛选 |
| experiment | `idx_experiment_model_id` | 查询模型关联实验 |
| experiment | `idx_experiment_dataset_id` | 查询评测集关联实验 |
| experiment | `idx_experiment_created_at` | 按创建时间排序 |
| experiment_result | `idx_result_experiment_id` | 查询实验的所有结果 |
| experiment_result | `idx_result_exp_status` | 按状态筛选结果 |
| experiment_result | `idx_result_exp_seq` | 游标分页 |

---

## 七、非功能性设计

### 7.1 性能设计

**列表页 < 2 秒**：通过合理索引 + 分页（每页 20 条）保证。模型/评测集/实验列表均有 `created_at` 索引支持排序，`status` 部分索引支持筛选。

**深翻页优化**：评测集数据条目和逐条结果均采用游标分页（`WHERE seq > last_seq LIMIT page_size`），避免 `OFFSET` 深翻页的全表扫描问题。

**大文件上传**：后端使用流式读取 JSON 文件（逐行解析），避免将 50MB 文件全部加载到内存。使用 Python 的 `ijson` 库实现流式 JSON 解析，内存占用控制在 O(1)。

**结果导出**：使用 FastAPI 的 `StreamingResponse` 流式写出 JSON，避免将全部结果序列化到内存后再返回。

### 7.2 安全设计

**API Key 加密**：AES-256-GCM，密钥通过环境变量 `ENCRYPTION_KEY`（base64 编码的 32 字节随机值）注入，不硬编码。

**脱敏处理**：所有涉及模型信息的接口在 Pydantic Schema 的序列化层统一脱敏，`api_key_enc` 字段永远不出现在响应中，替换为 `api_key_masked`（保留后 4 位）。

**权限控制**：通过请求头 `X-User-Id` 传递用户身份，Service 层校验操作权限（编辑/删除仅限创建人或管理员）。本期采用简单的创建人校验，不引入 RBAC 框架。

### 7.3 可用性设计

**启动恢复**：应用启动时检查数据库中状态为 `RUNNING` 的实验，将其标记为 `FAILED`（因进程重启导致任务丢失），避免实验永久停留在 `RUNNING` 状态。

**进度实时性**：评测执行过程中，每完成一条结果立即写入数据库（而非批量写入），前端可通过轮询实验详情接口（每 3 秒）获取实时进度。

**SQLite WAL 模式**：启用 WAL（Write-Ahead Logging）模式（`PRAGMA journal_mode=WAL`），提升并发读写性能，避免读操作被写操作阻塞。

---

## 八、关键决策记录

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 异步任务方案 | asyncio 原生（不用 Celery） | 并发规模小（最大 20），单进程内 asyncio 足够；避免引入 Redis/RabbitMQ 等外部依赖，符合"内嵌运行"约束 |
| 唯一性校验位置 | Service 层（不用数据库唯一索引） | 软删除场景下数据库唯一索引会与已删除记录冲突；SQLite 部分索引可解决但可移植性差；Service 层校验更灵活 |
| 统计预计算 | 实验完成时写入（不实时聚合） | 10000 条数据的聚合查询在 SQLite 上耗时不可控；预计算保证详情页 < 2 秒响应 |
| 结果数据快照 | 存储 input/expected_output 快照 | 防止评测集数据被修改后影响历史结果展示，保证历史可追溯 |
| 分页方案 | 游标分页（dataset_item/result） | 深翻页（第 200 页）时 OFFSET 性能差；游标分页 O(log n) 稳定 |
| 重试策略 | 本期不实现自动重试 | PRD 未要求；自动重试增加端点压力；用户可手动重新发起实验 |
