# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
"""
daily_content.py - 每日自動發布 SEO 文章
- 60 篇模板輪替，永不重複（直到所有篇完成再循環）
- 每篇自動加上日期、Schema、麵包屑、反連商品頁
- 自動更新 sitemap.xml
- 自動 git push 上 GitHub Pages

用法：
  python scripts/daily_content.py           # 發今天的文章
  python scripts/daily_content.py --preview # 預覽不發布
  python scripts/daily_content.py --reset   # 重置發布紀錄
"""
import json, os, subprocess, re
from pathlib import Path
from datetime import date, datetime

# 支援兩種執行環境：
# 1. 本機：scripts/ 在 site/ 外面
# 2. GitHub Actions：_scripts/ 在 site/ 裡面
_HERE = Path(__file__).parent
if _HERE.name == "_scripts":          # GitHub Actions 環境
    SITE     = _HERE.parent
    BASE     = SITE
    LOG_FILE = SITE / "data" / "published_articles.json"
else:                                  # 本機環境
    BASE     = _HERE.parent
    SITE     = BASE / "site"
    LOG_FILE = BASE / "data" / "published_articles.json"

BLOG_DIR  = SITE / "blog"
SITEMAP   = SITE / "sitemap.xml"
BLOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

SITE_URL  = "https://k69j54h-droid.github.io/xuanmama-cookies"
BRAND     = "璇媽手作烘培曲奇"
LINE_ID   = "ksgeeshain"
FB_URL    = "https://www.facebook.com/p/100057257358264/"

# ── 讀取模板 ──────────────────────────────────
def load_templates():
    sys.path.insert(0, str(Path(__file__).parent))
    from content_templates import TEMPLATES
    return TEMPLATES

# ── 讀取發布紀錄 ──────────────────────────────
def load_log():
    if LOG_FILE.exists():
        with open(LOG_FILE, encoding='utf-8') as f:
            return json.load(f)
    return {"published": [], "last_updated": ""}

def save_log(log):
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(log, f, ensure_ascii=False, indent=2)

# ── 選今日文章（防重複）──────────────────────
def pick_today_template(templates, log):
    published_ids = set(log.get("published", []))
    available = [t for t in templates if t["id"] not in published_ids]

    # 全部發過 → 清空重來（下一輪循環）
    if not available:
        print("60 篇全部發完！開始第二輪循環（重置紀錄）")
        log["published"] = []
        save_log(log)
        available = templates

    # 依分類輪替：A→B→C→A→B→C...
    cycle_map = {"A": 0, "B": 1, "C": 2}
    cycle_pos = len(log.get("published", [])) % 3
    preferred_cat = [k for k, v in cycle_map.items() if v == cycle_pos][0]

    preferred = [t for t in available if t["id"].startswith(preferred_cat)]
    pool = preferred if preferred else available

    # 固定用日期決定選哪篇（可重現，不隨機）
    today_num = int(date.today().strftime("%j"))
    return pool[today_num % len(pool)]

# ── 產生 HTML 文章頁面 ────────────────────────
def generate_html(template, today_str):
    title    = template["title"]
    slug     = template["slug"]
    keywords = "、".join(template["keywords"])
    category = template["category"]
    content  = template["content"].strip()
    url      = f"{SITE_URL}/blog/{slug}.html"
    kw_list  = template["keywords"]

    schema = json.dumps({
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": title,
        "datePublished": today_str,
        "dateModified": today_str,
        "author": {"@type": "Person", "name": "璇媽"},
        "publisher": {
            "@type": "Organization",
            "name": BRAND,
            "url": SITE_URL
        },
        "description": f"{title}｜{BRAND}官方部落格",
        "keywords": kw_list,
        "url": url
    }, ensure_ascii=False)

    faq_schema = json.dumps({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "首頁", "item": SITE_URL + "/"},
            {"@type": "ListItem", "position": 2, "name": category, "item": SITE_URL + f"/blog/#{category}"},
            {"@type": "ListItem", "position": 3, "name": title, "item": url}
        ]
    }, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}｜{BRAND}</title>
  <meta name="description" content="{title}。{BRAND}，雲林在地手工曲奇餅乾，彌月禮盒、喜餅、伴手禮，全台宅配。">
  <meta name="keywords" content="{keywords}，璇媽手作，雲林手工餅乾，曲奇禮盒">
  <link rel="canonical" href="{url}">
  <meta property="og:title" content="{title}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{url}">
  <meta property="og:site_name" content="{BRAND}">
  <script type="application/ld+json">{schema}</script>
  <script type="application/ld+json">{faq_schema}</script>
  <style>
    body{{font-family:'Noto Sans TC',sans-serif;max-width:800px;margin:0 auto;padding:20px 24px;color:#3E2A18;line-height:1.9;background:#FDFAF6}}
    h1{{font-size:1.6rem;color:#3E2A18;border-bottom:2px solid #B8964E;padding-bottom:12px;margin-bottom:24px}}
    h2{{font-size:1.15rem;color:#6B4C2A;margin-top:32px}}
    .meta{{font-size:.82rem;color:#8A8A8A;margin-bottom:28px}}
    .category{{background:#F5EDD8;color:#B8964E;padding:3px 10px;border-radius:20px;font-size:.78rem;font-weight:600}}
    table{{border-collapse:collapse;width:100%;margin:16px 0}}
    th,td{{border:1px solid #E2D4C0;padding:8px 12px;text-align:left;font-size:.88rem}}
    th{{background:#F5EDD8;color:#6B4C2A}}
    .cta-box{{background:#F5EDD8;border:1px solid #B8964E;border-radius:8px;padding:24px;margin:40px 0;text-align:center}}
    .cta-box h3{{color:#B8964E;margin-bottom:12px}}
    .btn{{display:inline-block;background:#06C755;color:#fff;padding:12px 28px;border-radius:50px;text-decoration:none;font-weight:700;margin:4px}}
    .btn-dark{{background:#3E2A18}}
    nav{{font-size:.82rem;margin-bottom:20px;color:#8A8A8A}}
    nav a{{color:#B8964E;text-decoration:none}}
    footer{{margin-top:60px;padding-top:20px;border-top:1px solid #E2D4C0;font-size:.8rem;color:#8A8A8A;text-align:center}}
    ul,ol{{padding-left:1.4em}}
  </style>
</head>
<body>
  <nav><a href="../">首頁</a> › <span>{category}</span> › {title}</nav>
  <article>
    <h1>{title}</h1>
    <div class="meta">
      <span class="category">{category}</span>
      &nbsp;發布日期：{today_str} &nbsp;|&nbsp; {BRAND}
    </div>
    {content}
    <div class="cta-box">
      <h3>🍪 有興趣訂購璇媽手作嗎？</h3>
      <p>雲林在地手工曲奇餅乾・彌月禮盒・喜餅・伴手禮<br>客製化包裝・全台宅配・5,000+ 顧客好評</p>
      <a href="https://line.me/ti/p/~{LINE_ID}" target="_blank" class="btn">💬 加 Line 訂購</a>
      <a href="{FB_URL}" target="_blank" class="btn btn-dark">📘 Facebook 粉絲專頁</a>
      <a href="../" class="btn btn-dark">🏠 回到官網</a>
    </div>
  </article>
  <footer>© 2026 {BRAND} · 雲林縣 · 全台宅配 · Line：{LINE_ID}</footer>
</body>
</html>"""

# ── 更新 sitemap.xml ──────────────────────────
def update_sitemap(slug, today_str):
    content = SITEMAP.read_text(encoding='utf-8')
    new_url = f"""  <url>
    <loc>{SITE_URL}/blog/{slug}.html</loc>
    <lastmod>{today_str}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>"""
    # 避免重複加入
    if f"/blog/{slug}.html" in content:
        # 更新 lastmod
        content = re.sub(
            rf'(<loc>{re.escape(SITE_URL)}/blog/{re.escape(slug)}\.html</loc>\s*<lastmod>)[^<]*(</lastmod>)',
            rf'\g<1>{today_str}\g<2>',
            content
        )
    else:
        content = content.replace("</urlset>", f"{new_url}\n</urlset>")
    SITEMAP.write_text(content, encoding='utf-8')

# ── 更新首頁 Blog 索引（加入最新文章連結）───
def update_blog_index(template, today_str):
    index = BLOG_DIR / "index.html"
    entry = f'<li><a href="{template["slug"]}.html">[{today_str}] {template["title"]}</a> <span>({template["category"]})</span></li>\n'

    if index.exists():
        content = index.read_text(encoding='utf-8')
        content = content.replace("<!-- NEW_ENTRY -->", f"<!-- NEW_ENTRY -->\n    {entry}")
        index.write_text(content, encoding='utf-8')
    else:
        html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <title>璇媽手作烘培曲奇 部落格</title>
  <meta name="description" content="璇媽手作部落格：烘焙知識、雲林在地故事、禮盒選購指南">
  <link rel="canonical" href="{SITE_URL}/blog/">
  <style>body{{font-family:'Noto Sans TC',sans-serif;max-width:800px;margin:0 auto;padding:24px;background:#FDFAF6;color:#3E2A18}} a{{color:#B8964E}} li{{margin:8px 0}}</style>
</head>
<body>
  <h1>璇媽手作・烘焙知識與禮盒選購指南</h1>
  <p><a href="../">← 回到官網</a></p>
  <ul>
    <!-- NEW_ENTRY -->
    {entry}
  </ul>
</body>
</html>"""
        index.write_text(html, encoding='utf-8')

# ── 主流程 ────────────────────────────────────
def run():
    preview = "--preview" in sys.argv
    reset   = "--reset" in sys.argv

    templates = load_templates()
    log       = load_log()

    if reset:
        log["published"] = []
        save_log(log)
        print("發布紀錄已重置")
        return

    template  = pick_today_template(templates, log)
    today_str = date.today().isoformat()

    print(f"今日文章：[{template['id']}] {template['title']}")
    print(f"分類：{template['category']}")
    print(f"關鍵字：{', '.join(template['keywords'])}")

    if preview:
        print("\n[預覽模式] 不發布")
        return

    # 1. 生成 HTML
    html = generate_html(template, today_str)
    dest = BLOG_DIR / f"{template['slug']}.html"
    dest.write_text(html, encoding='utf-8')
    print(f"✅ 文章已生成：{dest.name}")

    # 2. 更新 sitemap
    update_sitemap(template["slug"], today_str)
    print("✅ sitemap.xml 已更新")

    # 3. 更新 blog index
    update_blog_index(template, today_str)
    print("✅ blog/index.html 已更新")

    # 4. 記錄已發布
    log["published"].append(template["id"])
    log["last_updated"] = today_str
    log["total_published"] = len(log["published"])
    log["next_reset_at"] = f"第 {len(templates)} 篇發完後自動循環"
    save_log(log)
    print(f"✅ 發布紀錄：{len(log['published'])}/{len(templates)} 篇")

    # 5. Git push
    try:
        subprocess.run(["git", "add", "blog/", "sitemap.xml"], cwd=SITE, check=True)
        r = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=SITE, capture_output=True)
        if r.returncode != 0:
            subprocess.run(
                ["git", "commit", "-m", f"SEO文章[{template['id']}]：{template['title'][:30]} ({today_str})"],
                cwd=SITE, check=True
            )
            subprocess.run(["git", "push"], cwd=SITE, check=True)
            print("✅ 已推上 GitHub Pages")
        else:
            print("ℹ️  文章已存在，無需重複推送")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  git 失敗：{e}")

    print(f"\n完成！文章網址：{SITE_URL}/blog/{template['slug']}.html")

if __name__ == "__main__":
    run()
