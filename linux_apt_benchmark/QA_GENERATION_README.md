# 问答对生成工具

基于召回的安全数据，调用大模型API生成问答对。

## 文件说明

- `generate_qa_pairs.py` - 主程序：批量生成问答对
- `test_single_qa.py` - 测试程序：单实例测试和Prompt预览
- `data/question_instances_with_retrieval.json` - 输入数据（260个问题及召回信息）
- `data/question_answer_pairs.json` - 输出文件（生成的问答对）

## 前置要求

1. 安装依赖:
```bash
pip install openai
```

2. 设置API Key环境变量:
```bash
export DASHSCOPE_API_KEY="your-api-key-here"
```

## 使用方法

### 1. 单实例测试（推荐先测试）

预览Prompt结构（不调用API）:
```bash
cd /data/zhangh/WorkSpace/SecCoRA-CAAI/soc_benchmark/linux_apt_benchmark
python test_single_qa.py preview q1_inst0
```

测试单个实例:
```bash
python test_single_qa.py test q1_inst0
```

### 2. 批量生成问答对

生成全部260个问答对:
```bash
python generate_qa_pairs.py
```

指定参数:
```bash
python generate_qa_pairs.py \
    --input data/question_instances_with_retrieval.json \
    --output data/question_answer_pairs.json \
    --model qwen3-max \
    --start 0 \
    --interval 10
```

断点续传（从第50个实例开始）:
```bash
python generate_qa_pairs.py --start 50
```

只处理前10个实例（测试用）:
```bash
python generate_qa_pairs.py --start 0 --end 10
```

## 参数说明

| 参数 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| `--input` | `-i` | `data/question_instances_with_retrieval.json` | 输入文件路径 |
| `--output` | `-o` | `data/question_answer_pairs.json` | 输出文件路径 |
| `--model` | `-m` | `qwen3-max` | 模型名称 |
| `--start` | `-s` | `0` | 开始索引（用于断点续传） |
| `--end` | `-e` | `None` | 结束索引（None表示处理到最后） |
| `--interval` | `-n` | `10` | 每处理多少个实例保存一次 |

## 输出格式

生成的 `question_answer_pairs.json` 格式如下:

```json
[
  {
    "instance_id": "q1_inst0",
    "question_id": 1,
    "question": "主机004的敏感文件/etc/shadow被访问...",
    "dimension": "凭据访问",
    "attack_stage": "Credential Access",
    "answer": "根据审计数据分析...",
    "generation_status": "success",
    "retrieval_task": "recall_host_scope",
    "model": "qwen3-max",
    "timestamp": "2026-03-12T10:30:00"
  },
  ...
]
```

## Prompt设计

### System Prompt

```
你是一名专业的网络安全分析师，擅长分析Linux系统的安全日志和审计数据...
```

### User Prompt 结构

```
【问题】
{question}

【分析维度】
- 攻击阶段: {attack_stage}
- 安全维度: {dimension}

【召回的安全数据】
=== 审计事件 (共 X 条) ===
[1] 时间: ..., PID: ..., 命令: ..., ...
...

=== 安全告警 (共 X 条) ===
[1] 时间: ..., 级别: ..., 描述: ..., ...
...

请基于以上数据详细回答这个问题...
```

## 模型选择建议

- `qwen3-max` (默认) - 综合能力最强，推荐用于正式生成
- `qwen3-235b-a22b` - 大模型，分析更深入
- `qwen2.5-72b-instruct` - 性价比高

模型可通过 `--model` 参数指定。

## 注意事项

1. **API限流**: 脚本已内置0.5秒延迟，如遇限流会自动重试
2. **断点续传**: 支持从任意位置继续，已生成的结果不会丢失
3. **定期保存**: 默认每10个实例保存一次，避免意外中断丢失全部进度
4. **失败处理**: 失败的实例会记录状态，便于后续单独处理
