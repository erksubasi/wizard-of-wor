"""
Wizard of Wor - Axonometric 2.5D Edition
A 2.5D isometric reimagining of the classic 1981 arcade game.

Controls:
- Arrow Keys / WASD: Move
- Space: Shoot
- Mouse: Rotate camera view (move left/right)
- Mouse Wheel: Zoom in/out
- Middle Mouse / M: Reset camera
- ESC: Quit
"""

import math
import random

import pygame

# =============================================================================
# INITIALIZATION
# =============================================================================
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

# =============================================================================
# CONSTANTS
# =============================================================================
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 800

# Isometric projection constants
ISO_ANGLE = 30  # Degrees
ISO_SCALE = 1.0
TILE_WIDTH = 48  # Width of tile in isometric view
TILE_HEIGHT = 24  # Height of tile (half of width for 2:1 ratio)
WALL_HEIGHT = 36  # Height of walls in pixels


# Camera state (controlled by mouse)
class Camera:
    """Global camera state for view rotation."""

    angle = 0.0  # Rotation angle in radians
    zoom = 1.0  # Zoom level
    target_angle = 0.0
    target_zoom = 1.0

    @classmethod
    def update(cls):
        """Smoothly interpolate camera to target values."""
        cls.angle += (cls.target_angle - cls.angle) * 0.1
        cls.zoom += (cls.target_zoom - cls.zoom) * 0.1

    @classmethod
    def reset(cls):
        """Reset camera to default position."""
        cls.target_angle = 0.0
        cls.target_zoom = 1.0


# Maze dimensions
MAZE_WIDTH = 21
MAZE_HEIGHT = 15

# Colors - Neon palette
BLACK = (0, 0, 0)
DARK_BLUE = (5, 10, 25)
NEON_BLUE = (0, 150, 255)
NEON_CYAN = (0, 255, 255)
NEON_PURPLE = (180, 0, 255)
NEON_PINK = (255, 0, 150)
NEON_GREEN = (0, 255, 100)
NEON_RED = (255, 50, 50)
NEON_ORANGE = (255, 150, 0)
NEON_YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)

# Maze layout
MAZE = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 1, 0, 0, 1, 1, 1, 0, 1, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 0, 1],
    [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
    [1, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 1, 0, 0, 1, 1, 1, 0, 1, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]


# =============================================================================
# ISOMETRIC UTILITIES
# =============================================================================


def cart_to_iso(x, y):
    """Convert cartesian grid coordinates to isometric screen coordinates with rotation."""
    # Center the grid coordinates around the maze center
    cx = x - MAZE_WIDTH / 2
    cy = y - MAZE_HEIGHT / 2

    # Apply rotation around the center
    cos_a = math.cos(Camera.angle)
    sin_a = math.sin(Camera.angle)
    rx = cx * cos_a - cy * sin_a
    ry = cx * sin_a + cy * cos_a

    # Apply isometric projection with zoom
    # Standard 2:1 isometric: x_screen = (x - y), y_screen = (x + y) / 2
    # But we use TILE_WIDTH for x and TILE_HEIGHT for y scaling
    tile_w = TILE_WIDTH * Camera.zoom
    tile_h = TILE_HEIGHT * Camera.zoom

    iso_x = (rx - ry) * (tile_w / 2)
    iso_y = (rx + ry) * (tile_h / 2)
    return iso_x, iso_y


def get_tile_corner_offsets():
    """Get the 4 corner offsets for a tile in screen space.

    Returns offsets relative to the tile's center position.
    Corners are in order: top, right, bottom, left (for standard isometric).
    """
    cos_a = math.cos(Camera.angle)
    sin_a = math.sin(Camera.angle)
    tile_w = TILE_WIDTH * Camera.zoom
    tile_h = TILE_HEIGHT * Camera.zoom

    # A tile occupies 1x1 grid units. Its 4 corners in grid space are at:
    # (0.5, 0.5), (0.5, -0.5), (-0.5, -0.5), (-0.5, 0.5) relative to center
    # These need to go through the same rotation + isometric projection

    corners = []
    # Define corners in grid-space order that makes sense for isometric
    grid_corners = [
        (0.5, -0.5),  # Grid "north-east" -> screen top
        (0.5, 0.5),  # Grid "south-east" -> screen right
        (-0.5, 0.5),  # Grid "south-west" -> screen bottom
        (-0.5, -0.5),  # Grid "north-west" -> screen left
    ]

    for gx, gy in grid_corners:
        # Rotate
        rx = gx * cos_a - gy * sin_a
        ry = gx * sin_a + gy * cos_a
        # Isometric projection
        ox = (rx - ry) * (tile_w / 2)
        oy = (rx + ry) * (tile_h / 2)
        corners.append((int(ox), int(oy)))

    return corners


def iso_to_cart(iso_x, iso_y):
    """Convert isometric screen coordinates to cartesian."""
    x = (iso_x / (TILE_WIDTH // 2) + iso_y / (TILE_HEIGHT // 2)) / 2
    y = (iso_y / (TILE_HEIGHT // 2) - iso_x / (TILE_WIDTH // 2)) / 2
    return x, y


def get_screen_pos(grid_x, grid_y, offset_x=0, offset_y=0):
    """Get screen position for a grid position with offset to center the maze."""
    iso_x, iso_y = cart_to_iso(grid_x, grid_y)
    # Center the maze on screen
    screen_x = iso_x + SCREEN_WIDTH // 2 + offset_x
    screen_y = iso_y + SCREEN_HEIGHT // 2 - 50 + offset_y  # Center vertically
    return int(screen_x), int(screen_y)


def get_rotated_depth(grid_x, grid_y):
    """Calculate depth based on screen Y position for proper isometric sorting.

    In isometric projection, objects with higher screen Y values are "in front"
    and should be drawn later. This uses the actual screen position after
    all transformations (rotation, zoom, isometric projection).
    """
    # Get the actual screen position - this accounts for rotation and zoom
    _, screen_y = get_screen_pos(grid_x, grid_y)
    return screen_y


# =============================================================================
# ISOMETRIC DRAWING
# =============================================================================


class IsometricRenderer:
    """Handles all isometric drawing operations."""

    @staticmethod
    def draw_floor_tile(surface, grid_x, grid_y, color=DARK_BLUE, glow_color=None):
        """Draw an isometric floor tile with rotation support."""
        x, y = get_screen_pos(grid_x, grid_y)

        # Get pre-computed corner offsets (shared with wall blocks)
        corners = get_tile_corner_offsets()

        # Diamond shape for floor
        points = [(x + c[0], y + c[1]) for c in corners]

        # Draw glow first if specified
        if glow_color:
            # Calculate bounding box for glow
            min_x = min(p[0] for p in points)
            max_x = max(p[0] for p in points)
            min_y = min(p[1] for p in points)
            max_y = max(p[1] for p in points)
            w = max_x - min_x + 10
            h = max_y - min_y + 10

            glow_surf = pygame.Surface((w, h), pygame.SRCALPHA)
            # Offset points to local surface coordinates
            local_points = [(p[0] - min_x + 5, p[1] - min_y + 5) for p in points]
            pygame.draw.polygon(glow_surf, (*glow_color[:3], 30), local_points)
            surface.blit(
                glow_surf,
                (min_x - 5, min_y - 5),
                special_flags=pygame.BLEND_RGB_ADD,
            )

        # Fill
        pygame.draw.polygon(surface, color, points)
        # Outline
        pygame.draw.polygon(surface, NEON_BLUE, points, 1)

    @staticmethod
    def draw_wall_block(
        surface, grid_x, grid_y, color=NEON_BLUE, wall_height=WALL_HEIGHT
    ):
        """Draw an isometric wall block (cube) with rotation-aware rendering."""
        x, y = get_screen_pos(grid_x, grid_y)
        wh = int(wall_height * Camera.zoom)

        # Get pre-computed corner offsets (same as floor tile)
        corners = get_tile_corner_offsets()

        # Top face (always visible from above)
        top_color = tuple(min(255, int(c * 1.2)) for c in color[:3])
        top_points = [(x + corners[i][0], y + corners[i][1] - wh) for i in range(4)]
        pygame.draw.polygon(surface, top_color, top_points)
        pygame.draw.polygon(surface, WHITE, top_points, 1)

        # Determine which side faces are visible based on camera angle
        cos_a = math.cos(Camera.angle)
        sin_a = math.sin(Camera.angle)

        # Face normals in grid space (pointing outward):
        # Face 0 (between corners 0-1): normal is (+1, 0) - "east" face
        # Face 1 (between corners 1-2): normal is (0, +1) - "south" face
        # Face 2 (between corners 2-3): normal is (-1, 0) - "west" face
        # Face 3 (between corners 3-0): normal is (0, -1) - "north" face

        face_normals = [(1, 0), (0, 1), (-1, 0), (0, -1)]

        # A face is visible if, after rotation, its normal has positive (rx + ry)
        # This means it faces toward the camera in isometric view
        visible_faces = []
        for i, (nx, ny) in enumerate(face_normals):
            # Rotate normal
            rnx = nx * cos_a - ny * sin_a
            rny = nx * sin_a + ny * cos_a
            # Visibility check: face visible if it faces "toward" camera
            if (rnx + rny) > 0.01:  # Small threshold to avoid edge cases
                visible_faces.append((i, rnx + rny))

        # Sort by depth (draw back faces first) - smaller depth value first
        visible_faces.sort(key=lambda f: f[1])

        # Draw visible faces
        for face_idx, depth in visible_faces:
            c1 = face_idx
            c2 = (face_idx + 1) % 4

            # Brightness based on face orientation
            brightness = 0.3 + 0.35 * (depth / 1.5)
            brightness = max(0.25, min(0.75, brightness))

            face_color = tuple(int(c * brightness) for c in color[:3])

            face_points = [
                (x + corners[c1][0], y + corners[c1][1] - wh),  # Top corner 1
                (x + corners[c2][0], y + corners[c2][1] - wh),  # Top corner 2
                (x + corners[c2][0], y + corners[c2][1]),  # Bottom corner 2
                (x + corners[c1][0], y + corners[c1][1]),  # Bottom corner 1
            ]
            pygame.draw.polygon(surface, face_color, face_points)
            pygame.draw.polygon(surface, color, face_points, 1)

        # Neon edge glow on top
        pygame.draw.lines(surface, WHITE, True, top_points, 2)

    @staticmethod
    def draw_sprite_base(surface, grid_x, grid_y, z_offset=0):
        """Get position for drawing a sprite at grid position."""
        x, y = get_screen_pos(grid_x, grid_y)
        return x, y - z_offset


# =============================================================================
# SPRITE CLASSES
# =============================================================================


class IsoSprite:
    """Base class for isometric sprites."""

    def __init__(self, grid_x, grid_y):
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.z = 0  # Height offset
        self.frame = 0

    def get_screen_pos(self):
        """Get screen position for this sprite."""
        x, y = get_screen_pos(self.grid_x, self.grid_y)
        return x, y - self.z

    def get_depth(self):
        """Get depth for sorting (painter's algorithm)."""
        return self.grid_x + self.grid_y


class Player(IsoSprite):
    """The Space Marine player character."""

    def __init__(self, grid_x, grid_y):
        super().__init__(grid_x, grid_y)
        self.direction = (1, 0)  # Facing direction
        self.speed = 0.08
        self.lives = 3
        self.score = 0
        self.shoot_cooldown = 0
        self.color = NEON_YELLOW
        self.bob_offset = 0

    def get_rect(self):
        """Get collision rectangle in grid coordinates."""
        return pygame.Rect(
            (self.grid_x - 0.3) * TILE_WIDTH,
            (self.grid_y - 0.3) * TILE_HEIGHT,
            0.6 * TILE_WIDTH,
            0.6 * TILE_HEIGHT,
        )

    def move(self, dx, dy, maze):
        """Move with collision detection."""
        self.frame += 1

        if dx != 0 or dy != 0:
            self.direction = (dx, dy)
            # Walking bob animation
            self.bob_offset = math.sin(self.frame * 0.3) * 3
        else:
            self.bob_offset *= 0.8

        new_x = self.grid_x + dx * self.speed
        new_y = self.grid_y + dy * self.speed

        # Check collision
        test_x = int(new_x + 0.5)
        test_y = int(new_y + 0.5)

        # Horizontal movement
        if 0 <= test_x < MAZE_WIDTH:
            if maze[int(self.grid_y + 0.5)][test_x] == 0:
                self.grid_x = new_x

        # Vertical movement
        if 0 <= test_y < MAZE_HEIGHT:
            if maze[test_y][int(self.grid_x + 0.5)] == 0:
                self.grid_y = new_y

        # Clamp to maze bounds
        self.grid_x = max(0.5, min(MAZE_WIDTH - 1.5, self.grid_x))
        self.grid_y = max(0.5, min(MAZE_HEIGHT - 1.5, self.grid_y))

    def draw(self, surface):
        """Draw the Space Marine in isometric view."""
        x, y = self.get_screen_pos()
        y -= self.bob_offset

        # Shadow
        shadow_points = [
            (x, y + 8),
            (x + 12, y + 4),
            (x, y),
            (x - 12, y + 4),
        ]
        pygame.draw.polygon(surface, (0, 0, 0, 100), shadow_points)

        # Body (isometric box shape)
        body_height = 28

        # Front face
        front_color = self.color
        front_points = [
            (x - 10, y - body_height),
            (x + 10, y - body_height),
            (x + 10, y),
            (x - 10, y),
        ]
        pygame.draw.polygon(
            surface, tuple(int(c * 0.6) for c in front_color), front_points
        )

        # Top face (helmet/head area)
        top_points = [
            (x, y - body_height - 10),
            (x + 10, y - body_height - 5),
            (x, y - body_height),
            (x - 10, y - body_height - 5),
        ]
        pygame.draw.polygon(surface, front_color, top_points)

        # Visor
        visor_y = y - body_height - 6
        pygame.draw.ellipse(surface, NEON_CYAN, (x - 6, visor_y, 12, 6))
        pygame.draw.ellipse(surface, WHITE, (x - 4, visor_y + 1, 4, 3))

        # Armor details
        pygame.draw.line(
            surface, WHITE, (x - 8, y - body_height + 5), (x - 8, y - 5), 2
        )
        pygame.draw.line(
            surface, WHITE, (x + 8, y - body_height + 5), (x + 8, y - 5), 2
        )

        # Gun
        gun_len = 16
        dir_x, dir_y = self.direction
        # Convert direction to isometric
        iso_dir_x = (dir_x - dir_y) * 0.7
        iso_dir_y = (dir_x + dir_y) * 0.35

        gun_start = (x + iso_dir_x * 8, y - 15 + iso_dir_y * 8)
        gun_end = (x + iso_dir_x * (8 + gun_len), y - 15 + iso_dir_y * (8 + gun_len))

        pygame.draw.line(surface, (100, 100, 120), gun_start, gun_end, 4)
        pygame.draw.line(surface, self.color, gun_start, gun_end, 2)

        # Muzzle glow
        muzzle_pulse = abs(math.sin(self.frame * 0.2)) * 3
        pygame.draw.circle(
            surface, WHITE, (int(gun_end[0]), int(gun_end[1])), int(3 + muzzle_pulse)
        )


class Enemy(IsoSprite):
    """Enemy creature base class."""

    enemy_colors = {
        "burwor": NEON_BLUE,
        "garwor": NEON_ORANGE,
        "thorwor": NEON_RED,
        "worluk": NEON_GREEN,
        "wizard": NEON_PURPLE,
    }

    enemy_points = {
        "burwor": 100,
        "garwor": 200,
        "thorwor": 500,
        "worluk": 1000,
        "wizard": 2500,
    }

    enemy_speeds = {
        "burwor": 0.03,
        "garwor": 0.04,
        "thorwor": 0.05,
        "worluk": 0.06,
        "wizard": 0.04,
    }

    def __init__(self, grid_x, grid_y, enemy_type="burwor"):
        super().__init__(grid_x, grid_y)
        self.enemy_type = enemy_type
        self.color = self.enemy_colors.get(enemy_type, NEON_BLUE)
        self.points = self.enemy_points.get(enemy_type, 100)
        self.speed = self.enemy_speeds.get(enemy_type, 0.03)
        self.direction = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        self.move_timer = 0
        self.visible = True
        self.health = 3 if enemy_type == "wizard" else 1
        self.animation_offset = random.random() * 100
        self.just_became_visible = False  # Flag for sound trigger

    def get_rect(self):
        """Get collision rectangle."""
        return pygame.Rect(
            (self.grid_x - 0.4) * TILE_WIDTH,
            (self.grid_y - 0.4) * TILE_HEIGHT,
            0.8 * TILE_WIDTH,
            0.8 * TILE_HEIGHT,
        )

    def update(self, maze, player):
        """Update enemy AI."""
        self.frame += 1
        self.move_timer += 1

        # Garwor cloaking
        if self.enemy_type == "garwor":
            if random.random() < 0.01:
                was_visible = self.visible
                self.visible = not self.visible
                # Flag for sound when becoming visible
                if not was_visible and self.visible:
                    self.just_became_visible = True

        # Change direction occasionally or when hitting wall
        if self.move_timer > 30 or random.random() < 0.02:
            self.move_timer = 0

            # Sometimes move toward player
            if random.random() < 0.3:
                dx = player.grid_x - self.grid_x
                dy = player.grid_y - self.grid_y
                if abs(dx) > abs(dy):
                    self.direction = (1 if dx > 0 else -1, 0)
                else:
                    self.direction = (0, 1 if dy > 0 else -1)
            else:
                self.direction = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])

        # Move
        new_x = self.grid_x + self.direction[0] * self.speed
        new_y = self.grid_y + self.direction[1] * self.speed

        test_x = int(new_x + 0.5)
        test_y = int(new_y + 0.5)

        can_move = True
        if not (0 <= test_x < MAZE_WIDTH and 0 <= test_y < MAZE_HEIGHT):
            can_move = False
        elif maze[test_y][test_x] == 1:
            can_move = False

        if can_move:
            self.grid_x = new_x
            self.grid_y = new_y
        else:
            self.move_timer = 100  # Force direction change

    def draw(self, surface):
        """Draw enemy in isometric view."""
        if self.enemy_type == "garwor" and not self.visible:
            self._draw_shimmer(surface)
            return

        x, y = self.get_screen_pos()
        anim = self.frame + self.animation_offset

        # Shadow
        shadow_surf = pygame.Surface((30, 15), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 80), (0, 0, 30, 15))
        surface.blit(shadow_surf, (x - 15, y - 5))

        if self.enemy_type == "burwor":
            self._draw_burwor(surface, x, y, anim)
        elif self.enemy_type == "garwor":
            self._draw_garwor(surface, x, y, anim)
        elif self.enemy_type == "thorwor":
            self._draw_thorwor(surface, x, y, anim)
        elif self.enemy_type == "worluk":
            self._draw_worluk(surface, x, y, anim)
        elif self.enemy_type == "wizard":
            self._draw_wizard(surface, x, y, anim)

    def _draw_shimmer(self, surface):
        """Draw cloaking shimmer effect for invisible Garwor."""
        x, y = self.get_screen_pos()
        for i in range(5):
            shimmer_x = x + math.sin(self.frame * 0.2 + i) * 10
            shimmer_y = y - 15 + math.cos(self.frame * 0.2 + i) * 5
            alpha = int(50 + math.sin(self.frame * 0.3 + i) * 30)
            pygame.draw.circle(
                surface, (*NEON_ORANGE[:3], alpha), (int(shimmer_x), int(shimmer_y)), 3
            )

    def _draw_burwor(self, surface, x, y, anim):
        """Draw Burwor - Alien Crawler Beast."""
        color = self.color

        # Segmented body
        for i in range(3):
            seg_y = y - 10 - i * 8
            seg_width = 20 - i * 3
            seg_color = tuple(int(c * (1 - i * 0.15)) for c in color)
            pygame.draw.ellipse(
                surface, seg_color, (x - seg_width // 2, seg_y, seg_width, 12)
            )

        # Mandibles
        mandible_open = math.sin(anim * 0.3) * 5
        pygame.draw.line(
            surface, NEON_RED, (x - 8, y - 28), (x - 14 - mandible_open, y - 20), 3
        )
        pygame.draw.line(
            surface, NEON_RED, (x + 8, y - 28), (x + 14 + mandible_open, y - 20), 3
        )

        # Multiple eyes
        for i in range(3):
            eye_x = x - 6 + i * 6
            eye_y = y - 32
            pygame.draw.circle(surface, NEON_RED, (eye_x, eye_y), 3)
            pygame.draw.circle(surface, WHITE, (eye_x, eye_y), 1)

        # Legs
        leg_anim = math.sin(anim * 0.4) * 4
        for side in [-1, 1]:
            for i in range(3):
                leg_x = x + side * 12
                leg_y = y - 5 - i * 6
                offset = leg_anim if i % 2 == 0 else -leg_anim
                pygame.draw.line(
                    surface,
                    color,
                    (leg_x, leg_y),
                    (leg_x + side * (10 + offset), leg_y + 5),
                    2,
                )

    def _draw_garwor(self, surface, x, y, anim):
        """Draw Garwor - Cloaking Predator."""
        color = self.color

        # Sleek body
        body_points = [
            (x, y - 35),
            (x + 12, y - 20),
            (x + 10, y - 5),
            (x - 10, y - 5),
            (x - 12, y - 20),
        ]
        pygame.draw.polygon(surface, tuple(int(c * 0.7) for c in color), body_points)
        pygame.draw.polygon(surface, color, body_points, 2)

        # Dreadlock tendrils
        for i in range(4):
            tendril_x = x - 8 + i * 5
            sway = math.sin(anim * 0.15 + i) * 3
            pygame.draw.line(
                surface,
                (80, 50, 30),
                (tendril_x, y - 32),
                (tendril_x + sway, y - 20),
                2,
            )

        # Hunter eyes
        eye_glow = int(200 + math.sin(anim * 0.1) * 55)
        pygame.draw.circle(surface, (eye_glow, 100, 0), (x - 5, y - 28), 4)
        pygame.draw.circle(surface, (eye_glow, 100, 0), (x + 5, y - 28), 4)

        # Claws
        claw_anim = math.sin(anim * 0.3) * 3
        for side in [-1, 1]:
            claw_x = x + side * 14
            pygame.draw.line(
                surface,
                NEON_RED,
                (claw_x, y - 15),
                (claw_x + side * 6, y - 8 + claw_anim),
                2,
            )

    def _draw_thorwor(self, surface, x, y, anim):
        """Draw Thorwor - Xenomorph Scorpion."""
        color = self.color

        # Armored body segments
        for i in range(4):
            seg_y = y - 5 - i * 7
            seg_width = 22 - abs(i - 1.5) * 3
            seg_color = tuple(int(c * (0.6 + i * 0.1)) for c in color)
            pygame.draw.ellipse(
                surface, seg_color, (x - seg_width // 2, seg_y, seg_width, 10)
            )

        # Elongated head
        pygame.draw.polygon(
            surface, (60, 0, 0), [(x, y - 40), (x + 8, y - 30), (x - 8, y - 30)]
        )

        # Compound eyes
        for i in range(5):
            eye_x = x - 4 + (i % 3) * 4
            eye_y = y - 35 + (i // 3) * 3
            pygame.draw.circle(surface, NEON_PURPLE, (eye_x, eye_y), 2)

        # Pincers
        pincer_snap = math.sin(anim * 0.25) * 4
        for side in [-1, 1]:
            pygame.draw.line(
                surface,
                color,
                (x + side * 10, y - 25),
                (x + side * (18 + pincer_snap), y - 22),
                3,
            )
            pygame.draw.line(
                surface,
                color,
                (x + side * 10, y - 25),
                (x + side * (18 + pincer_snap), y - 28),
                3,
            )

        # Stinger tail
        tail_curve = math.sin(anim * 0.12) * 0.3
        prev = (x, y - 5)
        for i in range(5):
            angle = -math.pi / 2 + (i / 5) * math.pi * 0.7 + tail_curve
            dist = 8 + i * 4
            next_pt = (x + math.cos(angle) * 3, y - 5 - math.sin(angle) * dist)
            pygame.draw.line(surface, color, prev, next_pt, 3 - i // 2)
            prev = next_pt
        # Venom drop
        pygame.draw.circle(surface, NEON_YELLOW, (int(prev[0]), int(prev[1])), 4)

    def _draw_worluk(self, surface, x, y, anim):
        """Draw Worluk - Flying Demon Wraith."""
        color = self.color
        hover = math.sin(anim * 0.1) * 5
        y -= hover

        # Ghostly trail
        for i in range(4):
            trail_alpha = 60 - i * 15
            trail_y = y + i * 6
            pygame.draw.ellipse(
                surface,
                (*color[:3], trail_alpha),
                (x - 10 + i * 2, trail_y, 20 - i * 4, 10),
            )

        # Ethereal body
        body_points = [
            (x, y - 30),
            (x + 12, y - 15),
            (x + 8, y + 5),
            (x - 8, y + 5),
            (x - 12, y - 15),
        ]
        pygame.draw.polygon(surface, (0, 60, 0), body_points)
        pygame.draw.polygon(surface, color, body_points, 2)

        # Wings
        wing_flap = math.sin(anim * 0.4) * 15
        for side in [-1, 1]:
            wing_points = [
                (x + side * 10, y - 20),
                (x + side * 30, y - 25 - wing_flap * side),
                (x + side * 25, y - 10),
            ]
            pygame.draw.polygon(surface, (0, 40, 0), wing_points)
            pygame.draw.polygon(surface, color, wing_points, 2)

        # Skull face
        pygame.draw.ellipse(surface, (30, 50, 30), (x - 8, y - 28, 16, 12))
        # Burning eyes
        eye_flicker = random.random() * 30
        pygame.draw.circle(
            surface, (255, int(100 + eye_flicker), 0), (x - 4, y - 24), 3
        )
        pygame.draw.circle(
            surface, (255, int(100 + eye_flicker), 0), (x + 4, y - 24), 3
        )

    def _draw_wizard(self, surface, x, y, anim):
        """Draw Wizard of Wor - Eldritch Cosmic Horror."""
        color = self.color

        # Reality-warping aura
        for i in range(8):
            angle = anim * 0.05 + i * math.pi / 4
            ax = x + math.cos(angle) * 25
            ay = y - 20 + math.sin(angle) * 12
            pygame.draw.circle(surface, (*color[:3], 40), (int(ax), int(ay)), 4)

        # Void cloak
        cloak_sway = math.sin(anim * 0.1) * 3
        cloak_points = [
            (x, y - 40),
            (x + 15 + cloak_sway, y - 20),
            (x + 12, y + 5),
            (x - 12, y + 5),
            (x - 15 - cloak_sway, y - 20),
        ]
        pygame.draw.polygon(surface, (30, 0, 40), cloak_points)
        pygame.draw.polygon(surface, color, cloak_points, 2)

        # Glowing runes
        for i in range(3):
            rune_y = y - 10 - i * 10
            rune_glow = int(abs(math.sin(anim * 0.1 + i)) * 150 + 50)
            pygame.draw.circle(surface, (rune_glow, 0, rune_glow), (x, rune_y), 3)

        # Void face
        pygame.draw.ellipse(surface, BLACK, (x - 10, y - 38, 20, 15))

        # Multiple eldritch eyes
        for i in range(5):
            eye_phase = math.sin(anim * 0.15 + i * 1.2)
            if eye_phase > -0.3:
                eye_x = x + int(math.cos(i * 1.3) * 6)
                eye_y = y - 32 + int(math.sin(i * 1.7) * 4)
                eye_size = int(2 + eye_phase * 2)
                pygame.draw.circle(
                    surface, (255, 100, 255), (eye_x, eye_y), max(1, eye_size)
                )

        # Tentacles
        for t in range(6):
            base_angle = (t / 6) * math.pi * 2 + anim * 0.02
            prev = (x, y - 5)
            for seg in range(4):
                seg_angle = base_angle + math.sin(anim * 0.15 + t + seg * 0.5) * 0.5
                seg_len = 5 + seg * 3
                next_pt = (
                    prev[0] + math.cos(seg_angle) * seg_len,
                    prev[1] + math.sin(seg_angle) * seg_len * 0.5 + seg * 2,
                )
                pygame.draw.line(surface, color, prev, next_pt, 2)
                prev = next_pt
            pygame.draw.circle(surface, NEON_CYAN, (int(prev[0]), int(prev[1])), 2)

        # Staff
        staff_float = math.sin(anim * 0.12) * 2
        pygame.draw.line(
            surface,
            (100, 50, 150),
            (x + 20, y - 35 + staff_float),
            (x + 20, y + 5 + staff_float),
            3,
        )
        # Orb
        orb_pulse = abs(math.sin(anim * 0.2)) * 4
        pygame.draw.circle(
            surface, BLACK, (x + 20, int(y - 40 + staff_float)), int(8 + orb_pulse)
        )
        pygame.draw.circle(
            surface, NEON_CYAN, (x + 20, int(y - 40 + staff_float)), int(6 + orb_pulse)
        )


class Bullet(IsoSprite):
    """Plasma bullet projectile."""

    def __init__(self, grid_x, grid_y, direction, is_player=True):
        super().__init__(grid_x, grid_y)
        self.direction = direction
        self.speed = 0.25
        self.is_player = is_player
        self.color = NEON_YELLOW if is_player else NEON_RED
        self.active = True

    def update(self, maze):
        """Move bullet and check collisions."""
        self.frame += 1

        self.grid_x += self.direction[0] * self.speed
        self.grid_y += self.direction[1] * self.speed

        # Check wall collision
        test_x = int(self.grid_x + 0.5)
        test_y = int(self.grid_y + 0.5)

        if not (0 <= test_x < MAZE_WIDTH and 0 <= test_y < MAZE_HEIGHT):
            self.active = False
        elif maze[test_y][test_x] == 1:
            self.active = False

    def draw(self, surface):
        """Draw glowing bullet."""
        x, y = self.get_screen_pos()

        # Glow
        glow_surf = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*self.color[:3], 100), (10, 10), 10)
        surface.blit(glow_surf, (x - 10, y - 10), special_flags=pygame.BLEND_RGB_ADD)

        # Core
        pygame.draw.circle(surface, self.color, (int(x), int(y)), 5)
        pygame.draw.circle(surface, WHITE, (int(x), int(y)), 2)


# =============================================================================
# PARTICLE SYSTEM
# =============================================================================


class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-5, -1)
        self.color = color
        self.life = 30
        self.size = random.randint(2, 5)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.2  # Gravity
        self.life -= 1

    def draw(self, surface):
        alpha = min(255, self.life * 8)
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.size)


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def emit(self, x, y, color, count=20):
        for _ in range(count):
            self.particles.append(Particle(x, y, color))

    def update(self):
        for p in self.particles[:]:
            p.update()
            if p.life <= 0:
                self.particles.remove(p)

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)


# =============================================================================
# MAIN GAME CLASS
# =============================================================================


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Wizard of Wor - Axonometric 2.5D")
        self.clock = pygame.time.Clock()

        # Game state
        self.running = True
        self.game_over = False
        self.victory = False
        self.phase = "normal"
        self.phase_timer = 0

        # Find valid positions
        self.valid_positions = []
        for row in range(MAZE_HEIGHT):
            for col in range(MAZE_WIDTH):
                if MAZE[row][col] == 0:
                    self.valid_positions.append((col, row))

        # Create player (spawn at bottom)
        spawn_pos = None
        for pos in reversed(self.valid_positions):
            if pos[1] > MAZE_HEIGHT - 4:
                spawn_pos = pos
                break
        if not spawn_pos:
            spawn_pos = self.valid_positions[-1]

        self.player = Player(spawn_pos[0] + 0.5, spawn_pos[1] + 0.5)
        self.player_spawn = spawn_pos

        # Enemies and bullets
        self.enemies = []
        self.bullets = []
        self.particles = ParticleSystem()

        # Spawn initial enemies
        self.spawn_enemies()

        # Font
        self.font = pygame.font.Font(None, 36)
        self.big_font = pygame.font.Font(None, 72)

        # Message
        self.message = "WELCOME TO THE DUNGEON OF WOR!"
        self.message_timer = 120

        # Load sounds
        self.load_sounds()

    def load_sounds(self):
        """Load sound effects."""
        self.sounds = {}
        # Map logical sound names to new asset filenames
        sound_mapping = {
            "player_shot": "player-fire",
            "enemy_shot": "enemy-fire",
            "enemy_death": "enemy-dead",
            "player_death": "player-dead",
            "game_over": "gameover",
            "level_complete": "doublescore",
            "get_ready": "getready",
            "player_enters": "player-enters",
            "enemy_visible": "enemy-visible",
            "maze_exit": "maze-exit",
            "worluk_appear": "worluk",
            "worluk_dead": "worluk-dead",
            "worluk_escape": "worluk-escape",
            "wizard_dead": "wizard-dead",
            "wizard_escape": "wizard-escape",
            "loop1": "loop01",
            "loop2": "loop02",
            "loop3": "loop03",
            "loop4": "loop04",
            "loop5": "loop05",
        }
        for name, filename in sound_mapping.items():
            try:
                self.sounds[name] = pygame.mixer.Sound(f"assets/sounds/{filename}.wav")
                self.sounds[name].set_volume(0.5)
            except Exception as e:
                print(f"Could not load sound {filename}: {e}")

    def play_sound(self, name):
        if name in self.sounds:
            self.sounds[name].play()

    def spawn_enemies(self):
        """Spawn enemies for current phase."""
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
                self.enemies.append(Enemy(pos[0] + 0.5, pos[1] + 0.5, enemy_type))

        elif self.phase == "worluk":
            pos = random.choice(self.valid_positions)
            self.enemies.append(Enemy(pos[0] + 0.5, pos[1] + 0.5, "worluk"))
            self.message = "THE WORLUK APPEARS!"
            self.message_timer = 90
            self.play_sound("worluk_appear")

        elif self.phase == "wizard":
            pos = random.choice(self.valid_positions)
            self.enemies.append(Enemy(pos[0] + 0.5, pos[1] + 0.5, "wizard"))
            self.message = "I AM THE WIZARD OF WOR!"
            self.message_timer = 120
            self.play_sound("loop5")  # Dramatic sound for wizard

    def handle_input(self):
        """Handle player input."""
        keys = pygame.key.get_pressed()

        dx, dy = 0, 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -1
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = 1
        elif keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -1
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = 1

        self.player.move(dx, dy, MAZE)

        # Shooting
        if keys[pygame.K_SPACE] and self.player.shoot_cooldown <= 0:
            self.bullets.append(
                Bullet(
                    self.player.grid_x, self.player.grid_y, self.player.direction, True
                )
            )
            self.player.shoot_cooldown = 15
            self.play_sound("player_shot")

        if self.player.shoot_cooldown > 0:
            self.player.shoot_cooldown -= 1

    def update(self):
        """Update game logic."""
        if self.game_over or self.victory:
            return

        # Update enemies
        for enemy in self.enemies:
            enemy.update(MAZE, self.player)

            # Play sound when Garwor decloaks
            if enemy.just_became_visible:
                self.play_sound("enemy_visible")
                enemy.just_became_visible = False

            # Enemy shooting
            if random.random() < 0.005:
                dx = self.player.grid_x - enemy.grid_x
                dy = self.player.grid_y - enemy.grid_y
                if abs(dx) > abs(dy):
                    direction = (1 if dx > 0 else -1, 0)
                else:
                    direction = (0, 1 if dy > 0 else -1)
                self.bullets.append(
                    Bullet(enemy.grid_x, enemy.grid_y, direction, False)
                )

        # Update bullets
        for bullet in self.bullets[:]:
            bullet.update(MAZE)
            if not bullet.active:
                self.bullets.remove(bullet)
                continue

            # Check collisions
            if bullet.is_player:
                for enemy in self.enemies[:]:
                    if (
                        abs(bullet.grid_x - enemy.grid_x) < 0.6
                        and abs(bullet.grid_y - enemy.grid_y) < 0.6
                    ):
                        enemy.health -= 1
                        if enemy.health <= 0:
                            self.player.score += enemy.points
                            sx, sy = enemy.get_screen_pos()
                            self.particles.emit(sx, sy, enemy.color, 25)
                            self.enemies.remove(enemy)
                            # Play appropriate death sound based on enemy type
                            if enemy.enemy_type == "worluk":
                                self.play_sound("worluk_dead")
                            elif enemy.enemy_type == "wizard":
                                self.play_sound("wizard_dead")
                            else:
                                self.play_sound("enemy_death")
                        if bullet in self.bullets:
                            self.bullets.remove(bullet)
                        break
            else:
                # Enemy bullet hitting player
                if (
                    abs(bullet.grid_x - self.player.grid_x) < 0.5
                    and abs(bullet.grid_y - self.player.grid_y) < 0.5
                ):
                    self.player_hit()
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)

        # Player-enemy collision
        for enemy in self.enemies:
            if (
                abs(enemy.grid_x - self.player.grid_x) < 0.6
                and abs(enemy.grid_y - self.player.grid_y) < 0.6
            ):
                self.player_hit()
                break

        # Particles
        self.particles.update()

        # Phase management
        if len(self.enemies) == 0:
            self.phase_timer += 1
            if self.phase == "normal" and self.phase_timer >= 60:
                self.phase = "worluk"
                self.phase_timer = 0
                self.spawn_enemies()
            elif self.phase == "worluk" and self.phase_timer >= 60:
                self.phase = "wizard"
                self.phase_timer = 0
                self.spawn_enemies()
            elif self.phase == "wizard" and self.phase_timer >= 30:
                self.victory = True
                self.message = "DUNGEON CLEARED!"
                self.message_timer = 999
                self.play_sound("level_complete")

        # Message timer
        if self.message_timer > 0:
            self.message_timer -= 1

    def player_hit(self):
        """Handle player getting hit."""
        self.player.lives -= 1
        sx, sy = self.player.get_screen_pos()
        self.particles.emit(sx, sy, NEON_YELLOW, 30)
        self.play_sound("player_death")

        if self.player.lives <= 0:
            self.game_over = True
            self.message = "GAME OVER"
            self.message_timer = 999
            self.play_sound("game_over")
        else:
            self.player.grid_x = self.player_spawn[0] + 0.5
            self.player.grid_y = self.player_spawn[1] + 0.5
            self.message = "PREPARE YOURSELF!"
            self.message_timer = 60

    def draw(self):
        """Render the game."""
        self.screen.fill(DARK_BLUE)

        # Collect all drawable objects for depth sorting
        drawables = []

        # Draw floor tiles and collect walls
        for row in range(MAZE_HEIGHT):
            for col in range(MAZE_WIDTH):
                if MAZE[row][col] == 0:
                    IsometricRenderer.draw_floor_tile(
                        self.screen, col, row, DARK_BLUE, NEON_BLUE
                    )
                else:
                    drawables.append(("wall", col, row, get_rotated_depth(col, row)))

        # Add sprites
        drawables.append(
            (
                "player",
                self.player,
                get_rotated_depth(self.player.grid_x, self.player.grid_y),
            )
        )

        for enemy in self.enemies:
            drawables.append(
                ("enemy", enemy, get_rotated_depth(enemy.grid_x, enemy.grid_y))
            )

        for bullet in self.bullets:
            drawables.append(
                ("bullet", bullet, get_rotated_depth(bullet.grid_x, bullet.grid_y))
            )

        # Sort by depth
        drawables.sort(key=lambda x: x[-1])

        # Draw in order
        for item in drawables:
            if item[0] == "wall":
                IsometricRenderer.draw_wall_block(self.screen, item[1], item[2])
            elif item[0] == "player":
                item[1].draw(self.screen)
            elif item[0] == "enemy":
                item[1].draw(self.screen)
            elif item[0] == "bullet":
                item[1].draw(self.screen)

        # Draw particles
        self.particles.draw(self.screen)

        # HUD
        self.draw_hud()

        pygame.display.flip()

    def draw_hud(self):
        """Draw heads-up display."""
        # Score
        score_text = self.font.render(f"SCORE: {self.player.score}", True, NEON_YELLOW)
        self.screen.blit(score_text, (20, 20))

        # Lives
        lives_text = self.font.render(f"LIVES: {self.player.lives}", True, NEON_GREEN)
        self.screen.blit(lives_text, (20, 50))

        # Enemies
        enemies_text = self.font.render(f"ENEMIES: {len(self.enemies)}", True, NEON_RED)
        self.screen.blit(enemies_text, (SCREEN_WIDTH - 180, 20))

        # Phase
        phase_text = self.font.render(f"PHASE: {self.phase.upper()}", True, NEON_PURPLE)
        self.screen.blit(phase_text, (SCREEN_WIDTH - 180, 50))

        # Camera info
        angle_deg = int(math.degrees(Camera.angle) % 360)
        zoom_pct = int(Camera.zoom * 100)
        camera_text = self.font.render(
            f"VIEW: {angle_deg}° ZOOM: {zoom_pct}%", True, NEON_CYAN
        )
        self.screen.blit(camera_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 40))

        # Camera controls hint
        hint_text = pygame.font.Font(None, 24).render(
            "Drag to rotate | Scroll to zoom | M to reset", True, (100, 100, 150)
        )
        self.screen.blit(hint_text, (SCREEN_WIDTH // 2 - 140, SCREEN_HEIGHT - 20))

        # Message
        if self.message_timer > 0:
            msg_surface = self.big_font.render(self.message, True, NEON_CYAN)
            msg_rect = msg_surface.get_rect(center=(SCREEN_WIDTH // 2, 60))
            self.screen.blit(msg_surface, msg_rect)

        # Game over / Victory overlay
        if self.game_over or self.victory:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            self.screen.blit(overlay, (0, 0))

            text = "GAME OVER" if self.game_over else "VICTORY!"
            color = NEON_RED if self.game_over else NEON_GREEN
            text_surface = self.big_font.render(text, True, color)
            text_rect = text_surface.get_rect(
                center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40)
            )
            self.screen.blit(text_surface, text_rect)

            score_surface = self.font.render(
                f"Final Score: {self.player.score}", True, WHITE
            )
            score_rect = score_surface.get_rect(
                center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20)
            )
            self.screen.blit(score_surface, score_rect)

            restart_surface = self.font.render("Press R to Restart", True, NEON_CYAN)
            restart_rect = restart_surface.get_rect(
                center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60)
            )
            self.screen.blit(restart_surface, restart_rect)

    def run(self):
        """Main game loop."""
        self.play_sound("get_ready")
        self.play_sound("player_enters")

        # Track mouse for camera rotation
        last_mouse_x = None
        dragging = False

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_r and (self.game_over or self.victory):
                        self.__init__()
                    elif event.key == pygame.K_m:
                        # Reset camera with M key
                        Camera.reset()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click - start drag
                        dragging = True
                        last_mouse_x = event.pos[0]
                    elif event.button == 2:  # Middle click - reset camera
                        Camera.reset()
                    elif event.button == 4:  # Scroll up - zoom in
                        Camera.target_zoom = min(2.0, Camera.target_zoom + 0.1)
                    elif event.button == 5:  # Scroll down - zoom out
                        Camera.target_zoom = max(0.5, Camera.target_zoom - 0.1)
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        dragging = False
                        last_mouse_x = None
                elif event.type == pygame.MOUSEMOTION:
                    if dragging and last_mouse_x is not None:
                        # Rotate camera based on mouse drag
                        dx = event.pos[0] - last_mouse_x
                        Camera.target_angle += dx * 0.005
                        last_mouse_x = event.pos[0]
                elif event.type == pygame.MOUSEWHEEL:
                    # Mouse wheel zoom (alternative)
                    Camera.target_zoom = max(
                        0.5, min(2.0, Camera.target_zoom + event.y * 0.1)
                    )

            # Update camera smoothly
            Camera.update()

            self.handle_input()
            self.update()
            self.draw()

            self.clock.tick(60)

        pygame.quit()


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("WIZARD OF WOR - AXONOMETRIC 2.5D")
    print("=" * 50)
    print("Controls:")
    print("  Arrow Keys / WASD - Move")
    print("  Space - Shoot")
    print("  Mouse Drag - Rotate camera view")
    print("  Mouse Wheel - Zoom in/out")
    print("  M / Middle Click - Reset camera")
    print("  R - Restart (after game over)")
    print("  ESC - Quit")
    print("=" * 50 + "\n")

    game = Game()
    game.run()
