"""
生成问题实例 - 使用种子数据替换模板中的占位符
为每个问题生成指定数量的实例
"""

import json
import random
import logging
from typing import Dict, Any, List
from recall_functions import QUESTION_TO_RECALL

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

TEMPLATES_PATH = "questions_templates_v3.json"
SEEDS_PATH = "question_instance_seeds.json"
OUTPUT_PATH = "question_instances_260.json"


def load_templates():
    """加载问题模板"""
    with open(TEMPLATES_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_seeds():
    """加载种子数据"""
    with open(SEEDS_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_instance(template: Dict[str, Any], seeds: Dict[str, Any], instance_id: int) -> Dict[str, Any]:
    """
    为单个模板生成一个实例
    选择信息量丰富的实体（从种子数据前部选择）
    """
    question_id = template['id']
    question_text = template['question']
    
    # 获取该问题需要的参数
    if question_id not in QUESTION_TO_RECALL:
        logger.warning(f"问题 {question_id} 没有对应的召回函数映射")
        return None
    
    recall_func, required_params = QUESTION_TO_RECALL[question_id]
    
    # 为每个占位符选择值
    params = {}
    
    # host_id
    if '<host_id>' in question_text:
        if 'host_id' not in seeds or not seeds['host_id']:
            logger.error(f"问题 {question_id} 需要 host_id 但种子数据中没有")
            return None
        # 选择信息量丰富的（列表前面的）
        params['host_id'] = seeds['host_id'][instance_id % len(seeds['host_id'])]
        question_text = question_text.replace('<host_id>', params['host_id'])
    
    # uid
    if '<uid>' in question_text:
        if 'uid' not in seeds or not seeds['uid']:
            logger.error(f"问题 {question_id} 需要 uid 但种子数据中没有")
            return None
        params['uid'] = seeds['uid'][instance_id % len(seeds['uid'])]
        question_text = question_text.replace('<uid>', str(params['uid']))
    
    # src_ip
    if '<src_ip>' in question_text:
        if 'src_ip' not in seeds or not seeds['src_ip']:
            logger.error(f"问题 {question_id} 需要 src_ip 但种子数据中没有")
            return None
        params['src_ip'] = seeds['src_ip'][instance_id % len(seeds['src_ip'])]
        question_text = question_text.replace('<src_ip>', params['src_ip'])
    
    # md5_after
    if '<md5_after>' in question_text:
        if question_id == 20:  # 问题20需要成对的md5
            if 'md5_before_after_pairs' not in seeds or not seeds['md5_before_after_pairs']:
                logger.error(f"问题 {question_id} 需要 md5_before_after_pairs 但种子数据中没有")
                return None
            pair = seeds['md5_before_after_pairs'][instance_id % len(seeds['md5_before_after_pairs'])]
            params['md5_before'] = pair['md5_before']
            params['md5_after'] = pair['md5_after']
            question_text = question_text.replace('<md5_before>', params['md5_before'])
            question_text = question_text.replace('<md5_after>', params['md5_after'])
        else:
            if 'md5_after' not in seeds or not seeds['md5_after']:
                logger.error(f"问题 {question_id} 需要 md5_after 但种子数据中没有")
                return None
            params['md5_after'] = seeds['md5_after'][instance_id % len(seeds['md5_after'])]
            question_text = question_text.replace('<md5_after>', params['md5_after'])
    
    # md5_before (单独出现的情况，问题20在上面已处理)
    if '<md5_before>' in question_text and 'md5_before' not in params:
        if 'md5_before_after_pairs' not in seeds or not seeds['md5_before_after_pairs']:
            logger.error(f"问题 {question_id} 需要 md5_before 但种子数据中没有")
            return None
        pair = seeds['md5_before_after_pairs'][instance_id % len(seeds['md5_before_after_pairs'])]
        params['md5_before'] = pair['md5_before']
        question_text = question_text.replace('<md5_before>', params['md5_before'])
    
    # rule_id
    if '<rule_id>' in question_text:
        if 'rule_id' not in seeds or not seeds['rule_id']:
            logger.error(f"问题 {question_id} 需要 rule_id 但种子数据中没有")
            return None
        params['rule_id'] = seeds['rule_id'][instance_id % len(seeds['rule_id'])]
        question_text = question_text.replace('<rule_id>', params['rule_id'])
    
    # src_user
    if '<src_user>' in question_text:
        if 'src_user' not in seeds or not seeds['src_user']:
            logger.error(f"问题 {question_id} 需要 src_user 但种子数据中没有")
            return None
        params['src_user'] = seeds['src_user'][instance_id % len(seeds['src_user'])]
        question_text = question_text.replace('<src_user>', params['src_user'])
    
    # alert_level
    if '<alert_level>' in question_text:
        if 'alert_level' not in seeds or not seeds['alert_level']:
            logger.error(f"问题 {question_id} 需要 alert_level 但种子数据中没有")
            return None
        # 高危告警通常指较高的level
        params['alert_level'] = seeds['alert_level'][0]  # 取最高的level
        question_text = question_text.replace('<alert_level>', str(params['alert_level']))
    
    # 时间范围
    if '<start_time>' in question_text or '<end_time>' in question_text:
        if 'time_ranges' not in seeds or not seeds['time_ranges']:
            logger.error(f"问题 {question_id} 需要 time_ranges 但种子数据中没有")
            return None
        time_range = seeds['time_ranges'][instance_id % len(seeds['time_ranges'])]
        params['start_time'] = time_range['start_time']
        params['end_time'] = time_range['end_time']
        question_text = question_text.replace('<start_time>', params['start_time'])
        question_text = question_text.replace('<end_time>', params['end_time'])
    
    # 构建实例
    instance = {
        'instance_id': f"q{question_id}_inst{instance_id}",
        'question_id': question_id,
        'question': question_text,
        'dimension': template['dimension'],
        'attack_stage': template['attack_stage'],
        'metadata': template['metadata'],
        'recall_function': recall_func,
        'recall_params': params
    }
    
    return instance


def generate_instances(num_instances_per_question: int = 1):
    """
    为所有问题生成实例
    
    Args:
        num_instances_per_question: 每个问题生成的实例数量
    """
    logger.info(f"开始生成问题实例，每个问题 {num_instances_per_question} 个实例...")
    
    templates = load_templates()
    seeds = load_seeds()
    
    all_instances = []
    
    for template in templates:
        question_id = template['id']
        logger.info(f"处理问题 {question_id}...")
        
        question_instances = []
        for i in range(num_instances_per_question):
            instance = generate_instance(template, seeds, i)
            if instance:
                question_instances.append(instance)
            else:
                logger.warning(f"问题 {question_id} 的第 {i} 个实例生成失败")
        
        all_instances.extend(question_instances)
        logger.info(f"问题 {question_id} 生成了 {len(question_instances)} 个实例")
    
    # 保存实例
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(all_instances, f, indent=2, ensure_ascii=False)
    
    logger.info(f"共生成 {len(all_instances)} 个问题实例")
    logger.info(f"实例已保存到 {OUTPUT_PATH}")
    
    # 打印统计
    logger.info("=" * 50)
    logger.info("实例生成统计:")
    question_counts = {}
    for inst in all_instances:
        qid = inst['question_id']
        question_counts[qid] = question_counts.get(qid, 0) + 1
    
    for qid in sorted(question_counts.keys()):
        logger.info(f"  问题 {qid}: {question_counts[qid]} 个实例")
    
    return all_instances


def preview_instances(instances: List[Dict[str, Any]], num_to_show: int = 3):
    """预览生成的实例"""
    logger.info("\n" + "=" * 50)
    logger.info(f"预览前 {num_to_show} 个实例:")
    logger.info("=" * 50)
    
    for i, inst in enumerate(instances[:num_to_show]):
        logger.info(f"\n[实例 {i+1}]")
        logger.info(f"ID: {inst['instance_id']}")
        logger.info(f"问题ID: {inst['question_id']}")
        logger.info(f"问题: {inst['question']}")
        logger.info(f"召回函数: {inst['recall_function']}")
        logger.info(f"召回参数: {inst['recall_params']}")
        logger.info(f"维度: {inst['dimension']}")
        logger.info(f"攻击阶段: {inst['attack_stage']}")


if __name__ == "__main__":
    try:
        # 先生成每个问题1个实例供确认
        instances = generate_instances(num_instances_per_question=10)
        
        # 预览部分实例
        preview_instances(instances, num_to_show=5)
        
        logger.info("\n请检查生成的实例。如果没问题，可以修改 num_instances_per_question 参数批量生成。")
        
    except Exception as e:
        logger.error(f"生成实例时出错: {e}")
        raise
