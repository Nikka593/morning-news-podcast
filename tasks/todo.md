# todo.md — 朝ニュースPodcast 本実装

## 確定仕様
- スタイル: 1人ナレーター・カジュアルな語り（女性声 Nanami / 男性 Keita 選択可）
- 尺: 約10分・ニュース12本
- ジャンル: 総合 / IT・テック / ビジネス・経済
- 配信時刻: 毎朝6時（JST）＝ cron 21:00 UTC（前日）
- 公開範囲: URL限定公開（GitHub Pages）
- 費用: 完全無料（GitHub / Gemini無料枠 / edge-tts）

## タスク
- [x] 要件確定
- [x] 試作音声（雰囲気確認）
- [ ] config.yaml（ソース・番組情報・口調プロンプトを分離）
- [ ] fetch_news.py（RSS収集・重複除去）
- [ ] generate_script.py（Gemini生成＋キー無し時テンプレfallback）
- [ ] generate_audio.py（Gemini TTS＋edge-tts fallback）
- [ ] build_feed.py（Podcast RSS・直近14本保持）
- [ ] daily.yml（GitHub Actions 毎朝自動実行）
- [ ] エンドツーエンド検証（edge-tts経路で実音声を生成して証明）
- [ ] セットアップ手順書（非エンジニア向け・画面単位）
- [ ] zip納品

## 設計メモ（変わりやすい箇所を先頭に）
1. ニュースソース → config.yaml の feeds を編集するだけ
2. 口調・番組名 → config.yaml の persona / show を編集
3. コードは触らない設計
