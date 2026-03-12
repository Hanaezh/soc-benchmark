



## 设计理念
既保持与原数据的一致性，又符合APT攻击场景的特点。
1. **与原benchmark对齐**：包含IP情报、事件日志、访问日志三大核心组件
2. **APT场景适配**：突出文件操作、进程执行、横向移动等APT特征
3. **支持IOC查询**：通过threat_intelligence和ioc_associations表支持复杂的IOC溯源问题
4. **时间序列分析**：所有表都包含timestamp，支持攻击链时序分析
5. **合规性考虑**：保留MITRE ATT&CK、合规框架等字段


"我们的方法针对IOC溯源问答，而非特定数据源。原benchmark基于网络流量+IP情报验证了流量场景下的有效性；新增的Linux-APT-2024 benchmark基于主机审计+文件/进程IOC，验证了主机场景下的适用性。两者数据模态不同（网络包 vs 系统调用），但面对的核心问题一致：多源数据关联、时序溯源、威胁狩猎。"


# 补充在附录中使用
Linux-APT-2024 是专注 Linux 系统高级持续性威胁（APT）行为的开源数据集，模拟了 APT41、APT28 等典型组织的攻击链。为在该数据集上快速验证本文方法，我们根据数据特点设计了数据库 schema 与专家知识条目，schema 共包含 7 个表、126 个字段，专家知识共 21 条。
我们选取子集 Linux-APT-2024-04-06 (January)，并将共 10619 条数据转换后写入数据库。此外，我们人工构建了 26 个问题模板，并采用第 \ref{sec:qa-pair-synthesis} 节的方法扩展得到 260 个问答样例，其中以任务类型为基准分层抽样60 个作为 few-shot 示例库、200 个作为测试样例。原始数据集与转换后的数据均可通过第 \ref{sec:data availability} 节提供的开源链接获取。

Linux-APT-2024 is an open-source dataset focused on advanced persistent threat (APT) behaviors targeting Linux systems, simulating attack chains from typical organizations such as APT41 and APT28. To rapidly validate the methods presented in this paper on this dataset, we designed a database schema and expert knowledge entries based on the data characteristics. The schema comprises 7 tables and 126 fields, while the expert knowledge includes 21 entries.
We selected the subset Linux-APT-2024-04-06 (January) and converted its 10,619 records for insertion into the database. Additionally, we manually constructed 26 question templates and expanded them into 260 question-answer pairs using the method described in Section \ref{sec:qa-pair-synthesis}. Among these, 60 were stratified by task type for the few-shot example set, and 200 were reserved as test examples. Both the original and converted datasets are available via the open-source links provided in Section \ref{sec:data availability}.
