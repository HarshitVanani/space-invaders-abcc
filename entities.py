import config

class Player:
    """Detailed Spaceship vector model."""
    def __init__(self, canvas):
        self.canvas = canvas
        self.parts = []

        # Main Body (Cyan Triangle)
        self.ship_body = self.canvas.create_polygon(
            300, 630, 280, 660, 320, 660, 
            fill="#00F0FF", outline="#FFFFFF", width=2
        )
        # Cockpit Canopy
        self.cockpit = self.canvas.create_oval(
            294, 642, 306, 656, 
            fill="#FFD700", outline=""
        )
        # Left Wing Thruster
        self.left_wing = self.canvas.create_rectangle(
            275, 652, 282, 662, 
            fill="#FF0055", outline=""
        )
        # Right Wing Thruster
        self.right_wing = self.canvas.create_rectangle(
            318, 652, 325, 662, 
            fill="#FF0055", outline=""
        )

        self.parts = [self.ship_body, self.cockpit, self.left_wing, self.right_wing]

    def move_left(self):
        coords = self.canvas.coords(self.ship_body)
        if coords[2] > 20:
            for part in self.parts:
                self.canvas.move(part, -config.PLAYER_SPEED, 0)

    def move_right(self):
        coords = self.canvas.coords(self.ship_body)
        if coords[4] < config.WINDOW_WIDTH - 20:
            for part in self.parts:
                self.canvas.move(part, config.PLAYER_SPEED, 0)

    def get_tip_pos(self):
        coords = self.canvas.coords(self.ship_body)
        return coords[0], coords[1]


class Bullet:
    """High-Visibility Glowing Laser Beam."""
    def __init__(self, canvas, x, y):
        self.canvas = canvas
        # Outer Laser Glow (Thick Neon Red)
        self.glow = self.canvas.create_rectangle(
            x - 3, y - 22, x + 3, y,
            fill="#FF0055", outline=""
        )
        # Inner Core Beam (Bright Yellow)
        self.core = self.canvas.create_rectangle(
            x - 1, y - 20, x + 1, y - 2,
            fill="#FFFF00", outline=""
        )

        # Force lasers to draw ABOVE all other canvas layers
        self.canvas.tag_raise(self.glow)
        self.canvas.tag_raise(self.core)

    def update(self):
        self.canvas.move(self.glow, 0, -config.BULLET_SPEED)
        self.canvas.move(self.core, 0, -config.BULLET_SPEED)

    def is_offscreen(self):
        coords = self.canvas.coords(self.core)
        if not coords:
            return True
        return coords[3] < 0  # Off top boundary

    def destroy(self):
        self.canvas.delete(self.glow)
        self.canvas.delete(self.core)


class Alien:
    """Bee / Bug Spaceship vector entity."""
    def __init__(self, canvas, x, y, color):
        self.canvas = canvas
        self.parts = []

        # Bee Body
        self.body = self.canvas.create_oval(
            x + 10, y + 5, x + 30, y + 25, 
            fill=color, outline="#FFFFFF", width=1
        )
        # Left Wing
        self.wing_l = self.canvas.create_polygon(
            x + 10, y + 10, x - 2, y + 2, x + 5, y + 18, 
            fill="#00FFFF", outline=""
        )
        # Right Wing
        self.wing_r = self.canvas.create_polygon(
            x + 30, y + 10, x + 42, y + 2, x + 35, y + 18, 
            fill="#00FFFF", outline=""
        )
        # Glowing Eyes
        self.eye_l = self.canvas.create_oval(
            x + 14, y + 20, x + 18, y + 24, 
            fill="#FF0000", outline=""
        )
        self.eye_r = self.canvas.create_oval(
            x + 22, y + 20, x + 26, y + 24, 
            fill="#FF0000", outline=""
        )

        self.parts = [self.body, self.wing_l, self.wing_r, self.eye_l, self.eye_r]
        self.id = self.body  # Main hitbox anchor

    def move(self, dx, dy):
        for part in self.parts:
            self.canvas.move(part, dx, dy)

    def get_pos(self):
        return self.canvas.coords(self.body)

    def destroy(self):
        for part in self.parts:
            self.canvas.delete(part)