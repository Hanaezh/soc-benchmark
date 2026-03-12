"""
主脚本：运行完整的实例生成流程
1. 提取种子数据
2. 生成问题实例（先每个问题1个）
3. 预览实例供确认
"""

import logging
from extract_seeds import extract_seeds
from generate_instances import generate_instances, preview_instances

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """运行完整流程"""
    logger.info("=" * 60)
    logger.info("开始问题实例化流程")
    logger.info("=" * 60)
    
    # 步骤1: 提取种子数据
    logger.info("\n步骤1: 提取种子数据...")
    try:
        seeds = extract_seeds(limit_per_type=50)
        logger.info("✓ 种子数据提取完成")
    except Exception as e:
        logger.error(f"✗ 种子数据提取失败: {e}")
        return
    
    # 步骤2: 生成问题实例（先每个问题1个）
    logger.info("\n步骤2: 生成问题实例（每个问题1个）...")
    try:
        instances = generate_instances(num_instances_per_question=1)
        logger.info("✓ 问题实例生成完成")
    except Exception as e:
        logger.error(f"✗ 问题实例生成失败: {e}")
        return
    
    # 步骤3: 预览实例
    logger.info("\n步骤3: 预览生成的实例...")
    preview_instances(instances, num_to_show=10)
    
    logger.info("\n" + "=" * 60)
    logger.info("流程完成！")
    logger.info("=" * 60)
    logger.info("\n请检查以下文件:")
    logger.info("  - question_instance_seeds.json (种子数据)")
    logger.info("  - question_instances.json (生成的问题实例)")
    logger.info("\n如果实例没有问题，可以修改 generate_instances.py 中的")
    logger.info("num_instances_per_question 参数来批量生成更多实例。")


if __name__ == "__main__":
    main()
