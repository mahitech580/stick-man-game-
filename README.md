# 🥊 Stick Man Game

A real-time **2D Stickman Fighting Game** built entirely with **Python and Pygame**. The project focuses heavily on **Object-Oriented Programming (OOP)** while providing fast, responsive gameplay with combat, AI, effects, health systems, and projectiles.

## 🎮 Game Features

* ⚡ Real-time 60 FPS gameplay
* 🥊 Multiple melee attacks
* 🦵 Kick and heavy attacks
* 💥 Energy projectile attack
* 🛡️ Blocking system
* ❤️ Player and enemy health bars
* 🔋 Energy system
* 🔥 Combo system
* 💫 Hit effects and particles
* 🤖 AI-controlled enemy fighter
* 🏃 Smooth movement and jumping
* 🎯 Attack hitboxes and collision detection
* 🔄 Match restart system
* ⏸️ Pause functionality
* 🏆 Round-based fighting system
* 🎨 Dynamic Pygame graphics

## 🕹️ Controls

| Key     | Action       |
| ------- | ------------ |
| `A`     | Move Left    |
| `D`     | Move Right   |
| `W`     | Jump         |
| `J`     | Jab / Punch  |
| `K`     | Heavy Punch  |
| `I`     | Kick         |
| `O`     | Uppercut     |
| `L`     | Energy Blast |
| `SPACE` | Block        |
| `P`     | Pause        |
| `R`     | Restart      |

## 🧠 OOP Concepts Used

This project is designed around Object-Oriented Programming.

### Classes and Objects

The game is divided into independent classes such as:

* `Game`
* `Fighter`
* `Player`
* `Enemy`
* `Projectile`
* `Particle`
* `HealthBar`
* `HUD`
* `InputManager`
* `Background`
* `GameObject`

### Encapsulation

Fighter properties such as health, energy, movement state, and combat state are managed inside their respective classes.

### Inheritance

The player and enemy fighters inherit common functionality from the `Fighter` class.

```text
GameObject
     │
     └── Fighter
          ├── Player
          └── Enemy
```

### Abstraction

Abstract base classes are used for common game-object behavior.

### Polymorphism

Different game objects implement their own `update()` and `draw()` behavior.

### Composition

Complex objects such as the `Game` contain and coordinate fighters, projectiles, particles, effects, HUD components, and input handling.

### State-Based Design

Combat and movement behavior are separated into logical states and systems to keep the game architecture manageable.

## 🛠️ Technologies

* **Python 3.11+**
* **Pygame 2.6.1**
* Object-Oriented Programming
* Real-time game loop
* Collision detection
* Vector mathematics
* Event-driven keyboard input

## 📦 Installation

Clone the repository:

```bash
git clone https://github.com/mahitech580/stick-man-game-.git
cd stick-man-game-
```

Install Pygame:

```bash
python -m pip install pygame
```

Run the game:

```bash
python index.py
```

## 🗂️ Project Structure

```text
stick-man-game-/
│
├── index.py
├── README.md
├── requirements.txt
└── assets/
```

## 📋 Requirements

Create a `requirements.txt` file containing:

```text
pygame==2.6.1
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## ⚔️ Gameplay

The player fights an AI-controlled stickman opponent in an arena.

The objective is to reduce the opponent's health to zero while using:

```text
Movement
Jumping
Punches
Kicks
Blocking
Energy attacks
Combos
```

The enemy dynamically approaches the player and chooses attacks based on distance and combat conditions.

## 🚀 Performance

The game uses a controlled **60 FPS game loop** with delta-time based movement.

This allows:

* Smooth movement
* Responsive controls
* Consistent physics
* Fast combat
* Efficient rendering
* Real-time particle effects

## 🎯 Learning Objectives

This project is useful for practicing:

```text
Python
OOP
Inheritance
Polymorphism
Abstraction
Encapsulation
Game Development
Pygame
Collision Detection
Game Physics
AI Logic
Event Handling
Real-Time Programming
```

## 🔮 Future Improvements

Possible upgrades include:

* Character sprite animations
* Multiple playable fighters
* Local two-player mode
* More enemy AI levels
* Special attacks
* Combo chains
* Sound effects
* Background music
* Character selection
* Multiple arenas
* Online multiplayer
* Tournament mode
* Save/load system

## 👨‍💻 Author

**Mahendra K**

GitHub:
https://github.com/mahitech580

