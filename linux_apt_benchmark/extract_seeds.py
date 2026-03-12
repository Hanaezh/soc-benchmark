"""
从数据库提取问题实例化所需的种子数据
选择信息量丰富的实体（按出现频率排序）
"""

import duckdb
import json
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DB_PATH = "linux_apt_2024_04_06_january.duckdb"
OUTPUT_PATH = "question_instance_seeds.json"

def extract_seeds(limit_per_type=50):
    """提取各占位符的实例值"""
    conn = duckdb.connect(DB_PATH, read_only=True)
    seeds = {}
    
    logger.info("开始提取种子数据...")
    
    # host_id - 选择审计事件最多的主机（信息量最丰富）
    logger.info("提取 host_id...")
    result = conn.execute(f"""
        SELECT host_id 
        FROM audit_events 
        WHERE host_id IS NOT NULL 
        GROUP BY host_id 
        ORDER BY COUNT(*) DESC 
        LIMIT {limit_per_type}
    """).fetchall()
    seeds['host_id'] = [row[0] for row in result]
    logger.info(f"提取到 {len(seeds['host_id'])} 个 host_id")
    
    # uid - 选择活跃度高的用户
    logger.info("提取 uid...")
    result = conn.execute(f"""
        SELECT DISTINCT uid 
        FROM audit_events 
        WHERE uid IS NOT NULL 
        GROUP BY uid 
        ORDER BY COUNT(*) DESC 
        LIMIT {limit_per_type}
    """).fetchall()
    seeds['uid'] = [int(row[0]) for row in result]
    logger.info(f"提取到 {len(seeds['uid'])} 个 uid")
    
    # src_ip - 选择连接次数多的IP
    logger.info("提取 src_ip...")
    result = conn.execute(f"""
        SELECT src_ip 
        FROM network_activities 
        WHERE src_ip IS NOT NULL AND TRIM(src_ip) != '' 
        GROUP BY src_ip 
        ORDER BY COUNT(*) DESC 
        LIMIT {limit_per_type}
    """).fetchall()
    seeds['src_ip'] = [row[0] for row in result]
    logger.info(f"提取到 {len(seeds['src_ip'])} 个 src_ip")
    
    # md5_after - 选择出现次数多的文件哈希
    logger.info("提取 md5_after...")
    result = conn.execute(f"""
        SELECT md5_after 
        FROM file_integrity_events 
        WHERE md5_after IS NOT NULL AND TRIM(md5_after) != '' 
        GROUP BY md5_after 
        ORDER BY COUNT(*) DESC 
        LIMIT {limit_per_type}
    """).fetchall()
    seeds['md5_after'] = [row[0] for row in result]
    logger.info(f"提取到 {len(seeds['md5_after'])} 个 md5_after")
    
    # md5_before 和 md5_after 成对提取
    logger.info("提取 md5_before_after 对...")
    result = conn.execute(f"""
        SELECT md5_before, md5_after 
        FROM file_integrity_events 
        WHERE md5_before IS NOT NULL AND md5_after IS NOT NULL 
          AND TRIM(md5_before) != '' AND TRIM(md5_after) != ''
          AND md5_before != md5_after
        GROUP BY md5_before, md5_after 
        ORDER BY COUNT(*) DESC 
        LIMIT {limit_per_type}
    """).fetchall()
    seeds['md5_before_after_pairs'] = [{"md5_before": row[0], "md5_after": row[1]} for row in result]
    logger.info(f"提取到 {len(seeds['md5_before_after_pairs'])} 对 md5_before/after")
    
    # rule_id - 选择触发次数多的规则
    logger.info("提取 rule_id...")
    result = conn.execute(f"""
        SELECT rule_id 
        FROM security_alerts 
        WHERE rule_id IS NOT NULL 
        GROUP BY rule_id 
        ORDER BY COUNT(*) DESC 
        LIMIT {limit_per_type}
    """).fetchall()
    seeds['rule_id'] = [str(row[0]) for row in result]
    logger.info(f"提取到 {len(seeds['rule_id'])} 个 rule_id")
    
    # src_user - 选择活跃的源用户
    logger.info("提取 src_user...")
    result = conn.execute(f"""
        SELECT src_user 
        FROM network_activities 
        WHERE src_user IS NOT NULL AND TRIM(src_user) != '' 
        GROUP BY src_user 
        ORDER BY COUNT(*) DESC 
        LIMIT {limit_per_type}
    """).fetchall()
    seeds['src_user'] = [row[0] for row in result]
    logger.info(f"提取到 {len(seeds['src_user'])} 个 src_user")
    
    # alert_level - 所有可用的告警级别
    logger.info("提取 alert_level...")
    result = conn.execute("""
        SELECT DISTINCT alert_level 
        FROM security_alerts 
        WHERE alert_level IS NOT NULL 
        ORDER BY alert_level DESC
    """).fetchall()
    seeds['alert_level'] = [int(row[0]) for row in result]
    logger.info(f"提取到 {len(seeds['alert_level'])} 个 alert_level")
    
    # 时间范围 - 获取数据的时间跨度并生成常用时间段
    logger.info("提取 time_ranges...")
    result = conn.execute("""
        SELECT CAST(MIN(timestamp) AS VARCHAR) AS min_ts, 
               CAST(MAX(timestamp) AS VARCHAR) AS max_ts 
        FROM audit_events 
        WHERE timestamp IS NOT NULL
    """).fetchone()
    
    if result and result[0] and result[1]:
        min_ts = str(result[0])
        max_ts = str(result[1])
        logger.info(f"数据时间范围: {min_ts} 到 {max_ts}")
        
        # 生成一些有代表性的时间段
        seeds['time_ranges'] = [
            {"start_time": min_ts, "end_time": max_ts, "description": "全时间段"},
        ]
        
        # 提取一些有高活动量的时间段
        result = conn.execute("""
            SELECT 
                CAST(DATE_TRUNC('day', timestamp) AS VARCHAR) as day,
                COUNT(*) as cnt
            FROM audit_events
            WHERE timestamp IS NOT NULL
            GROUP BY DATE_TRUNC('day', timestamp)
            ORDER BY cnt DESC
            LIMIT 10
        """).fetchall()
        
        for row in result[:5]:  # 取前5个活跃天
            day_start = str(row[0])
            day_date = day_start.split('T')[0] if 'T' in day_start else day_start.split()[0]
            day_end = f"{day_date}T23:59:59"
            seeds['time_ranges'].append({
                "start_time": day_start,
                "end_time": day_end,
                "description": f"高活跃日 {day_date}"
            })
    else:
        logger.warning("无法提取时间范围，时间戳数据可能为空")
        seeds['time_ranges'] = []
    
    logger.info(f"提取到 {len(seeds['time_ranges'])} 个 time_ranges")
    
    conn.close()
    
    # 保存种子数据
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(seeds, f, indent=2, ensure_ascii=False)
    
    logger.info(f"种子数据已保存到 {OUTPUT_PATH}")
    
    # 打印统计信息
    logger.info("=" * 50)
    logger.info("种子数据统计:")
    for key, value in seeds.items():
        if key != 'time_ranges':
            logger.info(f"  {key}: {len(value)} 个")
        else:
            logger.info(f"  {key}: {len(value)} 个时间段")
    
    return seeds

if __name__ == "__main__":
    try:
        seeds = extract_seeds(limit_per_type=50)
        logger.info("种子数据提取完成")
    except Exception as e:
        logger.error(f"提取种子数据时出错: {e}")
        raise
