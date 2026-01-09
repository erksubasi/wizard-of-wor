# Wizard of Wor - Neon CRT Revival Edition

## Project Overview

A single-player Python/Pygame clone of the classic 1980 Midway arcade game "Wizard of Wor" with a modernized "Neon CRT Revival" aesthetic featuring glowing vector graphics, CRT post-processing effects, and particle systems.

## Quick Start

```bash
cd /Users/erk/repos/oyunbaz/wow
pdm install          # Install dependencies
pdm run game         # Run the game
```

**Controls:**
- Arrow keys or WASD: Move
- Space: Shoot
- R: Restart/Continue to next dungeon
- ESC: Quit

## Project Structure

```
wow/
├── wizard_of_wor.py   # Main game file (single-file architecture)
├── pyproject.toml     # PDM project config
├── pdm.lock           # Locked dependencies
└── .venv/             # Virtual environment
```

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

1. Enemies can occasionally cluster near spawn points
2. Wizard teleport has no visual transition effect
3. No audio feedback for any actions

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

*Last updated: 2026-01-09*
*Session: Initial implementation complete with Neon CRT Revival aesthetic*
