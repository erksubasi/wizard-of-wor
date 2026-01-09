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
Axonometric isometric view (~1400 lines) with rotatable camera.
- Mouse drag to rotate view, scroll to zoom, M to reset
- Custom 3D-looking wall blocks with proper face visibility
- Depth sorting using screen Y position (painter's algorithm)

**Key isometric functions:**
- `cart_to_iso(x, y)` - Grid coords → screen coords with rotation
- `get_tile_corner_offsets()` - Shared corner calculation for tiles/walls
- `get_rotated_depth(x, y)` - Screen Y for depth sorting

**Camera system:** `Camera` class with `angle`, `zoom`, smooth interpolation

### 3. 3D First-Person (`wizard_of_wor_3d.py`) - EXPERIMENTAL
Ursina engine first-person dungeon crawler.
- WASD movement, mouse look, click to shoot
- Full 3D maze with neon lighting

## Architecture (2D Version)

### Class Structure

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

### Key Constants

- Maze: 21x15 tiles, 32px each (2D) / 48x24 isometric (iso). Row 7 has side tunnels.
- Screen: 672x620 (2D), 1200x800 (iso)
- `MAZE` constant: 2D array (1=wall, 0=path)

### Enemy Behavior

| Type | AI |
|------|-----|
| Burwor | Chases player, no shooting |
| Garwor | Chases, turns invisible periodically |
| Thorwor | Aggressive, shoots at player |
| Worluk | Panicked escape to side tunnels |
| Wizard | Teleports, rapid shooting, flickers |

## Sound Assets

Located in `assets/sounds/`. Mapped in `load_sounds()`:
- `player-fire.wav`, `player-dead.wav`, `player-enters.wav`
- `enemy-fire.wav`, `enemy-dead.wav`, `enemy-visible.wav`
- `worluk.wav`, `worluk-dead.wav`, `wizard-dead.wav`
- `gameover.wav`, `getready.wav`

## Extending

**New enemy:** Add to `Enemy.__init__` dicts → `Enemy.update()` AI → `SpriteRenderer.draw_X()` → register in `Enemy.draw()` → spawn in `Game`

**New effect:** Add method to `PostProcessor` → call in `PostProcessor.process()` pipeline

## Known Issues

See `HANDOFF.md` for detailed status. Key issue:
- Isometric view has minor projection distortion at extreme rotation angles
