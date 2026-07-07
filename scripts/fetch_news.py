"""
fetch_news.py
config.yaml に書いたRSSソースからニュースを集め、重複を除き、
1エピソード分のニュース一覧を news.json に保存する。
"""
import json
import yaml
import feedparser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config.yaml"
OUT = ROOT / "build" / "news.json"


def load_config():
    with open(CONFIG, encoding="utf-8") as f:
        return yaml.safe_load(f)


def fetch(cfg):
    seen_titles = set()
    items = []
    for feed in cfg["feeds"]:
        d = feedparser.parse(feed["url"])
        count = 0
        for entry in d.entries:
            title = entry.get("title", "").strip()
            if not title or title in seen_titles:
                continue
            seen_titles.add(title)
            items.append({
                "genre": feed["genre"],
                "title": title,
                "summary": entry.get("summary", "").strip()[:400],
                "link": entry.get("link", ""),
            })
            count += 1
            if count >= feed.get("max_items", 5):
                break
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
