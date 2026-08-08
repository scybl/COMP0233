# TubePlanner

[English](README_en.md)

TubePlanner 是一个基于 TfL 网络数据的公共交通线路规划评估工具。项目使用 UCL RSE Tube Planning Web Service 的本地快照，将伦敦地铁、轻轨和相关轨道交通站点连接转换为带权图，并把站间通行时间换算为网络容量。

它用于比较候选线路扩展方案对乘坐路径选择和跨区域通行能力的影响：给定基准网络、候选扩展方案、成本配置和评价条件后，程序会计算每个方案的最大流收益与成本表现，并输出可复现的排序结果。

## 功能说明

- 将站点和线路转换为图结构，并把通行时间换算为容量。
- 使用 BFS 和 Edmonds-Karp 最大流算法评估候选方案的容量收益。
- 支持必要条件、期望条件和固定成本配置。
- 支持 text、CSV、JSON 三种输出格式。

## 结果展示

| 项目 | 结果 |
| --- | --- |
| UCL 快照网络 | 446 个站点，535 条等价连接 |
| 候选方案 | 7 个 |
| 成本日期 | 2026-07-01 |
| 排名第一方案 | `thameslink` |
| 输出文件 | `data/ucl_snapshot/results/ranking_2026-07-01.csv` |

示例输出：

```csv
rank,proposal,score,essential_passed
1,thameslink,223.32,True
2,weaving_cross,198.75,True
3,holborn_star,197.84,True
```

## 快速上手

```bash
bash scripts/setup_env.sh
bash scripts/run_ucl_snapshot.sh
```

复用已有 conda 环境：

```bash
conda run -n codex_python bash scripts/run_ucl_snapshot.sh
```

运行小型离线示例：

```bash
bash scripts/run_demo.sh
```

直接运行 UCL 快照 CLI：

```bash
python -m tube_planning.evaluation --network-file data/ucl_snapshot/baseline_network.csv --format csv data/ucl_snapshot/costs/2026-07-01.fixed-cost data/ucl_snapshot/demo_criteria.cfile "data/ucl_snapshot/proposals/*.csv"
```

更多运行例子：

```bash
make cli
make ucl-demo
make results
python -m tube_planning.evaluation --network-file examples/baseline_network.csv --format json examples/costs.fixed-cost examples/criteria.cfile "examples/proposals/*.csv"
```

对照结果文件：

- `examples/results/demo_ranking.csv`
- `examples/results/demo_ranking.json`
- `data/ucl_snapshot/results/ranking_2026-07-01.csv`

## 环境要求

- Python 3.10+
- 依赖见 `requirements.txt`

## 数据说明

- `data/ucl_snapshot/` 是 UCL RSE Tube Planning Web Service 的本地快照。
- 快照包含线路、站点索引、候选方案和 2026 年成本表；服务说明称其结合了 2017 年数据和较新的 TfL API 衍生来源，候选扩展方案为模拟方案。
- `examples/` 是不依赖外部服务的小型合成示例。
- 如需刷新快照，运行 `python scripts/cache_ucl_snapshot.py`。
- 如需联网模式，设置 `TUBE_PLANNING_WEB_SERVICE`，并使用 `--live-costings` 或 `--routes`。

## 目录结构

```text
tube_planning/        核心代码
data/ucl_snapshot/    UCL 服务本地快照
data/ucl_snapshot/results/  UCL 快照输出样例
examples/             示例数据
examples/results/     小型示例输出样例
tests/                测试
scripts/              环境配置和运行脚本
```

## 测试

```bash
pytest -q
```
