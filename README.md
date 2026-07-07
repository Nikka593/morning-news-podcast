# 朝ニュースPodcast 🎙️

毎朝6時、総合・IT/テック・ビジネス経済のニュースを自動で集めて、
1人ナレーターが約10分語るPodcastを生成し、スマホに配信する仕組み。

**費用ゼロ**（GitHub / Gemini無料枠 / edge-tts）・**サーバー不要**・
普段のPodcastアプリで聴けます。

## セットアップ
`docs/setup_guide.html` をブラウザで開いて、手順どおりに進めてください（非エンジニア向け・画面単位で解説）。

## 仕組み
```
毎朝6時 (GitHub Actions)
  → fetch_news.py    RSSからニュース収集
  → generate_script.py  Geminiで台本生成（キー無しは簡易テンプレ）
  → generate_audio.py   Gemini TTS→失敗時edge-ttsで音声化
  → build_feed.py    Podcast用RSS生成・古い回を自動削除
  → docs/ に公開（GitHub Pages）→ スマホのPodcastアプリに届く
```

## カスタマイズ
`config.yaml` だけ編集すればOK（ソース・語り口・声・保持数）。コードは触らない設計です。

## 声について
- **Gemini TTS**（APIキーあり）：より自然。無料枠に上限あり
- **edge-tts**（キー不要）：無料枠切れ時に自動で使われる保険
