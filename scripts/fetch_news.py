"""
fetch_news.py
config.yaml に書いたRSSソースからニュースを集め、重複を除き、
1エピソード分のニュース一覧を news.json に保存する。
"""
import json
import os
import re
import socket
socket.setdefaulttimeout(20)  # RSS取得が20秒以上固まったら諦めて次へ
import yaml
import feedparser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config.yaml"
OUT = ROOT / "build" / "news.json"


def load_config():
    with open(CONFIG, encoding="utf-8") as f:
        return yaml.safe_load(f)


def ai_select(candidates, hint, want):
    """候補記事から、hint（選別基準）に合うものをGeminiに選ばせる。
    キーが無い・失敗した場合は新着順で代替する。"""
    if not os.environ.get("GEMINI_API_KEY"):
        print(f"  AI選別: キー未設定 → 新着順で{want}本")
        return candidates[:want]
    try:
        from google import genai
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        listing = "\n".join(
            f"{i}. {c['title']} — {c['summary'][:100]}"
            for i, c in enumerate(candidates, 1)
        )
        prompt = (
            f"以下の記事一覧から「{hint}」という基準に最も合う記事を{want}本選び、"
            f"その番号だけをカンマ区切りで出力してください（例: 3,7）。"
            f"完全に合う記事が無ければ、最も近いものを選んでください。\n\n{listing}"
        )
        resp = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        nums = [int(n) for n in re.findall(r"\d+", resp.text)]
        picked = [candidates[n - 1] for n in nums if 1 <= n <= len(candidates)][:want]
        if picked:
            print(f"  AI選別: {len(candidates)}候補 → {[c['title'][:25] for c in picked]}")
            return picked
    except Exception as e:
        print(f"  AI選別失敗（{e}）→ 新着順で代替")
    return candidates[:want]


def fetch(cfg):
    seen_titles = set()
    items = []
    for feed in cfg["feeds"]:
        d = feedparser.parse(feed["url"])
        want = feed.get("max_items", 5)
        sel = feed.get("ai_select")
        limit = sel.get("candidates", 20) if sel else want
        pool = []
        for entry in d.entries:
            title = entry.get("title", "").strip()
            if not title or title in seen_titles:
                continue
            pool.append({
                "genre": feed["genre"],
                "title": title,
                "summary": entry.get("summary", "").strip()[:400],
                "link": entry.get("link", ""),
            })
            if len(pool) >= limit:
                break
        if sel:
            pool = ai_select(pool, sel.get("hint", ""), want)
        else:
            pool = pool[:want]
        for it in pool:
            seen_titles.add(it["title"])
        items.extend(pool)
    # 合計本数で切る
    total = cfg.get("total_items", 12)
    return items[:total]


def main():
    cfg = load_config()
    items = fetch(cfg)
    OUT.parent.mkdir(exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print(f"取得: {len(items)}本 → {OUT}")
    for i, it in enumerate(items, 1):
        print(f"  {i:2d}. [{it['genre']}] {it['title']}")


if __name__ == "__main__":
    main()
