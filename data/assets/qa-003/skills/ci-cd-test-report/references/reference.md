# 参考文档：Pytest 项目 CI/CD + 报告集成

## 目标

把本地可运行的 Pytest 自动化测试项目接入 CI/CD，做到代码提交后自动执行测试并产出可视化报告，便于团队查看和追踪质量。

## 支持场景

### 场景 A：UI 自动化（Playwright + Pytest）

- 常用 CI 平台：Jenkins
- 常用报告框架：Allure
- 典型文件：`Jenkinsfile`、`pytest.ini`、`requirements.txt`、`Dockerfile`、`tests/conftest.py`
- 关注点：浏览器依赖、失败截图、Allure 结果目录与 Jenkins 报告步骤一致

### 场景 B：API 自动化（Requests + Pytest）

- 常用 CI 平台：GitHub Actions
- 常用报告框架：pytest-html
- 典型文件：`.github/workflows/ci.yml`、`pytest.ini`、`requirements.txt`、`Dockerfile`、`tests/conftest.py`
- 关注点：`--html` 报告输出、`actions/upload-artifact` 归档、敏感变量通过 Secrets 管理

## 技术栈映射

- Python 3 + Pytest（通用）
- Jenkins 声明式 Pipeline（Jenkins 路线）
- GitHub Actions Workflow（Actions 路线）
- Docker 容器化（通用）
- Allure 或 pytest-html（按场景选择）

## 产物一致性要求

- CI 配置、pytest 参数、报告目录、产物归档路径必须相互对齐。
- `requirements.txt` 中的报告依赖必须与所选报告框架一致。
- `conftest.py` 中的 hook 应与报告框架匹配（Allure 或 pytest-html）。
