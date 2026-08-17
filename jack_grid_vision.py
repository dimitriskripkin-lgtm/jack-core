import base64, io, re, json
from PIL import Image, ImageDraw, ImageFont

def grid_b64(raw_b64):
    img = Image.open(io.BytesIO(base64.b64decode(raw_b64)))
    W, H = img.size
    draw = ImageDraw.Draw(img)
    font = None
    for fp in ["/data/data/com.termux/files/usr/share/fonts/TTF/DejaVuSans.ttf",
               "/data/data/com.termux/files/usr/share/fonts/TTF/FreeMono.ttf"]:
        try:
            font = ImageFont.truetype(fp, 40)
            break
        except Exception:
            continue
    if font is None:
        font = ImageFont.load_default()
    for x in range(0, W, 200):
        draw.line([(x, 0), (x, H)], fill=(255, 0, 255), width=4)
        draw.text((x + 6, 100), str(x), fill=(255, 0, 255), font=font)
    for y in range(200, H, 200):
        draw.line([(0, y), (W, y)], fill=(255, 0, 255), width=4)
        draw.text((6, y + 6), str(y), fill=(255, 0, 255), font=font)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88)
    return base64.b64encode(buf.getvalue()).decode()

def find_element(target, vision_ask, get_screen_b64):
    gb = grid_b64(get_screen_b64())
    prompt = ("The image has a magenta grid with pixel coordinate labels. "
              "Find this element: " + target + ". "
              "Read its center position from the grid labels. "
              'Return ONLY JSON: {"x": <int>, "y": <int>}')
    res = vision_ask(prompt, b64=gb, max_px=1080, quality=88)
    m = re.search(r"\{[^}]+\}", res, re.DOTALL)
    if not m:
        return None, res
    p = json.loads(m.group())
    return (int(p["x"]), int(p["y"])), res
