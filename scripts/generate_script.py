"""
generate_script.py
news.json を元に、1人ナレーターが約10分語るラジオ台本を作る。
- GEMINI_API_KEY があれば Gemini で自然な台本を生成
- キーが無い/失敗した場合は、テンプレートで最低限の台本を作る（配信は止めない）
出力: build/script.txt（読み上げ用のプレーンテキスト）
"""
import os
import json
import yaml
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config.yaml"
NEWS = ROOT / "build" / "news.json"
OUT = ROOT / "build" / "script.txt"

JST = timezone(timedelta(hours=9))


def load_config():
    with open(CONFIG, encoding="utf-8") as f:
        return yaml.safe_load(f)


def today_str():
    now = datetime.now(JST)
    wd = ["月", "火", "水", "木", "金", "土", "日"][now.weekday()]
    return f"{now.month}月{now.day}日、{wd}曜日"


def build_prompt(cfg, items):
    tone = cfg["persona"]["tone"]
    lines = []
    for i, it in enumerate(items, 1):
        lines.append(f"{i}. [{it['genre']}] {it['title']}\n   概要: {it['summary']}")
    news_block = "\n".join(lines)
    return f"""{tone}

今日は {today_str()} です。
以下の{len(items)}本のニュースを、1本あたり300〜360文字で、
順番に紹介するラジオ台本を書いてください。
- ジャンルが切り替わるところでは「続いては○○の話題です」と一言はさむ
- 難しい言葉は一言かみ砕く
- 全体で必ず3,800〜4,500文字にする（読み上げると約10分になる分量）。
  確認されている事実の範囲での背景情報（経緯・数字・関係者）を補足して、各ニュースをしっかり膨らませる
- 出力は「読み上げる文章そのもの」だけ。ト書きや話者名・記号は書かない

【今日のニュース】
{news_block}
"""


def generate_with_gemini(prompt):
    """Gemini APIで台本を生成。失敗したら例外を投げる。"""
    from google import genai
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return resp.text.strip()


def fallback_script(cfg, items):
    """キーが無いときの簡易台本（プラン検証・保険用）。"""
    parts = [f"おはようございます。{today_str()}の朝のニュースをお届けします。"]
    last_genre = None
    for it in items:
        if it["genre"] != last_genre:
            parts.append(f"続いては、{it['genre']}の話題です。")
            last_genre = it["genre"]
        parts.append(f"{it['title']}。{it['summary']}")
    parts.append("以上、今朝のニュースでした。それでは、いってらっしゃい。")
    return "\n".join(parts)


def main():
    cfg = load_config()
    items = json.loads(NEWS.read_text(encoding="utf-8"))
    prompt = build_prompt(cfg, items)

    if os.environ.get("GEMINI_API_KEY"):
        try:
            script = generate_with_gemini(prompt)
            if len(script) < 3200:  # 約10分に足りない場合は一度だけ膨らませ直す
                print(f"台本が{len(script)}文字と短いため、増量を再依頼")
                script = generate_with_gemini(
                    prompt
                    + f"\n\n【重要】先ほどの案は{len(script)}文字で短すぎました。"
                    + "各ニュースに背景や補足を加え、全体を必ず3,800文字以上にしてください。"
                )
            print("台本生成: Gemini")
        except Exception as e:
            print(f"Gemini失敗（{e}）→ テンプレートで代替")
            script = fallback_script(cfg, items)
    else:
        print("GEMINI_API_KEY 未設定 → テンプレートで代替")
        script = fallback_script(cfg, items)

    OUT.write_text(script, encoding="utf-8")
    print(f"台本: {len(script)}文字 → {OUT}")


if __name__ == "__main__":
    main()
