# 2026-11-24 치과 한 장짜리 광고 (A: 굳은 치석은 양치로 안 떨어져요 / B: 입술 들어 보기 체크) — 4:5, A는 9:16도
# 사진: 몽글이 치아 (IMG_3130 2.4초 4K 원본 → teeth4k.png). 문구 근거: 병원 카드뉴스 4호(AAHA·WSAVA) 문장.
# 실행: python3 tools/dental_single_1124.py <장면 폴더>  → <장면 폴더>/dental/*.png
import sys, os
from PIL import Image, ImageDraw, ImageFont
S = sys.argv[1]; OUT = os.path.join(S, "dental"); os.makedirs(OUT, exist_ok=True)
FD = "/home/user/paul-manual/assets/fonts"
def F(w, s): return ImageFont.truetype(os.path.join(FD, f"Pretendard-{w}.otf"), s)
BG, INK, SUB, ACC, LINE, PILL = (250,248,244), (28,36,48), (98,106,118), (214,84,56), (226,221,212), (238,234,226)

def crop_frac(img, box):
    w, h = img.size; l, t, r, b = box
    return img.crop((int(l*w), int(t*h), int(r*w), int(b*h)))
def fit(img, size):
    tw, th = size; w, h = img.size; s = max(tw / w, th / h)
    img = img.resize((round(w*s), round(h*s)), Image.LANCZOS); w, h = img.size
    l, t = (w - tw) // 2, (h - th) // 2; return img.crop((l, t, l + tw, t + th))
def lines(d, x, y, rows, font, fill, gap=1.3, accent=ACC):
    for row in rows:
        cx = x
        for seg in row.split("|"):
            col = accent if seg.startswith("*") else fill; seg = seg.strip("*")
            d.text((cx, y), seg, font=font, fill=col); cx += d.textlength(seg, font=font)
        y += int(font.size * gap)
    return y
def tag(im, d, x, y, text):
    f = F("Bold", 30); w = d.textlength(text, font=f)
    ov = Image.new("RGBA", im.size, (0,0,0,0)); od = ImageDraw.Draw(ov)
    od.rounded_rectangle([x, y, x + w + 44, y + 58], 29, fill=(15,18,24,170))
    im.paste(Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB"))
    d.text((x + 22, y + 29), text, font=f, fill="white", anchor="lm")
def footer(d, W, H, top):
    d.line([(64, top), (W - 64, top)], fill=LINE, width=2)
    d.text((64, top + 30), "24시 폴 동물병원 · 분당 정자동", font=F("Black", 34), fill=INK)
    d.text((64, top + 80), "치과 상담  카카오톡 @폴동물병원 · 031-717-7558", font=F("Medium", 30), fill=SUB)

teeth = crop_frac(Image.open(f"{S}/teeth4k.png").convert("RGB"), (0.04, 0.06, 0.72, 0.42))

# A안: 사실 한 줄 (굳은 치석은 양치로 안 떨어진다)
def make_a(W, H, photo_h, head_y, foot_top, tag_y=40):
    im = Image.new("RGB", (W, H), BG); im.paste(fit(teeth, (W, photo_h)), (0, 0)); d = ImageDraw.Draw(im)
    tag(im, d, 40, tag_y, "실제 진료 사진 · 13살 푸들"); d = ImageDraw.Draw(im)
    y = lines(d, 64, head_y, ["누렇게 굳은 치석,", "양치로는 |*안 떨어져요"], F("Black", 76), INK, gap=1.24)
    y = lines(d, 64, y + 20, ["치태는 며칠이면 단단한 치석이 돼요.", "그때부터는 스케일링이 필요해요."], F("Medium", 38), SUB, gap=1.5)
    d.text((64, y + 26), "입 냄새·누런 치아가 보이면 치과 검진부터", font=F("Bold", 36), fill=ACC)
    footer(d, W, H, foot_top); return im

# B안: 지금 해 보기 (입술 들어 보기 체크)
def make_b(W, H):
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    lines(d, 64, 70, ["지금 우리 아이", "입술을 |*살짝 들어 보세요"], F("Black", 72), INK, gap=1.24)
    ph = fit(teeth, (W - 128, 520))
    m = Image.new("L", ph.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, ph.size[0]-1, ph.size[1]-1], 32, fill=255)
    im.paste(ph, (64, 280), m); d = ImageDraw.Draw(im)
    y = 840
    for t in ["이가 누렇거나 갈색이에요", "잇몸 끝이 빨갛거나 피가 나요", "입 냄새가 심해졌어요"]:
        d.rounded_rectangle([64, y + 4, 108, y + 48], 10, outline=ACC, width=5)
        d.text((132, y + 26), t, font=F("Bold", 40), fill=INK, anchor="lm"); y += 76
    d.text((64, y + 12), "하나라도 있으면 치과 검진부터 받아 보세요", font=F("Bold", 36), fill=ACC)
    footer(d, W, H, H - 170); return im

make_a(1080, 1350, 690, 730, 1200).save(f"{OUT}/치과_A_4x5.png")
make_a(1080, 1920, 880, 920, 1350, tag_y=250).save(f"{OUT}/치과_A_9x16.png")
make_b(1080, 1350).save(f"{OUT}/치과_B_4x5.png")
sheet = Image.new("RGB", (390*3 + 10, 700), "white")
for i, n in enumerate(["치과_A_4x5", "치과_B_4x5", "치과_A_9x16"]):
    im = Image.open(f"{OUT}/{n}.png"); im.thumbnail((380, 680)); sheet.paste(im, (10 + i*390, 10))
sheet.save(f"{S}/dental_sheet.jpg", quality=85); print("ok")
