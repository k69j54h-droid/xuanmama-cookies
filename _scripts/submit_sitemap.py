"""
sitemap auto-submit script for xuanmama-cookies
Run after adding new articles: python _scripts/submit_sitemap.py
"""
import urllib.request, urllib.parse, sys, os, json
from datetime import datetime
sys.stdout.reconfigure(encoding="utf-8")

SITEMAP_URL = "https://k69j54h-droid.github.io/xuanmama-cookies/sitemap.xml"
SITE_BASE   = "https://k69j54h-droid.github.io/xuanmama-cookies"
LOG_FILE    = os.path.join(os.path.dirname(__file__), "../logs/sitemap_submit.log")

# All pages in sitemap - update this list when adding new articles
PAGES = [
    "/",
    "/blog/",
    "/blog/yunlin-banshouli-tuijian-qiuqi-binggan.html",
    "/blog/miyue-lihe-tuijian-shouqong-qiuqi.html",
    "/blog/xishi-xibing-tuijian-qiuqi.html",
    "/blog/qiye-songli-kezhihua-binggan-lihe.html",
    "/blog/yunlin-shuiguo-zhipei-tuijian.html",
    "/blog/chunjie-lihe-tuijian-nianjie-songli.html",
    "/blog/qiuqi-kouwei-bijiao-tezhong-jieshao.html",
    "/blog/miyue-lihe-vs-xibing-changhesong.html",
    "/blog/qiuqi-lihe-baocun-zhaipei-zhuyi.html",
]

GSC_URL = (
    "https://search.google.com/search-console/sitemaps"
    "?resource_id=https%3A%2F%2Fk69j54h-droid.github.io%2Fxuanmama-cookies%2F"
)
INSPECT_URL = (
    "https://search.google.com/search-console/inspect"
    "?resource_id=https%3A%2F%2Fk69j54h-droid.github.io%2Fxuanmama-cookies%2F"
)


def log(msg):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}\n")


def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*55}")
    print(f"  Xuanmama SEO - Sitemap Submit Helper  {now}")
    print(f"{'='*55}")
    print(f"  Sitemap : {SITEMAP_URL}")
    print(f"  Pages   : {len(PAGES)}")

    # Google deprecated sitemap ping in 2023 - must use Search Console UI
    print("\n[STEP 1] Open Search Console Sitemap page:")
    print(f"  {GSC_URL}")
    print(f"  -> Paste: sitemap.xml  -> Click [Submit]")

    print("\n[STEP 2] Request indexing for NEW articles:")
    for p in PAGES[2:]:  # skip home & blog index for brevity
        full = SITE_BASE + p
        print(f"  URL Inspect -> {full}")
    print(f"\n  URL Inspection tool: {INSPECT_URL}")

    print("\n[STEP 3] Verify in 1-3 days:")
    print("  Search Console -> Pages -> check Indexed count increases")

    log(f"Submit reminder shown | pages={len(PAGES)} | sitemap={SITEMAP_URL}")
    print(f"\n  Log saved to: {os.path.abspath(LOG_FILE)}")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    main()
