# 2026-11-24 건강검진 카드형 광고 7장 (4:5, 1080x1350) — 몽글이 결과지 이야기
# 다시 만들기:
#   1) 원본(드라이브 릴스_원본)을 work/in/1105, work/in/1105b 에 받는다 (CLAUDE.md 1번 방법)
#   2) 장면 추출: talkf.mov 19.5·26.0·12.6초(dog_a·dog_b·dog_c, make_reel --still로 HDR 보정),
#      4K 원본에서 ffmpeg로 IMG_3130 2.4초(teeth4k), IMG_3139 28.8초(bladder4k), IMG_3138 18.0초(grid4k), IMG_3139 4.4초(cover4k)
#   3) python3 tools/cards_checkup_1124.py <장면 폴더>  → <장면 폴더>/cards/01~07.png
# 결과지 표지는 보호자 이름 줄 위까지만 자른다 (cover4k 0.03~0.73).
import sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S = sys.argv[1]; OUT = os.path.join(S, "cards")
FD = "/home/user/paul-manual/assets/fonts"
def F(w, s): return ImageFont.truetype(os.path.join(FD, f"Pretendard-{w}.otf"), s)
W, H = 1080, 1350
BG, INK, SUB, ACC, DARK, LINE = (250,248,244), (28,36,48), (98,106,118), (214,84,56), (20,24,31), (226,221,212)

def crop_frac(img, box):
    w, h = img.size; l, t, r, b = box
    return img.crop((int(l*w), int(t*h), int(r*w), int(b*h)))

def fit(img, size):  # 가운데 기준으로 잘라서 꽉 채우기
    tw, th = size; w, h = img.size
    s = max(tw / w, th / h); img = img.resize((round(w*s), round(h*s)), Image.LANCZOS)
    w, h = img.size; l, t = (w - tw) // 2, (h - th) // 2
    return img.crop((l, t, l + tw, t + th))

def paste_round(canvas, img, xy, r=36):
    m = Image.new("L", img.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, img.size[0]-1, img.size[1]-1], r, fill=255)
    canvas.paste(img, xy, m)

def text_lines(d, x, y, lines, font, fill, gap=1.38, accent=None):
    for ln in lines:
        cx = x
        for seg in ln.split("|"):  # |로 나눈 조각 중 *로 감싼 것은 강조색
            col = accent if (accent and seg.startswith("*")) else fill
            seg = seg.strip("*")
            d.text((cx, y), seg, font=font, fill=col); cx += d.textlength(seg, font=font)
        y += int(font.size * gap)
    return y

def header(d, page):
    d.text((60, 52), "폴 건강검진 이야기 · 13살 몽글이", font=F("Bold", 30), fill=SUB)
    t = f"{page} / 7"; d.text((W - 60 - d.textlength(t, font=F("Bold", 30)), 52), t, font=F("Bold", 30), fill=SUB)

def footer(d):
    d.line([(60, H - 92), (W - 60, H - 92)], fill=LINE, width=2)
    d.text((60, H - 70), "24시 폴 동물병원 · 분당 정자동", font=F("Medium", 28), fill=SUB)

def badge(d, x, y, n):
    d.ellipse([x, y, x + 76, y + 76], fill=ACC)
    f = F("Black", 44); tw = d.textlength(str(n), font=f)
    d.text((x + 38 - tw/2, y + 38), str(n), font=f, fill="white", anchor="lm")

def card_cover():
    im = Image.new("RGB", (W, H), DARK)
    photo = fit(crop_frac(Image.open(f"{S}/dog_a.png").convert("RGB"), (0.0, 0.22, 1.0, 0.78)), (W, 860))
    im.paste(photo, (0, 0))
    g = Image.new("L", (1, 220)); [g.putpixel((0, i), int(255 * i / 219)) for i in range(220)]
    im.paste(Image.new("RGB", (W, 220), DARK), (0, 640), g.resize((W, 220)))
    d = ImageDraw.Draw(im)
    y = text_lines(d, 64, 880, ["증상 하나 없던 13살,", "건강검진에서", "찾은 것 |*3가지"], F("Black", 92), "white", gap=1.2, accent=(255,140,110))
    d.text((66, H - 78), "24시 폴 동물병원 · 분당 정자동", font=F("Medium", 30), fill=(170,176,186))
    return im

def card_story():
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im); header(d, 2)
    paste_round(im, fit(crop_frac(Image.open(f"{S}/dog_c.png").convert("RGB"), (0.05, 0.28, 0.95, 0.78)), (960, 640)), (60, 120))
    y = text_lines(d, 60, 810, ["겉으로는", "아무 증상이 없었어요"], F("Black", 64), INK, gap=1.25)
    text_lines(d, 60, y + 24, ["13살 몽글이는 소변 볼 때도", "불편한 증상이 없었어요.", "그런데 검진에서 |*3가지|가 보였어요."], F("Medium", 40), SUB, gap=1.5, accent=ACC)
    footer(d); return im

def contain(img, size, bg=(12, 14, 18)):  # 잘리지 않게 전체를 넣고 남는 곳은 어두운 바탕
    tw, th = size; w, h = img.size; s = min(tw / w, th / h)
    img = img.resize((round(w*s), round(h*s)), Image.LANCZOS)
    out = Image.new("RGB", size, bg); out.paste(img, ((tw - img.size[0]) // 2, (th - img.size[1]) // 2))
    return out

def card_finding(page, n, img, title, body, imgsize=(960, 700), mode="fit"):
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im); header(d, page)
    paste_round(im, (contain if mode == "contain" else fit)(img, imgsize), (60, 120))
    y0 = 120 + imgsize[1] + 50
    badge(d, 60, y0, n)
    d.text((160, y0 + 38), title, font=F("Black", 60), fill=INK, anchor="lm")
    text_lines(d, 60, y0 + 120, body, F("Medium", 40), SUB, gap=1.5)
    footer(d); return im

def card_report():
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im); header(d, 6)
    rep = crop_frac(Image.open(f"{S}/cover4k.png").convert("RGB"), (0.0, 0.03, 1.0, 0.73))
    paste_round(im, fit(rep, (440, 560)), (60, 130), r=24)
    text_lines(d, 540, 150, ["결과는", "원장이 직접 쓴", "결과지로", "받아요"], F("Black", 62), INK, gap=1.25)
    items = ["예약제 1시간, 모든 검사를 한 번에", "이상이 보이면 추가 검사·치료까지 바로",
             "심장·내분비 정밀 검진 (심장초음파·proBNP)", "결과는 카카오톡으로도 보내드려요"]
    y = 760
    for it in items:
        d.ellipse([60, y + 12, 84, y + 36], fill=ACC)
        d.text((104, y), it, font=F("Bold", 40), fill=INK); y += 92
    footer(d); return im

def card_end():
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im); header(d, 7)
    paste_round(im, fit(crop_frac(Image.open(f"{S}/dog_b.png").convert("RGB"), (0.05, 0.30, 0.95, 0.70)), (960, 470)), (60, 120))
    y = text_lines(d, 60, 650, ["강아지·고양이의 1년은", "사람의 |*5년"], F("Black", 66), INK, gap=1.25, accent=ACC)
    y = text_lines(d, 60, y + 16, ["1년에 한 번,", "7살이 넘었다면 6개월에 한 번 검진을 권해요."], F("Medium", 40), SUB, gap=1.5)
    d.rounded_rectangle([60, y + 30, W - 60, y + 30 + 250], 28, fill=(238,234,226))
    yy = y + 60
    d.text((96, yy), "24시 폴 동물병원", font=F("Black", 44), fill=INK); yy += 70
    d.text((96, yy), "분당 정자동 · 정자역 5번 출구 도보 5분 · 무료 주차", font=F("Medium", 33), fill=SUB); yy += 56
    d.text((96, yy), "검진 예약  카카오톡 @폴동물병원 · 031-717-7558", font=F("Bold", 33), fill=ACC)
    return im

cards = [
    card_cover(),
    card_story(),
    card_finding(3, 1, crop_frac(Image.open(f"{S}/bladder4k.png").convert("RGB"), (0.38, 0.30, 0.99, 0.555)),
                 "방광 속 결석, 약 1cm", ["초음파에서 보였어요.", "아직 배뇨 증상이 없어서", "2개월 뒤 크기를 다시 확인해요."]),
    card_finding(4, 2, crop_frac(Image.open(f"{S}/grid4k.png").convert("RGB"), (0.755, 0.452, 1.0, 0.598)),
                 "비장 결절, 약 1.5cm", ["모양은 고르고 양호해 보여요.", "커지는지 2개월 뒤 다시 봐요."], mode="contain"),
    card_finding(5, 3, crop_frac(Image.open(f"{S}/teeth4k.png").convert("RGB"), (0.12, 0.10, 0.66, 0.40)),
                 "어금니 치석", ["치석이 많이 쌓여 스케일링이 필요해요.", "급하지는 않아요."]),
    card_report(),
    card_end(),
]
for i, c in enumerate(cards, 1):
    c.save(os.path.join(OUT, f"{i:02d}.png"))
sheet = Image.new("RGB", (4*370 + 10, 2*462 + 10), "white")
for i, c in enumerate(cards):
    sheet.paste(c.resize((360, 450)), (10 + (i % 4)*370, 10 + (i // 4)*462))
sheet.save(os.path.join(S, "cards_sheet.jpg"), quality=85)
print("ok")
