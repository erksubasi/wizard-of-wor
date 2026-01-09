# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
pdm install          # Install dependencies
pdm run game         # Run the game
```

## Architecture

Single-file Pygame game (`wizard_of_wor.py`, ~1160 lines) - a Wizard of Wor clone with "Neon CRT Revival" aesthetic.

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

- Maze: 21x15 tiles, 32px each. Row 7 has side tunnels (wraparound).
- Screen: 672x620 (game area + radar + HUD)
- `MAZE` constant: 2D array (1=wall, 0=path)

### Enemy Behavior

| Type | AI |
|------|-----|
| Burwor | Chases player, no shooting |
| Garwor | Chases, turns invisible periodically |
| Thorwor | Aggressive, shoots at player |
| Worluk | Panicked escape to side tunnels |
| Wizard | Teleports, rapid shooting, flickers |

### Extending

**New enemy:** Add to `Enemy.__init__` dicts → `Enemy.update()` AI → `SpriteRenderer.draw_X()` → register in `Enemy.draw()` → spawn in `Game`

**New effect:** Add method to `PostProcessor` → call in `PostProcessor.process()` pipeline
