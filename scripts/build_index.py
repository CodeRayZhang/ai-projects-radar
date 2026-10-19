"""Rebuild the archive from dated Markdown files (Python 3.9+, no dependencies)."""
import argparse
from datetime import date
import html
from pathlib import Path
import re

BEGIN = "<!-- archive:start -->"
END = "<!-- archive:end -->"

def entries(root):
    result = []
    for path in root.glob("????-??/*.md"):
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", path.stem):
            raise ValueError(f"Invalid dated filename: {path}")
        day = date.fromisoformat(path.stem)
        if path.parent.name != day.strftime("%Y-%m"):
            raise ValueError(f"Date/directory mismatch: {path}")
        content = path.read_text(encoding="utf-8")
        if not content.strip():
            raise ValueError(f"Empty article: {path}")
        # Digest cover = first numbered story; radar cover = first H1.
        cover = re.search(r"^\*\*1[.、]\s*(.*?)\*\*\s*$", content, re.M)
        heading = re.search(r"^#\s+(.+)$", content, re.M)
        title = (heading or cover).group(1) if (heading or cover) else path.stem
        if title.startswith("[") and title.endswith("]"):
            title = title[1:-1]
        title = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", title)
        title = html.escape(title).replace("|", "&#124;").replace("\n", " ")
        result.append((day, path.relative_to(root).as_posix(), title))
    if not result:
        raise ValueError("No dated articles found")
    return sorted(result, reverse=True)

def render(root, readme):
    if readme.count(BEGIN) != 1 or readme.count(END) != 1:
        raise ValueError("README must contain exactly one archive marker pair")
    before, rest = readme.split(BEGIN)
    _, after = rest.split(END)
    rows = entries(root)
    day, path, _ = rows[0]
    block = f"\n\n## 最近一期\n\n[阅读 {day.isoformat()}](./{path}) · 共 **{len(rows)}** 期存档\n\n"
    block += "## 全部存档\n\n| 日期 | 标题（来自文章原文） |\n|---|---|\n"
    block += "".join(f"| [{d.isoformat()}](./{p}) | {t} |\n" for d, p, t in rows)
    return before + BEGIN + block + "\n" + END + after

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if README needs regeneration")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    path = root / "README.md"
    current = path.read_text(encoding="utf-8")
    updated = render(root, current)
    if args.check:
        if current != updated:
            parser.exit(1, "README index is stale; run python3 scripts/build_index.py\n")
    else:
        path.write_text(updated, encoding="utf-8")

if __name__ == "__main__":
    main()
