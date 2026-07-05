# Tube Planning

[English Version](README.md)

Tube Planning 是一个用于评估公共交通线路扩展方案的 Python 项目。项目从 CSV 边表中读取基准网络和候选扩展方案，将通行时间转换为图容量，根据成本和网络流指标对每个方案进行评估，并输出可复现的排序结果。

## 功能说明

项目将交通网络表示为邻接矩阵，其中站点是节点，线路连接是边。候选扩展方案以额外的边表表示，评估时会与基准网络合并，形成新的候选网络。

评估流程结合两类指标。成本指标根据固定的建设和运营成本配置，判断方案是否满足预算约束。性能指标使用 BFS 和 Edmonds-Karp 最大流算法，计算候选方案在指定源点和汇点之间带来的容量变化，并支持多源点、多汇点以及充足流场景。

项目提供三种使用方式：一键运行的离线展示、可输出 text/CSV/JSON 的命令行评估工具，以及可以在其他脚本中直接调用的 Python API。

## 安装与启动

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

运行一键展示：

```bash
python -m tube_planning.showcase
```

也可以使用项目快捷命令：

```bash
make demo
```

示例输出：

```text
Tube Planning Showcase
======================
Baseline network: 6 stations, 6 connections
Scenario: rank candidate extensions by cost and flow performance

Rank  Proposal                   Score  Essential
----------------------------------------------------
1     central_connector         149.40  pass
2     crosslink                  97.40  pass
```

安装后也可以直接运行：

```bash
tube-planning-showcase
```

## 命令行调用

使用内置离线示例运行完整评估：

```bash
python -m tube_planning.evaluation --network-file examples/baseline_network.csv --format csv examples/costs.fixed-cost examples/criteria.cfile "examples/proposals/*.csv"
```

输出：

```csv
rank,proposal,score,essential_passed
1,central_connector,149.40,True
2,crosslink,97.40,True
```

已安装命令行版本：

```bash
evaluate-proposals --network-file examples/baseline_network.csv --format json examples/costs.fixed-cost examples/criteria.cfile "examples/proposals/*.csv"
```

常用参数：

- `--network-file PATH`：指定本地基准网络 CSV。
- `--format {text,csv,json}`：指定输出格式。
- `-o, --output-file PATH`：将排序结果写入文件。

内置 CLI 场景也可以用快捷命令运行：

```bash
make cli
```

## Python 代码调用示例

下面的代码会读取 `examples/` 中的基准网络、成本配置、指标配置和两个候选方案，并输出排序结果：

```python
from pathlib import Path

from tube_planning.criteria.group import CriteriaGroup
from tube_planning.evaluation import evaluate_proposals, rank_proposals
from tube_planning.networks import Network, Proposal
from tube_planning.utils import adjacency_from_edges, read_edge_csv, read_fixed_costs

root = Path(".")
example_dir = root / "examples"

baseline_rows = read_edge_csv(example_dir / "baseline_network.csv")
baseline = Network(
    adj_mat=adjacency_from_edges(baseline_rows, weights_are_travel_times=True)
)

criteria = CriteriaGroup.from_file(example_dir / "criteria.cfile")
costs = read_fixed_costs(example_dir / "costs.fixed-cost")
proposals = [
    Proposal.from_file(path, name=path.stem)
    for path in sorted((example_dir / "proposals").glob("*.csv"))
]

records = evaluate_proposals(proposals, criteria, baseline, costs)
ranked = rank_proposals(records)

for rank, record in enumerate(ranked, start=1):
    print(rank, record["proposal"].name, round(record["score"], 2))
```

预期结果：

```text
1 central_connector 149.4
2 crosslink 97.4
```

## 输入文件格式

网络和候选方案 CSV 使用边表格式：

```text
station_i,station_j,travel_time_minutes
```

项目会将通行时间转换为容量：

```text
capacity = 60 / travel_time_minutes
```

评价指标写在 JSON `.cfile` 文件中，固定成本写在 JSON `.fixed-cost` 文件中。`examples/` 目录包含一个完整的离线示例。

## 目录结构

```text
tube_planning/        核心代码
  flow.py             流表示与路径增广
  networks/           网络和候选方案图模型
  criteria/           成本与性能评分
  evaluation.py       CLI 排序流程
  showcase.py         离线展示入口
examples/             离线示例数据
tests/                算法和评估流程测试
```

## 测试

```bash
pytest -q
```

快捷命令：

```bash
make test
```
