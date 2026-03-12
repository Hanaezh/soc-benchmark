"""
保存召回结果 - 为所有实例执行召回并保存结果
"""

import json
import logging
from datetime import datetime
from recall_functions import (
    recall_host_scope, recall_by_src_ip, recall_by_file_hash,
    recall_by_uid, recall_by_src_user, recall_by_rule_id
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def execute_recall(instance):
    """为单个实例执行召回"""
    func_name = instance['recall_function']
    params = instance['recall_params']
    
    try:
        if func_name == 'recall_host_scope':
            result = recall_host_scope(
                host_id=params['host_id'],
                start_time=params.get('start_time'),
                end_time=params.get('end_time')
            )
        elif func_name == 'recall_by_src_ip':
            result = recall_by_src_ip(
                src_ip=params['src_ip'],
                start_time=params.get('start_time'),
                end_time=params.get('end_time')
            )
        elif func_name == 'recall_by_file_hash':
            result = recall_by_file_hash(
                md5_after=params['md5_after'],
                md5_before=params.get('md5_before'),
                start_time=params.get('start_time'),
                end_time=params.get('end_time')
            )
        elif func_name == 'recall_by_uid':
            result = recall_by_uid(
                uid=params['uid'],
                start_time=params.get('start_time'),
                end_time=params.get('end_time')
            )
        elif func_name == 'recall_by_src_user':
            result = recall_by_src_user(
                src_user=params['src_user'],
                start_time=params.get('start_time'),
                end_time=params.get('end_time')
            )
        elif func_name == 'recall_by_rule_id':
            result = recall_by_rule_id(
                rule_id=params['rule_id'],
                start_time=params.get('start_time'),
                end_time=params.get('end_time')
            )
        else:
            logger.error(f"未知的召回函数: {func_name}")
            return None
        
        return result
        
    except Exception as e:
        logger.error(f"召回失败 [{instance['instance_id']}]: {e}")
        return None


def main():
    """为所有实例执行召回并保存结果"""
    logger.info("="*60)
    logger.info("开始为所有实例执行召回")
    logger.info("="*60)
    
    # 加载实例
    with open('data/question_instances_260.json', 'r', encoding='utf-8') as f:
        instances = json.load(f)
    
    logger.info(f"共有 {len(instances)} 个实例")
    
    # 执行召回
    results = []
    success_count = 0
    
    for i, instance in enumerate(instances, 1):
        logger.info(f"[{i}/{len(instances)}] 处理实例 {instance['instance_id']}...")
        
        recall_result = execute_recall(instance)
        
        if recall_result:
            # 合并实例信息和召回结果
            combined = {
                'instance': {
                    'instance_id': instance['instance_id'],
                    'question_id': instance['question_id'],
                    'question': instance['question'],
                    'dimension': instance['dimension'],
                    'attack_stage': instance['attack_stage']
                },
                'retrieval': recall_result
            }
            results.append(combined)
            success_count += 1
            logger.info(f"  ✓ 召回成功")
        else:
            logger.warning(f"  ✗ 召回失败")
    
    # 保存结果 - 使用自定义JSON编码器处理datetime
    def json_serializer(obj):
        """处理datetime等特殊类型"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")
    
    output_file = 'data/question_instances_with_retrieval.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=json_serializer)
    
    logger.info("\n" + "="*60)
    logger.info(f"召回完成: {success_count}/{len(instances)} 成功")
    logger.info(f"结果已保存到: {output_file}")
    logger.info("="*60)
    
    # 打印统计信息
    logger.info("\n数据量统计:")
    total_records = 0
    for result in results:
        summary = result['retrieval']['summary']
        for table_name, table_data in summary.items():
            if isinstance(table_data, dict) and 'count' in table_data:
                total_records += table_data['count']
    
    logger.info(f"  总召回记录数: {total_records}")
    logger.info(f"  平均每个实例: {total_records / len(results):.1f} 条记录")


if __name__ == "__main__":
    main()
