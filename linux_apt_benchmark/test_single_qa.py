"""
单实例测试脚本 - 用于验证QA生成流程
"""

import json
import os
from generate_qa_pairs import (
    create_openai_client,
    process_single_instance,
    format_retrieval_content,
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE
)


def test_single_instance(instance_id: str = "q1_inst0", model: str = "qwen3.5-flash"):
    """测试单个实例的QA生成"""

    print(f"\n{'='*80}")
    print(f"测试实例: {instance_id}")
    print(f"模型: {model}")
    print(f"{'='*80}\n")

    # 检查API key
    if not os.getenv("DASHSCOPE_API_KEY"):
        print("错误: 环境变量 DASHSCOPE_API_KEY 未设置！")
        print("请先设置: export DASHSCOPE_API_KEY='your-api-key'")
        return

    # 加载数据
    input_file = "data/question_instances_with_retrieval.json"
    print(f"加载数据: {input_file}")

    with open(input_file, 'r', encoding='utf-8') as f:
        all_data = json.load(f)

    # 查找指定实例
    instance_data = None
    for data in all_data:
        if data['instance']['instance_id'] == instance_id:
            instance_data = data
            break

    if not instance_data:
        print(f"错误: 未找到实例 {instance_id}")
        return

    # 显示问题信息
    instance = instance_data['instance']
    retrieval = instance_data['retrieval']

    print(f"\n【问题信息】")
    print(f"  实例ID: {instance['instance_id']}")
    print(f"  问题ID: {instance['question_id']}")
    print(f"  问题: {instance['question']}")
    print(f"  维度: {instance.get('dimension', 'N/A')}")
    print(f"  攻击阶段: {instance.get('attack_stage', 'N/A')}")

    print(f"\n【召回信息】")
    print(f"  召回任务: {retrieval.get('retrieval_task', 'N/A')}")
    print(f"  召回参数: {json.dumps(retrieval.get('params', {}), ensure_ascii=False)}")

    # 显示召回数据统计
    summary = retrieval.get('summary', {})
    print(f"\n【召回数据统计】")
    for table_name, table_data in summary.items():
        if isinstance(table_data, dict) and 'count' in table_data:
            print(f"  {table_name}: {table_data['count']} 条")

    # 创建客户端并生成答案
    print(f"\n{'='*80}")
    print("开始生成答案...")
    print(f"{'='*80}\n")

    try:
        client = create_openai_client()
        result = process_single_instance(client, instance_data, model)

        print(f"\n{'='*80}")
        print("【生成的答案】")
        print(f"{'='*80}\n")
        print(result['answer'])
        print(f"\n{'='*80}")
        print(f"生成状态: {result['generation_status']}")
        print(f"模型: {result['model']}")
        print(f"时间戳: {result['timestamp']}")
        print(f"{'='*80}")

        # 保存结果
        output_file = f"data/test_result_{instance_id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n结果已保存到: {output_file}")

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()


def preview_prompt(instance_id: str = "q1_inst0"):
    """预览Prompt（不调用API）"""

    print(f"\n{'='*80}")
    print(f"预览Prompt - 实例: {instance_id}")
    print(f"{'='*80}\n")

    # 加载数据
    input_file = "data/question_instances_with_retrieval.json"
    with open(input_file, 'r', encoding='utf-8') as f:
        all_data = json.load(f)

    # 查找指定实例
    instance_data = None
    for data in all_data:
        if data['instance']['instance_id'] == instance_id:
            instance_data = data
            break

    if not instance_data:
        print(f"错误: 未找到实例 {instance_id}")
        return

    instance = instance_data['instance']
    retrieval = instance_data['retrieval']

    # 格式化召回内容
    retrieval_content = format_retrieval_content(retrieval)

    # 构造用户prompt
    user_prompt = USER_PROMPT_TEMPLATE.format(
        question=instance['question'],
        attack_stage=instance.get('attack_stage', 'N/A'),
        dimension=instance.get('dimension', 'N/A'),
        retrieval_content=retrieval_content
    )

    print("【SYSTEM PROMPT】")
    print(f"长度: {len(SYSTEM_PROMPT)} 字符")
    print("-" * 80)
    print(SYSTEM_PROMPT)

    print(f"\n\n{'='*80}")
    print("【USER PROMPT】")
    print(f"长度: {len(user_prompt)} 字符")
    print("-" * 80)
    print(user_prompt[:3000])  # 只显示前3000字符
    if len(user_prompt) > 3000:
        print(f"\n... (还有 {len(user_prompt) - 3000} 字符)")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法:")
        print("  python test_single_qa.py test [instance_id]    # 测试单实例")
        print("  python test_single_qa.py preview [instance_id] # 预览Prompt")
        print("\n示例:")
        print("  python test_single_qa.py test q1_inst0")
        print("  python test_single_qa.py preview q1_inst0")
        sys.exit(1)

    command = sys.argv[1]
    instance_id = sys.argv[2] if len(sys.argv) > 2 else "q1_inst0"

    if command == "test":
        test_single_instance(instance_id)
    elif command == "preview":
        preview_prompt(instance_id)
    else:
        print(f"未知命令: {command}")
        print("可用命令: test, preview")
