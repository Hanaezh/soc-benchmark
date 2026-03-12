"""
导出所有Prompt到文件，供外部批量调用
生成纯文本格式的prompt文件，可以在其他环境调用API
"""

import json
import os
from typing import List, Dict, Any
from generate_qa_pairs import format_retrieval_content, SYSTEM_PROMPT, USER_PROMPT_TEMPLATE


def export_prompts(
    input_file: str = "data/question_instances_with_retrieval.json",
    output_dir: str = "data/prompts",
    batch_size: int = 10
):
    """
    导出所有prompt到文件

    生成两种格式:
    1. 单个JSONL文件 (方便程序处理)
    2. 分批文本文件 (方便人工检查)
    """

    os.makedirs(output_dir, exist_ok=True)

    # 加载数据
    print(f"加载数据: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        all_data = json.load(f)

    total = len(all_data)
    print(f"总共 {total} 个实例")

    # 生成JSONL格式
    jsonl_file = os.path.join(output_dir, "all_prompts.jsonl")
    with open(jsonl_file, 'w', encoding='utf-8') as f_jsonl:

        for i, instance_data in enumerate(all_data):
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

            # 构造完整请求体
            prompt_data = {
                "instance_id": instance['instance_id'],
                "question_id": instance['question_id'],
                "question": instance['question'],
                "system_prompt": SYSTEM_PROMPT,
                "user_prompt": user_prompt,
                "prompt_length": len(user_prompt),
                "model_config": {
                    "model": "qwen3-max",
                    "max_tokens": 8192,
                    "temperature": 0.7
                }
            }

            # 写入JSONL
            f_jsonl.write(json.dumps(prompt_data, ensure_ascii=False) + '\n')

            # 进度打印
            if (i + 1) % 50 == 0:
                print(f"已处理 {i+1}/{total}")

    print(f"✓ JSONL已导出: {jsonl_file}")

    # 生成分批文本文件（方便检查）
    batch_count = (total + batch_size - 1) // batch_size
    for batch_idx in range(batch_count):
        start = batch_idx * batch_size
        end = min((batch_idx + 1) * batch_size, total)

        batch_file = os.path.join(output_dir, f"batch_{batch_idx:03d}_{start:03d}_{end:03d}.txt")

        with open(batch_file, 'w', encoding='utf-8') as f:
            f.write(f"{'='*80}\n")
            f.write(f"批次 {batch_idx + 1}/{batch_count} (实例 {start}-{end-1})\n")
            f.write(f"{'='*80}\n\n")

            for i in range(start, end):
                instance_data = all_data[i]
                instance = instance_data['instance']
                retrieval = instance_data['retrieval']

                retrieval_content = format_retrieval_content(retrieval)
                user_prompt = USER_PROMPT_TEMPLATE.format(
                    question=instance['question'],
                    attack_stage=instance.get('attack_stage', 'N/A'),
                    dimension=instance.get('dimension', 'N/A'),
                    retrieval_content=retrieval_content
                )

                f.write(f"\n{'#'*80}\n")
                f.write(f"INSTANCE_ID: {instance['instance_id']}\n")
                f.write(f"QUESTION_ID: {instance['question_id']}\n")
                f.write(f"QUESTION: {instance['question']}\n")
                f.write(f"{'#'*80}\n\n")

                f.write(f"【SYSTEM PROMPT】\n{SYSTEM_PROMPT}\n\n")
                f.write(f"【USER PROMPT】({len(user_prompt)} 字符)\n{user_prompt}\n")
                f.write(f"{'='*80}\n")

        print(f"✓ 批次文件: {batch_file}")

    # 生成curl命令脚本
    curl_script = os.path.join(output_dir, "batch_curl.sh")
    with open(curl_script, 'w', encoding='utf-8') as f:
        f.write("#!/bin/bash\n\n")
        f.write("# 批量调用API的curl脚本\n")
        f.write("# 用法: DASHSCOPE_API_KEY=xxx bash batch_curl.sh\n\n")
        f.write('API_KEY="${DASHSCOPE_API_KEY:-}"\n')
        f.write('if [ -z "$API_KEY" ]; then\n')
        f.write('    echo "请设置 DASHSCOPE_API_KEY 环境变量"\n')
        f.write('    exit 1\n')
        f.write('fi\n\n')
        f.write('BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"\n')
        f.write('OUTPUT_DIR="api_responses"\n')
        f.write('mkdir -p "$OUTPUT_DIR"\n\n')

        f.write("# 读取JSONL并逐个调用\n")
        f.write("while IFS= read -r line; do\n")
        f.write('    INSTANCE_ID=$(echo "$line" | python3 -c "import sys,json; print(json.load(sys.stdin)['instance_id'])")\n')
        f.write('    SYSTEM_PROMPT=$(echo "$line" | python3 -c "import sys,json; print(json.load(sys.stdin)['system_prompt'])")\n')
        f.write('    USER_PROMPT=$(echo "$line" | python3 -c "import sys,json; print(json.load(sys.stdin)['user_prompt'])")\n')
        f.write('    \n')
        f.write('    echo "处理: $INSTANCE_ID"\n')
        f.write('    \n')
        f.write('    # 构造JSON payload\n')
        f.write('    PAYLOAD=$(python3 << PYEOF\n')
        f.write('import json\n')
        f.write('import sys\n')
        f.write('data = {\n')
        f.write('    "model": "qwen3-max",\n')
        f.write('    "messages": [\n')
        f.write('        {"role": "system", "content": sys.argv[1]},\n')
        f.write('        {"role": "user", "content": sys.argv[2]}\n')
        f.write('    ],\n')
        f.write('    "max_tokens": 8192\n')
        f.write('}\n')
        f.write('print(json.dumps(data, ensure_ascii=False))\n')
        f.write('PYEOF\n')
        f.write('        "$SYSTEM_PROMPT" "$USER_PROMPT"\n')
        f.write('    )\n')
        f.write('    \n')
        f.write('    # 调用API\n')
        f.write('    curl -s "$BASE_URL/chat/completions" \\\n')
        f.write('        -H "Authorization: Bearer $API_KEY" \\\n')
        f.write('        -H "Content-Type: application/json" \\\n')
        f.write('        -d "$PAYLOAD" \\\n')
        f.write('        > "$OUTPUT_DIR/${INSTANCE_ID}.json"\n')
        f.write('    \n')
        f.write('    echo "结果保存到: $OUTPUT_DIR/${INSTANCE_ID}.json"\n')
        f.write('    sleep 0.5  # 限流保护\n')
        f.write('done < all_prompts.jsonl\n')
        f.write('echo "全部完成!"\n')

    os.chmod(curl_script, 0o755)
    print(f"✓ curl脚本: {curl_script}")

    print(f"\n{'='*60}")
    print(f"导出完成！")
    print(f"输出目录: {output_dir}")
    print(f"{'='*60}")
    print(f"文件说明:")
    print(f"  - all_prompts.jsonl: JSONL格式，每行一个prompt")
    print(f"  - batch_*.txt: 分批文本文件，便于人工检查")
    print(f"  - batch_curl.sh: 批量调用脚本")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="导出所有Prompt到文件")
    parser.add_argument(
        "--input", "-i",
        default="data/question_instances_with_retrieval.json",
        help="输入文件路径"
    )
    parser.add_argument(
        "--output", "-o",
        default="data/prompts",
        help="输出目录"
    )
    parser.add_argument(
        "--batch-size", "-b",
        type=int,
        default=10,
        help="每批次的实例数量"
    )

    args = parser.parse_args()

    export_prompts(
        input_file=args.input,
        output_dir=args.output,
        batch_size=args.batch_size
    )


if __name__ == "__main__":
    main()
