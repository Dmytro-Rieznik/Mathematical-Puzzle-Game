# Mathematical Puzzle Game

A mathematical puzzle game developed in **Python** using **PyGame**.

The project was created as a college diploma project for the topic **"Mathematical Puzzles in Games"**. The gameplay is based on building mathematical expressions by connecting numbered nodes with wires and mathematical operators.

Levels are described using JSON files, allowing new puzzles to be added without modifying the game logic.

---

## Gameplay

Each level contains several numbered input nodes and one target output node.

The objective is to obtain the required output value by connecting inputs with wires and mathematical operators.

Available operators:

- Addition
- Subtraction
- Multiplication
- Division
- Square
- Square Root
- Cube
- Cube Root

For subtraction and division, the order of operands matters. A priority connection allows the player to select which input is processed first.

---

## Implementation

The project includes:

- Object-oriented project structure
- JSON-based level configuration
- Recursive graph traversal used to validate completed puzzles
- Progress saving system
- Level selection menu

---

## Technologies

- Python
- PyGame
- JSON

---

## Screenshots

### Level 1
Introduction to the core gameplay mechanics.

<img src="screenshots/level_1_completed.png" width="600">

### Level 2
Demonstrates subtraction and the priority connection mechanic.

<img src="screenshots/level_2_completed.png" width="600">

### Level 4
Initial state of one of the larger puzzles.

<img src="screenshots/level_4_empty.png" width="600">

### Level 4
Completed solution demonstrating mathematical operators and wire routing.

<img src="screenshots/level_4_completed.png" width="600">

---

## Running the Project

```bash
pip install -r requirements.txt
python main.py
```
