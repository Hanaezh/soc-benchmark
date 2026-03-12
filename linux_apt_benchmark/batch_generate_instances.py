"""
批量生成问题实例 - 为每个问题生成10个实例
"""

import logging
from generate_instances import generate_instances, preview_instances

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """批量生成问题实例"""
    logger.info("=" * 60)
    logger.info("批量生成问题实例（每个问题10个）")
    logger.info("=" * 60)
    
    try:
        # 生成10个实例
        instances = generate_instances(num_instances_per_question=10)
        
        logger.info("\n" + "=" * 60)
        logger.info("预览部分实例...")
        logger.info("=" * 60)
        
        # 预览每种类型问题的第一个实例
        preview_questions = [1, 5, 7, 12, 17, 20, 22, 26]
        preview_list = []
        
        for inst in instances:
            if inst['question_id'] in preview_questions:
                if not any(p['question_id'] == inst['question_id'] for p in preview_list):
                    preview_list.append(inst)
        
        preview_instances(preview_list, num_to_show=len(preview_list))
        
        logger.info("\n" + "=" * 60)
        logger.info("批量生成完成！")
        logger.info(f"共生成 {len(instances)} 个问题实例")
        logger.info("实例已保存到 question_instances.json")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"批量生成失败: {e}")
        raise


if __name__ == "__main__":
    main()
