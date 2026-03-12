# Linux-APT-2024 数据库构建说明

## 概述

本目录包含将原始CSV文件转换为DuckDB数据库的完整流程。数据库只包含有9206条记录的表及其依赖的主表，包含外键约束。

## 文件说明

- `Linux-APT-2024-04-06-January.csv` - 原始CSV数据文件
- `split_csv_to_tables.py` - 将原始CSV拆分为多个表CSV文件（一个表一个CSV）
- `build_database.py` - 从拆分后的CSV文件构建DuckDB数据库
- `test_database.py` - 数据库测试和统计脚本（结果会保存到logs/目录）
- `scheme.md` - 数据库schema文档（包含表列信息、描述、字段解释、字段样例、外键关系）
- `tables_csv/` - 拆分后的表CSV文件目录
- `logs/` - 测试日志目录

## 构建流程

### 步骤1: 拆分CSV为多个表文件

```bash
python split_csv_to_tables.py
```

这会生成以下CSV文件到 `tables_csv/` 目录：
- `host_assets.csv` (3条记录)
- `audit_events.csv` (9,206条记录)
- `process_executions.csv` (9,206条记录)
- `file_integrity_events.csv` (9,206条记录)
- `network_activities.csv` (9,206条记录)
- `security_rules.csv` (39条记录)
- `security_alerts.csv` (9,206条记录)

### 步骤2: 构建数据库

```bash
python build_database.py
```

这会：
1. 从 `tables_csv/` 目录读取CSV文件
2. 创建DuckDB数据库 `linux_apt_2024_04_06_january.duckdb`
3. 建立外键约束
4. 生成 `scheme.md` 文档

### 步骤3: 测试数据库

```bash
python test_database.py
```

这会运行各种统计查询，结果会同时输出到控制台和保存到 `logs/test_database_YYYYMMDD_HHMMSS.log`

## 数据库表结构

### 主表（无外键依赖）
- **host_assets** - 主机资产信息（3条记录）
- **security_rules** - 安全规则信息（39条记录）

### 核心表（9206条记录）
- **audit_events** - 审计事件日志（主表，被其他表引用）
- **process_executions** - 进程执行记录
- **file_integrity_events** - 文件完整性监控记录
- **network_activities** - 网络活动记录
- **security_alerts** - 安全告警记录

## 外键关系

- `audit_events.host_id` → `host_assets.host_id`
- `process_executions.event_id` → `audit_events.event_id`
- `process_executions.host_id` → `host_assets.host_id`
- `file_integrity_events.event_id` → `audit_events.event_id`
- `file_integrity_events.host_id` → `host_assets.host_id`
- `network_activities.event_id` → `audit_events.event_id`
- `network_activities.host_id` → `host_assets.host_id`
- `security_alerts.event_id` → `audit_events.event_id`
- `security_alerts.host_id` → `host_assets.host_id`
- `security_alerts.rule_id` → `security_rules.rule_id`

## 输出文件

- `linux_apt_2024_04_06_january.duckdb` - DuckDB数据库文件
- `scheme.md` - 完整的数据库schema文档（包含表列信息、描述、字段解释、字段样例、外键关系）
- `tables_csv/*.csv` - 拆分后的表CSV文件
- `logs/test_database_*.log` - 测试日志文件

## 注意事项

1. 必须先运行 `split_csv_to_tables.py` 生成表CSV文件，再运行 `build_database.py`
2. 数据库只包含有9206条记录的表及其依赖的主表
3. 所有外键约束已在数据库层面建立
4. 测试脚本会自动创建日志文件，每次运行都会生成新的日志（带时间戳）
