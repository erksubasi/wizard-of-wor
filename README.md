# Wizard of Wor - Neon CRT Revival

A modern reimagining of the classic 1981 arcade game **Wizard of Wor**, featuring neon vector graphics, CRT effects, and terrifying alien monsters!

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Pygame](https://img.shields.io/badge/Pygame-2.6+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 🎮 About

You are a **Space Marine** trapped in the deadly dungeons of Wor! Battle through waves of horrifying alien creatures, defeat the eldritch Wizard, and escape with your life.

### Features
- 🌟 **Neon Vector Graphics** - Glowing retro-futuristic visuals
- 📺 **CRT Effects** - Authentic scanlines and chromatic aberration
- 👾 **Terrifying Monsters** - Each enemy has unique behaviors and appearances
- 🔊 **8-bit Audio** - Crunchy sound effects and Votrax-style voice synthesis
- ⚡ **Smooth Gameplay** - Optimized collision detection and movement

## 🕹️ Controls

| Key | Action |
|-----|--------|
| Arrow Keys / WASD | Move |
| Space | Shoot |
| ESC | Quit |

## 👾 Enemies

| Monster | Description |
|---------|-------------|
| **Burwor** | Alien Crawler Beast with snapping mandibles |
| **Garwor** | Cloaking Predator with infrared vision (can turn invisible!) |
| **Thorwor** | Xenomorph Scorpion with venomous stinger tail |
| **Worluk** | Flying Demon Wraith - kill it for double points! |
| **Wizard of Wor** | Eldritch Cosmic Horror - the final boss |

## 🚀 Installation

### Prerequisites
- Python 3.11+
- PDM (Python package manager)

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/wizard-of-wor.git
cd wizard-of-wor

# Install dependencies with PDM
pdm install

# Generate sound assets
pdm run python generate_sounds.py

# Run the game!
pdm run python wizard_of_wor.py
```

### Alternative (without PDM)

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install pygame numpy

# Generate sounds and run
python generate_sounds.py
python wizard_of_wor.py
```

## 📁 Project Structure

```
wizard-of-wor/
├── wizard_of_wor.py    # Main game file
├── generate_sounds.py  # Audio asset generator
├── assets/
│   └── sounds/         # Generated audio files
├── pyproject.toml      # Project configuration
└── README.md
```

## 🎯 Gameplay Tips

1. **Use the tunnels** - Side tunnels wrap around the screen for quick escapes
2. **Watch for Garwors** - They shimmer when invisible, stay alert!
3. **Kill the Worluk** - Don't let it escape for bonus points
4. **Corner sliding** - The game helps you navigate tight corners smoothly

## 📜 Original Game

Wizard of Wor was created by **Midway** in 1981. This is a fan remake paying homage to the original classic with a modern neon aesthetic.

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

---

*"I AM THE WIZARD OF WOR!"* 🧙‍♂️
