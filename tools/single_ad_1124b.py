# 2026-11-24 한 장짜리 광고 다시 만들기 (사진 없이 글자 하나로 멈추게 하는 3안) — 4:5 1080x1350
# 1안 숫자 반전: "작년에 받은 건강검진, 약 5년 전" (7살 이후 1년 ≈ 사람 4~5살, 큰 개는 더 빠름)
# 2안 고백형: "솔직히, 저희는 광고를 잘 못해요 / 대신 365일 새벽에도 불을 켜 둡니다"
# 3안 번호 저장: "새벽 3시에 검색하지 마세요" + 메모지에 전화번호
# 실행: python3 tools/single_ad_1124b.py <저장 폴더>
import sys, os, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
FD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "fonts")
def F(w, s): return ImageFont.truetype(os.path.join(FD, f"Pretendard-{w}.otf"), s)
W, H = 1080, 1350
PHONE = "031-717-7558"

def grain(im, amount=7, seed=1):
    random.seed(seed)
    n = Image.effect_noise(im.size, 40).convert("L").point(lambda v: 128 + (v - 128) * amount // 40)
    return Image.composite(im, im, n) if False else Image.blend(im, Image.merge("RGB", (n, n, n)), 0.035)

def center(d, y, text, font, fill):
    d.text((W // 2, y), text, font=font, fill=fill, anchor="mt")

def highlight(d, x, y, text, font, fill, mark, pad=8):
    """형광펜 칠한 글자 한 줄"""
    w = d.textlength(text, font=font); a, b = font.getmetrics()
    d.rectangle([x - pad, y + int(a * 0.42), x + w + pad, y + a + int(b * 0.3)], fill=mark)
    d.text((x, y), text, font=font, fill=fill)
    return x + w

# 1안: 숫자 반전 ─────────────────────────────────────────────
def ad1():
    BG, INK, Y, SUB = (18, 34, 52), (246, 243, 236), (255, 206, 84), (150, 166, 184)
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    d.text((80, 120), "작년에 받은", font=F("Bold", 70), fill=INK)
    d.text((80, 212), "건강검진,", font=F("Bold", 70), fill=INK)
    d.text((80, 360), "사람 나이로 치면", font=F("Medium", 52), fill=SUB)
    # 큰 숫자
    big = F("Black", 400)
    d.text((80, 420), "약", font=F("Black", 96), fill=Y)
    x = 80 + d.textlength("약 ", font=F("Black", 96))
    d.text((x - 10, 360), "5년", font=big, fill=Y)
    d.text((86, 840), "전이에요.", font=F("Black", 96), fill=INK)
    d.text((80, 1000), "7살이 넘으면 1년에 사람 나이로 약 4~5살씩 먹어요.", font=F("Medium", 34), fill=SUB)
    d.text((80, 1048), "큰 개는 더 빨라요. 그래서 노령견은 1년에 두 번을 권해요.", font=F("Medium", 34), fill=SUB)
    d.line([(80, 1150), (W - 80, 1150)], fill=(48, 66, 88), width=2)
    d.text((80, 1188), "분당 정자동 24시 폴 동물병원", font=F("Black", 38), fill=INK)
    d.text((W - 80, 1192), PHONE, font=F("Bold", 36), fill=Y, anchor="ra")
    return grain(im)

# 2안: 고백형 ───────────────────────────────────────────────
def ad2():
    BG, INK, SUB, ACC, MARK = (244, 239, 229), (30, 32, 36), (112, 108, 100), (206, 84, 52), (255, 214, 102)
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    d.text((80, 150), "솔직히 말하면,", font=F("Bold", 50), fill=ACC)
    f = F("Black", 108)
    y = 240
    for t in ["저희 병원은", "광고를", "잘 못해요."]:
        d.text((80, y), t, font=f, fill=INK); y += 138
    d.text((80, y + 36), "그래서 이것도 그냥 글씨만 썼어요.", font=F("Medium", 42), fill=SUB)
    y = 840
    d.text((80, y), "대신 365일,", font=F("Bold", 72), fill=INK); y += 104
    highlight(d, 80, y, "새벽에도 불을 켜 둡니다.", F("Bold", 72), INK, MARK)
    d.line([(80, 1150), (W - 80, 1150)], fill=(214, 206, 192), width=2)
    d.text((80, 1188), "분당 정자동 24시 폴 동물병원", font=F("Black", 38), fill=INK)
    d.text((W - 80, 1192), PHONE, font=F("Bold", 36), fill=ACC, anchor="ra")
    return grain(im)

# 3안: 번호 저장 (메모지) ─────────────────────────────────────
def ad3():
    BG, INK, SUB, PAPER, PIN = (28, 30, 38), (246, 244, 238), (160, 164, 176), (255, 248, 222), (232, 92, 62)
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    center(d, 110, "새벽 3시에", F("Black", 96), INK)
    center(d, 228, "검색하지 마세요.", F("Black", 96), INK)
    center(d, 368, "그땐 손이 떨려서 아무것도 눈에 안 들어와요.", F("Medium", 38), SUB)
    # 메모지 (그림자 + 살짝 기울임)
    mw, mh = 820, 560
    memo = Image.new("RGBA", (mw, mh), (0, 0, 0, 0)); md = ImageDraw.Draw(memo)
    md.rounded_rectangle([0, 0, mw - 1, mh - 1], 24, fill=PAPER + (255,))
    md.rounded_rectangle([0, 0, mw - 1, 92], 24, fill=(255, 214, 102, 255))
    md.rectangle([0, 60, mw - 1, 92], fill=(255, 214, 102, 255))
    md.text((44, 46), "미리 저장해 둘 번호", font=F("Bold", 40), fill=(60, 48, 20), anchor="lm")
    md.text((44, 150), "새벽·주말·공휴일에도 여는 곳", font=F("Medium", 38), fill=(110, 100, 80))
    md.text((44, 236), PHONE, font=F("Black", 96), fill=(30, 32, 36))
    md.text((44, 372), "24시 폴 동물병원", font=F("Black", 50), fill=(30, 32, 36))
    md.text((44, 452), "분당 정자동 · 365일 24시간", font=F("Medium", 38), fill=(110, 100, 80))
    rot = memo.rotate(-2.2, resample=Image.BICUBIC, expand=True)
    sh = Image.new("RGBA", rot.size, (0, 0, 0, 0))
    sh.paste((0, 0, 0, 150), (0, 0), rot.split()[3]); sh = sh.filter(ImageFilter.GaussianBlur(22))
    px, py = (W - rot.size[0]) // 2, 470
    base = im.convert("RGBA"); base.alpha_composite(sh, (px + 10, py + 24)); base.alpha_composite(rot, (px, py))
    im = base.convert("RGB"); d = ImageDraw.Draw(im)
    d.ellipse([W // 2 - 20, py + 4, W // 2 + 20, py + 44], fill=PIN)
    center(d, 1150, "지금 '연락처에 저장' 해 두세요.", F("Bold", 44), INK)
    center(d, 1222, "그날 밤, 한 번에 전화할 수 있게.", F("Medium", 38), SUB)
    return grain(im)

for name, fn in [("1안_검진5년", ad1), ("2안_고백", ad2), ("3안_번호저장", ad3)]:
    fn().save(os.path.join(OUT, f"{name}_4x5.png"))
sheet = Image.new("RGB", (370 * 3 + 40, 480), "white")
for i, n in enumerate(["1안_검진5년", "2안_고백", "3안_번호저장"]):
    t = Image.open(os.path.join(OUT, f"{n}_4x5.png")); t.thumbnail((360, 460)); sheet.paste(t, (10 + i * 375, 10))
sheet.save(os.path.join(OUT, "sheet.jpg"), quality=88); print("ok")
