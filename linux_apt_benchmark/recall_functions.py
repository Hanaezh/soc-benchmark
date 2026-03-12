"""
实现6个召回函数，每个函数返回统一的JSON摘要
按实体召回多表数据，供多个问题共用
"""

import duckdb
import json
from typing import Optional, Dict, Any, List
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DB_PATH = "linux_apt_2024_04_06_january.duckdb"
SAMPLE_LIMIT = 100  # 每个表最多返回的样本数


def get_connection():
    """获取数据库连接"""
    return duckdb.connect(DB_PATH, read_only=True)


def recall_host_scope(host_id: str, start_time: Optional[str] = None, end_time: Optional[str] = None) -> Dict[str, Any]:
    """
    召回某主机的多表摘要
    支持问题: 1,2,3,4,5,6,8,9,10,11
    """
    conn = get_connection()
    summary = {}
    
    time_filter = ""
    if start_time and end_time:
        time_filter = f"AND timestamp BETWEEN '{start_time}' AND '{end_time}'"
    
    # 审计事件
    query = f"""
        SELECT event_id, timestamp, pid, ppid, exe, command, uid, file_name, success, cwd, session, tty
        FROM audit_events
        WHERE host_id = ?
        {time_filter}
        LIMIT {SAMPLE_LIMIT}
    """
    result = conn.execute(query, [host_id]).fetchall()
    summary['audit_events'] = {
        'count': len(result),
        'samples': [dict(zip(['event_id', 'timestamp', 'pid', 'ppid', 'exe', 'command', 'uid', 
                              'file_name', 'success', 'cwd', 'session', 'tty'], row)) for row in result]
    }
    
    # 告警
    query = f"""
        SELECT a.alert_id, a.timestamp, a.rule_id, a.alert_level, a.description, 
               r.mitre_technique, r.mitre_tactic
        FROM security_alerts a
        LEFT JOIN security_rules r ON a.rule_id = r.rule_id
        WHERE a.host_id = ?
        {time_filter}
        LIMIT {SAMPLE_LIMIT}
    """
    result = conn.execute(query, [host_id]).fetchall()
    summary['security_alerts'] = {
        'count': len(result),
        'samples': [dict(zip(['alert_id', 'timestamp', 'rule_id', 'alert_level', 'description',
                              'mitre_technique', 'mitre_tactic'], row)) for row in result]
    }
    
    # 网络活动
    query = f"""
        SELECT activity_id, timestamp, src_ip, src_port, src_user, dst_user
        FROM network_activities
        WHERE host_id = ?
        {time_filter}
        LIMIT {SAMPLE_LIMIT}
    """
    result = conn.execute(query, [host_id]).fetchall()
    summary['network_activities'] = {
        'count': len(result),
        'samples': [dict(zip(['activity_id', 'timestamp', 'src_ip', 'src_port', 
                              'src_user', 'dst_user'], row)) for row in result]
    }
    
    # 文件完整性事件
    query = f"""
        SELECT fim_id, timestamp, file_path, event_type, md5_before, md5_after, 
               perm_after, uid_after, uname_after, size_before, size_after
        FROM file_integrity_events
        WHERE host_id = ?
        {time_filter}
        LIMIT {SAMPLE_LIMIT}
    """
    result = conn.execute(query, [host_id]).fetchall()
    summary['file_integrity_events'] = {
        'count': len(result),
        'samples': [dict(zip(['fim_id', 'timestamp', 'file_path', 'event_type', 'md5_before', 'md5_after',
                              'perm_after', 'uid_after', 'uname_after', 'size_before', 'size_after'], row)) 
                    for row in result]
    }
    
    conn.close()
    
    return {
        'retrieval_task': 'recall_host_scope',
        'params': {'host_id': host_id, 'start_time': start_time, 'end_time': end_time},
        'summary': summary,
        'coverage_question_ids': [1, 2, 3, 4, 5, 6, 8, 9, 10, 11]
    }


def recall_by_src_ip(src_ip: str, start_time: Optional[str] = None, end_time: Optional[str] = None) -> Dict[str, Any]:
    """
    召回某源IP的网络活动摘要
    支持问题: 12,13,14,15,16
    """
    conn = get_connection()
    
    time_filter = ""
    if start_time and end_time:
        time_filter = f"AND timestamp BETWEEN '{start_time}' AND '{end_time}'"
    
    # 网络活动明细
    query = f"""
        SELECT activity_id, timestamp, host_id, src_ip, src_port, src_user, dst_user
        FROM network_activities
        WHERE src_ip = ?
        {time_filter}
        LIMIT {SAMPLE_LIMIT}
    """
    result = conn.execute(query, [src_ip]).fetchall()
    samples = [dict(zip(['activity_id', 'timestamp', 'host_id', 'src_ip', 'src_port', 
                         'src_user', 'dst_user'], row)) for row in result]
    
    # 端口分布
    query = f"""
        SELECT src_port, COUNT(*) as count
        FROM network_activities
        WHERE src_ip = ?
        {time_filter}
        GROUP BY src_port
        ORDER BY count DESC
    """
    result = conn.execute(query, [src_ip]).fetchall()
    port_distribution = [{'port': row[0], 'count': row[1]} for row in result]
    
    # 目标用户分布
    query = f"""
        SELECT dst_user, COUNT(*) as count
        FROM network_activities
        WHERE src_ip = ?
        {time_filter}
        GROUP BY dst_user
        ORDER BY count DESC
    """
    result = conn.execute(query, [src_ip]).fetchall()
    dst_user_distribution = [{'dst_user': row[0], 'count': row[1]} for row in result]
    
    conn.close()
    
    return {
        'retrieval_task': 'recall_by_src_ip',
        'params': {'src_ip': src_ip, 'start_time': start_time, 'end_time': end_time},
        'summary': {
            'network_activities': {
                'count': len(samples),
                'samples': samples,
                'port_distribution': port_distribution,
                'dst_user_distribution': dst_user_distribution
            }
        },
        'coverage_question_ids': [12, 13, 14, 15, 16]
    }


def recall_by_file_hash(md5_after: str, md5_before: Optional[str] = None, 
                       start_time: Optional[str] = None, end_time: Optional[str] = None) -> Dict[str, Any]:
    """
    召回某文件哈希的FIM摘要
    支持问题: 17,18,19,20,21
    """
    conn = get_connection()
    
    time_filter = ""
    if start_time and end_time:
        time_filter = f"AND timestamp BETWEEN '{start_time}' AND '{end_time}'"
    
    # 构建哈希过滤条件
    if md5_before:
        hash_filter = f"md5_before = '{md5_before}' AND md5_after = '{md5_after}'"
    else:
        hash_filter = f"md5_after = '{md5_after}'"
    
    # FIM事件明细
    query = f"""
        SELECT fim_id, timestamp, host_id, file_path, event_type, md5_before, md5_after,
               perm_after, size_before, size_after
        FROM file_integrity_events
        WHERE {hash_filter}
        {time_filter}
        LIMIT {SAMPLE_LIMIT}
    """
    result = conn.execute(query).fetchall()
    samples = [dict(zip(['fim_id', 'timestamp', 'host_id', 'file_path', 'event_type', 'md5_before',
                         'md5_after', 'perm_after', 'size_before', 'size_after'], row)) for row in result]
    
    # 事件类型统计
    query = f"""
        SELECT event_type, COUNT(*) as count
        FROM file_integrity_events
        WHERE {hash_filter}
        {time_filter}
        GROUP BY event_type
    """
    result = conn.execute(query).fetchall()
    event_type_counts = [{'event_type': row[0], 'count': row[1]} for row in result]
    
    # 首次和最近时间
    query = f"""
        SELECT MIN(timestamp) as first_seen, MAX(timestamp) as last_seen
        FROM file_integrity_events
        WHERE {hash_filter}
        {time_filter}
    """
    result = conn.execute(query).fetchone()
    first_seen = result[0] if result else None
    last_seen = result[1] if result else None
    
    # 路径列表
    paths = list(set([s['file_path'] for s in samples if s['file_path']]))
    
    conn.close()
    
    return {
        'retrieval_task': 'recall_by_file_hash',
        'params': {'md5_after': md5_after, 'md5_before': md5_before, 
                   'start_time': start_time, 'end_time': end_time},
        'summary': {
            'file_integrity_events': {
                'count': len(samples),
                'samples': samples,
                'paths': paths,
                'event_type_counts': event_type_counts,
                'first_seen': first_seen,
                'last_seen': last_seen
            }
        },
        'coverage_question_ids': [17, 18, 19, 20, 21]
    }


def recall_by_uid(uid: int, start_time: Optional[str] = None, end_time: Optional[str] = None) -> Dict[str, Any]:
    """
    召回某用户的审计摘要
    支持问题: 22,23,24,25 (以及5,8可联合使用)
    """
    conn = get_connection()
    
    time_filter = ""
    if start_time and end_time:
        time_filter = f"AND timestamp BETWEEN '{start_time}' AND '{end_time}'"
    
    # 审计事件明细
    query = f"""
        SELECT event_id, timestamp, host_id, pid, ppid, exe, command, uid, euid, 
               file_name, success, cwd
        FROM audit_events
        WHERE uid = ?
        {time_filter}
        LIMIT {SAMPLE_LIMIT}
    """
    result = conn.execute(query, [uid]).fetchall()
    samples = [dict(zip(['event_id', 'timestamp', 'host_id', 'pid', 'ppid', 'exe', 'command',
                         'uid', 'euid', 'file_name', 'success', 'cwd'], row)) for row in result]
    
    # 命令统计
    commands = list(set([s['command'] for s in samples if s['command']]))
    
    # 文件名列表
    file_names = list(set([s['file_name'] for s in samples if s['file_name']]))
    
    # 涉及主机
    hosts = list(set([s['host_id'] for s in samples if s['host_id']]))
    
    conn.close()
    
    return {
        'retrieval_task': 'recall_by_uid',
        'params': {'uid': uid, 'start_time': start_time, 'end_time': end_time},
        'summary': {
            'audit_events': {
                'count': len(samples),
                'samples': samples,
                'commands': commands[:50],  # 限制数量
                'file_names': file_names[:50],
                'hosts': hosts
            }
        },
        'coverage_question_ids': [22, 23, 24, 25, 5, 8]
    }


def recall_by_src_user(src_user: str, start_time: Optional[str] = None, end_time: Optional[str] = None) -> Dict[str, Any]:
    """
    召回某源用户的网络摘要
    支持问题: 26
    """
    conn = get_connection()
    
    time_filter = ""
    if start_time and end_time:
        time_filter = f"AND timestamp BETWEEN '{start_time}' AND '{end_time}'"
    
    # 网络活动明细
    query = f"""
        SELECT activity_id, timestamp, host_id, src_ip, src_port, src_user, dst_user
        FROM network_activities
        WHERE src_user = ?
        {time_filter}
        LIMIT {SAMPLE_LIMIT}
    """
    result = conn.execute(query, [src_user]).fetchall()
    samples = [dict(zip(['activity_id', 'timestamp', 'host_id', 'src_ip', 'src_port',
                         'src_user', 'dst_user'], row)) for row in result]
    
    # 目标用户分布
    query = f"""
        SELECT dst_user, COUNT(*) as count
        FROM network_activities
        WHERE src_user = ?
        {time_filter}
        GROUP BY dst_user
        ORDER BY count DESC
    """
    result = conn.execute(query, [src_user]).fetchall()
    dst_user_distribution = [{'dst_user': row[0], 'count': row[1]} for row in result]
    
    # 源IP分布
    query = f"""
        SELECT src_ip, COUNT(*) as count
        FROM network_activities
        WHERE src_user = ?
        {time_filter}
        GROUP BY src_ip
        ORDER BY count DESC
    """
    result = conn.execute(query, [src_user]).fetchall()
    src_ip_distribution = [{'src_ip': row[0], 'count': row[1]} for row in result]
    
    conn.close()
    
    return {
        'retrieval_task': 'recall_by_src_user',
        'params': {'src_user': src_user, 'start_time': start_time, 'end_time': end_time},
        'summary': {
            'network_activities': {
                'count': len(samples),
                'samples': samples,
                'dst_user_distribution': dst_user_distribution,
                'src_ip_distribution': src_ip_distribution
            }
        },
        'coverage_question_ids': [26]
    }


def recall_by_rule_id(rule_id: str, start_time: Optional[str] = None, end_time: Optional[str] = None) -> Dict[str, Any]:
    """
    召回某规则在多主机上的触发情况
    支持问题: 7 (以及3可使用)
    """
    conn = get_connection()
    
    time_filter = ""
    if start_time and end_time:
        time_filter = f"AND timestamp BETWEEN '{start_time}' AND '{end_time}'"
    
    # 告警明细
    query = f"""
        SELECT a.alert_id, a.timestamp, a.host_id, a.rule_id, a.alert_level, a.description
        FROM security_alerts a
        WHERE a.rule_id = ?
        {time_filter}
        LIMIT {SAMPLE_LIMIT}
    """
    result = conn.execute(query, [rule_id]).fetchall()
    samples = [dict(zip(['alert_id', 'timestamp', 'host_id', 'rule_id', 'alert_level', 
                         'description'], row)) for row in result]
    
    # 按主机分组统计
    query = f"""
        SELECT host_id, COUNT(*) as count
        FROM security_alerts
        WHERE rule_id = ?
        {time_filter}
        GROUP BY host_id
        ORDER BY count DESC
    """
    result = conn.execute(query, [rule_id]).fetchall()
    by_host_id = [{'host_id': row[0], 'count': row[1]} for row in result]
    
    conn.close()
    
    return {
        'retrieval_task': 'recall_by_rule_id',
        'params': {'rule_id': rule_id, 'start_time': start_time, 'end_time': end_time},
        'summary': {
            'security_alerts': {
                'count': len(samples),
                'samples': samples,
                'by_host_id': by_host_id
            }
        },
        'coverage_question_ids': [7, 3]
    }


# 问题ID到召回函数的映射
QUESTION_TO_RECALL = {
    1: ('recall_host_scope', ['host_id']),
    2: ('recall_host_scope', ['host_id']),
    3: ('recall_host_scope', ['host_id', 'alert_level']),
    4: ('recall_host_scope', ['host_id']),
    5: ('recall_host_scope', ['host_id', 'uid', 'start_time', 'end_time']),
    6: ('recall_host_scope', ['host_id']),
    7: ('recall_by_rule_id', ['rule_id', 'start_time', 'end_time']),
    8: ('recall_host_scope', ['host_id', 'uid', 'start_time', 'end_time']),
    9: ('recall_host_scope', ['host_id']),
    10: ('recall_host_scope', ['host_id', 'start_time', 'end_time']),
    11: ('recall_host_scope', ['host_id']),
    12: ('recall_by_src_ip', ['src_ip', 'start_time', 'end_time']),
    13: ('recall_by_src_ip', ['src_ip']),
    14: ('recall_by_src_ip', ['src_ip', 'start_time', 'end_time']),
    15: ('recall_by_src_ip', ['src_ip']),
    16: ('recall_by_src_ip', ['src_ip', 'start_time', 'end_time']),
    17: ('recall_by_file_hash', ['md5_after']),
    18: ('recall_by_file_hash', ['md5_after']),
    19: ('recall_by_file_hash', ['md5_after']),
    20: ('recall_by_file_hash', ['md5_before', 'md5_after']),
    21: ('recall_by_file_hash', ['md5_after']),
    22: ('recall_by_uid', ['uid', 'start_time', 'end_time']),
    23: ('recall_by_uid', ['uid', 'start_time', 'end_time']),
    24: ('recall_by_uid', ['uid', 'start_time', 'end_time']),
    25: ('recall_by_uid', ['uid', 'start_time', 'end_time']),
    26: ('recall_by_src_user', ['src_user', 'start_time', 'end_time']),
}


if __name__ == "__main__":
    # 测试召回函数
    logger.info("测试召回函数...")
    
    # 测试 recall_host_scope
    result = recall_host_scope("004")
    logger.info(f"recall_host_scope 返回: {result['summary'].keys()}")
    
    # 测试 recall_by_src_ip
    result = recall_by_src_ip("192.168.217.1")
    logger.info(f"recall_by_src_ip 返回: {result['summary'].keys()}")
