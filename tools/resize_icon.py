from PIL import Image
from pathlib import Path

p = Path(__file__).parents[1] / 'icon.png'
if not p.exists():
    raise SystemExit('icon.png not found')
img = Image.open(p).convert('RGBA')
img.thumbnail((128, 128), Image.LANCZOS)
# ensure exact size by placing on white background
bg = Image.new('RGBA', (128,128), (255,255,255,0))
# center
x = (128 - img.width) // 2
y = (128 - img.height) // 2
bg.paste(img, (x,y), img)
out = Path(__file__).parents[1] / 'icon_small.png'
bg.save(out)
print('Saved', out)
