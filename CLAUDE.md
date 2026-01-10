# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
pdm install          # Install dependencies
pdm run game         # Run 2D neon version
pdm run game-iso     # Run isometric 2.5D version
pdm run game-3d      # Run 3D first-person version (Ursina)
```

## Game Versions

### 1. 2D Neon CRT (`wizard_of_wor.py`) - STABLE
Single-file Pygame game (~1850 lines) - Wizard of Wor clone with "Neon CRT Revival" aesthetic.
- Top-down view with CRT post-processing effects
- Complete gameplay with all enemy types and phases

### 2. Isometric 2.5D (`wizard_of_wor_iso.py`) - PLAYABLE
**Ursina engine** (~1350 lines) with orthographic camera for true isometric projection.
- Mouse drag to rotate view around the maze (Lazy Susan style)
- Scroll wheel to zoom in/out, M to reset camera
- **Textured underwater theme** with sand floor, teal walls, coral decorations, animated bubbles
- Proper 3D rendering with no projection distortion

**Key classes:**
- `IsometricCamera` - Orthographic camera with pivot-based rotation around maze center
- `MazeBuilder` - Creates 3D wall geometry with texture-mapped surfaces and procedural decorations
- `HUD` - Score, lives, and status display
- `GameManager` - Game loop and state management
- `Player`, `Enemy`, `Bullet` - 3D entities with grid-based movement

**Texture assets:**
- `assets/images/underwater_floor_tile.png` - Sandy beige floor texture
- `assets/images/underwater_wall_tile.png` - Teal wall texture
- `assets/images/underwater_background.png` - Deep ocean background
- `assets/images/underwater_assets/` - Decorator sprites:
  - Wall tops: `wall_plus.png`, `wall_t.png`, `wall_corner.png`, `wall_straight.png`
  - Decorations: `coral_pink_orange.png`, `coral_blue.png`, `seaweed_starfish.png`, `anemone_yellow_coral.png`
  - Props: `shell.png`, `rock.png`, `submarine.png`, `sparkle.png`
  - Particles: `bubble_large.png`, `bubble_small.png`

**Old Pygame version:** Backed up as `wizard_of_wor_iso_pygame.py`

### 3. 3D First-Person (`wizard_of_wor_3d.py`) - EXPERIMENTAL
Ursina engine first-person dungeon crawler.
- WASD movement, mouse look, click to shoot
- Full 3D maze with neon lighting

## Architecture

### 2D Version (`wizard_of_wor.py`)

**Core gameplay:**
- `Game` - Main loop, phase transitions (normal → worluk → wizard → victory)
- `Player` - Movement with corner sliding, shooting
- `Enemy` - Type-driven AI (burwor/garwor/thorwor/worluk/wizard)
- `Bullet` - Projectile with trail

**Rendering pipeline:**
- `PostProcessor` - CRT effects: `bloom → chromatic_aberration → scanlines`
- `ParticleSystem` - Explosions, spawn rings, bullet trails
- `SpriteRenderer` - Static draw methods for all entities with glow effects
- `MazeRenderer` - Pulsing vector-line walls
- `Radar` - Minimap with flickering invisible enemies
- `HUD` - LED-style score/lives/messages

### Isometric 2.5D Version (`wizard_of_wor_iso.py`)

**Core gameplay:**
- `GameManager` - Main loop, game state, phase transitions
- `IsometricCamera` - Pivot-based camera system with Lazy Susan rotation
- `MazeBuilder` - Constructs 3D maze geometry from MAZE array with:
  - Texture-mapped floor and walls
  - Smart wall-top decals (plus/T/corner/straight based on neighbors)
  - Procedural coral, seaweed, shell decorations
  - Animated floating bubbles and sparkles
- `HUD` - Score, lives, phase info display
- `Player`, `Enemy`, `Bullet` - 3D grid-based entities

**Rendering:**
- Ursina engine with orthographic camera for true isometric projection
- Texture-mapped floor and wall surfaces (underwater theme)
- Billboard sprites for decorations (always face camera)
- Animated elements: bubbles float upward, sparkles rotate

### Key Constants

**Shared:**
- `MAZE` constant: 21x15 tile grid (1=wall, 0=path). Row 7 has side tunnels for wraparound.

**2D Version:**
- Tile size: 32px each
- Screen: 672x480 (game area) + 80px (HUD) + 60px (radar) = 620px total

**Isometric Version:**
- Tile size: 1.0 units in 3D space
- Wall height: 0.8 units
- Screen: 1200x800 (orthographic view)

### Enemy Behavior

| Type | AI |
|------|-----|
| Burwor | Chases player, no shooting |
| Garwor | Chases, turns invisible periodically |
| Thorwor | Aggressive, shoots at player |
| Worluk | Panicked escape to side tunnels |
| Wizard | Teleports, rapid shooting, flickers |

## Sound Assets

Located in `assets/sounds/`. Mapped in `load_sounds()` (2D version):
- `player-fire.wav`, `player-dead.wav`, `player-enters.wav`
- `enemy-fire.wav`, `enemy-dead.wav`, `enemy-visible.wav`
- `worluk.wav`, `worluk-dead.wav`, `wizard-dead.wav`
- `gameover.wav`, `getready.wav`

## Extending

**2D Version - New enemy:** Add to `Enemy.__init__` dicts → `Enemy.update()` AI → `SpriteRenderer.draw_X()` → register in `Enemy.draw()` → spawn in `Game`

**2D Version - New effect:** Add method to `PostProcessor` → call in `PostProcessor.process()` pipeline

**Isometric Version - New textures:** Add PNG files to `assets/images/underwater_assets/` and reference in the `DECOR_TEXTURES` or `WALL_TOP_TEXTURES` dicts at the top of the file. MazeBuilder uses these for wall tops (`_add_wall_decal`), perimeter decorations (`_add_perimeter_decorations`), floor props (`_add_floor_decorations`), bubbles (`_create_bubble_particles`), and sparkles (`_add_sparkles`).

## Known Issues

See `HANDOFF.md` for detailed status.

**RESOLVED:**
- Pygame isometric projection distortion - switched to Ursina engine with proper 3D orthographic camera.

**OPEN (possibly macOS specific):**
- Ursina `model="plane"` does not render on macOS. **Workaround:** Use `model="quad"` with `rotation_x=90` instead.
- `window.color` setting not applied - background stays white instead of dark ocean blue.
