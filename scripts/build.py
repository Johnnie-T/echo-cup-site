#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""最小静态站构建脚本：把 content/ 的 Markdown 与 data/works.json 生成 dist/ 静态页面。

用法：
    python scripts/build.py

生成：
    dist/index.html              首页（名单对照 + 作品列表）
    dist/works/<id>/index.html   每篇作品
    dist/assets/...              样式、脚本、自动生成的封面图
    dist/404.html                找不到页面时的兜底页

只依赖 Python 标准库。改完内容或数据，重新运行一次即可。
"""

from __future__ import annotations

import html
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content"
DATA_FILE = ROOT / "data" / "works.json"
ASSETS_DIR = ROOT / "assets"
DIST_DIR = ROOT / "dist"

ROD_PRIZE = 4000  # 鱼竿奖奖金，固定 4000 元

RANK_ORDER = {"特别奖": 0, "一等奖": 1, "二等奖": 2, "三等奖": 3}

# 封面图配色：左深右浅，按顺序循环使用
COVER_PALETTES = [
    ("#12323a", "#2f6f6b"),
    ("#261c2b", "#8b5a7a"),
    ("#1a2739", "#3f6b9e"),
    ("#33240f", "#a3781f"),
    ("#1b3025", "#4f8763"),
    ("#301c26", "#a34f5f"),
]


# --------------------------------------------------------------------------
# 小工具
# --------------------------------------------------------------------------
def esc(value: object) -> str:
    """转义成 HTML 安全的字符串。"""
    return html.escape(str(value), quote=True)


def money(amount: object) -> str:
    try:
        return f"{int(amount):,}"
    except (TypeError, ValueError):
        return "0"


def fmt_int(value: object, fallback: str = "—") -> str:
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return fallback


# --------------------------------------------------------------------------
# Markdown 子集：## 标题、> 引用、**粗体**、*斜体*、`代码`、[链接](url)、--- 分隔线
# --------------------------------------------------------------------------
def inline(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    return text


def md_to_html(markdown: str) -> str:
    blocks: list[str] = []
    buffer: list[str] = []

    def flush() -> None:
        if buffer:
            blocks.append("<p>" + inline(esc(" ".join(buffer))) + "</p>")
            buffer.clear()

    for raw in markdown.splitlines():
        line = raw.strip()
        if not line:
            flush()
            continue
        if line == "---":
            flush()
            blocks.append("<hr>")
            continue
        if line.startswith("## "):
            flush()
            blocks.append("<h2>" + inline(esc(line[3:].strip())) + "</h2>")
            continue
        if line.startswith("# "):
            flush()
            blocks.append("<h2>" + inline(esc(line[2:].strip())) + "</h2>")
            continue
        if line.startswith("> "):
            flush()
            blocks.append("<blockquote><p>" + inline(esc(line[2:].strip())) + "</p></blockquote>")
            continue
        buffer.append(line)
    flush()
    return "\n".join(blocks)


# --------------------------------------------------------------------------
# 片段渲染
# --------------------------------------------------------------------------
def cover_svg(work: dict, index: int) -> str:
    left, right = COVER_PALETTES[(index - 1) % len(COVER_PALETTES)]
    title = str(work["title"])
    size = 32 if len(title) <= 4 else 27 if len(title) <= 5 else 22
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 240" '
        f'role="img" aria-label="{esc(title)}">'
        '<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{left}"/><stop offset="1" stop-color="{right}"/>'
        "</linearGradient></defs>"
        '<rect width="400" height="240" fill="url(#bg)"/>'
        '<circle cx="318" cy="52" r="96" fill="#ffffff" opacity="0.05"/>'
        '<circle cx="62" cy="212" r="118" fill="#ffffff" opacity="0.035"/>'
        '<text x="28" y="206" fill="#ffffff" fill-opacity="0.55" font-size="13" '
        f'font-family="sans-serif" letter-spacing="2">NO. {index:02d}</text>'
        f'<text x="28" y="150" fill="#ffffff" font-size="{size}" font-family="sans-serif" '
        f'font-weight="600">{esc(title)}</text>'
        "</svg>"
    )


def badges(work: dict) -> str:
    out = []
    if work.get("human"):
        out.append(f'<span class="badge badge-human">人类评委{esc(work["human"])}</span>')
    if work.get("ai"):
        out.append(f'<span class="badge badge-ai">AI 评委{esc(work["ai"])}</span>')
    if work.get("rod"):
        out.append('<span class="badge badge-rod">鱼竿奖</span>')
    if not work.get("aiAssisted", True):
        out.append('<span class="badge badge-plain">未用 AI</span>')
    return "".join(out)


def card_html(work: dict, index: int) -> str:
    human = bool(work.get("human"))
    ai = bool(work.get("ai"))
    return (
        f'      <article class="card" data-card data-both="{int(human and ai)}" '
        f'data-human="{int(human)}" data-ai="{int(ai)}" '
        f'data-rod="{int(bool(work.get("rod")))}" '
        f'data-words="{int(work.get("words") or 0)}">\n'
        f'        <a class="card-link" href="works/{esc(work["id"])}/index.html">\n'
        f'          <img class="cover" src="assets/covers/{esc(work["id"])}.svg" '
        f'alt="《{esc(work["title"])}》封面" width="400" height="240" loading="lazy">\n'
        '          <div class="card-body">\n'
        f'            <h3>{esc(work["title"])}</h3>\n'
        f'            <p class="byline">{esc(work["author"])} · {fmt_int(work.get("words"))} 字</p>\n'
        f'            <p class="summary">{esc(work.get("summary", ""))}</p>\n'
        f'            <div class="badges">{badges(work)}</div>\n'
        "          </div>\n"
        "        </a>\n"
        "      </article>"
    )


def rank_items(works: list[dict], side: str) -> str:
    items = []
    for work in works:
        label = work.get(side)
        if not label:
            continue
        both = bool(work.get("human")) and bool(work.get("ai"))
        cls = ' class="is-both"' if both else ""
        amount = money(work.get(f"{side}Prize") or 0)
        items.append(
            f'<li{cls}><a href="works/{esc(work["id"])}/index.html">{esc(work["title"])}</a>'
            f'<span class="prize">{esc(label)} · {amount} 元</span></li>'
        )
    return "\n".join(items)


def favicon() -> str:
    return (
        "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E"
        "%3Crect width='32' height='32' rx='7' fill='%232f6f6b'/%3E"
        "%3Ctext x='16' y='23' font-size='19' text-anchor='middle' fill='%23fff'"
        " font-family='sans-serif'%3E%E5%9B%9E%3C/text%3E%3C/svg%3E"
    )


# --------------------------------------------------------------------------
# 页面模板
# --------------------------------------------------------------------------
def header_html(site: dict, prefix: str) -> str:
    name = esc(site.get("name", "作品集"))
    base = prefix + "index.html"
    return f"""<header class="site-header">
  <div class="wrap header-inner">
    <a class="brand" href="{base}">{name}</a>
    <nav class="site-nav" aria-label="主导航">
      <a href="{base}#awards">名单</a>
      <a href="{base}#works">作品</a>
      <a href="{base}#about">关于</a>
    </nav>
    <button id="theme-toggle" class="theme-toggle" type="button" aria-label="切换深浅色">深色</button>
  </div>
</header>"""


def footer_html(site: dict, prefix: str) -> str:
    note = esc(site.get("footer", ""))
    return f"""<footer class="site-footer">
  <div class="wrap">
    <p>{note}</p>
    <p>纯静态站 · 由 <code>scripts/build.py</code> 生成 · 不需要数据库和服务器程序</p>
  </div>
</footer>"""


def html_doc(title: str, description: str, prefix: str, body: str, og_image: str = "") -> str:
    image = f'\n<meta property="og:image" content="{esc(og_image)}">' if og_image else ""
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<meta property="og:type" content="website">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">{image}
<link rel="icon" href="{favicon()}">
<link rel="stylesheet" href="{prefix}assets/style.css">
<script src="{prefix}assets/app.js" defer></script>
</head>
<body>
{body}
</body>
</html>
"""


def render_index(site: dict, works: list[dict]) -> str:
    total_prize = sum((w.get("humanPrize") or 0) + (w.get("aiPrize") or 0) for w in works)
    total_prize += sum(ROD_PRIZE for w in works if w.get("rod"))
    both_count = sum(1 for w in works if w.get("human") and w.get("ai"))
    ai_used = sum(1 for w in works if w.get("aiAssisted"))
    words_total = sum(int(w.get("words") or 0) for w in works)

    human_sorted = sorted(
        [w for w in works if w.get("human")],
        key=lambda w: (RANK_ORDER.get(str(w["human"]), 9), -(w.get("humanPrize") or 0)),
    )
    ai_sorted = sorted(
        [w for w in works if w.get("ai")],
        key=lambda w: (RANK_ORDER.get(str(w["ai"]), 9), -(w.get("aiPrize") or 0)),
    )

    human_only = sum(1 for w in works if w.get("human") and not w.get("ai"))
    ai_only = sum(1 for w in works if w.get("ai") and not w.get("human"))
    rod_count = sum(1 for w in works if w.get("rod"))

    chips = "\n        ".join(
        f'<button class="chip" type="button" data-filter="{key}" '
        f'aria-pressed="{"true" if key == "all" else "false"}">'
        f'{esc(label)}<span>{count}</span></button>'
        for key, label, count in [
            ("all", "全部", len(works)),
            ("both", "两边都获奖", both_count),
            ("human", "只获人类评委奖", human_only),
            ("ai", "只获 AI 评委奖", ai_only),
            ("rod", "鱼竿奖", rod_count),
        ]
    )

    cards = "\n".join(card_html(w, i) for i, w in enumerate(works, start=1))

    body = f"""{header_html(site, "")}

<main>
  <section class="hero wrap">
    <p class="eyebrow">最小静态站示例</p>
    <h1>{esc(site.get("name", ""))}</h1>
    <p class="tagline">{esc(site.get("tagline", ""))}</p>
    <p class="intro">{esc(site.get("intro", ""))}</p>
    <div class="stats">
      <div><div class="stat-num">{len(works)}</div><div class="stat-label">部作品</div></div>
      <div><div class="stat-num">{both_count}</div><div class="stat-label">两边都获奖</div></div>
      <div><div class="stat-num">{money(total_prize)}</div><div class="stat-label">奖金合计（元）</div></div>
      <div><div class="stat-num">{fmt_int(words_total)}</div><div class="stat-label">总字数</div></div>
    </div>
  </section>

  <section id="awards" class="wrap section">
    <div class="section-head">
      <h2>两份名单</h2>
      <p>同一批作品，人类评委与 AI 评委各排一次；两边都获奖的带 ★。</p>
    </div>
    <div class="pairs">
      <div class="pair-col is-human">
        <h3>人类评委 · {len(human_sorted)} 部</h3>
        <ol class="rank">
{rank_items(human_sorted, "human")}
        </ol>
      </div>
      <div class="pair-col is-ai">
        <h3>AI 评委 · {len(ai_sorted)} 部</h3>
        <ol class="rank">
{rank_items(ai_sorted, "ai")}
        </ol>
      </div>
    </div>
  </section>

  <section id="works" class="wrap section">
    <div class="section-head">
      <h2>全部作品</h2>
      <p>点封面进入正文；下面的筛选和排序全部在浏览器里完成。</p>
    </div>
    <div class="toolbar">
      <div class="filters" role="group" aria-label="按奖项筛选">
        {chips}
      </div>
      <label class="sort">排序
        <select id="sort">
          <option value="default">默认顺序</option>
          <option value="words-asc">篇幅：短 → 长</option>
          <option value="words-desc">篇幅：长 → 短</option>
        </select>
      </label>
    </div>
    <p class="result-note" id="result-note">共 {len(works)} 部作品</p>
    <div class="works-grid" id="works-grid">
{cards}
      <p class="empty-state" id="empty-state" hidden>这个筛选下没有作品，换个条件试试。</p>
    </div>
  </section>

  <section id="about" class="wrap section">
    <div class="section-head">
      <h2>这个站是怎么来的</h2>
      <p>只有四个目录，没有数据库。</p>
    </div>
    <div class="about-grid">
      <div class="about-card">
        <h3><code>content/</code></h3>
        <p>每篇作品一个 Markdown 文件，写标题、分段、引用都在这里。它就是你要交给我的「素材」。</p>
      </div>
      <div class="about-card">
        <h3><code>data/works.json</code></h3>
        <p>作品清单：标题、作者、字数、奖项、奖金、是否用 AI。相当于一张 Excel 表。</p>
      </div>
      <div class="about-card">
        <h3><code>assets/</code></h3>
        <p>样式与交互脚本。换配色改 <code>style.css</code> 顶部的变量即可。</p>
      </div>
      <div class="about-card">
        <h3><code>dist/</code></h3>
        <p>构建产物：真正的静态网页。发布时只需要把这一个目录传上去。</p>
      </div>
    </div>
  </section>
</main>

{footer_html(site, "")}"""

    title = f'{site.get("name", "作品集")} · {site.get("tagline", "")}'
    return html_doc(title, str(site.get("intro", "")), "", body)


def render_work(
    site: dict,
    work: dict,
    index: int,
    total: int,
    prev_work: dict | None,
    next_work: dict | None,
    body_html: str,
) -> str:
    prefix = "../../"

    pager_parts = []
    if prev_work:
        pager_parts.append(
            f'<a class="prev" href="../{esc(prev_work["id"])}/index.html">'
            f'<span>← 上一篇</span>{esc(prev_work["title"])}</a>'
        )
    if next_work:
        pager_parts.append(
            f'<a class="next" href="../{esc(next_work["id"])}/index.html">'
            f'<span>下一篇 →</span>{esc(next_work["title"])}</a>'
        )
    pager = "\n      ".join(pager_parts)

    body = f"""{header_html(site, prefix)}

<main class="wrap reader">
  <p class="crumb"><a href="{prefix}index.html#works">← 全部作品</a> · 第 {index} / {total} 篇</p>
  <h1>{esc(work["title"])}</h1>
  <p class="byline">{esc(work["author"])} · {fmt_int(work.get("words"))} 字</p>
  <div class="badges">{badges(work)}</div>
  <p class="lead">{esc(work.get("summary", ""))}</p>
  <article class="prose">
{body_html}
  </article>
  <nav class="pager" aria-label="上一篇 / 下一篇">
      {pager}
  </nav>
</main>

{footer_html(site, prefix)}"""

    cover = f"../../assets/covers/{work['id']}.svg"
    return html_doc(f'{work["title"]} · {site.get("name", "")}', str(work.get("summary", "")), prefix, body, cover)


def render_404(site: dict) -> str:
    body = f"""{header_html(site, "")}

<main class="wrap reader">
  <h1>这一页不在了</h1>
  <p class="lead">链接可能过期了，或者作品名拼错了。</p>
  <p><a href="index.html">← 回到首页</a></p>
</main>

{footer_html(site, "")}"""
    return html_doc("页面不存在 · " + str(site.get("name", "")), "页面不存在", "", body)


# --------------------------------------------------------------------------
# 入口
# --------------------------------------------------------------------------
def main() -> int:
    # Windows 控制台默认是 GBK，输出 ✓ 或中文会直接抛 UnicodeEncodeError
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):
            pass

    if not DATA_FILE.exists():
        print(f"× 找不到数据文件：{DATA_FILE}", file=sys.stderr)
        return 1
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"× data/works.json 不是合法 JSON：{exc}", file=sys.stderr)
        return 1

    site = data.get("site", {})
    works = data.get("works", [])
    if not works:
        print("× data/works.json 里没有作品", file=sys.stderr)
        return 1

    seen: set[str] = set()
    problems: list[str] = []
    bodies: dict[str, str] = {}

    for work in works:
        wid = str(work.get("id", ""))
        if not wid:
            problems.append(f"有一部作品缺少 id：{work.get('title')!r}")
            continue
        if wid in seen:
            problems.append(f"id 重复：{wid}")
            continue
        seen.add(wid)

        path = CONTENT_DIR / str(work.get("file", ""))
        if not path.is_file():
            problems.append(f"{wid}：找不到正文文件 content/{work.get('file')}")
            continue

        text = path.read_text(encoding="utf-8")
        if not work.get("words"):
            work["words"] = len(re.sub(r"\s+", "", text))
        bodies[wid] = md_to_html(text)

    if problems:
        print("构建失败：", file=sys.stderr)
        for item in problems:
            print("  × " + item, file=sys.stderr)
        return 1

    pages: dict[str, str] = {"index.html": render_index(site, works)}
    for i, work in enumerate(works):
        pages[f"works/{work['id']}/index.html"] = render_work(
            site,
            work,
            i + 1,
            len(works),
            works[i - 1] if i > 0 else None,
            works[i + 1] if i + 1 < len(works) else None,
            bodies[str(work["id"])],
        )
        pages[f"assets/covers/{work['id']}.svg"] = cover_svg(work, i + 1)
    pages["404.html"] = render_404(site)

    # 全部渲染成功后才动磁盘：出错时 dist/ 保持原样
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True)
    for rel, text in pages.items():
        target = DIST_DIR / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    shutil.copytree(ASSETS_DIR, DIST_DIR / "assets", dirs_exist_ok=True)

    words_total = sum(int(w.get("words") or 0) for w in works)
    html_pages = len(works) + 2  # 首页 + 作品页 + 404
    print(f"✓ 生成 {html_pages} 个页面（首页 + {len(works)} 篇作品 + 404）")
    print(f"  产物共 {len(pages) + 2} 个文件 → dist/")
    print(f"  作品字数合计 {words_total:,} 字（取自 data/works.json）")
    print("  预览：双击 dist/index.html，或运行 python -m http.server -d dist 8000")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
