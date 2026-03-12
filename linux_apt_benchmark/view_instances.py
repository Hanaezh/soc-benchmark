"""
查看问题实例工具 - 方便浏览和检查生成的实例
"""

import json
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


def load_instances():
    """加载问题实例"""
    with open('question_instances.json', 'r', encoding='utf-8') as f:
        return json.load(f)


def view_by_question_id(instances, question_id):
    """查看特定问题的所有实例"""
    filtered = [inst for inst in instances if inst['question_id'] == question_id]
    
    if not filtered:
        logger.info(f"未找到问题 {question_id} 的实例")
        return
    
    logger.info(f"\n{'='*80}")
    logger.info(f"问题 {question_id} 的所有实例 (共 {len(filtered)} 个)")
    logger.info('='*80)
    
    for i, inst in enumerate(filtered, 1):
        logger.info(f"\n[实例 {i}] {inst['instance_id']}")
        logger.info(f"问题: {inst['question']}")
        logger.info(f"召回函数: {inst['recall_function']}")
        logger.info(f"召回参数: {json.dumps(inst['recall_params'], ensure_ascii=False)}")
        logger.info(f"维度: {inst['dimension']}")
        logger.info('-'*80)


def view_summary(instances):
    """查看实例统计摘要"""
    logger.info("\n" + "="*80)
    logger.info("问题实例统计摘要")
    logger.info("="*80)
    
    # 按问题ID统计
    stats = {}
    for inst in instances:
        qid = inst['question_id']
        if qid not in stats:
            stats[qid] = {
                'count': 0,
                'dimension': inst['dimension'],
                'attack_stage': inst['attack_stage'],
                'recall_func': inst['recall_function']
            }
        stats[qid]['count'] += 1
    
    logger.info(f"\n总计: {len(instances)} 个实例，覆盖 {len(stats)} 个问题\n")
    logger.info(f"{'问题ID':<8} {'实例数':<8} {'维度':<20} {'攻击阶段':<25} {'召回函数'}")
    logger.info("-"*100)
    
    for qid in sorted(stats.keys()):
        s = stats[qid]
        logger.info(f"{qid:<8} {s['count']:<8} {s['dimension']:<20} {s['attack_stage']:<25} {s['recall_func']}")
    
    # 按召回函数统计
    logger.info("\n" + "="*80)
    logger.info("按召回函数统计")
    logger.info("="*80)
    
    func_stats = {}
    for inst in instances:
        func = inst['recall_function']
        func_stats[func] = func_stats.get(func, 0) + 1
    
    for func, count in sorted(func_stats.items()):
        logger.info(f"{func:<30} {count:>4} 个实例")


def view_specific_instance(instances, instance_id):
    """查看特定实例的详细信息"""
    for inst in instances:
        if inst['instance_id'] == instance_id:
            logger.info("\n" + "="*80)
            logger.info(f"实例详情: {instance_id}")
            logger.info("="*80)
            logger.info(json.dumps(inst, indent=2, ensure_ascii=False))
            return
    
    logger.info(f"未找到实例: {instance_id}")


def main():
    """主函数"""
    instances = load_instances()
    
    if len(sys.argv) == 1:
        # 无参数，显示摘要
        view_summary(instances)
    elif sys.argv[1] == 'summary':
        # 显示摘要
        view_summary(instances)
    elif sys.argv[1] == 'question' and len(sys.argv) > 2:
        # 显示特定问题的所有实例
        question_id = int(sys.argv[2])
        view_by_question_id(instances, question_id)
    elif sys.argv[1] == 'instance' and len(sys.argv) > 2:
        # 显示特定实例
        instance_id = sys.argv[2]
        view_specific_instance(instances, instance_id)
    else:
        logger.info("用法:")
        logger.info("  python view_instances.py                    # 显示摘要")
        logger.info("  python view_instances.py summary            # 显示摘要")
        logger.info("  python view_instances.py question <ID>      # 显示特定问题的所有实例")
        logger.info("  python view_instances.py instance <ID>      # 显示特定实例详情")
        logger.info("\n例如:")
        logger.info("  python view_instances.py question 1")
        logger.info("  python view_instances.py instance q1_inst0")


if __name__ == "__main__":
    main()
