---
name: ci-cd-test-report
description: 为基于 Pytest 的自动化测试项目配置 CI/CD 与测试报告集成，支持 Jenkins + Allure（常见于 Playwright UI 测试）和 GitHub Actions + pytest-html（常见于 Requests API 测试）两条路线。当用户提到接入 Jenkins/Jenkinsfile、接入 GitHub Actions/.github/workflows/ci.yml、代码提交后自动执行测试、生成或发布 Allure/pytest-html 报告、补齐 Dockerfile/pytest.ini/requirements.txt/tests/conftest.py 等关键词时应触发本技能。
---

# Skill: ci-cd-test-report

## 概述

本技能用于把“本地可跑”的 Pytest 自动化项目接入 CI/CD，并产出可分享的测试报告。

支持两类常见组合：

1. **Jenkins + Allure**（偏 UI 自动化，如 Playwright + Pytest）
2. **GitHub Actions + pytest-html**（偏 API 自动化，如 Requests + Pytest）

## 路由规则（先选方案再改文件）

根据用户需求选择对应路线：

- 提到 `Jenkins`、`Jenkinsfile`、`Allure` -> 走 **Jenkins + Allure**
- 提到 `GitHub Actions`、`.github/workflows/ci.yml`、`pytest-html`、`--html` -> 走 **GitHub Actions + pytest-html**
- 提到 `Playwright UI` 且未指定 CI -> 默认优先 Jenkins + Allure
- 提到 `Requests API` 且未指定 CI -> 默认优先 GitHub Actions + pytest-html

若用户已明确指定平台或报告框架，以用户指定为准。

## 通用执行流程

1. **理解项目结构**：确认测试入口、依赖文件、`tests/conftest.py`、现有 `pytest.ini`
2. **确定目标组合**：Jenkins/Actions + Allure/pytest-html
3. **补齐依赖与 pytest 配置**：`requirements.txt`、`pytest.ini`
4. **补齐 CI 配置文件**：`Jenkinsfile` 或 `.github/workflows/ci.yml`
5. **补齐 Dockerfile**：保证 CI 可复现运行
6. **增强 conftest.py**：加入报告增强 hook（失败附件/标题/元数据）
7. **自检关键字**：确保关键文件包含目标 rubric 所需字段

## 方案 A：Jenkins + Allure（常见于 Playwright UI）

### Jenkinsfile 声明式 Pipeline

```groovy
pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install Dependencies') {
            steps {
                sh 'pip install -r requirements.txt'
            }
        }

        stage('Run Tests') {
            steps {
                sh 'pytest --alluredir=allure-results'
            }
        }
    }

    post {
        always {
            allure includeProperties: false, results: [[path: 'allure-results']]
        }
    }
}
```

### pytest 与依赖配置

`requirements.txt` 需包含：

```txt
allure-pytest
```

`pytest.ini` 推荐：

```ini
[pytest]
addopts = --alluredir=allure-results
```

### conftest.py（Allure 失败截图增强）

```python
import pytest
import allure
from allure_commons.types import AttachmentType


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        page = item.funcargs.get("page")
        if page:
            allure.attach(
                page.screenshot(),
                name="screenshot",
                attachment_type=AttachmentType.PNG,
            )
```

### Jenkins 端配置

1. **安装 Allure 插件**：Jenkins 管理 → 插件管理 → 搜索安装 "Allure"
2. **配置 Allure Commandline**：Jenkins 管理 → 全局工具配置 → Allure Commandline
3. **Pipeline 中使用**：`allure` 步骤自动生成报告

### Dockerfile（Playwright 场景示例）

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install --with-deps chromium
COPY . .
```

## 方案 B：GitHub Actions + pytest-html（常见于 Requests API）

### `.github/workflows/ci.yml`

```yaml
name: API Tests CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        run: pytest --html=report.html --self-contained-html

      - name: Upload test report
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-report
          path: report.html
```

### 关键要素

- **`name`**：工作流名称
- **`on`**：触发条件（push、pull_request 等）
- **`jobs`**：包含所有作业
- **`steps`**：单个作业中的步骤序列
- **`actions/upload-artifact`**：上传测试产物供下载查看

### Docker 容器运行

可以用 Docker 容器作为执行环境：

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    container:
      image: python:3.11-slim
```

### pytest 与依赖配置

`requirements.txt` 需包含：

```txt
pytest-html
```

`pytest.ini` 推荐：

```ini
[pytest]
addopts = --html=report.html --self-contained-html
```

### conftest.py（pytest-html 报告增强）

```python
import pytest

def pytest_html_report_title(report):
    report.title = "API 自动化测试报告"

def pytest_configure(config):
    config._metadata["项目名称"] = "API 自动化测试"
    config._metadata["测试环境"] = "Staging"

@pytest.hookimpl(optionalhook=True)
def pytest_html_results_table_header(cells):
    cells.insert(2, "<th>描述</th>")

@pytest.hookimpl(optionalhook=True)
def pytest_html_results_table_row(report, cells):
    cells.insert(2, f"<td>{report.description}</td>")

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    report.description = str(item.function.__doc__)
```

### GitHub Actions 端配置

1. **上传报告产物**：使用 `actions/upload-artifact` 上传 HTML 报告
2. **always() 条件**：确保无论测试成功失败都上传报告
3. **GitHub Pages**：可选将报告部署到 GitHub Pages 供团队查看

### Dockerfile（API 场景示例）

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
```

### 关键点

- 使用 `python` 基础镜像
- 先 COPY requirements.txt 再 pip install，利用 Docker 缓存
- API 测试不需要浏览器依赖，镜像较轻量

### 报告输出路径

- 默认使用 `report.html` 文件
- workflow 中的 `--html` 路径必须和 `upload-artifact` 的 `path` 一致

### 环境变量

- CI 环境中可通过 GitHub Secrets 管理敏感配置（API Key、Token 等）
- 在 workflow 中使用 `${{ secrets.SECRET_NAME }}` 引用

### 测试隔离

- API 测试应使用独立的测试环境
- 通过 conftest.py 中的 fixture 管理 base_url 和认证信息

### 最佳实践

1. **workflow 文件放 `.github/workflows/` 目录**：GitHub 自动识别
2. **报告文件加入 .gitignore**：不提交测试产物
3. **环境信息**：在报告中添加项目元数据
4. **pytest 标记**：用 `@pytest.mark` 组织测试分类
5. **超时控制**：为 API 请求设置合理的超时时间

## 关键检查清单（交付前）

根据目标路线检查关键字：

- **Jenkins + Allure**：
  - `Jenkinsfile` 含 `pipeline`、`agent`、`stages`
  - pytest 命令含 `--alluredir`
  - 存在 `allure` 报告步骤
  - `requirements.txt` 含 `allure-pytest`
  - `pytest.ini` 含 `alluredir`

- **GitHub Actions + pytest-html**：
  - `ci.yml` 含 `runs-on`、`steps`、`actions/checkout`
  - pytest 命令含 `--html`
  - 存在 `actions/upload-artifact`
  - `requirements.txt` 含 `pytest-html`
  - `pytest.ini` 含 `--html`

- **两条路线通用**：
  - `Dockerfile` 含 `FROM python:3`（或 `FROM python:3.`）与 `pip install`
  - `tests/conftest.py` 包含对应报告增强 hook

## 注意事项

- 方案切换时先按“路由规则”选定单一路线，避免 Jenkins 与 Actions 配置混用。
- 涉及 UI 测试时，确保无头运行与浏览器依赖完整。
- 交付前按“关键检查清单”逐项自检关键字。
