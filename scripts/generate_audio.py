"""
generate_audio.py
script.txt（読み上げ文）を1人ナレーターの音声にして、MP3を出力する。
- GEMINI_API_KEY があれば Gemini TTS を試す
- 無い/失敗/無料枠切れ の場合は edge-tts（キー不要・無料）で生成
出力: docs/episodes/YYYY-MM-DD.mp3
"""
import os
import re
import ssl
import asyncio
import yaml
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config.yaml"
SCRIPT = ROOT / "build" / "script.txt"
EP_DIR = ROOT / "docs" / "episodes"
JST = timezone(timedelta(hours=9))

# edge-ttsの声（gender→ボイス名）
EDGE_VOICE = {"female": "ja-JP-NanamiNeural", "male": "ja-JP-KeitaNeural"}
# Gemini TTSの声
GEMINI_VOICE = {"female": "Kore", "male": "Puck"}


def load_config():
    with open(CONFIG, encoding="utf-8") as f:
        return yaml.safe_load(f)


def today_slug():
    return datetime.now(JST).strftime("%Y-%m-%d")


# ---------- edge-tts 経路（キー不要・保険）----------
async def edge_tts_generate(text, gender, out_path):
    import edge_tts.communicate as comm
    import edge_tts.voices as vo
    # プロキシ/社内ネットワーク環境でのSSL対策（通常PCでは無害）
    ca = "/etc/ssl/certs/ca-certificates.crt"
    if os.path.exists(ca):
        ctx = ssl.create_default_context(cafile=ca)
        comm._SSL_CTX = ctx
        vo._SSL_CTX = ctx
    import edge_tts
    from pydub import AudioSegment

    voice = EDGE_VOICE.get(gender, EDGE_VOICE["female"])
    # 長文は段落ごとに分割して合成し、間をはさんで結合
    paragraphs = [p.strip() for p in re.split(r"\n+", text) if p.strip()]
    combined = AudioSegment.silent(duration=300)
    gap = AudioSegment.silent(duration=450)
    tmp = ROOT / "build" / "tts_tmp.mp3"
    for i, para in enumerate(paragraphs):
        await edge_tts.Communicate(para, voice).save(str(tmp))
        combined += AudioSegment.from_mp3(tmp) + gap
    combined.export(out_path, format="mp3", bitrate="96k")
    return len(combined) / 1000


# ---------- Gemini TTS 経路 ----------
def gemini_tts_generate(text, gender, out_path):
    from google import genai
    from google.genai import types
    import wave

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    voice = GEMINI_VOICE.get(gender, GEMINI_VOICE["female"])
    resp = client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
        contents=text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
                )
            ),
        ),
    )
    pcm = resp.candidates[0].content.parts[0].inline_data.data
    # PCM(24kHz,16bit,mono) を wav→mp3 に変換
    wav_path = str(out_path).replace(".mp3", ".wav")
    with wave.open(wav_path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(24000)
        w.writeframes(pcm)
    from pydub import AudioSegment
    seg = AudioSegment.from_wav(wav_path)
    seg.export(out_path, format="mp3", bitrate="96k")
    os.remove(wav_path)
    return len(seg) / 1000


def main():
    cfg = load_config()
    gender = cfg["persona"].get("gender", "female")
    text = SCRIPT.read_text(encoding="utf-8")
    EP_DIR.mkdir(parents=True, exist_ok=True)
    out = EP_DIR / f"{today_slug()}.mp3"

    used = None
    dur = 0
    if os.environ.get("GEMINI_API_KEY"):
        try:
            dur = gemini_tts_generate(text, gender, out)
            used = "Gemini TTS"
        except Exception as e:
            print(f"Gemini TTS失敗（{e}）→ edge-ttsに切替")
    if used is None:
        dur = asyncio.run(edge_tts_generate(text, gender, out))
        used = "edge-tts"

    print(f"音声生成: {used}  長さ{dur:.0f}秒 → {out}")


if __name__ == "__main__":
    main()
