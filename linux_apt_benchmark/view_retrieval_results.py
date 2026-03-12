"""
查看召回结果工具 - 方便浏览 question_instances_with_retrieval.json
"""

import json
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


def load_results():
    """加载召回结果"""
    with open('question_instances_with_retrieval.json', 'r', encoding='utf-8') as f:
        return json.load(f)


def view_summary(results):
    """查看整体摘要"""
    logger.info("\n" + "="*80)
    logger.info("召回结果整体摘要")
    logger.info("="*80)
    logger.info(f"\n总实例数: {len(results)}")
    
    # 统计各类数据量
    total_audit = 0
    total_alerts = 0
    total_network = 0
    total_fim = 0
    
    for result in results:
        summary = result['retrieval']['summary']
        if 'audit_events' in summary:
            total_audit += summary['audit_events']['count']
        if 'security_alerts' in summary:
            total_alerts += summary['security_alerts']['count']
        if 'network_activities' in summary:
            total_network += summary['network_activities']['count']
        if 'file_integrity_events' in summary:
            total_fim += summary['file_integrity_events']['count']
    
    logger.info(f"\n总召回记录数:")
    logger.info(f"  审计事件: {total_audit} 条")
    logger.info(f"  安全告警: {total_alerts} 条")
    logger.info(f"  网络活动: {total_network} 条")
    logger.info(f"  文件完整性事件: {total_fim} 条")
    logger.info(f"  合计: {total_audit + total_alerts + total_network + total_fim} 条")
    
    # 按问题统计
    logger.info(f"\n按问题统计:")
    logger.info(f"{'问题ID':<8} {'问题':<60} {'召回记录数'}")
    logger.info("-"*100)
    
    for result in results:
        instance = result['instance']
        summary = result['retrieval']['summary']
        
        count = 0
        for table_data in summary.values():
            if isinstance(table_data, dict) and 'count' in table_data:
                count += table_data['count']
        
        q_text = instance['question'][:55] + "..." if len(instance['question']) > 55 else instance['question']
        logger.info(f"{instance['question_id']:<8} {q_text:<60} {count:>4} 条")


def view_instance(results, instance_id):
    """查看特定实例的召回结果"""
    for result in results:
        if result['instance']['instance_id'] == instance_id:
            logger.info("\n" + "="*80)
            logger.info(f"实例: {instance_id}")
            logger.info("="*80)
            
            instance = result['instance']
            logger.info(f"\n【问题信息】")
            logger.info(f"问题ID: {instance['question_id']}")
            logger.info(f"问题: {instance['question']}")
            logger.info(f"维度: {instance['dimension']}")
            logger.info(f"攻击阶段: {instance['attack_stage']}")
            
            retrieval = result['retrieval']
            logger.info(f"\n【召回信息】")
            logger.info(f"召回任务: {retrieval['retrieval_task']}")
            logger.info(f"召回参数: {json.dumps(retrieval['params'], ensure_ascii=False)}")
            logger.info(f"覆盖问题: {retrieval['coverage_question_ids']}")
            
            logger.info(f"\n【召回数据摘要】")
            for table_name, table_data in retrieval['summary'].items():
                if isinstance(table_data, dict) and 'count' in table_data:
                    logger.info(f"\n{table_name}: {table_data['count']} 条记录")
                    
                    # 显示前3条样本
                    if 'samples' in table_data and table_data['samples']:
                        logger.info(f"  样本预览（前3条）:")
                        for i, sample in enumerate(table_data['samples'][:3], 1):
                            logger.info(f"    [{i}] {json.dumps(sample, ensure_ascii=False)[:150]}...")
            
            return
    
    logger.info(f"未找到实例: {instance_id}")


def view_question(results, question_id):
    """查看特定问题的召回结果"""
    filtered = [r for r in results if r['instance']['question_id'] == question_id]
    
    if not filtered:
        logger.info(f"未找到问题 {question_id} 的召回结果")
        return
    
    logger.info("\n" + "="*80)
    logger.info(f"问题 {question_id} 的召回结果")
    logger.info("="*80)
    
    for result in filtered:
        instance = result['instance']
        retrieval = result['retrieval']
        
        logger.info(f"\n[{instance['instance_id']}]")
        logger.info(f"问题: {instance['question']}")
        logger.info(f"召回函数: {retrieval['retrieval_task']}")
        logger.info(f"召回参数: {json.dumps(retrieval['params'], ensure_ascii=False)}")
        
        # 统计召回数据量
        total = 0
        details = []
        for table_name, table_data in retrieval['summary'].items():
            if isinstance(table_data, dict) and 'count' in table_data:
                count = table_data['count']
                total += count
                details.append(f"{table_name}={count}")
        
        logger.info(f"召回数据: {total} 条 ({', '.join(details)})")
        logger.info("-"*80)


def export_instance_to_file(results, instance_id, output_file):
    """导出特定实例的召回结果到文件"""
    for result in results:
        if result['instance']['instance_id'] == instance_id:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            logger.info(f"实例 {instance_id} 已导出到: {output_file}")
            return
    
    logger.info(f"未找到实例: {instance_id}")


def main():
    """主函数"""
    results = load_results()
    
    if len(sys.argv) == 1:
        # 无参数，显示摘要
        view_summary(results)
    elif sys.argv[1] == 'summary':
        # 显示摘要
        view_summary(results)
    elif sys.argv[1] == 'instance' and len(sys.argv) > 2:
        # 查看特定实例
        instance_id = sys.argv[2]
        view_instance(results, instance_id)
    elif sys.argv[1] == 'question' and len(sys.argv) > 2:
        # 查看特定问题的所有实例
        question_id = int(sys.argv[2])
        view_question(results, question_id)
    elif sys.argv[1] == 'export' and len(sys.argv) > 3:
        # 导出特定实例到文件
        instance_id = sys.argv[2]
        output_file = sys.argv[3]
        export_instance_to_file(results, instance_id, output_file)
    else:
        logger.info("用法:")
        logger.info("  python view_retrieval_results.py                        # 显示摘要")
        logger.info("  python view_retrieval_results.py summary                # 显示摘要")
        logger.info("  python view_retrieval_results.py instance <ID>          # 查看特定实例的召回结果")
        logger.info("  python view_retrieval_results.py question <ID>          # 查看特定问题的所有召回结果")
        logger.info("  python view_retrieval_results.py export <ID> <file>     # 导出实例到文件")
        logger.info("\n例如:")
        logger.info("  python view_retrieval_results.py instance q1_inst0")
        logger.info("  python view_retrieval_results.py question 1")
        logger.info("  python view_retrieval_results.py export q1_inst0 q1_result.json")


if __name__ == "__main__":
    main()
