"""
Wizard of Wor 3D - First Person Dungeon Crawler
A 3D reimagining of the classic 1981 arcade game.

Controls:
- WASD: Move
- Mouse: Look around
- Left Click: Shoot
- ESC: Exit
"""

import math
import random

from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.shaders import lit_with_shadows_shader

# =============================================================================
# MAZE LAYOUT (Dungeon 7 reference)
# =============================================================================
MAZE_LAYOUT = [
    "#####################",
    "#.#####..###..#####.#",
    "#..##.#.......#.##..#",
    "#.....#.##.##.#.....#",
    "#...#...........#...#",
    "#...#..#######..#...#",
    "#...####.....####...#",
    "#......#.....#......#",  # Closed tunnels for 3D
    "#......#.....#......#",
    "#..#.....#.#.....#..#",
    "#..#.##..#.#..##.#..#",
    "#..###.........###..#",
    "#...................#",
    "#...................#",
    "#####################",
]
MAZE = [[1 if cell == "#" else 0 for cell in row] for row in MAZE_LAYOUT]

MAZE_WIDTH = len(MAZE[0])
MAZE_HEIGHT = len(MAZE)
TILE_SIZE = 2  # Size of each tile in 3D units
WALL_HEIGHT = 3

# Colors (neon theme)
NEON_BLUE = color.rgb(0, 150, 255)
NEON_CYAN = color.rgb(0, 255, 255)
NEON_PURPLE = color.rgb(180, 0, 255)
NEON_PINK = color.rgb(255, 0, 150)
NEON_GREEN = color.rgb(0, 255, 100)
NEON_RED = color.rgb(255, 50, 50)
NEON_ORANGE = color.rgb(255, 150, 0)
NEON_YELLOW = color.rgb(255, 255, 0)

# =============================================================================
# GAME APPLICATION
# =============================================================================
app = Ursina(
    title="Shapshique of Wor 3D",
    borderless=False,
    fullscreen=False,
    development_mode=False,
    vsync=True,
)

# =============================================================================
# CUSTOM SHADERS AND EFFECTS
# =============================================================================


class NeonMaterial:
    """Creates glowing neon materials."""

    @staticmethod
    def create(base_color, emission_strength=2):
        return color.rgb(
            min(255, int(base_color.r * 255 * emission_strength)),
            min(255, int(base_color.g * 255 * emission_strength)),
            min(255, int(base_color.b * 255 * emission_strength)),
        )


# =============================================================================
# MAZE BUILDER
# =============================================================================


class MazeBuilder:
    """Builds the 3D maze from the 2D layout."""

    def __init__(self):
        self.walls = []
        self.floor_tiles = []
        self.valid_positions = []

    def build(self):
        """Create the 3D maze."""
        # Create floor
        floor = Entity(
            model="plane",
            scale=(MAZE_WIDTH * TILE_SIZE, 1, MAZE_HEIGHT * TILE_SIZE),
            position=(
                MAZE_WIDTH * TILE_SIZE / 2 - TILE_SIZE / 2,
                0,
                MAZE_HEIGHT * TILE_SIZE / 2 - TILE_SIZE / 2,
            ),
            color=color.rgb(10, 10, 30),
            texture="white_cube",
            collider="box",
        )

        # Create ceiling
        ceiling = Entity(
            model="plane",
            scale=(MAZE_WIDTH * TILE_SIZE, 1, MAZE_HEIGHT * TILE_SIZE),
            position=(
                MAZE_WIDTH * TILE_SIZE / 2 - TILE_SIZE / 2,
                WALL_HEIGHT,
                MAZE_HEIGHT * TILE_SIZE / 2 - TILE_SIZE / 2,
            ),
            rotation=(180, 0, 0),
            color=color.rgb(5, 5, 20),
            texture="white_cube",
        )

        # Create walls and track valid positions
        for row in range(MAZE_HEIGHT):
            for col in range(MAZE_WIDTH):
                x = col * TILE_SIZE
                z = row * TILE_SIZE

                if MAZE[row][col] == 1:
                    # Create wall block
                    wall = Entity(
                        model="cube",
                        position=(x, WALL_HEIGHT / 2, z),
                        scale=(TILE_SIZE, WALL_HEIGHT, TILE_SIZE),
                        color=color.rgb(20, 40, 80),
                        collider="box",
                    )
                    self.walls.append(wall)

                    # Add neon edge lines
                    self._add_wall_glow(x, z)
                else:
                    # Track valid floor positions
                    self.valid_positions.append((x, z))

                    # Add floor grid glow
                    self._add_floor_glow(x, z)

        return self.valid_positions

    def _add_wall_glow(self, x, z):
        """Add glowing edges to walls."""
        # Top edge glow
        edge = Entity(
            model="cube",
            position=(x, WALL_HEIGHT + 0.05, z),
            scale=(TILE_SIZE + 0.1, 0.1, TILE_SIZE + 0.1),
            color=NEON_BLUE,
            unlit=True,
        )

    def _add_floor_glow(self, x, z):
        """Add subtle grid lines on floor."""
        # Grid line
        line = Entity(
            model="cube",
            position=(x, 0.01, z),
            scale=(TILE_SIZE - 0.1, 0.02, 0.05),
            color=color.rgb(0, 50, 100),
            unlit=True,
        )


# =============================================================================
# PLASMA BULLET
# =============================================================================


class PlasmaBullet(Entity):
    """Glowing plasma projectile."""

    def __init__(self, position, direction, is_player=True, **kwargs):
        super().__init__(
            model="sphere",
            scale=0.2,
            position=position,
            color=NEON_YELLOW if is_player else NEON_RED,
            unlit=True,
            **kwargs,
        )
        self.direction = direction
        self.speed = 30
        self.is_player = is_player
        self.lifetime = 3
        self.age = 0

        # Glow effect
        self.glow = Entity(
            parent=self,
            model="sphere",
            scale=2,
            color=(
                color.rgba(255, 255, 0, 50)
                if is_player
                else color.rgba(255, 50, 50, 50)
            ),
            unlit=True,
        )

    def update(self):
        self.age += time.dt
        if self.age > self.lifetime:
            destroy(self)
            return

        # Move bullet
        self.position += self.direction * self.speed * time.dt

        # Check wall collision
        hit_info = raycast(self.position, self.direction, distance=0.5, ignore=[self])
        if hit_info.hit:
            # Spawn impact particles
            self._spawn_impact()
            destroy(self)

    def _spawn_impact(self):
        """Create impact effect."""
        for _ in range(5):
            particle = Entity(
                model="sphere",
                scale=0.1,
                position=self.position,
                color=self.color,
                unlit=True,
            )
            particle.animate_scale(0, duration=0.3)
            particle.animate_position(
                self.position
                + Vec3(
                    random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1)
                ),
                duration=0.3,
            )
            destroy(particle, delay=0.3)


# =============================================================================
# ENEMY BASE CLASS
# =============================================================================


class Enemy(Entity):
    """Base class for all enemies."""

    def __init__(self, position, enemy_type="burwor", **kwargs):
        self.enemy_type = enemy_type
        self.base_color = self._get_color()

        super().__init__(
            model="cube",
            scale=(0.8, 1.5, 0.8),
            position=Vec3(position[0], 0.75, position[1]),
            color=self.base_color,
            collider="box",
            **kwargs,
        )

        self.speed = self._get_speed()
        self.health = self._get_health()
        self.points = self._get_points()
        self.direction = Vec3(random.choice([-1, 1]), 0, 0)
        self.move_timer = 0
        self.shoot_cooldown = 0
        self.visible_enemy = True  # For Garwor cloaking
        self.animation_time = 0

        # Create enemy visuals
        self._create_visuals()

    def _get_color(self):
        colors = {
            "burwor": NEON_BLUE,
            "garwor": NEON_ORANGE,
            "thorwor": NEON_RED,
            "worluk": NEON_GREEN,
            "wizard": NEON_PURPLE,
        }
        return colors.get(self.enemy_type, NEON_BLUE)

    def _get_speed(self):
        speeds = {"burwor": 2, "garwor": 3, "thorwor": 4, "worluk": 5, "wizard": 3}
        return speeds.get(self.enemy_type, 2)

    def _get_health(self):
        health = {"burwor": 1, "garwor": 1, "thorwor": 1, "worluk": 1, "wizard": 3}
        return health.get(self.enemy_type, 1)

    def _get_points(self):
        points = {
            "burwor": 100,
            "garwor": 200,
            "thorwor": 500,
            "worluk": 1000,
            "wizard": 2500,
        }
        return points.get(self.enemy_type, 100)

    def _create_visuals(self):
        """Create enemy-specific visual elements."""
        # Eyes
        eye_color = NEON_RED if self.enemy_type != "wizard" else NEON_CYAN

        self.left_eye = Entity(
            parent=self,
            model="sphere",
            scale=0.15,
            position=(-0.2, 0.3, 0.4),
            color=eye_color,
            unlit=True,
        )

        self.right_eye = Entity(
            parent=self,
            model="sphere",
            scale=0.15,
            position=(0.2, 0.3, 0.4),
            color=eye_color,
            unlit=True,
        )

        # Type-specific features
        if self.enemy_type == "burwor":
            # Mandibles
            self.left_mandible = Entity(
                parent=self,
                model="cube",
                scale=(0.1, 0.05, 0.3),
                position=(-0.3, 0, 0.5),
                rotation=(0, -30, 0),
                color=self.base_color,
            )
            self.right_mandible = Entity(
                parent=self,
                model="cube",
                scale=(0.1, 0.05, 0.3),
                position=(0.3, 0, 0.5),
                rotation=(0, 30, 0),
                color=self.base_color,
            )

        elif self.enemy_type == "thorwor":
            # Stinger tail
            self.tail = Entity(
                parent=self,
                model="cube",
                scale=(0.1, 0.1, 0.6),
                position=(0, 0.8, -0.5),
                rotation=(45, 0, 0),
                color=NEON_YELLOW,
            )

        elif self.enemy_type == "worluk":
            # Wings
            self.left_wing = Entity(
                parent=self,
                model="quad",
                scale=(0.8, 0.6, 1),
                position=(-0.6, 0.2, 0),
                rotation=(0, 90, 0),
                color=color.rgba(0, 255, 100, 150),
                double_sided=True,
            )
            self.right_wing = Entity(
                parent=self,
                model="quad",
                scale=(0.8, 0.6, 1),
                position=(0.6, 0.2, 0),
                rotation=(0, -90, 0),
                color=color.rgba(0, 255, 100, 150),
                double_sided=True,
            )

        elif self.enemy_type == "wizard":
            # Staff
            self.staff = Entity(
                parent=self,
                model="cube",
                scale=(0.1, 1.5, 0.1),
                position=(0.5, 0, 0),
                color=NEON_PURPLE,
            )
            # Orb
            self.orb = Entity(
                parent=self,
                model="sphere",
                scale=0.2,
                position=(0.5, 0.8, 0),
                color=NEON_CYAN,
                unlit=True,
            )

    def update(self):
        self.animation_time += time.dt

        # Animate eyes
        eye_pulse = 1 + math.sin(self.animation_time * 5) * 0.2
        self.left_eye.scale = Vec3(0.15 * eye_pulse, 0.15 * eye_pulse, 0.15 * eye_pulse)
        self.right_eye.scale = Vec3(
            0.15 * eye_pulse, 0.15 * eye_pulse, 0.15 * eye_pulse
        )

        # Type-specific animations
        if self.enemy_type == "burwor" and hasattr(self, "left_mandible"):
            mandible_angle = math.sin(self.animation_time * 8) * 15
            self.left_mandible.rotation_y = -30 - mandible_angle
            self.right_mandible.rotation_y = 30 + mandible_angle

        elif self.enemy_type == "worluk" and hasattr(self, "left_wing"):
            wing_flap = math.sin(self.animation_time * 10) * 20
            self.left_wing.rotation_z = wing_flap
            self.right_wing.rotation_z = -wing_flap
            self.y = 0.75 + math.sin(self.animation_time * 3) * 0.2

        elif self.enemy_type == "wizard" and hasattr(self, "orb"):
            self.orb.scale = 0.2 + math.sin(self.animation_time * 4) * 0.05

        # Garwor cloaking
        if self.enemy_type == "garwor":
            if random.random() < 0.005:  # Random cloak toggle
                self.visible_enemy = not self.visible_enemy
                self.alpha = 0.2 if not self.visible_enemy else 1

        # AI Movement
        self.move_timer += time.dt
        if self.move_timer > 0.5:
            self.move_timer = 0
            if random.random() < 0.3:
                # Change direction
                directions = [
                    Vec3(1, 0, 0),
                    Vec3(-1, 0, 0),
                    Vec3(0, 0, 1),
                    Vec3(0, 0, -1),
                ]
                self.direction = random.choice(directions)

        # Move
        new_pos = self.position + self.direction * self.speed * time.dt

        # Check wall collision
        hit = raycast(self.position, self.direction, distance=1, ignore=[self])
        if not hit.hit:
            self.position = new_pos
        else:
            # Bounce off wall
            self.direction = -self.direction

        # Face movement direction
        if self.direction.x != 0 or self.direction.z != 0:
            target_angle = math.atan2(self.direction.x, self.direction.z)
            self.rotation_y = math.degrees(target_angle)

    def take_damage(self, amount=1):
        """Handle taking damage."""
        self.health -= amount

        # Flash red
        self.color = NEON_RED
        invoke(setattr, self, "color", self.base_color, delay=0.1)

        if self.health <= 0:
            self.die()
            return True
        return False

    def die(self):
        """Handle death."""
        # Spawn death particles
        for _ in range(20):
            particle = Entity(
                model="sphere",
                scale=0.15,
                position=self.position,
                color=self.base_color,
                unlit=True,
            )
            particle.animate_position(
                self.position
                + Vec3(
                    random.uniform(-2, 2), random.uniform(0, 3), random.uniform(-2, 2)
                ),
                duration=0.5,
                curve=curve.out_expo,
            )
            particle.animate_scale(0, duration=0.5)
            destroy(particle, delay=0.5)

        destroy(self)


# =============================================================================
# PLAYER GUN
# =============================================================================


class PlasmaGun(Entity):
    """First-person plasma rifle."""

    def __init__(self):
        super().__init__(
            parent=camera,
            model="cube",
            scale=(0.1, 0.1, 0.5),
            position=(0.4, -0.3, 0.5),
            color=color.gray,
            rotation=(0, 0, 0),
        )

        # Gun barrel
        self.barrel = Entity(
            parent=self,
            model="cube",
            scale=(0.5, 0.5, 1.5),
            position=(0, 0, 0.8),
            color=color.dark_gray,
        )

        # Muzzle glow
        self.muzzle = Entity(
            parent=self,
            model="sphere",
            scale=0.15,
            position=(0, 0, 1.5),
            color=NEON_YELLOW,
            unlit=True,
        )

        self.cooldown = 0
        self.base_position = self.position

    def update(self):
        if self.cooldown > 0:
            self.cooldown -= time.dt

        # Muzzle pulse
        self.muzzle.scale = 0.15 + math.sin(time.time() * 10) * 0.03

        # Idle bob
        self.position = self.base_position + Vec3(
            math.sin(time.time() * 2) * 0.01, math.sin(time.time() * 3) * 0.01, 0
        )

    def shoot(self):
        if self.cooldown > 0:
            return None

        self.cooldown = 0.2

        # Recoil animation
        self.animate_position(self.base_position + Vec3(0, 0, -0.1), duration=0.05)
        invoke(self.animate_position, self.base_position, duration=0.1, delay=0.05)

        # Muzzle flash
        self.muzzle.scale = 0.4
        self.muzzle.animate_scale(0.15, duration=0.1)

        # Create bullet
        bullet = PlasmaBullet(
            position=camera.world_position + camera.forward * 1,
            direction=camera.forward,
            is_player=True,
        )

        return bullet


# =============================================================================
# HUD
# =============================================================================


class HUD(Entity):
    """Heads-up display."""

    def __init__(self):
        super().__init__()

        # Score
        self.score_text = Text(
            text="SCORE: 0", position=(-0.85, 0.45), scale=2, color=NEON_YELLOW
        )

        # Health
        self.health_text = Text(
            text="LIVES: 3", position=(-0.85, 0.40), scale=2, color=NEON_GREEN
        )

        # Enemy count
        self.enemy_text = Text(
            text="ENEMIES: 0", position=(0.55, 0.45), scale=2, color=NEON_RED
        )

        # Crosshair
        self.crosshair = Entity(
            parent=camera.ui, model="quad", scale=0.02, color=NEON_CYAN
        )

        # Message display
        self.message = Text(
            text="", position=(0, 0.3), origin=(0, 0), scale=3, color=NEON_PURPLE
        )
        self.message_timer = 0

    def update_score(self, score):
        self.score_text.text = f"SCORE: {score}"

    def update_lives(self, lives):
        self.health_text.text = f"LIVES: {lives}"
        self.health_text.color = NEON_GREEN if lives > 1 else NEON_RED

    def update_enemies(self, count):
        self.enemy_text.text = f"ENEMIES: {count}"

    def show_message(self, text, duration=2):
        self.message.text = text
        self.message_timer = duration

    def update(self):
        if self.message_timer > 0:
            self.message_timer -= time.dt
            if self.message_timer <= 0:
                self.message.text = ""


# =============================================================================
# GAME MANAGER
# =============================================================================


class GameManager(Entity):
    """Manages game state and logic."""

    def __init__(self):
        super().__init__()

        self.score = 0
        self.lives = 3
        self.level = 1
        self.phase = "normal"
        self.enemies = []
        self.bullets = []
        self.game_over = False
        self.victory = False

        # Build maze
        self.maze_builder = MazeBuilder()
        self.valid_positions = self.maze_builder.build()

        # Setup player
        self.setup_player()

        # Create gun
        self.gun = PlasmaGun()

        # Create HUD
        self.hud = HUD()

        # Spawn enemies
        self.spawn_enemies()

        # Add lighting
        self.setup_lighting()

        # Show welcome message
        self.hud.show_message("WELCOME TO THE DUNGEON OF WOR!", 3)

    def setup_player(self):
        """Setup first-person player controller."""
        # Find spawn position (bottom-left area)
        spawn_pos = None
        for pos in self.valid_positions:
            if pos[1] > MAZE_HEIGHT * TILE_SIZE * 0.7:  # Bottom area
                spawn_pos = pos
                break

        if not spawn_pos:
            spawn_pos = self.valid_positions[0]

        self.player = FirstPersonController(
            position=(spawn_pos[0], 1, spawn_pos[1]),
            speed=8,
            jump_height=0,  # No jumping in this game
            gravity=0,  # No gravity needed
        )
        self.player.cursor.visible = False
        self.player_spawn = spawn_pos

    def setup_lighting(self):
        """Setup atmospheric lighting."""
        # Ambient light
        AmbientLight(color=color.rgba(50, 50, 80, 255))

        # Player light (flashlight effect)
        self.player_light = PointLight(
            parent=camera,
            position=(0, 0, 0),
            color=color.rgb(100, 150, 255),
            shadows=False,
        )

    def spawn_enemies(self):
        """Spawn enemies for current phase."""
        # Clear existing enemies
        for enemy in self.enemies:
            if enemy:
                destroy(enemy)
        self.enemies = []

        if self.phase == "normal":
            # Spawn mix of burwors, garwors, thorwors
            enemy_types = ["burwor"] * 3 + ["garwor"] * 2 + ["thorwor"] * 1

            for enemy_type in enemy_types:
                pos = random.choice(self.valid_positions)
                # Make sure not too close to player
                while (
                    abs(pos[0] - self.player_spawn[0]) < 4
                    and abs(pos[1] - self.player_spawn[1]) < 4
                ):
                    pos = random.choice(self.valid_positions)

                enemy = Enemy(pos, enemy_type)
                self.enemies.append(enemy)

        elif self.phase == "worluk":
            pos = random.choice(self.valid_positions)
            enemy = Enemy(pos, "worluk")
            self.enemies.append(enemy)
            self.hud.show_message("THE WORLUK APPEARS!", 3)

        elif self.phase == "wizard":
            pos = random.choice(self.valid_positions)
            enemy = Enemy(pos, "wizard")
            self.enemies.append(enemy)
            self.hud.show_message("I AM THE WIZARD OF WOR!", 3)

        self.hud.update_enemies(len(self.enemies))

    def input(self, key):
        if self.game_over or self.victory:
            if key == "r":
                # Restart game
                scene.clear()
                self.__init__()
            return

        if key == "left mouse down":
            bullet = self.gun.shoot()
            if bullet:
                self.bullets.append(bullet)

    def update(self):
        if self.game_over:
            self.hud.show_message("GAME OVER - Press R to restart", 999)
            return

        if self.victory:
            self.hud.show_message(
                f"VICTORY! Score: {self.score} - Press R to restart", 999
            )
            return

        # Update HUD
        self.hud.update_score(self.score)
        self.hud.update_lives(self.lives)

        # Check bullet-enemy collisions
        for bullet in self.bullets[:]:
            if not bullet or not hasattr(bullet, "position"):
                self.bullets.remove(bullet)
                continue

            if bullet.is_player:
                for enemy in self.enemies[:]:
                    if not enemy:
                        continue
                    if distance(bullet.position, enemy.position) < 1:
                        # Hit!
                        if enemy.take_damage():
                            self.score += enemy.points
                            self.enemies.remove(enemy)
                            self.hud.update_enemies(len(self.enemies))
                        destroy(bullet)
                        if bullet in self.bullets:
                            self.bullets.remove(bullet)
                        break

        # Check if player is hit by enemy
        for enemy in self.enemies:
            if not enemy:
                continue
            if distance(self.player.position, enemy.position) < 1.5:
                self.player_hit()
                break

        # Check phase progression
        if len(self.enemies) == 0:
            if self.phase == "normal":
                self.phase = "worluk"
                invoke(self.spawn_enemies, delay=1)
            elif self.phase == "worluk":
                self.phase = "wizard"
                invoke(self.spawn_enemies, delay=1)
            elif self.phase == "wizard":
                self.victory = True

    def player_hit(self):
        """Handle player getting hit."""
        self.lives -= 1
        self.hud.update_lives(self.lives)

        # Flash screen red
        flash = Entity(
            parent=camera.ui,
            model="quad",
            scale=2,
            color=color.rgba(255, 0, 0, 100),
            z=-1,
        )
        flash.animate_color(color.rgba(255, 0, 0, 0), duration=0.5)
        destroy(flash, delay=0.5)

        if self.lives <= 0:
            self.game_over = True
        else:
            # Respawn
            self.player.position = Vec3(self.player_spawn[0], 1, self.player_spawn[1])
            self.hud.show_message("PREPARE YOURSELF!", 2)


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    # Set window properties
    window.title = "Shapshique of Wor"
    window.borderless = False
    window.fullscreen = False
    window.exit_button.visible = False
    window.fps_counter.enabled = True

    # Set sky color
    window.color = color.rgb(5, 5, 15)

    # Create game
    game = GameManager()

    # Instructions
    print("\n" + "=" * 50)
    print("WIZARD OF WOR 3D")
    print("=" * 50)
    print("Controls:")
    print("  WASD - Move")
    print("  Mouse - Look around")
    print("  Left Click - Shoot")
    print("  ESC - Exit")
    print("=" * 50 + "\n")

    app.run()
    app.run()
    app.run()
    app.run()
