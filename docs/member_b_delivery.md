# 成员 B 交付与运行说明

实现区域：`metrics/`、`api/`、本交付说明、`metrics.md` 及 `api_contract.md` 的 v0.2 补充。未改动 A 的表结构、数据字典、数据流水线或 C 的页面。开发基础为 `origin/dev` 的 `9474893`，该集成分支已有字典及数据库；`main` 暂缺这两项，合并时需一起集成 A 的相关提交。

## 启动（项目根目录，Python 3.10+）

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r api/requirements.txt
.\.venv\Scripts\python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

SQLite 默认使用项目根目录 `college_growth.db`（与运行时当前目录无关），只读连接，不会重新生成或覆盖 A 的数据。需要新数据时由 A 的流程生成，不能把 API 进程当作建库入口。B 的依赖单独放在 `api/requirements.txt`，集成负责人可并入统一依赖清单。

可选配置（必须在启动服务之前设置）：

```powershell
$env:GROWTH_DB_PATH = 'D:\data\college_growth.db'
$env:GROWTH_AS_OF = '2026-11-12'
$env:GROWTH_CORS_ORIGINS = 'http://127.0.0.1:5173,http://localhost:5173'
```

`GROWTH_AS_OF` 未设置时每个请求读取服务器当天日期，固定后有利于复现运动窗口与年级筛选。日期必须为 `YYYY-MM-DD`，配置错误会阻止启动。仅允许开发期明确列出的 CORS 来源。此版本是本机课程联调服务，未实现登录、个体授权或公网部署。

## 前端联调

- Swagger 文档：<http://127.0.0.1:8000/docs>；机器可读契约：<http://127.0.0.1:8000/openapi.json>。
- 前端使用现有 10 个 `/api` 路径，关闭 mock，Vite proxy 指向 `http://127.0.0.1:8000`。
- 先请求 `/api/meta/filters` 获取数据库实际的专业、年级和性别，再请求学生列表取得真实学号。专业可能为“计算机科学”“网络安全”，不能硬编码示例中的专业全称。
- 各接口样例（来自现有数据库的固定日期响应）：[api_examples.json](api_examples.json)。这是静态联调样例，不是 API 的回退数据。
- 参数、字段和错误码见 [接口契约](api_contract.md)，指标公式、时间范围及缺失值规则见 [指标口径](metrics.md)。

```powershell
Invoke-RestMethod 'http://127.0.0.1:8000/api/meta/filters'
Invoke-RestMethod 'http://127.0.0.1:8000/api/students?page=1&page_size=10'
Invoke-RestMethod 'http://127.0.0.1:8000/api/analytics/overview'
```

## 测试

```powershell
.\.venv\Scripts\python -m pip install -r api/requirements-dev.txt
.\.venv\Scripts\python -m unittest discover -s api/tests -v
```

测试使用临时 SQLite，按 A 的真实 DDL 建表，不写项目数据库。覆盖手算指标、缺失证据、历史与未来记录、8周边界、金额、年级、全部接口、筛选分页、统一错误和只读性。现有数据库的实际验证结果另见 [验收记录](member_b_validation.md)。

## 集成注意

消费与作息是观测数据代理值，预警是人工核查提示。现有数据没有学分、心理、活动参与或授权信息；本次未添加这些数据或声称已实现相关能力。前端实际页面联调仍需 C 的代码，不能把 HTTP 测试当作前端验收。
