import tkinter as tk
import config
from entities import Player, Alien
from game_engine import GameEngine

class SpaceInvadersApp:
    def __init__(self, root):
        self.root = root
        self.root.title(config.WINDOW_TITLE)
        self.root.resizable(False, False)

        # Create Canvas Engine
        self.canvas = tk.Canvas(
            root, 
            width=config.WINDOW_WIDTH, 
            height=config.WINDOW_HEIGHT, 
            bg=config.BG_COLOR
        )
        self.canvas.pack()

        # Initialize Game Entities
        self.player = Player(self.canvas)
        self.aliens = []
        self.create_alien_fleet()

        # Initialize Core Game Engine Loop
        self.engine = GameEngine(self.canvas, self.player, self.aliens, self)

        # Force keyboard focus to the main window
        self.root.focus_force()

        # Global Key Event Listener (Catches 'r', 'R', 'p', 'P', Space, Arrows)
        self.root.bind("<KeyPress>", self.handle_keypress)

        # Start Dynamic Animation Frame Loop
        self.engine.tick()

    def handle_keypress(self, event):
        """Universal keypress handler to prevent focus loss issues."""
        key = event.keysym.lower()

        # Movement (Blocked if paused)
        if not self.engine.is_paused:
            if key == "left":
                self.player.move_left()
            elif key == "right":
                self.player.move_right()

        # Firing
        if key == "space":
            self.engine.shoot()

        # Pause / Resume
        if key == "p":
            self.engine.toggle_pause()

        # Restart Game
        if key == "r":
            self.engine.reset_game()

    def create_alien_fleet(self):
        """Generate matrix of aliens using config parameters."""
        for row in range(config.ALIEN_ROWS):
            color = config.ALIEN_ROW_1_COLOR if row % 2 == 0 else config.ALIEN_ROW_2_COLOR
            for col in range(config.ALIEN_COLS):
                x = 60 + col * config.ALIEN_X_SPACING
                y = 60 + row * config.ALIEN_Y_SPACING
                alien = Alien(self.canvas, x, y, color)
                self.aliens.append(alien)

def main():
    root = tk.Tk()
    app = SpaceInvadersApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()