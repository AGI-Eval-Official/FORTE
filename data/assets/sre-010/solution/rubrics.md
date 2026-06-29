# Rubrics

> **通过标准：所有 rubric 均须满足，该任务才算通过。任一 rubric 不通过，则整体判定为 FAIL。**

```path
```

```json
[
  {
    "id": "01",
    "content": "根因分析必须识别出双十一大促零点 QPS 激增（查询 QPS 从 600/s 激增至 4800/s，写入 QPS 从 400/s 激增至 3200/s，均激增约 8 倍）是本次集群读写性能瓶颈的直接触发因素，并建立完整的因果链。必须明确指出：(1) 日志片段 1 的集群配置显示，8 个 data 节点均为 vm-sata-16c-32g 机型，使用 SATA 磁盘，IO 性能相对较低，在大促流量冲击下磁盘 IO 成为瓶颈（日志片段 9 中 disk.io.util 全部节点均达到 97%~99%，远超 80% 阈值）；(2) 日志片段 3、4、6 中，es-node-04、es-node-06、es-node-08 在 00:00 大促开始后相继出现 Young GC 频率激增（collection_count 从正常的 2~3 次/5s 升至 8~11 次/5s）、Old GC 时间延长（duration 从 3.4s 升至 8.1s，collection_count 达到 3~4 次/min，超过阈值 1 次/min），说明 QPS 激增导致 JVM 堆内存压力持续升高（heap_used_percent 达到 87%~91%）；(3) 日志片段 3、4、6、7、8 中的慢查询日志显示，多个节点出现 9.8s~14.2s 的超长查询耗时，其中 user-activity-2024-11 索引存在 from=5000 的深度分页查询（agg 聚合 + 深度分页双重叠加），item-search-2024-11 索引存在多层 agg 聚合查询（terms + range 聚合），这类重查询在高 QPS 下进一步加剧了 CPU 和内存压力；(4) 日志片段 9 的诊断数据显示，8 个 data 节点 CPU 全部达到 93%~97%，线程池 write 和 search 队列均已打满（queue=1000/500），累计 rejected 数量达到数万次，集群进入 YELLOW 状态，48 个副本分片处于 UNASSIGNED 状态（原因为 throttled，磁盘使用率超过 85% 水位线导致副本分配被限流）。以下为日志中存在的干扰项，根因分析不应将其列为本次故障的根因或主要原因：日志片段 2 中 es-node-01 出现的 master 节点心跳超时重试（timeout waiting for response，均已 retry 成功），属于 data 节点高负载导致的响应延迟，master 本身运行正常，不是根因；日志片段 2 中的 License 即将过期警告（license will expire in 14 days），与本次性能故障无关；日志片段 5 中 es-node-07 的 snapshot 失败，系高 IO 负载下锁竞争导致的备份任务失败，属于故障的次生影响，不是根因；日志片段 7 中 es-node-09 的 CircuitBreakingException 触发后立即自动 reset，属于高负载下的短暂保护性熔断，不是导致集群劣化的根因；日志片段 8 中 es-node-10 的 ShardLockObtainFailedException 在 retry 后成功，属于高 IO 下的锁竞争瞬时失败，不是根因。判定为'不通过'的情况：仅将问题归因为节点故障或网络问题，未识别 QPS 激增与计算资源不足的因果关系；未提及 SATA 磁盘 IO 瓶颈；未分析 GC 恶化过程；未提及深度分页或重聚合查询对资源的额外消耗；未提及线程池打满和副本 UNASSIGNED 现象；将 master 心跳超时、License 过期、snapshot 失败、circuit breaker 短暂触发或 shard lock 重试成功等干扰项误判为本次故障的根因。",
    "weight": 1
  },
  {
    "id": "02",
    "content": "紧急止损方案必须覆盖两个并行推进的层面，不要求严格的先后顺序，但两个层面均须提及：【ES 侧可直接执行的 API 操作】包含以下内容：(1) 对于 48 个 UNASSIGNED 副本分片，需开启分片分配并触发重试：PUT /_cluster/settings {\"transient\": {\"cluster.routing.allocation.enable\": \"all\"}}，以及 POST /_cluster/reroute?retry_failed=true；(2) 调大 refresh_interval 降低写入 IO 频率，如 PUT /index_name/_settings {\"index.refresh_interval\": \"30s\"}；(3) 清理 fielddata 缓存释放堆内存，如 POST /_cache/clear?fielddata=true；以上 API 命令中节点 IP 须使用日志中出现的实际地址（如 10.1.1.1:9200）。【需协调业务方执行的客户端降级措施】包含以下内容：(1) 立即对查询和写入请求限流，将 QPS 降至集群可承受范围（参考正常基线 600/s 查询、400/s 写入）；(2) 立即停止或熔断深度分页查询（from=5000）和多层聚合查询，降低单次查询的 CPU 和内存消耗。判定为'不通过'的情况：未给出任何可执行的 ES 侧 API 命令；未提及副本分片 UNASSIGNED 的处理方案；未提及客户端限流或业务降级措施；未提及立即停止或熔断深度分页和重聚合查询；仅建议重启节点而未分析根因。",
    "weight": 1
  }
]
```
