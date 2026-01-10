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
import os
import random
import traceback

from ursina import *


# =============================================================================
# SOUND MANAGER
# =============================================================================
class SoundManager:
    """Manages all game sounds - matching original Wizard of Wor."""

    def __init__(self):
        self.sound_paths = {}
        self.music = None
        self.music_volume = 0.25
        self.sfx_volume = 0.5
        self.current_loop = 1
        self.beat_timer = 0
        self.beat_interval = 0.5  # Seconds between beats
        self.last_radar_time = 0
        self.load_sounds()

    def load_sounds(self):
        """Load all sound effect paths."""
        self.sound_paths = {
            # Main game sounds
            "player_fire": "assets/sounds/player-fire.wav",
            "enemy_fire": "assets/sounds/enemy-fire.wav",
            "enemy_dead": "assets/sounds/enemy-dead.wav",
            "player_dead": "assets/sounds/player-dead.wav",
            "worluk": "assets/sounds/worluk.wav",
            "worluk_dead": "assets/sounds/worluk-dead.wav",
            "worluk_escape": "assets/sounds/worluk-escape.wav",
            "wizard_dead": "assets/sounds/wizard-dead.wav",
            "wizard_escape": "assets/sounds/wizard-escape.wav",
            "enemy_visible": "assets/sounds/enemy-visible.wav",
            "player_enters": "assets/sounds/player-enters.wav",
            "get_ready": "assets/sounds/getready.wav",
            "game_over": "assets/sounds/gameover.wav",
            "maze_exit": "assets/sounds/maze-exit.wav",
            "double_score": "assets/sounds/doublescore.wav",
            # Background loops (tempo increases with fewer enemies)
            "loop01": "assets/sounds/loop01.wav",
            "loop02": "assets/sounds/loop02.wav",
            "loop03": "assets/sounds/loop03.wav",
            "loop04": "assets/sounds/loop04.wav",
            "loop05": "assets/sounds/loop05.wav",
            # Old/classic sounds (fallbacks)
            "radar_blip": "assets/sounds/old/radar_blip.wav",
            "walking_beat": "assets/sounds/old/walking_beat.wav",
            "walking_beat_fast": "assets/sounds/old/walking_beat_fast.wav",
            "laugh": "assets/sounds/old/laugh.wav",
            "voice_wizard": "assets/sounds/old/voice_wizard.wav",
            "voice_welcome": "assets/sounds/old/voice_welcome.wav",
            "voice_prepare": "assets/sounds/old/voice_prepare.wav",
            "voice_game_over": "assets/sounds/old/voice_game_over.wav",
            "wizard_teleport": "assets/sounds/old/wizard_teleport.wav",
        }

        # Verify files exist
        for name, path in self.sound_paths.items():
            if not os.path.exists(path):
                print(f"Warning: Sound file not found: {path}")

    def play(self, name, volume=None):
        """Play a sound effect (creates new Audio instance each time)."""
        if name in self.sound_paths and os.path.exists(self.sound_paths[name]):
            try:
                vol = volume if volume is not None else self.sfx_volume
                Audio(self.sound_paths[name], volume=vol, autoplay=True)
            except Exception as e:
                print(f"Warning: Could not play sound {name}: {e}")

    def play_music(self, name, volume=None):
        """Play background music (loops)."""
        if self.music:
            self.music.stop()
            self.music = None

        if name in self.sound_paths and os.path.exists(self.sound_paths[name]):
            try:
                vol = volume if volume is not None else self.music_volume
                self.music = Audio(
                    self.sound_paths[name], volume=vol, loop=True, autoplay=True
                )
            except Exception as e:
                print(f"Warning: Could not play music {name}: {e}")

    def stop_music(self):
        """Stop background music."""
        if self.music:
            self.music.stop()
            self.music = None

    def update_music_tempo(self, enemy_count, max_enemies=6):
        """Change background loop based on remaining enemies (like original WoW)."""
        # Original Wizard of Wor speeds up music as enemies decrease
        if enemy_count <= 0:
            return

        # Calculate which loop to play (1-5, higher = faster tempo)
        if enemy_count >= max_enemies:
            new_loop = 1
        elif enemy_count >= max_enemies * 0.7:
            new_loop = 2
        elif enemy_count >= max_enemies * 0.5:
            new_loop = 3
        elif enemy_count >= max_enemies * 0.3:
            new_loop = 4
        else:
            new_loop = 5

        if new_loop != self.current_loop:
            self.current_loop = new_loop
            self.play_music(f"loop0{new_loop}", self.music_volume)

    def play_radar_blip(self, distance, current_time):
        """Play radar blip based on enemy distance (like original WoW radar)."""
        # Only blip if enough time has passed (avoid spam)
        if current_time - self.last_radar_time < 0.3:
            return

        # Closer enemies = louder blip
        if distance < 3:
            self.play("radar_blip", 0.4)
            self.last_radar_time = current_time
        elif distance < 5:
            self.play("radar_blip", 0.25)
            self.last_radar_time = current_time
        elif distance < 8:
            self.play("radar_blip", 0.1)
            self.last_radar_time = current_time


# Global sound manager instance (created after app init)
sound_manager = None

# =============================================================================
# MAZE LAYOUT
# =============================================================================
MAZE_LAYOUT = [
    "#####################",
    "#.#####..###..#####.#",
    "#..##.#.......#.##..#",
    "#.....#.##.##.#.....#",
    "#...#...........#...#",
    "#...#..#######..#...#",
    "#...####.....####...#",
    ".......#.....#.......",
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
TILE_SIZE = 1.0  # Size of each tile in 3D units
WALL_HEIGHT = 0.8
WALL_THICKNESS = 1.2  # Visual wall thickness to tighten corridors
WALL_TOP_SCALE = TILE_SIZE * WALL_THICKNESS * 1.02

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

# Texture assets directory
ASSET_DIR = "assets/images/underwater_assets"
FLOOR_TEXTURE_PATH = f"{ASSET_DIR}/floor_tile.png"
WALL_TEXTURE_PATH = f"{ASSET_DIR}/wall_tile_base.png"
BACKGROUND_TEXTURE_PATH = f"{ASSET_DIR}/background.png"
SEA_CREATURE_DIR = "assets/images/sea_creatures"
PLAYER_TEXTURE_PATH = "assets/images/shapshique.png"

WALL_TOP_TEXTURE_PATHS = {
    "plus": f"{ASSET_DIR}/wall_plus.png",
    "t": f"{ASSET_DIR}/wall_t.png",
    "corner": f"{ASSET_DIR}/wall_corner.png",
    "straight": f"{ASSET_DIR}/wall_straight.png",
}
DECOR_TEXTURE_PATHS = {
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
SMALL_FISH_TEXTURE_PATHS = [
    f"{SEA_CREATURE_DIR}/small_fish_1.png",
    f"{SEA_CREATURE_DIR}/small_fish_2.png",
    f"{SEA_CREATURE_DIR}/small_fish_3.png",
    f"{SEA_CREATURE_DIR}/small_fish_4.png",
    f"{SEA_CREATURE_DIR}/small_fish_5.png",
    f"{SEA_CREATURE_DIR}/small_fish_6.png",
]

# =============================================================================
# GAME APPLICATION
# =============================================================================
app = Ursina(
    title="Shapshique of Wor - Isometric 2.5D",
    borderless=False,
    fullscreen=False,
    development_mode=True,
    vsync=True,
    use_ingame_console=True,
)


def load_art_texture(path, clamp=True):
    texture = load_texture(path)
    if texture:
        texture.filtering = None
        texture.wrap_mode = "clamp" if clamp else "repeat"
    return texture


TEXTURES = {
    "floor": load_art_texture(FLOOR_TEXTURE_PATH, clamp=False),
    "wall": load_art_texture(WALL_TEXTURE_PATH, clamp=True),
    "background": load_art_texture(BACKGROUND_TEXTURE_PATH, clamp=True),
}
for key, path in WALL_TOP_TEXTURE_PATHS.items():
    TEXTURES[f"wall_{key}"] = load_art_texture(path, clamp=True)
for key, path in DECOR_TEXTURE_PATHS.items():
    TEXTURES[key] = load_art_texture(path, clamp=True)
for idx, path in enumerate(SMALL_FISH_TEXTURE_PATHS, start=1):
    TEXTURES[f"small_fish_{idx}"] = load_art_texture(path, clamp=True)
TEXTURES["player"] = load_art_texture(PLAYER_TEXTURE_PATH, clamp=True)

WALL_TOP_TEXTURES = {
    "plus": TEXTURES["wall_plus"],
    "t": TEXTURES["wall_t"],
    "corner": TEXTURES["wall_corner"],
    "straight": TEXTURES["wall_straight"],
}
DECOR_TEXTURES = {
    "coral_pink_orange": TEXTURES["coral_pink_orange"],
    "seaweed_starfish": TEXTURES["seaweed_starfish"],
    "anemone_yellow_coral": TEXTURES["anemone_yellow_coral"],
    "coral_blue": TEXTURES["coral_blue"],
    "shell": TEXTURES["shell"],
    "rock": TEXTURES["rock"],
    "sparkle": TEXTURES["sparkle"],
    "submarine": TEXTURES["submarine"],
    "bubble_large": TEXTURES["bubble_large"],
    "bubble_small": TEXTURES["bubble_small"],
}
SMALL_FISH_TEXTURES = [
    TEXTURES[f"small_fish_{idx}"] for idx in range(1, len(SMALL_FISH_TEXTURE_PATHS) + 1)
]


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
        self.min_zoom = 8  # Allow closer zoom for detail view
        self.max_zoom = 45
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
            texture=TEXTURES["background"],
            color=color.white,
            unlit=True,
            double_sided=True,
            position=(0, 0, 100),
        )
        self._update_background_scale()

    def update(self):
        try:
            # Smooth yaw interpolation
            self.yaw += (self.target_yaw - self.yaw) * 0.15
            self.pivot.rotation_y = -self.yaw

            # Smooth pan interpolation
            self.pivot.position += (self.target_pivot_pos - self.pivot.position) * 0.1

            # Smooth zoom
            camera.fov += (self.target_zoom - camera.fov) * 0.1
            if not math.isfinite(camera.fov):
                camera.fov = self.target_zoom
            camera.fov = clamp(camera.fov, self.min_zoom, self.max_zoom)
            self._update_background_scale()

            # Left-click drag rotation
            if mouse.left and not held_keys["shift"]:
                # Use mouse velocity for smooth rotation
                self.target_yaw += mouse.velocity[0] * self.rotation_sensitivity

            # Shift + mouse move for panning (pure 2D screen-space like dragging paper)
            if held_keys["shift"]:
                if mouse.velocity[0] != 0 or mouse.velocity[1] != 0:
                    if not (
                        math.isfinite(mouse.velocity[0])
                        and math.isfinite(mouse.velocity[1])
                    ):
                        return
                    # Scale by orthographic zoom level for consistent pan speed
                    pan_scale = camera.fov * 0.8

                    # Use camera's world-space right and up vectors for true screen-space pan
                    # This moves the pivot opposite to mouse direction (drag-to-pan feel)
                    cam_right = camera.right
                    cam_up = camera.up

                    # Mouse X -> pan horizontally on screen
                    # Mouse Y -> pan vertically on screen
                    self.target_pivot_pos -= cam_right * mouse.velocity[0] * pan_scale
                    self.target_pivot_pos -= cam_up * mouse.velocity[1] * pan_scale

                    # Keep pivot Y at ground level (don't let it go underground or too high)
                    self.target_pivot_pos.y = 0

                    # Clamp pan to reasonable bounds around the maze
                    maze_center_x = MAZE_WIDTH * TILE_SIZE / 2
                    maze_center_z = MAZE_HEIGHT * TILE_SIZE / 2
                    max_pan = 20  # Max distance from maze center
                    self.target_pivot_pos.x = clamp(
                        self.target_pivot_pos.x,
                        maze_center_x - max_pan,
                        maze_center_x + max_pan,
                    )
                    self.target_pivot_pos.z = clamp(
                        self.target_pivot_pos.z,
                        maze_center_z - max_pan,
                        maze_center_z + max_pan,
                    )
        except Exception:
            print("IsometricCamera.update error; resetting camera.")
            traceback.print_exc()
            self.reset()

    def input(self, key):
        try:
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
        except Exception:
            print(f"IsometricCamera.input error ({key}); resetting camera.")
            traceback.print_exc()
            self.reset()

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
        if not math.isfinite(aspect) or aspect <= 0:
            return
        size = camera.fov
        if not math.isfinite(size) or size <= 0:
            return
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
class Bubble(Entity):
    """Smoothly drifting bubble sprite with wraparound."""

    def __init__(self, texture, bounds, y_bounds):
        super().__init__(
            model="quad",
            texture=texture,
            color=color.white,  # Use white to preserve PNG alpha/gradient
            unlit=True,
            double_sided=True,
            billboard=True,
        )
        self.x_min, self.x_max, self.z_min, self.z_max = bounds
        self.y_min, self.y_max = y_bounds
        self._reset(random_y=True)

    def _reset(self, random_y=False):
        self.base_x = random.uniform(self.x_min, self.x_max)
        self.base_z = random.uniform(self.z_min, self.z_max)
        self.drift_phase = random.uniform(0, math.tau)
        self.drift_speed = random.uniform(0.4, 0.9)
        self.drift_radius = random.uniform(0.05, 0.18)
        self.speed = random.uniform(0.18, 0.35)
        scale = random.uniform(0.25, 0.45)
        self.scale = (scale, scale)
        self.y = random.uniform(self.y_min, self.y_max) if random_y else self.y_min

    def update(self):
        self.y += self.speed * time.dt
        if self.y > self.y_max:
            self._reset()

        t = (self.y - self.y_min) / (self.y_max - self.y_min)
        fade = min(t / 0.15, (1 - t) / 0.15, 1.0)
        self.alpha = 0.15 + 0.85 * fade

        angle = time.time() * self.drift_speed + self.drift_phase
        self.x = self.base_x + math.sin(angle) * self.drift_radius
        self.z = self.base_z + math.cos(angle) * self.drift_radius


class TrailBubble(Entity):
    """Small bubble particle for creature trails - floats up and fades away."""

    def __init__(self, position):
        super().__init__(
            model="sphere",
            color=color.rgba(180, 230, 255, 180),
            scale=random.uniform(0.04, 0.12),
            position=position,
            unlit=True,
        )
        # Add random offset so they don't spawn in a perfect line
        self.x += random.uniform(-0.08, 0.08)
        self.z += random.uniform(-0.08, 0.08)

        self.drift_speed = random.uniform(-0.15, 0.15)  # Drifting left/right
        self.rise_speed = random.uniform(0.4, 0.8)  # Floating up
        self.fade_speed = random.uniform(0.4, 0.7)

    def update(self):
        # Float upward
        self.y += self.rise_speed * time.dt

        # Drift sideways (simulates water current)
        self.x += self.drift_speed * time.dt

        # Slowly fade away
        self.alpha -= time.dt * self.fade_speed

        # Destroy when invisible (cleanup memory!)
        if self.alpha <= 0:
            destroy(self)


class AmbientFish(Entity):
    """Ambient fish that swims smoothly outside the maze boundaries."""

    def __init__(self, x, z, texture, swim_direction=1):
        super().__init__(
            model="quad",
            texture=texture,
            color=color.white,
            unlit=True,
            double_sided=True,
            billboard=True,
        )
        # World position (not grid)
        self.world_x = x
        self.world_z = z
        self.base_y = random.uniform(0.3, 1.5)  # Height variation

        # Swimming parameters - slow and smooth
        self.speed = random.uniform(0.3, 0.8)  # Slow swimming speed
        self.swim_direction = swim_direction  # 1 = right, -1 = left
        self.vertical_drift = random.uniform(-0.1, 0.1)  # Slight vertical movement

        # Smooth bobbing animation
        self.bob_phase = random.uniform(0, math.tau)
        self.bob_speed = random.uniform(0.5, 1.0)  # Slower bobbing
        self.bob_amp = random.uniform(0.05, 0.15)

        # Gentle wave motion
        self.wave_phase = random.uniform(0, math.tau)
        self.wave_speed = random.uniform(0.3, 0.6)
        self.wave_amp = random.uniform(0.1, 0.25)

        # Scale
        self.base_scale = random.uniform(0.4, 0.8)
        self.facing = swim_direction
        self.bubble_cooldown = random.uniform(0, 2)

        # Shadow (optional - may not be visible outside maze)
        self.shadow = None
        self._update_scale()
        self._sync_position()

    def _update_scale(self):
        texture = self.texture
        aspect = 1.4
        if texture and hasattr(texture, "size") and texture.size[1] != 0:
            aspect = texture.size[0] / texture.size[1]
        self.scale = (self.base_scale * aspect * self.facing, self.base_scale)

    def _sync_position(self):
        t = time.time()

        # Smooth horizontal movement
        self.world_x += self.swim_direction * self.speed * time.dt

        # Gentle wave motion perpendicular to swim direction
        wave_offset = math.sin(t * self.wave_speed + self.wave_phase) * self.wave_amp

        # Smooth vertical bobbing
        bob = math.sin(t * self.bob_speed + self.bob_phase) * self.bob_amp

        # Apply position
        self.x = self.world_x
        self.z = self.world_z + wave_offset + self.vertical_drift * math.sin(t * 0.2)
        self.y = self.base_y + bob

        # Update shadow if exists
        if self.shadow:
            self.shadow.x = self.x
            self.shadow.z = self.z
            self.shadow.y = 0.02

    def update(self):
        self._sync_position()

        # Wrap around when fish swims too far
        maze_width_world = MAZE_WIDTH * TILE_SIZE
        margin = 8  # Distance outside maze to swim

        if self.swim_direction > 0 and self.world_x > maze_width_world + margin:
            self.world_x = -margin
        elif self.swim_direction < 0 and self.world_x < -margin:
            self.world_x = maze_width_world + margin

        # Spawn bubble trail behind the fish (less frequently for ambient)
        self.bubble_cooldown -= time.dt
        if self.bubble_cooldown <= 0:
            spawn_pos = Vec3(
                self.x - self.swim_direction * 0.3,
                self.y,
                self.z,
            )
            TrailBubble(position=spawn_pos)
            self.bubble_cooldown = random.uniform(0.4, 1.0)  # Less frequent bubbles


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
        self.ambient_fish = []

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

    def _is_safe_fish_tile(self, col, row):
        if self._is_wall(col, row):
            return False
        for dx, dy in [
            (1, 0),
            (-1, 0),
            (0, 1),
            (0, -1),
            (1, 1),
            (1, -1),
            (-1, 1),
            (-1, -1),
        ]:
            nx = col + dx
            ny = row + dy
            if not (0 <= nx < MAZE_WIDTH and 0 <= ny < MAZE_HEIGHT):
                return False
            if self._is_wall(nx, ny):
                return False
        return True

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
            scale=(WALL_TOP_SCALE, WALL_TOP_SCALE),
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
        # Create sandy ocean floor (sized to maze bounds, no extra border)
        floor_scale_x = MAZE_WIDTH
        floor_scale_z = MAZE_HEIGHT
        floor = Entity(
            model="quad",
            scale=(floor_scale_x, floor_scale_z),
            rotation_x=90,  # Rotate quad to be horizontal
            position=(
                MAZE_WIDTH * TILE_SIZE / 2 - TILE_SIZE / 2,
                -0.1,
                MAZE_HEIGHT * TILE_SIZE / 2 - TILE_SIZE / 2,
            ),
            texture=TEXTURES["floor"],
            texture_scale=(floor_scale_x / 2, floor_scale_z / 2),
            color=color.rgb(220, 200, 160),  # Warm sandy tint
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
                        scale=(
                            TILE_SIZE * WALL_THICKNESS,
                            WALL_HEIGHT,
                            TILE_SIZE * WALL_THICKNESS,
                        ),
                        texture=TEXTURES["wall"],
                        texture_scale=(1, 1),
                        color=color.white,
                    )
                    self.walls.append(wall)

                    # Glowing cyan top edge
                    edge = Entity(
                        model="cube",
                        position=(x, WALL_HEIGHT + 0.03, z),
                        scale=(
                            TILE_SIZE * WALL_THICKNESS,
                            0.06,
                            TILE_SIZE * WALL_THICKNESS,
                        ),
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

        # Add ambient fish (disabled for now)
        # self._add_ambient_fish()

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
        bounds = (
            -2 * TILE_SIZE,
            (MAZE_WIDTH + 2) * TILE_SIZE,
            -2 * TILE_SIZE,
            (MAZE_HEIGHT + 2) * TILE_SIZE,
        )
        y_bounds = (0.4, 3.0)
        for _ in range(28):
            # Use small bubble most of the time, large bubble occasionally
            if random.random() < 0.8:
                texture = DECOR_TEXTURES["bubble_small"]
            else:
                texture = DECOR_TEXTURES["bubble_large"]
            bubble = Bubble(texture, bounds, y_bounds)
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

    def _add_ambient_fish(self):
        """Spawn ambient fish swimming outside the maze boundaries."""
        maze_width = MAZE_WIDTH * TILE_SIZE
        maze_height = MAZE_HEIGHT * TILE_SIZE

        # Spawn fish on different "lanes" outside the maze
        fish_count = 12  # Number of ambient fish

        for i in range(fish_count):
            texture = random.choice(SMALL_FISH_TEXTURES)

            # Randomly choose which side of the maze (top, bottom, left, right)
            side = random.choice(["top", "bottom", "left", "right"])

            if side == "top":
                # Fish swimming above the maze (negative Z)
                x = random.uniform(-3, maze_width + 3)
                z = random.uniform(-4, -1.5)
                direction = random.choice([1, -1])
            elif side == "bottom":
                # Fish swimming below the maze (positive Z)
                x = random.uniform(-3, maze_width + 3)
                z = random.uniform(maze_height + 1.5, maze_height + 4)
                direction = random.choice([1, -1])
            elif side == "left":
                # Fish swimming to the left of maze
                x = random.uniform(-5, -2)
                z = random.uniform(-2, maze_height + 2)
                direction = 1  # Swim right
            else:  # right
                # Fish swimming to the right of maze
                x = random.uniform(maze_width + 2, maze_width + 5)
                z = random.uniform(-2, maze_height + 2)
                direction = -1  # Swim left

            fish = AmbientFish(x, z, texture, swim_direction=direction)
            self.ambient_fish.append(fish)


# =============================================================================
# PLAYER
# =============================================================================
class Player(Entity):
    """Player entity - Shapshique sprite."""

    def __init__(self, grid_x, grid_y, **kwargs):
        super().__init__(
            model="quad",
            texture=TEXTURES["player"],
            position=(grid_x * TILE_SIZE, 0.45, grid_y * TILE_SIZE),
            color=color.white,
            unlit=True,
            double_sided=True,
            billboard=True,
            **kwargs,
        )

        self.grid_x = grid_x
        self.grid_y = grid_y
        self.speed = 0.08
        self.direction = (1, 0)  # Facing right
        self.shoot_cooldown = 0
        self.base_scale = 0.75
        self.facing = 1
        self.shadow = None

        self.score = 0
        self.lives = 3

        self._update_scale()
        self._spawn_shadow()

    def _update_scale(self):
        texture = self.texture
        aspect = 1.0
        if texture and hasattr(texture, "size") and texture.size[1] != 0:
            aspect = texture.size[0] / texture.size[1]
        self.scale = (self.base_scale * aspect * self.facing, self.base_scale)

    def _spawn_shadow(self):
        self.shadow = Entity(
            model="quad",
            texture="circle",
            color=color.black66,
            rotation_x=90,
            scale=(0.55, 0.25),
            unlit=True,
            double_sided=True,
        )

    def move(self, dx, dy):
        """Move with collision detection."""
        if dx != 0 or dy != 0:
            self.direction = (dx, dy)

            if dx > 0 and self.facing != 1:
                self.facing = 1
                self.texture_scale = Vec2(1, 1)
                self._update_scale()
            elif dx < 0 and self.facing != -1:
                self.facing = -1
                self.texture_scale = Vec2(-1, 1)
                self._update_scale()

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
        if self.shadow:
            self.shadow.x = self.x
            self.shadow.z = self.z
            self.shadow.y = 0.02

    def update(self):
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= time.dt * 60  # Convert to frames


# =============================================================================
# BULLET
# =============================================================================
class Bullet(Entity):
    """Plasma bullet projectile."""

    def __init__(self, grid_x, grid_y, direction, is_player=True, **kwargs):
        bullet_color = color.rgba(120, 220, 255, 200) if is_player else NEON_RED

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
        self.trail_cooldown = 0

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

        # Water trail for player shots
        if self.is_player:
            self.trail_cooldown -= time.dt
            if self.trail_cooldown <= 0:
                TrailBubble(position=self.position + Vec3(0, -0.05, 0))
                self.trail_cooldown = random.uniform(0.03, 0.08)

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
        particle_count = 10 if self.is_player else 5
        for _ in range(particle_count):
            particle = Entity(
                model="sphere",
                scale=random.uniform(0.05, 0.12),
                position=self.position,
                color=(
                    self.color if not self.is_player else color.rgba(140, 230, 255, 180)
                ),
                unlit=True,
            )
            particle.animate_scale(0, duration=0.25)
            particle.animate_position(
                self.position
                + Vec3(
                    random.uniform(-0.4, 0.4),
                    random.uniform(0, 0.6),
                    random.uniform(-0.4, 0.4),
                ),
                duration=0.25,
            )
            destroy(particle, delay=0.3)


# =============================================================================
# ENEMY
# =============================================================================
class Enemy(Entity):
    """Enemy entity with type-specific behavior - using fish sprites."""

    # Fish texture mappings for each enemy type
    ENEMY_TEXTURES = {
        "burwor": "assets/images/sea_creatures/glow_fish.png",
        "garwor": "assets/images/sea_creatures/jellyfish.png",
        "thorwor": "assets/images/sea_creatures/barracuda.png",
        "worluk": "assets/images/sea_creatures/eel.png",
        "wizard": "assets/images/sea_creatures/anglerfish_large.png",
    }

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

    ENEMY_SCALES = {
        "burwor": 0.6,
        "garwor": 0.7,
        "thorwor": 0.8,
        "worluk": 0.75,
        "wizard": 0.9,
    }

    def __init__(self, grid_x, grid_y, enemy_type="burwor", **kwargs):
        self.enemy_type = enemy_type
        self.enemy_color = self.ENEMY_COLORS.get(enemy_type, NEON_BLUE)

        # Choose texture for enemy type
        texture_path = self.ENEMY_TEXTURES.get(
            enemy_type, self.ENEMY_TEXTURES["burwor"]
        )

        base_scale = self.ENEMY_SCALES.get(enemy_type, 0.6)

        super().__init__(
            model="quad",
            texture=texture_path,
            color=color.white,  # Use white to show texture properly
            scale=(base_scale, base_scale),
            position=(grid_x * TILE_SIZE, 0.35, grid_y * TILE_SIZE),
            unlit=True,
            double_sided=True,
            billboard=True,
            **kwargs,
        )

        self.grid_x = grid_x
        self.grid_y = grid_y
        self.base_scale = base_scale
        self.speed = self.ENEMY_SPEEDS.get(enemy_type, 0.03)
        self.points = self.ENEMY_POINTS.get(enemy_type, 100)
        self.direction = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        self.move_timer = 0
        self.visible = True
        self.health = 3 if enemy_type == "wizard" else 1
        self.bubble_cooldown = 0  # Timer for bubble trail spawning
        self.facing = 1  # 1 = right, -1 = left

        # Create shadow
        self._create_shadow()

    def _create_shadow(self):
        """Create a shadow beneath the enemy."""
        self.shadow = Entity(
            model="quad",
            texture="circle",
            color=color.black66,
            rotation_x=90,
            scale=(self.base_scale * 0.8, self.base_scale * 0.4),
            position=(self.x, 0.02, self.z),
            unlit=True,
            double_sided=True,
        )

    def update(self):
        # Gentle bobbing animation for swimming effect
        anim_time = time.time()
        bob = math.sin(anim_time * 3 + hash(str(self.grid_x) + str(self.grid_y))) * 0.03
        self.y = 0.35 + bob

        # Garwor cloaking (jellyfish becomes translucent)
        if self.enemy_type == "garwor":
            if random.random() < 0.003:
                was_visible = self.visible
                self.visible = not self.visible
                self.alpha = 0.3 if not self.visible else 0.9
                # Play sound when becoming visible (like original WoW)
                if self.visible and not was_visible and sound_manager:
                    sound_manager.play("enemy_visible", 0.3)

        # Wizard pulsing glow and teleport
        if self.enemy_type == "wizard":
            pulse = 0.85 + math.sin(anim_time * 4) * 0.15
            self.scale = Vec3(self.base_scale * pulse, self.base_scale * pulse, 1)

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

        # Flip sprite horizontally based on movement direction
        if self.direction[0] != 0:
            new_facing = 1 if self.direction[0] > 0 else -1
            if new_facing != self.facing:
                self.facing = new_facing
                self.scale_x = abs(self.scale_x) * self.facing

        # Update shadow position
        if hasattr(self, "shadow"):
            self.shadow.x = self.x
            self.shadow.z = self.z

        # Spawn bubble trail behind the enemy
        self.bubble_cooldown -= time.dt
        if self.bubble_cooldown <= 0:
            # Spawn bubble slightly behind the enemy
            spawn_pos = Vec3(
                self.x - self.direction[0] * 0.3,
                self.y + 0.1,
                self.z - self.direction[1] * 0.3,
            )
            TrailBubble(position=spawn_pos)
            self.bubble_cooldown = random.uniform(0.1, 0.25)

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
        # Death particles using enemy color
        particle_color = self.ENEMY_COLORS.get(self.enemy_type, NEON_BLUE)
        for _ in range(15):
            particle = Entity(
                model="sphere",
                scale=0.1,
                position=self.position,
                color=particle_color,
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

        # Destroy shadow
        if hasattr(self, "shadow") and self.shadow:
            destroy(self.shadow)

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
            position=(-0.78, 0.45),
            scale=1.5,
            color=NEON_YELLOW,
        )

        # Lives
        self.lives_text = Text(
            text="LIVES: 3",
            position=(-0.78, 0.40),
            scale=1.5,
            color=NEON_GREEN,
        )

        # Enemies
        self.enemies_text = Text(
            text="ENEMIES: 0",
            position=(0.45, 0.45),
            scale=1.5,
            color=NEON_RED,
        )

        # Phase
        self.phase_text = Text(
            text="PHASE: NORMAL",
            position=(0.45, 0.40),
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

        # Debug overlay (movement + grid info)
        self.debug_text = Text(
            text="",
            position=(-0.78, -0.35),
            scale=0.9,
            color=NEON_CYAN,
        )

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

    def update_debug(self, player, input_x, input_z):
        grid_x = int(player.grid_x + 0.5)
        grid_y = int(player.grid_y + 0.5)
        tile = "out"
        if 0 <= grid_x < MAZE_WIDTH and 0 <= grid_y < MAZE_HEIGHT:
            tile = "wall" if MAZE[grid_y][grid_x] == 1 else "open"

        keys = []
        if held_keys["w"] or held_keys["up arrow"]:
            keys.append("W/Up")
        if held_keys["s"] or held_keys["down arrow"]:
            keys.append("S/Down")
        if held_keys["a"] or held_keys["left arrow"]:
            keys.append("A/Left")
        if held_keys["d"] or held_keys["right arrow"]:
            keys.append("D/Right")
        if held_keys["shift"]:
            keys.append("Shift")
        key_text = ", ".join(keys) if keys else "none"

        self.debug_text.text = (
            f"Pos: ({player.grid_x:.2f}, {player.grid_y:.2f})\n"
            f"Grid: ({grid_x}, {grid_y}) {tile}\n"
            f"Input: ({input_x}, {input_z}) Keys: {key_text}"
        )


# =============================================================================
# GAME MANAGER
# =============================================================================
class GameManager(Entity):
    """Manages game state and logic."""

    def __init__(self):
        super().__init__()

        # Initialize sound manager
        global sound_manager
        if sound_manager is None:
            sound_manager = SoundManager()

        self.game_over = False
        self.victory = False
        self.phase = "normal"

        # Build maze
        self.maze_builder = MazeBuilder()
        self.valid_positions = self.maze_builder.build()

        # Setup camera
        self.iso_camera = IsometricCamera()

        # Find spawn position (prefer interior tiles so the sprite isn't jammed against walls)
        spawn_candidates = self.maze_builder.interior_positions or self.valid_positions
        bottom_candidates = [
            pos for pos in spawn_candidates if pos[1] > MAZE_HEIGHT - 4
        ]
        if bottom_candidates:
            spawn_pos = random.choice(bottom_candidates)
        else:
            spawn_pos = spawn_candidates[-1]

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

        # Play sounds like original Wizard of Wor
        if sound_manager:
            sound_manager.play("voice_welcome")  # "Welcome to the Dungeon of Wor!"
            invoke(lambda: sound_manager.play("player_enters"), delay=0.5)
            invoke(lambda: sound_manager.play_music("loop01", 0.2), delay=2.0)

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
            # Store max enemies for tempo tracking
            self.max_enemies = len(self.enemies)

        elif self.phase == "worluk":
            pos = random.choice(self.valid_positions)
            enemy = Enemy(pos[0] + 0.5, pos[1] + 0.5, "worluk")
            self.enemies.append(enemy)
            self.max_enemies = 1
            self.hud.show_message("THE WORLUK APPEARS!", 3)
            if sound_manager:
                sound_manager.play("worluk")
                sound_manager.play_music("loop04", 0.25)  # Fast tempo for worluk

        elif self.phase == "wizard":
            pos = random.choice(self.valid_positions)
            enemy = Enemy(pos[0] + 0.5, pos[1] + 0.5, "wizard")
            self.enemies.append(enemy)
            self.max_enemies = 1
            self.hud.show_message("I AM THE WIZARD OF WOR!", 3)
            if sound_manager:
                sound_manager.play("voice_wizard")  # Classic "I am the Wizard of Wor!"
                sound_manager.play_music("loop05", 0.25)  # Fastest tempo for wizard

        self.hud.update_enemies(len(self.enemies))

    def input(self, key):
        if self.game_over or self.victory:
            if key == "r":
                # Restart game
                scene.clear()
                if sound_manager:
                    sound_manager.stop_music()
                self.__init__()
            return

        # Pass camera controls
        self.iso_camera.input(key)

        # Shooting
        if key == "space" and self.player.shoot_cooldown <= 0:
            self._spawn_water_burst()
            bullet = Bullet(
                self.player.grid_x,
                self.player.grid_y,
                self.player.direction,
                is_player=True,
            )
            self.bullets.append(bullet)
            self.player.shoot_cooldown = 15
            if sound_manager:
                sound_manager.play("player_fire", 0.4)

    def _spawn_water_burst(self):
        if not self.player:
            return
        direction = Vec3(self.player.direction[0], 0, self.player.direction[1])
        if direction.length() == 0:
            direction = Vec3(1, 0, 0)
        direction = direction.normalized()
        origin = Vec3(self.player.x, 0.45, self.player.z) + direction * 0.4
        for _ in range(8):
            offset = Vec3(
                random.uniform(-0.12, 0.12),
                random.uniform(-0.05, 0.08),
                random.uniform(-0.12, 0.12),
            )
            TrailBubble(position=origin + offset)

    def update(self):
        if self.game_over or self.victory:
            return

        # Handle player input - CAMERA-RELATIVE movement
        # Get raw input direction
        input_x, input_z = 0, 0
        if held_keys["left arrow"] or held_keys["left"] or held_keys["a"]:
            input_x = -1
        elif held_keys["right arrow"] or held_keys["right"] or held_keys["d"]:
            input_x = 1
        if held_keys["up arrow"] or held_keys["up"] or held_keys["w"]:
            input_z = 1  # Forward relative to camera
        elif held_keys["down arrow"] or held_keys["down"] or held_keys["s"]:
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
        self.hud.update_debug(self.player, input_x, input_z)

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
                            # Play appropriate death sound
                            if sound_manager:
                                if enemy.enemy_type == "wizard":
                                    sound_manager.play("wizard_dead")
                                elif enemy.enemy_type == "worluk":
                                    sound_manager.play("worluk_dead")
                                else:
                                    sound_manager.play("enemy_dead")
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

        # Update music tempo based on remaining enemies (like original WoW)
        if sound_manager and self.phase == "normal" and hasattr(self, "max_enemies"):
            sound_manager.update_music_tempo(len(self.enemies), self.max_enemies)

        # Radar blip for nearby enemies (invisible garwor detection)
        if sound_manager and self.enemies:
            closest_dist = float("inf")
            for enemy in self.enemies:
                if enemy:
                    dist = math.sqrt(
                        (self.player.grid_x - enemy.grid_x) ** 2
                        + (self.player.grid_y - enemy.grid_y) ** 2
                    )
                    if dist < closest_dist:
                        closest_dist = dist
            # Play radar blip for close enemies
            if closest_dist < 8:
                sound_manager.play_radar_blip(closest_dist, time.time())

        # Phase progression
        if len(self.enemies) == 0:
            if self.phase == "normal":
                self.phase = "worluk"
                if sound_manager:
                    sound_manager.play("maze_exit")  # Level clear sound
                invoke(self.spawn_enemies, delay=1)
            elif self.phase == "worluk":
                self.phase = "wizard"
                invoke(self.spawn_enemies, delay=1)
            elif self.phase == "wizard":
                self.victory = True
                if sound_manager:
                    sound_manager.play("laugh")  # Victory laugh
                self.show_end_screen()

    def player_hit(self):
        """Handle player getting hit."""
        self.player.lives -= 1
        self.hud.update_lives(self.player.lives)

        # Play player death sound
        if sound_manager:
            sound_manager.play("player_dead")

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
            if sound_manager:
                sound_manager.play("voice_prepare")  # "Prepare yourself!" voice

    def show_end_screen(self):
        """Show game over or victory screen."""
        # Stop music and play end sound
        if sound_manager:
            sound_manager.stop_music()
            if self.game_over:
                sound_manager.play("game_over")
                invoke(
                    lambda: sound_manager.play("voice_game_over"), delay=0.5
                )  # Voice "Game Over"
            else:
                sound_manager.play("double_score")

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
