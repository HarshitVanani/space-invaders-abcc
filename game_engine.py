import config
from entities import Alien, Bullet

class GameEngine:
    def __init__(self, canvas, player, aliens, app):
        self.canvas = canvas
        self.player = player
        self.aliens = aliens
        self.app = app
        self.bullets = []
        
        self.score = 0
        self.wave = 1
        self.game_over = False
        self.is_paused = False
        
        # Motion state for aliens
        self.alien_dir_x = config.ALIEN_SPEED_X
        
        # Dynamic HUD UI
        self.hud_text = self.canvas.create_text(
            10, 15, 
            anchor="nw", 
            text=f"Score: {self.score}  |  Wave: {self.wave}", 
            fill="#00FF66", 
            font=("Consolas", 14, "bold")
        )
        self.game_over_text = None
        self.pause_text = None

    def toggle_pause(self):
        """Toggles pause state and overlays UI text."""
        if self.game_over:
            return

        self.is_paused = not self.is_paused

        if self.is_paused:
            self.pause_text = self.canvas.create_text(
                config.WINDOW_WIDTH / 2, 
                config.WINDOW_HEIGHT / 2, 
                text="GAME PAUSED\n\nPress 'P' to Resume", 
                fill="#00F0FF", 
                font=("Consolas", 20, "bold"), 
                justify="center"
            )
        else:
            if self.pause_text:
                self.canvas.delete(self.pause_text)
                self.pause_text = None
            self.tick()

    def shoot(self):
        """Spawns bullet from rocket tip."""
        if self.game_over or self.is_paused:
            return
        
        if len(self.bullets) < config.MAX_BULLETS:
            tx, ty = self.player.get_tip_pos()
            bullet = Bullet(self.canvas, tx, ty)
            self.bullets.append(bullet)

    def tick(self):
        """Core Game Animation Loop (~60 FPS)."""
        if self.game_over or self.is_paused:
            return

        # 1. Update Bullets
        for bullet in self.bullets[:]:
            bullet.update()
            if bullet.is_offscreen():
                bullet.destroy()
                self.bullets.remove(bullet)

        # 2. Update Aliens & Edge Detection
        reverse_dir = False
        for alien in self.aliens:
            pos = alien.get_pos()
            if not pos:
                continue

            if pos[2] >= config.WINDOW_WIDTH - 10 or pos[0] <= 10:
                reverse_dir = True

            # Invasion line reached -> Game Over
            if pos[3] >= 610:
                self.trigger_game_over()
                return

        if reverse_dir:
            self.alien_dir_x *= -1
            for alien in self.aliens:
                alien.move(0, config.ALIEN_DROP_Y)

        for alien in self.aliens:
            alien.move(self.alien_dir_x, 0)

        # 3. Collision Detection (Bullet vs Alien)
        for bullet in self.bullets[:]:
            b_coords = self.canvas.coords(bullet.core)
            if not b_coords:
                continue

            for alien in self.aliens[:]:
                a_coords = alien.get_pos()
                if not a_coords:
                    continue

                if (b_coords[0] < a_coords[2] and b_coords[2] > a_coords[0] and
                    b_coords[1] < a_coords[3] and b_coords[3] > a_coords[1]):
                    
                    bullet.destroy()
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    
                    alien.destroy()
                    self.aliens.remove(alien)
                    
                    self.score += 20
                    self.update_hud()
                    break

        # Check Next Wave Condition
        if not self.aliens:
            self.wave += 1
            self.update_hud()
            self.app.create_alien_fleet()

        self.canvas.after(16, self.tick)

    def update_hud(self):
        """Updates top HUD scores."""
        self.canvas.itemconfig(
            self.hud_text, 
            text=f"Score: {self.score}  |  Wave: {self.wave}"
        )

    def trigger_game_over(self):
        """Displays game over banner."""
        self.game_over = True
        self.game_over_text = self.canvas.create_text(
            config.WINDOW_WIDTH / 2, 
            config.WINDOW_HEIGHT / 2, 
            text="GAME OVER - INVASION SUCCESSFUL!\n\nPress 'R' to Restart", 
            fill="#FF0055", 
            font=("Consolas", 18, "bold"), 
            justify="center"
        )

    def reset_game(self):
        """Resets game state and reloads entities for a fresh match."""
        if not self.game_over and not self.is_paused:
            return

        # Clear text overlays
        if self.game_over_text:
            self.canvas.delete(self.game_over_text)
            self.game_over_text = None
        if self.pause_text:
            self.canvas.delete(self.pause_text)
            self.pause_text = None

        # Clean up remaining entities
        for b in self.bullets:
            b.destroy()
        self.bullets.clear()

        for a in self.aliens:
            a.destroy()
        self.aliens.clear()

        # Reset Stats
        self.score = 0
        self.wave = 1
        self.game_over = False
        self.is_paused = False
        self.alien_dir_x = config.ALIEN_SPEED_X
        self.update_hud()

        # Re-spawns fleet and starts loop
        self.app.create_alien_fleet()
        self.tick()