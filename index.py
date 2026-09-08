import turtle
import math
import random
import time
from abc import ABC, abstractmethod


# ============================================================
# STICKMAN FIGHTER - REAL TIME TURTLE GAME
# ============================================================


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
        return Vector2(
            self.x / length,
            self.y / length
        )

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
        if self.paused:
            current = self.pause_started
        else:
            current = time.time()

        return current - self.start_time - self.paused_time


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


class Particle(GameObject):
    def __init__(
        self,
        x,
        y,
        color,
        velocity,
        life,
        size
    ):
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

        self.graphics.dot(
            self.position.x,
            self.position.y,
            size
        )


class HitEffect(GameObject):
    def __init__(
        self,
        x,
        y,
        color="yellow"
    ):
        super().__init__(x, y)
        self.radius = 5
        self.max_radius = 35
        self.graphics = GraphicsObject(color, 2)
        self.life = 12

    def update(self, game):
        self.radius += 3
        self.life -= 1

        if self.life <= 0:
            self.active = False

    def draw(self):
        if not self.active:
            return

        self.graphics.clear()

        self.graphics.circle(
            self.position.x,
            self.position.y,
            self.radius
        )


class Projectile(GameObject):
    def __init__(
        self,
        owner,
        x,
        y,
        direction
    ):
        super().__init__(x, y)
        self.owner = owner
        self.direction = direction
        self.speed = 8
        self.life = 90
        self.radius = 7
        self.damage = 8
        self.graphics = GraphicsObject(owner.projectile_color, 2)

    def update(self, game):
        if not self.active:
            return

        self.position.x += self.direction * self.speed
        self.life -= 1

        target = (
            game.player
            if self.owner is game.enemy
            else game.enemy
        )

        if self.position.distance_to(
            target.position
        ) < 35:

            target.take_damage(
                self.damage,
                self.position.x
            )

            game.create_hit_effect(
                self.position.x,
                self.position.y,
                target.color
            )

            self.active = False

        if abs(self.position.x) > game.arena.width / 2:
            self.active = False

        if self.life <= 0:
            self.active = False

    def draw(self):
        if not self.active:
            return

        self.graphics.clear()

        self.graphics.dot(
            self.position.x,
            self.position.y,
            self.radius
        )


class HealthBar:
    def __init__(
        self,
        x,
        y,
        width,
        height,
        color
    ):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.background = GraphicsObject("#303030", 1)
        self.foreground = GraphicsObject(color, 1)

    def draw(self, health, max_health):
        self.background.clear()
        self.foreground.clear()

        self.background.pen.fillcolor("#303030")
        self.background.pen.begin_fill()

        self.background.pen.goto(
            self.x,
            self.y
        )

        self.background.pen.pendown()

        for px, py in [
            (self.x + self.width, self.y),
            (self.x + self.width, self.y + self.height),
            (self.x, self.y + self.height)
        ]:
            self.background.pen.goto(px, py)

        self.background.pen.goto(
            self.x,
            self.y
        )

        self.background.pen.end_fill()
        self.background.pen.penup()

        ratio = max(
            0,
            min(
                1,
                health / max_health
            )
        )

        current_width = self.width * ratio

        self.foreground.pen.fillcolor(
            self.color
        )

        self.foreground.pen.begin_fill()

        self.foreground.pen.goto(
            self.x,
            self.y
        )

        self.foreground.pen.pendown()

        for px, py in [
            (self.x + current_width, self.y),
            (
                self.x + current_width,
                self.y + self.height
            ),
            (self.x, self.y + self.height)
        ]:
            self.foreground.pen.goto(px, py)

        self.foreground.pen.goto(
            self.x,
            self.y
        )

        self.foreground.pen.end_fill()
        self.foreground.pen.penup()


class FighterState(ABC):
    @abstractmethod
    def update(self, fighter, game):
        pass


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


class Fighter(GameObject):
    def __init__(
        self,
        name,
        x,
        y,
        color,
        projectile_color
    ):
        super().__init__(x, y)

        self.name = name
        self.color = color
        self.projectile_color = projectile_color

        self.width = 32
        self.height = 95

        self.max_health = 100
        self.health = 100

        self.energy = 100
        self.max_energy = 100

        self.speed = 4
        self.jump_power = 12
        self.gravity = -0.65

        self.direction = 1

        self.blocking = False
        self.attacking = False

        self.attack_timer = 0
        self.attack_cooldown = 0
        self.hit_registered = False

        self.punch_damage = 10
        self.kick_damage = 16

        self.stun_timer = 0
        self.invulnerability = 0

        self.state = IdleState()

        self.graphics = GraphicsObject(
            color,
            4
        )

    def set_state(self, state):
        self.state = state

    def set_direction_to_target(self, target):
        if target.position.x > self.position.x:
            self.direction = 1
        else:
            self.direction = -1

    def move(self, amount):
        if self.stun_timer > 0:
            return

        self.position.x += amount

        self.position.x = max(
            -450,
            min(450, self.position.x)
        )

        if abs(amount) > 0:
            self.set_state(
                WalkingState()
            )
        else:
            self.set_state(
                IdleState()
            )

    def jump(self):
        if self.stun_timer > 0:
            return

        if self.position.y <= -170:

            self.velocity.y = self.jump_power

            self.set_state(
                JumpingState()
            )

            return True

        return False

    def punch(self):
        if (
            self.stun_timer <= 0
            and self.attack_cooldown <= 0
            and self.energy >= 8
        ):

            self.attacking = True
            self.attack_timer = 12
            self.attack_cooldown = 18
            self.hit_registered = False
            self.energy -= 8

            self.set_state(
                AttackingState()
            )

            return True

        return False

    def kick(self):
        if (
            self.stun_timer <= 0
            and self.attack_cooldown <= 0
            and self.energy >= 14
        ):

            self.attacking = True
            self.attack_timer = 18
            self.attack_cooldown = 27
            self.hit_registered = False
            self.energy -= 14

            self.set_state(
                AttackingState()
            )

            return True

        return False

    def projectile(self):
        if (
            self.stun_timer <= 0
            and self.energy >= 35
            and self.attack_cooldown <= 0
        ):

            self.energy -= 35
            self.attack_cooldown = 35

            return Projectile(
                self,
                self.position.x + (
                    self.direction * 30
                ),
                self.position.y + 45,
                self.direction
            )

        return None

    def block(self, value):
        if self.stun_timer > 0:
            self.blocking = False
            return

        self.blocking = value

        if value:
            self.set_state(
                BlockingState()
            )

    def take_damage(
        self,
        damage,
        attacker_x
    ):

        if self.invulnerability > 0:
            return

        final_damage = damage

        if self.blocking:
            final_damage *= 0.25
            self.energy += 5

        final_damage = int(
            max(
                1,
                final_damage
            )
        )

        self.health -= final_damage

        self.stun_timer = (
            8 if not self.blocking
            else 3
        )

        self.invulnerability = 5

        direction = (
            1
            if self.position.x < attacker_x
            else -1
        )

        self.velocity.x = (
            direction * 4
        )

        self.velocity.y = 3

    def attack_hitbox(self):
        if not self.attacking:
            return None

        reach = (
            46
            if self.attack_timer > 6
            else 35
        )

        x = (
            self.position.x
            + self.direction * reach
        )

        y = self.position.y + 35

        radius = 24

        return (
            x,
            y,
            radius
        )

    def update_attack(self, opponent, game):

        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        if self.attack_timer > 0:

            self.attack_timer -= 1

            if (
                not self.hit_registered
                and self.attack_timer <= 9
            ):

                hitbox = self.attack_hitbox()

                if hitbox:

                    hx, hy, radius = hitbox

                    distance = math.sqrt(
                        (
                            hx
                            - opponent.position.x
                        ) ** 2
                        +
                        (
                            hy
                            - (
                                opponent.position.y
                                + 35
                            )
                        ) ** 2
                    )

                    if distance < radius + 25:

                        damage = (
                            self.kick_damage
                            if self.attack_timer > 10
                            else self.punch_damage
                        )

                        opponent.take_damage(
                            damage,
                            self.position.x
                        )

                        game.create_hit_effect(
                            opponent.position.x,
                            opponent.position.y + 35,
                            "#ffff00"
                        )

                        game.create_particles(
                            opponent.position.x,
                            opponent.position.y + 35,
                            self.color
                        )

                        self.hit_registered = True

        else:
            self.attacking = False

    def apply_physics(self):

        self.position.y += self.velocity.y

        self.velocity.y += self.gravity

        self.velocity.x *= 0.82

        if self.position.y <= -170:

            self.position.y = -170
            self.velocity.y = 0

    def regenerate_energy(self):

        self.energy += 0.45

        self.energy = min(
            self.max_energy,
            self.energy
        )

    def update(self, game):

        if self.stun_timer > 0:
            self.stun_timer -= 1

        if self.invulnerability > 0:
            self.invulnerability -= 1

        self.state.update(
            self,
            game
        )

        self.apply_physics()

        self.regenerate_energy()

        self.update_attack(
            game.enemy
            if self is game.player
            else game.player,
            game
        )

    def draw(self):

        self.graphics.clear()

        x = self.position.x
        ground = self.position.y

        head_y = ground + 78
        neck_y = ground + 60
        waist_y = ground + 30

        body_shoulder_y = ground + 58

        leg_y = ground

        direction = self.direction

        self.graphics.circle(
            x,
            head_y,
            13
        )

        self.graphics.line(
            x,
            neck_y,
            x,
            waist_y
        )

        shoulder_x = x + (
            direction * 3
        )

        left_arm_x = x - 20
        right_arm_x = x + 20

        left_hand_x = x - 30
        right_hand_x = x + 30

        arm_y = body_shoulder_y

        self.graphics.line(
            shoulder_x,
            arm_y,
            left_arm_x,
            arm_y - 20
        )

        self.graphics.line(
            left_arm_x,
            arm_y - 20,
            left_hand_x,
            arm_y - 42
        )

        self.graphics.line(
            shoulder_x,
            arm_y,
            right_arm_x,
            arm_y - 20
        )

        self.graphics.line(
            right_arm_x,
            arm_y - 20,
            right_hand_x,
            arm_y - 42
        )

        self.graphics.line(
            x,
            waist_y,
            x - 14,
            leg_y
        )

        self.graphics.line(
            x,
            waist_y,
            x + 14,
            leg_y
        )

        if self.attacking:

            attack_x = (
                x
                + direction * 48
            )

            attack_y = (
                ground + 43
            )

            self.graphics.line(
                x + direction * 6,
                body_shoulder_y,
                attack_x,
                attack_y
            )

            self.graphics.circle(
                attack_x,
                attack_y,
                5
            )

        if self.blocking:

            shield_x = (
                x
                + direction * 38
            )

            shield_y = (
                ground + 45
            )

            self.graphics.circle(
                shield_x,
                shield_y,
                22
            )


class Player(Fighter):
    def __init__(self):
        super().__init__(
            "PLAYER",
            -220,
            -170,
            "#00eaff",
            "#00ffff"
        )

        self.controls = {
            "left": False,
            "right": False,
            "up": False,
            "block": False,
            "punch": False,
            "kick": False,
            "projectile": False
        }

    def handle_input(self, game):

        if self.controls["left"]:
            self.move(-self.speed)

        if self.controls["right"]:
            self.move(self.speed)

        if self.controls["up"]:
            self.jump()

        self.block(
            self.controls["block"]
        )

        if self.controls["punch"]:
            self.punch()
            self.controls["punch"] = False

        if self.controls["kick"]:
            self.kick()
            self.controls["kick"] = False

        if self.controls["projectile"]:

            projectile = self.projectile()

            if projectile:
                game.add_projectile(
                    projectile
                )

            self.controls[
                "projectile"
            ] = False

    def update(self, game):

        self.handle_input(game)

        super().update(game)


class AIController:
    def __init__(self, fighter):
        self.fighter = fighter
        self.target = None

        self.think_timer = 0
        self.attack_timer = 0

        self.random_seed = random.random()

    def decide(self, game):

        if not self.fighter.active:
            return

        target = self.target

        if target is None:
            return

        distance = (
            target.position.x
            - self.fighter.position.x
        )

        abs_distance = abs(distance)

        self.fighter.set_direction_to_target(
            target
        )

        if self.fighter.stun_timer > 0:
            return

        if self.think_timer > 0:
            self.think_timer -= 1
            return

        self.think_timer = random.randint(
            4,
            10
        )

        if target.attacking and abs_distance < 100:

            if random.random() < 0.4:

                self.fighter.block(
                    True
                )

                return

        self.fighter.block(False)

        if abs_distance > 170:

            if distance > 0:
                self.fighter.move(
                    self.fighter.speed * 0.8
                )
            else:
                self.fighter.move(
                    -self.fighter.speed * 0.8
                )

            if (
                random.random() < 0.04
                and self.fighter.energy > 35
            ):

                projectile = (
                    self.fighter.projectile()
                )

                if projectile:
                    game.add_projectile(
                        projectile
                    )

            return

        if abs_distance > 95:

            if distance > 0:
                self.fighter.move(
                    self.fighter.speed
                )
            else:
                self.fighter.move(
                    -self.fighter.speed
                )

            if (
                random.random() < 0.12
                and self.fighter.energy > 30
            ):

                projectile = (
                    self.fighter.projectile()
                )

                if projectile:
                    game.add_projectile(
                        projectile
                    )

            return

        choice = random.random()

        if choice < 0.25:

            self.fighter.punch()

        elif choice < 0.45:

            self.fighter.kick()

        elif choice < 0.52:

            self.fighter.jump()

        elif choice < 0.63:

            projectile = (
                self.fighter.projectile()
            )

            if projectile:
                game.add_projectile(
                    projectile
                )

        else:

            if distance > 0:
                self.fighter.move(
                    self.fighter.speed
                )
            else:
                self.fighter.move(
                    -self.fighter.speed
                )


class Enemy(Fighter):
    def __init__(self):
        super().__init__(
            "ENEMY",
            220,
            -170,
            "#ff304f",
            "#ff5570"
        )

        self.ai = AIController(
            self
        )

    def update(self, game):

        self.ai.target = game.player

        self.ai.decide(game)

        super().update(game)


class Arena:
    def __init__(
        self,
        width=1000,
        height=650
    ):

        self.width = width
        self.height = height

        self.graphics = GraphicsObject(
            "#6c6c6c",
            2
        )

    def draw(self):

        self.graphics.clear()

        self.graphics.pen.color(
            "#6c6c6c"
        )

        self.graphics.pen.pensize(2)

        self.graphics.line(
            -500,
            -180,
            500,
            -180
        )

        for x in range(-500, 501, 50):

            self.graphics.line(
                x,
                -180,
                x,
                -210
            )

        self.graphics.line(
            -490,
            -180,
            -490,
            230
        )

        self.graphics.line(
            490,
            -180,
            490,
            230
        )

        for y in range(
            -130,
            231,
            60
        ):

            self.graphics.line(
                -490,
                y,
                490,
                y
            )

        self.graphics.circle(
            0,
            -170,
            100
        )


class HUD:
    def __init__(self):

        self.writer = turtle.Turtle()
        self.writer.hideturtle()
        self.writer.penup()
        self.writer.speed(0)

        self.player_bar = HealthBar(
            -460,
            230,
            350,
            22,
            "#00eaff"
        )

        self.enemy_bar = HealthBar(
            110,
            230,
            350,
            22,
            "#ff304f"
        )

        self.player_energy = HealthBar(
            -460,
            198,
            240,
            10,
            "#00aaff"
        )

        self.enemy_energy = HealthBar(
            220,
            198,
            240,
            10,
            "#ff8800"
        )

    def clear(self):

        self.writer.clear()

        self.player_bar.background.clear()
        self.player_bar.foreground.clear()

        self.enemy_bar.background.clear()
        self.enemy_bar.foreground.clear()

        self.player_energy.background.clear()
        self.player_energy.foreground.clear()

        self.enemy_energy.background.clear()
        self.enemy_energy.foreground.clear()

    def text(
        self,
        x,
        y,
        text,
        size=18,
        color="white",
        align="center"
    ):

        self.writer.goto(
            x,
            y
        )

        self.writer.color(
            color
        )

        self.writer.write(
            text,
            align=align,
            font=(
                "Arial",
                size,
                "bold"
            )
        )

    def draw(
        self,
        player,
        enemy,
        round_number,
        round_time,
        message
    ):

        self.clear()

        self.player_bar.draw(
            player.health,
            player.max_health
        )

        self.enemy_bar.draw(
            enemy.health,
            enemy.max_health
        )

        self.player_energy.draw(
            player.energy,
            player.max_energy
        )

        self.enemy_energy.draw(
            enemy.energy,
            enemy.max_energy
        )

        self.text(
            -460,
            260,
            player.name,
            16,
            "#00eaff",
            "left"
        )

        self.text(
            460,
            260,
            enemy.name,
            16,
            "#ff304f",
            "right"
        )

        self.text(
            0,
            245,
            f"ROUND {round_number}",
            18,
            "white"
        )

        self.text(
            0,
            215,
            f"{max(0, int(round_time)):02d}",
            24,
            "#ffff00"
        )

        if message:

            self.text(
                0,
                130,
                message,
                30,
                "#ffffff"
            )

        self.text(
            -470,
            -295,
            "A / D = Move",
            11,
            "#cccccc",
            "left"
        )

        self.text(
            -470,
            -315,
            "W = Jump",
            11,
            "#cccccc",
            "left"
        )

        self.text(
            -100,
            -295,
            "J = Punch",
            11,
            "#cccccc",
            "left"
        )

        self.text(
            -100,
            -315,
            "K = Kick",
            11,
            "#cccccc",
            "left"
        )

        self.text(
            100,
            -295,
            "L = Energy Blast",
            11,
            "#cccccc",
            "left"
        )

        self.text(
            100,
            -315,
            "SPACE = Block",
            11,
            "#cccccc",
            "left"
        )

        self.text(
            470,
            -295,
            "P = Pause",
            11,
            "#cccccc",
            "right"
        )

        self.text(
            470,
            -315,
            "R = Restart",
            11,
            "#cccccc",
            "right"
        )


class SoundManager:
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

    def win(self):
        pass


class InputManager:
    def __init__(self, screen, player):

        self.screen = screen
        self.player = player

        screen.listen()

        screen.onkeypress(
            self.left_down,
            "a"
        )

        screen.onkeyrelease(
            self.left_up,
            "a"
        )

        screen.onkeypress(
            self.right_down,
            "d"
        )

        screen.onkeyrelease(
            self.right_up,
            "d"
        )

        screen.onkeypress(
            self.jump,
            "w"
        )

        screen.onkeypress(
            self.punch,
            "j"
        )

        screen.onkeypress(
            self.kick,
            "k"
        )

        screen.onkeypress(
            self.projectile,
            "l"
        )

        screen.onkeypress(
            self.block_down,
            "space"
        )

        screen.onkeyrelease(
            self.block_up,
            "space"
        )

    def left_down(self):
        self.player.controls[
            "left"
        ] = True

    def left_up(self):
        self.player.controls[
            "left"
        ] = False

    def right_down(self):
        self.player.controls[
            "right"
        ] = True

    def right_up(self):
        self.player.controls[
            "right"
        ] = False

    def jump(self):
        self.player.controls[
            "up"
        ] = True

    def punch(self):
        self.player.controls[
            "punch"
        ] = True

    def kick(self):
        self.player.controls[
            "kick"
        ] = True

    def projectile(self):
        self.player.controls[
            "projectile"
        ] = True

    def block_down(self):
        self.player.controls[
            "block"
        ] = True

    def block_up(self):
        self.player.controls[
            "block"
        ] = False


class RoundManager:
    def __init__(self):

        self.round_number = 1
        self.player_rounds = 0
        self.enemy_rounds = 0

        self.round_length = 60

        self.time_left = (
            self.round_length
        )

        self.active = True

        self.message = ""

        self.round_end_timer = 0

    def reset_round(self):

        self.time_left = (
            self.round_length
        )

        self.active = True
        self.message = ""

    def start_next_round(
        self,
        player,
        enemy
    ):

        self.round_number += 1

        player.health = (
            player.max_health
        )

        enemy.health = (
            enemy.max_health
        )

        player.energy = (
            player.max_energy
        )

        enemy.energy = (
            enemy.max_energy
        )

        player.position.x = -220
        player.position.y = -170

        enemy.position.x = 220
        enemy.position.y = -170

        player.velocity = Vector2()
        enemy.velocity = Vector2()

        player.attacking = False
        enemy.attacking = False

        player.blocking = False
        enemy.blocking = False

        self.reset_round()

    def end_round(
        self,
        player,
        enemy
    ):

        if not self.active:
            return

        self.active = False

        if (
            player.health
            > enemy.health
        ):

            self.player_rounds += 1

            self.message = (
                "PLAYER WINS THE ROUND!"
            )

        elif (
            enemy.health
            > player.health
        ):

            self.enemy_rounds += 1

            self.message = (
                "ENEMY WINS THE ROUND!"
            )

        else:

            self.message = (
                "DRAW!"
            )

    def match_winner(self):

        if self.player_rounds >= 2:
            return "PLAYER"

        if self.enemy_rounds >= 2:
            return "ENEMY"

        return None


class MatchManager:
    def __init__(self):

        self.player = Player()
        self.enemy = Enemy()

        self.round_manager = (
            RoundManager()
        )

        self.game_over = False

        self.final_message = ""

    def reset_match(self):

        self.player.health = (
            self.player.max_health
        )

        self.enemy.health = (
            self.enemy.max_health
        )

        self.player.energy = (
            self.player.max_energy
        )

        self.enemy.energy = (
            self.enemy.max_energy
        )

        self.player.position = Vector2(
            -220,
            -170
        )

        self.enemy.position = Vector2(
            220,
            -170
        )

        self.round_manager = (
            RoundManager()
        )

        self.game_over = False
        self.final_message = ""


class Game:
    def __init__(self):

        self.screen = turtle.Screen()

        self.screen.setup(
            width=1050,
            height=700
        )

        self.screen.title(
            "Stickman Arena - Python OOP"
        )

        self.screen.bgcolor(
            "#10131c"
        )

        self.screen.tracer(
            0,
            0
        )

        self.arena = Arena()

        self.hud = HUD()

        self.sound = SoundManager()

        self.match = MatchManager()

        self.player = (
            self.match.player
        )

        self.enemy = (
            self.match.enemy
        )

        self.round_manager = (
            self.match.round_manager
        )

        self.input = InputManager(
            self.screen,
            self.player
        )

        self.objects = []

        self.projectiles = []

        self.particles = []

        self.effects = []

        self.running = True

        self.paused = False

        self.last_time = time.time()

        self.frame_count = 0

        self.message_timer = 0

        self.bind_game_keys()

        self.arena.draw()

    def bind_game_keys(self):

        self.screen.onkeypress(
            self.toggle_pause,
            "p"
        )

        self.screen.onkeypress(
            self.restart,
            "r"
        )

    def toggle_pause(self):

        if self.match.game_over:
            return

        self.paused = not self.paused

        if self.paused:
            self.hud.draw(
                self.player,
                self.enemy,
                self.round_manager.round_number,
                self.round_manager.time_left,
                "PAUSED"
            )

        else:
            self.last_time = time.time()

    def restart(self):

        self.match.reset_match()

        self.player = (
            self.match.player
        )

        self.enemy = (
            self.match.enemy
        )

        self.round_manager = (
            self.match.round_manager
        )

        self.input.player = (
            self.player
        )

        self.projectiles.clear()
        self.particles.clear()
        self.effects.clear()

        self.paused = False
        self.match.game_over = False

    def add_projectile(
        self,
        projectile
    ):

        self.projectiles.append(
            projectile
        )

    def create_particles(
        self,
        x,
        y,
        color
    ):

        for _ in range(8):

            velocity = Vector2(
                random.uniform(
                    -4,
                    4
                ),
                random.uniform(
                    1,
                    6
                )
            )

            particle = Particle(
                x,
                y,
                color,
                velocity,
                random.randint(
                    10,
                    24
                ),
                random.randint(
                    5,
                    10
                )
            )

            self.particles.append(
                particle
            )

    def create_hit_effect(
        self,
        x,
        y,
        color
    ):

        self.effects.append(
            HitEffect(
                x,
                y,
                color
            )
        )

    def cleanup(self):

        self.projectiles = [
            item
            for item in self.projectiles
            if item.active
        ]

        self.particles = [
            item
            for item in self.particles
            if item.active
        ]

        self.effects = [
            item
            for item in self.effects
            if item.active
        ]

    def update_round(self):

        if not self.round_manager.active:
            return

        now = time.time()

        delta = (
            now - self.last_time
        )

        self.last_time = now

        self.round_manager.time_left -= delta

        if self.round_manager.time_left <= 0:

            self.round_manager.time_left = 0

            self.round_manager.end_round(
                self.player,
                self.enemy
            )

            self.message_timer = 90

    def check_round_end(self):

        if not self.round_manager.active:
            return

        if (
            self.player.health <= 0
            or self.enemy.health <= 0
        ):

            self.round_manager.end_round(
                self.player,
                self.enemy
            )

            self.message_timer = 90

    def process_round_transition(self):

        if self.round_manager.active:
            return

        winner = (
            self.round_manager
            .match_winner()
        )

        if winner:

            self.match.game_over = True

            self.match.final_message = (
                "PLAYER WINS THE MATCH!"
                if winner == "PLAYER"
                else "ENEMY WINS THE MATCH!"
            )

            return

        if self.message_timer > 0:

            self.message_timer -= 1

            return

        self.round_manager.start_next_round(
            self.player,
            self.enemy
        )

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

    def draw_objects(self):

        self.player.draw()

        self.enemy.draw()

        for projectile in self.projectiles:
            projectile.draw()

        for particle in self.particles:
            particle.draw()

        for effect in self.effects:
            effect.draw()

    def draw_hud(self):

        if self.match.game_over:

            self.hud.draw(
                self.player,
                self.enemy,
                self.round_manager.round_number,
                0,
                self.match.final_message
                + "   Press R to Restart"
            )

            return

        self.hud.draw(
            self.player,
            self.enemy,
            self.round_manager.round_number,
            self.round_manager.time_left,
            self.round_manager.message
            if not self.round_manager.active
            else ""
        )

    def game_loop(self):

        if not self.running:

            return

        if not self.paused:

            if not self.match.game_over:

                self.update_round()

                self.update_objects()

                self.check_round_end()

                self.process_round_transition()

                self.cleanup()

        self.draw_objects()

        self.draw_hud()

        self.screen.update()

        self.screen.ontimer(
            self.game_loop,
            16
        )

    def start(self):

        self.game_loop()

        self.screen.mainloop()


class GameFactory:
    @staticmethod
    def create():

        game = Game()

        return game


class ScoreBoard:
    def __init__(self):

        self.player_score = 0
        self.enemy_score = 0

    def add_player(self):
        self.player_score += 1

    def add_enemy(self):
        self.enemy_score += 1

    def reset(self):
        self.player_score = 0
        self.enemy_score = 0


class DamageCalculator:
    def __init__(self):

        self.punch_damage = 10
        self.kick_damage = 16

    def calculate(
        self,
        attack_type,
        blocking=False
    ):

        if attack_type == "PUNCH":

            damage = self.punch_damage

        elif attack_type == "KICK":

            damage = self.kick_damage

        else:

            damage = 0

        if blocking:

            damage *= 0.25

        return max(
            1,
            int(damage)
        )


class CollisionDetector:
    def __init__(self):

        self.fighter_distance = 48
        self.projectile_distance = 32

    def fighters_collide(
        self,
        first,
        second
    ):

        return (
            first.position.distance_to(
                second.position
            )
            < self.fighter_distance
        )

    def projectile_hits(
        self,
        projectile,
        fighter
    ):

        return (
            projectile.position.distance_to(
                fighter.position
            )
            < self.projectile_distance
        )


class Logger:
    def __init__(
        self,
        filename="game.log"
    ):

        self.filename = filename

    def write(self, message):

        try:

            with open(
                self.filename,
                "a",
                encoding="utf-8"
            ) as file:

                file.write(
                    message + "\n"
                )

        except OSError:

            pass


class GameStatistics:
    def __init__(self):

        self.total_damage_dealt = 0
        self.total_hits = 0
        self.punches = 0
        self.kicks = 0
        self.projectiles = 0

    def register_damage(
        self,
        amount
    ):

        self.total_damage_dealt += amount
        self.total_hits += 1

    def register_punch(self):

        self.punches += 1

    def register_kick(self):

        self.kicks += 1

    def register_projectile(self):

        self.projectiles += 1

    def reset(self):

        self.total_damage_dealt = 0
        self.total_hits = 0
        self.punches = 0
        self.kicks = 0
        self.projectiles = 0


class TrainingMode:
    def __init__(self):

        self.enabled = False

    def toggle(self):

        self.enabled = not self.enabled

    def apply(self, fighter):

        if not self.enabled:
            return

        fighter.energy = (
            fighter.max_energy
        )

        fighter.health = (
            fighter.max_health
        )


class Difficulty:
    EASY = "Easy"
    NORMAL = "Normal"
    HARD = "Hard"


class DifficultyManager:
    def __init__(self):

        self.current = (
            Difficulty.NORMAL
        )

    def set_difficulty(
        self,
        difficulty
    ):

        valid = {
            Difficulty.EASY,
            Difficulty.NORMAL,
            Difficulty.HARD
        }

        if difficulty in valid:

            self.current = difficulty

    def multiplier(self):

        if self.current == Difficulty.EASY:
            return 0.7

        if self.current == Difficulty.HARD:
            return 1.25

        return 1.0


class ReplayData:
    def __init__(self):

        self.frames = []

    def record(
        self,
        player_x,
        enemy_x
    ):

        self.frames.append(
            (
                player_x,
                enemy_x
            )
        )

    def clear(self):

        self.frames.clear()


class Camera:
    def __init__(self):

        self.x = 0
        self.y = 0

    def follow(self, target):

        self.x += (
            target.position.x
            - self.x
        ) * 0.05

        self.y += (
            target.position.y
            - self.y
        ) * 0.05


class TextButton:
    def __init__(
        self,
        x,
        y,
        label
    ):

        self.x = x
        self.y = y
        self.label = label

    def contains(
        self,
        x,
        y
    ):

        return (
            abs(x - self.x) < 80
            and abs(y - self.y) < 25
        )


class GameConfig:
    WIDTH = 1050
    HEIGHT = 700
    FPS = 60
    GROUND_Y = -170
    PLAYER_START_X = -220
    ENEMY_START_X = 220
    ROUND_TIME = 60


class Application:
    def __init__(self):

        self.game = (
            GameFactory.create()
        )

    def run(self):

        self.game.start()


if __name__ == "__main__":
    Application().run()