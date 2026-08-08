# TubePlanner

[English](README_en.md)

TubePlanner 是一个基于 TfL 网络数据的公共交通线路规划评估工具。项目使用 UCL RSE Tube Planning Web Service 的本地快照；该服务整合 2017 年线路数据和较新的 TfL API 衍生来源，并包含模拟候选扩展方案与成本数据。

项目将伦敦地铁、轻轨和相关轨道交通站点连接转换为带权图，用于估算站点间最佳路线、比较候选扩展方案对最短通行时间和跨区域通行能力的影响。当前重点是离线规划评估，不提供实时拥堵或实时换乘信息。

## 功能说明

- 将站点和线路转换为图结构，支持通行时间和网络容量两种权重语义。
- 使用 BFS 和 Edmonds-Karp 最大流算法评估候选方案的容量收益。
- 使用 Dijkstra 算法计算站点间估计最短通行路线，并可叠加候选扩展边对比时间变化。
- 支持必要条件、期望条件和固定成本配置。
- 支持 text、CSV、JSON 三种输出格式。

## 结果展示

| 项目 | 结果 |
| --- | --- |
| UCL 快照网络 | 446 个站点，535 条等价连接 |
| 候选方案 | 7 个 |
| 成本日期 | 2026-07-01 |
| 排名第一方案 | `thameslink` |
| 最短路示例 | `Highgate -> Waterloo` |
| 基准最短通行时间 | `22.00 minutes` |
| 叠加 `goodrum` 后 | `15.00 minutes` |
| 排名输出 | `data/ucl_snapshot/results/ranking_2026-07-01.csv` |
| 路线输出 | `data/ucl_snapshot/results/route_highgate_waterloo.txt` |

方案排序示例：

```csv
rank,proposal,score,essential_passed
1,thameslink,223.32,True
2,weaving_cross,198.75,True
3,holborn_star,197.84,True
```

路线结果示例：

```text
Source: Highgate (123)
Target: Waterloo (271)
Estimated travel time: 22.00 minutes
Route:
Highgate -> Archway -> Tufnell park -> Kentish town -> Camden town -> Euston -> Warren street -> Goodge street -> Tottenham court road -> Leicester square -> Charing cross -> Embankment -> Waterloo
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

运行最短路线示例：

```bash
python -m tube_planning.routing --source Highgate --target Waterloo
python -m tube_planning.routing --source Highgate --target Waterloo --extra-edges data/ucl_snapshot/proposals/goodrum.csv
```

直接运行 UCL 快照 CLI：

```bash
python -m tube_planning.evaluation --network-file data/ucl_snapshot/baseline_network.csv --format csv data/ucl_snapshot/costs/2026-07-01.fixed-cost data/ucl_snapshot/demo_criteria.cfile "data/ucl_snapshot/proposals/*.csv"
```

更多运行例子：

```bash
make cli
make ucl-demo
make route-demo
make results
python -m tube_planning.evaluation --network-file examples/baseline_network.csv --format json examples/costs.fixed-cost examples/criteria.cfile "examples/proposals/*.csv"
```

对照结果文件：

- `examples/results/demo_ranking.csv`
- `examples/results/demo_ranking.json`
- `data/ucl_snapshot/results/ranking_2026-07-01.csv`
- `data/ucl_snapshot/results/route_highgate_waterloo.txt`
- `data/ucl_snapshot/results/route_highgate_waterloo_goodrum.txt`

## 环境要求

- Python 3.10+
- 依赖见 `requirements.txt`

## 数据说明

- `data/ucl_snapshot/` 是 UCL RSE Tube Planning Web Service 的本地快照。
- 快照包含线路、站点索引、候选方案和 2026 年成本表；服务说明称其结合了 2017 年数据和较新的 TfL API 衍生来源，候选扩展方案和成本数据为模拟数据。
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
