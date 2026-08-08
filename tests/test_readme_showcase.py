from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_readme_has_showcase_sections_and_english_companion():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    english = (ROOT / "README_en.md").read_text(encoding="utf-8")

    assert "## 功能说明" in readme
    assert "## 结果展示" in readme
    assert "## 快速上手" in readme
    assert "## 环境要求" in readme
    assert "## 数据说明" in readme
    assert "## Results" in english
    assert "## Features" in english
    assert "## Quick Start" in english
    assert "## Requirements" in english
    assert "## Data Notes" in english


def test_readme_uses_reproducible_text_results_not_static_image():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    english = (ROOT / "README_en.md").read_text(encoding="utf-8")

    assert "showcase-preview.svg" not in readme
    assert "showcase-preview.svg" not in english
    assert "![TubePlanner" not in readme
    assert "![TubePlanner" not in english
    assert "data/ucl_snapshot/results/ranking_2026-07-01.csv" in readme
    assert "data/ucl_snapshot/results/ranking_2026-07-01.csv" in english
    assert "data/ucl_snapshot/results/route_highgate_waterloo.txt" in readme
    assert "data/ucl_snapshot/results/route_highgate_waterloo.txt" in english
    assert "Dijkstra" in readme
    assert "Dijkstra" in english
