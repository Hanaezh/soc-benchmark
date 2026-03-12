# 问题实例化与召回系统

## 系统概述

本系统实现了基于设计文档 `docs/retrieval_schema_design.md` 的问题实例化与召回方案，包含三个核心模块：

1. **示例挖掘模块** (`extract_seeds.py`) - 从数据库提取实例值
2. **召回函数模块** (`recall_functions.py`) - 实现6个召回函数
3. **实例生成模块** (`generate_instances.py`) - 生成问题实例

## 文件结构

```
.
├── extract_seeds.py              # 种子数据提取脚本
├── recall_functions.py           # 召回函数实现
├── generate_instances.py         # 问题实例生成脚本
├── run_instance_generation.py   # 主流程脚本
├── test_recall.py               # 召回功能测试脚本
├── batch_generate_instances.py  # 批量生成脚本
├── question_instance_seeds.json # 提取的种子数据
└── question_instances.json      # 生成的问题实例
```

## 使用流程

### 1. 生成单个实例（供确认）

首次使用，为每个问题生成1个实例供确认：

```bash
python run_instance_generation.py
```

这将：
- 从数据库提取种子数据
- 为26个问题各生成1个实例
- 预览前10个实例
- 生成 `question_instance_seeds.json` 和 `question_instances.json`

### 2. 测试召回功能

验证召回函数是否正常工作：

```bash
python test_recall.py
```

### 3. 批量生成实例

确认实例没有问题后，批量生成10个实例：

```bash
python batch_generate_instances.py
```

或者手动指定数量：

```python
python generate_instances.py  # 修改代码中的 num_instances_per_question 参数
```

## 核心模块说明

### 1. extract_seeds.py

**功能**：从数据库中提取各占位符的实例值

**提取的数据类型**：
- `host_id` - 按审计事件数排序（信息量丰富）
- `uid` - 按活跃度排序
- `src_ip` - 按连接次数排序
- `md5_after` - 按出现次数排序
- `md5_before_after_pairs` - 成对的文件哈希变更
- `rule_id` - 按触发次数排序
- `src_user` - 按活跃度排序
- `alert_level` - 所有告警级别
- `time_ranges` - 数据时间范围和高活跃时段

**输出**：`question_instance_seeds.json`

### 2. recall_functions.py

**功能**：实现6个召回函数，按实体召回多表数据

**召回函数列表**：

| 函数名 | 主参数 | 可选参数 | 支持的问题ID |
|--------|--------|----------|--------------|
| `recall_host_scope` | host_id | start_time, end_time | 1,2,3,4,5,6,8,9,10,11 |
| `recall_by_src_ip` | src_ip | start_time, end_time | 12,13,14,15,16 |
| `recall_by_file_hash` | md5_after | md5_before, start_time, end_time | 17,18,19,20,21 |
| `recall_by_uid` | uid | start_time, end_time | 22,23,24,25 |
| `recall_by_src_user` | src_user | start_time, end_time | 26 |
| `recall_by_rule_id` | rule_id | start_time, end_time | 7 |

**返回格式**：统一的JSON摘要结构

```json
{
  "retrieval_task": "recall_host_scope",
  "params": {"host_id": "004", ...},
  "summary": {
    "audit_events": {"count": N, "samples": [...]},
    "security_alerts": {"count": N, "samples": [...]},
    ...
  },
  "coverage_question_ids": [1, 2, 3, ...]
}
```

### 3. generate_instances.py

**功能**：使用种子数据替换问题模板中的占位符

**实例结构**：

```json
{
  "instance_id": "q1_inst0",
  "question_id": 1,
  "question": "主机004的敏感文件...",
  "dimension": "凭据访问",
  "attack_stage": "Credential Access",
  "metadata": {...},
  "recall_function": "recall_host_scope",
  "recall_params": {"host_id": "004"}
}
```

## 设计特点

### 1. 简洁性
- 代码结构清晰，避免过度复杂的错误处理
- 直接的SQL查询，无过多抽象层

### 2. 信息量优先
- 种子数据按出现频率/活跃度排序
- 优先选择信息量丰富的实体

### 3. 一对多映射
- 一个召回函数支持多个问题
- 减少重复查询，提高效率

### 4. 扩展性
- 新增问题优先映射到已有召回类型
- 必要时再增加新的召回函数

## 数据统计

当前提取的种子数据（基于 `linux_apt_2024_04_06_january.duckdb`）：

- host_id: 3 个
- uid: 3 个
- src_ip: 1 个
- md5_after: 6 个
- md5_before_after_pairs: 3 对
- rule_id: 39 个
- src_user: 2 个
- alert_level: 8 个
- time_ranges: 4 个时间段

## 使用示例

### 手动调用召回函数

```python
from recall_functions import recall_host_scope

# 召回某主机的多表摘要
result = recall_host_scope(
    host_id="004",
    start_time="2024-01-04 17:30:03.224",
    end_time="2024-01-06 10:03:58.529"
)

print(f"审计事件数: {result['summary']['audit_events']['count']}")
print(f"告警数: {result['summary']['security_alerts']['count']}")
```

### 加载和使用实例

```python
import json

# 加载问题实例
with open('question_instances.json', 'r') as f:
    instances = json.load(f)

# 使用实例
for inst in instances:
    print(f"问题: {inst['question']}")
    print(f"召回函数: {inst['recall_function']}")
    print(f"召回参数: {inst['recall_params']}")
```

## 注意事项

1. **数据库路径**：确保 `linux_apt_2024_04_06_january.duckdb` 存在于当前目录
2. **模板文件**：需要 `questions_templates_v3.json` 文件
3. **时间格式**：时间戳格式为 `YYYY-MM-DD HH:MM:SS.mmm`
4. **内存使用**：每个召回函数限制返回100条样本，避免内存溢出

## 常见问题

### Q: 如何增加种子数据数量？

修改 `extract_seeds.py` 中的 `limit_per_type` 参数：

```python
seeds = extract_seeds(limit_per_type=100)  # 默认50
```

### Q: 如何修改每个召回函数返回的样本数量？

修改 `recall_functions.py` 中的 `SAMPLE_LIMIT` 常量：

```python
SAMPLE_LIMIT = 200  # 默认100
```

### Q: 生成的实例不符合预期怎么办？

1. 检查 `question_instance_seeds.json` 中的种子数据是否合理
2. 查看日志输出，确认没有警告或错误
3. 使用 `test_recall.py` 测试召回功能是否正常

## 后续扩展

1. **增加召回函数**：如需支持新的查询模式，在 `recall_functions.py` 中添加新函数
2. **优化查询性能**：可添加数据库索引或使用缓存
3. **支持更多问题模板**：更新 `QUESTION_TO_RECALL` 映射
4. **答案生成**：基于召回结果生成问题答案
