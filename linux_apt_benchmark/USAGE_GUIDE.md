# 问题实例化与召回系统使用指南

## 快速开始

### 步骤 1: 生成第一批实例（供确认）
```bash
python run_instance_generation.py
```

### 步骤 2: 查看生成的实例
```bash
python view_instances.py summary
python view_instances.py question 1
```

### 步骤 3: 测试召回功能
```bash
python test_recall.py
```

### 步骤 4: 批量生成实例
```bash
python batch_generate_instances.py
```

## 文件说明

### 核心脚本
- `run_instance_generation.py` - 主流程（生成1个实例/问题）
- `batch_generate_instances.py` - 批量生成（10个实例/问题）
- `test_recall.py` - 测试召回功能
- `view_instances.py` - 查看实例工具
- `save_retrieval_results.py` - 保存召回结果

### 输出文件
- `question_instance_seeds.json` - 种子数据
- `question_instances.json` - 问题实例
- `question_instances_with_retrieval.json` - 带召回结果的完整数据

## 常用命令

```bash
# 查看所有实例统计
python view_instances.py summary

# 查看特定问题的实例
python view_instances.py question 1

# 测试召回功能
python test_recall.py

# 批量生成10个实例/问题
python batch_generate_instances.py

# 保存所有召回结果
python save_retrieval_results.py
```

## 问题分类

### 主机类（1-11）- recall_host_scope
凭据访问、网络连接、告警分析、SSH密钥、侦察命令等

### 网络类（12-16）- recall_by_src_ip
连接统计、用户关联、活动模式、横向扩散、端口扫描

### 文件类（17-21）- recall_by_file_hash  
文件追踪、生命周期、权限变更、哈希变更、操作统计

### 用户类（22-25）- recall_by_uid
命令审计、文件访问、进程统计、权限提升

### 其他（7, 26）
规则触发、源用户活动

详细文档请参考 README_instance_generation.md
