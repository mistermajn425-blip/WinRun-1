"""Вырезает ассеты из tools/sheet.png в assets/ (фон убирается).
Запуск: python tools/extract_assets.py   (нужны pillow и numpy)"""
import os

import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets")

# имя x1 y1 x2 y2 [*]  — координаты листа 1312x1199, * = без удаления фона
TABLE = """
art 0 0 407 568 *
bg_city 15 608 140 885 *
bg_beach 150 608 274 885 *
bg_night 283 608 408 885 *
bg_snow 417 608 541 885 *
hero_mike 428 50 556 285
hero_lina 560 50 662 285
hero_jay 672 50 782 285
hero_chris 788 55 896 285
guard 925 70 1062 288
dog 1062 165 1172 292
robot 1180 72 1298 272
skin1 430 380 500 545
skin2 520 380 602 545
skin3 610 380 692 545
skin4 700 380 777 545
skin5 788 380 865 545
board1 912 385 990 548
board2 990 385 1052 548
board3 1052 385 1137 548
board4 1140 385 1212 548
board5 1215 385 1297 550
o_train_blue 575 612 674 704
o_train_red 684 612 772 704
o_train_yellow 780 612 852 704
o_barrier 870 615 948 692
o_light 960 608 1012 793
o_crate_grey 583 710 674 797
o_crate_gold 693 710 784 797
o_crate_wood 803 710 894 797
o_bollard 908 700 950 793
o_barricade 695 810 778 893
o_trash 786 810 843 895
o_cone 843 810 902 895
o_barrel 908 810 962 895
p_coin 1060 620 1122 684
p_magnet 1056 693 1134 774
p_star 1143 698 1212 772
p_x2 1222 700 1294 774
p_shoe 1066 788 1160 867
p_chest 1182 783 1284 882
ui_avatar 14 958 96 1047
ui_crown 106 970 142 1000
ui_pause 242 974 298 1028
ui_heart 242 1036 276 1068
icon_shop 376 968 446 1038
icon_bag 456 968 526 1038
icon_missions 536 968 602 1038
icon_settings 608 968 676 1038
emo1 703 964 777 1044
emo2 781 964 854 1044
emo3 856 964 929 1044
emo4 930 964 1000 1044
fx_arrow 1026 970 1114 1042
fx_sun 1112 973 1184 1042
fx_smoke 1190 960 1284 1024
fx_purple 1068 1038 1194 1114
fx_splat 1196 1028 1288 1100
run0 2 1106 78 1190
run1 82 1106 158 1190
run2 170 1106 246 1190
run3 260 1106 336 1190
run4 350 1106 426 1190
run5 439 1106 515 1190
run6 529 1106 605 1190
run7 619 1106 695 1190
run_board0 726 1094 864 1190
run_board1 880 1094 958 1190
"""


def label(mask):
    """Связные области (4-соседство) без scipy."""
    h, w = mask.shape
    lab, n = np.zeros((h, w), int), 0
    for sy, sx in zip(*np.nonzero(mask)):
        if lab[sy, sx]:
            continue
        n += 1
        lab[sy, sx] = n
        stack = [(sy, sx)]
        while stack:
            y, x = stack.pop()
            for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= yy < h and 0 <= xx < w and mask[yy, xx] and not lab[yy, xx]:
                    lab[yy, xx] = n
                    stack.append((yy, xx))
    return lab, n


def cut(img, box, opaque):
    crop = img.crop(box).convert("RGB")
    if opaque:
        return crop.convert("RGBA")
    a = np.asarray(crop).astype(int)
    border = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
    bg = np.median(border, axis=0)
    lab, _ = label(np.abs(a - bg).max(axis=2) < 10)
    edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    fg = ~np.isin(lab, list(edge))
    lab, n = label(fg)  # выкидываем мусор (обрывки подписей и соседей)
    if n:
        sizes = np.bincount(lab.ravel())[1:]
        fg = np.isin(lab, [i + 1 for i, s in enumerate(sizes) if s >= sizes.max() * 0.12])
    alpha = Image.fromarray((fg * 255).astype("uint8"))
    alpha = alpha.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
    out = crop.convert("RGBA")
    out.putalpha(alpha)
    return out.crop(alpha.getbbox() or (0, 0) + out.size)


def main():
    img = Image.open(os.path.join(HERE, "sheet.png")).convert("RGB")
    sx, sy = img.width / 1312, img.height / 1199
    os.makedirs(OUT, exist_ok=True)
    for line in TABLE.strip().splitlines():
        p = line.split()
        x1, y1, x2, y2 = map(int, p[1:5])
        box = (round(x1 * sx), round(y1 * sy), round(x2 * sx), round(y2 * sy))
        cut(img, box, len(p) > 5).save(os.path.join(OUT, p[0] + ".png"))
    # иконка приложения 512x512
    av = Image.open(os.path.join(OUT, "ui_avatar.png"))
    side = max(av.size)
    icon = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    icon.paste(av, ((side - av.width) // 2, (side - av.height) // 2))
    icon.resize((512, 512), Image.LANCZOS).save(os.path.join(OUT, "icon.png"))
    print("готово:", len(os.listdir(OUT)), "файлов в assets/")


if __name__ == "__main__":
    main()
