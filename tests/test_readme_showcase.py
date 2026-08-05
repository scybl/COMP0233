from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]


def test_readme_has_showcase_sections_and_english_companion():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    english = (ROOT / "README_en.md").read_text(encoding="utf-8")

    assert "## 简历亮点" in readme
    assert "## 复现边界" in readme
    assert "## Resume Highlights" in english
    assert "## Reproducibility Boundaries" in english


def test_showcase_preview_asset_exists_and_is_valid_svg():
    image = ROOT / "docs" / "images" / "showcase-preview.svg"
    assert image.is_file()
    ET.parse(image)
