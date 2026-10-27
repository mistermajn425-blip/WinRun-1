"""WinRun — раннер в стиле Subway Surfers на Kivy (Python 3.12+).
Управление: свайпы (вверх — прыжок, вниз — быстрое приземление) или стрелки/WASD на ПК."""
import math
import os
import random

from kivy.app import App
from kivy.clock import Clock
from kivy.core.image import Image as CI
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line, Rectangle, RoundedRectangle
from kivy.storage.jsonstore import JsonStore
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.utils import platform

if platform != "android":
    Window.size = (405, 720)

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
ZMAX = 50.0
LOCS = ("city", "beach", "night", "snow")
NAMES = ("Город", "Пляж", "Ночной город", "Снежный город")
# препятствие: (высота спрайта в долях экрана, высокое? — только объезд)
OBS = {"train_blue": (.30, 1), "train_red": (.30, 1), "train_yellow": (.30, 1), "light": (.34, 1),
       "barrier": (.09, 0), "crate_grey": (.10, 0), "crate_gold": (.10, 0), "crate_wood": (.10, 0),
       "barricade": (.11, 0), "trash": (.11, 0), "cone": (.08, 0), "barrel": (.11, 0), "bollard": (.12, 0)}
POWER = {"magnet": 8, "star": 6, "x2": 10, "shoe": 8}  # длительность, сек
_tex = {}


def T(name):
    if name not in _tex:
        _tex[name] = CI(os.path.join(D, name + ".png")).texture
    return _tex[name]


class Game(Widget):
    def __init__(self, save_dir, **kw):
        super().__init__(**kw)
        try:
            self.store = JsonStore(os.path.join(save_dir, "winrun.json"))
            self.best = self.store.get("s")["best"] if self.store.exists("s") else 0
        except Exception:
            self.store, self.best = None, 0
        self.loc, self.mode, self.t = 0, "menu", 0.0
        self.btns, self.lbls = {}, {}
        self.base = self.hor = self.sp = 0
        self.reset()
        Window.bind(on_keyboard=self.on_key)
        Clock.schedule_interval(self.update, 1 / 60)

    # ---------- состояние ----------
    def reset(self):
        self.lane, self.px = 1, 1.0
        self.jy = self.vy = 0.0
        self.items, self.fx = [], []
        self.dist = self.score = 0.0
        self.coins, self.hearts, self.hurt, self.chase = 0, 3, 0.0, 0.0
        self.pw = dict.fromkeys(POWER, 0.0)
        self.nxt, self.safe, self.speed = 10.0, 1, 16.0

    def start(self):
        self.reset()
        self.mode = "play"

    def finish(self):
        self.mode = "over"
        self.best = max(self.best, int(self.score))
        try:
            self.store.put("s", best=self.best)
        except Exception:
            pass

    def proj(self, lane, z):
        s = 1 / (1 + max(z, -1.0) * .09)
        return (self.width / 2 + (lane - 1) * self.sp * s,
                self.base + (self.hor - self.base) * (1 - s), s)

    # ---------- логика ----------
    def spawn(self):
        self.safe = min(2, max(0, self.safe + random.choice((-1, 0, 1))))  # всегда есть проход
        r = random.random()
        if r < .3:
            l = random.randrange(3)
            self.items += [["coin", l, ZMAX + i * 1.4] for i in range(6)]
        elif r < .92:
            free = [l for l in range(3) if l != self.safe]
            for l in random.sample(free, random.choice((1, 2))):
                self.items.append([random.choice(tuple(OBS)), l, ZMAX])
            if random.random() < .6:
                self.items += [["coin", self.safe, ZMAX + i * 1.4] for i in range(4)]
        else:
            k = random.choice(("magnet", "star", "x2", "shoe", "chest"))
            self.items.append([k, random.randrange(3), ZMAX])

    def add_fx(self, name, it):
        x, y, s = self.proj(it[1], it[2])
        self.fx.append([name, x, y + .04 * self.height * s, 0.0])

    def touch_item(self, it):
        """True — предмет «съеден» (подобран / разбит / ударил)."""
        k = it[0]
        if k == "coin":
            self.coins += 2 if self.pw["x2"] > 0 else 1
            self.score += 10
            self.add_fx("sun", it)
            return True
        if k == "chest":
            self.coins += 20
            self.score += 200
            self.add_fx("sun", it)
            return True
        if k in POWER:
            self.pw[k] = POWER[k]
            return True
        if self.pw["star"] > 0:  # на доске всё сносим
            self.add_fx("sun", it)
            return True
        if self.hurt > 0 or (not OBS[k][1] and self.jy > .7):
            return False  # перепрыгнули / неуязвимость
        self.hearts -= 1
        self.hurt, self.chase = 1.5, 1.6
        self.add_fx("splat", it)
        if self.hearts <= 0:
            self.finish()
        return True

    def step(self, dt):
        self.speed = 16 + min(16, self.dist / 120)
        v = self.speed * dt
        self.dist += v
        self.score += v * (2 if self.pw["x2"] > 0 else 1)
        self.hurt, self.chase = max(0, self.hurt - dt), max(0, self.chase - dt)
        for k in self.pw:
            self.pw[k] = max(0, self.pw[k] - dt)
        for f in self.fx:
            f[3] += dt
        self.fx = [f for f in self.fx if f[3] < .5]
        self.px += (self.lane - self.px) * min(1, dt * 14)
        if self.jy > 0 or self.vy > 0:
            self.jy += self.vy * dt
            self.vy -= 30 * dt
            if self.jy <= 0:
                self.jy = self.vy = 0.0
        self.nxt -= v
        if self.nxt <= 0:
            self.spawn()
            self.nxt = random.uniform(.55, .9) * self.speed
        for it in self.items[:]:
            it[2] -= v
            if it[0] == "coin" and self.pw["magnet"] > 0 and it[2] < 18:
                it[1] += (self.px - it[1]) * min(1, dt * 6)
                it[2] -= v * .5
            if -.8 < it[2] < .8 and abs(it[1] - self.px) < .55:
                if self.touch_item(it):
                    self.items.remove(it)
            elif it[2] < -1.5:
                self.items.remove(it)

    def update(self, dt):
        dt = min(dt, .05)
        self.t += dt
        if self.mode == "play":
            self.step(dt)
        if self.width < 10:
            return
        W, H = self.size
        self.base, self.hor, self.sp = H * .13, H * .42, W * .27
        self.btns = {}
        for l in self.lbls.values():
            l.opacity = 0
        c = self.canvas.before
        c.clear()
        with c:
            if self.mode == "menu":
                self.menu()
            else:
                self.world()
                self.hud()
                if self.mode == "pause":
                    self.overlay("ПАУЗА", (("resume", "ПРОДОЛЖИТЬ"), ("menu", "МЕНЮ")))
                elif self.mode == "over":
                    self.overlay("ИГРА ОКОНЧЕНА", (("again", "ЗАНОВО"), ("menu", "МЕНЮ")), True)

    # ---------- рисование ----------
    def spr(self, n, cx, y, h, a=1.0, mw=None, sx=1.0):
        t = T(n)
        r = t.width / t.height
        w = h * r
        if mw and w > mw:
            w, h = mw, mw / r
        Color(1, 1, 1, a)
        Rectangle(texture=t, pos=(cx - w * sx / 2, y), size=(w * sx, h))

    def cover(self, n):
        t = T(n)
        W, H = self.size
        k = max(W / t.width, H / t.height)
        w, h = t.width * k, t.height * k
        Color(1, 1, 1, 1)
        Rectangle(texture=t, pos=((W - w) / 2, (H - h) / 2), size=(w, h))

    def put(self, key, text, x, y, fs, color=(1, 1, 1, 1), left=False):
        l = self.lbls.get(key)
        if l is None:
            l = self.lbls[key] = Label(bold=True, outline_width=3, outline_color=(0, .05, .15, 1),
                                       size_hint=(None, None))
            self.add_widget(l)
        if l.text != text or l.font_size != fs:
            l.text, l.font_size = text, fs
            l.texture_update()
        l.color, l.size, l.opacity = color, l.texture_size, 1
        if left:
            l.pos = (x, y - l.height / 2)
        else:
            l.center = (x, y)

    def button(self, key, text, cx, cy, w, h, col=(1, .62, .05)):
        Color(0, 0, 0, .5)
        RoundedRectangle(pos=(cx - w / 2 + 3, cy - h / 2 - 6), size=(w, h), radius=[h * .3])
        Color(*col, 1)
        RoundedRectangle(pos=(cx - w / 2, cy - h / 2), size=(w, h), radius=[h * .3])
        Color(1, 1, 1, .3)
        RoundedRectangle(pos=(cx - w / 2 + 6, cy), size=(w - 12, h / 2 - 5), radius=[h * .2])
        self.btns[key] = (cx - w / 2, cy - h / 2, w, h)
        self.put("b_" + key, text, cx, cy, h * .45)

    def menu(self):
        W, H = self.size
        self.cover("art")
        Color(0, 0, 0, .5)
        Rectangle(pos=(0, 0), size=(W, H * .38))
        self.put("best", "Рекорд: %d" % self.best, W / 2, H * .355, H * .026, (1, .85, .2, 1))
        for i, n in enumerate(LOCS):
            cx, h = W * (.125 + .25 * i), H * .2
            t = T("bg_" + n)
            w = min(h * t.width / t.height, W * .22)
            self.spr("bg_" + n, cx, H * .15, h, 1, W * .22)
            if i == self.loc:
                Color(1, .8, 0, 1)
            else:
                Color(1, 1, 1, .4)
            Line(rectangle=(cx - w / 2, H * .15, w, h), width=3 if i == self.loc else 1.5)
            self.btns["loc%d" % i] = (cx - w / 2, H * .15, w, h)
            self.put("l%d" % i, NAMES[i], cx, H * .125, H * .017)
        self.button("play", "ИГРАТЬ", W / 2, H * .06, W * .6, H * .07)

    def world(self):
        W, H = self.size
        self.cover("bg_" + LOCS[self.loc])
        Color(0, 0, 0, .22)  # бегущие шпалы — ощущение скорости
        off = self.dist % 3
        for i in range(14):
            z = i * 3 - off
            x0, y, s = self.proj(-.5, z)
            Line(points=(x0, y, self.proj(2.5, z)[0], y), width=1 + 2 * s)
        for k, lane, z in sorted(self.items, key=lambda i: -i[2]):
            x, y, s = self.proj(lane, z)
            a = min(1, (ZMAX - z) / 8)
            if k in OBS:
                self.spr("o_" + k, x, y, OBS[k][0] * H * s, a, self.sp * .95 * s)
            elif k == "coin":
                self.spr("p_coin", x, y + .035 * H * s, .05 * H * s, a,
                         sx=.25 + .75 * abs(math.cos(self.t * 6 + z)))
            else:
                self.spr("p_" + k, x, y + .03 * H * s, .075 * H * s, a)
        x, y, s = self.proj(self.px, 0)
        Color(0, 0, 0, .3)
        Ellipse(pos=(x - .06 * W, self.base - .008 * H), size=(.12 * W, .02 * H))
        y += self.jy * .09 * H
        a = .45 if self.hurt > 0 and int(self.t * 16) % 2 else 1
        if self.pw["star"] > 0:
            self.spr("run_board%d" % (int(self.t * 8) % 2), x, y, .17 * H, a, W * .4)
        else:
            self.spr("run%d" % (int(self.t * 14) % 8), x, y, .20 * H, a)
        if self.chase > 0:  # охранник и собака на хвосте
            a = min(1, self.chase)
            self.spr("guard", W * .24, self.base - .05 * H, .2 * H, a)
            self.spr("dog", W * .76, self.base - .04 * H, .09 * H, a)
        for n, fx, fy, age in self.fx:
            h = (.07 if n == "sun" else .18) * H * (1 + age * 2)
            self.spr("fx_" + n, fx, fy - h / 2, h, max(0, 1 - age * 2))

    def hud(self):
        W, H = self.size
        self.spr("ui_crown", .06 * W, H * .935, H * .045)
        self.put("score", str(int(self.score)), .12 * W, H * .957, H * .03, left=True)
        self.spr("p_coin", .06 * W, H * .885, H * .04)
        self.put("coins", str(self.coins), .12 * W, H * .905, H * .026, (1, .9, .3, 1), left=True)
        for i in range(self.hearts):
            self.spr("ui_heart", W / 2 + (i - 1) * .09 * W, H * .935, H * .04)
        if self.mode == "play":
            self.spr("ui_pause", .9 * W, H * .925, H * .06)
            self.btns["pause"] = (.8 * W, H * .9, .2 * W, H * .1)
        y = .86 * H
        for k, v in self.pw.items():
            if v > 0:
                self.spr("p_" + k, .93 * W, y, .045 * H)
                Color(1, 1, 1, .8)
                Rectangle(pos=(.8 * W, y + .015 * H), size=(.11 * W * v / POWER[k], .012 * H))
                y -= .06 * H

    def overlay(self, title, buttons, stats=False):
        W, H = self.size
        Color(0, 0, 0, .65)
        Rectangle(pos=(0, 0), size=self.size)
        self.put("t", title, W / 2, H * .66, H * .045, (1, .75, .1, 1))
        if stats:
            self.put("s1", "Счёт: %d" % self.score, W / 2, H * .58, H * .034)
            self.put("s2", "Рекорд: %d   Монеты: %d" % (self.best, self.coins), W / 2, H * .53, H * .024)
        for i, (k, txt) in enumerate(buttons):
            self.button(k, txt, W / 2, H * (.42 - .1 * i), W * .6, H * .075)

    # ---------- ввод ----------
    def move(self, d):
        if self.mode == "play":
            self.lane = min(2, max(0, self.lane + d))

    def jump(self):
        if self.mode == "play" and self.jy == 0 and self.vy == 0:
            self.vy = 9.5 * (1.3 if self.pw["shoe"] > 0 else 1)

    def down(self):
        if self.mode == "play" and self.jy > 0:
            self.vy = -18

    def press(self, k):
        if k.startswith("loc"):
            self.loc = int(k[3:])
        elif k in ("play", "again"):
            self.start()
        elif k == "pause":
            self.mode = "pause"
        elif k == "resume":
            self.mode = "play"
        elif k == "menu":
            self.mode = "menu"

    def on_touch_down(self, t):
        for k, (x, y, w, h) in self.btns.items():
            if x <= t.x <= x + w and y <= t.y <= y + h:
                self.press(k)
                return True
        t.ud["p"] = t.pos
        return True

    def on_touch_move(self, t):
        p = t.ud.get("p")
        if not p or self.mode != "play":
            return True
        dx, dy = t.x - p[0], t.y - p[1]
        if max(abs(dx), abs(dy)) > self.width * .07:
            if abs(dx) > abs(dy):
                self.move(1 if dx > 0 else -1)
            elif dy > 0:
                self.jump()
            else:
                self.down()
            t.ud["p"] = None
        return True

    def on_key(self, win, key, *args):
        if key == 27:  # Esc / «Назад» на Android
            if self.mode == "play":
                self.mode = "pause"
            elif self.mode == "pause":
                self.mode = "play"
            elif self.mode == "over":
                self.mode = "menu"
            else:
                return False
            return True
        if key in (13, 32) and self.mode in ("menu", "over"):
            self.start()
        elif key in (276, 97):
            self.move(-1)
        elif key in (275, 100):
            self.move(1)
        elif key in (273, 119, 32):
            self.jump()
        elif key in (274, 115):
            self.down()
        else:
            return False
        return True


class WinRunApp(App):
    title = "WinRun"

    def build(self):
        self.game = Game(self.user_data_dir)
        return self.game

    def on_pause(self):
        if self.game.mode == "play":
            self.game.mode = "pause"
        return True


if __name__ == "__main__":
    WinRunApp().run()
