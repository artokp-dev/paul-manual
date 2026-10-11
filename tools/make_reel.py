#!/usr/bin/env python3
"""편집 계획(JSON) → 인스타 릴스용 9:16 영상 (1080x1920, 30fps, H.264/AAC).

사용법:
  python3 tools/make_reel.py work/plans/coco.json              # 완성 영상
  python3 tools/make_reel.py work/plans/coco.json --still 1.5  # 1.5초 지점 미리보기 PNG

계획 형식은 tools/example_plan.json 참고.
- clips: 원본에서 잘라 쓸 구간들 (순서대로 이어 붙임)
    src, start, end(생략하면 끝까지), speed(0.5~4), volume, mute,
    fit("crop" 꽉 채우기 | "blur" 전체 보이게+흐린 배경), zoom(1 이상), x(0~1, 가로 크롭 위치)
- texts: 완성 영상 기준 시간에 얹을 글자
    start, end(null이면 끝까지), text("\n" 줄바꿈), style(기본 "paul"), y, size
    "paul"은 @24paulah 기존 스타일: 흰 글씨 + 검은 둥근 상자(인스타 앱 텍스트 배경과 같은 모양).
    다른 스타일(hook, sub, box, end, small)은 *강조* 노란색을 쓸 수 있다. 실험용.
- 음악은 넣지 않는다. 인스타 앱에서 원장님이 직접 얹는다.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(ROOT, "assets", "fonts")
MAX_TEXT_W = 880  # 오른쪽 버튼·가장자리 피해서

# y는 글자 덩어리의 세로 중심 (화면 높이 비율).
# 인스타가 위 ~13%, 아래 ~25%를 계정명·캡션으로 가리므로 그 사이에 둔다.
STYLES = {
    # @24paulah 기존 스타일 (2026-10 계정 분석): 보통 굵기, 강조색·테두리 없음, 줄마다 검은 상자.
    # 기본 위치는 세로 75%, 처치 동작이 아래쪽이면 0.20~0.25로 올린다. 0.80 아래는 앱 캡션에 가린다.
    "paul": dict(font="Pretendard-Medium.otf", size=70, stroke=0, y=0.75, box="lines", gap=1.45,
                 accent=False),
    "hook": dict(font="Pretendard-Black.otf", size=92, stroke=10, y=0.30, box=False, gap=1.18),
    "sub": dict(font="Pretendard-Bold.otf", size=60, stroke=7, y=0.66, box=False, gap=1.22),
    "box": dict(font="Pretendard-Bold.otf", size=54, stroke=0, y=0.66, box=True, gap=1.32),
    "end": dict(font="Pretendard-Black.otf", size=78, stroke=9, y=0.45, box=False, gap=1.2),
    "small": dict(font="Pretendard-Bold.otf", size=40, stroke=5, y=0.16, box=False, gap=1.2),
}
WHITE, ACCENT, OUTLINE = "#FFFFFF", "#FFE14D", "#000000"


# ---------- 글자 이미지 ----------

def strip_emoji(text):
    """프리텐다드에는 이모지가 없어 네모(□)로 나온다. 영상 글자에서는 뺀다."""
    kept = "".join(ch for ch in text
                   if not (0x1F000 <= ord(ch) <= 0x1FAFF or 0x2600 <= ord(ch) <= 0x27BF
                           or ord(ch) in (0xFE0F, 0x200D)))
    if kept != text:
        print(f"참고: 영상 글자에서 이모지를 뺐어요 → {kept.strip()}", file=sys.stderr)
    return kept.rstrip()


def parse_markup(text):
    """'*강조*'를 (글자, 강조여부) 목록으로. 줄 단위로 나눈다."""
    lines = []
    for raw in strip_emoji(text).split("\n"):
        chars, accent = [], False
        for ch in raw:
            if ch == "*":
                accent = not accent
                continue
            chars.append((ch, accent))
        lines.append(chars)
    return lines


def wrap(line, font, max_w):
    """띄어쓰기 기준으로 줄을 접는다. 한 단어가 너무 길면 글자 단위로 자른다."""
    def width(cs):
        return font.getlength("".join(c for c, _ in cs))

    words, cur = [], []
    for c in line:
        if c[0] == " ":
            if cur:
                words.append(cur)
                cur = []
        else:
            cur.append(c)
    if cur:
        words.append(cur)

    out, cur = [], []
    for w in words:
        trial = cur + [(" ", False)] + w if cur else w
        if width(trial) <= max_w:
            cur = trial
            continue
        if cur:
            out.append(cur)
        cur = []
        for c in w:
            if cur and width(cur + [c]) > max_w:
                out.append(cur)
                cur = []
            cur.append(c)
    if cur or not out:
        out.append(cur)
    return out


def segments(line):
    """같은 색끼리 묶기."""
    segs = []
    for ch, acc in line:
        if segs and segs[-1][1] == acc:
            segs[-1][0] += ch
        else:
            segs.append([ch, acc])
    return segs


def render_text(item, path):
    st = dict(STYLES[item.get("style", "paul")])
    size = item.get("size", st["size"])
    font = ImageFont.truetype(os.path.join(FONT_DIR, st["font"]), size)
    stroke = round(st["stroke"] * size / st["size"])

    lines = []
    for raw in parse_markup(item["text"]):
        lines.extend(wrap(raw, font, MAX_TEXT_W))
    line_h = size * st["gap"]
    block_h = line_h * len(lines)
    cy = item.get("y", st["y"]) * H
    top = cy - block_h / 2

    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    widths = [font.getlength("".join(c for c, _ in ln)) for ln in lines]

    if st["box"] == "lines":
        # 인스타 텍스트 배경처럼 줄마다 폭이 다른 상자를 위아래로 붙인다.
        pad_x, radius = size * 0.5, size * 0.35
        for i, w_ in enumerate(widths):
            draw.rounded_rectangle(
                [(W - w_) / 2 - pad_x, top + line_h * i,
                 (W + w_) / 2 + pad_x, top + line_h * (i + 1)],
                radius=radius, fill=(0, 0, 0, 255))
    elif st["box"]:
        pad_x, pad_y = 36, 26
        bw = max(widths) + pad_x * 2
        draw.rounded_rectangle(
            [(W - bw) / 2, top - pad_y, (W + bw) / 2, top + block_h + pad_y],
            radius=28, fill=(0, 0, 0, 170))

    # 외곽선을 먼저 전부 그리고 글자를 위에 그려야 옆 글자를 덮지 않는다.
    for pass_ in ("stroke", "fill"):
        if pass_ == "stroke" and not stroke:
            continue
        for i, ln in enumerate(lines):
            x = (W - widths[i]) / 2
            y = top + line_h * (i + 0.5)
            for seg, acc in segments(ln):
                if pass_ == "stroke":
                    draw.text((x, y), seg, font=font, anchor="lm", fill=OUTLINE,
                              stroke_width=stroke, stroke_fill=OUTLINE)
                else:
                    draw.text((x, y), seg, font=font, anchor="lm",
                              fill=ACCENT if acc and st.get("accent", True) else WHITE)
                x += font.getlength(seg)
    img.save(path)


# ---------- 영상 ----------

def probe(src):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json",
         "-show_streams", "-show_format", src],
        capture_output=True, text=True, check=True)
    info = json.loads(out.stdout)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    return {
        "duration": float(info["format"]["duration"]),
        "transfer": v.get("color_transfer"),
        "audio": any(s["codec_type"] == "audio" for s in info["streams"]),
    }


def atempo_chain(speed):
    """atempo는 0.5~2.0만 받으니 나눠서 건다."""
    parts, s = [], speed
    while s > 2.0:
        parts.append("atempo=2.0")
        s /= 2.0
    while s < 0.5:
        parts.append("atempo=0.5")
        s /= 0.5
    parts.append(f"atempo={s:.4f}")
    return ",".join(parts)


def video_chain(clip, info):
    f = []
    # 아이폰 HDR(HLG/PQ)을 그대로 줄이면 색이 바래니 일반 색으로 변환한다.
    if info["transfer"] in ("arib-std-b67", "smpte2084"):
        f.append(f"zscale=tin={info['transfer']}:min=bt2020nc:pin=bt2020:t=linear:npl=100,"
                 "format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,"
                 "zscale=t=bt709:m=bt709:r=tv,format=yuv420p")
    speed = clip.get("speed", 1.0)
    if speed != 1.0:
        f.append(f"setpts=PTS/{speed}")
    zoom = clip.get("zoom", 1.0)
    zw, zh = int(W * zoom) // 2 * 2, int(H * zoom) // 2 * 2
    x = clip.get("x", 0.5)
    fill = (f"scale={zw}:{zh}:force_original_aspect_ratio=increase,"
            f"crop={W}:{H}:(iw-{W})*{x}:(ih-{H})/2")
    if clip.get("fit", "crop") == "blur":
        f.append(f"split[bg][fg];"
                 f"[bg]scale=270:480:force_original_aspect_ratio=increase,crop=270:480,"
                 f"boxblur=12:2,eq=brightness=-0.08,scale={W}:{H}[bgb];"
                 f"[fg]scale={W}:{H}:force_original_aspect_ratio=decrease[fgs];"
                 f"[bgb][fgs]overlay=(W-w)/2:(H-h)/2")
    else:
        f.append(fill)
    f.append(f"fps={FPS},setsar=1,format=yuv420p")
    return ",".join(f)


def build(plan, tmp, still=None, out_path=None):
    def resolve(p):
        return p if os.path.isabs(p) else os.path.normpath(os.path.join(ROOT, p))

    inputs, chains, concat_in = [], [], []

    def next_index():
        return sum(1 for x in inputs if x == "-i")

    total = 0.0
    for i, clip in enumerate(plan["clips"]):
        src = resolve(clip["src"])
        info = probe(src)
        start = clip.get("start", 0.0)
        end = clip.get("end") or info["duration"]
        speed = clip.get("speed", 1.0)
        length = (end - start) / speed
        total += length

        vi = next_index()
        inputs += ["-ss", f"{start}", "-to", f"{end}", "-i", src]
        chains.append(f"[{vi}:v]{video_chain(clip, info)}[v{i}]")

        if info["audio"] and not clip.get("mute"):
            a = [f"[{vi}:a]aresample=48000,aformat=channel_layouts=stereo"]
            if speed != 1.0:
                a.append(atempo_chain(speed))
            a.append(f"volume={clip.get('volume', 1.0)}")
            chains.append(",".join(a) + f"[a{i}]")
        else:
            si = next_index()
            inputs += ["-f", "lavfi", "-t", f"{length}", "-i",
                       "anullsrc=r=48000:cl=stereo"]
            chains.append(f"[{si}:a]anull[a{i}]")
        concat_in.append(f"[v{i}][a{i}]")

    n = len(plan["clips"])
    chains.append(f"{''.join(concat_in)}concat=n={n}:v=1:a=1[vc][ac]")

    last = "vc"
    for k, item in enumerate(plan.get("texts", [])):
        png = os.path.join(tmp, f"text_{k:02d}.png")
        render_text(item, png)
        ti = next_index()
        inputs += ["-i", png]
        s = item.get("start", 0.0)
        e = item.get("end")
        e = total if e is None else e
        chains.append(f"[{last}][{ti}:v]overlay=0:0:"
                      f"enable='between(t,{s},{e})'[t{k}]")
        last = f"t{k}"
    if still is None:
        chains.append("[ac]loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[aout]")
    else:
        chains.append("[ac]anullsink")

    cmd = ["ffmpeg", "-y", "-v", "error", *inputs,
           "-filter_complex", ";".join(chains), "-map", f"[{last}]"]
    if still is not None:
        cmd += ["-ss", f"{still}", "-frames:v", "1", out_path]
    else:
        cmd += ["-map", "[aout]",
                "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", f"{FPS}",
                "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                "-movflags", "+faststart", out_path]
    subprocess.run(cmd, check=True)
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("--still", type=float, help="이 시점 한 장면만 PNG로 (미리보기)")
    args = ap.parse_args()

    with open(args.plan, encoding="utf-8") as fp:
        plan = json.load(fp)
    out = plan["output"]
    out = out if os.path.isabs(out) else os.path.join(ROOT, out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if args.still is not None:
        out = os.path.splitext(out)[0] + f"_still_{args.still:.1f}s.png"

    with tempfile.TemporaryDirectory() as tmp:
        total = build(plan, tmp, args.still, out)

    size = os.path.getsize(out) / 1e6
    print(f"완성: {out} ({total:.1f}초, {size:.1f}MB)")


if __name__ == "__main__":
    sys.exit(main())
