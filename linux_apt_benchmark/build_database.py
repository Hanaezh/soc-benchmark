"""
Build DuckDB database from split CSV files (one CSV per table).

只保留有9206条记录的表及其依赖的主表：
- host_assets (主表，被引用)
- audit_events (9206条，主表)
- process_executions (9206条)
- file_integrity_events (9206条)
- network_activities (9206条)
- security_rules (主表，被引用)
- security_alerts (9206条)

包含外键约束。

Outputs:
- linux_apt_2024_04_06_january.duckdb
- scheme.md

Usage:
  1. 先运行: python split_csv_to_tables.py (拆分CSV)
  2. 再运行: python build_database.py (构建数据库)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import duckdb


DATA_DIR = Path(__file__).resolve().parent
TABLES_CSV_DIR = DATA_DIR / "tables_csv"
DB_PATH = DATA_DIR / "linux_apt_2024_04_06_january.duckdb"
SCHEME_MD_PATH = DATA_DIR / "scheme.md"


@dataclass(frozen=True)
class TableDoc:
    name: str
    description: str
    column_descriptions: dict[str, str]


TABLE_DOCS: dict[str, TableDoc] = {
    "host_assets": TableDoc(
        name="host_assets",
        description="存储被监控的主机信息（从 Wazuh agent / predecoder 字段聚合得到）。",
        column_descriptions={
            "host_id": "主机唯一标识（优先使用 agent_id，其次 hostname）。",
            "agent_ip": "主机 IP（agent.ip）。",
            "agent_name": "Agent 名称（agent.name）。",
            "agent_id": "Wazuh agent id（agent.id）。",
            "hostname": "主机名（predecoder.hostname）。",
            "manager_name": "Wazuh manager name（manager.name）。",
            "first_seen": "该主机在日志中首次出现的时间。",
            "last_seen": "该主机在日志中最后出现的时间。",
        },
    ),
    "audit_events": TableDoc(
        name="audit_events",
        description="核心审计事件日志（从 auditd/audit 相关字段抽取）。",
        column_descriptions={
            "event_id": "事件唯一标识（使用 CSV 中 _id）。",
            "timestamp": "事件时间戳（优先使用 _source.timestamp 秒级 epoch，其次 _source.@timestamp）。",
            "host_id": "关联主机（host_assets.host_id）。",
            "syscall": "系统调用号/名称（data.audit.syscall）。",
            "audit_type": "审计事件类型（data.audit.type，如 SYSCALL）。",
            "audit_id": "审计 ID（data.audit.id）。",
            "audit_key": "audit key（data.audit.key）。",
            "success": "是否成功（data.audit.success）。",
            "pid": "进程 ID（data.audit.pid）。",
            "ppid": "父进程 ID（data.audit.ppid）。",
            "exe": "可执行文件路径（data.audit.exe）。",
            "command": "命令/进程名（data.audit.command）。",
            "cwd": "当前工作目录（data.audit.cwd）。",
            "exit_code": "退出码（data.audit.exit）。",
            "uid": "用户 ID（data.audit.uid）。",
            "gid": "组 ID（data.audit.gid）。",
            "auid": "审计用户 ID（data.audit.auid）。",
            "euid": "有效用户 ID（data.audit.euid）。",
            "suid": "saved uid（data.audit.suid）。",
            "egid": "有效组 ID（data.audit.egid）。",
            "fsgid": "fs gid（data.audit.fsgid）。",
            "fsuid": "fs uid（data.audit.fsuid）。",
            "sgid": "saved gid（data.audit.sgid）。",
            "session": "会话 ID（data.audit.session）。",
            "tty": "终端（data.audit.tty）。",
            "arch": "架构（data.audit.arch）。",
            "file_inode": "文件 inode（data.audit.file.inode）。",
            "file_mode": "文件权限/模式（data.audit.file.mode）。",
            "file_name": "文件名（data.audit.file.name）。",
            "audit_res": "审计结果（data.audit.res）。",
            "location": "日志位置（location）。",
            "input_type": "输入类型（input.type）。",
        },
    ),
    "process_executions": TableDoc(
        name="process_executions",
        description="进程执行记录（从 audit.execve a0-a7 等字段抽取）。",
        column_descriptions={
            "execution_id": "执行记录唯一标识（exec_<event_id>）。",
            "event_id": "关联 audit_events.event_id。",
            "timestamp": "事件时间戳。",
            "host_id": "关联主机。",
            "arg0": "execve 参数 a0（data.audit.execve.a0）。",
            "arg1": "execve 参数 a1（data.audit.execve.a1）。",
            "arg2": "execve 参数 a2（data.audit.execve.a2）。",
            "arg3": "execve 参数 a3（data.audit.execve.a3）。",
            "arg4": "execve 参数 a4（data.audit.execve.a4）。",
            "arg5": "execve 参数 a5（data.audit.execve.a5）。",
            "arg6": "execve 参数 a6（data.audit.execve.a6）。",
            "arg7": "execve 参数 a7（data.audit.execve.a7）。",
        },
    ),
    "file_integrity_events": TableDoc(
        name="file_integrity_events",
        description="文件完整性监控记录（从 syscheck 字段抽取）。",
        column_descriptions={
            "fim_id": "文件完整性监控记录唯一标识（fim_<event_id>）。",
            "event_id": "关联 audit_events.event_id。",
            "timestamp": "事件时间戳。",
            "host_id": "关联主机。",
            "file_path": "文件路径（syscheck.path）。",
            "event_type": "事件类型（syscheck.event）。",
            "mode": "文件模式（syscheck.mode）。",
            "changed_attributes": "变更属性列表（syscheck.changed_attributes）。",
            "md5_before": "变更前 md5（syscheck.md5_before）。",
            "md5_after": "变更后 md5（syscheck.md5_after）。",
            "sha1_before": "变更前 sha1（syscheck.sha1_before）。",
            "sha1_after": "变更后 sha1（syscheck.sha1_after）。",
            "sha256_before": "变更前 sha256（syscheck.sha256_before）。",
            "sha256_after": "变更后 sha256（syscheck.sha256_after）。",
            "size_before": "变更前大小（syscheck.size_before）。",
            "size_after": "变更后大小（syscheck.size_after）。",
            "mtime_before": "变更前修改时间（syscheck.mtime_before）。",
            "mtime_after": "变更后修改时间（syscheck.mtime_after）。",
            "inode_before": "变更前 inode（syscheck.inode_before）。",
            "inode_after": "变更后 inode（syscheck.inode_after）。",
            "perm_after": "变更后权限（syscheck.perm_after）。",
            "uid_after": "变更后用户 ID（syscheck.uid_after）。",
            "gid_after": "变更后组 ID（syscheck.gid_after）。",
            "uname_after": "变更后用户名（syscheck.uname_after）。",
            "gname_after": "变更后组名（syscheck.gname_after）。",
        },
    ),
    "network_activities": TableDoc(
        name="network_activities",
        description="网络活动记录（从 data.srcip/srcport/srcuser/dstuser 字段抽取）。",
        column_descriptions={
            "activity_id": "网络活动记录唯一标识（net_<event_id>）。",
            "event_id": "关联 audit_events.event_id。",
            "timestamp": "事件时间戳。",
            "host_id": "关联主机。",
            "src_ip": "源 IP（data.srcip）。",
            "src_port": "源端口（data.srcport）。",
            "src_user": "源用户（data.srcuser）。",
            "dst_user": "目的用户（data.dstuser）。",
        },
    ),
    "security_rules": TableDoc(
        name="security_rules",
        description="检测规则信息（从 rule.* 与 decoder.* 字段去重抽取）。",
        column_descriptions={
            "rule_id": "规则 ID（rule.id）。",
            "rule_level": "规则等级（rule.level）。",
            "description": "规则描述（rule.description）。",
            "groups": "规则组（rule.groups）。",
            "mail": "邮件通知（rule.mail）。",
            "mitre_technique": "MITRE technique（rule.mitre.technique）。",
            "mitre_id": "MITRE technique id（rule.mitre.id）。",
            "mitre_tactic": "MITRE tactic（rule.mitre.tactic）。",
            "gdpr": "GDPR 合规（rule.gdpr）。",
            "pci_dss": "PCI DSS 合规（rule.pci_dss）。",
            "hipaa": "HIPAA 合规（rule.hipaa）。",
            "tsc": "TSC 合规（rule.tsc）。",
            "nist_800_53": "NIST 800-53 合规（rule.nist_800_53）。",
            "gpg13": "GPG13 合规（rule.gpg13）。",
            "decoder_parent": "decoder parent（decoder.parent）。",
            "decoder_name": "decoder name（decoder.name）。",
        },
    ),
    "security_alerts": TableDoc(
        name="security_alerts",
        description="基于规则触发的告警（本 CSV 每行可视作一条告警/事件）。",
        column_descriptions={
            "alert_id": "告警 ID（alert_<event_id>）。",
            "event_id": "关联事件（audit_events.event_id）。",
            "timestamp": "告警时间戳。",
            "host_id": "关联主机。",
            "rule_id": "规则 ID（security_rules.rule_id）。",
            "alert_level": "告警等级（rule.level）。",
            "description": "告警描述（rule.description）。",
            "fired_times": "触发次数（rule.firedtimes）。",
            "full_log": "原始完整日志（full_log）。",
            "previous_output": "previous_output。",
            "previous_log": "previous_log。",
            "data_file": "数据文件字段（data.file）。",
            "data_title": "数据标题（data.title）。",
            "data_tty": "数据终端（data.tty）。",
            "data_pwd": "数据工作目录（data.pwd）。",
            "data_command": "数据命令（data.command）。",
            "data_uid": "数据用户 ID（data.uid）。",
            "extra_data": "额外数据（data.extra_data）。",
        },
    ),
}


def _qi(name: str) -> str:
    """Quote an identifier value (table/column) safely."""
    return '"' + name.replace('"', '""') + '"'


def build_db() -> None:
    """从拆分后的CSV文件构建数据库，包含外键约束"""
    if not TABLES_CSV_DIR.exists():
        raise FileNotFoundError(
            f"Tables CSV directory not found: {TABLES_CSV_DIR}\n"
            f"Please run split_csv_to_tables.py first to generate CSV files."
        )

    if DB_PATH.exists():
        DB_PATH.unlink()

    con = duckdb.connect(str(DB_PATH))
    con.execute("PRAGMA threads=4;")

    # 创建表结构（带外键约束）
    print("创建表结构...")
    
    # 1. host_assets (主表，无外键)
    con.execute(
        """
        CREATE TABLE host_assets (
            host_id VARCHAR PRIMARY KEY,
            agent_ip VARCHAR,
            agent_name VARCHAR,
            agent_id VARCHAR,
            hostname VARCHAR,
            manager_name VARCHAR,
            first_seen TIMESTAMP,
            last_seen TIMESTAMP
        );
        """
    )

    # 2. audit_events (主表，引用 host_assets)
    con.execute(
        """
        CREATE TABLE audit_events (
            event_id VARCHAR PRIMARY KEY,
            timestamp TIMESTAMP,
            host_id VARCHAR,
            syscall VARCHAR,
            audit_type VARCHAR,
            audit_id VARCHAR,
            audit_key VARCHAR,
            success VARCHAR,
            pid INTEGER,
            ppid INTEGER,
            exe VARCHAR,
            command TEXT,
            cwd VARCHAR,
            exit_code VARCHAR,
            uid INTEGER,
            gid INTEGER,
            auid INTEGER,
            euid INTEGER,
            suid INTEGER,
            egid INTEGER,
            fsgid INTEGER,
            fsuid INTEGER,
            sgid INTEGER,
            session INTEGER,
            tty VARCHAR,
            arch VARCHAR,
            file_inode BIGINT,
            file_mode VARCHAR,
            file_name VARCHAR,
            audit_res VARCHAR,
            location VARCHAR,
            input_type VARCHAR,
            FOREIGN KEY (host_id) REFERENCES host_assets(host_id)
        );
        """
    )

    # 3. security_rules (主表，无外键)
    con.execute(
        """
        CREATE TABLE security_rules (
            rule_id VARCHAR PRIMARY KEY,
            rule_level INTEGER,
            description TEXT,
            groups TEXT,
            mail VARCHAR,
            mitre_technique TEXT,
            mitre_id TEXT,
            mitre_tactic TEXT,
            gdpr TEXT,
            pci_dss TEXT,
            hipaa TEXT,
            tsc TEXT,
            nist_800_53 TEXT,
            gpg13 TEXT,
            decoder_parent VARCHAR,
            decoder_name VARCHAR
        );
        """
    )

    # 4. process_executions (引用 audit_events 和 host_assets)
    con.execute(
        """
        CREATE TABLE process_executions (
            execution_id VARCHAR PRIMARY KEY,
            event_id VARCHAR,
            timestamp TIMESTAMP,
            host_id VARCHAR,
            arg0 TEXT,
            arg1 TEXT,
            arg2 TEXT,
            arg3 TEXT,
            arg4 TEXT,
            arg5 TEXT,
            arg6 TEXT,
            arg7 TEXT,
            FOREIGN KEY (event_id) REFERENCES audit_events(event_id),
            FOREIGN KEY (host_id) REFERENCES host_assets(host_id)
        );
        """
    )

    # 5. file_integrity_events (引用 audit_events 和 host_assets)
    con.execute(
        """
        CREATE TABLE file_integrity_events (
            fim_id VARCHAR PRIMARY KEY,
            event_id VARCHAR,
            timestamp TIMESTAMP,
            host_id VARCHAR,
            file_path VARCHAR,
            event_type VARCHAR,
            mode VARCHAR,
            changed_attributes TEXT,
            md5_before VARCHAR,
            md5_after VARCHAR,
            sha1_before VARCHAR,
            sha1_after VARCHAR,
            sha256_before VARCHAR,
            sha256_after VARCHAR,
            size_before BIGINT,
            size_after BIGINT,
            mtime_before TIMESTAMP,
            mtime_after TIMESTAMP,
            inode_before BIGINT,
            inode_after BIGINT,
            perm_after VARCHAR,
            uid_after INTEGER,
            gid_after INTEGER,
            uname_after VARCHAR,
            gname_after VARCHAR,
            FOREIGN KEY (event_id) REFERENCES audit_events(event_id),
            FOREIGN KEY (host_id) REFERENCES host_assets(host_id)
        );
        """
    )

    # 6. network_activities (引用 audit_events 和 host_assets)
    con.execute(
        """
        CREATE TABLE network_activities (
            activity_id VARCHAR PRIMARY KEY,
            event_id VARCHAR,
            timestamp TIMESTAMP,
            host_id VARCHAR,
            src_ip VARCHAR,
            src_port INTEGER,
            src_user VARCHAR,
            dst_user VARCHAR,
            FOREIGN KEY (event_id) REFERENCES audit_events(event_id),
            FOREIGN KEY (host_id) REFERENCES host_assets(host_id)
        );
        """
    )

    # 7. security_alerts (引用 audit_events, host_assets, security_rules)
    con.execute(
        """
        CREATE TABLE security_alerts (
            alert_id VARCHAR PRIMARY KEY,
            event_id VARCHAR,
            timestamp TIMESTAMP,
            host_id VARCHAR,
            rule_id VARCHAR,
            alert_level INTEGER,
            description TEXT,
            fired_times INTEGER,
            full_log TEXT,
            previous_output TEXT,
            previous_log TEXT,
            data_file VARCHAR,
            data_title TEXT,
            data_tty VARCHAR,
            data_pwd VARCHAR,
            data_command TEXT,
            data_uid INTEGER,
            extra_data TEXT,
            FOREIGN KEY (event_id) REFERENCES audit_events(event_id),
            FOREIGN KEY (host_id) REFERENCES host_assets(host_id),
            FOREIGN KEY (rule_id) REFERENCES security_rules(rule_id)
        );
        """
    )

    # 加载数据（按外键依赖顺序）
    print("加载数据...")
    
    # 1. 先加载主表（无外键依赖）
    csv_path = TABLES_CSV_DIR / "host_assets.csv"
    if csv_path.exists():
        print(f"  加载 host_assets...")
        con.execute(f"COPY host_assets FROM '{csv_path.as_posix()}' (HEADER, DELIMITER ',', AUTO_DETECT TRUE);")
        n = con.execute("SELECT COUNT(*) FROM host_assets").fetchone()[0]
        print(f"    ✓ {n:,} 条记录")

    csv_path = TABLES_CSV_DIR / "security_rules.csv"
    if csv_path.exists():
        print(f"  加载 security_rules...")
        con.execute(f"COPY security_rules FROM '{csv_path.as_posix()}' (HEADER, DELIMITER ',', AUTO_DETECT TRUE);")
        n = con.execute("SELECT COUNT(*) FROM security_rules").fetchone()[0]
        print(f"    ✓ {n:,} 条记录")

    # 2. 加载 audit_events（依赖 host_assets）
    csv_path = TABLES_CSV_DIR / "audit_events.csv"
    if csv_path.exists():
        print(f"  加载 audit_events...")
        con.execute(f"COPY audit_events FROM '{csv_path.as_posix()}' (HEADER, DELIMITER ',', AUTO_DETECT TRUE);")
        n = con.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0]
        print(f"    ✓ {n:,} 条记录")

    # 3. 加载依赖 audit_events 的表
    for table_name in ["process_executions", "file_integrity_events", "network_activities", "security_alerts"]:
        csv_path = TABLES_CSV_DIR / f"{table_name}.csv"
        if csv_path.exists():
            print(f"  加载 {table_name}...")
            con.execute(f"COPY {_qi(table_name)} FROM '{csv_path.as_posix()}' (HEADER, DELIMITER ',', AUTO_DETECT TRUE);")
            n = con.execute(f"SELECT COUNT(*) FROM {_qi(table_name)}").fetchone()[0]
            print(f"    ✓ {n:,} 条记录")

    con.execute("ANALYZE;")
    con.close()
    print("\n✓ 数据库构建完成")


def _fetch_table_info(con: duckdb.DuckDBPyConnection, table: str) -> list[dict[str, Any]]:
    rows = con.execute(f"PRAGMA table_info('{table}')").fetchall()
    return [
        {
            "name": r[1],
            "type": r[2],
            "notnull": bool(r[3]),
            "pk": bool(r[5]),
        }
        for r in rows
    ]


def _fetch_examples(con: duckdb.DuckDBPyConnection, table: str, col: str, limit: int = 5) -> list[str]:
    q = f"""
    SELECT CAST({_qi(col)} AS VARCHAR) AS v
    FROM {_qi(table)}
    WHERE {_qi(col)} IS NOT NULL AND CAST({_qi(col)} AS VARCHAR) <> ''
    GROUP BY 1
    ORDER BY length(v) ASC, v ASC
    LIMIT {limit}
    """
    try:
        vals = [r[0] for r in con.execute(q).fetchall()]
        return [v for v in vals if v is not None]
    except Exception:
        return []


# 外键关系定义（手动维护，因为DuckDB查询外键的方式较复杂）
FOREIGN_KEYS: dict[str, list[dict[str, str]]] = {
    "audit_events": [
        {"column": "host_id", "references_table": "host_assets", "references_column": "host_id"},
    ],
    "process_executions": [
        {"column": "event_id", "references_table": "audit_events", "references_column": "event_id"},
        {"column": "host_id", "references_table": "host_assets", "references_column": "host_id"},
    ],
    "file_integrity_events": [
        {"column": "event_id", "references_table": "audit_events", "references_column": "event_id"},
        {"column": "host_id", "references_table": "host_assets", "references_column": "host_id"},
    ],
    "network_activities": [
        {"column": "event_id", "references_table": "audit_events", "references_column": "event_id"},
        {"column": "host_id", "references_table": "host_assets", "references_column": "host_id"},
    ],
    "security_alerts": [
        {"column": "event_id", "references_table": "audit_events", "references_column": "event_id"},
        {"column": "host_id", "references_table": "host_assets", "references_column": "host_id"},
        {"column": "rule_id", "references_table": "security_rules", "references_column": "rule_id"},
    ],
}


def write_scheme_md() -> None:
    con = duckdb.connect(str(DB_PATH), read_only=True)

    parts: list[str] = []
    parts.append("# Linux-APT-2024 (04-06 January) 数据库 Scheme\n")
    parts.append(f"- DB: `{DB_PATH.name}` (DuckDB)\n")
    parts.append(f"- CSV 来源: `tables_csv/` 目录（每个表一个CSV文件）\n")
    parts.append(f"- 原始CSV: `Linux-APT-2024-04-06-January.csv`\n")
    parts.append("\n> 说明：该数据库只包含有9206条记录的表及其依赖的主表，包含外键约束。数据先拆分为多个CSV文件（一个表一个CSV），再加载到数据库。\n\n")

    tables = [
        "host_assets",
        "audit_events",
        "process_executions",
        "file_integrity_events",
        "network_activities",
        "security_rules",
        "security_alerts",
    ]

    for t in tables:
        doc = TABLE_DOCS.get(t)
        parts.append(f"## {t}\n")
        parts.append(f"{doc.description if doc else ''}\n\n")

        # 外键信息
        fks = FOREIGN_KEYS.get(t, [])
        if fks:
            parts.append("**外键关系：**\n")
            for fk in fks:
                parts.append(f"- `{fk['column']}` → `{fk['references_table']}.{fk['references_column']}`\n")
            parts.append("\n")

        info = _fetch_table_info(con, t)
        parts.append("| column | type | pk | notnull | description | examples |\n")
        parts.append("|---|---|---:|---:|---|---|\n")
        for c in info:
            name = c["name"]
            desc = (doc.column_descriptions.get(name) if doc else None) or ""
            ex = _fetch_examples(con, t, name, limit=5)
            ex_s = ", ".join([x.replace("\n", "\\n") for x in ex])
            parts.append(
                f"| `{name}` | `{c['type']}` | {1 if c['pk'] else 0} | {1 if c['notnull'] else 0} | {desc} | {ex_s} |\n"
            )
        parts.append("\n")

    con.close()
    SCHEME_MD_PATH.write_text("".join(parts), encoding="utf-8")


def main() -> None:
    build_db()
    write_scheme_md()
    print(f"OK: created DB: {DB_PATH}")
    print(f"OK: wrote scheme: {SCHEME_MD_PATH}")


if __name__ == "__main__":
    main()
