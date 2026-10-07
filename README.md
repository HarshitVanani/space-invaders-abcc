# 🚀 Space Invaders (Tkinter Vector Edition)

A modern, object-oriented implementation of the classic **Space Invaders** arcade game built using **Python 3** and **Tkinter**. This project demonstrates modular Python software architecture, clean OOP paradigms, procedural vector drawing on a canvas, and robust key-binding management.

Developed as a mini-project submission for the **CIE-PR** university curriculum.

---

## 📌 Features

* **Modular Architecture**: Clean separation of application entry, game engine state, dynamic entities, and configuration constants.
* **Vector Graphics**: Procedurally drawn player ship, enemy fleet, and dynamic projectile elements rendering entirely on Tkinter's native `Canvas`.
* **State Management**: Built-in mechanisms for continuous keyboard input handling, live scoring updates, wave progression, pausing, and soft resets.
* **Universal Focus Control**: Global event binding layer ensuring consistent responsiveness across different operating systems and keyboard states.

---

## 📁 Project Structure

```text
space-invaders-tkinter/
├── config.py         # Global game parameters, canvas dimensions, and color schemes
├── entities.py       # Object-oriented classes for Player, Alien, and Bullet
├── game_engine.py    # Main animation tick loop, collision logic, and state management
├── main.py           # Application entry point, window management, and input bindings
└── README.md         # Project documentation