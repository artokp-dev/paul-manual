#!/usr/bin/env python3
"""영상 → 시간이 찍힌 장면 모음 이미지(콘택트 시트).

Claude가 영상을 직접 볼 수 없으니, 일정 간격으로 프레임을 뽑아
한 장에 모아 두고 Read로 본다. 영상 정보(길이, 해상도, 소리 유무, HDR)도 출력한다.

사용법:
  python3 tools/sheet.py work/in/IMG_1234.MOV
  python3 tools/sheet.py work/in/IMG_1234.MOV --every 0.5 --out work/sheets/coco
"""
import argparse
import json
import math
import os
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = os.path.join(ROOT, "assets", "fonts", "Pretendard-Bold.otf")
THUMB_W = 300
COLS, ROWS = 4, 5


def probe(src):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json",
         "-show_streams", "-show_format", src],
        capture_output=True, text=True, check=True)
    info = json.loads(out.stdout)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    return {
        "duration": float(info["format"]["duration"]),
        "width": v.get("width"),
        "height": v.get("height"),
        "fps": v.get("avg_frame_rate"),
        "codec": v.get("codec_name"),
        "hdr": v.get("color_transfer") in ("arib-std-b67", "smpte2084"),
        "audio": any(s["codec_type"] == "audio" for s in info["streams"]),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--every", type=float, help="몇 초마다 한 장 (기본: 길이에 맞춰 자동)")
    ap.add_argument("--out", help="저장 폴더 (기본: work/sheets/<파일이름>)")
    args = ap.parse_args()

    info = probe(args.src)
    dur = info["duration"]
    every = args.every or max(0.5, round(dur / 40, 1))
    name = os.path.splitext(os.path.basename(args.src))[0]
    out_dir = args.out or os.path.join(ROOT, "work", "sheets", name)
    os.makedirs(out_dir, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            ["ffmpeg", "-v", "error", "-i", args.src,
             "-vf", f"fps=1/{every},scale={THUMB_W}:-2", "-q:v", "4",
             os.path.join(tmp, "%05d.jpg")],
            check=True)
        frames = sorted(f for f in os.listdir(tmp) if f.endswith(".jpg"))
        font = ImageFont.truetype(FONT, 22)
        per_sheet = COLS * ROWS
        sheets = []
        for s in range(math.ceil(len(frames) / per_sheet)):
            chunk = frames[s * per_sheet:(s + 1) * per_sheet]
            first = Image.open(os.path.join(tmp, chunk[0]))
            tw, th = first.size
            rows = math.ceil(len(chunk) / COLS)
            sheet = Image.new("RGB", (tw * COLS, th * rows), "black")
            draw = ImageDraw.Draw(sheet)
            for i, f in enumerate(chunk):
                x, y = (i % COLS) * tw, (i // COLS) * th
                sheet.paste(Image.open(os.path.join(tmp, f)), (x, y))
                t = (s * per_sheet + i) * every
                draw.text((x + 8, y + 6), f"{t:.1f}s", font=font, fill="#FFE14D",
                          stroke_width=3, stroke_fill="black")
            path = os.path.join(out_dir, f"sheet_{s + 1:02d}.jpg")
            sheet.save(path, quality=85)
            sheets.append(path)

    print(f"길이 {dur:.1f}초 | {info['width']}x{info['height']} | {info['codec']} "
          f"| fps {info['fps']} | 소리 {'있음' if info['audio'] else '없음'} "
          f"| HDR {'예' if info['hdr'] else '아니오'}")
    print(f"{every}초 간격, 장면 모음 {len(sheets)}장:")
    for p in sheets:
        print("  " + p)


if __name__ == "__main__":
    sys.exit(main())
