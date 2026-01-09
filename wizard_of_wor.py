#!/usr/bin/env python3
"""
Wizard of Wor - Neon CRT Revival Edition
A modernized retro clone with glowing vector aesthetics and CRT effects.
Controls: Arrow keys to move, Space to shoot, R to restart, ESC to quit
"""

import math
import random

import pygame

# Initialize Pygame
pygame.init()

# Constants
TILE_SIZE = 41
MAZE_WIDTH = 21
MAZE_HEIGHT = 15
GAME_WIDTH = MAZE_WIDTH * TILE_SIZE
GAME_HEIGHT = MAZE_HEIGHT * TILE_SIZE
HUD_HEIGHT = 80
RADAR_HEIGHT = 60
SCREEN_WIDTH = GAME_WIDTH
SCREEN_HEIGHT = GAME_HEIGHT + HUD_HEIGHT + RADAR_HEIGHT

# Speed settings
ENEMY_SPEED_MULTIPLIER = 0.3  # Adjust this to make enemies faster (>1) or slower (<1)

# Colors - Neon Palette
BLACK = (0, 0, 0)
DARK_BLUE = (0, 0, 20)
NEON_BLUE = (0, 150, 255)
NEON_CYAN = (0, 255, 255)
NEON_YELLOW = (255, 255, 0)
NEON_RED = (255, 50, 50)
NEON_ORANGE = (255, 150, 0)
NEON_PURPLE = (200, 0, 255)
NEON_GREEN = (0, 255, 100)
NEON_PINK = (255, 100, 200)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)

# Maze layout (1 = wall, 0 = path)
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

# Pre-compute wall rectangles for fast collision detection
WALL_RECTS = []
for row in range(MAZE_HEIGHT):
    for col in range(MAZE_WIDTH):
        if MAZE[row][col] == 1:
            WALL_RECTS.append(
                pygame.Rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            )


def fast_wall_collision(rect):
    """Fast collision check against pre-computed wall rectangles."""
    return rect.collidelist(WALL_RECTS) != -1


class PostProcessor:
    """Handles CRT-style post-processing effects."""

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.scanline_surface = self.create_scanlines()
        self.time = 0

    def create_scanlines(self):
        """Create scanline overlay."""
        surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for y in range(0, self.height, 3):
            pygame.draw.line(surface, (0, 0, 0, 60), (0, y), (self.width, y))
        return surface

    def apply_bloom(self, surface, intensity=0.3):
        """Apply bloom effect by blurring bright areas."""
        # Simple bloom: scale down, blur, scale up, blend
        small = pygame.transform.smoothscale(
            surface, (self.width // 4, self.height // 4)
        )
        bloomed = pygame.transform.smoothscale(small, (self.width, self.height))
        bloomed.set_alpha(int(255 * intensity))
        surface.blit(bloomed, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        return surface

    def apply_chromatic_aberration(self, surface, offset=2):
        """Apply chromatic aberration effect."""
        result = pygame.Surface((self.width, self.height))
        result.fill(BLACK)

        # Extract and offset color channels
        r_surface = surface.copy()
        b_surface = surface.copy()

        # Tint surfaces
        r_surface.fill((255, 0, 0), special_flags=pygame.BLEND_RGB_MULT)
        b_surface.fill((0, 0, 255), special_flags=pygame.BLEND_RGB_MULT)

        # Offset and blend
        result.blit(r_surface, (-offset, 0), special_flags=pygame.BLEND_RGB_ADD)
        result.blit(surface, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        result.blit(b_surface, (offset, 0), special_flags=pygame.BLEND_RGB_ADD)

        return result

    def apply_scanlines(self, surface):
        """Apply scanline effect."""
        surface.blit(self.scanline_surface, (0, 0))
        return surface

    def apply_vignette(self, surface):
        """Apply vignette effect (darker corners)."""
        vignette = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        center = (self.width // 2, self.height // 2)
        max_dist = math.sqrt(center[0] ** 2 + center[1] ** 2)

        for ring in range(0, int(max_dist), 20):
            alpha = int((ring / max_dist) ** 2 * 100)
            pygame.draw.circle(
                vignette, (0, 0, 0, alpha), center, int(max_dist - ring), 20
            )

        surface.blit(vignette, (0, 0))
        return surface

    def process(self, surface):
        """Apply post-processing effects."""
        result = self.apply_chromatic_aberration(surface, 1)
        result = self.apply_scanlines(result)
        return result


class ParticleSystem:
    """Manages particle effects for explosions and trails."""

    def __init__(self):
        self.particles = []

    def emit_explosion(self, x, y, color, count=20):
        """Create explosion particles."""
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 8)
            self.particles.append(
                {
                    "x": x,
                    "y": y,
                    "vx": math.cos(angle) * speed,
                    "vy": math.sin(angle) * speed,
                    "color": color,
                    "life": random.randint(20, 40),
                    "size": random.randint(2, 5),
                    "type": "explosion",
                }
            )

    def emit_trail(self, x, y, color):
        """Create bullet trail particle."""
        self.particles.append(
            {
                "x": x + random.uniform(-2, 2),
                "y": y + random.uniform(-2, 2),
                "vx": random.uniform(-0.5, 0.5),
                "vy": random.uniform(-0.5, 0.5),
                "color": color,
                "life": 10,
                "size": 3,
                "type": "trail",
            }
        )

    def emit_spawn(self, x, y, color):
        """Create spawn effect particles."""
        for i in range(15):
            angle = (i / 15) * math.pi * 2
            self.particles.append(
                {
                    "x": x,
                    "y": y,
                    "vx": math.cos(angle) * 3,
                    "vy": math.sin(angle) * 3,
                    "color": color,
                    "life": 30,
                    "size": 4,
                    "type": "spawn",
                }
            )

    def update(self):
        """Update all particles."""
        for p in self.particles[:]:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["life"] -= 1
            p["vx"] *= 0.95
            p["vy"] *= 0.95

            if p["life"] <= 0:
                self.particles.remove(p)

    def draw(self, surface):
        """Draw all particles with glow."""
        for p in self.particles:
            alpha = min(255, p["life"] * 8)
            color = (*p["color"][:3], alpha) if len(p["color"]) == 3 else p["color"]

            # Glow
            glow_size = p["size"] * 2
            glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(
                glow_surf,
                (*p["color"][:3], alpha // 3),
                (glow_size, glow_size),
                glow_size,
            )
            surface.blit(
                glow_surf,
                (int(p["x"] - glow_size), int(p["y"] - glow_size)),
                special_flags=pygame.BLEND_RGB_ADD,
            )

            # Core
            pygame.draw.circle(
                surface, p["color"][:3], (int(p["x"]), int(p["y"])), p["size"]
            )


class SpriteRenderer:
    """Renders game sprites with glow effects."""

    @staticmethod
    def draw_glow_rect(surface, color, rect, glow_radius=4):
        """Draw a rectangle with glow effect."""
        # Outer glow
        glow_color = (*color[:3], 50)
        glow_rect = rect.inflate(glow_radius * 2, glow_radius * 2)
        glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, glow_color, glow_surf.get_rect(), border_radius=2)
        surface.blit(glow_surf, glow_rect.topleft, special_flags=pygame.BLEND_RGB_ADD)

        # Core
        pygame.draw.rect(surface, color, rect)

    @staticmethod
    def draw_glow_line(surface, color, start, end, width=2, glow_radius=3):
        """Draw a line with glow effect."""
        # Glow layers
        for i in range(glow_radius, 0, -1):
            alpha = 100 // i
            glow_color = (*color[:3], alpha)
            temp = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            pygame.draw.line(temp, glow_color, start, end, width + i * 2)
            surface.blit(temp, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

        # Core line
        pygame.draw.line(surface, color, start, end, width)

    @staticmethod
    def draw_player(surface, x, y, direction, frame, color=NEON_YELLOW):
        """Draw the Space Marine / Astronaut Soldier."""
        cx, cy = x + TILE_SIZE // 2, y + TILE_SIZE // 2
        walk_bob = math.sin(frame * 0.3) * 2 if direction != (0, 0) else 0

        # Legs (armored boots)
        leg_y = y + TILE_SIZE - 10
        leg_offset = int(math.sin(frame * 0.4) * 3) if direction != (0, 0) else 0
        pygame.draw.rect(surface, (80, 80, 100), (x + 8 - leg_offset, leg_y, 6, 10))
        pygame.draw.rect(
            surface, (80, 80, 100), (x + TILE_SIZE - 14 + leg_offset, leg_y, 6, 10)
        )
        # Boot glow trim
        pygame.draw.line(
            surface,
            color,
            (x + 8 - leg_offset, leg_y + 9),
            (x + 14 - leg_offset, leg_y + 9),
            2,
        )
        pygame.draw.line(
            surface,
            color,
            (x + TILE_SIZE - 14 + leg_offset, leg_y + 9),
            (x + TILE_SIZE - 8 + leg_offset, leg_y + 9),
            2,
        )

        # Body armor (power suit torso)
        body_rect = pygame.Rect(
            x + 6, y + 10 + int(walk_bob), TILE_SIZE - 12, TILE_SIZE - 18
        )
        pygame.draw.rect(surface, (60, 60, 80), body_rect)
        # Armor chest plate glow lines
        pygame.draw.line(
            surface,
            color,
            (x + 8, y + 12 + int(walk_bob)),
            (x + 8, y + 24 + int(walk_bob)),
            2,
        )
        pygame.draw.line(
            surface,
            color,
            (x + TILE_SIZE - 8, y + 12 + int(walk_bob)),
            (x + TILE_SIZE - 8, y + 24 + int(walk_bob)),
            2,
        )
        pygame.draw.line(
            surface,
            color,
            (x + 10, y + 18 + int(walk_bob)),
            (x + TILE_SIZE - 10, y + 18 + int(walk_bob)),
            1,
        )
        # Backpack/life support
        pygame.draw.rect(
            surface, (50, 50, 70), (x + TILE_SIZE - 10, y + 14 + int(walk_bob), 6, 12)
        )
        pygame.draw.circle(
            surface, NEON_CYAN, (x + TILE_SIZE - 7, y + 17 + int(walk_bob)), 2
        )  # oxygen indicator

        # Helmet (rounded space helmet)
        helmet_rect = pygame.Rect(x + 8, y + 2 + int(walk_bob), TILE_SIZE - 16, 14)
        pygame.draw.ellipse(surface, (70, 70, 90), helmet_rect)
        # Visor (glowing cyan)
        visor_rect = pygame.Rect(x + 10, y + 5 + int(walk_bob), TILE_SIZE - 20, 8)
        pygame.draw.ellipse(surface, NEON_CYAN, visor_rect)
        # Visor reflection
        pygame.draw.arc(
            surface, WHITE, (x + 11, y + 5 + int(walk_bob), 8, 6), 0.5, 2.5, 1
        )
        # Antenna
        pygame.draw.line(
            surface,
            color,
            (x + TILE_SIZE - 12, y + 2 + int(walk_bob)),
            (x + TILE_SIZE - 8, y - 4 + int(walk_bob)),
            2,
        )
        pygame.draw.circle(
            surface, NEON_RED, (x + TILE_SIZE - 8, y - 4 + int(walk_bob)), 2
        )

        # Arm with plasma rifle
        arm_x = cx + direction[0] * 4
        arm_y = cy + direction[1] * 4 + int(walk_bob)
        # Shoulder pad
        pygame.draw.circle(
            surface,
            (80, 80, 100),
            (x + 8 if direction[0] <= 0 else x + TILE_SIZE - 8, y + 14 + int(walk_bob)),
            4,
        )

        # Plasma rifle
        gun_x = cx + direction[0] * 16
        gun_y = cy + direction[1] * 16
        # Gun body
        SpriteRenderer.draw_glow_line(
            surface, (100, 100, 120), (arm_x, arm_y), (gun_x, gun_y), 4, 1
        )
        # Gun barrel glow
        SpriteRenderer.draw_glow_line(
            surface,
            color,
            (arm_x + direction[0] * 6, arm_y + direction[1] * 6),
            (gun_x, gun_y),
            2,
            2,
        )
        # Muzzle energy glow
        muzzle_pulse = abs(math.sin(frame * 0.2)) * 2
        pygame.draw.circle(
            surface, color, (int(gun_x), int(gun_y)), int(3 + muzzle_pulse)
        )
        pygame.draw.circle(surface, WHITE, (int(gun_x), int(gun_y)), 2)

    @staticmethod
    def draw_burwor(surface, x, y, direction, frame, visible=True):
        """Draw Burwor - Alien Crawler Beast with mandibles."""
        if not visible:
            return

        cx, cy = x + TILE_SIZE // 2, y + TILE_SIZE // 2
        color = NEON_BLUE
        pulse = abs(math.sin(frame * 0.15)) * 0.3 + 0.7

        # Segmented body (insectoid alien)
        for i in range(3):
            seg_y = y + 8 + i * 8
            seg_width = TILE_SIZE - 10 - i * 2
            seg_x = x + (TILE_SIZE - seg_width) // 2
            seg_color = tuple(int(c * (1 - i * 0.15)) for c in color[:3])
            pygame.draw.ellipse(surface, seg_color, (seg_x, seg_y, seg_width, 10))

        # Slimy glow trail
        for i in range(3):
            trail_alpha = 80 - i * 25
            pygame.draw.circle(
                surface,
                (*color[:3], trail_alpha),
                (cx - direction[0] * (i + 1) * 6, cy - direction[1] * (i + 1) * 4),
                4 - i,
            )

        # Alien head with carapace
        head_rect = pygame.Rect(x + 6, y + 2, TILE_SIZE - 12, 12)
        pygame.draw.ellipse(surface, color, head_rect)
        # Carapace ridges
        for i in range(3):
            ridge_y = y + 4 + i * 3
            pygame.draw.line(
                surface,
                (*color[:3],),
                (x + 10, ridge_y),
                (x + TILE_SIZE - 10, ridge_y),
                1,
            )

        # Multiple alien eyes (6 eyes in 2 rows)
        eye_glow = int(pulse * 255)
        for row in range(2):
            for i in range(3):
                eye_x = x + 10 + i * 6
                eye_y = y + 6 + row * 4
                pygame.draw.circle(surface, (eye_glow, 50, 50), (eye_x, eye_y), 2)
                pygame.draw.circle(surface, WHITE, (eye_x, eye_y), 1)

        # Mandibles (snapping animation)
        mandible_open = abs(math.sin(frame * 0.3)) * 4
        pygame.draw.line(
            surface, NEON_RED, (x + 8, y + 14), (x + 4 - int(mandible_open), y + 20), 3
        )
        pygame.draw.line(
            surface,
            NEON_RED,
            (x + TILE_SIZE - 8, y + 14),
            (x + TILE_SIZE - 4 + int(mandible_open), y + 20),
            3,
        )
        # Dripping saliva
        if frame % 20 < 10:
            pygame.draw.line(surface, (100, 200, 100), (cx, y + 18), (cx, y + 22), 1)

        # Skittering legs
        leg_anim = math.sin(frame * 0.5) * 3
        for side in [-1, 1]:
            for i in range(3):
                leg_x = cx + side * 12
                leg_y = y + 10 + i * 6
                leg_end_x = leg_x + side * (
                    8 + int(leg_anim if i % 2 == 0 else -leg_anim)
                )
                leg_end_y = leg_y + 4
                pygame.draw.line(
                    surface, color, (leg_x, leg_y), (leg_end_x, leg_end_y), 2
                )

    @staticmethod
    def draw_garwor(surface, x, y, direction, frame, visible=True):
        """Draw Garwor - Cloaking Alien Predator with thermal vision."""
        cx, cy = x + TILE_SIZE // 2, y + TILE_SIZE // 2
        color = NEON_ORANGE

        if not visible:
            # Predator-style cloaking shimmer
            shimmer = math.sin(frame * 0.3) * 20 + 40
            # Distortion outline
            for i in range(8):
                angle = frame * 0.1 + i * 0.8
                sx = cx + math.cos(angle) * 12
                sy = cy + math.sin(angle) * 12
                pygame.draw.circle(
                    surface, (*color[:3], int(shimmer)), (int(sx), int(sy)), 2
                )
            # Heat signature eyes only
            pygame.draw.circle(surface, (255, 100, 0, 100), (x + 12, y + 10), 3)
            pygame.draw.circle(
                surface, (255, 100, 0, 100), (x + TILE_SIZE - 12, y + 10), 3
            )
            return

        # Sleek predator body
        body_points = [
            (cx, y + 4),  # Head top
            (x + TILE_SIZE - 6, y + 12),  # Right shoulder
            (x + TILE_SIZE - 4, cy + 8),  # Right hip
            (cx, y + TILE_SIZE - 2),  # Bottom
            (x + 4, cy + 8),  # Left hip
            (x + 6, y + 12),  # Left shoulder
        ]
        pygame.draw.polygon(surface, (60, 40, 20), body_points)
        # Bio-luminescent stripes
        for i in range(3):
            stripe_y = y + 14 + i * 6
            pygame.draw.line(
                surface, color, (x + 10, stripe_y), (x + TILE_SIZE - 10, stripe_y), 2
            )

        # Elongated predator skull
        pygame.draw.ellipse(surface, (80, 50, 30), (x + 8, y + 2, TILE_SIZE - 16, 14))
        # Dreadlock-like tendrils
        for i in range(4):
            tendril_x = x + 10 + i * 5
            sway = math.sin(frame * 0.2 + i) * 3
            pygame.draw.line(
                surface,
                (60, 40, 30),
                (tendril_x, y + 14),
                (tendril_x + sway, y + 24),
                2,
            )

        # Infrared hunter eyes
        eye_pulse = abs(math.sin(frame * 0.15)) * 50 + 200
        pygame.draw.ellipse(surface, BLACK, (x + 10, y + 6, 8, 5))
        pygame.draw.ellipse(surface, BLACK, (x + TILE_SIZE - 18, y + 6, 8, 5))
        pygame.draw.circle(
            surface, (int(eye_pulse), 100, 0), (x + 14 + direction[0], y + 8), 2
        )
        pygame.draw.circle(
            surface,
            (int(eye_pulse), 100, 0),
            (x + TILE_SIZE - 14 + direction[0], y + 8),
            2,
        )

        # Fanged mouth
        pygame.draw.line(
            surface, (40, 40, 40), (x + 12, y + 14), (x + TILE_SIZE - 12, y + 14), 1
        )
        for i in range(4):
            fang_x = x + 12 + i * 5
            pygame.draw.line(surface, WHITE, (fang_x, y + 14), (fang_x, y + 17), 1)

        # Clawed arms
        claw_anim = math.sin(frame * 0.4) * 2
        for side in [-1, 1]:
            arm_x = cx + side * 14
            pygame.draw.line(
                surface,
                color,
                (arm_x, y + 16),
                (arm_x + side * 6, y + 22 + claw_anim),
                2,
            )
            # Three claws
            for c in range(3):
                claw_end = arm_x + side * (8 + c * 2)
                pygame.draw.line(
                    surface,
                    NEON_RED,
                    (arm_x + side * 6, y + 22 + claw_anim),
                    (claw_end, y + 26 + claw_anim + c),
                    1,
                )

    @staticmethod
    def draw_thorwor(surface, x, y, direction, frame, visible=True):
        """Draw Thorwor - Armored Xenomorph Scorpion Terror."""
        if not visible:
            return

        cx, cy = x + TILE_SIZE // 2, y + TILE_SIZE // 2
        color = NEON_RED
        pulse = abs(math.sin(frame * 0.1))

        # Armored exoskeleton body segments
        for i in range(4):
            seg_y = y + 6 + i * 6
            seg_width = TILE_SIZE - 8 - abs(i - 1.5) * 2
            seg_x = x + (TILE_SIZE - seg_width) // 2
            armor_color = tuple(int(c * (0.6 + i * 0.1)) for c in color[:3])
            pygame.draw.ellipse(surface, armor_color, (seg_x, seg_y, seg_width, 8))
            # Armor plate shine
            pygame.draw.arc(
                surface,
                (255, 150, 150),
                (seg_x + 2, seg_y, seg_width - 4, 6),
                0.5,
                2.5,
                1,
            )

        # Alien head with elongated skull
        head_points = [
            (cx - 8, y + 8),
            (cx, y - 2),  # Elongated top
            (cx + 8, y + 8),
            (cx, y + 12),
        ]
        pygame.draw.polygon(surface, (40, 0, 0), head_points)
        pygame.draw.polygon(surface, color, head_points, 2)

        # Compound eyes (spider-like arrangement)
        eye_positions = [
            (cx - 6, y + 4),
            (cx, y + 2),
            (cx + 6, y + 4),
            (cx - 4, y + 7),
            (cx + 4, y + 7),
        ]
        for ex, ey in eye_positions:
            pygame.draw.circle(surface, (100, 0, 50), (ex, ey), 2)
            pygame.draw.circle(surface, (255, int(pulse * 100), 255), (ex, ey), 1)

        # Massive crushing pincers
        pincer_snap = math.sin(frame * 0.25) * 3
        for side in [-1, 1]:
            pincer_base = (x + (TILE_SIZE // 2) + side * 10, y + 10)
            pincer_claw1 = (pincer_base[0] + side * (10 + pincer_snap), y + 6)
            pincer_claw2 = (pincer_base[0] + side * (10 + pincer_snap), y + 14)
            pygame.draw.line(surface, color, pincer_base, pincer_claw1, 3)
            pygame.draw.line(surface, color, pincer_base, pincer_claw2, 3)
            # Pincer tips
            pygame.draw.circle(surface, NEON_YELLOW, pincer_claw1, 2)
            pygame.draw.circle(surface, NEON_YELLOW, pincer_claw2, 2)

        # Segmented stinger tail (curving over body)
        tail_segments = 5
        tail_curve = math.sin(frame * 0.15) * 0.3
        prev_point = (cx, y + TILE_SIZE - 6)
        for i in range(tail_segments):
            angle = -math.pi / 2 + (i / tail_segments) * math.pi * 0.8 + tail_curve
            dist = 6 + i * 3
            next_point = (
                cx + math.cos(angle) * dist * 0.3,
                y + TILE_SIZE - 6 - math.sin(angle) * dist,
            )
            seg_color = tuple(int(c * (1 - i * 0.1)) for c in color[:3])
            pygame.draw.line(
                surface,
                seg_color,
                prev_point,
                (int(next_point[0]), int(next_point[1])),
                3 - i // 2,
            )
            prev_point = next_point
        # Venomous stinger tip
        stinger_glow = int(pulse * 100 + 155)
        pygame.draw.circle(
            surface,
            (stinger_glow, stinger_glow, 0),
            (int(prev_point[0]), int(prev_point[1])),
            4,
        )
        pygame.draw.circle(surface, WHITE, (int(prev_point[0]), int(prev_point[1])), 2)
        # Dripping venom
        if frame % 30 < 15:
            venom_y = int(prev_point[1]) + (frame % 15)
            pygame.draw.circle(surface, NEON_GREEN, (int(prev_point[0]), venom_y), 1)

        # Scuttling legs
        leg_anim = math.sin(frame * 0.6) * 4
        for side in [-1, 1]:
            for i in range(4):
                leg_y = y + 8 + i * 5
                leg_offset = leg_anim if i % 2 == 0 else -leg_anim
                leg_end = (x + (TILE_SIZE // 2) + side * (18 + leg_offset), leg_y + 3)
                pygame.draw.line(
                    surface, (100, 0, 0), (cx + side * 6, leg_y), leg_end, 2
                )

    @staticmethod
    def draw_worluk(surface, x, y, direction, frame):
        """Draw Worluk - Flying Demon Wraith of the Void."""
        cx, cy = x + TILE_SIZE // 2, y + TILE_SIZE // 2
        color = NEON_GREEN
        hover = math.sin(frame * 0.1) * 3

        # Ghostly aura trail
        for i in range(5):
            trail_alpha = 60 - i * 12
            trail_y = cy + i * 4
            pygame.draw.circle(
                surface, (*color[:3], trail_alpha), (cx, int(trail_y)), 8 - i
            )

        # Ethereal body (semi-transparent demonic form)
        body_points = [
            (cx, y + 4 + hover),  # Head
            (x + TILE_SIZE - 6, y + 14 + hover),
            (x + TILE_SIZE - 8, y + TILE_SIZE - 4 + hover),
            (cx + 4, y + TILE_SIZE + 2 + hover),  # Tattered bottom
            (cx - 4, y + TILE_SIZE + 2 + hover),
            (x + 8, y + TILE_SIZE - 4 + hover),
            (x + 6, y + 14 + hover),
        ]
        pygame.draw.polygon(surface, (0, 60, 0), body_points)
        pygame.draw.polygon(surface, color, body_points, 2)

        # Tattered cape/wings (membranous)
        wing_flap = math.sin(frame * 0.4) * 8
        for side in [-1, 1]:
            wing_points = [
                (cx + side * 8, y + 10 + hover),
                (x + side * (TILE_SIZE // 2 + 16), y + 6 + hover - wing_flap * side),
                (x + side * (TILE_SIZE // 2 + 14), cy + hover),
                (
                    x + side * (TILE_SIZE // 2 + 18),
                    cy + 10 + hover + wing_flap * side * 0.5,
                ),
                (cx + side * 6, y + TILE_SIZE - 8 + hover),
            ]
            # Wing membrane
            pygame.draw.polygon(surface, (0, 40, 0), wing_points)
            # Wing bones
            pygame.draw.lines(surface, color, False, wing_points, 2)
            # Wing veins
            for i in range(3):
                vein_start = (cx + side * 8, y + 12 + i * 6 + hover)
                vein_end = (wing_points[1][0] - side * i * 4, wing_points[1][1] + i * 6)
                pygame.draw.line(
                    surface,
                    (0, 80, 0),
                    vein_start,
                    (int(vein_end[0]), int(vein_end[1])),
                    1,
                )

        # Skull face
        skull_rect = pygame.Rect(x + 10, y + 4 + hover, TILE_SIZE - 20, 12)
        pygame.draw.ellipse(surface, (20, 40, 20), skull_rect)
        # Hollow eye sockets with burning eyes
        eye_flicker = random.random() * 30
        pygame.draw.ellipse(surface, BLACK, (x + 12, y + 6 + hover, 6, 5))
        pygame.draw.ellipse(surface, BLACK, (x + TILE_SIZE - 18, y + 6 + hover, 6, 5))
        pygame.draw.circle(
            surface, (255, int(100 + eye_flicker), 0), (x + 15, y + 8 + hover), 2
        )
        pygame.draw.circle(
            surface,
            (255, int(100 + eye_flicker), 0),
            (x + TILE_SIZE - 15, y + 8 + hover),
            2,
        )
        # Skull nose hole
        pygame.draw.polygon(
            surface,
            BLACK,
            [(cx, y + 10 + hover), (cx - 2, y + 13 + hover), (cx + 2, y + 13 + hover)],
        )
        # Jagged mouth
        for i in range(5):
            tooth_x = x + 12 + i * 4
            pygame.draw.line(
                surface,
                WHITE,
                (tooth_x, y + 14 + hover),
                (tooth_x + 2, y + 17 + hover),
                1,
            )

        # Spectral claws reaching out
        claw_reach = math.sin(frame * 0.3) * 4
        for side in [-1, 1]:
            claw_base = (cx + side * 6, cy + hover)
            for c in range(3):
                claw_end = (
                    claw_base[0] + side * (10 + claw_reach) + c * side * 2,
                    claw_base[1] + 6 + c * 2,
                )
                pygame.draw.line(surface, color, claw_base, claw_end, 2)
                pygame.draw.circle(surface, NEON_YELLOW, claw_end, 1)

    @staticmethod
    def draw_wizard(surface, x, y, frame):
        """Draw the Wizard of Wor - Eldritch Cosmic Horror Entity."""
        cx, cy = x + TILE_SIZE // 2, y + TILE_SIZE // 2
        color = NEON_PURPLE
        pulse = math.sin(frame * 0.08)

        # Reality-warping aura
        for i in range(5):
            aura_radius = 20 + i * 4 + int(pulse * 3)
            aura_alpha = 50 - i * 10
            angle_offset = frame * 0.05 + i * 0.5
            for j in range(8):
                angle = angle_offset + j * math.pi / 4
                ax = cx + math.cos(angle) * aura_radius
                ay = cy + math.sin(angle) * aura_radius
                pygame.draw.circle(
                    surface, (*color[:3], aura_alpha), (int(ax), int(ay)), 3
                )

        # Void cloak (living darkness)
        cloak_sway = math.sin(frame * 0.1) * 3
        cloak_points = [
            (cx, y - 2),  # Top peak
            (cx + 12 + cloak_sway, y + 8),
            (x + TILE_SIZE + 2, y + TILE_SIZE - 2),
            (cx + 6, y + TILE_SIZE + 4),  # Tattered bottom
            (cx, y + TILE_SIZE),
            (cx - 6, y + TILE_SIZE + 4),
            (x - 2, y + TILE_SIZE - 2),
            (cx - 12 - cloak_sway, y + 8),
        ]
        pygame.draw.polygon(surface, (20, 0, 30), cloak_points)
        pygame.draw.polygon(surface, color, cloak_points, 2)
        # Cloak runes (glowing symbols)
        for i in range(3):
            rune_y = y + 16 + i * 8
            rune_glow = int(abs(math.sin(frame * 0.1 + i)) * 150 + 50)
            pygame.draw.line(
                surface,
                (rune_glow, 0, rune_glow),
                (cx - 6, rune_y),
                (cx + 6, rune_y),
                1,
            )
            pygame.draw.line(
                surface,
                (rune_glow, 0, rune_glow),
                (cx, rune_y - 3),
                (cx, rune_y + 3),
                1,
            )

        # Horrific face emerging from void
        face_emerge = abs(pulse) * 3
        # No face - just an empty void with eyes
        void_rect = pygame.Rect(x + 10, y + 4, TILE_SIZE - 20, 14)
        pygame.draw.ellipse(surface, BLACK, void_rect)

        # Multiple eldritch eyes (appearing and disappearing)
        num_eyes = 5
        for i in range(num_eyes):
            eye_phase = math.sin(frame * 0.15 + i * 1.2)
            if eye_phase > -0.3:  # Eye visible
                eye_x = cx + int(math.cos(i * 1.3) * 6)
                eye_y = y + 8 + int(math.sin(i * 1.7) * 4)
                eye_size = int(2 + eye_phase * 2)
                eye_color = (255, int(50 + eye_phase * 100), int(200 + eye_phase * 55))
                pygame.draw.circle(surface, eye_color, (eye_x, eye_y), max(1, eye_size))
                # Vertical slit pupil
                if eye_size > 1:
                    pygame.draw.line(
                        surface,
                        BLACK,
                        (eye_x, eye_y - eye_size + 1),
                        (eye_x, eye_y + eye_size - 1),
                        1,
                    )

        # Cosmic tentacles
        num_tentacles = 6
        for t in range(num_tentacles):
            base_angle = (t / num_tentacles) * math.pi * 2 + frame * 0.02
            tentacle_length = 12 + int(math.sin(frame * 0.1 + t) * 4)

            prev_x, prev_y = cx, cy + 4
            for seg in range(4):
                seg_angle = base_angle + math.sin(frame * 0.15 + t + seg * 0.5) * 0.5
                seg_len = tentacle_length / 4
                next_x = prev_x + math.cos(seg_angle) * seg_len
                next_y = prev_y + math.sin(seg_angle) * seg_len * 0.6 + seg * 2
                thickness = 3 - seg // 2
                pygame.draw.line(
                    surface,
                    color,
                    (int(prev_x), int(prev_y)),
                    (int(next_x), int(next_y)),
                    thickness,
                )
                prev_x, prev_y = next_x, next_y
            # Tentacle tip
            pygame.draw.circle(surface, NEON_CYAN, (int(prev_x), int(prev_y)), 2)

        # Eldritch staff of power
        staff_float = math.sin(frame * 0.12) * 2
        staff_x = x + TILE_SIZE + 4
        staff_points = [
            (staff_x, y - 4 + staff_float),
            (staff_x, y + TILE_SIZE + 2 + staff_float),
        ]
        pygame.draw.line(surface, (100, 50, 150), staff_points[0], staff_points[1], 3)
        # Orb of void energy
        orb_pulse = abs(math.sin(frame * 0.2)) * 4
        pygame.draw.circle(
            surface, BLACK, (staff_x, int(y - 6 + staff_float)), int(6 + orb_pulse)
        )
        pygame.draw.circle(
            surface, NEON_CYAN, (staff_x, int(y - 6 + staff_float)), int(4 + orb_pulse)
        )
        pygame.draw.circle(surface, WHITE, (staff_x, int(y - 6 + staff_float)), 2)
        # Energy crackling from orb
        for i in range(3):
            spark_angle = frame * 0.3 + i * 2
            spark_x = staff_x + math.cos(spark_angle) * (8 + orb_pulse)
            spark_y = y - 6 + staff_float + math.sin(spark_angle) * (8 + orb_pulse)
            pygame.draw.line(
                surface,
                NEON_CYAN,
                (staff_x, int(y - 6 + staff_float)),
                (int(spark_x), int(spark_y)),
                1,
            )


class MazeRenderer:
    """Renders the maze with neon glow effects."""

    def __init__(self, maze, tile_size):
        self.maze = maze
        self.tile_size = tile_size
        self.wall_color = NEON_BLUE
        self.pulse_time = 0

    def draw(self, surface):
        """Draw maze walls as glowing vector lines."""
        self.pulse_time += 0.05
        pulse = 0.7 + 0.3 * math.sin(self.pulse_time)

        wall_color = tuple(int(c * pulse) for c in self.wall_color)

        for row in range(len(self.maze)):
            for col in range(len(self.maze[0])):
                if self.maze[row][col] == 1:
                    x = col * self.tile_size
                    y = row * self.tile_size

                    # Check neighbors to draw appropriate lines
                    # Top edge
                    if row == 0 or self.maze[row - 1][col] == 0:
                        self._draw_wall_segment(
                            surface, (x, y), (x + self.tile_size, y), wall_color
                        )
                    # Bottom edge
                    if row == len(self.maze) - 1 or self.maze[row + 1][col] == 0:
                        self._draw_wall_segment(
                            surface,
                            (x, y + self.tile_size),
                            (x + self.tile_size, y + self.tile_size),
                            wall_color,
                        )
                    # Left edge
                    if col == 0 or self.maze[row][col - 1] == 0:
                        self._draw_wall_segment(
                            surface, (x, y), (x, y + self.tile_size), wall_color
                        )
                    # Right edge
                    if col == len(self.maze[0]) - 1 or self.maze[row][col + 1] == 0:
                        self._draw_wall_segment(
                            surface,
                            (x + self.tile_size, y),
                            (x + self.tile_size, y + self.tile_size),
                            wall_color,
                        )

    def _draw_wall_segment(self, surface, start, end, color):
        """Draw a wall segment - simple line, no glow for performance."""
        pygame.draw.line(surface, color, start, end, 2)


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.direction = (1, 0)
        self.speed = 5
        self.lives = 3
        self.score = 0
        self.shoot_cooldown = 0
        self.frame = 0
        self.color = NEON_YELLOW

    def get_rect(self):
        return pygame.Rect(self.x, self.y, TILE_SIZE - 4, TILE_SIZE - 4)

    def move(self, dx, dy, maze):
        self.frame += 1

        if dx != 0 or dy != 0:
            self.direction = (dx, dy)

        new_x = self.x + dx * self.speed
        new_y = self.y + dy * self.speed

        # Handle wraparound at tunnel
        if new_x < 0:
            new_x = GAME_WIDTH - TILE_SIZE
        elif new_x > GAME_WIDTH - TILE_SIZE:
            new_x = 0

        new_rect = pygame.Rect(new_x, new_y, TILE_SIZE - 4, TILE_SIZE - 4)

        if not fast_wall_collision(new_rect):
            self.x = new_x
            self.y = new_y
        else:
            # Enhanced corner sliding - find the nearest valid corridor
            # When moving horizontally and blocked, try to align to vertical corridor
            # When moving vertically and blocked, try to align to horizontal corridor

            corner_tolerance = (
                TILE_SIZE // 2 + 4
            )  # How far off we can be and still slide

            if dx != 0:  # Moving horizontally, try to snap to vertical corridor
                # Find nearest tile-aligned Y position
                tile_y = round(self.y / TILE_SIZE) * TILE_SIZE + 2
                offset = tile_y - self.y

                if abs(offset) <= corner_tolerance:
                    # Check if snapping would let us through
                    test_rect = pygame.Rect(new_x, tile_y, TILE_SIZE - 4, TILE_SIZE - 4)
                    if not fast_wall_collision(test_rect):
                        # Gradually slide toward the opening
                        slide_speed = min(abs(offset), self.speed)
                        self.y += slide_speed if offset > 0 else -slide_speed
                        return

                # Also try one tile up/down
                for offset_tiles in [-1, 1]:
                    test_tile_y = tile_y + offset_tiles * TILE_SIZE
                    offset = test_tile_y - self.y
                    if abs(offset) <= corner_tolerance:
                        test_rect = pygame.Rect(
                            new_x, test_tile_y, TILE_SIZE - 4, TILE_SIZE - 4
                        )
                        if not fast_wall_collision(test_rect):
                            slide_speed = min(abs(offset), self.speed)
                            self.y += slide_speed if offset > 0 else -slide_speed
                            return

            if dy != 0:  # Moving vertically, try to snap to horizontal corridor
                # Find nearest tile-aligned X position
                tile_x = round(self.x / TILE_SIZE) * TILE_SIZE + 2
                offset = tile_x - self.x

                if abs(offset) <= corner_tolerance:
                    # Check if snapping would let us through
                    test_rect = pygame.Rect(tile_x, new_y, TILE_SIZE - 4, TILE_SIZE - 4)
                    if not fast_wall_collision(test_rect):
                        # Gradually slide toward the opening
                        slide_speed = min(abs(offset), self.speed)
                        self.x += slide_speed if offset > 0 else -slide_speed
                        return

                # Also try one tile left/right
                for offset_tiles in [-1, 1]:
                    test_tile_x = tile_x + offset_tiles * TILE_SIZE
                    offset = test_tile_x - self.x
                    if abs(offset) <= corner_tolerance:
                        test_rect = pygame.Rect(
                            test_tile_x, new_y, TILE_SIZE - 4, TILE_SIZE - 4
                        )
                        if not fast_wall_collision(test_rect):
                            slide_speed = min(abs(offset), self.speed)
                            self.x += slide_speed if offset > 0 else -slide_speed
                            return

    def draw(self, surface):
        SpriteRenderer.draw_player(
            surface, self.x, self.y, self.direction, self.frame, self.color
        )


class Bullet:
    def __init__(self, x, y, direction, is_player=True):
        self.x = x
        self.y = y
        self.direction = direction
        self.speed = 14
        self.is_player = is_player
        self.active = True
        self.trail = []

    def get_rect(self):
        return pygame.Rect(self.x - 4, self.y - 4, 8, 8)

    def update(self, maze):
        # Store trail
        self.trail.append((self.x, self.y))
        if len(self.trail) > 5:
            self.trail.pop(0)

        self.x += self.direction[0] * self.speed
        self.y += self.direction[1] * self.speed

        # Wraparound
        if self.x < 0:
            self.x = GAME_WIDTH
        elif self.x > GAME_WIDTH:
            self.x = 0

        # Wall collision
        tile_x = int(self.x // TILE_SIZE)
        tile_y = int(self.y // TILE_SIZE)

        if 0 <= tile_x < MAZE_WIDTH and 0 <= tile_y < MAZE_HEIGHT:
            if maze[tile_y][tile_x] == 1:
                self.active = False

        if self.y < 0 or self.y > GAME_HEIGHT:
            self.active = False

    def draw(self, surface):
        color = NEON_CYAN if self.is_player else NEON_RED

        # Trail
        for i, (tx, ty) in enumerate(self.trail):
            alpha = (i + 1) / len(self.trail)
            trail_color = tuple(int(c * alpha) for c in color)
            pygame.draw.circle(surface, trail_color, (int(tx), int(ty)), 2)

        # Glow
        glow_surf = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*color, 100), (10, 10), 8)
        surface.blit(
            glow_surf,
            (int(self.x - 10), int(self.y - 10)),
            special_flags=pygame.BLEND_RGB_ADD,
        )

        # Core
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), 4)
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), 3)


class Enemy:
    def __init__(self, x, y, enemy_type="burwor"):
        self.x = x
        self.y = y
        self.enemy_type = enemy_type
        base_speed = {"burwor": 3, "garwor": 3, "thorwor": 4, "worluk": 5, "wizard": 0}[
            enemy_type
        ]
        self.speed = base_speed * ENEMY_SPEED_MULTIPLIER
        self.direction = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        self.shoot_timer = random.randint(30, 90)
        self.active = True
        self.visible = True
        self.invisible_timer = random.randint(60, 120) if enemy_type == "garwor" else 0
        self.frame = random.randint(0, 100)
        self.teleport_timer = random.randint(90, 180) if enemy_type == "wizard" else 0

        self.points = {
            "burwor": 100,
            "garwor": 200,
            "thorwor": 500,
            "worluk": 1000,
            "wizard": 2500,
        }
        self.colors = {
            "burwor": NEON_BLUE,
            "garwor": NEON_ORANGE,
            "thorwor": NEON_RED,
            "worluk": NEON_GREEN,
            "wizard": NEON_PURPLE,
        }

    def get_rect(self):
        return pygame.Rect(self.x, self.y, TILE_SIZE - 4, TILE_SIZE - 4)

    def update(self, maze, player, valid_positions=None):
        self.frame += 1
        self.shoot_timer -= 1

        # Garwor invisibility
        if self.enemy_type == "garwor":
            self.invisible_timer -= 1
            if self.invisible_timer <= 0:
                self.visible = not self.visible
                self.invisible_timer = random.randint(60, 120)

        # Wizard teleportation and flickering visibility
        if self.enemy_type == "wizard" and valid_positions:
            self.teleport_timer -= 1
            if self.teleport_timer <= 0:
                pos = random.choice(valid_positions)
                self.x, self.y = pos
                self.teleport_timer = random.randint(60, 120)
            self.visible = self.frame % 6 != 0
            return  # Wizard doesn't move normally

        # Continuous smooth movement for all enemies
        new_x = self.x + self.direction[0] * self.speed
        new_y = self.y + self.direction[1] * self.speed

        # Worluk escape check
        if self.enemy_type == "worluk":
            if new_x < -TILE_SIZE // 2 or new_x > GAME_WIDTH:
                self.active = False
                return

        # Wraparound at tunnels
        if new_x < 0:
            new_x = GAME_WIDTH - TILE_SIZE
        elif new_x > GAME_WIDTH - TILE_SIZE:
            new_x = 0

        new_rect = pygame.Rect(new_x, new_y, TILE_SIZE - 4, TILE_SIZE - 4)

        if not fast_wall_collision(new_rect):
            self.x = new_x
            self.y = new_y
        else:
            # Hit wall - pick new direction
            self._pick_new_direction(player)

        # Occasionally reconsider direction to chase player
        if random.random() < 0.03:
            self._pick_new_direction(player)

    def _pick_new_direction(self, player):
        """Pick a new valid direction, preferring to chase player."""
        possible = []
        for d in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            test_x = self.x + d[0] * self.speed * 2
            test_y = self.y + d[1] * self.speed * 2
            test_rect = pygame.Rect(test_x, test_y, TILE_SIZE - 4, TILE_SIZE - 4)
            if not fast_wall_collision(test_rect):
                possible.append(d)

        if not possible:
            return

        # Worluk: prefer directions toward tunnels
        if self.enemy_type == "worluk":
            tunnel_y = 7 * TILE_SIZE
            if self.y < tunnel_y:
                preferred = [(0, 1), (-1, 0), (1, 0)]
            elif self.y > tunnel_y:
                preferred = [(0, -1), (-1, 0), (1, 0)]
            else:
                preferred = [(-1, 0), (1, 0)]
            for d in preferred:
                if d in possible:
                    self.direction = d
                    return

        # Chase player with some probability
        if random.random() < 0.6:
            dx = 1 if player.x > self.x else -1 if player.x < self.x else 0
            dy = 1 if player.y > self.y else -1 if player.y < self.y else 0
            if (dx, 0) in possible and random.random() < 0.5:
                self.direction = (dx, 0)
                return
            if (0, dy) in possible:
                self.direction = (0, dy)
                return

        # Random valid direction
        self.direction = random.choice(possible)

    def should_shoot(self, player):
        if self.enemy_type in ["burwor", "worluk"]:  # Burwor and Worluk don't shoot
            return False

        if self.shoot_timer <= 0:
            # Wizard shoots more frequently and from further away
            if self.enemy_type == "wizard":
                self.shoot_timer = random.randint(30, 60)  # Very aggressive
                return True  # Wizard always shoots when ready
            else:
                self.shoot_timer = random.randint(90, 200)
                if (
                    abs(self.x - player.x) < TILE_SIZE * 2
                    or abs(self.y - player.y) < TILE_SIZE * 2
                ):
                    return True
        return False

    def get_shoot_direction(self, player):
        if abs(self.x - player.x) < TILE_SIZE * 2:
            return (0, 1 if player.y > self.y else -1)
        else:
            return (1 if player.x > self.x else -1, 0)

    def draw(self, surface):
        draw_funcs = {
            "burwor": SpriteRenderer.draw_burwor,
            "garwor": SpriteRenderer.draw_garwor,
            "thorwor": SpriteRenderer.draw_thorwor,
            "worluk": lambda s, x, y, d, f, v=True: SpriteRenderer.draw_worluk(
                s, x, y, d, f
            ),
            "wizard": lambda s, x, y, d, f, v=True: SpriteRenderer.draw_wizard(
                s, x, y, f
            ),
        }

        draw_func = draw_funcs.get(self.enemy_type, SpriteRenderer.draw_burwor)
        draw_func(surface, self.x, self.y, self.direction, self.frame, self.visible)


class Radar:
    """Minimap radar display."""

    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.scale_x = width / GAME_WIDTH
        self.scale_y = height / GAME_HEIGHT

    def draw(self, surface, maze, player, enemies, frame):
        # Background
        pygame.draw.rect(surface, (0, 0, 30), (self.x, self.y, self.width, self.height))
        pygame.draw.rect(
            surface, NEON_BLUE, (self.x, self.y, self.width, self.height), 1
        )

        # Maze walls (simplified)
        for row in range(len(maze)):
            for col in range(len(maze[0])):
                if maze[row][col] == 1:
                    rx = self.x + col * self.width // MAZE_WIDTH
                    ry = self.y + row * self.height // MAZE_HEIGHT
                    rw = self.width // MAZE_WIDTH
                    rh = self.height // MAZE_HEIGHT
                    pygame.draw.rect(surface, (0, 50, 100), (rx, ry, rw, rh))

        # Enemy blips
        for enemy in enemies:
            ex = self.x + int(enemy.x * self.scale_x)
            ey = self.y + int(enemy.y * self.scale_y)
            color = enemy.colors.get(enemy.enemy_type, NEON_RED)

            # Flicker if invisible
            if not enemy.visible and frame % 10 > 5:
                continue

            pygame.draw.circle(surface, color, (ex, ey), 3)

        # Player blip (pulsing)
        px = self.x + int(player.x * self.scale_x)
        py = self.y + int(player.y * self.scale_y)
        pulse = 2 + abs(math.sin(frame * 0.2))
        pygame.draw.circle(surface, NEON_YELLOW, (px, py), int(pulse))


class HUD:
    """Heads-up display with score and lives."""

    def __init__(self, y_offset):
        self.y = y_offset
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

    def draw(self, surface, player, enemies_left, dungeon=1):
        # Score (LED style)
        score_text = f"SCORE: {player.score:06d}"
        self._draw_led_text(surface, score_text, 10, self.y + 10, NEON_GREEN)

        # Lives
        lives_x = 10
        lives_y = self.y + 35
        self._draw_led_text(surface, "LIVES:", lives_x, lives_y, NEON_YELLOW)
        for i in range(player.lives):
            pygame.draw.rect(
                surface, NEON_YELLOW, (lives_x + 70 + i * 20, lives_y, 12, 15)
            )
            pygame.draw.rect(
                surface, NEON_CYAN, (lives_x + 72 + i * 20, lives_y + 3, 8, 4)
            )

        # Enemies remaining
        enemies_text = f"ENEMIES: {enemies_left}"
        self._draw_led_text(
            surface, enemies_text, SCREEN_WIDTH - 150, self.y + 10, NEON_RED
        )

        # Dungeon level
        dungeon_text = f"DUNGEON {dungeon}"
        self._draw_led_text(
            surface, dungeon_text, SCREEN_WIDTH // 2 - 50, self.y + 10, NEON_PURPLE
        )

    def _draw_led_text(self, surface, text, x, y, color):
        """Draw text with LED-style glow."""
        # Glow
        glow_surf = self.font.render(text, True, color)
        glow_surf.set_alpha(100)
        surface.blit(glow_surf, (x - 1, y - 1))
        surface.blit(glow_surf, (x + 1, y + 1))

        # Core text
        text_surf = self.font.render(text, True, color)
        surface.blit(text_surf, (x, y))

    def draw_message(self, surface, message, color=WHITE):
        """Draw centered message."""
        text = self.font.render(message, True, color)
        rect = text.get_rect(center=(SCREEN_WIDTH // 2, GAME_HEIGHT // 2))

        # Background box
        bg_rect = rect.inflate(40, 20)
        pygame.draw.rect(surface, BLACK, bg_rect)
        pygame.draw.rect(surface, color, bg_rect, 2)

        surface.blit(text, rect)


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Wizard of Wor - Neon CRT Revival")
        self.clock = pygame.time.Clock()

        # Initialize audio
        pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
        self.load_sounds()

        # Rendering systems
        self.post_processor = PostProcessor(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.particle_system = ParticleSystem()
        self.maze_renderer = MazeRenderer(MAZE, TILE_SIZE)
        self.hud = HUD(GAME_HEIGHT + RADAR_HEIGHT)
        self.radar = Radar(
            SCREEN_WIDTH // 2 - 100, GAME_HEIGHT + 5, 200, RADAR_HEIGHT - 10
        )

        # Game surface (before post-processing)
        self.game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

        self.dungeon = 1
        self.reset_game()

        # Play welcome voice
        self.play_sound("voice_welcome")

    def load_sounds(self):
        """Load all sound effects and voice lines."""
        self.sounds = {}
        sound_files = [
            "player_shot",
            "enemy_shot",
            "enemy_death",
            "player_death",
            "walking_beat",
            "walking_beat_fast",
            "radar_blip",
            "worluk_escape",
            "wizard_teleport",
            "level_complete",
            "game_over",
            "voice_wizard",
            "voice_welcome",
            "voice_prepare",
            "voice_insert_coin",
            "voice_game_over",
            "laugh",
        ]

        for name in sound_files:
            try:
                self.sounds[name] = pygame.mixer.Sound(f"assets/sounds/{name}.wav")
            except:
                print(f"Warning: Could not load sound {name}")
                self.sounds[name] = None

        # Set volumes
        if self.sounds.get("walking_beat"):
            self.sounds["walking_beat"].set_volume(0.3)
        if self.sounds.get("walking_beat_fast"):
            self.sounds["walking_beat_fast"].set_volume(0.3)
        if self.sounds.get("radar_blip"):
            self.sounds["radar_blip"].set_volume(0.2)

    def play_sound(self, name):
        """Play a sound by name."""
        if name in self.sounds and self.sounds[name]:
            self.sounds[name].play()

    def is_valid_spawn(self, x, y):
        rect = pygame.Rect(x, y, TILE_SIZE - 4, TILE_SIZE - 4)
        for row in range(MAZE_HEIGHT):
            for col in range(MAZE_WIDTH):
                if MAZE[row][col] == 1:
                    wall_rect = pygame.Rect(
                        col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE
                    )
                    if rect.colliderect(wall_rect):
                        return False
        return True

    def find_valid_spawn_positions(self, max_row=None):
        positions = []
        for row in range(MAZE_HEIGHT):
            if max_row is not None and row > max_row:
                continue
            for col in range(MAZE_WIDTH):
                if MAZE[row][col] == 0:
                    x = col * TILE_SIZE + 2
                    y = row * TILE_SIZE + 2
                    if self.is_valid_spawn(x, y):
                        positions.append((x, y))
        return positions

    def find_player_spawn(self):
        """Spawn player from bottom left corner (like original arcade Wor-Pen)."""
        # Bottom row is row 13 (row 14 is wall), left corner area is columns 1-3
        spawn_row = MAZE_HEIGHT - 2  # Row 13

        # Try bottom-left corner first (original P1 spawn)
        for col in range(1, 4):
            if MAZE[spawn_row][col] == 0:
                x = col * TILE_SIZE + 2
                y = spawn_row * TILE_SIZE + 2
                if self.is_valid_spawn(x, y):
                    return x, y

        # Fallback to bottom-right corner
        for col in range(MAZE_WIDTH - 2, MAZE_WIDTH - 4, -1):
            if MAZE[spawn_row][col] == 0:
                x = col * TILE_SIZE + 2
                y = spawn_row * TILE_SIZE + 2
                if self.is_valid_spawn(x, y):
                    return x, y

        # Last resort fallback
        positions = self.find_valid_spawn_positions()
        bottom_positions = [p for p in positions if p[1] > MAZE_HEIGHT * TILE_SIZE // 2]
        return random.choice(bottom_positions) if bottom_positions else positions[0]

    def reset_game(self):
        player_x, player_y = self.find_player_spawn()
        self.player = Player(player_x, player_y)
        self.player_spawn = (player_x, player_y)

        # Spawn effect
        self.particle_system.emit_spawn(
            player_x + TILE_SIZE // 2, player_y + TILE_SIZE // 2, NEON_YELLOW
        )

        self.bullets = []
        self.enemies = []
        self.valid_positions = self.find_valid_spawn_positions()

        # Game phase: "normal" -> "worluk" -> "wizard" -> victory
        self.phase = "normal"
        self.phase_timer = 0
        self.worluk_escaped = False
        self.message = ""
        self.message_timer = 0

        # Spawn enemies
        enemy_spawn_positions = self.find_valid_spawn_positions(max_row=6)
        num_enemies = min(6, len(enemy_spawn_positions))

        if num_enemies > 0:
            selected_positions = random.sample(enemy_spawn_positions, num_enemies)
            enemy_types = ["burwor"] * 3 + ["garwor"] * 2 + ["thorwor"]

            for i, pos in enumerate(selected_positions):
                enemy = Enemy(pos[0], pos[1], enemy_types[i])
                self.enemies.append(enemy)
                self.particle_system.emit_spawn(
                    pos[0] + TILE_SIZE // 2,
                    pos[1] + TILE_SIZE // 2,
                    enemy.colors[enemy.enemy_type],
                )

        self.game_over = False
        self.victory = False
        self.frame = 0

    def spawn_worluk(self):
        """Spawn the Worluk bonus creature."""
        self.phase = "worluk"
        self.message = "THE WORLUK APPEARS!"
        self.message_timer = 90
        self.play_sound("radar_blip")  # Alert sound for Worluk

        # Spawn in center of maze
        spawn_pos = random.choice(self.valid_positions)
        worluk = Enemy(spawn_pos[0], spawn_pos[1], "worluk")
        self.enemies.append(worluk)
        self.particle_system.emit_spawn(
            spawn_pos[0] + TILE_SIZE // 2, spawn_pos[1] + TILE_SIZE // 2, NEON_GREEN
        )

    def spawn_wizard(self):
        """Spawn the Wizard of Wor boss."""
        self.phase = "wizard"
        self.message = "I AM THE WIZARD OF WOR!"
        self.message_timer = 120
        self.play_sound("voice_wizard")
        self.play_sound("wizard_teleport")

        # Spawn in a random position
        spawn_pos = random.choice(self.valid_positions)
        wizard = Enemy(spawn_pos[0], spawn_pos[1], "wizard")
        self.enemies.append(wizard)
        self.particle_system.emit_spawn(
            spawn_pos[0] + TILE_SIZE // 2, spawn_pos[1] + TILE_SIZE // 2, NEON_PURPLE
        )

    def handle_input(self):
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

        if keys[pygame.K_SPACE] and self.player.shoot_cooldown <= 0:
            bullet_x = self.player.x + TILE_SIZE // 2
            bullet_y = self.player.y + TILE_SIZE // 2
            self.bullets.append(Bullet(bullet_x, bullet_y, self.player.direction, True))
            self.player.shoot_cooldown = 12
            self.play_sound("player_shot")

        if self.player.shoot_cooldown > 0:
            self.player.shoot_cooldown -= 1

    def update(self):
        if self.game_over or self.victory:
            return

        self.frame += 1
        self.particle_system.update()

        # Update bullets
        for bullet in self.bullets[:]:
            bullet.update(MAZE)
            if not bullet.active:
                # Wall hit particles
                self.particle_system.emit_explosion(
                    bullet.x, bullet.y, NEON_CYAN if bullet.is_player else NEON_RED, 5
                )
                self.bullets.remove(bullet)

        # Update enemies
        for enemy in self.enemies[:]:
            enemy.update(MAZE, self.player, self.valid_positions)

            if enemy.should_shoot(self.player):
                direction = enemy.get_shoot_direction(self.player)
                bullet_x = enemy.x + TILE_SIZE // 2
                bullet_y = enemy.y + TILE_SIZE // 2
                self.bullets.append(Bullet(bullet_x, bullet_y, direction, False))
                self.play_sound("enemy_shot")

        # Bullet-enemy collisions
        for bullet in self.bullets[:]:
            if bullet.is_player:
                for enemy in self.enemies[:]:
                    if bullet.get_rect().colliderect(enemy.get_rect()):
                        self.player.score += enemy.points.get(enemy.enemy_type, 100)
                        # Death explosion
                        self.particle_system.emit_explosion(
                            enemy.x + TILE_SIZE // 2,
                            enemy.y + TILE_SIZE // 2,
                            enemy.colors.get(enemy.enemy_type, NEON_RED),
                            30,
                        )
                        self.play_sound("enemy_death")
                        self.enemies.remove(enemy)
                        if bullet in self.bullets:
                            self.bullets.remove(bullet)
                        break

        # Bullet-player collisions
        for bullet in self.bullets[:]:
            if not bullet.is_player:
                if bullet.get_rect().colliderect(self.player.get_rect()):
                    self.player.lives -= 1
                    self.particle_system.emit_explosion(
                        self.player.x + TILE_SIZE // 2,
                        self.player.y + TILE_SIZE // 2,
                        NEON_YELLOW,
                        40,
                    )
                    self.play_sound("player_death")
                    self.bullets.remove(bullet)
                    if self.player.lives <= 0:
                        self.game_over = True
                        self.play_sound("game_over")
                        self.play_sound("voice_game_over")
                    else:
                        self.player.x, self.player.y = self.player_spawn
                        self.particle_system.emit_spawn(
                            self.player.x + TILE_SIZE // 2,
                            self.player.y + TILE_SIZE // 2,
                            NEON_YELLOW,
                        )

        # Player-enemy collisions
        for enemy in self.enemies:
            if self.player.get_rect().colliderect(enemy.get_rect()):
                self.player.lives -= 1
                self.particle_system.emit_explosion(
                    self.player.x + TILE_SIZE // 2,
                    self.player.y + TILE_SIZE // 2,
                    NEON_YELLOW,
                    40,
                )
                self.play_sound("player_death")
                if self.player.lives <= 0:
                    self.game_over = True
                    self.play_sound("game_over")
                    self.play_sound("voice_game_over")
                else:
                    self.player.x, self.player.y = self.player_spawn
                break

        # Check for Worluk escape
        for enemy in self.enemies[:]:
            if enemy.enemy_type == "worluk" and not enemy.active:
                self.enemies.remove(enemy)
                self.worluk_escaped = True
                self.message = "THE WORLUK ESCAPED!"
                self.message_timer = 60
                self.play_sound("worluk_escape")

        # Update message timer
        if self.message_timer > 0:
            self.message_timer -= 1

        # Phase management
        if len(self.enemies) == 0:
            self.phase_timer += 1

            if self.phase == "normal":
                # All regular enemies defeated - spawn Worluk after delay
                if self.phase_timer >= 60:
                    self.spawn_worluk()
                    self.phase_timer = 0

            elif self.phase == "worluk":
                # Worluk killed or escaped - spawn Wizard after delay
                if self.phase_timer >= 90:
                    self.spawn_wizard()
                    self.phase_timer = 0

            elif self.phase == "wizard":
                # Wizard defeated - victory!
                self.victory = True
                self.message = "DUNGEON CLEARED!"
                self.message_timer = 120
                self.play_sound("level_complete")

    def draw(self):
        self.game_surface.fill(DARK_BLUE)

        # Draw maze
        self.maze_renderer.draw(self.game_surface)

        # Draw enemies
        for enemy in self.enemies:
            enemy.draw(self.game_surface)

        # Draw player
        self.player.draw(self.game_surface)

        # Draw bullets
        for bullet in self.bullets:
            bullet.draw(self.game_surface)

        # Draw particles
        self.particle_system.draw(self.game_surface)

        # Draw radar
        self.radar.draw(self.game_surface, MAZE, self.player, self.enemies, self.frame)

        # Draw HUD
        self.hud.draw(self.game_surface, self.player, len(self.enemies), self.dungeon)

        # Phase messages
        if self.message_timer > 0 and self.message:
            color = (
                NEON_GREEN
                if "WORLUK" in self.message
                else NEON_PURPLE if "WIZARD" in self.message else NEON_CYAN
            )
            self.hud.draw_message(self.game_surface, self.message, color)

        # Game over / victory messages
        if self.game_over:
            self.hud.draw_message(
                self.game_surface, "GAME OVER - Press R to Restart", NEON_RED
            )
        elif self.victory:
            self.hud.draw_message(
                self.game_surface, "VICTORY! Press R to Continue", NEON_GREEN
            )

        # Apply post-processing
        processed = self.post_processor.process(self.game_surface)
        self.screen.blit(processed, (0, 0))

        pygame.display.flip()

    def run(self):
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_r:
                        if self.victory:
                            self.dungeon += 1
                            self.player.score = self.player.score  # Keep score
                        else:
                            self.dungeon = 1
                        self.reset_game()

            self.handle_input()
            self.update()
            self.draw()

            self.clock.tick(60)

        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()
    game.run()
    game.run()
    game.run()
