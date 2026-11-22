# 回声杯 · 最小静态站

一个可以直接打开、也能直接发布的作品集站点。**没有数据库、没有服务器程序**，全部是提前生成好的 HTML 文件。

打开方式：双击 `dist/index.html`。

---

## 一、目录结构

```
HtmlLearning/
├── content/              每篇作品的正文（Markdown）
│   ├── 001-hui-sheng-ji-yuan.md
│   └── ...
├── data/
│   └── works.json        站点信息 + 作品清单（相当于一张 Excel 表）
├── assets/
│   ├── style.css         全站样式（配色、字体、布局都在开头）
│   └── app.js            深浅色切换、筛选、排序
├── scripts/
│   ├── build.py          构建脚本：把上面三样生成成 dist/
│   └── verify.py         自检：页面齐全、链接不会 404
└── dist/                 构建产物 —— 发布时只需要这一个目录
    ├── index.html
    ├── works/<id>/index.html
    ├── assets/           样式、脚本、自动生成的封面
    └── 404.html
```

只有 `content/`、`data/`、`assets/` 是「源文件」，`dist/` 是每次构建重新生成的，**不要手改 dist/**。

---

## 二、日常三步

```powershell
# 1. 改内容：改 content/*.md 或 data/works.json
# 2. 重新生成页面
python scripts/build.py
# 3. 自检（可选，但推荐）
python scripts/verify.py
# 4. 看效果
#    双击 dist/index.html
#    或起一个本地服务： python -m http.server -d dist 8000
```

构建成功会打印：

```
✓ 生成 6 篇作品 → dist/（8 个页面）
  正文合计 121,800 字
```

---

## 三、加一篇新作品

1. 在 `content/` 放一个新文件，比如 `007-wo-de-zuo-pin.md`，正常写正文：

```markdown
第一段直接写。

## 一

小标题用两个井号；引用用大于号：

> 一句想被记住的话。

**加粗**、*斜体*、`代码`、[链接](https://example.com) 都支持。
```

2. 在 `data/works.json` 的 `works` 数组里加一条：

```json
{
  "id": "wo-de-zuo-pin",
  "title": "我的作品",
  "author": "作者名",
  "words": 12000,
  "summary": "一句话简介，会显示在卡片和详情页开头。",
  "file": "007-wo-de-zuo-pin.md",
  "human": "二等奖",
  "humanPrize": 20000,
  "ai": null,
  "aiPrize": 0,
  "rod": false,
  "aiAssisted": true
}
```

字段说明：

| 字段 | 作用 |
|---|---|
| `id` | 唯一标识，也是网址路径 `works/<id>/`，建议用拼音 |
| `words` | 字数，不填会自动统计 |
| `human` / `ai` | 奖项名，没有就写 `null`（决定出现在哪份名单、能否被筛出来） |
| `humanPrize` / `aiPrize` | 奖金数字，只用于显示和合计 |
| `rod` | 是否获鱼竿奖，`true` 会多 4000 元并显示徽章 |
| `aiAssisted` | `false` 会显示「未用 AI」徽章 |

3. 重新运行 `python scripts/build.py`。

---

## 四、换名字、换配色

- **站名 / 标语 / 页脚**：改 `data/works.json` 里的 `site` 对象。
- **配色**：改 `assets/style.css` 开头的 `:root` 变量，例如 `--accent`（主色）、`--bg`（背景）。深色模式在同文件的 `[data-theme="dark"]` 里改。
- **封面图**：目前按标题自动生成渐变 SVG（`scripts/build.py` 里的 `cover_svg`）。想用真图，就在 `data/works.json` 里加个 `cover` 字段，再把 `card_html` 里的 `src` 换成它。

---

## 五、发布到公网（Cloudflare Pages，免费）

对应之前讲过的 5 步：

```powershell
git init
git add .
git commit -m "初版"
git remote add origin https://github.com/<你的账号>/<仓库名>.git
git push -u origin main
```

然后：

1. 打开 <https://dash.cloudflare.com/> → **Workers & Pages** → **Create** → **Pages** → **Connect to Git**
2. 选中这个仓库
3. **Build command** 留空（静态文件已经生成好了），**Build output directory** 填 `dist`
4. 保存，等一两分钟，会给你一个 `xxx.pages.dev` 网址
5. 想用自己的域名：项目 → **Custom domains** → 填域名 → 按提示加一条 CNAME 记录，证书自动签发

> 如果你不想让 Cloudflare 在云端跑 Python，就把 `dist/` 提交进仓库，构建命令留空直接发布即可。另一种做法是每次本地跑完 `build.py` 再 push。

以后更新：改完内容 → `python scripts/build.py` → `git add . && git commit -m "更新"` → `git push`，网站自动重新发布。

---

## 六、这个站没有的东西

| 没有 | 想要的话 |
|---|---|
| 阅读量统计 | 需要一个接口 + 数据库，或者接第三方统计（如 Cloudflare Web Analytics、Umami） |
| 收藏 / 笔记 / 留言 | 必须有后端 + 数据库 + 登录，静态站做不到 |
| 站内搜索 | 站小可以不做；作品多了可以用 Pagefind 之类做纯前端搜索 |
| 后台发文界面 | 目前「后台」就是编辑 Markdown 文件 |

---

## 七、备注

- 正文为虚构示例，发布前请换成真实内容并确认授权。
- `build.py` 只依赖 Python 标准库（3.8+ 均可）。
