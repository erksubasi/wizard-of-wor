"""
Wizard of Wor - Isometric 2.5D Edition (Ursina Engine)
A 2.5D isometric reimagining of the classic 1981 arcade game.

Uses Ursina engine with orthographic camera for proper isometric projection.

Controls:
- Arrow Keys / WASD: Move (camera-relative)
- Space: Shoot
- Right Mouse Drag: Rotate camera (Lazy Susan style)
- Mouse Wheel: Zoom in/out
- Middle Mouse / M: Reset camera
- ESC: Quit
"""

import math
import random

from ursina import *

# =============================================================================
# MAZE LAYOUT
# =============================================================================
MAZE = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 1, 0, 0, 1, 1, 1, 0, 1, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 0, 1],
    [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],  # Tunnel row
    [1, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 1, 0, 0, 1, 1, 1, 0, 1, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]

MAZE_WIDTH = len(MAZE[0])
MAZE_HEIGHT = len(MAZE)
TILE_SIZE = 1.0  # Size of each tile in 3D units
WALL_HEIGHT = 0.8

# Colors (underwater theme - matching reference art)
NEON_BLUE = color.rgb(0, 150, 255)
NEON_CYAN = color.rgb(0, 255, 255)
NEON_PURPLE = color.rgb(150, 80, 200)
NEON_PINK = color.rgb(255, 130, 180)
NEON_GREEN = color.rgb(100, 200, 100)  # Sea green
NEON_RED = color.rgb(255, 80, 80)
NEON_ORANGE = color.rgb(255, 150, 80)  # Coral orange
NEON_YELLOW = color.rgb(255, 220, 100)  # Submarine yellow
DARK_BLUE = color.rgb(15, 30, 50)  # Deep ocean
FLOOR_COLOR = color.rgb(210, 195, 160)  # Sandy beige floor
WALL_COLOR = color.rgb(80, 150, 160)  # Teal wall base

# Underwater specific colors
CORAL_PINK = color.rgb(255, 120, 150)
CORAL_ORANGE = color.rgb(255, 140, 80)
SEAWEED_GREEN = color.rgb(30, 120, 60)
DEEP_WATER = color.rgb(10, 30, 60)
SAND_COLOR = color.rgb(60, 80, 70)

# Texture assets (cropped from assets/images/underwater_maze_assets.png)
FLOOR_TEXTURE = "assets/images/underwater_floor_tile.png"
WALL_TEXTURE = "assets/images/underwater_wall_tile.png"
BACKGROUND_TEXTURE = "assets/images/underwater_background.png"

ASSET_DIR = "assets/images/underwater_assets"
WALL_TOP_TEXTURES = {
    "plus": f"{ASSET_DIR}/wall_plus.png",
    "t": f"{ASSET_DIR}/wall_t.png",
    "corner": f"{ASSET_DIR}/wall_corner.png",
    "straight": f"{ASSET_DIR}/wall_straight.png",
}
DECOR_TEXTURES = {
    "coral_pink_orange": f"{ASSET_DIR}/coral_pink_orange.png",
    "seaweed_starfish": f"{ASSET_DIR}/seaweed_starfish.png",
    "anemone_yellow_coral": f"{ASSET_DIR}/anemone_yellow_coral.png",
    "coral_blue": f"{ASSET_DIR}/coral_blue.png",
    "shell": f"{ASSET_DIR}/shell.png",
    "rock": f"{ASSET_DIR}/rock.png",
    "sparkle": f"{ASSET_DIR}/sparkle.png",
    "submarine": f"{ASSET_DIR}/submarine.png",
    "bubble_large": f"{ASSET_DIR}/bubble_large.png",
    "bubble_small": f"{ASSET_DIR}/bubble_small.png",
}

# =============================================================================
# GAME APPLICATION
# =============================================================================
app = Ursina(
    title="Wizard of Wor - Isometric 2.5D",
    borderless=False,
    fullscreen=False,
    development_mode=False,
    vsync=True,
)


# =============================================================================
# ISOMETRIC CAMERA CONTROLLER (Lazy Susan / Pivot System)
# =============================================================================
class IsometricCamera(Entity):
    """
    Pro camera rig using industry best practices:
    1. Locked pitch (no tilting) - keeps isometric look consistent
    2. Pivot-based rotation (Lazy Susan) - rotates around center, not itself
    3. Left-click drag to rotate
    4. Two-finger trackpad / scroll to pan
    """

    def __init__(self):
        super().__init__()

        # Camera settings
        self.rotation_sensitivity = 80  # Degrees per screen-width of drag
        self.pan_sensitivity = 30  # Pan speed for trackpad
        self.min_zoom = 15  # Don't allow zooming in too much (causes clipping)
        self.max_zoom = 40
        self.target_zoom = 24  # Default zoom to fit maze nicely

        # The pivot sits at maze center - camera orbits around this
        self.pivot = Entity(
            position=(MAZE_WIDTH * TILE_SIZE / 2, 0, MAZE_HEIGHT * TILE_SIZE / 2)
        )

        # Target position for smooth panning
        self.target_pivot_pos = Vec3(
            MAZE_WIDTH * TILE_SIZE / 2, 0, MAZE_HEIGHT * TILE_SIZE / 2
        )

        # Yaw = rotation around Y axis (the "Lazy Susan" spin)
        self.yaw = 225  # Classic isometric angle from top-right
        self.target_yaw = 225

        # Fixed pitch for isometric look (LOCKED - never changes)
        self.pitch = 35.264  # True isometric angle

        # Setup camera as child of pivot
        camera.parent = self.pivot
        camera.orthographic = True
        camera.fov = self.target_zoom

        # Set clip planes to see all geometry
        camera.clip_plane_near = 0.1
        camera.clip_plane_far = 1000

        # Position camera high and back from pivot
        distance = 50
        camera.position = (
            0,
            distance * math.sin(math.radians(self.pitch)),
            -distance * math.cos(math.radians(self.pitch)),
        )
        camera.look_at(self.pivot)

        # Apply initial rotation
        self.pivot.rotation_y = -self.yaw

        # Static underwater background that scales with orthographic zoom
        self.background = Entity(
            parent=camera,
            model="quad",
            texture=BACKGROUND_TEXTURE,
            color=color.white,
            unlit=True,
            double_sided=True,
            position=(0, 0, 100),
        )
        self._update_background_scale()

    def update(self):
        # Smooth yaw interpolation
        self.yaw += (self.target_yaw - self.yaw) * 0.15
        self.pivot.rotation_y = -self.yaw

        # Smooth pan interpolation
        self.pivot.position += (self.target_pivot_pos - self.pivot.position) * 0.1

        # Smooth zoom
        camera.fov += (self.target_zoom - camera.fov) * 0.1
        self._update_background_scale()

        # Left-click drag rotation
        if mouse.left:
            # Use mouse velocity for smooth rotation
            self.target_yaw += mouse.velocity[0] * self.rotation_sensitivity

        # Shift + mouse drag for panning
        # Simple screen-space panning: directly move the view along camera axes
        if held_keys["shift"]:
            if mouse.velocity[0] != 0 or mouse.velocity[1] != 0:
                # Scale by orthographic zoom level for consistent pan speed
                scale = camera.fov / 50
                self.target_pivot_pos += camera.right * mouse.velocity[0] * scale
                self.target_pivot_pos -= camera.up * mouse.velocity[1] * scale

    def input(self, key):
        if key == "middle mouse down" or key == "m":
            self.reset()

        elif key == "scroll up":
            if held_keys["shift"]:
                # Shift+scroll = pan forward/back
                forward = self.get_camera_forward()
                self.target_pivot_pos += forward * 2
            else:
                self.target_zoom = max(self.min_zoom, self.target_zoom - 1)

        elif key == "scroll down":
            if held_keys["shift"]:
                # Shift+scroll = pan forward/back
                forward = self.get_camera_forward()
                self.target_pivot_pos -= forward * 2
            else:
                self.target_zoom = min(self.max_zoom, self.target_zoom + 1)

    def reset(self):
        """Reset camera to default isometric position."""
        self.target_yaw = 225
        self.target_zoom = 24
        self.target_pivot_pos = Vec3(
            MAZE_WIDTH * TILE_SIZE / 2, 0, MAZE_HEIGHT * TILE_SIZE / 2
        )

    def _update_background_scale(self):
        aspect = (
            window.aspect_ratio
            if hasattr(window, "aspect_ratio")
            else window.size[0] / window.size[1]
        )
        size = camera.fov
        self.background.scale = (size * aspect, size)

    def get_camera_forward(self):
        """Get the forward direction relative to camera view (flattened to XZ plane)."""
        # The pivot's forward vector, but flattened (no Y component)
        forward = self.pivot.forward
        forward.y = 0
        if forward.length() > 0:
            forward = forward.normalized()
        return forward

    def get_camera_right(self):
        """Get the right direction relative to camera view (flattened to XZ plane)."""
        right = self.pivot.right
        right.y = 0
        if right.length() > 0:
            right = right.normalized()
        return right


# =============================================================================
# MAZE BUILDER
# =============================================================================
class MazeBuilder:
    """Builds the 3D underwater maze from the 2D layout."""

    def __init__(self):
        self.walls = []
        self.floor_tiles = []
        self.valid_positions = []
        self.wall_edges = []
        self.wall_decals = []
        self.decorations = []
        self.bubbles = []
        self.edge_positions = []
        self.interior_positions = []
        self.sparkles = []

    def _is_wall(self, col, row):
        return 0 <= row < MAZE_HEIGHT and 0 <= col < MAZE_WIDTH and MAZE[row][col] == 1

    def _is_edge_floor(self, col, row):
        if col in (0, MAZE_WIDTH - 1) or row in (0, MAZE_HEIGHT - 1):
            return True
        return (
            self._is_wall(col - 1, row)
            or self._is_wall(col + 1, row)
            or self._is_wall(col, row - 1)
            or self._is_wall(col, row + 1)
        )

    def _tile_center(self, col, row):
        return (col + 0.5) * TILE_SIZE, (row + 0.5) * TILE_SIZE

    def _get_wall_sprite(self, col, row):
        north = self._is_wall(col, row - 1)
        south = self._is_wall(col, row + 1)
        west = self._is_wall(col - 1, row)
        east = self._is_wall(col + 1, row)
        count = sum((north, south, west, east))

        if count == 4:
            return WALL_TOP_TEXTURES["plus"], 0
        if count == 3:
            if not south:
                rotation = 0
            elif not east:
                rotation = 90
            elif not north:
                rotation = 180
            else:
                rotation = 270
            return WALL_TOP_TEXTURES["t"], rotation
        if count == 2:
            if (north and south) or (east and west):
                rotation = 90 if north and south else 0
                return WALL_TOP_TEXTURES["straight"], rotation
            if north and east:
                rotation = 0
            elif east and south:
                rotation = 270
            elif south and west:
                rotation = 180
            else:
                rotation = 90
            return WALL_TOP_TEXTURES["corner"], rotation
        if count == 1:
            rotation = 90 if (north or south) else 0
            return WALL_TOP_TEXTURES["straight"], rotation
        return WALL_TOP_TEXTURES["plus"], 0

    def _add_wall_decal(self, col, row, x, z):
        texture, rotation = self._get_wall_sprite(col, row)
        decal = Entity(
            model="quad",
            texture=texture,
            rotation_x=90,
            rotation_y=rotation,
            position=(x, WALL_HEIGHT + 0.07, z),
            scale=(TILE_SIZE * 1.05, TILE_SIZE * 1.05),
            color=color.white,
            unlit=True,
            double_sided=True,
        )
        self.wall_decals.append(decal)

    def _spawn_upright_sprite(self, texture, x, z, width, height, y_offset=0.0):
        scale_factor = random.uniform(0.85, 1.15)
        sprite = Entity(
            model="quad",
            texture=texture,
            position=(x, height * scale_factor / 2 + y_offset, z),
            scale=(width * scale_factor, height * scale_factor),
            color=color.white,
            unlit=True,
            double_sided=True,
            billboard=True,
        )
        self.decorations.append(sprite)

    def _spawn_floor_sprite(self, texture, x, z, width, depth, y_offset=0.02):
        scale_factor = random.uniform(0.85, 1.15)
        sprite = Entity(
            model="quad",
            texture=texture,
            rotation_x=90,
            rotation_y=random.uniform(0, 360),
            position=(x, y_offset, z),
            scale=(width * scale_factor, depth * scale_factor),
            color=color.white,
            unlit=True,
            double_sided=True,
        )
        self.decorations.append(sprite)

    def _spawn_sparkle(self, x, z, y):
        scale = random.uniform(0.15, 0.25)
        sparkle = Entity(
            model="quad",
            texture=DECOR_TEXTURES["sparkle"],
            position=(x, y, z),
            scale=(scale, scale),
            color=color.rgba(255, 255, 255, 200),
            unlit=True,
            double_sided=True,
            billboard=True,
        )
        sparkle.animate_rotation_z(
            sparkle.rotation_z + random.choice([90, 180, 270]),
            duration=random.uniform(2.5, 4.5),
            loop=True,
            curve=curve.linear,
        )
        self.sparkles.append(sparkle)

    def build(self):
        """Create the 3D underwater maze matching reference art style."""
        # Create sandy ocean floor
        floor_scale_x = MAZE_WIDTH + 4
        floor_scale_z = MAZE_HEIGHT + 4
        floor = Entity(
            model="quad",
            scale=(floor_scale_x, floor_scale_z),
            rotation_x=90,  # Rotate quad to be horizontal
            position=(
                MAZE_WIDTH * TILE_SIZE / 2 - TILE_SIZE / 2,
                -0.1,
                MAZE_HEIGHT * TILE_SIZE / 2 - TILE_SIZE / 2,
            ),
            texture=FLOOR_TEXTURE,
            texture_scale=(floor_scale_x, floor_scale_z),
            color=color.white,
            unlit=True,
            double_sided=True,
        )
        self.floor_tiles.append(floor)

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
                        scale=(TILE_SIZE * 0.95, WALL_HEIGHT, TILE_SIZE * 0.95),
                        texture=WALL_TEXTURE,
                        texture_scale=(1, 1),
                        color=color.white,
                    )
                    self.walls.append(wall)

                    # Glowing cyan top edge
                    edge = Entity(
                        model="cube",
                        position=(x, WALL_HEIGHT + 0.03, z),
                        scale=(TILE_SIZE * 0.98, 0.06, TILE_SIZE * 0.98),
                        color=color.rgb(0, 220, 230),
                        unlit=True,
                    )
                    self.wall_edges.append(edge)

                    # Top decal based on wall neighbors
                    self._add_wall_decal(col, row, x, z)
                else:
                    # Track valid floor positions
                    self.valid_positions.append((col, row))
                    if self._is_edge_floor(col, row):
                        self.edge_positions.append((col, row))
                    else:
                        self.interior_positions.append((col, row))

        # Add coral decorations around the maze perimeter
        self._add_perimeter_decorations()

        # Add floor decorations (starfish, shells)
        self._add_floor_decorations()

        # Add floating bubbles
        self._create_bubble_particles()

        # Add water sparkles
        self._add_sparkles()

        return self.valid_positions

    def _add_perimeter_decorations(self):
        """Add coral and seaweed around the maze edges."""
        edge_decors = [
            (DECOR_TEXTURES["coral_pink_orange"], 1.4, 0.9),
            (DECOR_TEXTURES["seaweed_starfish"], 1.3, 0.9),
            (DECOR_TEXTURES["anemone_yellow_coral"], 1.0, 0.8),
            (DECOR_TEXTURES["coral_blue"], 0.9, 0.8),
        ]

        edge_pool = self.edge_positions[:]
        random.shuffle(edge_pool)
        edge_count = max(12, int(len(edge_pool) * 0.2))
        for col, row in edge_pool[:edge_count]:
            x, z = self._tile_center(col, row)
            texture, width, height = random.choice(edge_decors)
            self._spawn_upright_sprite(texture, x, z, width, height)

        # Extra decorations just outside the maze bounds
        outside_positions = []
        for col in range(-2, MAZE_WIDTH + 2, 2):
            outside_positions.append((col, -2))
            outside_positions.append((col, MAZE_HEIGHT + 1))
        for row in range(-1, MAZE_HEIGHT + 2, 2):
            outside_positions.append((-2, row))
            outside_positions.append((MAZE_WIDTH + 1, row))

        for col, row in random.sample(
            outside_positions, min(12, len(outside_positions))
        ):
            x, z = self._tile_center(col, row)
            texture, width, height = random.choice(edge_decors)
            self._spawn_upright_sprite(texture, x, z, width, height)

        # Place a decorative submarine near the maze edge
        sub_candidates = outside_positions or self.edge_positions
        if sub_candidates:
            sub_col, sub_row = random.choice(sub_candidates)
            x, z = self._tile_center(sub_col, sub_row)
            self._spawn_upright_sprite(
                DECOR_TEXTURES["submarine"], x, z, 1.4, 1.0, 0.05
            )

    def _add_floor_decorations(self):
        """Add starfish, shells scattered on floor."""
        floor_candidates = self.interior_positions or self.valid_positions
        random.shuffle(floor_candidates)

        floor_count = max(18, int(len(floor_candidates) * 0.2))
        for col, row in floor_candidates[:floor_count]:
            x, z = self._tile_center(col, row)
            if random.random() < 0.6:
                self._spawn_floor_sprite(DECOR_TEXTURES["shell"], x, z, 0.5, 0.4)
            else:
                self._spawn_floor_sprite(DECOR_TEXTURES["rock"], x, z, 0.5, 0.35)

    def _create_bubble_particles(self):
        """Create floating bubble particles for atmosphere."""
        for _ in range(28):
            x = random.uniform(-2, MAZE_WIDTH + 2) * TILE_SIZE
            z = random.uniform(-2, MAZE_HEIGHT + 2) * TILE_SIZE
            texture = random.choice(
                [DECOR_TEXTURES["bubble_large"], DECOR_TEXTURES["bubble_small"]]
            )
            scale = random.uniform(0.25, 0.45)

            bubble = Entity(
                model="quad",
                texture=texture,
                position=(x, random.uniform(0.5, 2.5), z),
                scale=(scale, scale),
                color=color.rgba(200, 255, 255, 160),
                unlit=True,
                double_sided=True,
                billboard=True,
            )
            bubble.animate_y(
                bubble.y + random.uniform(2.5, 4.5),
                duration=random.uniform(5, 9),
                loop=True,
                curve=curve.linear,
            )
            self.bubbles.append(bubble)

    def _add_sparkles(self):
        if not self.valid_positions:
            return
        sparkle_count = max(10, int(len(self.valid_positions) * 0.12))
        for col, row in random.sample(
            self.valid_positions, min(sparkle_count, len(self.valid_positions))
        ):
            x, z = self._tile_center(col, row)
            x += random.uniform(-0.2, 0.2)
            z += random.uniform(-0.2, 0.2)
            self._spawn_sparkle(x, z, random.uniform(0.6, 1.6))


# =============================================================================
# PLAYER
# =============================================================================
class Player(Entity):
    """Player entity - Cute Submarine."""

    def __init__(self, grid_x, grid_y, **kwargs):
        super().__init__(
            model="cube",
            scale=(0.7, 0.5, 0.5),
            position=(grid_x * TILE_SIZE, 0.3, grid_y * TILE_SIZE),
            color=NEON_YELLOW,  # Yellow submarine!
            **kwargs,
        )

        self.grid_x = grid_x
        self.grid_y = grid_y
        self.speed = 0.08
        self.direction = (1, 0)  # Facing right
        self.shoot_cooldown = 0

        self.score = 0
        self.lives = 3

        # Submarine cabin/window
        self.visor = Entity(
            parent=self,
            model="sphere",
            scale=(0.5, 0.6, 0.4),
            position=(0, 0.1, 0.2),
            color=color.rgb(150, 220, 255),  # Light blue window
        )

        # Periscope
        self.periscope = Entity(
            parent=self,
            model="cube",
            scale=(0.1, 0.3, 0.1),
            position=(0, 0.4, 0),
            color=color.rgb(200, 180, 80),
        )

        # Propeller area
        self.propeller = Entity(
            parent=self,
            model="cube",
            scale=(0.2, 0.3, 0.15),
            position=(0, 0, -0.35),
            color=color.rgb(200, 180, 80),
        )

    def move(self, dx, dy):
        """Move with collision detection."""
        if dx != 0 or dy != 0:
            self.direction = (dx, dy)

            # Face movement direction
            if dx > 0:
                self.rotation_y = -90
            elif dx < 0:
                self.rotation_y = 90
            elif dy > 0:
                self.rotation_y = 180
            elif dy < 0:
                self.rotation_y = 0

        new_x = self.grid_x + dx * self.speed
        new_y = self.grid_y + dy * self.speed

        # Check collision
        test_x = int(new_x + 0.5)
        test_y = int(new_y + 0.5)

        # Horizontal movement
        if 0 <= test_x < MAZE_WIDTH:
            if MAZE[int(self.grid_y + 0.5)][test_x] == 0:
                self.grid_x = new_x

        # Vertical movement
        if 0 <= test_y < MAZE_HEIGHT:
            if MAZE[test_y][int(self.grid_x + 0.5)] == 0:
                self.grid_y = new_y

        # Clamp to maze bounds
        self.grid_x = max(0.5, min(MAZE_WIDTH - 1.5, self.grid_x))
        self.grid_y = max(0.5, min(MAZE_HEIGHT - 1.5, self.grid_y))

        # Update 3D position
        self.x = self.grid_x * TILE_SIZE
        self.z = self.grid_y * TILE_SIZE

    def update(self):
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= time.dt * 60  # Convert to frames


# =============================================================================
# BULLET
# =============================================================================
class Bullet(Entity):
    """Plasma bullet projectile."""

    def __init__(self, grid_x, grid_y, direction, is_player=True, **kwargs):
        bullet_color = NEON_YELLOW if is_player else NEON_RED

        super().__init__(
            model="sphere",
            scale=0.15,
            position=(grid_x * TILE_SIZE, 0.4, grid_y * TILE_SIZE),
            color=bullet_color,
            unlit=True,
            **kwargs,
        )

        self.grid_x = grid_x
        self.grid_y = grid_y
        self.direction = direction
        self.speed = 0.25
        self.is_player = is_player
        self.lifetime = 3

        # Glow effect
        self.glow = Entity(
            parent=self,
            model="sphere",
            scale=2,
            color=(
                color.rgba(
                    bullet_color.r * 255, bullet_color.g * 255, bullet_color.b * 255, 50
                )
                if is_player
                else color.rgba(255, 50, 50, 50)
            ),
            unlit=True,
        )

    def update(self):
        self.lifetime -= time.dt

        if self.lifetime <= 0:
            destroy(self)
            return

        # Move bullet
        self.grid_x += self.direction[0] * self.speed
        self.grid_y += self.direction[1] * self.speed

        # Update 3D position
        self.x = self.grid_x * TILE_SIZE
        self.z = self.grid_y * TILE_SIZE

        # Check wall collision
        test_x = int(self.grid_x + 0.5)
        test_y = int(self.grid_y + 0.5)

        if (
            test_x < 0
            or test_x >= MAZE_WIDTH
            or test_y < 0
            or test_y >= MAZE_HEIGHT
            or MAZE[test_y][test_x] == 1
        ):
            self._spawn_impact()
            destroy(self)

    def _spawn_impact(self):
        """Create impact particles."""
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
                    random.uniform(-0.5, 0.5),
                    random.uniform(0, 0.5),
                    random.uniform(-0.5, 0.5),
                ),
                duration=0.3,
            )
            destroy(particle, delay=0.3)


# =============================================================================
# ENEMY
# =============================================================================
class Enemy(Entity):
    """Enemy entity with type-specific behavior."""

    ENEMY_COLORS = {
        "burwor": NEON_BLUE,
        "garwor": NEON_ORANGE,
        "thorwor": NEON_RED,
        "worluk": NEON_GREEN,
        "wizard": NEON_PURPLE,
    }

    ENEMY_SPEEDS = {
        "burwor": 0.03,
        "garwor": 0.04,
        "thorwor": 0.05,
        "worluk": 0.06,
        "wizard": 0.04,
    }

    ENEMY_POINTS = {
        "burwor": 100,
        "garwor": 200,
        "thorwor": 500,
        "worluk": 1000,
        "wizard": 2500,
    }

    def __init__(self, grid_x, grid_y, enemy_type="burwor", **kwargs):
        self.enemy_type = enemy_type
        enemy_color = self.ENEMY_COLORS.get(enemy_type, NEON_BLUE)

        super().__init__(
            model="cube",
            scale=(0.5, 0.7, 0.5),
            position=(grid_x * TILE_SIZE, 0.35, grid_y * TILE_SIZE),
            color=enemy_color,
            **kwargs,
        )

        self.grid_x = grid_x
        self.grid_y = grid_y
        self.speed = self.ENEMY_SPEEDS.get(enemy_type, 0.03)
        self.points = self.ENEMY_POINTS.get(enemy_type, 100)
        self.direction = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        self.move_timer = 0
        self.visible = True
        self.health = 3 if enemy_type == "wizard" else 1

        # Visual elements
        self._create_visuals(enemy_color)

    def _create_visuals(self, base_color):
        """Create enemy-specific visual elements."""
        # Eyes
        eye_color = NEON_RED if self.enemy_type != "wizard" else NEON_CYAN

        self.left_eye = Entity(
            parent=self,
            model="sphere",
            scale=0.15,
            position=(-0.15, 0.2, 0.25),
            color=eye_color,
            unlit=True,
        )

        self.right_eye = Entity(
            parent=self,
            model="sphere",
            scale=0.15,
            position=(0.15, 0.2, 0.25),
            color=eye_color,
            unlit=True,
        )

        # Type-specific features
        if self.enemy_type == "thorwor":
            # Stinger tail
            self.tail = Entity(
                parent=self,
                model="cube",
                scale=(0.1, 0.1, 0.4),
                position=(0, 0.4, -0.3),
                rotation=(30, 0, 0),
                color=NEON_YELLOW,
            )

        elif self.enemy_type == "wizard":
            # Staff
            self.staff = Entity(
                parent=self,
                model="cube",
                scale=(0.08, 0.8, 0.08),
                position=(0.35, 0, 0),
                color=NEON_PURPLE,
            )
            # Orb
            self.orb = Entity(
                parent=self,
                model="sphere",
                scale=0.12,
                position=(0.35, 0.45, 0),
                color=NEON_CYAN,
                unlit=True,
            )

    def update(self):
        # Animation
        anim_time = time.time()
        eye_pulse = 1 + math.sin(anim_time * 5) * 0.2
        self.left_eye.scale = Vec3(0.15 * eye_pulse, 0.15 * eye_pulse, 0.15 * eye_pulse)
        self.right_eye.scale = Vec3(
            0.15 * eye_pulse, 0.15 * eye_pulse, 0.15 * eye_pulse
        )

        # Garwor cloaking
        if self.enemy_type == "garwor":
            if random.random() < 0.003:
                self.visible = not self.visible
                self.alpha = 0.2 if not self.visible else 1

        # Wizard orb animation
        if self.enemy_type == "wizard" and hasattr(self, "orb"):
            self.orb.scale = 0.12 + math.sin(anim_time * 4) * 0.03

        # AI Movement
        self.move_timer += time.dt

        if self.move_timer > 0.5:
            self.move_timer = 0
            if random.random() < 0.3:
                self.direction = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])

        # Move
        new_x = self.grid_x + self.direction[0] * self.speed
        new_y = self.grid_y + self.direction[1] * self.speed

        # Check collision
        test_x = int(new_x + 0.5)
        test_y = int(new_y + 0.5)

        can_move = True
        if test_x < 0 or test_x >= MAZE_WIDTH or test_y < 0 or test_y >= MAZE_HEIGHT:
            can_move = False
        elif MAZE[test_y][test_x] == 1:
            can_move = False

        if can_move:
            self.grid_x = new_x
            self.grid_y = new_y
        else:
            # Bounce
            self.direction = (-self.direction[0], -self.direction[1])

        # Update 3D position
        self.x = self.grid_x * TILE_SIZE
        self.z = self.grid_y * TILE_SIZE

        # Face movement direction
        if self.direction[0] > 0:
            self.rotation_y = -90
        elif self.direction[0] < 0:
            self.rotation_y = 90
        elif self.direction[1] > 0:
            self.rotation_y = 180
        elif self.direction[1] < 0:
            self.rotation_y = 0

    def take_damage(self):
        """Handle taking damage. Returns True if enemy dies."""
        self.health -= 1

        # Flash white
        original_color = self.color
        self.color = color.white
        invoke(setattr, self, "color", original_color, delay=0.1)

        return self.health <= 0

    def die(self):
        """Handle death with particles."""
        for _ in range(15):
            particle = Entity(
                model="sphere",
                scale=0.1,
                position=self.position,
                color=self.color,
                unlit=True,
            )
            particle.animate_position(
                self.position
                + Vec3(
                    random.uniform(-1, 1), random.uniform(0, 1.5), random.uniform(-1, 1)
                ),
                duration=0.5,
                curve=curve.out_expo,
            )
            particle.animate_scale(0, duration=0.5)
            destroy(particle, delay=0.5)

        destroy(self)


# =============================================================================
# HUD
# =============================================================================
class HUD(Entity):
    """Heads-up display."""

    def __init__(self):
        super().__init__()

        # Score
        self.score_text = Text(
            text="SCORE: 0",
            position=(-0.85, 0.45),
            scale=1.5,
            color=NEON_YELLOW,
        )

        # Lives
        self.lives_text = Text(
            text="LIVES: 3",
            position=(-0.85, 0.40),
            scale=1.5,
            color=NEON_GREEN,
        )

        # Enemies
        self.enemies_text = Text(
            text="ENEMIES: 0",
            position=(0.55, 0.45),
            scale=1.5,
            color=NEON_RED,
        )

        # Phase
        self.phase_text = Text(
            text="PHASE: NORMAL",
            position=(0.55, 0.40),
            scale=1.5,
            color=NEON_PURPLE,
        )

        # Camera info
        self.camera_text = Text(
            text="VIEW: 45° | Drag to rotate, scroll to zoom",
            position=(0, -0.45),
            origin=(0, 0),
            scale=1,
            color=NEON_CYAN,
        )

        # Message
        self.message_text = Text(
            text="",
            position=(0, 0.3),
            origin=(0, 0),
            scale=2,
            color=NEON_CYAN,
        )
        self.message_timer = 0

    def update_score(self, score):
        self.score_text.text = f"SCORE: {score}"

    def update_lives(self, lives):
        self.lives_text.text = f"LIVES: {lives}"
        self.lives_text.color = NEON_GREEN if lives > 1 else NEON_RED

    def update_enemies(self, count):
        self.enemies_text.text = f"ENEMIES: {count}"

    def update_phase(self, phase):
        self.phase_text.text = f"PHASE: {phase.upper()}"

    def update_camera(self, yaw, zoom):
        yaw_display = int(yaw % 360)
        self.camera_text.text = f"YAW: {yaw_display}° | Drag=rotate | Scroll=zoom | Shift+Drag=pan | M=reset"

    def show_message(self, text, duration=2):
        self.message_text.text = text
        self.message_timer = duration

    def update(self):
        if self.message_timer > 0:
            self.message_timer -= time.dt
            if self.message_timer <= 0:
                self.message_text.text = ""


# =============================================================================
# GAME MANAGER
# =============================================================================
class GameManager(Entity):
    """Manages game state and logic."""

    def __init__(self):
        super().__init__()

        self.game_over = False
        self.victory = False
        self.phase = "normal"

        # Build maze
        self.maze_builder = MazeBuilder()
        self.valid_positions = self.maze_builder.build()

        # Setup camera
        self.iso_camera = IsometricCamera()

        # Find spawn position
        spawn_pos = None
        for pos in reversed(self.valid_positions):
            if pos[1] > MAZE_HEIGHT - 4:
                spawn_pos = pos
                break
        if not spawn_pos:
            spawn_pos = self.valid_positions[-1]

        self.player_spawn = spawn_pos
        self.player = Player(spawn_pos[0] + 0.5, spawn_pos[1] + 0.5)

        # Enemies and bullets
        self.enemies = []
        self.bullets = []

        # Create HUD
        self.hud = HUD()

        # Spawn enemies
        self.spawn_enemies()

        # Initial message
        self.hud.show_message("WELCOME TO THE DUNGEON OF WOR!", 3)

        # Setup lighting
        self.setup_lighting()

    def setup_lighting(self):
        """Setup atmospheric lighting."""
        # Ambient light
        AmbientLight(color=color.rgba(80, 80, 100, 255))

        # Directional light from above
        DirectionalLight(
            y=10,
            rotation=(45, 45, 0),
            color=color.rgb(150, 150, 200),
        )

    def spawn_enemies(self):
        """Spawn enemies for current phase."""
        # Clear existing enemies
        for enemy in self.enemies:
            if enemy:
                destroy(enemy)
        self.enemies = []

        if self.phase == "normal":
            types = ["burwor"] * 3 + ["garwor"] * 2 + ["thorwor"] * 1
            for enemy_type in types:
                pos = random.choice(self.valid_positions)
                # Not too close to player
                while (
                    abs(pos[0] - self.player_spawn[0]) < 5
                    and abs(pos[1] - self.player_spawn[1]) < 5
                ):
                    pos = random.choice(self.valid_positions)
                enemy = Enemy(pos[0] + 0.5, pos[1] + 0.5, enemy_type)
                self.enemies.append(enemy)

        elif self.phase == "worluk":
            pos = random.choice(self.valid_positions)
            enemy = Enemy(pos[0] + 0.5, pos[1] + 0.5, "worluk")
            self.enemies.append(enemy)
            self.hud.show_message("THE WORLUK APPEARS!", 3)

        elif self.phase == "wizard":
            pos = random.choice(self.valid_positions)
            enemy = Enemy(pos[0] + 0.5, pos[1] + 0.5, "wizard")
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

        # Pass camera controls
        self.iso_camera.input(key)

        # Shooting
        if key == "space" and self.player.shoot_cooldown <= 0:
            bullet = Bullet(
                self.player.grid_x,
                self.player.grid_y,
                self.player.direction,
                is_player=True,
            )
            self.bullets.append(bullet)
            self.player.shoot_cooldown = 15

    def update(self):
        if self.game_over or self.victory:
            return

        # Handle player input - CAMERA-RELATIVE movement
        # Get raw input direction
        input_x, input_z = 0, 0
        if held_keys["left"] or held_keys["a"]:
            input_x = -1
        elif held_keys["right"] or held_keys["d"]:
            input_x = 1
        if held_keys["up"] or held_keys["w"]:
            input_z = 1  # Forward relative to camera
        elif held_keys["down"] or held_keys["s"]:
            input_z = -1  # Backward relative to camera

        # Transform input to world-space using camera orientation
        dx, dy = 0, 0
        if input_x != 0 or input_z != 0:
            cam_forward = self.iso_camera.get_camera_forward()
            cam_right = self.iso_camera.get_camera_right()

            # Calculate world-space movement direction
            world_dir_x = cam_forward.x * input_z + cam_right.x * input_x
            world_dir_z = cam_forward.z * input_z + cam_right.z * input_x

            # Convert to grid movement (dx, dy in maze coords)
            # In our maze, X is horizontal, Z is vertical (mapped to dy)
            if abs(world_dir_x) > abs(world_dir_z):
                dx = 1 if world_dir_x > 0 else -1
            elif abs(world_dir_z) > 0:
                dy = 1 if world_dir_z > 0 else -1

        self.player.move(dx, dy)

        # Update HUD
        self.hud.update_score(self.player.score)
        self.hud.update_lives(self.player.lives)
        self.hud.update_phase(self.phase)
        self.hud.update_enemies(len(self.enemies))
        self.hud.update_camera(self.iso_camera.yaw, camera.fov)

        # Check bullet-enemy collisions
        for bullet in self.bullets[:]:
            if not bullet or not hasattr(bullet, "grid_x"):
                if bullet in self.bullets:
                    self.bullets.remove(bullet)
                continue

            if bullet.is_player:
                for enemy in self.enemies[:]:
                    if not enemy:
                        continue
                    dist = math.sqrt(
                        (bullet.grid_x - enemy.grid_x) ** 2
                        + (bullet.grid_y - enemy.grid_y) ** 2
                    )
                    if dist < 0.8:
                        if enemy.take_damage():
                            self.player.score += enemy.points
                            enemy.die()
                            self.enemies.remove(enemy)
                            self.hud.update_enemies(len(self.enemies))
                        destroy(bullet)
                        if bullet in self.bullets:
                            self.bullets.remove(bullet)
                        break

        # Check player-enemy collision
        for enemy in self.enemies:
            if not enemy:
                continue
            dist = math.sqrt(
                (self.player.grid_x - enemy.grid_x) ** 2
                + (self.player.grid_y - enemy.grid_y) ** 2
            )
            if dist < 0.8:
                self.player_hit()
                break

        # Phase progression
        if len(self.enemies) == 0:
            if self.phase == "normal":
                self.phase = "worluk"
                invoke(self.spawn_enemies, delay=1)
            elif self.phase == "worluk":
                self.phase = "wizard"
                invoke(self.spawn_enemies, delay=1)
            elif self.phase == "wizard":
                self.victory = True
                self.show_end_screen()

    def player_hit(self):
        """Handle player getting hit."""
        self.player.lives -= 1
        self.hud.update_lives(self.player.lives)

        # Flash effect
        flash = Entity(
            parent=camera.ui,
            model="quad",
            scale=2,
            color=color.rgba(255, 0, 0, 100),
            z=-1,
        )
        flash.animate_color(color.rgba(255, 0, 0, 0), duration=0.5)
        destroy(flash, delay=0.5)

        if self.player.lives <= 0:
            self.game_over = True
            self.show_end_screen()
        else:
            # Respawn
            self.player.grid_x = self.player_spawn[0] + 0.5
            self.player.grid_y = self.player_spawn[1] + 0.5
            self.player.x = self.player.grid_x * TILE_SIZE
            self.player.z = self.player.grid_y * TILE_SIZE
            self.hud.show_message("PREPARE YOURSELF!", 2)

    def show_end_screen(self):
        """Show game over or victory screen."""
        # Overlay
        overlay = Entity(
            parent=camera.ui,
            model="quad",
            scale=2,
            color=color.rgba(0, 0, 0, 150),
            z=-0.5,
        )

        text = "GAME OVER" if self.game_over else "VICTORY!"
        text_color = NEON_RED if self.game_over else NEON_GREEN

        Text(
            text=text,
            position=(0, 0.1),
            origin=(0, 0),
            scale=3,
            color=text_color,
        )

        Text(
            text=f"Final Score: {self.player.score}",
            position=(0, -0.05),
            origin=(0, 0),
            scale=1.5,
            color=color.white,
        )

        Text(
            text="Press R to Restart",
            position=(0, -0.15),
            origin=(0, 0),
            scale=1.2,
            color=NEON_CYAN,
        )


# =============================================================================
# MAIN
# =============================================================================
if __name__ == "__main__":
    # Set window properties
    window.title = "Wizard of Wor - Underwater Edition"
    window.borderless = False
    window.fullscreen = False
    window.exit_button.visible = False
    window.fps_counter.enabled = True
    window.color = color.rgb(15, 35, 55)  # Deep ocean background

    # Create game
    game = GameManager()

    # Instructions
    print("\n" + "=" * 50)
    print("WIZARD OF WOR - ISOMETRIC 2.5D (Ursina Engine)")
    print("=" * 50)
    print("Controls:")
    print("  Arrow Keys / WASD - Move (camera-relative)")
    print("  Space - Shoot")
    print("  Mouse Drag - Rotate camera")
    print("  Shift + Drag - Pan camera (trackpad two-finger)")
    print("  Mouse Wheel - Zoom in/out")
    print("  M / Middle Click - Reset camera")
    print("  R - Restart (after game over)")
    print("  ESC - Exit")
    print("=" * 50 + "\n")

    app.run()
