# 问题实例化与召回方案设计

## 1. 目标

1. **Target 示例发现**：从库中挖掘各占位符（host_id、uid、src_ip、md5_after 等）的实例值，用于将 26 个问题模板实例化。
2. **召回函数设计**：用少量「按实体召回」的查询函数覆盖多类问题，返回与目标实体相关的摘要 JSON，供多题共用，而不是一题一查。
3. **模版化实现**：查询通过参数化函数实现，支持时间区间等可选参数，返回统一 JSON 结构。

---

## 2. 问题模板与占位符归纳

### 2.1 占位符类型

| 占位符 | 对应 schema 字段 | 涉及问题 ID | 示例来源表 |
|--------|------------------|-------------|------------|
| `<host_id>` | host_assets.host_id / 各表.host_id | 1,2,3,4,5,6,8,9,10,11 | host_assets, audit_events |
| `<uid>` | audit_events.uid | 5,8,22,23,24,25 | audit_events |
| `<src_ip>` | network_activities.src_ip | 12,13,14,15,16 | network_activities |
| `<md5_after>` | file_integrity_events.md5_after | 17,18,19,21 | file_integrity_events |
| `<md5_before>` | file_integrity_events.md5_before | 20 | file_integrity_events |
| `<rule_id>` | security_alerts.rule_id | 3,7 | security_alerts, security_rules |
| `<src_user>` | network_activities.src_user | 26 | network_activities |
| `<alert_level>` | security_alerts.alert_level | 3 | security_alerts |
| `<start_time>`, `<end_time>` | 各表.timestamp | 5,7,8,10,12,14,16,22,23,24,25,26 | - |

### 2.2 按「主实体」归类

- **以 host 为主**：1,2,3,4,5,6,8,9,10,11 → 召回「某主机的多表摘要」即可支撑多题。
- **以 src_ip 为主**：12,13,14,15,16 → 召回「某 IP 的网络活动摘要」。
- **以 file hash 为主**：17,18,19,20,21 → 召回「某哈希的 FIM 摘要」。
- **以 uid 为主**：22,23,24,25（5,8 在 host 召回后可按 uid 过滤）→ 召回「某用户的审计摘要」。
- **以 src_user 为主**：26 → 召回「某源用户的网络摘要」。
- **以 rule_id 为主**：7（3 以 host 为主，rule 作条件）→ 召回「某规则在多主机上的触发摘要」。

---

## 3. 召回函数与问题映射（一对多）

原则：**一个召回函数 = 一类「实体 + 可选时间」的摘要**，多道题共用同一类摘要，靠 LLM 或上层逻辑从摘要里取不同维度作答。

### 3.1 函数清单

| 函数名 | 主参数 | 可选参数 | 返回内容摘要 | 支持的问题 ID |
|--------|--------|----------|--------------|----------------|
| `recall_host_scope` | host_id | start_time, end_time | 该主机的审计事件、告警、网络活动、相关 FIM 的摘要（含时间、关键字段） | 1,2,3,4,5,6,8,9,10,11 |
| `recall_by_src_ip` | src_ip | start_time, end_time | 该 IP 的连接次数、端口/用户分布、时间序列摘要 | 12,13,14,15,16 |
| `recall_by_file_hash` | md5_after | md5_before, start_time, end_time | 该哈希的路径、事件类型、权限变更、首次/最近时间等 | 17,18,19,20,21 |
| `recall_by_uid` | uid | start_time, end_time | 该用户的命令、访问文件、进程、权限变更等审计摘要 | 22,23,24,25；5,8 可与 host 召回结果联合使用 |
| `recall_by_src_user` | src_user | start_time, end_time | 该源用户的连接数、目标用户与 IP 分布 | 26 |
| `recall_by_rule_id` | rule_id | start_time, end_time | 该规则在各 host 上的触发时间、host 列表、时间分布 | 7；3 的 rule 条件可用在 host 摘要上过滤 |

### 3.2 问题 → 召回函数 映射表

| 问题 ID | 主召回函数 | 辅助/过滤 |
|---------|------------|-----------|
| 1 | recall_host_scope | 过滤 file_name 含 shadow |
| 2 | recall_host_scope | 用其中的 network 段 |
| 3 | recall_host_scope | 过滤 alert_level≥param，用 rule/MITRE 段 |
| 4 | recall_host_scope | 用 FIM 段，过滤 path 含 authorized_keys |
| 5 | recall_host_scope 或 recall_by_uid | 时间 + host/uid 双条件 |
| 6 | recall_host_scope | 用 audit 段，按 command 匹配侦察命令 |
| 7 | recall_by_rule_id | - |
| 8 | recall_host_scope | 时间 + uid，用 audit+FIM 段 |
| 9 | recall_host_scope | 用 audit 段，按 command 匹配凭据工具 |
| 10 | recall_host_scope | 时间 + 网络+审计，匹配 SSH 失败 |
| 11 | recall_host_scope | 用 audit+file 段，匹配 DB 相关路径 |
| 12 | recall_by_src_ip | 时间，统计连接数、端口 |
| 13 | recall_by_src_ip | 用户列表、首次连接时间 |
| 14 | recall_by_src_ip | 时间，频率/时段 |
| 15 | recall_by_src_ip | 目标用户列表 |
| 16 | recall_by_src_ip | 时间，源端口列表 |
| 17 | recall_by_file_hash | 路径、event_type |
| 18 | recall_by_file_hash | 首次/最近时间 |
| 19 | recall_by_file_hash | perm 变更 |
| 20 | recall_by_file_hash | md5_before 也传入 |
| 21 | recall_by_file_hash | event_type 统计 |
| 22 | recall_by_uid | 时间，command+timestamp |
| 23 | recall_by_uid | 时间，file_name 等 |
| 24 | recall_by_uid | 时间，pid/exe 统计 |
| 25 | recall_by_uid | 时间，command/euid |
| 26 | recall_by_src_user | 时间，连接数、目标分布 |

---

## 4. Target 示例从哪里来（示例挖掘）

目标：为每个占位符类型得到「可填进模板」的若干实例，用于生成 26 题的实例化题目。

### 4.1 挖掘逻辑（可写成独立脚本或函数）

以下 SQL 均针对 `linux_apt_2024_04_06_january.duckdb`，`N` 可取 20～50。

- **host_id**  
  - `SELECT host_id FROM host_assets` 或  
  - `SELECT host_id FROM audit_events WHERE host_id IS NOT NULL GROUP BY host_id ORDER BY COUNT(*) DESC LIMIT N`
- **uid**  
  - `SELECT DISTINCT uid FROM audit_events WHERE uid IS NOT NULL ORDER BY uid LIMIT N`
- **src_ip**  
  - `SELECT src_ip FROM network_activities WHERE src_ip IS NOT NULL AND TRIM(src_ip) != '' GROUP BY src_ip ORDER BY COUNT(*) DESC LIMIT N`
- **md5_after**  
  - `SELECT md5_after FROM file_integrity_events WHERE md5_after IS NOT NULL AND TRIM(md5_after) != '' GROUP BY md5_after ORDER BY COUNT(*) DESC LIMIT N`
- **md5_before**  
  - `SELECT md5_before, md5_after FROM file_integrity_events WHERE md5_before IS NOT NULL AND md5_after IS NOT NULL AND TRIM(md5_before) != '' LIMIT N`（成对抽样供题 20）
- **rule_id**  
  - `SELECT rule_id FROM security_alerts WHERE rule_id IS NOT NULL GROUP BY rule_id ORDER BY COUNT(*) DESC LIMIT N`
- **src_user**  
  - `SELECT src_user FROM network_activities WHERE src_user IS NOT NULL AND TRIM(src_user) != '' GROUP BY src_user ORDER BY COUNT(*) DESC LIMIT N`
- **alert_level**  
  - `SELECT DISTINCT alert_level FROM security_alerts WHERE alert_level IS NOT NULL ORDER BY alert_level DESC`
- **start_time / end_time**  
  - `SELECT MIN(timestamp) AS min_ts, MAX(timestamp) AS max_ts FROM audit_events WHERE timestamp IS NOT NULL`，再在应用层生成如「最近 24h」「最近 7 天」的区间示例。

输出形态：可写入 `question_instance_seeds.json`（或同类配置），结构例如：

```json
{
  "host_id": ["000", "003", "004"],
  "uid": [0, 1000, 128],
  "src_ip": ["192.168.217.1", "..."],
  "md5_after": ["4aeccea27dd316d2b5991bd161a8d764", "..."],
  "rule_id": ["502", "503", "510"],
  "src_user": ["root", "sohaib"],
  "alert_level": [5, 6, 7],
  "time_ranges": [["2024-01-04T00:00:00", "2024-01-06T23:59:59"]]
}
```

用于在「实例化」阶段替换模板中的 `<host_id>`、`<uid>` 等。

---

## 5. 召回函数返回结构（统一 JSON 摘要）

各函数均返回「任务级摘要」而非逐行原始日志，便于多题复用。建议统一包一层：

```json
{
  "retrieval_task": "recall_host_scope | recall_by_src_ip | ...",
  "params": { "host_id": "004", "start_time": "...", "end_time": "..." },
  "summary": {
    "audit_events": { "count": N, "samples": [...], "by_uid": {...}, "by_command_type": "..." },
    "network_activities": { "count": N, "samples": [...], "by_src_ip": {...}, "port_distribution": [...] },
    "security_alerts": { "count": N, "samples": [...], "by_rule_id": {...}, "by_level": [...] },
    "file_integrity_events": { "count": N, "samples": [...], "by_path_pattern": "...", "first_last_ts": {...} }
  },
  "coverage_question_ids": [1, 2, 3, 4, 5, 6, 8, 9, 10, 11]
}
```

- 仅与本实体相关的表/字段出现在 `summary` 下；若某表对本实体无数据，可省略或 `"count": 0`。
- `coverage_question_ids` 表示该摘要可支撑的问题 ID，便于链路上选择「用哪次召回结果」答哪一题。

---

## 6. 实现层次建议

```
┌─────────────────────────────────────────────────────────────────┐
│  Instance Generator（实例化）                                     │
│  - 读 questions_templates_v3.json + question_instance_seeds.json   │
│  - 替换 <host_id>, <uid>, <start_time>, <end_time> 等 → 实例题目   │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│  Retriever（召回）                                                │
│  - 从实例题目/结构化 query 中解析 (entity_type, entity_id, [t_start,t_end]) │
│  - 根据 entity_type 调对应 recall_*(entity_id, t_start, t_end)   │
│  - 返回统一 JSON 摘要                                              │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│  Query Layer（模版化 SQL）                                        │
│  - recall_host_scope(host_id, start, end) → SQL 模版 + 参数绑定   │
│  - recall_by_src_ip(src_ip, start, end) → …                      │
│  - recall_by_file_hash(md5_after, md5_before, start, end) → …    │
│  - recall_by_uid(uid, start, end) → …                            │
│  - recall_by_src_user(src_user, start, end) → …                 │
│  - recall_by_rule_id(rule_id, start, end) → …                   │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│  DuckDB (linux_apt_2024_04_06_january.duckdb)                    │
└─────────────────────────────────────────────────────────────────┘
```

- **Query Layer**：实现 6 个模版化查询函数，内部用参数化 SQL（或 ORM/建造器）访问 DuckDB，返回已拼好的 `summary` 子结构。
- **Retriever**：只做「解析 → 选函数 → 调 Query Layer → 包成统一 JSON」。
- **Instance Generator**：负责「模板 + 种子 → 实例题目」和（若需要）把实例题标上对应的 `coverage_question_ids`，便于检索到摘要后知道能答哪些题。

---

## 7. 查询函数与 SQL 模版规格（实现级）

### 7.1 约定

- 所有时间参数若为 `None` 或未传，表示不按时间过滤；否则用 `timestamp BETWEEN :start_time AND :end_time`。
- 返回的 `samples` 行数由调用方或配置指定上限（如 100），避免单次返回过大。

### 7.2 recall_host_scope(host_id, start_time=None, end_time=None)

**作用**：某主机在可选时间内的多表摘要，供 1,2,3,4,5,6,8,9,10,11 等题共用。

**SQL 模版要点**（可分多条执行后拼成 `summary`）：

- 审计：  
  `SELECT event_id, timestamp, pid, ppid, exe, command, uid, file_name, success, cwd, session, tty FROM audit_events WHERE host_id = :host_id [AND timestamp BETWEEN :start AND :end] [LIMIT K]`
- 告警：  
  `SELECT a.alert_id, a.timestamp, a.rule_id, a.alert_level, a.description, r.mitre_technique, r.mitre_tactic FROM security_alerts a LEFT JOIN security_rules r ON a.rule_id = r.rule_id WHERE a.host_id = :host_id [AND a.timestamp BETWEEN :start AND :end] [LIMIT K]`
- 网络：  
  `SELECT activity_id, timestamp, src_ip, src_port, src_user, dst_user FROM network_activities WHERE host_id = :host_id [AND timestamp BETWEEN :start AND :end] [LIMIT K]`
- FIM：  
  `SELECT fim_id, timestamp, file_path, event_type, md5_before, md5_after, perm_after, uid_after, uname_after, size_before, size_after FROM file_integrity_events WHERE host_id = :host_id [AND timestamp BETWEEN :start AND :end] [LIMIT K]`

**返回**：`summary.audit_events / security_alerts / network_activities / file_integrity_events` 各含 `count` 与 `samples`；可按需增加聚合（如 `by_uid`、`by_rule_id`）以利多题复用。

### 7.3 recall_by_src_ip(src_ip, start_time=None, end_time=None)

**作用**：某源 IP 的网络活动摘要，供 12,13,14,15,16 使用。

**SQL 模版要点**：

- 明细：  
  `SELECT activity_id, timestamp, host_id, src_ip, src_port, src_user, dst_user FROM network_activities WHERE src_ip = :src_ip [AND timestamp BETWEEN :start AND :end] [LIMIT K]`
- 聚合（在应用层或一条 SQL）：按 `src_port` 计数、按 `dst_user` 计数、总连接数、时间范围。

**返回**：`summary.network_activities` 含 `count`、`samples`、`port_distribution`、`dst_user_distribution`、`time_range`。

### 7.4 recall_by_file_hash(md5_after, md5_before=None, start_time=None, end_time=None)

**作用**：以 md5 为键的 FIM 摘要，供 17,18,19,20,21 使用。

**SQL 模版要点**：

- 按 md5_after：  
  `SELECT fim_id, timestamp, host_id, file_path, event_type, md5_before, md5_after, perm_after, size_before, size_after FROM file_integrity_events WHERE md5_after = :md5_after [AND timestamp BETWEEN :start AND :end] [LIMIT K]`
- 若提供 md5_before（如题 20）：  
  `WHERE md5_before = :md5_before AND md5_after = :md5_after [AND timestamp BETWEEN :start AND :end]`

**返回**：`summary.file_integrity_events` 含 `count`、`samples`、`paths`、`event_type_counts`、`first_seen`、`last_seen`、`perm_changes`（可从 samples 中推导）。

### 7.5 recall_by_uid(uid, start_time=None, end_time=None)

**作用**：某用户的审计摘要，供 22,23,24,25 使用；5,8 在 host 召回基础上可按 uid 再滤。

**SQL 模版要点**：

- `SELECT event_id, timestamp, host_id, pid, ppid, exe, command, uid, euid, file_name, success, cwd FROM audit_events WHERE uid = :uid [AND timestamp BETWEEN :start AND :end] [LIMIT K]`

**返回**：`summary.audit_events` 含 `count`、`samples`、`commands`、`file_names`、`hosts`、可含 `euid_changes`（euid 从非 0 变为 0 等）以支撑权限提升类题。

### 7.6 recall_by_src_user(src_user, start_time=None, end_time=None)

**作用**：某源用户的网络摘要，供 26 使用。

**SQL 模版要点**：

- `SELECT activity_id, timestamp, host_id, src_ip, src_port, src_user, dst_user FROM network_activities WHERE src_user = :src_user [AND timestamp BETWEEN :start AND :end] [LIMIT K]`

**返回**：`summary.network_activities` 含 `count`、`samples`、`dst_user_distribution`、`src_ip_distribution`。

### 7.7 recall_by_rule_id(rule_id, start_time=None, end_time=None)

**作用**：某规则在多主机上的触发情况，供 7 使用。

**SQL 模版要点**：

- `SELECT a.alert_id, a.timestamp, a.host_id, a.rule_id, a.alert_level, a.description FROM security_alerts a WHERE a.rule_id = :rule_id [AND a.timestamp BETWEEN :start AND :end] [LIMIT K]`
- 聚合：按 `host_id` 分组计数、时间分布。

**返回**：`summary.security_alerts` 含 `count`、`samples`、`by_host_id`、`time_range`。

### 7.8 问题 → 召回函数映射配置（推荐落地为 JSON）

便于在代码中「根据问题 ID 或模板元数据选择召回函数 + 参数来源」；全部 26 题示例：

```json
{
  "question_id_to_retrieval": {
    "1":  { "func": "recall_host_scope",   "entity_from": ["host_id"],           "time_from": null },
    "2":  { "func": "recall_host_scope",   "entity_from": ["host_id"],           "time_from": null },
    "3":  { "func": "recall_host_scope",   "entity_from": ["host_id","alert_level"], "time_from": null },
    "4":  { "func": "recall_host_scope",   "entity_from": ["host_id"],           "time_from": null },
    "5":  { "func": "recall_host_scope",   "entity_from": ["host_id","uid"],     "time_from": ["start_time","end_time"] },
    "6":  { "func": "recall_host_scope",   "entity_from": ["host_id"],           "time_from": null },
    "7":  { "func": "recall_by_rule_id",   "entity_from": ["rule_id"],           "time_from": ["start_time","end_time"] },
    "8":  { "func": "recall_host_scope",   "entity_from": ["host_id","uid"],     "time_from": ["start_time","end_time"] },
    "9":  { "func": "recall_host_scope",   "entity_from": ["host_id"],           "time_from": null },
    "10": { "func": "recall_host_scope",   "entity_from": ["host_id"],           "time_from": ["start_time","end_time"] },
    "11": { "func": "recall_host_scope",   "entity_from": ["host_id"],           "time_from": null },
    "12": { "func": "recall_by_src_ip",    "entity_from": ["src_ip"],            "time_from": ["start_time","end_time"] },
    "13": { "func": "recall_by_src_ip",    "entity_from": ["src_ip"],            "time_from": null },
    "14": { "func": "recall_by_src_ip",    "entity_from": ["src_ip"],            "time_from": ["start_time","end_time"] },
    "15": { "func": "recall_by_src_ip",    "entity_from": ["src_ip"],            "time_from": null },
    "16": { "func": "recall_by_src_ip",    "entity_from": ["src_ip"],            "time_from": ["start_time","end_time"] },
    "17": { "func": "recall_by_file_hash", "entity_from": ["md5_after"],          "time_from": null },
    "18": { "func": "recall_by_file_hash", "entity_from": ["md5_after"],          "time_from": null },
    "19": { "func": "recall_by_file_hash", "entity_from": ["md5_after"],          "time_from": null },
    "20": { "func": "recall_by_file_hash", "entity_from": ["md5_before","md5_after"], "time_from": null },
    "21": { "func": "recall_by_file_hash", "entity_from": ["md5_after"],          "time_from": null },
    "22": { "func": "recall_by_uid",       "entity_from": ["uid"],               "time_from": ["start_time","end_time"] },
    "23": { "func": "recall_by_uid",       "entity_from": ["uid"],               "time_from": ["start_time","end_time"] },
    "24": { "func": "recall_by_uid",       "entity_from": ["uid"],               "time_from": ["start_time","end_time"] },
    "25": { "func": "recall_by_uid",       "entity_from": ["uid"],               "time_from": ["start_time","end_time"] },
    "26": { "func": "recall_by_src_user",  "entity_from": ["src_user"],          "time_from": ["start_time","end_time"] }
  }
}
```

若某题需要两个实体（如 host + uid），用 `recall_host_scope(host_id, start, end)` 得到摘要后，在应用层按 `uid` 过滤即可，无需新增组合召回函数。

---

## 8. 小结

- **Target 示例**：用聚合/去重 SQL 从各表中得到 host_id、uid、src_ip、md5_after、rule_id、src_user、alert_level、时间区间等列表，写入种子文件，再用于实例化 26 个模板。
- **召回与问题**：用 6 个「按实体 + 可选时间」的召回函数覆盖 26 题；一函数对应多题，返回的是「实体相关摘要」JSON，而不是每题一条 SQL。
- **模版化**：每个召回函数对应固定 SQL 模版（含可选时间过滤），通过参数绑定生成可执行语句，保证安全、可复用且易扩展（新题优先映射到已有召回类型，必要时再增加新召回类型）。
