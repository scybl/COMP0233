# TubePlanner

[English](README_en.md)

TubePlanner 是一个公共交通网络扩展评估工具。它从 CSV 边表读取基准网络和候选扩展方案，结合成本约束与最大流指标，对方案进行排序。

![TubePlanner 排序结果预览](docs/images/showcase-preview.svg)

## 功能说明

- 将站点和线路转换为图结构，并把通行时间换算为容量。
- 使用 BFS 和 Edmonds-Karp 最大流算法评估候选方案的容量收益。
- 支持必要条件、期望条件和固定成本配置。
- 支持 text、CSV、JSON 三种输出格式。

## 结果展示

| 项目 | 结果 |
| --- | --- |
| 示例网络 | 6 个站点，6 条连接 |
| 排名第一方案 | `central_connector` |
| 方案得分 | 149.40 |
| 必要条件 | pass |

示例输出：

```text
Rank  Proposal                   Score  Essential
----------------------------------------------------
1     central_connector         149.40  pass
2     crosslink                  97.40  pass
```

## 快速上手

```bash
bash scripts/setup_env.sh
bash scripts/run_demo.sh
```

复用已有 conda 环境：

```bash
conda run -n codex_python bash scripts/run_demo.sh
```

运行 CLI：

```bash
python -m tube_planning.evaluation --network-file examples/baseline_network.csv --format csv examples/costs.fixed-cost examples/criteria.cfile "examples/proposals/*.csv"
```

## 环境要求

- Python 3.10+
- 依赖见 `requirements.txt`

## 数据说明

- `examples/baseline_network.csv` 是基准网络。
- `examples/proposals/` 存放候选扩展方案。
- `examples/costs.fixed-cost` 和 `examples/criteria.cfile` 存放成本与评价配置。

## 目录结构

```text
tube_planning/        核心代码
examples/             示例数据
tests/                测试
scripts/              环境配置和运行脚本
docs/images/          README 结果图
```

## 测试

```bash
pytest -q
```
