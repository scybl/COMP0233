# 示例数据

[English](README_en.md)

这个目录提供了一个完整的离线示例，用于展示如何评估公共交通线路扩展方案。示例不依赖外部 API 或实时交通数据。

## 场景

基准网络包含 6 个站点和 6 条既有连接。目标是在两个候选扩展方案之间排序，综合考虑建设成本、运营成本和跨城流量能力。

候选方案：

- `central_connector`：增加两条较短的内部连接，改善网络中部的路径选择。
- `crosslink`：增加端到端捷径和一条局部连接，在本示例中的综合得分较低。

期望排序：

```text
1 central_connector 149.40
2 crosslink          97.40
```

## 文件

- `baseline_network.csv`：当前网络边表。
- `proposals/*.csv`：候选扩展方案边表。
- `criteria.cfile`：必要和期望评估指标。
- `costs.fixed-cost`：固定建设和运营成本配置。

## 运行

```bash
make demo
```

也可以直接运行 CLI 示例：

```bash
make cli
```

等价的 Python 模块命令：

```bash
python -m tube_planning.evaluation --network-file examples/baseline_network.csv --format csv examples/costs.fixed-cost examples/criteria.cfile "examples/proposals/*.csv"
```

## CSV 格式

网络和候选方案文件使用边表格式：

```text
station_i,station_j,travel_time_minutes
```

通行时间会转换为容量：

```text
capacity = 60 / travel_time_minutes
```
