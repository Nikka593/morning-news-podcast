"""
build_feed.py
docs/episodes/ の中のMP3を集めて、Podcastアプリが読める feed.xml を作る。
これを作ることで、スマホのPodcastアプリに番組として登録できるようになる。
古いエピソードは keep_episodes を超えた分を自動削除する。
"""
import yaml
from pathlib import Path
from datetime import datetime, timezone, timedelta
from email.utils import format_datetime
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config.yaml"
EP_DIR = ROOT / "docs" / "episodes"
FEED = ROOT / "docs" / "feed.xml"
JST = timezone(timedelta(hours=9))


def load_config():
    with open(CONFIG, encoding="utf-8") as f:
        return yaml.safe_load(f)


def prune(cfg):
    """古いエピソードを削除して直近 keep_episodes 本だけ残す。"""
    keep = cfg.get("keep_episodes", 14)
    mp3s = sorted(EP_DIR.glob("*.mp3"), reverse=True)  # 新しい順
    for old in mp3s[keep:]:
        old.unlink()
        print(f"削除（保持数超過）: {old.name}")
    return sorted(EP_DIR.glob("*.mp3"), reverse=True)


def item_xml(cfg, mp3):
    base = cfg["show"]["base_url"].rstrip("/")
    slug = mp3.stem                       # 例: 2026-07-07
    url = f"{base}/episodes/{mp3.name}"
    size = mp3.stat().st_size
    dt = datetime.strptime(slug, "%Y-%m-%d").replace(hour=6, tzinfo=JST)
    title = f"{slug} の朝ニュース"
    return f"""    <item>
      <title>{escape(title)}</title>
      <enclosure url="{escape(url)}" length="{size}" type="audio/mpeg"/>
      <guid isPermaLink="false">{escape(slug)}</guid>
      <pubDate>{format_datetime(dt)}</pubDate>
    </item>"""


def main():
    cfg = load_config()
    show = cfg["show"]
    base = show["base_url"].rstrip("/")
    mp3s = prune(cfg)

    items = "\n".join(item_xml(cfg, m) for m in mp3s)
    now = format_datetime(datetime.now(JST))
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>{escape(show['title'])}</title>
    <link>{escape(base)}</link>
    <language>{escape(show.get('language','ja'))}</language>
    <description>{escape(show['description'])}</description>
    <itunes:author>{escape(show['author'])}</itunes:author>
    <itunes:explicit>false</itunes:explicit>
    <lastBuildDate>{now}</lastBuildDate>
{items}
  </channel>
</rss>
"""
    FEED.write_text(feed, encoding="utf-8")
    print(f"フィード生成: {len(mp3s)}エピソード → {FEED}")


if __name__ == "__main__":
    main()
