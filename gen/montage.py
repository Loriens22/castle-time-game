import sys, glob
from PIL import Image
out = sys.argv[1]; files = sys.argv[2:]; ims = [Image.open(f) for f in files]
cols = min(len(ims), int(sys.argv[0] and 6)); h = max(i.height for i in ims); w = max(i.width for i in ims)
cols = min(6, len(ims)); rows = (len(ims) + cols - 1) // cols
M = Image.new('RGB', (w * cols, h * rows), (30, 30, 30))
for k, im in enumerate(ims): M.paste(im, ((k % cols) * w, (k // cols) * h))
sc = min(1.0, 1800 / M.width); M = M.resize((int(M.width * sc), int(M.height * sc))); M.save(out)
