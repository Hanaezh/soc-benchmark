# 如何查看召回结果

## 📊 文件说明

生成的文件包含：

### 1. question_instances.json
- **内容**：问题实例（不含召回数据）
- **大小**：约50KB
- **用途**：查看生成的问题和参数

### 2. question_instances_with_retrieval.json ⭐
- **内容**：问题实例 + 完整召回数据
- **大小**：1.7MB（52,575行）
- **用途**：完整的实例-召回数据集
- **数据量**：26个实例，4567条召回记录

## 🔍 查看方式

### 方式1: 使用查看工具（推荐）

```bash
# 查看整体摘要统计
python view_retrieval_results.py summary

# 查看特定实例的召回结果
python view_retrieval_results.py instance q1_inst0

# 查看某个问题的所有实例
python view_retrieval_results.py question 1

# 导出单个实例到独立文件（方便详细查看）
python view_retrieval_results.py export q1_inst0 q1_result.json
```

### 方式2: 直接打开JSON文件

```bash
# 使用文本编辑器
code question_instances_with_retrieval.json
vim question_instances_with_retrieval.json

# 使用命令行查看
cat question_instances_with_retrieval.json | less
```

### 方式3: 使用Python脚本

```python
import json

# 加载数据
with open('question_instances_with_retrieval.json', 'r') as f:
    results = json.load(f)

# 查看第一个实例
first = results[0]
print(f"问题: {first['instance']['question']}")
print(f"召回数据量: {len(first['retrieval']['summary'])}")

# 遍历所有实例
for result in results:
    instance = result['instance']
    retrieval = result['retrieval']
    print(f"Q{instance['question_id']}: {instance['question'][:50]}...")
```

## 📋 数据结构

每个实例的完整结构：

```json
{
  "instance": {
    "instance_id": "q1_inst0",
    "question_id": 1,
    "question": "主机004的敏感文件...",
    "dimension": "凭据访问",
    "attack_stage": "Credential Access"
  },
  "retrieval": {
    "retrieval_task": "recall_host_scope",
    "params": {
      "host_id": "004",
      "start_time": null,
      "end_time": null
    },
    "summary": {
      "audit_events": {
        "count": 100,
        "samples": [
          {
            "event_id": "...",
            "timestamp": "2024-01-04T17:39:04.183000",
            "pid": 4793,
            "exe": "/usr/bin/dash",
            "command": "sh",
            "uid": 0,
            "file_name": "/bin/sh",
            ...
          }
        ]
      },
      "security_alerts": {
        "count": 100,
        "samples": [...]
      },
      "network_activities": {
        "count": 100,
        "samples": [...]
      },
      "file_integrity_events": {
        "count": 100,
        "samples": [...]
      }
    },
    "coverage_question_ids": [1, 2, 3, 4, 5, 6, 8, 9, 10, 11]
  }
}
```

## 📊 召回数据统计

当前26个实例的召回数据量：

| 数据类型 | 总记录数 |
|---------|---------|
| 审计事件 | 1,400 条 |
| 安全告警 | 1,100 条 |
| 网络活动 | 1,041 条 |
| 文件完整性事件 | 1,026 条 |
| **总计** | **4,567 条** |

平均每个实例召回 **175.7** 条记录。

## 🎯 常用操作示例

### 查看问题1（主机004敏感文件访问）的召回结果

```bash
python view_retrieval_results.py instance q1_inst0
```

输出示例：
```
【问题信息】
问题: 主机004的敏感文件/etc/shadow被访问...
维度: 凭据访问

【召回数据摘要】
audit_events: 100 条记录
security_alerts: 100 条记录
network_activities: 100 条记录
file_integrity_events: 100 条记录
```

### 查看问题12（网络连接统计）的召回结果

```bash
python view_retrieval_results.py instance q12_inst0
```

这个问题召回的是源IP `192.168.217.1` 的网络活动数据。

### 导出特定实例做详细分析

```bash
# 导出问题1的完整召回数据
python view_retrieval_results.py export q1_inst0 q1_full.json

# 导出问题7（规则触发）的召回数据
python view_retrieval_results.py export q7_inst0 q7_full.json

# 导出问题17（文件哈希）的召回数据
python view_retrieval_results.py export q17_inst0 q17_full.json
```

### 按问题类型查看

```bash
# 主机类问题（1-11）
python view_retrieval_results.py question 1
python view_retrieval_results.py question 5

# 网络类问题（12-16）
python view_retrieval_results.py question 12
python view_retrieval_results.py question 14

# 文件类问题（17-21）
python view_retrieval_results.py question 17
python view_retrieval_results.py question 20

# 用户类问题（22-25）
python view_retrieval_results.py question 22
python view_retrieval_results.py question 25
```

## 💡 实用技巧

### 1. 查找特定字段

使用 `jq` 工具：

```bash
# 查看所有问题ID
cat question_instances_with_retrieval.json | jq '.[].instance.question_id'

# 查看某个实例的召回参数
cat question_instances_with_retrieval.json | jq '.[] | select(.instance.instance_id=="q1_inst0") | .retrieval.params'

# 统计各类召回函数的使用次数
cat question_instances_with_retrieval.json | jq '.[].retrieval.retrieval_task' | sort | uniq -c
```

### 2. 提取样本数据

```python
import json

with open('question_instances_with_retrieval.json', 'r') as f:
    results = json.load(f)

# 提取所有审计事件
all_audit_events = []
for result in results:
    if 'audit_events' in result['retrieval']['summary']:
        samples = result['retrieval']['summary']['audit_events']['samples']
        all_audit_events.extend(samples)

print(f"总审计事件数: {len(all_audit_events)}")

# 提取主机004的所有数据
host_004_data = [r for r in results if r['retrieval']['params'].get('host_id') == '004']
print(f"主机004相关问题数: {len(host_004_data)}")
```

### 3. 生成分析报告

```python
import json

with open('question_instances_with_retrieval.json', 'r') as f:
    results = json.load(f)

# 按维度统计
dimensions = {}
for result in results:
    dim = result['instance']['dimension']
    dimensions[dim] = dimensions.get(dim, 0) + 1

print("按安全维度统计:")
for dim, count in sorted(dimensions.items(), key=lambda x: x[1], reverse=True):
    print(f"  {dim}: {count} 个问题")
```

## 📁 输出文件清单

执行召回后生成的文件：

```
question_instances_with_retrieval.json    # 完整数据（1.7MB）
q1_inst0_full.json                       # 单个实例导出示例
q7_inst0_full.json                       # 单个实例导出示例
...
```

## ❓ 常见问题

### Q: 文件太大，打不开怎么办？

使用查看工具：
```bash
python view_retrieval_results.py instance q1_inst0
```

或导出单个实例：
```bash
python view_retrieval_results.py export q1_inst0 q1.json
```

### Q: 如何只看召回参数不看数据？

查看 `question_instances.json`（不含召回数据，只有50KB）。

### Q: 如何验证召回结果的正确性？

```bash
# 测试召回功能
python test_recall.py

# 手动验证某个实例
python -c "
from recall_functions import recall_host_scope
result = recall_host_scope('004')
print(f'审计事件: {result[\"summary\"][\"audit_events\"][\"count\"]}条')
"
```

### Q: 如何批量导出所有实例？

```python
import json

with open('question_instances_with_retrieval.json', 'r') as f:
    results = json.load(f)

for result in results:
    instance_id = result['instance']['instance_id']
    filename = f"instances/{instance_id}.json"
    with open(filename, 'w', encoding='utf-8') as out:
        json.dump(result, out, indent=2, ensure_ascii=False)
```

## 🚀 下一步

1. **分析召回质量**：检查召回的数据是否包含回答问题所需的信息
2. **生成答案**：基于召回结果生成问题答案
3. **批量生成**：如果质量OK，运行 `python batch_generate_instances.py` 生成更多实例
4. **评估优化**：根据使用情况优化召回策略和数据量

## 📖 相关文档

- `README_instance_generation.md` - 系统详细说明
- `USAGE_GUIDE.md` - 快速使用指南
- `docs/retrieval_schema_design.md` - 设计文档
