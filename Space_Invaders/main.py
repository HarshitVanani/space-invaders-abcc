"""
Space Invaders Game using Tkinter
=================================
Subject : Programming for Scientific Computing (Python) - CE0525, Semester V
Project : Mini Project - Space Invaders Game using Tkinter
Team    : Priyanshu Patel, Tilkesh Pawar, Harshit Vanani

Description
-----------
The player controls a spaceship at the bottom of the window and shoots down
waves of alien invaders. The game includes:

    * Game window (Tkinter Canvas) with a starry background
    * Spaceship, aliens, bullets, shields and a bonus UFO
    * Movement, shooting and collision detection
    * Scoring system, lives, levels and a persistent high score
    * Pause / restart / game-over handling

Controls
--------
    LEFT / A     : move left
    RIGHT / D    : move right
    SPACE        : shoot
    P            : pause / resume
    ENTER        : start game
    R            : restart (after game over or at any time)
    ESC          : quit

Only the Python standard library is used (tkinter, json, os, random).
Run with:   python main.py
"""

import json
import os
import random
import tkinter as tk

# --------------------------------------------------------------------------- #
# Configuration constants
# --------------------------------------------------------------------------- #
WIDTH, HEIGHT = 800, 640
FRAME_MS = 16                       # ~60 frames per second
MARGIN = 20                         # horizontal margin for the alien fleet
GROUND_Y = HEIGHT - 40              # y position of the ground line

PLAYER_SPEED = 6
PLAYER_START_LIVES = 3
PLAYER_FIRE_DELAY = 22              # frames between two shots
PLAYER_MAX_BULLETS = 3
PLAYER_BULLET_SPEED = 10
INVULNERABLE_FRAMES = 120           # frames of protection after being hit

ALIEN_ROWS, ALIEN_COLS = 5, 8
ALIEN_GAP_X, ALIEN_GAP_Y = 58, 42
ALIEN_DROP = 18                     # pixels the fleet drops at an edge
ALIEN_POINTS = {0: 30, 1: 20, 2: 10}  # row type -> points

BUNKER_COUNT = 4
BLOCK_SIZE = 8

UFO_POINTS = (50, 100, 150, 300)

HIGH_SCORE_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "highscore.json"
)

# Game states
STATE_START = "start"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"
STATE_LEVEL_CLEAR = "level_clear"
STATE_GAME_OVER = "game_over"

# Colours
COL_BG = "#05060f"
COL_PLAYER = "#35e06b"
COL_TEXT = "#f2f2f2"
COL_ACCENT = "#ffd84a"
ALIEN_COLORS = {0: "#ff5ec4", 1: "#5ee0ff", 2: "#9dff5e"}


# --------------------------------------------------------------------------- #
# Sprites
# --------------------------------------------------------------------------- #
class Sprite:
    """Base class: a rectangular game object made of one or more canvas items."""

    def __init__(self, canvas, x, y, w, h):
        self.canvas = canvas
        self.x, self.y = x, y          # top-left corner
        self.w, self.h = w, h
        self.items = []

    def move(self, dx, dy):
        self.x += dx
        self.y += dy
        for item in self.items:
            self.canvas.move(item, dx, dy)

    @property
    def rect(self):
        return self.x, self.y, self.x + self.w, self.y + self.h

    def collides(self, other):
        """Axis-aligned bounding-box collision test."""
        ax1, ay1, ax2, ay2 = self.rect
        bx1, by1, bx2, by2 = other.rect
        return ax1 < bx2 and ax2 > bx1 and ay1 < by2 and ay2 > by1

    def set_visible(self, visible):
        state = "normal" if visible else "hidden"
        for item in self.items:
            self.canvas.itemconfigure(item, state=state)

    def delete(self):
        for item in self.items:
            self.canvas.delete(item)
        self.items.clear()


class Player(Sprite):
    """The player's spaceship."""

    WIDTH, HEIGHT = 50, 24

    def __init__(self, canvas):
        x = (WIDTH - self.WIDTH) / 2
        y = GROUND_Y - self.HEIGHT - 12
        super().__init__(canvas, x, y, self.WIDTH, self.HEIGHT)
        c = canvas
        self.items = [
            c.create_rectangle(x, y + 12, x + 50, y + 24,
                               fill=COL_PLAYER, outline="", tags="game"),
            c.create_rectangle(x + 8, y + 6, x + 42, y + 12,
                               fill=COL_PLAYER, outline="", tags="game"),
            c.create_rectangle(x + 22, y, x + 28, y + 6,
                               fill="#b8ffd0", outline="", tags="game"),
        ]

    def move_by(self, dx):
        """Move horizontally while staying inside the window."""
        new_x = max(MARGIN / 2, min(WIDTH - MARGIN / 2 - self.w, self.x + dx))
        super().move(new_x - self.x, 0)


class Alien(Sprite):
    """One alien invader. `kind` (0-2) decides its colour and score value."""

    WIDTH, HEIGHT = 36, 26

    def __init__(self, canvas, x, y, kind):
        super().__init__(canvas, x, y, self.WIDTH, self.HEIGHT)
        self.kind = kind
        self.col = 0                       # column index inside the fleet
        self.points = ALIEN_POINTS[kind]
        color = ALIEN_COLORS[kind]
        c = canvas
        self.items = [
            c.create_rectangle(x + 4, y + 6, x + 32, y + 20,
                               fill=color, outline="", tags="game"),   # body
            c.create_rectangle(x, y + 10, x + 36, y + 16,
                               fill=color, outline="", tags="game"),   # arms
            c.create_rectangle(x + 9, y + 10, x + 14, y + 15,
                               fill=COL_BG, outline="", tags="game"),  # eye
            c.create_rectangle(x + 22, y + 10, x + 27, y + 15,
                               fill=COL_BG, outline="", tags="game"),  # eye
            c.create_rectangle(x + 6, y + 20, x + 11, y + 26,
                               fill=color, outline="", tags="game"),   # leg
            c.create_rectangle(x + 25, y + 20, x + 30, y + 26,
                               fill=color, outline="", tags="game"),   # leg
            c.create_line(x + 10, y + 6, x + 6, y,
                          fill=color, width=2, tags="game"),           # antenna
            c.create_line(x + 26, y + 6, x + 30, y,
                          fill=color, width=2, tags="game"),           # antenna
        ]


class Bullet(Sprite):
    """A projectile. Negative `vy` moves up (player), positive moves down."""

    WIDTH, HEIGHT = 4, 14

    def __init__(self, canvas, cx, y, vy, color):
        super().__init__(canvas, cx - self.WIDTH / 2, y, self.WIDTH, self.HEIGHT)
        self.vy = vy
        self.items = [
            canvas.create_rectangle(self.x, self.y, self.x + self.w,
                                    self.y + self.h, fill=color,
                                    outline="", tags="game")
        ]

    def update(self):
        self.move(0, self.vy)

    def off_screen(self):
        return self.y + self.h < 0 or self.y > HEIGHT


class Block(Sprite):
    """A single destructible block that makes up a shield (bunker)."""

    def __init__(self, canvas, x, y):
        super().__init__(canvas, x, y, BLOCK_SIZE, BLOCK_SIZE)
        self.items = [
            canvas.create_rectangle(x, y, x + BLOCK_SIZE, y + BLOCK_SIZE,
                                    fill="#2fbf5a", outline="#1c7a38",
                                    tags="game")
        ]


class Ufo(Sprite):
    """Bonus mystery ship that flies across the top of the screen."""

    WIDTH, HEIGHT = 44, 18

    def __init__(self, canvas, direction):
        x = -self.WIDTH if direction > 0 else WIDTH
        super().__init__(canvas, x, 52, self.WIDTH, self.HEIGHT)
        self.direction = direction
        self.speed = 3
        self.points = random.choice(UFO_POINTS)
        y = self.y
        self.items = [
            canvas.create_oval(x, y + 6, x + 44, y + 18,
                               fill="#ff4d4d", outline="", tags="game"),
            canvas.create_oval(x + 12, y, x + 32, y + 12,
                               fill="#ffb3b3", outline="", tags="game"),
        ]

    def update(self):
        self.move(self.direction * self.speed, 0)

    def off_screen(self):
        return self.x > WIDTH + 10 or self.x + self.w < -10


class Explosion:
    """Short-lived visual effect drawn when something is destroyed."""

    def __init__(self, canvas, cx, cy, color="#ffa500", size=16, life=14):
        self.canvas = canvas
        self.life = life
        self.item = canvas.create_oval(cx - size, cy - size, cx + size,
                                       cy + size, fill=color, outline="#fff2a8",
                                       width=2, tags="game")

    def update(self):
        """Advance the effect; return False once it should be removed."""
        self.life -= 1
        if self.life <= 0:
            self.canvas.delete(self.item)
            return False
        if self.life < 7:
            self.canvas.itemconfigure(self.item, fill="#8a3b00", outline="")
        return True

    def delete(self):
        self.canvas.delete(self.item)


# --------------------------------------------------------------------------- #
# Game controller
# --------------------------------------------------------------------------- #
class SpaceInvadersGame:
    """Owns the window, the game state and the main loop."""

    def __init__(self, root):
        self.root = root
        self.root.title("Space Invaders - Tkinter")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT,
                                bg=COL_BG, highlightthickness=0)
        self.canvas.pack()

        # Persistent / session data
        self.high_score = self.load_high_score()
        self.state = STATE_START
        self.score = 0
        self.lives = PLAYER_START_LIVES
        self.level = 1
        self.record_broken = False

        # Input handling
        self.keys = set()
        self._release_jobs = {}

        # Game objects
        self.player = None
        self.aliens = []
        self.blocks = []
        self.player_bullets = []
        self.alien_bullets = []
        self.explosions = []
        self.ufo = None

        # Timers / counters
        self.fire_cooldown = 0
        self.invulnerable = 0
        self.level_timer = 0
        self.fleet_dir = 1
        self.fleet_total = 1
        self.frame = 0

        self._loop_job = None
        self._running = True

        self.draw_background()
        self.create_hud()
        self.bind_keys()
        self.show_start_screen()

        self.root.protocol("WM_DELETE_WINDOW", self.quit)
        self._loop_job = self.root.after(FRAME_MS, self.loop)

    # ------------------------------------------------------------------ #
    # Persistence
    # ------------------------------------------------------------------ #
    @staticmethod
    def load_high_score():
        try:
            with open(HIGH_SCORE_FILE, "r", encoding="utf-8") as fh:
                return int(json.load(fh).get("high_score", 0))
        except (OSError, ValueError, TypeError, AttributeError):
            return 0

    def save_high_score(self):
        try:
            with open(HIGH_SCORE_FILE, "w", encoding="utf-8") as fh:
                json.dump({"high_score": self.high_score}, fh)
        except OSError:
            pass  # saving the score is optional; never crash the game

    # ------------------------------------------------------------------ #
    # Static drawing (background + HUD)
    # ------------------------------------------------------------------ #
    def draw_background(self):
        rng = random.Random(7)  # fixed seed -> same stars every run
        for _ in range(90):
            x, y = rng.randint(0, WIDTH), rng.randint(40, GROUND_Y)
            r = rng.choice((1, 1, 1, 2))
            shade = rng.choice(("#555a7a", "#8a90b8", "#c8ccee"))
            self.canvas.create_oval(x, y, x + r, y + r, fill=shade,
                                    outline="", tags="star")
        self.canvas.create_line(0, GROUND_Y, WIDTH, GROUND_Y,
                                fill="#2fbf5a", width=2, tags="star")

    def create_hud(self):
        font = ("Courier", 15, "bold")
        self.score_text = self.canvas.create_text(
            20, 20, anchor="w", fill=COL_TEXT, font=font, tags="hud")
        self.level_text = self.canvas.create_text(
            WIDTH / 2, 20, anchor="center", fill=COL_ACCENT, font=font,
            tags="hud")
        self.high_text = self.canvas.create_text(
            WIDTH - 20, 20, anchor="e", fill=COL_TEXT, font=font, tags="hud")
        self.lives_text = self.canvas.create_text(
            20, HEIGHT - 18, anchor="w", fill=COL_TEXT, font=font,
            tags="hud")
        self.update_hud()

    def update_hud(self):
        c = self.canvas
        c.itemconfigure(self.score_text, text=f"SCORE: {self.score:05d}")
        c.itemconfigure(self.level_text, text=f"LEVEL {self.level}")
        c.itemconfigure(self.high_text, text=f"HIGH: {self.high_score:05d}")
        c.itemconfigure(self.lives_text, text=f"LIVES: {max(self.lives, 0)}")

    # ------------------------------------------------------------------ #
    # Overlays (start / pause / game over / level clear)
    # ------------------------------------------------------------------ #
    def clear_overlay(self):
        self.canvas.delete("overlay")

    def draw_overlay(self, title, lines, title_color=COL_ACCENT):
        self.clear_overlay()
        c = self.canvas
        c.create_text(WIDTH / 2, HEIGHT / 2 - 110, text=title,
                      fill=title_color, font=("Courier", 40, "bold"),
                      tags="overlay")
        for i, line in enumerate(lines):
            c.create_text(WIDTH / 2, HEIGHT / 2 - 40 + i * 30, text=line,
                          fill=COL_TEXT, font=("Courier", 15), tags="overlay")

    def show_start_screen(self):
        self.state = STATE_START
        self.draw_overlay("SPACE INVADERS", [
            "LEFT / RIGHT or A / D  -  Move",
            "SPACE  -  Shoot",
            "P  -  Pause        ESC  -  Quit",
            "",
            "Press ENTER to start",
        ])

    # ------------------------------------------------------------------ #
    # Input
    # ------------------------------------------------------------------ #
    def bind_keys(self):
        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.bind("<KeyRelease>", self.on_key_release)
        self.root.focus_set()

    def on_key_press(self, event):
        key = event.keysym.lower()
        job = self._release_jobs.pop(key, None)
        if job is not None:               # key auto-repeat: cancel fake release
            self.root.after_cancel(job)
        is_repeat = key in self.keys
        self.keys.add(key)
        if is_repeat:
            return
        # One-shot actions (ignored while the key is auto-repeating)
        if key == "escape":
            self.quit()
        elif key == "return" and self.state == STATE_START:
            self.new_game()
        elif key == "p" and self.state in (STATE_PLAYING, STATE_PAUSED):
            self.toggle_pause()
        elif key == "r" and self.state != STATE_START:
            self.new_game()
        elif key == "return" and self.state == STATE_GAME_OVER:
            self.new_game()

    def on_key_release(self, event):
        key = event.keysym.lower()
        # Delay removal slightly so X11 auto-repeat does not cause stutter.
        if key in self._release_jobs:
            self.root.after_cancel(self._release_jobs[key])
        self._release_jobs[key] = self.root.after(
            12, lambda k=key: self._finish_release(k))

    def _finish_release(self, key):
        self._release_jobs.pop(key, None)
        self.keys.discard(key)

    def pressed(self, *names):
        return any(n in self.keys for n in names)

    # ------------------------------------------------------------------ #
    # Game setup
    # ------------------------------------------------------------------ #
    def new_game(self):
        """Reset everything and start from level 1."""
        self.score = 0
        self.lives = PLAYER_START_LIVES
        self.level = 1
        self.record_broken = False
        self.reset_world()
        self.state = STATE_PLAYING
        self.clear_overlay()
        self.update_hud()

    def reset_world(self):
        """Rebuild all game objects for the current level."""
        self.canvas.delete("game")
        self.player_bullets.clear()
        self.alien_bullets.clear()
        self.explosions.clear()
        self.aliens.clear()
        self.blocks.clear()
        self.ufo = None
        self.fire_cooldown = 0
        self.invulnerable = 0
        self.fleet_dir = 1
        self.player = Player(self.canvas)
        self.build_wave()
        self.build_bunkers()

    def build_wave(self):
        top = 80 + min(self.level - 1, 4) * 10
        left = (WIDTH - ((ALIEN_COLS - 1) * ALIEN_GAP_X + Alien.WIDTH)) / 2
        for row in range(ALIEN_ROWS):
            kind = 0 if row == 0 else (1 if row < 3 else 2)
            for col in range(ALIEN_COLS):
                alien = Alien(self.canvas,
                              left + col * ALIEN_GAP_X,
                              top + row * ALIEN_GAP_Y,
                              kind)
                alien.col = col
                self.aliens.append(alien)
        self.fleet_total = len(self.aliens)

    def build_bunkers(self):
        cols, rows = 9, 4
        bunker_w = cols * BLOCK_SIZE
        spacing = WIDTH / BUNKER_COUNT
        top = self.player.y - 95
        for i in range(BUNKER_COUNT):
            left = spacing * i + (spacing - bunker_w) / 2
            for r in range(rows):
                for c in range(cols):
                    if r == rows - 1 and 3 <= c <= 5:   # arch-shaped gap
                        continue
                    self.blocks.append(Block(
                        self.canvas,
                        left + c * BLOCK_SIZE,
                        top + r * BLOCK_SIZE))

    # ------------------------------------------------------------------ #
    # Pause / quit
    # ------------------------------------------------------------------ #
    def toggle_pause(self):
        if self.state == STATE_PLAYING:
            self.state = STATE_PAUSED
            self.draw_overlay("PAUSED", ["Press P to resume"])
        elif self.state == STATE_PAUSED:
            self.state = STATE_PLAYING
            self.clear_overlay()

    def quit(self):
        if not self._running:
            return
        self._running = False
        self.save_high_score()
        if self._loop_job is not None:
            try:
                self.root.after_cancel(self._loop_job)
            except tk.TclError:
                pass
        self.root.destroy()

    # ------------------------------------------------------------------ #
    # Main loop
    # ------------------------------------------------------------------ #
    def loop(self):
        if not self._running:
            return
        self.frame += 1
        self.update_explosions()
        if self.state == STATE_PLAYING:
            self.update_playing()
        elif self.state == STATE_LEVEL_CLEAR:
            self.update_level_clear()
        self.update_hud()
        self._loop_job = self.root.after(FRAME_MS, self.loop)

    def update_playing(self):
        self.handle_player_input()
        self.update_fleet()
        if self.state != STATE_PLAYING:          # fleet may have reached the ground
            return
        self.update_player_bullets()
        self.update_alien_bullets()
        if self.state != STATE_PLAYING:          # player may have lost last life
            return
        self.update_ufo()
        self.alien_shoot()
        self.update_invulnerability()
        if not self.aliens and self.state == STATE_PLAYING:
            self.start_level_clear()

    # ------------------------------------------------------------------ #
    # Player
    # ------------------------------------------------------------------ #
    def handle_player_input(self):
        if self.pressed("left", "a"):
            self.player.move_by(-PLAYER_SPEED)
        if self.pressed("right", "d"):
            self.player.move_by(PLAYER_SPEED)

        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1
        if (self.pressed("space") and self.fire_cooldown == 0
                and len(self.player_bullets) < PLAYER_MAX_BULLETS):
            self.player_bullets.append(Bullet(
                self.canvas, self.player.x + self.player.w / 2,
                self.player.y - Bullet.HEIGHT, -PLAYER_BULLET_SPEED, "#ffffff"))
            self.fire_cooldown = PLAYER_FIRE_DELAY

    def update_invulnerability(self):
        if self.invulnerable > 0:
            self.invulnerable -= 1
            self.player.set_visible((self.invulnerable // 6) % 2 == 0)
            if self.invulnerable == 0:
                self.player.set_visible(True)

    def player_hit(self):
        """Handle the player being struck by an alien bullet."""
        self.lives -= 1
        cx = self.player.x + self.player.w / 2
        cy = self.player.y + self.player.h / 2
        self.explosions.append(Explosion(self.canvas, cx, cy,
                                         color="#35e06b", size=26, life=20))
        for bullet in self.alien_bullets:
            bullet.delete()
        self.alien_bullets.clear()
        if self.lives <= 0:
            self.game_over()
        else:
            self.invulnerable = INVULNERABLE_FRAMES

    # ------------------------------------------------------------------ #
    # Aliens
    # ------------------------------------------------------------------ #
    def fleet_speed(self):
        """Fleet speeds up as aliens are destroyed and as levels increase."""
        base = 0.6 + 0.25 * (self.level - 1)
        destroyed = (self.fleet_total - len(self.aliens)) / self.fleet_total
        return min(base * (1 + destroyed * 2.5), 6.0)

    def update_fleet(self):
        if not self.aliens:
            return
        dx = self.fleet_dir * self.fleet_speed()
        leftmost = min(a.x for a in self.aliens)
        rightmost = max(a.x + a.w for a in self.aliens)

        hit_edge = ((self.fleet_dir > 0 and rightmost + dx > WIDTH - MARGIN) or
                    (self.fleet_dir < 0 and leftmost + dx < MARGIN))
        if hit_edge:
            self.fleet_dir *= -1
            for alien in self.aliens:
                alien.move(0, ALIEN_DROP)
        else:
            for alien in self.aliens:
                alien.move(dx, 0)

        lowest = max(a.y + a.h for a in self.aliens)
        # Aliens trample through shields
        if self.blocks and lowest >= min(b.y for b in self.blocks):
            for alien in self.aliens:
                for block in self.blocks[:]:
                    if alien.collides(block):
                        block.delete()
                        self.blocks.remove(block)
        # Invasion succeeded -> game over
        if lowest >= self.player.y:
            self.lives = 0
            self.game_over()

    def alien_shoot(self):
        if not self.aliens:
            return
        max_bullets = min(2 + self.level, 8)
        chance = min(0.012 + 0.003 * self.level, 0.04)
        if len(self.alien_bullets) >= max_bullets or random.random() > chance:
            return
        # Only the lowest alien of each column may shoot
        bottom = {}
        for alien in self.aliens:
            if alien.col not in bottom or alien.y > bottom[alien.col].y:
                bottom[alien.col] = alien
        shooter = random.choice(list(bottom.values()))
        speed = min(4 + 0.3 * self.level, 8)
        self.alien_bullets.append(Bullet(
            self.canvas, shooter.x + shooter.w / 2,
            shooter.y + shooter.h, speed, "#ff6b6b"))

    # ------------------------------------------------------------------ #
    # Bullets, collisions and scoring
    # ------------------------------------------------------------------ #
    def add_score(self, points):
        self.score += points
        if self.score > self.high_score:
            self.high_score = self.score
            self.record_broken = True

    def update_player_bullets(self):
        for bullet in self.player_bullets[:]:
            bullet.update()
            if bullet.off_screen() or self.hit_block(bullet):
                self.remove_bullet(bullet, self.player_bullets)
                continue
            # Bullet vs alien
            target = next((a for a in self.aliens if bullet.collides(a)), None)
            if target is not None:
                self.destroy_alien(target)
                self.remove_bullet(bullet, self.player_bullets)
                continue
            # Bullet vs UFO
            if self.ufo is not None and bullet.collides(self.ufo):
                self.add_score(self.ufo.points)
                self.explosions.append(Explosion(
                    self.canvas, self.ufo.x + self.ufo.w / 2,
                    self.ufo.y + self.ufo.h / 2, color="#ff4d4d", size=22))
                self.ufo.delete()
                self.ufo = None
                self.remove_bullet(bullet, self.player_bullets)

    def update_alien_bullets(self):
        for bullet in self.alien_bullets[:]:
            bullet.update()
            if bullet.off_screen() or self.hit_block(bullet):
                self.remove_bullet(bullet, self.alien_bullets)
                continue
            if self.invulnerable == 0 and bullet.collides(self.player):
                self.remove_bullet(bullet, self.alien_bullets)
                self.player_hit()
                if self.state != STATE_PLAYING:
                    return

    def hit_block(self, bullet):
        """Destroy the first shield block the bullet touches (if any)."""
        for block in self.blocks:
            if bullet.collides(block):
                block.delete()
                self.blocks.remove(block)
                return True
        return False

    @staticmethod
    def remove_bullet(bullet, collection):
        bullet.delete()
        if bullet in collection:
            collection.remove(bullet)

    def destroy_alien(self, alien):
        self.add_score(alien.points)
        self.explosions.append(Explosion(
            self.canvas, alien.x + alien.w / 2, alien.y + alien.h / 2,
            color=ALIEN_COLORS[alien.kind]))
        alien.delete()
        self.aliens.remove(alien)

    # ------------------------------------------------------------------ #
    # UFO and explosions
    # ------------------------------------------------------------------ #
    def update_ufo(self):
        if self.ufo is None:
            if random.random() < 0.0016 and self.aliens:
                self.ufo = Ufo(self.canvas, random.choice((-1, 1)))
            return
        self.ufo.update()
        if self.ufo.off_screen():
            self.ufo.delete()
            self.ufo = None

    def update_explosions(self):
        self.explosions = [e for e in self.explosions if e.update()]

    # ------------------------------------------------------------------ #
    # Level flow and game over
    # ------------------------------------------------------------------ #
    def start_level_clear(self):
        self.state = STATE_LEVEL_CLEAR
        self.level_timer = 100
        self.add_score(100 * self.level)           # level clear bonus
        for bullet in self.alien_bullets + self.player_bullets:
            bullet.delete()
        self.alien_bullets.clear()
        self.player_bullets.clear()
        if self.ufo is not None:
            self.ufo.delete()
            self.ufo = None
        self.draw_overlay(f"LEVEL {self.level} CLEARED",
                          [f"Bonus: +{100 * self.level}", "Get ready..."],
                          title_color="#35e06b")

    def update_level_clear(self):
        self.level_timer -= 1
        if self.level_timer <= 0:
            self.level += 1
            self.reset_world()
            self.clear_overlay()
            self.state = STATE_PLAYING

    def game_over(self):
        self.state = STATE_GAME_OVER
        self.save_high_score()
        new_record = self.record_broken
        lines = [f"Final score: {self.score}",
                 f"High score : {self.high_score}"]
        if new_record:
            lines.append("NEW HIGH SCORE!")
        lines += ["", "Press R or ENTER to play again", "ESC to quit"]
        self.draw_overlay("GAME OVER", lines, title_color="#ff5555")


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def main():
    root = tk.Tk()
    SpaceInvadersGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()