# Wizard of Wor - Project Handoff

## Project Overview

A Python/Pygame clone of the classic 1980 Midway arcade game "Wizard of Wor" with multiple rendering modes:

1. **2D Neon CRT** (`wizard_of_wor.py`) - Classic top-down view with neon glow effects and CRT post-processing
2. **3D First-Person** (`wizard_of_wor_3d.py`) - Experimental Ursina engine first-person view
3. **Isometric 2.5D** (`wizard_of_wor_iso.py`) - Axonometric view with mouse-controlled camera rotation

**Latest update:** Isometric Ursina version now uses textures cropped from `assets/images/underwater_maze_assets.png` for the floor, walls, and the full-scene background.

## Quick Start

```bash
cd /Users/erk/repos/oyunbaz/wow
pdm install              # Install dependencies
pdm run game             # 2D Neon version
pdm run game-iso         # Isometric 2.5D version
pdm run game-3d          # 3D First-person version
```

## Project Structure

```
wizard-of-wor/
├── wizard_of_wor.py       # 2D neon version (~1850 lines)
├── wizard_of_wor_3d.py    # 3D Ursina version
├── wizard_of_wor_iso.py   # Isometric 2.5D version (~1340 lines)
├── assets/
│   ├── images/            # Underwater art assets and derived textures
│   └── sounds/            # Sound effects (.wav files)
├── pyproject.toml         # PDM project config
├── CLAUDE.md              # AI assistant instructions
├── HANDOFF.md             # This file
└── README.md              # Project readme
```

---

## ⚠️ OPEN PROBLEMS

See sections below for current open issues:
1. **Ursina "plane" Model Not Rendering** - macOS-specific? Workaround: use "quad" with rotation
2. **window.color Not Applied** - Background stays white

---

## ✅ RESOLVED: Pygame Isometric Projection Distortion

**Status:** RESOLVED - Switched to Ursina 3D engine  
**File:** `wizard_of_wor_iso_pygame.py` (archived)  
**Original Severity:** Medium

#### Problem Description

When the camera is rotated using mouse drag, the isometric projection shows visual distortion. While depth sorting has been fixed to use screen-space Y-sorting, the projection math itself produces slightly off results at non-cardinal rotation angles.

**What was fixed:**
- ✅ Depth sorting now uses screen Y position (`get_rotated_depth()`)
- ✅ Wall block face visibility uses rotated normals
- ✅ Shared `get_tile_corner_offsets()` function for consistent tile/wall rendering

**What remains broken:**
- ❌ Projection geometry distorts at intermediate rotation angles (e.g., 45°, 135°)
- ❌ Tiles don't maintain perfect isometric proportions when rotated
- ❌ Slight visual "warping" or "stretching" visible during rotation

#### Current Implementation

The depth sorting was changed from `grid_x + grid_y` to screen Y position:

```python
def get_rotated_depth(x, y):
    """Get depth value based on screen Y position after rotation."""
    _, screen_y = get_screen_pos(x, y)
    return screen_y
```

Wall face visibility uses rotated normals:

```python
# Rotate normal by camera angle
cos_a = math.cos(-Camera.angle)
sin_a = math.sin(-Camera.angle)
rnx = nx * cos_a - ny * sin_a
rny = nx * sin_a + ny * cos_a
# Face is visible if it points toward camera
if (rnx + rny) > 0:
    # Draw face
```

#### Root Cause (Remaining Issue)

The isometric transformation in `cart_to_iso()` applies rotation before the 2:1 isometric projection. This creates a shear effect rather than a true axonometric rotation:

```python
def cart_to_iso(x, y):
    """Convert grid coordinates to screen with rotation."""
    # Center
    cx = x - MAZE_WIDTH / 2
    cy = y - MAZE_HEIGHT / 2
    
    # Rotate in grid space
    cos_a = math.cos(Camera.angle)
    sin_a = math.sin(Camera.angle)
    rx = cx * cos_a - cy * sin_a
    ry = cx * sin_a + cy * cos_a
    
    # Apply 2:1 isometric projection
    iso_x = (rx - ry) * (TILE_WIDTH / 2) * Camera.zoom
    iso_y = (rx + ry) * (TILE_HEIGHT / 2) * Camera.zoom
    
    return iso_x + SCREEN_WIDTH // 2, iso_y + ISO_OFFSET_Y
```

The issue is that true isometric/axonometric rotation should rotate the 3D viewpoint, not the 2D grid. The current approach applies 2D rotation to grid coords, then projects to isometric - this doesn't preserve angles correctly.

#### Suggested Fixes

**Option 1: True 3D Rotation with Orthographic Projection**

Instead of rotating in 2D grid space, use actual 3D coordinates and rotate the camera viewpoint:

```python
def cart_to_iso_3d(x, y, z=0):
    """True axonometric projection with 3D camera rotation."""
    # Grid to 3D world space
    wx = (x - MAZE_WIDTH / 2) * TILE_SIZE_3D
    wy = (y - MAZE_HEIGHT / 2) * TILE_SIZE_3D
    wz = z
    
    # Camera rotation around Z axis (vertical)
    cos_a = math.cos(Camera.angle)
    sin_a = math.sin(Camera.angle)
    rx = wx * cos_a - wy * sin_a
    ry = wx * sin_a + wy * cos_a
    rz = wz
    
    # Fixed isometric camera angles (atan(1/sqrt(2)) ≈ 35.264°)
    # Project to 2D using orthographic projection
    iso_angle = math.radians(35.264)
    screen_x = rx
    screen_y = ry * math.sin(iso_angle) - rz * math.cos(iso_angle)
    
    return screen_x * Camera.zoom + SCREEN_WIDTH // 2, screen_y * Camera.zoom + ISO_OFFSET_Y
```

**Option 2: Pre-compute Rotated Tile Sprites**

Generate tile/wall sprites at multiple rotation angles (0°, 90°, 180°, 270°) and switch between them based on camera quadrant. This avoids projection math issues but requires more assets.

**Option 3: Use a 3D Engine with Orthographic Camera**

Consider using Pygame-ce's 3D capabilities or a lightweight 3D library with orthographic projection. This handles rotation correctly by design.

**UPDATE (2026-01-10): This issue was RESOLVED by switching to Ursina engine. See below.**

---

## ✅ RESOLVED: Isometric Projection Issue

**Resolution:** Replaced Pygame-based isometric rendering with Ursina 3D engine.

The new implementation uses:
- **Orthographic camera** - True isometric projection without distortion
- **Real 3D geometry** - Cubes for walls, proper depth handling
- **Camera orbiting pivot** - Rotates around maze center at fixed tilt angle (35.264°)

**Files:**
- `wizard_of_wor_iso.py` - New Ursina-based version (now works correctly)
- `wizard_of_wor_iso_pygame.py` - Old Pygame version (backup for reference)
 - `assets/images/underwater_floor_tile.png` - Cropped floor texture
 - `assets/images/underwater_wall_tile.png` - Cropped wall texture
 - `assets/images/underwater_background.png` - Cropped scene background

```python
# Key camera implementation
class IsometricCamera(Entity):
    def update_camera_position(self):
        camera.orthographic = True
        # Position on sphere around pivot
        rad = math.radians(self.angle)
        tilt_rad = math.radians(35.264)  # True isometric angle
        x = self.pivot.x + distance * math.sin(rad) * math.cos(tilt_rad)
        y = self.pivot.y + distance * math.sin(tilt_rad)
        z = self.pivot.z + distance * math.cos(rad) * math.cos(tilt_rad)
        camera.position = Vec3(x, y, z)
        camera.look_at(self.pivot)
```

---

## ⚠️ OPEN PROBLEM: Ursina "plane" Model Not Rendering (Possible macOS Issue)

**Status:** WORKAROUND FOUND  
**File:** [wizard_of_wor_iso.py](wizard_of_wor_iso.py) - `MazeBuilder.build()` method  
**Severity:** Low - Workaround exists  
**Platform:** macOS (Apple Silicon / M-series) - may not affect other platforms

### Problem Description

When creating a floor using Ursina's built-in `"plane"` model, the entity does not render at all. The plane is invisible regardless of:
- Color settings (tried `color.red`, `color.brown`, `color.rgb()`)
- Position/scale adjustments
- `unlit=True` or `False`
- `double_sided=True`
- Clip plane adjustments

The `"plane"` model simply does not appear on screen.

### Failed Attempts

```python
# DOES NOT WORK - plane is invisible
floor = Entity(
    model="plane",
    scale=(50, 1, 40),
    position=(10, -0.1, 7),
    color=color.red,
)
```

### Working Workaround

Use `"quad"` model with `rotation_x=90` instead of `"plane"`:

```python
# WORKS - quad rotated to be horizontal
floor = Entity(
    model="quad",
    scale=(50, 40),          # Note: 2D scale, not 3D
    rotation_x=90,           # Rotate to horizontal
    position=(10, -0.1, 7),
    color=color.red,
    unlit=True,
    double_sided=True,
)
```

### Root Cause Hypothesis

This may be a macOS-specific rendering issue with Ursina/Panda3D:
1. Possible backface culling issue specific to the "plane" model on macOS
2. Could be related to Metal rendering backend on Apple Silicon
3. The "plane" model might have incorrect normals or winding order on macOS

### Investigation Needed

- [ ] Test on Windows/Linux to confirm if macOS-specific
- [ ] Check Ursina GitHub issues for similar reports
- [ ] Test with different Panda3D rendering backends
- [ ] Investigate if this affects other flat models

---

## ⚠️ OPEN PROBLEM: window.color Not Applied (White Background)

**Status:** UNRESOLVED  
**File:** [wizard_of_wor_iso.py](wizard_of_wor_iso.py) - main block  
**Severity:** Low - Cosmetic issue

### Problem Description

Setting `window.color` in the main block does not change the background color:

```python
if __name__ == "__main__":
    window.color = color.rgb(15, 35, 55)  # Deep ocean - NOT WORKING
```

The background remains white instead of the dark ocean blue. This may be related to:
- Orthographic camera setup
- Timing of when `window.color` is set vs when camera is configured
- Possible macOS-specific issue

### Workaround Options

1. Create a large skybox/background Entity behind the scene
2. Set `camera.clip_plane_far` to show a colored "void"
3. Use a full-screen quad at far distance with desired color

---

## Architecture

The game is contained in a single `wizard_of_wor.py` file (~1160 lines) with the following class structure:

### Core Classes

| Class | Purpose |
|-------|---------|
| `Game` | Main game loop, state management, phase transitions |
| `Player` | Player movement, shooting, collision |
| `Enemy` | All enemy types with type-specific AI |
| `Bullet` | Projectile physics and collision |

### Rendering Classes

| Class | Purpose |
|-------|---------|
| `PostProcessor` | CRT effects: scanlines, bloom, chromatic aberration |
| `ParticleSystem` | Explosion, spawn, and trail particles |
| `SpriteRenderer` | Static methods for drawing all game entities with glow |
| `MazeRenderer` | Glowing vector-line maze walls |
| `Radar` | Minimap display showing all entities |
| `HUD` | Score, lives, dungeon counter, messages |

## Game Flow

```
NORMAL PHASE          WORLUK PHASE           WIZARD PHASE
    │                      │                      │
    ▼                      ▼                      ▼
┌─────────┐          ┌──────────┐          ┌──────────┐
│ 6 base  │  clear   │ Worluk   │  kill/   │ Wizard   │  defeat
│ enemies │ ──────►  │ spawns   │ escape   │ spawns   │ ──────► VICTORY
│         │          │ (bonus)  │ ──────►  │ (boss)   │
└─────────┘          └──────────┘          └──────────┘
```

## Enemy Types

| Type | Color | Points | Behavior |
|------|-------|--------|----------|
| Burwor | Blue | 100 | Basic grunt, doesn't shoot |
| Garwor | Orange | 200 | Can turn invisible (shimmer on radar) |
| Thorwor | Red | 500 | Aggressive, shoots at player |
| Worluk | Green | 1000 | Bonus creature, tries to escape through tunnels |
| Wizard | Purple | 2500 | Boss, teleports randomly, shoots rapidly, flickers |

## Key Implementation Details

### Maze
- 21x15 tile grid stored in `MAZE` constant (1=wall, 0=path)
- Row 7 has side tunnels (wraparound exits at x=0 and x=max)
- Walls rendered as glowing vector lines, not filled rectangles

### Collision System
- Tile-based collision with `collides_with_maze()` method
- Corner sliding implemented to prevent getting stuck at turns
- Spawn validation ensures entities never spawn inside walls

### Post-Processing Pipeline
```python
game_surface → bloom → chromatic_aberration → scanlines → screen
```

### Particle Types
- `explosion`: Radial burst on death (color-matched to enemy)
- `spawn`: Expanding ring when entity appears
- `trail`: Following bullet projectiles

## What's Implemented

- [x] CRT post-processing (scanlines, bloom, chromatic aberration)
- [x] Glowing neon maze walls with pulse animation
- [x] Player sprite with directional gun
- [x] All 5 enemy types with distinct sprites and AI
- [x] Particle effects (explosions, spawns, trails)
- [x] Radar minimap with flickering invisible enemies
- [x] LED-style HUD (score, lives, dungeon counter)
- [x] Bullet trails with glow
- [x] Phase-based gameplay (normal → worluk → wizard → victory)
- [x] Dungeon progression (score persists between levels)
- [x] Corner sliding for smooth movement

## What's NOT Implemented (Future Work)

### Audio
- [ ] Sound effects (shooting, explosions, enemy sounds)
- [ ] Votrax-style synthesized speech ("I am the Wizard of Wor!")
- [ ] Background music/rhythm that speeds up

### Gameplay
- [ ] Two-player mode (Player 2 as Yellow Worrior)
- [ ] Increasing difficulty per dungeon
- [ ] High score persistence
- [ ] Double Score Dungeon bonus
- [ ] Different maze layouts per dungeon

### Visual Polish
- [ ] Spawn gates/Wor-Pens with opening animation
- [ ] Teleport warp effect for Wizard
- [ ] Screen shake on explosions
- [ ] Vignette effect (implemented but not enabled)

## Constants Reference

```python
TILE_SIZE = 32
MAZE_WIDTH = 21
MAZE_HEIGHT = 15
GAME_WIDTH = 672   # 21 * 32
GAME_HEIGHT = 480  # 15 * 32
HUD_HEIGHT = 80
RADAR_HEIGHT = 60
SCREEN_HEIGHT = 620  # GAME + HUD + RADAR
```

## Color Palette

```python
NEON_BLUE = (0, 150, 255)      # Maze walls, Burwor
NEON_CYAN = (0, 255, 255)      # Player visor, player bullets
NEON_YELLOW = (255, 255, 0)    # Player body
NEON_RED = (255, 50, 50)       # Thorwor, enemy bullets
NEON_ORANGE = (255, 150, 0)    # Garwor
NEON_PURPLE = (200, 0, 255)    # Wizard
NEON_GREEN = (0, 255, 100)     # Worluk, score
```

## Known Issues

### Resolved
1. **✅ Isometric projection distortion** - RESOLVED by switching to Ursina engine

### Minor
2. Enemies can occasionally cluster near spawn points
3. Wizard teleport has no visual transition effect
4. Some sounds may not have corresponding audio files yet

---

## Game Versions

### 2D Neon (`wizard_of_wor.py`)
- **Status:** Complete and stable
- **Features:** CRT post-processing, scanlines, bloom, particle effects
- **Controls:** Arrow keys/WASD, Space to shoot

### Isometric 2.5D (`wizard_of_wor_iso.py`)
- **Status:** Complete - now using Ursina engine
- **Engine:** Ursina with orthographic camera
- **Features:** Rotatable camera (mouse drag), zoom (scroll wheel), proper 3D rendering
- **Controls:** Arrow keys/WASD, Space to shoot, Mouse drag to rotate, Scroll to zoom, M to reset camera
- **Note:** Old Pygame version backed up as `wizard_of_wor_iso_pygame.py`

### 3D First-Person (`wizard_of_wor_3d.py`)
- **Status:** Experimental
- **Engine:** Ursina
- **Notes:** Was deemed "not ideal for this type of game"

---

## Sound Assets

Located in `assets/sounds/`:

| File | Purpose |
|------|---------|
| `player-fire.wav` | Player shooting |
| `player-dead.wav` | Player death |
| `enemy-fire.wav` | Enemy shooting |
| `enemy-dead.wav` | Generic enemy death |
| `enemy-visible.wav` | Garwor decloaking |
| `worluk.wav` | Worluk spawn |
| `worluk-dead.wav` | Worluk death |
| `worluk-escape.wav` | Worluk escaping |
| `wizard-dead.wav` | Wizard death |
| `wizard-escape.wav` | Wizard escaping |
| `getready.wav` | Game start |
| `player-enters.wav` | Player spawn |
| `gameover.wav` | Game over |
| `doublescore.wav` | Double score bonus |
| `maze-exit.wav` | Maze exit/tunnel |
| `loop01-05.wav` | Background music |

---

## Dependencies

- Python 3.11+
- pygame 2.6.1

## Extending the Game

### Adding a New Enemy Type

1. Add color and points to `Enemy.__init__()` dictionaries
2. Add AI behavior in `Enemy.update()`
3. Add sprite rendering in `SpriteRenderer.draw_newenemy()`
4. Register in `Enemy.draw()` draw_funcs dictionary
5. Add to spawn logic in `Game.reset_game()` or new spawn method

### Adding Sound

```python
# In Game.__init__():
pygame.mixer.init()
self.sounds = {
    'shoot': pygame.mixer.Sound('assets/shoot.wav'),
    'explosion': pygame.mixer.Sound('assets/explosion.wav'),
}

# When shooting:
self.sounds['shoot'].play()
```

### Adding New Post-Processing Effect

1. Add method to `PostProcessor` class
2. Call it in `PostProcessor.process()` pipeline

---

*Last updated: 2026-01-10*
*Session: Switched isometric version from Pygame to Ursina engine - projection distortion issue RESOLVED*
