import turtle
import math
import random
import time
import json
import os
from abc import ABC, abstractmethod
from enum import Enum, auto


# ================================================================
# STICKMAN ARENA: ADVANCED EDITION
# ----------------------------------------------------------------
# A real-time turtle-graphics fighting game featuring:
#   - Full menu flow: main menu -> character select -> fight
#   - Four playable characters with unique stats & special moves
#   - Light/heavy punches & kicks, uppercuts, sweeps, dashes
#   - Energy-fueled special moves (unique per character)
#   - Combo counter with live damage scaling
#   - Stamina-limited blocking with a parry window
#   - Knockdown / wake-up invulnerability mechanic
#   - Screen shake, floating damage numbers, brief hit-stop
#   - Four difficulty tiers that scale the AI's aggression
#   - Best-of-N round structure with transition screens
#   - Persistent profile: wins/losses + unlockable achievements
#   - Optional local two-player mode
# ================================================================


# ----------------------------------------------------------------
# CONFIG & ENUMS
# ----------------------------------------------------------------

class GameConfig:
    WIDTH = 1050
    HEIGHT = 700
    FRAME_MS = 16
    GROUND_Y = -170
    ARENA_LEFT = -450
    ARENA_RIGHT = 450
    PLAYER_START_X = -220
    ENEMY_START_X = 220
    ROUND_TIME = 60
    ROUNDS_TO_WIN = 2
    SAVE_FILE = "stickman_fighter_save.json"


class GameState(Enum):
    MAIN_MENU = auto()
    CHARACTER_SELECT = auto()
    FIGHTING = auto()
    PAUSED = auto()
    ROUND_TRANSITION = auto()
    GAME_OVER = auto()


class Difficulty(Enum):
    EASY = "Easy"
    NORMAL = "Normal"
    HARD = "Hard"
    NIGHTMARE = "Nightmare"


DIFFICULTY_ORDER = [
    Difficulty.EASY,
    Difficulty.NORMAL,
    Difficulty.HARD,
    Difficulty.NIGHTMARE
]


DIFFICULTY_MULTIPLIERS = {
    Difficulty.EASY: {
        "damage": 0.75,
        "reaction": 1.5,
        "aggression": 0.65
    },
    Difficulty.NORMAL: {
        "damage": 1.0,
        "reaction": 1.0,
        "aggression": 1.0
    },
    Difficulty.HARD: {
        "damage": 1.15,
        "reaction": 0.65,
        "aggression": 1.3
    },
    Difficulty.NIGHTMARE: {
        "damage": 1.35,
        "reaction": 0.4,
        "aggression": 1.65
    }
}


class MoveType(Enum):
    LIGHT_PUNCH = auto()
    HEAVY_PUNCH = auto()
    LIGHT_KICK = auto()
    HEAVY_KICK = auto()
    UPPERCUT = auto()
    SWEEP = auto()
    SPECIAL = auto()
    PROJECTILE = auto()
    DASH = auto()


# Frame counts and energy/stamina costs for each move type.
# Kept centralized so balance tweaks happen in one place.
MOVE_STARTUP = {
    MoveType.LIGHT_PUNCH: 8,
    MoveType.HEAVY_PUNCH: 16,
    MoveType.LIGHT_KICK: 10,
    MoveType.HEAVY_KICK: 20,
    MoveType.UPPERCUT: 18,
    MoveType.SWEEP: 14,
}

MOVE_ACTIVE_WINDOW = {
    MoveType.LIGHT_PUNCH: 5,
    MoveType.HEAVY_PUNCH: 7,
    MoveType.LIGHT_KICK: 6,
    MoveType.HEAVY_KICK: 9,
    MoveType.UPPERCUT: 8,
    MoveType.SWEEP: 7,
}

MOVE_COOLDOWN = {
    MoveType.LIGHT_PUNCH: 10,
    MoveType.HEAVY_PUNCH: 22,
    MoveType.LIGHT_KICK: 14,
    MoveType.HEAVY_KICK: 30,
    MoveType.UPPERCUT: 34,
    MoveType.SWEEP: 26,
}

MOVE_ENERGY_COST = {
    MoveType.LIGHT_PUNCH: 4,
    MoveType.HEAVY_PUNCH: 10,
    MoveType.LIGHT_KICK: 6,
    MoveType.HEAVY_KICK: 14,
    MoveType.UPPERCUT: 16,
    MoveType.SWEEP: 12,
    MoveType.PROJECTILE: 30,
    MoveType.SPECIAL: 55,
    MoveType.DASH: 8,
}

MOVE_REACH = {
    MoveType.LIGHT_PUNCH: 40,
    MoveType.HEAVY_PUNCH: 48,
    MoveType.LIGHT_KICK: 44,
    MoveType.HEAVY_KICK: 52,
    MoveType.UPPERCUT: 40,
    MoveType.SWEEP: 46,
}


# ----------------------------------------------------------------
# MATH / TIMING HELPERS
# ----------------------------------------------------------------

class Vector2:
    def __init__(self, x=0, y=0):
        self.x = float(x)
        self.y = float(y)

    def copy(self):
        return Vector2(self.x, self.y)

    def add(self, other):
        self.x += other.x
        self.y += other.y
        return self

    def subtract(self, other):
        self.x -= other.x
        self.y -= other.y
        return self

    def multiply(self, value):
        self.x *= value
        self.y *= value
        return self

    def length(self):
        return math.sqrt(self.x * self.x + self.y * self.y)

    def normalized(self):
        length = self.length()
        if length == 0:
            return Vector2()
        return Vector2(self.x / length, self.y / length)

    def distance_to(self, other):
        return math.sqrt(
            (self.x - other.x) ** 2 +
            (self.y - other.y) ** 2
        )


class Timer:
    def __init__(self):
        self.start_time = time.time()
        self.paused_time = 0
        self.paused = False
        self.pause_started = None

    def reset(self):
        self.start_time = time.time()
        self.paused_time = 0
        self.paused = False
        self.pause_started = None

    def pause(self):
        if not self.paused:
            self.paused = True
            self.pause_started = time.time()

    def resume(self):
        if self.paused:
            self.paused_time += time.time() - self.pause_started
            self.paused = False
            self.pause_started = None

    def elapsed(self):
        current = self.pause_started if self.paused else time.time()
        return current - self.start_time - self.paused_time


def clamp(value, low, high):
    return max(low, min(high, value))


def lerp(a, b, t):
    return a + (b - a) * t


class GameObject(ABC):
    def __init__(self, x, y):
        self.position = Vector2(x, y)
        self.velocity = Vector2()
        self.active = True

    @abstractmethod
    def update(self, game):
        pass

    @abstractmethod
    def draw(self):
        pass


# ----------------------------------------------------------------
# LOW LEVEL DRAWING
# ----------------------------------------------------------------

class GraphicsObject:
    def __init__(self, color="white", pensize=3):
        self.pen = turtle.Turtle()
        self.pen.hideturtle()
        self.pen.speed(0)
        self.pen.penup()
        self.pen.color(color)
        self.pen.pensize(pensize)

    def clear(self):
        self.pen.clear()

    def set_color(self, color):
        self.pen.color(color)

    def line(self, x1, y1, x2, y2):
        self.pen.penup()
        self.pen.goto(x1, y1)
        self.pen.pendown()
        self.pen.goto(x2, y2)
        self.pen.penup()

    def circle(self, x, y, radius):
        self.pen.penup()
        self.pen.goto(x, y - radius)
        self.pen.setheading(0)
        self.pen.pendown()
        self.pen.circle(radius)
        self.pen.penup()

    def dot(self, x, y, size):
        self.pen.penup()
        self.pen.goto(x, y)
        self.pen.dot(size)
        self.pen.penup()

    def filled_circle(self, x, y, radius, color):
        self.pen.penup()
        self.pen.goto(x, y - radius)
        self.pen.setheading(0)
        self.pen.fillcolor(color)
        self.pen.begin_fill()
        self.pen.pendown()
        self.pen.circle(radius)
        self.pen.end_fill()
        self.pen.penup()

    def polygon(self, points):
        if not points:
            return
        self.pen.penup()
        self.pen.goto(points[0][0], points[0][1])
        self.pen.pendown()
        for point in points[1:]:
            self.pen.goto(point[0], point[1])
        self.pen.goto(points[0][0], points[0][1])
        self.pen.penup()

    def filled_rect(self, x, y, width, height, color):
        self.pen.penup()
        self.pen.goto(x, y)
        self.pen.fillcolor(color)
        self.pen.begin_fill()
        self.pen.pendown()
        for px, py in [
            (x + width, y),
            (x + width, y + height),
            (x, y + height),
            (x, y)
        ]:
            self.pen.goto(px, py)
        self.pen.end_fill()
        self.pen.penup()


class ScreenShake:
    """Tracks a decaying random offset applied to arena drawing."""

    def __init__(self):
        self.timer = 0
        self.intensity = 0
        self.offset_x = 0
        self.offset_y = 0

    def trigger(self, intensity, duration):
        self.intensity = max(self.intensity, intensity)
        self.timer = max(self.timer, duration)

    def update(self):
        if self.timer > 0:
            self.timer -= 1
            fade = self.timer / 12.0
            magnitude = self.intensity * max(0, fade)
            self.offset_x = random.uniform(-magnitude, magnitude)
            self.offset_y = random.uniform(-magnitude, magnitude)
            if self.timer <= 0:
                self.offset_x = 0
                self.offset_y = 0
        else:
            self.offset_x = 0
            self.offset_y = 0


# ----------------------------------------------------------------
# TRANSIENT VISUAL EFFECTS
# ----------------------------------------------------------------

class Particle(GameObject):
    def __init__(self, x, y, color, velocity, life, size):
        super().__init__(x, y)
        self.velocity = velocity.copy()
        self.color = color
        self.life = life
        self.max_life = life
        self.size = size
        self.gravity = -0.15
        self.graphics = GraphicsObject(color)

    def update(self, game):
        if not self.active:
            return
        self.position.add(self.velocity)
        self.velocity.y += self.gravity
        self.life -= 1
        if self.life <= 0:
            self.active = False

    def draw(self):
        if not self.active:
            return
        self.graphics.clear()
        ratio = self.life / self.max_life
        size = max(1, int(self.size * ratio))
        self.graphics.dot(self.position.x, self.position.y, size)


class HitEffect(GameObject):
    def __init__(self, x, y, color="yellow", big=False):
        super().__init__(x, y)
        self.radius = 5
        self.growth = 5 if big else 3
        self.graphics = GraphicsObject(color, 3 if big else 2)
        self.life = 16 if big else 12

    def update(self, game):
        self.radius += self.growth
        self.life -= 1
        if self.life <= 0:
            self.active = False

    def draw(self):
        if not self.active:
            return
        self.graphics.clear()
        self.graphics.circle(self.position.x, self.position.y, self.radius)


class DamageNumber(GameObject):
    """Floating combat text popup used for damage, PARRY!, BLOCKED, etc."""

    def __init__(self, x, y, text, color="white", size=14):
        super().__init__(x, y)
        self.text = text
        self.color = color
        self.size = size
        self.life = 34
        self.max_life = 34
        self.writer = turtle.Turtle()
        self.writer.hideturtle()
        self.writer.penup()
        self.writer.speed(0)
        self.writer.color(color)

    def update(self, game):
        self.position.y += 1.4
        self.life -= 1
        if self.life <= 0:
            self.active = False

    def draw(self):
        self.writer.clear()
        if not self.active:
            return
        fade_ratio = self.life / self.max_life
        size = max(8, int(self.size * (0.6 + 0.4 * fade_ratio)))
        self.writer.goto(self.position.x, self.position.y)
        self.writer.write(
            self.text,
            align="center",
            font=("Arial", size, "bold")
        )

    def wipe(self):
        self.writer.clear()


class ComboPopup(GameObject):
    """Big flashy combo counter text that appears mid-arena."""

    def __init__(self, x, y, hits):
        super().__init__(x, y)
        self.hits = hits
        self.life = 40
        self.max_life = 40
        self.writer = turtle.Turtle()
        self.writer.hideturtle()
        self.writer.penup()
        self.writer.speed(0)

    def update(self, game):
        self.life -= 1
        if self.life <= 0:
            self.active = False

    def draw(self):
        self.writer.clear()
        if not self.active:
            return
        ratio = self.life / self.max_life
        size = int(18 + 10 * min(1.0, (self.max_life - self.life) / 6.0))
        color = "#ffcc00" if self.hits < 6 else "#ff5050"
        self.writer.color(color)
        self.writer.goto(self.position.x, self.position.y)
        self.writer.write(
            f"{self.hits} HIT COMBO!",
            align="center",
            font=("Arial", size, "bold")
        )

    def wipe(self):
        self.writer.clear()


class Projectile(GameObject):
    def __init__(self, owner, x, y, direction, damage=8, speed=8,
                 radius=7, life=90, color=None, piercing=False):
        super().__init__(x, y)
        self.owner = owner
        self.direction = direction
        self.speed = speed
        self.life = life
        self.radius = radius
        self.damage = damage
        self.piercing = piercing
        self.hit_targets = set()
        self.graphics = GraphicsObject(color or owner.character.projectile_color, 2)

    def update(self, game):
        if not self.active:
            return
        self.position.x += self.direction * self.speed
        self.life -= 1

        target = game.enemy if self.owner is game.player else game.player

        already_hit = id(target) in self.hit_targets

        if not already_hit and self.position.distance_to(target.position) < 35:
            target.take_damage(self.damage, self.owner, game, source_move=MoveType.PROJECTILE)
            game.create_hit_effect(self.position.x, self.position.y, target.character.color)
            self.hit_targets.add(id(target))
            if not self.piercing:
                self.active = False

        if abs(self.position.x) > game.arena.width / 2:
            self.active = False

        if self.life <= 0:
            self.active = False

    def draw(self):
        if not self.active:
            return
        self.graphics.clear()
        self.graphics.dot(self.position.x, self.position.y, self.radius)


# ----------------------------------------------------------------
# UI BARS
# ----------------------------------------------------------------

class Bar:
    """Generic horizontal meter (health / energy / stamina)."""

    def __init__(self, x, y, width, height, color, bg_color="#303030"):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.bg_color = bg_color
        self.background = GraphicsObject(bg_color, 1)
        self.foreground = GraphicsObject(color, 1)

    def _fill_rect(self, graphics, x, y, width, height, color):
        graphics.pen.penup()
        graphics.pen.goto(x, y)
        graphics.pen.fillcolor(color)
        graphics.pen.begin_fill()
        graphics.pen.pendown()
        for px, py in [
            (x + width, y),
            (x + width, y + height),
            (x, y + height)
        ]:
            graphics.pen.goto(px, py)
        graphics.pen.goto(x, y)
        graphics.pen.end_fill()
        graphics.pen.penup()

    def draw(self, value, max_value, flash=False):
        self.background.clear()
        self.foreground.clear()

        self._fill_rect(
            self.background, self.x, self.y,
            self.width, self.height, self.bg_color
        )

        ratio = clamp(value / max_value if max_value else 0, 0, 1)
        current_width = self.width * ratio
        color = "#ffffff" if flash else self.color

        if current_width > 0:
            self._fill_rect(
                self.foreground, self.x, self.y,
                current_width, self.height, color
            )


class HealthBar(Bar):
    pass


# ----------------------------------------------------------------
# CHARACTER DEFINITIONS
# ----------------------------------------------------------------

class SpecialType(Enum):
    ENERGY_WAVE = auto()
    SHADOW_DASH = auto()
    GROUND_SLAM = auto()
    TRIPLE_BURST = auto()


class CharacterDefinition:
    def __init__(
        self, key, name, color, projectile_color, description,
        special_name, special_type,
        max_health, max_energy, max_stamina,
        speed, jump_power,
        light_punch, heavy_punch, light_kick, heavy_kick,
        uppercut, sweep, special_damage
    ):
        self.key = key
        self.name = name
        self.color = color
        self.projectile_color = projectile_color
        self.description = description
        self.special_name = special_name
        self.special_type = special_type

        self.max_health = max_health
        self.max_energy = max_energy
        self.max_stamina = max_stamina

        self.speed = speed
        self.jump_power = jump_power

        self.damage = {
            MoveType.LIGHT_PUNCH: light_punch,
            MoveType.HEAVY_PUNCH: heavy_punch,
            MoveType.LIGHT_KICK: light_kick,
            MoveType.HEAVY_KICK: heavy_kick,
            MoveType.UPPERCUT: uppercut,
            MoveType.SWEEP: sweep,
            MoveType.SPECIAL: special_damage,
        }


def build_character_roster():
    roster = [
        CharacterDefinition(
            key="ronin",
            name="RONIN",
            color="#00eaff",
            projectile_color="#00ffff",
            description="Balanced all-rounder. Easy to learn.",
            special_name="ENERGY WAVE",
            special_type=SpecialType.ENERGY_WAVE,
            max_health=100, max_energy=100, max_stamina=100,
            speed=4.0, jump_power=12,
            light_punch=7, heavy_punch=14, light_kick=9, heavy_kick=17,
            uppercut=15, sweep=11, special_damage=26
        ),
        CharacterDefinition(
            key="whisper",
            name="WHISPER",
            color="#c86bff",
            projectile_color="#e2b3ff",
            description="Fast, fragile, relentless pressure.",
            special_name="SHADOW DASH",
            special_type=SpecialType.SHADOW_DASH,
            max_health=82, max_energy=110, max_stamina=90,
            speed=5.6, jump_power=13.5,
            light_punch=6, heavy_punch=11, light_kick=8, heavy_kick=14,
            uppercut=12, sweep=9, special_damage=24
        ),
        CharacterDefinition(
            key="titan",
            name="TITAN",
            color="#ff8a3d",
            projectile_color="#ffbb66",
            description="Slow but hits like a truck.",
            special_name="GROUND SLAM",
            special_type=SpecialType.GROUND_SLAM,
            max_health=125, max_energy=90, max_stamina=115,
            speed=2.9, jump_power=10.5,
            light_punch=9, heavy_punch=18, light_kick=11, heavy_kick=21,
            uppercut=19, sweep=14, special_damage=32
        ),
        CharacterDefinition(
            key="specter",
            name="SPECTER",
            color="#ff304f",
            projectile_color="#ff5570",
            description="Zoner. Wins fights at a distance.",
            special_name="TRIPLE BURST",
            special_type=SpecialType.TRIPLE_BURST,
            max_health=88, max_energy=115, max_stamina=95,
            speed=3.6, jump_power=12,
            light_punch=6, heavy_punch=12, light_kick=8, heavy_kick=15,
            uppercut=13, sweep=10, special_damage=10
        ),
    ]
    return roster


# ----------------------------------------------------------------
# FIGHTER STATE MACHINE
# ----------------------------------------------------------------

class FighterState(ABC):
    @abstractmethod
    def update(self, fighter, game):
        pass

    def label(self):
        return self.__class__.__name__.replace("State", "")


class IdleState(FighterState):
    def update(self, fighter, game):
        fighter.velocity.x *= 0.7


class WalkingState(FighterState):
    def update(self, fighter, game):
        fighter.velocity.x *= 0.9


class JumpingState(FighterState):
    def update(self, fighter, game):
        fighter.velocity.y += fighter.gravity


class BlockingState(FighterState):
    def update(self, fighter, game):
        fighter.velocity.x *= 0.5


class AttackingState(FighterState):
    def update(self, fighter, game):
        fighter.velocity.x *= 0.8


class DashingState(FighterState):
    def update(self, fighter, game):
        fighter.velocity.x *= 0.95


class StunnedState(FighterState):
    def update(self, fighter, game):
        fighter.velocity.x *= 0.85


class KnockedDownState(FighterState):
    def update(self, fighter, game):
        fighter.velocity.x *= 0.9


# ----------------------------------------------------------------
# COMBO TRACKING
# ----------------------------------------------------------------

class ComboTracker:
    WINDOW_FRAMES = 48

    def __init__(self):
        self.hits = 0
        self.timer = 0
        self.longest_this_match = 0
        self.announced = 0

    def register_hit(self):
        self.hits += 1
        self.timer = self.WINDOW_FRAMES
        self.longest_this_match = max(self.longest_this_match, self.hits)

    def tick(self):
        if self.timer > 0:
            self.timer -= 1
            if self.timer <= 0:
                self.reset()

    def reset(self):
        self.hits = 0
        self.timer = 0
        self.announced = 0

    def damage_multiplier(self):
        if self.hits <= 1:
            return 1.0
        return max(0.4, 1.0 - 0.07 * (self.hits - 1))


# ----------------------------------------------------------------
# FIGHTER
# ----------------------------------------------------------------

class Fighter(GameObject):
    def __init__(self, name, x, y, character):
        super().__init__(x, y)

        self.name = name
        self.character = character

        self.width = 32
        self.height = 95

        self.max_health = character.max_health
        self.health = character.max_health

        self.max_energy = character.max_energy
        self.energy = character.max_energy

        self.max_stamina = character.max_stamina
        self.stamina = character.max_stamina

        self.speed = character.speed
        self.jump_power = character.jump_power
        self.gravity = -0.65

        self.direction = 1

        self.blocking = False
        self.parry_window = 0

        self.attacking = False
        self.current_move = None
        self.attack_timer = 0
        self.attack_active_frames = 0
        self.attack_cooldown = 0
        self.hit_registered = False

        self.dash_cooldown = 0
        self.special_cooldown = 0

        self.stun_timer = 0
        self.invulnerability = 0
        self.knocked_down_timer = 0
        self.wake_up_invuln = 0

        self.combo = ComboTracker()

        self.state = IdleState()
        self.graphics = GraphicsObject(character.color, 4)

    # ---------------- helpers ----------------

    def set_state(self, state):
        self.state = state

    def is_incapacitated(self):
        return (
            self.stun_timer > 0
            or self.knocked_down_timer > 0
        )

    def can_start_new_action(self):
        return (
            not self.is_incapacitated()
            and self.attack_cooldown <= 0
            and not self.attacking
        )

    def set_direction_to_target(self, target):
        self.direction = 1 if target.position.x > self.position.x else -1

    # ---------------- movement ----------------

    def move(self, amount):
        if self.is_incapacitated():
            return

        self.position.x += amount
        self.position.x = clamp(
            self.position.x,
            GameConfig.ARENA_LEFT + 40,
            GameConfig.ARENA_RIGHT - 40
        )

        if abs(amount) > 0 and not self.attacking:
            self.set_state(WalkingState())
        elif not self.attacking and not self.blocking:
            self.set_state(IdleState())

    def jump(self):
        if self.is_incapacitated():
            return False

        if self.position.y <= GameConfig.GROUND_Y:
            self.velocity.y = self.jump_power
            self.set_state(JumpingState())
            return True

        return False

    def dash(self):
        if self.is_incapacitated() or self.dash_cooldown > 0:
            return False

        cost = MOVE_ENERGY_COST[MoveType.DASH]

        if self.energy < cost:
            return False

        self.energy -= cost
        self.dash_cooldown = 34
        self.velocity.x = self.direction * self.speed * 3.2
        self.invulnerability = max(self.invulnerability, 7)
        self.set_state(DashingState())
        return True

    def block(self, value):
        if self.is_incapacitated():
            self.blocking = False
            return

        was_blocking = self.blocking
        self.blocking = bool(value) and self.stamina > 0

        if self.blocking and not was_blocking:
            self.parry_window = 8

        if self.blocking:
            self.set_state(BlockingState())
            self.stamina -= 0.9

            if self.stamina <= 0:
                self.stamina = 0
                self.blocking = False
                self.stun_timer = max(self.stun_timer, 14)

    # ---------------- melee attacks ----------------

    def _start_attack(self, move_type):
        if not self.can_start_new_action():
            return False

        cost = MOVE_ENERGY_COST[move_type]

        if self.energy < cost:
            return False

        self.energy -= cost
        self.attacking = True
        self.current_move = move_type

        startup = MOVE_STARTUP[move_type]
        active = MOVE_ACTIVE_WINDOW[move_type]

        self.attack_timer = startup + active
        self.attack_active_frames = active
        self.attack_cooldown = MOVE_COOLDOWN[move_type]
        self.hit_registered = False

        self.set_state(AttackingState())
        return True

    def light_punch(self):
        return self._start_attack(MoveType.LIGHT_PUNCH)

    def heavy_punch(self):
        return self._start_attack(MoveType.HEAVY_PUNCH)

    def light_kick(self):
        return self._start_attack(MoveType.LIGHT_KICK)

    def heavy_kick(self):
        return self._start_attack(MoveType.HEAVY_KICK)

    def uppercut(self):
        return self._start_attack(MoveType.UPPERCUT)

    def sweep(self):
        return self._start_attack(MoveType.SWEEP)

    # ---------------- ranged / special ----------------

    def projectile(self):
        cost = MOVE_ENERGY_COST[MoveType.PROJECTILE]

        if (
            self.is_incapacitated()
            or self.energy < cost
            or self.attack_cooldown > 0
        ):
            return None

        self.energy -= cost
        self.attack_cooldown = 22

        return Projectile(
            self,
            self.position.x + self.direction * 30,
            self.position.y + 45,
            self.direction,
            damage=9,
            speed=8
        )

    def special_move(self, opponent, game):
        cost = MOVE_ENERGY_COST[MoveType.SPECIAL]

        if (
            self.is_incapacitated()
            or self.energy < cost
            or self.special_cooldown > 0
        ):
            return False

        self.energy -= cost
        self.special_cooldown = 95
        self.set_state(AttackingState())

        damage = self.character.damage[MoveType.SPECIAL]
        special = self.character.special_type

        if special == SpecialType.ENERGY_WAVE:

            game.add_projectile(Projectile(
                self,
                self.position.x + self.direction * 32,
                self.position.y + 48,
                self.direction,
                damage=damage,
                speed=11,
                radius=13,
                life=100,
                color=self.character.projectile_color
            ))

        elif special == SpecialType.SHADOW_DASH:

            travel = 260 * self.direction
            self.position.x = clamp(
                self.position.x + travel,
                GameConfig.ARENA_LEFT + 40,
                GameConfig.ARENA_RIGHT - 40
            )
            self.invulnerability = max(self.invulnerability, 10)
            self.set_state(DashingState())

            if self.position.distance_to(opponent.position) < 75:
                opponent.take_damage(
                    damage, self, game,
                    source_move=MoveType.SPECIAL
                )
                game.create_hit_effect(
                    opponent.position.x,
                    opponent.position.y + 35,
                    "#ffffff",
                    big=True
                )
                game.create_particles(
                    opponent.position.x,
                    opponent.position.y + 35,
                    self.character.color
                )

            game.screen_shake.trigger(6, 10)

        elif special == SpecialType.GROUND_SLAM:

            game.screen_shake.trigger(11, 18)
            game.create_hit_effect(
                self.position.x, self.position.y + 10,
                "#ffaa00", big=True
            )

            if (
                abs(self.position.x - opponent.position.x) < 155
                and opponent.knocked_down_timer <= 0
            ):
                opponent.take_damage(
                    damage, self, game,
                    source_move=MoveType.SPECIAL,
                    force_knockdown=True
                )
                game.create_particles(
                    opponent.position.x,
                    opponent.position.y + 20,
                    self.character.color
                )

        elif special == SpecialType.TRIPLE_BURST:

            for speed, y_offset in ((9, 55), (10, 45), (11, 35)):
                game.add_projectile(Projectile(
                    self,
                    self.position.x + self.direction * 28,
                    self.position.y + y_offset,
                    self.direction,
                    damage=damage,
                    speed=speed,
                    radius=8,
                    life=80,
                    color=self.character.projectile_color
                ))

        return True

    # ---------------- damage / defense ----------------

    def take_damage(self, damage, attacker, game, source_move=None, force_knockdown=False):
        if self.invulnerability > 0:
            return

        attacker_x = attacker.position.x if attacker else self.position.x

        parried = bool(self.blocking and self.parry_window > 0 and attacker is not None)
        blocked = bool(self.blocking and not parried)

        final_damage = float(damage)
        label = None
        label_color = "#ffffff"

        if (
            attacker is getattr(game, "enemy", None)
            and not getattr(game, "two_player_mode", False)
        ):
            final_damage *= game.difficulty_manager.damage_multiplier()

        if parried:
            final_damage = 0
            self.energy = min(self.max_energy, self.energy + 12)
            label = "PARRY!"
            label_color = "#00ff88"
            self.invulnerability = max(self.invulnerability, 10)

            round_manager = getattr(game, "round_manager", None)
            if round_manager is not None:
                round_manager.register_parry(self is game.player)

            if attacker:
                attacker.stun_timer = max(attacker.stun_timer, 26)
                attacker.attacking = False
                attacker.current_move = None

        elif blocked:
            final_damage *= 0.2
            self.energy = min(self.max_energy, self.energy + 4)
            label = "BLOCKED"
            label_color = "#8fd3ff"

        else:
            combo_mult = attacker.combo.damage_multiplier() if attacker else 1.0
            final_damage *= combo_mult

        final_damage = int(max(0, round(final_damage)))
        self.health = max(0, self.health - final_damage)

        if not parried:
            if final_damage > 0:
                label = f"-{final_damage}"
                if not blocked:
                    label_color = "#ff5050"
            elif label is None:
                label = "0"

            self.stun_timer = 3 if blocked else 10
            self.invulnerability = max(self.invulnerability, 5)

            knock_dir = 1 if self.position.x < attacker_x else -1
            self.velocity.x = knock_dir * (3 if blocked else 5)
            self.velocity.y = 2 if blocked else 4

            should_knock_down = (
                force_knockdown
                or (source_move == MoveType.SWEEP and not blocked)
                or (not blocked and self.health <= 0)
            )

            if source_move == MoveType.UPPERCUT and not blocked and not should_knock_down:
                self.velocity.y = 11

            if should_knock_down:
                self.knocked_down_timer = 55
                self.velocity.y = max(self.velocity.y, 6)
                self.set_state(KnockedDownState())
            else:
                self.set_state(StunnedState())

        game.spawn_damage_number(
            self.position.x,
            self.position.y + 92,
            label,
            label_color
        )

        if attacker and final_damage > 0 and not blocked and not parried:
            game.register_combo_hit(attacker)
            game.stats.register_damage(final_damage)

        if self is game.player and final_damage > 0:
            game.stats.register_player_hit()

    def attack_hitbox(self):
        if not self.attacking or self.current_move not in MOVE_REACH:
            return None

        reach = MOVE_REACH[self.current_move]
        x = self.position.x + self.direction * reach
        y = self.position.y + (20 if self.current_move == MoveType.SWEEP else 35)
        radius = 22 if self.current_move in (
            MoveType.LIGHT_PUNCH, MoveType.LIGHT_KICK
        ) else 27

        return (x, y, radius)

    def update_attack(self, opponent, game):
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1

        if self.special_cooldown > 0:
            self.special_cooldown -= 1

        if not self.attacking:
            return

        self.attack_timer -= 1

        if not self.hit_registered and self.attack_timer <= self.attack_active_frames:
            hitbox = self.attack_hitbox()

            if hitbox:
                hx, hy, radius = hitbox
                distance = math.sqrt(
                    (hx - opponent.position.x) ** 2 +
                    (hy - (opponent.position.y + 35)) ** 2
                )

                if distance < radius + 25:
                    damage = self.character.damage[self.current_move]

                    opponent.take_damage(
                        damage, self, game,
                        source_move=self.current_move
                    )

                    big_hit = self.current_move in (
                        MoveType.HEAVY_PUNCH, MoveType.HEAVY_KICK,
                        MoveType.UPPERCUT, MoveType.SWEEP
                    )

                    game.create_hit_effect(
                        opponent.position.x,
                        opponent.position.y + 35,
                        "#ffff00",
                        big=big_hit
                    )

                    game.create_particles(
                        opponent.position.x,
                        opponent.position.y + 35,
                        self.character.color
                    )

                    if big_hit:
                        game.screen_shake.trigger(4, 6)

                    self.hit_registered = True

        if self.attack_timer <= 0:
            self.attacking = False
            self.current_move = None

    def apply_physics(self):
        self.position.y += self.velocity.y
        self.velocity.y += self.gravity
        self.velocity.x *= 0.82

        if self.position.y <= GameConfig.GROUND_Y:
            self.position.y = GameConfig.GROUND_Y
            self.velocity.y = 0

        self.position.x = clamp(
            self.position.x,
            GameConfig.ARENA_LEFT + 40,
            GameConfig.ARENA_RIGHT - 40
        )

    def regenerate(self):
        self.energy = min(self.max_energy, self.energy + 0.4)

        if not self.blocking:
            self.stamina = min(self.max_stamina, self.stamina + 0.6)

    def update(self, game):
        if self.stun_timer > 0:
            self.stun_timer -= 1

        if self.invulnerability > 0:
            self.invulnerability -= 1

        if self.knocked_down_timer > 0:
            self.knocked_down_timer -= 1

            if self.knocked_down_timer <= 0:
                self.wake_up_invuln = 20
                self.set_state(IdleState())

        if self.wake_up_invuln > 0:
            self.wake_up_invuln -= 1
            self.invulnerability = max(self.invulnerability, 1)

        if self.parry_window > 0:
            self.parry_window -= 1

        self.regenerate()

        self.state.update(self, game)
        self.apply_physics()

        self.update_attack(
            game.enemy if self is game.player else game.player,
            game
        )

        self.combo.tick()

    # ---------------- rendering ----------------

    def draw(self):
        self.graphics.clear()

        if self.knocked_down_timer > 0:
            self._draw_knocked_down()
            return

        x = self.position.x
        ground = self.position.y

        flicker_skip = self.invulnerability > 0 and self.invulnerability % 2 == 0

        if flicker_skip:
            return

        head_y = ground + 78
        neck_y = ground + 60
        waist_y = ground + 30
        shoulder_y = ground + 58

        direction = self.direction

        self.graphics.circle(x, head_y, 13)
        self.graphics.line(x, neck_y, x, waist_y)

        shoulder_x = x + direction * 3
        left_arm_x = x - 20
        right_arm_x = x + 20
        left_hand_x = x - 30
        right_hand_x = x + 30

        self.graphics.line(shoulder_x, shoulder_y, left_arm_x, shoulder_y - 20)
        self.graphics.line(left_arm_x, shoulder_y - 20, left_hand_x, shoulder_y - 42)
        self.graphics.line(shoulder_x, shoulder_y, right_arm_x, shoulder_y - 20)
        self.graphics.line(right_arm_x, shoulder_y - 20, right_hand_x, shoulder_y - 42)

        leg_spread = 14
        if self.state.label() == "Dashing":
            leg_spread = 22

        self.graphics.line(x, waist_y, x - leg_spread, ground)
        self.graphics.line(x, waist_y, x + leg_spread, ground)

        if self.attacking and self.current_move in MOVE_REACH:
            reach = MOVE_REACH[self.current_move]
            attack_y = ground + (23 if self.current_move == MoveType.SWEEP else 43)
            attack_x = x + direction * reach

            self.graphics.line(
                x + direction * 6, shoulder_y,
                attack_x, attack_y
            )
            self.graphics.circle(attack_x, attack_y, 5)

        if self.blocking:
            shield_x = x + direction * 38
            shield_y = ground + 45
            self.graphics.circle(shield_x, shield_y, 22)

        if self.dash_cooldown > 28:
            trail_x = x - direction * 18
            self.graphics.line(trail_x, ground + 10, trail_x, ground + 70)

    def _draw_knocked_down(self):
        x = self.position.x
        ground = self.position.y
        direction = self.direction

        self.graphics.circle(x - direction * 30, ground + 10, 11)
        self.graphics.line(x - direction * 18, ground + 8, x + direction * 25, ground + 6)
        self.graphics.line(x + direction * 5, ground + 7, x + direction * 20, ground - 2)
        self.graphics.line(x + direction * 5, ground + 9, x + direction * 20, ground + 16)


# ----------------------------------------------------------------
# CONTROLLERS
# ----------------------------------------------------------------

class HumanControlledMixin:
    """Shared input-handling logic for any fighter driven by a keyboard."""

    def default_controls(self):
        return {
            "left": False, "right": False, "up": False, "dash": False,
            "block": False, "light_punch": False, "heavy_punch": False,
            "light_kick": False, "heavy_kick": False, "uppercut": False,
            "sweep": False, "projectile": False, "special": False,
        }

    def get_opponent(self, game):
        raise NotImplementedError

    def handle_input(self, game):
        controls = self.controls

        if controls["left"]:
            self.move(-self.speed)
        if controls["right"]:
            self.move(self.speed)

        if controls["up"]:
            self.jump()
            controls["up"] = False

        if controls["dash"]:
            self.dash()
            controls["dash"] = False

        self.block(controls["block"])

        opponent = self.get_opponent(game)

        if controls["light_punch"]:
            self.light_punch()
            controls["light_punch"] = False

        if controls["heavy_punch"]:
            self.heavy_punch()
            controls["heavy_punch"] = False

        if controls["light_kick"]:
            self.light_kick()
            controls["light_kick"] = False

        if controls["heavy_kick"]:
            self.heavy_kick()
            controls["heavy_kick"] = False

        if controls["uppercut"]:
            self.uppercut()
            controls["uppercut"] = False

        if controls["sweep"]:
            self.sweep()
            controls["sweep"] = False

        if controls["projectile"]:
            projectile = self.projectile()
            if projectile:
                game.add_projectile(projectile)
            controls["projectile"] = False

        if controls["special"]:
            self.special_move(opponent, game)
            controls["special"] = False


class Player(Fighter, HumanControlledMixin):
    def __init__(self, character):
        super().__init__(
            "PLAYER",
            GameConfig.PLAYER_START_X,
            GameConfig.GROUND_Y,
            character
        )
        self.controls = self.default_controls()

    def get_opponent(self, game):
        return game.enemy

    def update(self, game):
        self.handle_input(game)
        super().update(game)


class AIController:
    def __init__(self, fighter):
        self.fighter = fighter
        self.target = None
        self.think_timer = 0

    def _incoming_projectile(self, game):
        for projectile in game.projectiles:
            if not projectile.active or projectile.owner is not self.target:
                continue

            dx = self.fighter.position.x - projectile.position.x

            if (dx * projectile.direction) > 0 and abs(dx) < 220:
                return projectile

        return None

    def _advance(self, distance, game, diff_mult, ranged_chance=0.05):
        step = self.fighter.speed * (0.85 if abs(distance) > 200 else 1.0)

        if distance > 0:
            self.fighter.move(step)
        else:
            self.fighter.move(-step)

        if (
            random.random() < ranged_chance * diff_mult["aggression"]
            and self.fighter.energy > 35
        ):
            projectile = self.fighter.projectile()
            if projectile:
                game.add_projectile(projectile)

    def decide(self, game):
        if not self.fighter.active:
            return

        target = self.target

        if target is None:
            return

        self.fighter.set_direction_to_target(target)

        if self.fighter.is_incapacitated():
            return

        diff_mult = game.difficulty_manager.multipliers()

        incoming = self._incoming_projectile(game)

        if incoming and random.random() < 0.5 * diff_mult["aggression"]:
            if random.random() < 0.5:
                self.fighter.jump()
            else:
                self.fighter.block(True)
            return

        if self.think_timer > 0:
            self.think_timer -= 1
            return

        base_think = random.randint(4, 10)
        self.think_timer = max(1, int(base_think * diff_mult["reaction"]))

        distance = target.position.x - self.fighter.position.x
        abs_distance = abs(distance)

        if target.attacking and abs_distance < 110:
            if random.random() < 0.35 * diff_mult["aggression"]:
                self.fighter.block(True)
                return

        self.fighter.block(False)

        if (
            self.fighter.energy >= MOVE_ENERGY_COST[MoveType.SPECIAL]
            and self.fighter.special_cooldown <= 0
            and abs_distance < 260
            and random.random() < 0.18 * diff_mult["aggression"]
        ):
            self.fighter.special_move(target, game)
            return

        if abs_distance > 200:
            self._advance(distance, game, diff_mult, ranged_chance=0.04)
            return

        if abs_distance > 100:
            self._advance(distance, game, diff_mult, ranged_chance=0.14)
            return

        choice = random.random()

        if choice < 0.15:
            self.fighter.light_punch()
        elif choice < 0.28:
            self.fighter.heavy_punch()
        elif choice < 0.42:
            self.fighter.light_kick()
        elif choice < 0.53:
            self.fighter.heavy_kick()
        elif choice < 0.61 and target.knocked_down_timer <= 0:
            self.fighter.uppercut()
        elif choice < 0.70:
            self.fighter.sweep()
        elif choice < 0.78:
            self.fighter.jump()
        elif choice < 0.88:
            projectile = self.fighter.projectile()
            if projectile:
                game.add_projectile(projectile)
        elif choice < 0.95:
            self.fighter.dash()
        else:
            self._advance(distance, game, diff_mult)


class Enemy(Fighter, HumanControlledMixin):
    def __init__(self, character):
        super().__init__(
            "ENEMY",
            GameConfig.ENEMY_START_X,
            GameConfig.GROUND_Y,
            character
        )
        self.ai = AIController(self)
        self.human_controlled = False
        self.controls = self.default_controls()

    def get_opponent(self, game):
        return game.player

    def update(self, game):
        if self.human_controlled:
            self.handle_input(game)
        else:
            self.ai.target = game.player
            self.ai.decide(game)

        super().update(game)


# ----------------------------------------------------------------
# ARENA & HUD
# ----------------------------------------------------------------

class Arena:
    def __init__(self, width=1000, height=650):
        self.width = width
        self.height = height
        self.graphics = GraphicsObject("#6c6c6c", 2)
        self.deco = GraphicsObject("#242938", 1)
        self.deco_offset = 0.0

    def draw(self, shake=None):
        ox = shake.offset_x if shake else 0
        oy = shake.offset_y if shake else 0

        self.graphics.clear()
        self.graphics.pen.color("#6c6c6c")
        self.graphics.pen.pensize(2)

        self.graphics.line(-500 + ox, -180 + oy, 500 + ox, -180 + oy)

        for x in range(-500, 501, 50):
            self.graphics.line(x + ox, -180 + oy, x + ox, -210 + oy)

        self.graphics.line(-490 + ox, -180 + oy, -490 + ox, 230 + oy)
        self.graphics.line(490 + ox, -180 + oy, 490 + ox, 230 + oy)

        for y in range(-130, 231, 60):
            self.graphics.line(-490 + ox, y + oy, 490 + ox, y + oy)

        self.graphics.circle(0 + ox, -170 + oy, 100)

        self.deco_offset += 0.15
        self.deco.clear()
        for i in range(6):
            cx = -400 + i * 160 + math.sin(self.deco_offset + i) * 8
            cy = 250 + (i % 2) * 10
            self.deco.circle(cx + ox, cy + oy, 14)


class HUD:
    def __init__(self):
        self.writer = turtle.Turtle()
        self.writer.hideturtle()
        self.writer.penup()
        self.writer.speed(0)

        self.player_health = Bar(-460, 230, 350, 22, "#00eaff")
        self.enemy_health = Bar(110, 230, 350, 22, "#ff304f")

        self.player_energy = Bar(-460, 205, 240, 9, "#00aaff")
        self.enemy_energy = Bar(220, 205, 240, 9, "#ff8800")

        self.player_stamina = Bar(-460, 192, 240, 7, "#66ffaa")
        self.enemy_stamina = Bar(220, 192, 240, 7, "#ffee66")

    def clear(self):
        self.writer.clear()
        for bar in (
            self.player_health, self.enemy_health,
            self.player_energy, self.enemy_energy,
            self.player_stamina, self.enemy_stamina
        ):
            bar.background.clear()
            bar.foreground.clear()

    def text(self, x, y, text, size=18, color="white", align="center", font="Arial", bold=True):
        self.writer.goto(x, y)
        self.writer.color(color)
        self.writer.write(
            text, align=align,
            font=(font, size, "bold" if bold else "normal")
        )

    def draw(self, player, enemy, round_number, round_time, message, difficulty_label, two_player):
        self.clear()

        self.player_health.draw(player.health, player.max_health)
        self.enemy_health.draw(enemy.health, enemy.max_health)

        self.player_energy.draw(player.energy, player.max_energy)
        self.enemy_energy.draw(enemy.energy, enemy.max_energy)

        self.player_stamina.draw(player.stamina, player.max_stamina)
        self.enemy_stamina.draw(enemy.stamina, enemy.max_stamina)

        self.text(-460, 260, f"{player.name} ({player.character.name})", 14, "#00eaff", "left")
        self.text(460, 260, f"{enemy.name} ({enemy.character.name})", 14, "#ff304f", "right")

        self.text(0, 245, f"ROUND {round_number}", 18, "white")
        self.text(0, 215, f"{max(0, int(round_time)):02d}", 24, "#ffff00")

        mode_label = "2P LOCAL" if two_player else f"AI: {difficulty_label}"
        self.text(0, -175 + 452, mode_label, 12, "#888888")

        if player.combo.hits > 1:
            self.text(-460, 175, f"COMBO x{player.combo.hits}", 13, "#ffcc00", "left")

        if enemy.combo.hits > 1:
            self.text(460, 175, f"COMBO x{enemy.combo.hits}", 13, "#ffcc00", "right")

        if message:
            self.text(0, 130, message, 30, "#ffffff")

        self.text(-470, -295, "A/D Move   W Jump   S Dash", 11, "#cccccc", "left")
        self.text(-470, -315, "J/K Punch (lt/hv)   N/M Kick (lt/hv)", 11, "#cccccc", "left")
        self.text(150, -295, "U Uppercut  H Sweep  L Blast", 11, "#cccccc", "left")
        self.text(150, -315, "SPACE Block/Parry   F Special", 11, "#cccccc", "left")
        self.text(470, -295, "P Pause", 11, "#cccccc", "right")
        self.text(470, -315, "R Restart", 11, "#cccccc", "right")


class SoundManager:
    """Placeholder hooks -- kept silent by default but centralizes event
    points so real audio can be wired in later without touching game logic."""

    def __init__(self):
        self.enabled = False

    def hit(self):
        pass

    def punch(self):
        pass

    def kick(self):
        pass

    def projectile(self):
        pass

    def special(self):
        pass

    def win(self):
        pass

    def menu_select(self):
        pass


# ----------------------------------------------------------------
# DIFFICULTY
# ----------------------------------------------------------------

class DifficultyManager:
    def __init__(self):
        self.index = DIFFICULTY_ORDER.index(Difficulty.NORMAL)

    @property
    def current(self):
        return DIFFICULTY_ORDER[self.index]

    def cycle(self):
        self.index = (self.index + 1) % len(DIFFICULTY_ORDER)
        return self.current

    def multipliers(self):
        return DIFFICULTY_MULTIPLIERS[self.current]

    def damage_multiplier(self):
        return self.multipliers()["damage"]

    def label(self):
        return self.current.value


# ----------------------------------------------------------------
# STATS / ACHIEVEMENTS / PERSISTENCE
# ----------------------------------------------------------------

class GameStatistics:
    def __init__(self):
        self.reset()

    def reset(self):
        self.total_damage_dealt = 0
        self.total_hits = 0
        self.times_player_hit = 0
        self.longest_combo = 0

    def register_damage(self, amount):
        self.total_damage_dealt += amount
        self.total_hits += 1

    def register_player_hit(self):
        self.times_player_hit += 1

    def update_combo(self, hits):
        self.longest_combo = max(self.longest_combo, hits)


ACHIEVEMENTS = [
    {"id": "first_win", "name": "First Blood", "desc": "Win your first match."},
    {"id": "flawless", "name": "Flawless Victory", "desc": "Win a round without taking any damage."},
    {"id": "combo_master", "name": "Combo Master", "desc": "Land an 8+ hit combo."},
    {"id": "comeback", "name": "Comeback Kid", "desc": "Win a round after dropping below 20% health."},
    {"id": "five_wins", "name": "Seasoned Fighter", "desc": "Win 5 matches total."},
    {"id": "parry_king", "name": "Perfect Timing", "desc": "Win a round after landing a parry."},
]


class StatsManager:
    """Loads and saves a small JSON profile to disk between sessions."""

    def __init__(self):
        self.data = {
            "matches_played": 0,
            "matches_won": 0,
            "matches_lost": 0,
            "best_combo": 0,
            "achievements": [],
            "favorite_character": {},
        }
        self.load()

    def load(self):
        if not os.path.exists(GameConfig.SAVE_FILE):
            return

        try:
            with open(GameConfig.SAVE_FILE, "r", encoding="utf-8") as handle:
                loaded = json.load(handle)
                self.data.update(loaded)
        except (OSError, ValueError):
            pass

    def save(self):
        try:
            with open(GameConfig.SAVE_FILE, "w", encoding="utf-8") as handle:
                json.dump(self.data, handle, indent=2)
        except OSError:
            pass

    def record_match(self, won, character_key):
        self.data["matches_played"] += 1

        if won:
            self.data["matches_won"] += 1
        else:
            self.data["matches_lost"] += 1

        favorites = self.data.setdefault("favorite_character", {})
        favorites[character_key] = favorites.get(character_key, 0) + 1

        self.save()

    def unlock(self, achievement_id):
        if achievement_id not in self.data["achievements"]:
            self.data["achievements"].append(achievement_id)
            self.save()
            return True
        return False

    def has(self, achievement_id):
        return achievement_id in self.data["achievements"]


class AchievementManager:
    def __init__(self, stats_manager):
        self.stats_manager = stats_manager
        self.pending_toasts = []

    def check_match_win(self, character_key):
        newly = []

        if self.stats_manager.unlock("first_win"):
            newly.append("first_win")

        if self.stats_manager.data["matches_won"] >= 5:
            if self.stats_manager.unlock("five_wins"):
                newly.append("five_wins")

        for achievement_id in newly:
            self._queue_toast(achievement_id)

        return newly

    def check_round_win(self, winner_took_no_damage, combo_hits, had_comeback, had_parry_win):
        newly = []

        if winner_took_no_damage and self.stats_manager.unlock("flawless"):
            newly.append("flawless")

        if combo_hits >= 8 and self.stats_manager.unlock("combo_master"):
            newly.append("combo_master")

        if had_comeback and self.stats_manager.unlock("comeback"):
            newly.append("comeback")

        if had_parry_win and self.stats_manager.unlock("parry_king"):
            newly.append("parry_king")

        for achievement_id in newly:
            self._queue_toast(achievement_id)

        return newly

    def _queue_toast(self, achievement_id):
        info = next((a for a in ACHIEVEMENTS if a["id"] == achievement_id), None)
        if info:
            self.pending_toasts.append(info["name"])


# ----------------------------------------------------------------
# ROUND / MATCH FLOW
# ----------------------------------------------------------------

class RoundManager:
    def __init__(self):
        self.round_number = 1
        self.player_rounds = 0
        self.enemy_rounds = 0
        self.round_length = GameConfig.ROUND_TIME
        self.time_left = self.round_length
        self.active = True
        self.message = ""

        self.player_min_health_ratio = 1.0
        self.enemy_min_health_ratio = 1.0
        self.parry_landed_by_player = False
        self.parry_landed_by_enemy = False

    def reset_round(self):
        self.time_left = self.round_length
        self.active = True
        self.message = ""
        self.player_min_health_ratio = 1.0
        self.enemy_min_health_ratio = 1.0
        self.parry_landed_by_player = False
        self.parry_landed_by_enemy = False

    def register_parry(self, by_player):
        if by_player:
            self.parry_landed_by_player = True
        else:
            self.parry_landed_by_enemy = True

    def track_health(self, player, enemy):
        self.player_min_health_ratio = min(
            self.player_min_health_ratio,
            player.health / player.max_health
        )
        self.enemy_min_health_ratio = min(
            self.enemy_min_health_ratio,
            enemy.health / enemy.max_health
        )

    def match_winner(self):
        if self.player_rounds >= GameConfig.ROUNDS_TO_WIN:
            return "PLAYER"
        if self.enemy_rounds >= GameConfig.ROUNDS_TO_WIN:
            return "ENEMY"
        return None

    def end_round(self, player, enemy, achievement_manager):
        if not self.active:
            return

        self.active = False
        winner_is_player = None

        if player.health > enemy.health:
            self.player_rounds += 1
            self.message = f"{player.character.name} WINS THE ROUND!"
            winner_is_player = True
        elif enemy.health > player.health:
            self.enemy_rounds += 1
            self.message = f"{enemy.character.name} WINS THE ROUND!"
            winner_is_player = False
        else:
            self.message = "DRAW!"

        if winner_is_player is True and achievement_manager is not None:
            no_damage = self.player_min_health_ratio >= 0.999
            comeback = self.player_min_health_ratio < 0.2
            parry_win = self.parry_landed_by_player
            combo_hits = player.combo.longest_this_match

            achievement_manager.check_round_win(
                no_damage, combo_hits, comeback, parry_win
            )


class MatchManager:
    def __init__(self, player_character, enemy_character, two_player_mode):
        self.player = Player(player_character)
        self.enemy = Enemy(enemy_character)

        if two_player_mode:
            self.enemy.human_controlled = True

        self.two_player_mode = two_player_mode
        self.round_manager = RoundManager()
        self.game_over = False
        self.final_message = ""

    def start_next_round(self):
        round_manager = self.round_manager
        round_manager.round_number += 1

        for fighter, start_x in (
            (self.player, GameConfig.PLAYER_START_X),
            (self.enemy, GameConfig.ENEMY_START_X)
        ):
            fighter.health = fighter.max_health
            fighter.energy = fighter.max_energy
            fighter.stamina = fighter.max_stamina
            fighter.position = Vector2(start_x, GameConfig.GROUND_Y)
            fighter.velocity = Vector2()
            fighter.attacking = False
            fighter.current_move = None
            fighter.blocking = False
            fighter.stun_timer = 0
            fighter.knocked_down_timer = 0
            fighter.invulnerability = 0
            fighter.combo.reset()
            fighter.set_state(IdleState())

        round_manager.reset_round()


# ----------------------------------------------------------------
# INPUT
# ----------------------------------------------------------------

class InputManager:
    """Binds keyboard events for up to two local fighters. Each handler
    checks game state so keys are harmless outside active gameplay."""

    def __init__(self, screen, game):
        self.screen = screen
        self.game = game

        screen.listen()
        self._bind_player_one()
        self._bind_player_two()

        screen.onkeypress(self.game.toggle_pause, "p")
        screen.onkeypress(self.game.restart_to_menu, "r")

    def _in_fight(self):
        return (
            self.game.state == GameState.FIGHTING
            and not self.game.paused
        )

    def _bind_player_one(self):
        screen = self.screen
        controls = lambda: self.game.player.controls

        def set_flag(key, value):
            if self._in_fight():
                controls()[key] = value

        screen.onkeypress(lambda: set_flag("left", True), "a")
        screen.onkeyrelease(lambda: set_flag("left", False), "a")
        screen.onkeypress(lambda: set_flag("right", True), "d")
        screen.onkeyrelease(lambda: set_flag("right", False), "d")

        screen.onkeypress(lambda: set_flag("up", True), "w")
        screen.onkeypress(lambda: set_flag("dash", True), "s")

        screen.onkeypress(lambda: set_flag("block", True), "space")
        screen.onkeyrelease(lambda: set_flag("block", False), "space")

        screen.onkeypress(lambda: set_flag("light_punch", True), "j")
        screen.onkeypress(lambda: set_flag("heavy_punch", True), "k")
        screen.onkeypress(lambda: set_flag("light_kick", True), "n")
        screen.onkeypress(lambda: set_flag("heavy_kick", True), "m")
        screen.onkeypress(lambda: set_flag("uppercut", True), "u")
        screen.onkeypress(lambda: set_flag("sweep", True), "h")
        screen.onkeypress(lambda: set_flag("projectile", True), "l")
        screen.onkeypress(lambda: set_flag("special", True), "f")

    def _bind_player_two(self):
        screen = self.screen

        def set_flag(key, value):
            if self._in_fight() and self.game.enemy.human_controlled:
                self.game.enemy.controls[key] = value

        screen.onkeypress(lambda: set_flag("left", True), "Left")
        screen.onkeyrelease(lambda: set_flag("left", False), "Left")
        screen.onkeypress(lambda: set_flag("right", True), "Right")
        screen.onkeyrelease(lambda: set_flag("right", False), "Right")

        screen.onkeypress(lambda: set_flag("up", True), "Up")
        screen.onkeypress(lambda: set_flag("dash", True), "Down")

        screen.onkeypress(lambda: set_flag("block", True), "0")
        screen.onkeyrelease(lambda: set_flag("block", False), "0")

        screen.onkeypress(lambda: set_flag("light_punch", True), "1")
        screen.onkeypress(lambda: set_flag("heavy_punch", True), "2")
        screen.onkeypress(lambda: set_flag("light_kick", True), "3")
        screen.onkeypress(lambda: set_flag("heavy_kick", True), "4")
        screen.onkeypress(lambda: set_flag("uppercut", True), "5")
        screen.onkeypress(lambda: set_flag("sweep", True), "6")
        screen.onkeypress(lambda: set_flag("projectile", True), "7")
        screen.onkeypress(lambda: set_flag("special", True), "9")


# ----------------------------------------------------------------
# MENUS
# ----------------------------------------------------------------

class Button:
    def __init__(self, x, y, width, height, label, action, sublabel=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.label = label
        self.action = action
        self.sublabel = sublabel

    def contains(self, x, y):
        return (
            self.x - self.width / 2 <= x <= self.x + self.width / 2
            and self.y - self.height / 2 <= y <= self.y + self.height / 2
        )


class MenuBase:
    def __init__(self):
        self.panel = turtle.Turtle()
        self.panel.hideturtle()
        self.panel.penup()
        self.panel.speed(0)

        self.writer = turtle.Turtle()
        self.writer.hideturtle()
        self.writer.penup()
        self.writer.speed(0)

        self.buttons = []

    def clear(self):
        self.panel.clear()
        self.writer.clear()

    def text(self, x, y, msg, size=16, color="white", align="center", bold=True):
        self.writer.goto(x, y)
        self.writer.color(color)
        self.writer.write(
            msg, align=align,
            font=("Arial", size, "bold" if bold else "normal")
        )

    def draw_button(self, button, accent="#2c3446", border="#5a6b8c"):
        x, y, w, h = button.x, button.y, button.width, button.height

        self.panel.penup()
        self.panel.goto(x - w / 2, y - h / 2)
        self.panel.fillcolor(accent)
        self.panel.pencolor(border)
        self.panel.pensize(2)
        self.panel.begin_fill()
        self.panel.pendown()

        for px, py in [
            (x + w / 2, y - h / 2),
            (x + w / 2, y + h / 2),
            (x - w / 2, y + h / 2),
            (x - w / 2, y - h / 2)
        ]:
            self.panel.goto(px, py)

        self.panel.end_fill()
        self.panel.penup()

        self.text(x, y + (4 if button.sublabel else -6), button.label, 15, "#ffffff")

        if button.sublabel:
            self.text(x, y - 14, button.sublabel, 10, "#aab4c8")

    def handle_click(self, x, y):
        for button in self.buttons:
            if button.contains(x, y):
                button.action()
                return True
        return False


class MainMenu(MenuBase):
    def draw(self, game):
        self.clear()

        self.text(0, 220, "STICKMAN ARENA", 42, "#00eaff")
        self.text(0, 175, "ADVANCED EDITION", 16, "#888888")

        self.buttons = [
            Button(0, 90, 360, 55, "1 PLAYER (VS AI)", lambda: game.begin_character_select(False)),
            Button(0, 15, 360, 55, "2 PLAYER (LOCAL)", lambda: game.begin_character_select(True)),
            Button(0, -60, 360, 50, f"DIFFICULTY: {game.difficulty_manager.label()}", game.cycle_difficulty),
            Button(0, -130, 360, 50, "QUIT", game.quit_game),
        ]

        for button in self.buttons:
            self.draw_button(button)

        stats = game.stats_manager.data
        self.text(
            0, -200,
            f"Record: {stats['matches_won']}W - {stats['matches_lost']}L    "
            f"Achievements: {len(stats['achievements'])}/{len(ACHIEVEMENTS)}",
            12, "#666666"
        )

        self.text(0, -260, "Click a button to begin", 11, "#444444")


class CharacterSelectMenu(MenuBase):
    def draw(self, game):
        self.clear()

        picking_slot = 1 if game.p1_character is None else 2
        slot_label = "PLAYER 1" if picking_slot == 1 else "PLAYER 2"

        self.text(0, 260, f"{slot_label}: CHOOSE YOUR FIGHTER", 24, "#ffffff")

        self.buttons = []
        roster = game.character_roster
        spacing = 235
        start_x = -(len(roster) - 1) * spacing / 2

        for i, character in enumerate(roster):
            x = start_x + i * spacing
            self._draw_character_card(character, x, 30)

            self.buttons.append(Button(
                x, 30, 205, 300,
                "",
                (lambda c=character: game.on_character_picked(c))
            ))

        self.text(0, -240, "Click a fighter to select", 12, "#666666")

    def _draw_character_card(self, character, x, y):
        w, h = 205, 300

        self.panel.penup()
        self.panel.goto(x - w / 2, y - h / 2)
        self.panel.fillcolor("#20263a")
        self.panel.pencolor(character.color)
        self.panel.pensize(3)
        self.panel.begin_fill()
        self.panel.pendown()

        for px, py in [
            (x + w / 2, y - h / 2),
            (x + w / 2, y + h / 2),
            (x - w / 2, y + h / 2),
            (x - w / 2, y - h / 2)
        ]:
            self.panel.goto(px, py)

        self.panel.end_fill()
        self.panel.penup()

        self._stick_icon(x, y + 95, character.color)

        self.text(x, y + 15, character.name, 16, character.color)
        self.text(x, y - 8, character.description, 9, "#cccccc")
        self.text(x, y - 45, f"HP {character.max_health}", 10, "#ff8080")
        self.text(x, y - 63, f"SPD {character.speed:.1f}", 10, "#80ff80")
        self.text(x, y - 81, character.special_name, 9, "#ffe080")

    def _stick_icon(self, x, y, color):
        self.panel.pencolor(color)
        self.panel.pensize(3)

        self.panel.penup()
        self.panel.goto(x, y - 12)
        self.panel.setheading(0)
        self.panel.pendown()
        self.panel.circle(12)
        self.panel.penup()

        self.panel.goto(x, y - 12)
        self.panel.pendown()
        self.panel.goto(x, y - 55)
        self.panel.penup()

        self.panel.goto(x - 18, y - 30)
        self.panel.pendown()
        self.panel.goto(x + 18, y - 30)
        self.panel.penup()

        self.panel.goto(x, y - 55)
        self.panel.pendown()
        self.panel.goto(x - 14, y - 85)
        self.panel.penup()

        self.panel.goto(x, y - 55)
        self.panel.pendown()
        self.panel.goto(x + 14, y - 85)
        self.panel.penup()


class PauseMenu(MenuBase):
    def draw(self, game):
        self.clear()

        self.text(0, 100, "PAUSED", 34, "#ffffff")

        self.buttons = [
            Button(0, 30, 300, 50, "RESUME", game.toggle_pause),
            Button(0, -35, 300, 50, "RESTART MATCH", game.restart_match),
            Button(0, -100, 300, 50, "MAIN MENU", game.return_to_main_menu),
            Button(0, -165, 300, 50, "QUIT", game.quit_game),
        ]

        for button in self.buttons:
            self.draw_button(button)


class GameOverMenu(MenuBase):
    def draw(self, game):
        self.clear()

        self.text(0, 210, game.match.final_message, 26, "#ffffff")

        self.text(
            0, 160,
            f"Damage dealt: {int(game.stats.total_damage_dealt)}   "
            f"Longest combo: {game.stats.longest_combo}",
            13, "#aaaaaa"
        )

        toast_y = 120
        for name in game.achievement_manager.pending_toasts:
            self.text(0, toast_y, f"ACHIEVEMENT UNLOCKED: {name}", 14, "#ffd24d")
            toast_y -= 24

        self.buttons = [
            Button(0, 0, 320, 50, "REMATCH", game.rematch),
            Button(0, -65, 320, 50, "CHARACTER SELECT", game.replay_character_select),
            Button(0, -130, 320, 50, "MAIN MENU", game.return_to_main_menu),
            Button(0, -195, 320, 50, "QUIT", game.quit_game),
        ]

        for button in self.buttons:
            self.draw_button(button)


# ----------------------------------------------------------------
# GAME
# ----------------------------------------------------------------

class Game:
    def __init__(self):
        self.screen = turtle.Screen()
        self.screen.setup(width=GameConfig.WIDTH, height=GameConfig.HEIGHT)
        self.screen.title("Stickman Arena - Advanced Edition")
        self.screen.bgcolor("#10131c")
        self.screen.tracer(0, 0)

        self.arena = Arena()
        self.hud = HUD()
        self.sound = SoundManager()
        self.screen_shake = ScreenShake()

        self.difficulty_manager = DifficultyManager()
        self.stats_manager = StatsManager()
        self.achievement_manager = AchievementManager(self.stats_manager)
        self.stats = GameStatistics()

        self.character_roster = build_character_roster()

        self.main_menu = MainMenu()
        self.character_select_menu = CharacterSelectMenu()
        self.pause_menu = PauseMenu()
        self.game_over_menu = GameOverMenu()

        self.state = GameState.MAIN_MENU
        self.paused = False
        self.running = True
        self._fight_visuals_dirty = False

        self.two_player_pending = False
        self.two_player_mode = False
        self.p1_character = None
        self.p2_character = None

        self.match = None
        self.player = None
        self.enemy = None
        self.round_manager = None

        self.projectiles = []
        self.particles = []
        self.effects = []
        self.damage_numbers = []
        self.combo_popups = []

        self.message_timer = 0
        self.last_time = time.time()

        self.input = InputManager(self.screen, self)
        self.screen.onclick(self.handle_click)

    # ---------------- state transitions ----------------

    def begin_character_select(self, two_player):
        self.pause_menu.clear()
        self.game_over_menu.clear()

        self.two_player_pending = two_player
        self.p1_character = None
        self.p2_character = None
        self.state = GameState.CHARACTER_SELECT

    def on_character_picked(self, character):
        if self.p1_character is None:
            self.p1_character = character

            if not self.two_player_pending:
                self.p2_character = random.choice(self.character_roster)
                self.start_match()

        elif self.p2_character is None:
            self.p2_character = character
            self.start_match()

    def start_match(self):
        self.pause_menu.clear()
        self.game_over_menu.clear()

        self.match = MatchManager(self.p1_character, self.p2_character, self.two_player_pending)
        self.player = self.match.player
        self.enemy = self.match.enemy
        self.round_manager = self.match.round_manager
        self.two_player_mode = self.two_player_pending

        self.projectiles = []
        self.particles = []
        self.effects = []
        self.damage_numbers = []
        self.combo_popups = []

        self.stats.reset()
        self.achievement_manager.pending_toasts = []

        self.message_timer = 0
        self.last_time = time.time()
        self.paused = False
        self._fight_visuals_dirty = True
        self.state = GameState.FIGHTING

    def rematch(self):
        self.start_match()

    def replay_character_select(self):
        self.begin_character_select(self.two_player_mode)

    def return_to_main_menu(self):
        self.pause_menu.clear()
        self.game_over_menu.clear()
        self.paused = False
        self.state = GameState.MAIN_MENU

    def cycle_difficulty(self):
        self.difficulty_manager.cycle()

    def quit_game(self):
        self.running = False
        self.stats_manager.save()
        try:
            self.screen.bye()
        except turtle.Terminator:
            pass

    def toggle_pause(self):
        if self.state not in (GameState.FIGHTING, GameState.PAUSED):
            return

        if self.match and self.match.game_over:
            return

        self.paused = not self.paused

        if self.paused:
            self.state = GameState.PAUSED
        else:
            self.pause_menu.clear()
            self.state = GameState.FIGHTING
            self.last_time = time.time()

    def restart_match(self):
        self.start_match()

    def restart_to_menu(self):
        # Bound to the "r" key -- a quick full restart of the current match.
        if self.state in (GameState.FIGHTING, GameState.PAUSED, GameState.GAME_OVER):
            if self.p1_character and self.p2_character:
                self.start_match()

    def handle_click(self, x, y):
        if self.state == GameState.MAIN_MENU:
            self.main_menu.handle_click(x, y)
        elif self.state == GameState.CHARACTER_SELECT:
            self.character_select_menu.handle_click(x, y)
        elif self.state == GameState.PAUSED:
            self.pause_menu.handle_click(x, y)
        elif self.state == GameState.GAME_OVER:
            self.game_over_menu.handle_click(x, y)

    # ---------------- visual effect helpers ----------------

    def add_projectile(self, projectile):
        self.projectiles.append(projectile)

    def create_particles(self, x, y, color):
        for _ in range(8):
            velocity = Vector2(random.uniform(-4, 4), random.uniform(1, 6))
            self.particles.append(Particle(
                x, y, color, velocity,
                random.randint(10, 24),
                random.randint(5, 10)
            ))

    def create_hit_effect(self, x, y, color, big=False):
        self.effects.append(HitEffect(x, y, color, big=big))

    def spawn_damage_number(self, x, y, text, color):
        if text is None:
            return
        self.damage_numbers.append(DamageNumber(x, y, text, color))

    def register_combo_hit(self, fighter):
        fighter.combo.register_hit()
        self.stats.update_combo(fighter.combo.hits)

        if fighter.combo.hits >= 3 and fighter.combo.hits != fighter.combo.announced:
            fighter.combo.announced = fighter.combo.hits
            self.combo_popups.append(ComboPopup(
                fighter.position.x,
                fighter.position.y + 140,
                fighter.combo.hits
            ))

    # ---------------- per-frame logic ----------------

    def cleanup(self):
        def sweep(items):
            keep = []
            for item in items:
                if item.active:
                    keep.append(item)
                else:
                    if hasattr(item, "graphics"):
                        item.graphics.clear()
                    elif hasattr(item, "writer"):
                        item.writer.clear()
            return keep

        self.projectiles = sweep(self.projectiles)
        self.particles = sweep(self.particles)
        self.effects = sweep(self.effects)
        self.damage_numbers = sweep(self.damage_numbers)
        self.combo_popups = sweep(self.combo_popups)

    def update_round_timer(self):
        if not self.round_manager.active:
            return

        now = time.time()
        delta = now - self.last_time
        self.last_time = now

        self.round_manager.time_left -= delta

        if self.round_manager.time_left <= 0:
            self.round_manager.time_left = 0
            self.round_manager.end_round(self.player, self.enemy, self.achievement_manager)
            self.message_timer = 90

    def check_round_end(self):
        if not self.round_manager.active:
            return

        if self.player.health <= 0 or self.enemy.health <= 0:
            self.round_manager.end_round(self.player, self.enemy, self.achievement_manager)
            self.message_timer = 90

    def process_round_transition(self):
        if self.round_manager.active:
            return

        winner = self.round_manager.match_winner()

        if winner:
            self.match.game_over = True
            self.match.final_message = (
                f"{self.player.character.name} WINS THE MATCH!"
                if winner == "PLAYER"
                else f"{self.enemy.character.name} WINS THE MATCH!"
            )

            self.stats.longest_combo = max(
                self.player.combo.longest_this_match,
                self.enemy.combo.longest_this_match
            )

            if winner == "PLAYER":
                self.achievement_manager.check_match_win(self.p1_character.key)

            self.stats_manager.record_match(winner == "PLAYER", self.p1_character.key)

            self.state = GameState.GAME_OVER
            return

        if self.message_timer > 0:
            self.message_timer -= 1
            return

        self.match.start_next_round()
        self.last_time = time.time()

    def update_objects(self):
        if not self.round_manager.active:
            return

        self.player.update(self)
        self.enemy.update(self)

        for projectile in self.projectiles:
            projectile.update(self)

        for particle in self.particles:
            particle.update(self)

        for effect in self.effects:
            effect.update(self)

        for number in self.damage_numbers:
            number.update(self)

        for popup in self.combo_popups:
            popup.update(self)

        self.round_manager.track_health(self.player, self.enemy)
        self.screen_shake.update()

    def draw_objects(self):
        self.player.draw()
        self.enemy.draw()

        for projectile in self.projectiles:
            projectile.draw()

        for particle in self.particles:
            particle.draw()

        for effect in self.effects:
            effect.draw()

        for number in self.damage_numbers:
            number.draw()

        for popup in self.combo_popups:
            popup.draw()

    def draw_hud(self):
        message = self.round_manager.message if not self.round_manager.active else ""

        self.hud.draw(
            self.player, self.enemy,
            self.round_manager.round_number,
            self.round_manager.time_left,
            message,
            self.difficulty_manager.label(),
            self.two_player_mode
        )

    def _clear_fight_visuals(self):
        if not self._fight_visuals_dirty:
            return

        self.arena.graphics.clear()
        self.arena.deco.clear()
        self.hud.clear()

        for group in (
            self.projectiles, self.particles, self.effects,
            self.damage_numbers, self.combo_popups
        ):
            for item in group:
                if hasattr(item, "graphics"):
                    item.graphics.clear()
                elif hasattr(item, "writer"):
                    item.writer.clear()

        self.projectiles = []
        self.particles = []
        self.effects = []
        self.damage_numbers = []
        self.combo_popups = []

        if self.player:
            self.player.graphics.clear()
        if self.enemy:
            self.enemy.graphics.clear()

        self._fight_visuals_dirty = False

    # ---------------- main loop ----------------

    def game_loop(self):
        if not self.running:
            return

        if self.state == GameState.MAIN_MENU:
            self._clear_fight_visuals()
            self.main_menu.draw(self)

        elif self.state == GameState.CHARACTER_SELECT:
            self._clear_fight_visuals()
            self.character_select_menu.draw(self)

        else:
            if self.state == GameState.FIGHTING:
                self.update_round_timer()
                self.update_objects()
                self.check_round_end()
                self.process_round_transition()
                self.cleanup()

            self.arena.draw(self.screen_shake)
            self.draw_objects()
            self.draw_hud()

            if self.state == GameState.PAUSED:
                self.pause_menu.draw(self)
            elif self.state == GameState.GAME_OVER:
                self.game_over_menu.draw(self)

        self.screen.update()
        self.screen.ontimer(self.game_loop, GameConfig.FRAME_MS)

    def start(self):
        self.game_loop()
        self.screen.mainloop()


class GameFactory:
    @staticmethod
    def create():
        return Game()


class Application:
    def __init__(self):
        self.game = GameFactory.create()

    def run(self):
        self.game.start()


if __name__ == "__main__":
    Application().run()
