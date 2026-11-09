# 前端接口清单（v0.1）

> 提出方：C（前端展示层）　接收方：B（指标与接口层）
> 用途：前端按这份契约先在 mock 上开发，B 按这份契约实现 `api/`；字段有异议请直接在群里改这一份，改完同步版本号。

## 一、通用约定

| 项目 | 约定 | 说明 |
| --- | --- | --- |
| 前缀 | `/api` | 前端通过 `VITE_API_BASE` 配置，联调时用 vite proxy 转发 |
| 方法 | 全部 `GET` | 目前只有查询，没有写操作 |
| 编码 | UTF-8，`application/json` | |
| 字段命名 | 英文小写 + 下划线（`total_score`） | 与 A 的数据字典保持一致 |
| 日期 | `YYYY-MM-DD`；日期时间 `YYYY-MM-DD HH:mm:ss` | 不用时间戳 |
| 分页 | `page` 从 **1** 开始，`page_size` 默认 10 | |
| 空值 | 返回空数组 `[]`，不要返回 `null` | 前端按空数组渲染「暂无数据」 |

### 统一返回结构

```json
{ "code": 0, "message": "ok", "data": {} }
```

- `code = 0` 表示成功，其他值为失败；
- 失败时 `data` 为 `null`，`message` 写一句能直接展示给用户的中文；
- 前端约定错误码：`404` 资源不存在，`500` 服务端异常。

---

## 二、接口总表

| # | 接口 | 用途 | 优先级 |
| --- | --- | --- | --- |
| 1 | `GET /api/meta/filters` | 筛选下拉框枚举 | P0 |
| 2 | `GET /api/students` | 学生分页列表 | P0 |
| 3 | `GET /api/students/{id}/portrait` | 基本画像 + 六维指标 | P0 |
| 4 | `GET /api/students/{id}/scores` | 学业明细 | P0 |
| 5 | `GET /api/students/{id}/consume` | 消费明细 | P1 |
| 6 | `GET /api/students/{id}/library` | 借阅明细 | P1 |
| 7 | `GET /api/students/{id}/sport` | 运动明细 | P1 |
| 8 | `GET /api/analytics/overview` | 群体总览 KPI | P1 |
| 9 | `GET /api/analytics/majors` | 专业维度对比 | P1 |
| 10 | `GET /api/analytics/alerts` | 预警名单 | P2 |

---

## 三、接口详情

### 1. 筛选枚举 `GET /api/meta/filters`

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "majors": ["计算机科学与技术", "软件工程", "人工智能"],
    "grades": ["大一", "大二", "大三", "大四"],
    "genders": ["男", "女"]
  }
}
```

### 2. 学生列表 `GET /api/students`

查询参数（全部可选）：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `major` | string | 专业全称 |
| `grade` | string | `大一` / `大二` / `大三` / `大四` |
| `gender` | string | `男` / `女` |
| `keyword` | string | 按姓名或学号模糊匹配 |
| `page` | int | 默认 1 |
| `page_size` | int | 默认 10 |

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "list": [
      {
        "student_id": "20230001",
        "name": "韩若曦",
        "gender": "女",
        "major": "网络空间安全",
        "enroll_year": 2023,
        "total_score": 71,
        "level": "良好",
        "academic": 83
      }
    ],
    "total": 100,
    "page": 1,
    "page_size": 10
  }
}
```

- `total_score`：综合成长分 0-100；
- `level`：`优秀`（≥80）/ `良好`（≥70）/ `合格`（≥60）/ `待提升`（<60）；
- `academic`：学业维度分，列表页用来排序。

### 3. 个体画像 `GET /api/students/{id}/portrait`

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "basic": {
      "student_id": "20230001",
      "name": "韩若曦",
      "gender": "女",
      "major": "网络空间安全",
      "enroll_year": 2023,
      "enroll_date": "2023-09-04"
    },
    "total_score": 81,
    "level": "优秀",
    "tags": ["学业稳定", "阅读爱好者", "运动达人", "晨型作息"],
    "metrics": [
      { "key": "academic",    "label": "学业表现",   "value": 89, "desc": "各科成绩加权平均后的归一化得分" },
      { "key": "reading",     "label": "阅读素养",   "value": 79, "desc": "图书馆借阅册数与借阅频次的综合得分" },
      { "key": "sport",       "label": "运动健康",   "value": 83, "desc": "运动时长、频次与消耗热量的综合得分" },
      { "key": "routine",     "label": "作息规律",   "value": 78, "desc": "早餐覆盖率与夜宵占比折算的作息得分" },
      { "key": "consumption", "label": "消费理性",   "value": 66, "desc": "日均消费与合理区间的偏离度" },
      { "key": "diversity",   "label": "生活丰富度", "value": 71, "desc": "消费场景、消费品类与运动类型的多样性" }
    ]
  }
}
```

> **需要 B 确认的两件事**
> 1. 六个 `key` 是否就按这套口径？`metrics` 的顺序就是雷达图的顶点顺序；
> 2. `total_score` 的权重是多少（前端 mock 暂用 学业 40% + 其余各 12%），
>    定了以后请写进 `docs/data_dictionary.md`，前端展示口径要和 B 一致。

### 4. 学业明细 `GET /api/students/{id}/scores`

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "trend": [
      { "label": "2024-01", "value": 86 },
      { "label": "2024-06", "value": 86 },
      { "label": "2025-01", "value": 89 }
    ],
    "courses": [
      { "label": "计算机网络", "value": 92 },
      { "label": "高等数学", "value": 78 }
    ],
    "best_course": "计算机网络",
    "weak_course": "高等数学"
  }
}
```

- `trend`：按学期聚合的平均分，`label` 用 `YYYY-MM`（考试月份）；
- `courses`：各课程平均分，前端按分数降序展示。

### 5. 消费明细 `GET /api/students/{id}/consume`

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "structure": [
      { "label": "正餐", "value": 66, "amount": 1113.8 },
      { "label": "饮品", "value": 12, "amount": 191.7 }
    ],
    "hourly": [{ "label": "0", "value": 0 }, { "label": "12", "value": 8 }],
    "summary": {
      "avg_daily": 14.4,
      "total_amount": 1149.2,
      "record_count": 82,
      "breakfast_rate": 0.51,
      "night_rate": 0.08
    }
  }
}
```

- `structure[].value` 是次数，`amount` 是金额；
- `hourly` 固定 24 项，`label` 为 `"0"`…`"23"`；
- `breakfast_rate` / `night_rate` 为 0-1 的小数。

### 6. 借阅明细 `GET /api/students/{id}/library`

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "top": [{ "label": "百年孤独", "value": 2 }, { "label": "机器学习", "value": 1 }],
    "total": 11,
    "avg_days": 16
  }
}
```

### 7. 运动明细 `GET /api/students/{id}/sport`

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "types": [{ "label": "健身", "value": 9 }, { "label": "跑步", "value": 4 }],
    "total_minutes": 998,
    "total_calories": 7887,
    "weekly": [{ "label": "第1周", "value": 0 }, { "label": "第2周", "value": 120 }]
  }
}
```

- `weekly` 固定 8 项，`label` 用 `第1周`…`第8周`。

### 8. 群体总览 `GET /api/analytics/overview`

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "students": 100,
    "avg_score": 68,
    "alert_count": 16,
    "top_major": "计算机科学与技术",
    "avg_metrics": [
      { "label": "学业表现", "value": 65 },
      { "label": "阅读素养", "value": 70 }
    ]
  }
}
```

### 9. 专业对比 `GET /api/analytics/majors`

```json
{
  "code": 0,
  "message": "ok",
  "data": [
    {
      "major": "计算机科学与技术",
      "students": 23,
      "avg_score": 71,
      "dims": [
        { "label": "学业表现", "value": 68 },
        { "label": "阅读素养", "value": 73 }
      ]
    }
  ]
}
```

- `dims` 顺序与画像页 `metrics` 一致，前端据此算「优势维度 / 短板维度」。

### 10. 预警名单 `GET /api/analytics/alerts`

```json
{
  "code": 0,
  "message": "ok",
  "data": [
    {
      "student_id": "20250087",
      "name": "田泽宇",
      "major": "人工智能",
      "total_score": 51,
      "level": "待提升",
      "reason": "学业预警 / 综合分偏低"
    }
  ]
}
```

- 按 `total_score` 升序（最需要干预的排前面）；
- `reason` 多个原因用 ` / ` 连接，建议不超过两个。

---

## 四、联调约定

1. **端口**：建议 B 的服务跑在 `127.0.0.1:8000`，前端把 `VITE_USE_MOCK` 改成 `false` 后走 vite proxy；
2. **CORS**：开发期用 proxy 可以不管跨域；如果 B 直接暴露端口，需要允许 `http://127.0.0.1:5173`；
3. **mock**：前端 `mock/` 目录已经按这份契约实现了全部 10 个接口，B 可以拿它对照返回结构；
4. **变更流程**：字段有变动先改这份文档、在群里说一声，再动代码（避免前端白改）。

## 五、待确认清单

| # | 问题 | 找谁 |
| --- | --- | --- |
| 1 | 六维指标的口径与权重 | B |
| 2 | 是否统一返回 `{code, message, data}` | B |
| 3 | 后端框架与端口（Flask / FastAPI） | B |
| 4 | `student_id` 是学号还是流水号、类型 | A |
| 5 | 中文枚举是否固定（男/女、一食堂、正餐…） | A |
| 6 | `data_dictionary.md` 的产出时间 | A |

## 六、变更记录

| 版本 | 日期 | 变更内容 | 修改人 |
| --- | --- | --- | --- |
| v0.1 | 2026-11-06 | 首版，10 个接口 | C |
