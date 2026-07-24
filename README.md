# X-Wing Fighter - Arcade Edition

A feature-rich, 2D vertical scrolling arcade space shooter built with **Python** and **Pygame**, heavily inspired by classic 1980s arcade cabinet titles like *Star Wars* and *Galaga*.

## Features
- **Progressive Wave System:** Increasing enemy speeds, spawn rates, and dynamic difficulty scaling across sectors.
- **Capital Flagship Boss Fights:** Encounter Star Destroyer capital ships every 5 level - 1, featuring multi-phase combat (Turret tracking + Superlaser charging sequence).
- **Synthetic Retro Audio:** Procedurally generated 8-bit laser and explosion sound effects using Python's `array` and Pygame's `mixer` pre-init buffers—no external asset files required.
- **Persistent High Score Leaderboard:** JSON-backed top 10 arcade high score tracking with 3-character initials entry.
- **Power-Up Matrix:** Collectable field power-ups including Shield boosters (S), Quad-Blaster weapon upgrades (W), Hyperdrive Time Dilation (H), and sector-clearing Seismic Charge Bombs (B).

## Controls
- **A / D:** Move Left / Right
- **SPACEBAR:** Fire Lasers / Insert Coin / Progress Menus
- **ENTER:** Lock High Score Initials

## Installation & Running
1. Download the latest `Xwing.exe` release from the releases page.
2. Ensure `highscores.json` is in the same directory (or it will be automatically generated upon your first high score save).
3. Double-click `Xwing.exe` to launch the game.
