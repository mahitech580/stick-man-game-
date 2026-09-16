# 🥊 Stickman Arena — Advanced Edition

> A real-time 2D stickman fighting game built with Python and Turtle Graphics, featuring character-specific abilities, AI opponents, combo-based combat, defensive mechanics, special attacks, round-based matches, achievements, and persistent player statistics.

## 🎮 Overview

**Stickman Arena** is an object-oriented fighting game developed in Python using the built-in `turtle` graphics library.

The project goes beyond a simple graphics demo by implementing a complete game architecture with:

* Character selection
* Multiple playable fighters
* Real-time combat
* AI-controlled opponents
* Local two-player mode
* Character-specific statistics and special attacks
* Combo and damage scaling
* Blocking and parrying
* Stamina and energy systems
* Knockdowns and wake-up invulnerability
* Projectiles and visual effects
* Round and match management
* Difficulty levels
* Achievements
* Persistent player statistics

## ✨ Features

### 🥋 Combat System

* Light and heavy punches
* Light and heavy kicks
* Uppercuts
* Sweeps
* Dash attacks
* Projectile attacks
* Character-specific special moves
* Energy-based attack system
* Stamina-limited blocking
* Timed parry mechanic
* Knockdown and recovery system
* Hit effects and floating damage numbers
* Combo tracking with dynamic damage scaling

### 👊 Playable Characters

The game includes four fighters with different combat characteristics:

| Character   | Playstyle                    | Special Move |
| ----------- | ---------------------------- | ------------ |
| **RONIN**   | Balanced all-rounder         | Energy Wave  |
| **WHISPER** | Fast and aggressive          | Shadow Dash  |
| **TITAN**   | High health and heavy damage | Ground Slam  |
| **SPECTER** | Ranged / zoning fighter      | Triple Burst |

Each character has unique:

* Health
* Energy
* Stamina
* Movement speed
* Jump power
* Attack damage
* Special ability

## 🤖 AI System

The single-player mode includes an AI controller with four difficulty levels:

* **Easy**
* **Normal**
* **Hard**
* **Nightmare**

AI behavior dynamically considers:

* Player distance
* Incoming projectiles
* Player attacks
* Available energy
* Special cooldowns
* Ranged attacks
* Blocking
* Jumping
* Dash opportunities
* Attack selection

Difficulty changes AI reaction time, aggression, and damage scaling.

## 🏆 Match System

Matches use a **Best-of-3 round structure**.

The game includes:

* Round timer
* Round transitions
* Match victory detection
* Rematches
* Character selection replay
* Match statistics
* Game-over screen

## 🏅 Achievements

The game includes persistent achievements such as:

* **First Blood**
* **Flawless Victory**
* **Combo Master**
* **Comeback Kid**
* **Seasoned Fighter**
* **Perfect Timing**

Achievements are stored between sessions using a local JSON save file.

## 💾 Persistent Statistics

Player progress is stored in:

```text
stickman_fighter_save.json
```

The profile can track:

* Matches played
* Matches won
* Matches lost
* Best combo
* Unlocked achievements
* Character usage statistics

## 👥 Local 2-Player Mode

The game also supports local multiplayer.

### Player 1

```text
A / D       Move
W           Jump
S           Dash
J           Light Punch
K           Heavy Punch
N           Light Kick
M           Heavy Kick
U           Uppercut
H           Sweep
L           Projectile
F           Special
SPACE       Block / Parry
P           Pause
R           Restart
```

### Player 2

```text
← / →       Move
↑           Jump
↓           Dash
1           Light Punch
2           Heavy Punch
3           Light Kick
4           Heavy Kick
5           Uppercut
6           Sweep
7           Projectile
9           Special
0           Block / Parry
```

## 🧱 Architecture

The project follows an object-oriented architecture rather than putting the entire game into a single procedural loop.

Major components include:

```text
Game
├── Application
├── GameFactory
├── GameState
├── GameConfig
├── MatchManager
├── RoundManager
├── Fighter
│   ├── Player
│   └── Enemy
├── AIController
├── FighterState
│   ├── IdleState
│   ├── WalkingState
│   ├── JumpingState
│   ├── BlockingState
│   ├── AttackingState
│   ├── DashingState
│   ├── StunnedState
│   └── KnockedDownState
├── CharacterDefinition
├── ComboTracker
├── Projectile
├── Particle
├── HitEffect
├── DamageNumber
├── ComboPopup
├── Arena
├── HUD
├── InputManager
├── DifficultyManager
├── StatsManager
├── AchievementManager
└── Menu System
```

## 🛠️ Technologies

* **Python**
* **Turtle Graphics**
* **Object-Oriented Programming**
* **Abstract Base Classes**
* **Enums**
* **State Pattern**
* **JSON Persistence**
* **Real-Time Game Loop**
* **Keyboard & Mouse Input**
* **Collision / Hitbox Detection**

## 📁 Project Structure

```text
stick-man-game-/
│
├── stickman_arena.py
├── stickman_fighter_save.json
└── README.md
```

> The JSON save file is generated automatically when the game stores player progress.

## ▶️ Run Locally

### Requirements

Python 3.x

### Start the game

```bash
python stickman_arena.py
```

A Turtle Graphics window will open with the main menu.

## 🌐 Run Online

The game can also be tested through online Python environments that support Turtle graphics.

Recommended:

**Replit — Python Turtle**

https://replit.com/languages/python_turtle

Upload the Python source file, run the program, and use the graphical interface provided by the environment.

## 🧠 What This Project Demonstrates

This project demonstrates practical implementation of:

* Object-oriented software design
* State-machine architecture
* Real-time update loops
* Event-driven input handling
* Collision detection
* Game physics
* AI decision logic
* Resource management
* Persistent storage
* Modular UI design
* Gameplay balancing
* Animation and visual effects

## 🚀 Future Improvements

Potential extensions include:

* Sound effects and background music
* More playable characters
* Additional arenas
* Online multiplayer
* Improved animation system
* Controller support
* Advanced AI behavior
* Replay system
* Leaderboards
* Save profiles
* More special attacks
* Improved graphical rendering

## 👨‍💻 Author

**Mahendra Sai Kondaveeti**

Computer Science & Engineering Graduate | Aspiring Software Developer

GitHub: [@mahitech580](https://github.com/mahitech580)

---

⭐ **Star the repository if you found the project interesting!**
