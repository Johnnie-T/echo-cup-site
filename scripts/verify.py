#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""构建自检：确认 dist/ 页面齐全、链接都能落到真实文件上。

用法：
    python scripts/verify.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
DATA_FILE = ROOT / "data" / "works.json"


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):
            pass

    if not DIST.is_dir():
        print("× 还没有 dist/，先运行 python scripts/build.py", file=sys.stderr)
        return 1

    works = json.loads(DATA_FILE.read_text(encoding="utf-8"))["works"]
    problems: list[str] = []

    index = DIST / "index.html"
    if not index.is_file():
        problems.append("缺少 dist/index.html")
    else:
        page = index.read_text(encoding="utf-8")
        cards = page.count("data-card")
        if cards != len(works):
            problems.append(f"首页卡片数 {cards} ≠ 作品数 {len(works)}")
        if "{" in page or "}" in page:
            problems.append("首页里残留未替换的 { } 占位符")
        for href in re.findall(r'href="([^"]+)"', page):
            if href.startswith(("http", "#", "data:", "mailto:")):
                continue
            target = (DIST / href.split("#")[0]).resolve()
            if not target.exists():
                problems.append(f"首页链接指向不存在的文件：{href}")

    for work in works:
        wid = work["id"]
        page = DIST / "works" / wid / "index.html"
        if not page.is_file():
            problems.append(f"缺少作品页：works/{wid}/")
            continue
        text = page.read_text(encoding="utf-8")
        if str(work["title"]) not in text:
            problems.append(f"{wid}：页面里找不到标题")
        if not (DIST / "assets" / "covers" / f"{wid}.svg").is_file():
            problems.append(f"{wid}：缺少封面图")

    for name in ("style.css", "app.js"):
        if not (DIST / "assets" / name).is_file():
            problems.append(f"缺少 dist/assets/{name}")

    if problems:
        print("自检未通过：", file=sys.stderr)
        for item in problems:
            print("  × " + item, file=sys.stderr)
        return 1

    print(f"✓ 自检通过：首页 + {len(works)} 篇作品页，链接与封面全部可用")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
