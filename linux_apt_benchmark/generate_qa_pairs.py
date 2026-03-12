"""
基于召回信息生成问答对
调用大模型API根据召回数据回答问题
"""

import json
import os
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from openai import OpenAI

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ===================== Prompt 定义 =====================

SYSTEM_PROMPT = """你是一名专业的网络安全分析师，擅长分析Linux系统的安全日志和审计数据。
你的任务是根据提供的安全数据回答问题，识别潜在的安全威胁和异常行为。

分析原则：
1. 仔细分析提供的审计事件、安全告警、网络活动等数据
2. 关注异常时间、异常进程、异常文件访问等可疑行为
3. 结合MITRE ATT&CK框架识别攻击技术
4. 给出明确的结论和详细的分析依据
5. 如果数据不足以回答问题，请明确说明

输出要求：
- 提供结构化、专业的分析答案
- 包含关键发现的时间、进程、用户等信息
- 简要解释判断依据和推理过程
- 评估是否为正常业务需求或安全威胁"""

USER_PROMPT_TEMPLATE = """【问题】
{question}

【分析维度】
- 攻击阶段: {attack_stage}
- 安全维度: {dimension}

【召回的安全数据】
{retrieval_content}

请基于以上数据详细回答这个问题。分析应该：
1. 直接回答问题中的每个要点
2. 引用具体的数据记录作为证据
3. 给出明确的结论和判断依据
"""


def format_retrieval_content(retrieval_data: Dict[str, Any]) -> str:
    """格式化召回数据为可读文本"""
    content_parts = []
    summary = retrieval_data.get('summary', {})

    # 审计事件
    if 'audit_events' in summary:
        audit = summary['audit_events']
        content_parts.append(f"\n=== 审计事件 (共 {audit.get('count', 0)} 条) ===")
        samples = audit.get('samples', [])
        for i, sample in enumerate(samples[:30], 1):  # 限制样本数量
            content_parts.append(
                f"[{i}] 时间: {sample.get('timestamp', 'N/A')}, "
                f"PID: {sample.get('pid', 'N/A')}, "
                f"命令: {sample.get('command', 'N/A')}, "
                f"执行文件: {sample.get('exe', 'N/A')}, "
                f"访问文件: {sample.get('file_name', 'N/A')}, "
                f"UID: {sample.get('uid', 'N/A')}, "
                f"CWD: {sample.get('cwd', 'N/A')}, "
                f"PPID: {sample.get('ppid', 'N/A')}, "
                f"会话: {sample.get('session', 'N/A')}"
            )
        if len(samples) > 30:
            content_parts.append(f"... 还有 {len(samples) - 30} 条记录")

    # 安全告警
    if 'security_alerts' in summary:
        alerts = summary['security_alerts']
        content_parts.append(f"\n=== 安全告警 (共 {alerts.get('count', 0)} 条) ===")
        samples = alerts.get('samples', [])
        for i, sample in enumerate(samples[:20], 1):
            content_parts.append(
                f"[{i}] 时间: {sample.get('timestamp', 'N/A')}, "
                f"级别: {sample.get('alert_level', 'N/A')}, "
                f"规则: {sample.get('rule_id', 'N/A')}, "
                f"描述: {sample.get('description', 'N/A')}, "
                f"MITRE技术: {sample.get('mitre_technique', 'N/A')}"
            )
        if len(samples) > 20:
            content_parts.append(f"... 还有 {len(samples) - 20} 条记录")

    # 网络活动
    if 'network_activities' in summary:
        network = summary['network_activities']
        content_parts.append(f"\n=== 网络活动 (共 {network.get('count', 0)} 条) ===")
        samples = network.get('samples', [])
        for i, sample in enumerate(samples[:15], 1):
            content_parts.append(
                f"[{i}] 时间: {sample.get('timestamp', 'N/A')}, "
                f"源IP: {sample.get('src_ip', 'N/A')}, "
                f"源端口: {sample.get('src_port', 'N/A')}, "
                f"源用户: {sample.get('src_user', 'N/A')}, "
                f"目标用户: {sample.get('dst_user', 'N/A')}"
            )
        if len(samples) > 15:
            content_parts.append(f"... 还有 {len(samples) - 15} 条记录")

    # 文件完整性事件
    if 'file_integrity_events' in summary:
        fim = summary['file_integrity_events']
        content_parts.append(f"\n=== 文件完整性事件 (共 {fim.get('count', 0)} 条) ===")
        samples = fim.get('samples', [])
        for i, sample in enumerate(samples[:15], 1):
            content_parts.append(
                f"[{i}] 时间: {sample.get('timestamp', 'N/A')}, "
                f"文件: {sample.get('file_path', 'N/A')}, "
                f"事件类型: {sample.get('event_type', 'N/A')}, "
                f"用户: {sample.get('user', 'N/A')}"
            )
        if len(samples) > 15:
            content_parts.append(f"... 还有 {len(samples) - 15} 条记录")

    return "\n".join(content_parts)


def create_openai_client() -> OpenAI:
    """创建OpenAI客户端"""
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("环境变量 DASHSCOPE_API_KEY 未设置")

    return OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )


def call_llm(
    client: OpenAI,
    system_prompt: str,
    user_prompt: str,
    model: str = "qwen3.5-flash ",
    max_retries: int = 3
) -> Optional[str]:
    """调用大模型API生成答案"""

    for attempt in range(max_retries):
        try:
            logger.info(f"调用LLM (尝试 {attempt + 1}/{max_retries})...")

            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                extra_body={"enable_search": True},
                max_tokens=8192,
                stream=False
            )

            result = completion.choices[0].message.content
            logger.info(f"回答完成，长度: {len(result)} 字符")
            return result

        except Exception as e:
            logger.error(f"生成过程中出现错误: {str(e)}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 指数退避
                logger.info(f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
            else:
                logger.error("已达到最大重试次数，放弃生成")
                return None

    return None


def process_single_instance(
    client: OpenAI,
    instance_data: Dict[str, Any],
    model: str = "qwen3-max"
) -> Dict[str, Any]:
    """处理单个实例，生成问答对"""

    instance = instance_data['instance']
    retrieval = instance_data['retrieval']

    instance_id = instance['instance_id']
    question = instance['question']
    dimension = instance.get('dimension', 'N/A')
    attack_stage = instance.get('attack_stage', 'N/A')

    logger.info(f"\n处理实例: {instance_id}")
    logger.info(f"问题: {question[:80]}...")

    # 格式化召回内容
    retrieval_content = format_retrieval_content(retrieval)

    # 构造用户prompt
    user_prompt = USER_PROMPT_TEMPLATE.format(
        question=question,
        attack_stage=attack_stage,
        dimension=dimension,
        retrieval_content=retrieval_content
    )

    input_length = len(user_prompt)
    logger.info(f"Prompt长度: {input_length} 字符")

    # 调用LLM生成答案
    answer = call_llm(client, SYSTEM_PROMPT, user_prompt, model)

    output_length = len(answer) if answer else 0
    logger.info(f"输出长度: {output_length} 字符")

    # 构造结果
    result = {
        "instance_id": instance_id,
        "question_id": instance['question_id'],
        "question": question,
        "dimension": dimension,
        "attack_stage": attack_stage,
        "answer": answer if answer else "",
        "input_length": input_length,
        "output_length": output_length,
        "generation_status": "success" if answer else "failed",
        # "retrieval_task": retrieval.get('retrieval_task', 'N/A'),
        # "model": model,
        # "timestamp": datetime.now().isoformat()
    }

    return result


def generate_qa_pairs(
    input_file: str = "data/question_instances_with_retrieval.json",
    output_file: str = "data/question_answer_pairs.json",
    model: str = "qwen3-max",
    start_idx: int = 0,
    end_idx: Optional[int] = None,
    save_interval: int = 10
) -> List[Dict[str, Any]]:
    """
    批量生成问答对

    Args:
        input_file: 输入文件路径
        output_file: 输出文件路径
        model: 模型名称
        start_idx: 开始索引（用于断点续传）
        end_idx: 结束索引（None表示到最后）
        save_interval: 每处理多少个实例保存一次
    """

    # 创建客户端
    client = create_openai_client()

    # 加载数据
    logger.info(f"加载数据: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        all_data = json.load(f)

    total = len(all_data)
    logger.info(f"总共 {total} 个实例")

    # 确定处理范围
    end_idx = end_idx if end_idx is not None else total
    data_to_process = all_data[start_idx:end_idx]
    logger.info(f"将处理第 {start_idx} 到 {end_idx-1} 个实例 (共 {len(data_to_process)} 个)")

    # 加载已有结果（断点续传）
    results = []
    if os.path.exists(output_file) and start_idx > 0:
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                results = json.load(f)
            logger.info(f"已加载 {len(results)} 条已有结果")
        except Exception as e:
            logger.warning(f"加载已有结果失败: {e}")

    # 处理每个实例
    for i, instance_data in enumerate(data_to_process, start=start_idx):
        logger.info(f"\n{'='*60}")
        logger.info(f"进度: {i+1}/{total} ({(i+1)/total*100:.1f}%)")
        logger.info(f"{'='*60}")

        try:
            result = process_single_instance(client, instance_data, model)
            results.append(result)

            # 定期保存
            if (i + 1) % save_interval == 0:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                logger.info(f"中间结果已保存到: {output_file} ({len(results)} 条)")

            # 防止API限流，添加小延迟
            time.sleep(0.5)

        except Exception as e:
            logger.error(f"处理实例 {instance_data['instance']['instance_id']} 时出错: {e}")
            # 记录失败信息
            results.append({
                "instance_id": instance_data['instance']['instance_id'],
                "question_id": instance_data['instance']['question_id'],
                "question": instance_data['instance']['question'],
                "dimension": instance_data['instance'].get('dimension', 'N/A'),
                "attack_stage": instance_data['instance'].get('attack_stage', 'N/A'),
                "answer": "",
                "input_length": 0,
                "output_length": 0,
                "generation_status": "error",
                "error_message": str(e),
                "model": model,
                "timestamp": datetime.now().isoformat()
            })

    # 最终保存
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    logger.info(f"\n{'='*60}")
    logger.info(f"处理完成！共生成 {len(results)} 个问答对")
    logger.info(f"结果保存到: {output_file}")
    logger.info(f"{'='*60}")

    # 统计成功/失败
    success_count = sum(1 for r in results if r.get('generation_status') == 'success')
    failed_count = sum(1 for r in results if r.get('generation_status') != 'success')
    logger.info(f"成功: {success_count}, 失败: {failed_count}")

    return results


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="基于召回信息生成问答对")
    parser.add_argument(
        "--input", "-i",
        default="data/question_instances_with_retrieval.json",
        help="输入文件路径 (JSON格式，包含问题和召回数据)"
    )
    parser.add_argument(
        "--output", "-o",
        default="data/question_answer_pairs.json",
        help="输出文件路径"
    )
    parser.add_argument(
        "--model", "-m",
        default="qwen3-max",
        help="模型名称 (默认: qwen3-max)"
    )
    parser.add_argument(
        "--start", "-s",
        type=int,
        default=0,
        help="开始索引 (用于断点续传)"
    )
    parser.add_argument(
        "--end", "-e",
        type=int,
        default=None,
        help="结束索引 (默认处理到最后)"
    )
    parser.add_argument(
        "--interval", "-n",
        type=int,
        default=10,
        help="每处理多少个实例保存一次 (默认: 10)"
    )

    args = parser.parse_args()

    # 检查环境变量
    if not os.getenv("DASHSCOPE_API_KEY"):
        logger.error("错误: 环境变量 DASHSCOPE_API_KEY 未设置！")
        logger.error("请先设置环境变量: export DASHSCOPE_API_KEY='your-api-key'")
        return

    # 生成问答对
    generate_qa_pairs(
        input_file=args.input,
        output_file=args.output,
        model=args.model,
        start_idx=args.start,
        end_idx=args.end,
        save_interval=args.interval
    )


if __name__ == "__main__":
    main()
