import pygame
import sys
import random
from datetime import datetime
import json
import os

# Get script directory for leaderboard file
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LEADERBOARD_FILE = os.path.join(SCRIPT_DIR, "snake_leaderboard.json")

pygame.mixer.init()

# Game BGM
game_bg_soundpath = os.path.join(SCRIPT_DIR, "snake_rush_bgm.wav")
game_bg = pygame.mixer.Sound(game_bg_soundpath)
game_bg.set_volume(0.3)  # Set volume

# Game Over Sound
game_over_soundpath = os.path.join(SCRIPT_DIR, "game_over.wav")
game_over_sound = pygame.mixer.Sound(game_over_soundpath)
game_over_sound.set_volume(0.7)  # Set volume

# Food capture sound
food_capture_soundpath = os.path.join(SCRIPT_DIR, "food_capture_sound.wav")
food_capture_sound = pygame.mixer.Sound(food_capture_soundpath)
food_capture_sound.set_volume(0.5)

# Settings Variables
bgm_muted = False
sfx_muted = False
game_bg_playing = False
fullscreen = False

# Initialize Pygame
pygame.init()

# Calculate grid-aligned screen dimensions
BLOCK_SIZE = 40
GRID_WIDTH = pygame.display.Info().current_w // BLOCK_SIZE
GRID_HEIGHT = pygame.display.Info().current_h // BLOCK_SIZE
SCREEN_WIDTH = GRID_WIDTH * BLOCK_SIZE
SCREEN_HEIGHT = GRID_HEIGHT * BLOCK_SIZE

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption('Snake - Endless Mode')

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)
GRAY = (100, 100, 100)
DARK_GRAY = (50, 50, 50)
LIGHT_GRAY = (150, 150, 150)
ORANGE = (255, 165, 0)

# Game settings
BASE_FPS = 8
MAX_FPS = 20
SPEED_INTERVAL = 5  # Increase speed every 5 points
clock = pygame.time.Clock()

class Button:
    def __init__(self, x, y, width, height, text, color, hover_color, text_color=WHITE):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False
        self.font = pygame.font.Font(None, 36)
        
    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=5)
        
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
        
    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered
        
    def is_clicked(self, pos, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(pos)
        return False

class ToggleButton(Button):
    def __init__(self, x, y, width, height, text, color, hover_color, text_color=WHITE, is_on=False):
        super().__init__(x, y, width, height, text, color, hover_color, text_color)
        self.is_on = is_on
        
    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=5)
        
        status = "ON" if self.is_on else "OFF"
        full_text = f"{self.text}: {status}"
        text_surf = self.font.render(full_text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
        
    def toggle(self):
        self.is_on = not self.is_on
        return self.is_on

class LeaderBoard:
    def __init__(self):
        self.scores = []
        self.load_scores()
    
    def load_scores(self):
        if os.path.exists(LEADERBOARD_FILE):
            try:
                with open(LEADERBOARD_FILE, 'r') as f:
                    self.scores = json.load(f)
                    # Ensure scores are sorted
                    self.scores.sort(key=lambda x: x['score'], reverse=True)
                    # Keep only top 10
                    self.scores = self.scores[:10]
            except (json.JSONDecodeError, IOError):
                # If file is corrupted, start fresh
                self.scores = []
        else:
            # Create file if it doesn't exist
            with open(LEADERBOARD_FILE, 'w') as f:
                json.dump([], f)
    
    def save_scores(self):
        with open(LEADERBOARD_FILE, 'w') as f:
            json.dump(self.scores, f)
    
    def add_score(self, score, length):
        if score > 0:
            new_entry = {
                'score': score,
                'length': length,
                'date': datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            
            # Add new score and sort
            self.scores.append(new_entry)
            self.scores.sort(key=lambda x: x['score'], reverse=True)
            
            # Keep only top 10
            if len(self.scores) > 10:
                self.scores = self.scores[:10]
            
            self.save_scores()
    
    def get_top_scores(self, limit=10):
        return self.scores[:limit]
    
    def get_high_score(self):
        return self.scores[0]['score'] if self.scores else 0
    
    def is_high_score(self, score):
        if not self.scores:
            return True
        return len(self.scores) < 10 or score > min(entry['score'] for entry in self.scores)

class Snake:
    def __init__(self):
        self.reset()
        
    def reset(self):
        grid_x = GRID_WIDTH // 2
        grid_y = GRID_HEIGHT // 2
        self.positions = [(grid_x * BLOCK_SIZE, grid_y * BLOCK_SIZE)]
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.length = 1
        self.score = 0
        self.color = GREEN
    
    def get_head_position(self):
        return self.positions[0]
    
    def update(self):
        self.direction = self.next_direction
        
        head_x, head_y = self.get_head_position()
        dir_x, dir_y = self.direction
        
        new_x = (head_x + dir_x * BLOCK_SIZE) % SCREEN_WIDTH
        new_y = (head_y + dir_y * BLOCK_SIZE) % SCREEN_HEIGHT
        
        if (new_x, new_y) in self.positions[1:]:
            return True  # Game over
            
        self.positions.insert(0, (new_x, new_y))
        if len(self.positions) > self.length:
            self.positions.pop()
        
        return False
    
    def change_direction(self, direction):
        if (direction[0] * -1, direction[1] * -1) != self.direction:
            self.next_direction = direction
    
    def draw(self, surface):
        for i, p in enumerate(self.positions):
            shade = 255 - (i * 3)
            shade = max(50, shade)
            color = (0, shade, 0)
            
            if i == 0:
                color = CYAN
            
            rect = pygame.Rect(p[0], p[1], BLOCK_SIZE, BLOCK_SIZE)
            pygame.draw.rect(surface, color, rect)
            pygame.draw.rect(surface, BLACK, rect, 1)

class Food:
    def __init__(self, food_type=1):
        self.type = food_type
        self.color = RED
        self.position = (0, 0)
        self.randomize_position()
        self.timer = 0
        self.active = True
        self.points = 1
        
        if self.type == 2:
            self.color = YELLOW
            self.timer = 150
            self.points = 2
        elif self.type == 3:
            self.color = BLUE
            self.timer = 100
            self.points = 3
        elif self.type == 4:
            self.color = PURPLE
            self.timer = 80
            self.points = 5
    
    def randomize_position(self):
        self.position = (
            random.randint(0, GRID_WIDTH - 1) * BLOCK_SIZE,
            random.randint(0, GRID_HEIGHT - 1) * BLOCK_SIZE
        )
    
    def update(self):
        if self.type > 1:
            self.timer -= 1
            if self.timer <= 0:
                self.active = False
        return self.active
    
    def draw(self, surface):
        if self.active:
            rect = pygame.Rect(self.position[0], self.position[1], BLOCK_SIZE, BLOCK_SIZE)
            pygame.draw.rect(surface, self.color, rect)
            pygame.draw.rect(surface, BLACK, rect, 1)
            
            center_x = self.position[0] + BLOCK_SIZE//2
            center_y = self.position[1] + BLOCK_SIZE//2
            
            if self.type == 2:
                pygame.draw.circle(surface, BLACK, (center_x, center_y), BLOCK_SIZE//4)
            elif self.type == 3:
                points = [
                    (center_x, self.position[1] + 2),
                    (self.position[0] + BLOCK_SIZE - 2, center_y),
                    (center_x, self.position[1] + BLOCK_SIZE - 2),
                    (self.position[0] + 2, center_y)
                ]
                pygame.draw.polygon(surface, BLACK, points)
            elif self.type == 4:
                pygame.draw.line(surface, BLACK, 
                               (self.position[0] + 4, center_y), 
                               (self.position[0] + BLOCK_SIZE - 4, center_y), 3)
                pygame.draw.line(surface, BLACK, 
                               (center_x, self.position[1] + 4), 
                               (center_x, self.position[1] + BLOCK_SIZE - 4), 3)
            else:
                pygame.draw.circle(surface, BLACK, (center_x, center_y), BLOCK_SIZE//4)

class Game:
    def __init__(self):
        self.snake = Snake()
        self.foods = []
        self.game_over = False
        self.paused = False
        self.current_speed = BASE_FPS
        self.leaderboard = LeaderBoard()
        self.score_submitted = False
        self.title_screen = True
        self.show_leaderboard = False
        self.show_options = False
        self.fullscreen = True  # Start in fullscreen
        
        # Pause menu buttons
        button_width = 200
        button_height = 50
        center_x = SCREEN_WIDTH // 2 - button_width // 2
        button_spacing = 70
        start_y = SCREEN_HEIGHT // 2 - 120
        
        self.resume_button = Button(center_x, start_y, button_width, button_height, 
                                   "Resume", GRAY, LIGHT_GRAY)
        self.leaderboard_button = Button(center_x, start_y + button_spacing, button_width, button_height, 
                                        "Leaderboard", BLUE, CYAN)
        self.options_button = Button(center_x, start_y + button_spacing * 2, button_width, button_height,
                                   "Options", PURPLE, (200, 100, 200))
        self.restart_button = Button(center_x, start_y + button_spacing * 3, button_width, button_height, 
                                    "Restart", ORANGE, YELLOW)
        self.quit_button = Button(center_x, start_y + button_spacing * 4, button_width, button_height, 
                                 "Main Menu", RED, (255, 100, 100))
        
        # Leaderboard back button
        self.back_button = Button(center_x, SCREEN_HEIGHT - 100, button_width, button_height,
                                 "Back", GRAY, LIGHT_GRAY)
        
        # Options menu buttons
        self.mute_sounds_button = ToggleButton(center_x, start_y + button_spacing, button_width, button_height,
                                             "Sound FX", GRAY, LIGHT_GRAY, is_on=not sfx_muted)
        self.mute_bgm_button = ToggleButton(center_x, start_y + button_spacing * 2, button_width, button_height,
                                          "BGM", GRAY, LIGHT_GRAY, is_on=not bgm_muted)
        self.fullscreen_button = ToggleButton(center_x, start_y + button_spacing * 3, button_width, button_height,
                                            "Fullscreen", GRAY, LIGHT_GRAY, is_on=self.fullscreen)
        self.options_back_button = Button(center_x, start_y + button_spacing * 4, button_width, button_height,
                                        "Back", GRAY, LIGHT_GRAY)
        
        # Title screen buttons
        self.start_button = Button(center_x, SCREEN_HEIGHT // 2 + 50, button_width, button_height,
                                 "Start Game", GREEN, (100, 255, 100))
        self.title_leaderboard_button = Button(center_x, SCREEN_HEIGHT // 2 + 50 + button_spacing, 
                                            button_width, button_height, "Leaderboard", BLUE, CYAN)
        self.title_options_button = Button(center_x, SCREEN_HEIGHT // 2 + 50 + button_spacing * 2,
                                        button_width, button_height, "Options", PURPLE, (200, 100, 200))
        self.title_quit_button = Button(center_x, SCREEN_HEIGHT // 2 + 50 + button_spacing * 3,
                                      button_width, button_height, "Quit", RED, (255, 100, 100))
        
        self.spawn_food()
        self.spawn_food()

        # When starting the game:
        global game_bg_playing
        if not game_bg_playing:
            game_bg.play(-1)
            game_bg_playing = True
            # Apply mute state
            if bgm_muted:
                game_bg.set_volume(0.0)
            else:
                game_bg.set_volume(0.3)
    
    def toggle_fullscreen(self):
        global screen, SCREEN_WIDTH, SCREEN_HEIGHT, fullscreen
        fullscreen = not fullscreen
        
        if fullscreen:
            info = pygame.display.Info()
            screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
        else:
            screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
        
        SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
        self.reposition_ui()
    
    def reposition_ui(self):
        button_width = 200
        button_height = 50
        center_x = SCREEN_WIDTH // 2 - button_width // 2
        button_spacing = 70
        start_y = SCREEN_HEIGHT // 2 - 120
        
        # Reposition pause menu buttons
        self.resume_button.rect = pygame.Rect(center_x, start_y, button_width, button_height)
        self.leaderboard_button.rect = pygame.Rect(center_x, start_y + button_spacing, button_width, button_height)
        self.options_button.rect = pygame.Rect(center_x, start_y + button_spacing * 2, button_width, button_height)
        self.restart_button.rect = pygame.Rect(center_x, start_y + button_spacing * 3, button_width, button_height)
        self.quit_button.rect = pygame.Rect(center_x, start_y + button_spacing * 4, button_width, button_height)
        
        # Reposition leaderboard back button
        self.back_button.rect = pygame.Rect(center_x, SCREEN_HEIGHT - 100, button_width, button_height)
        
        # Reposition title screen buttons
        self.start_button.rect = pygame.Rect(center_x, SCREEN_HEIGHT // 2 + 50, button_width, button_height)
        self.title_leaderboard_button.rect = pygame.Rect(center_x, SCREEN_HEIGHT // 2 + 50 + button_spacing, 
                                                    button_width, button_height)
        self.title_options_button.rect = pygame.Rect(center_x, SCREEN_HEIGHT // 2 + 50 + button_spacing * 2,
                                                button_width, button_height)
        self.title_quit_button.rect = pygame.Rect(center_x, SCREEN_HEIGHT // 2 + 50 + button_spacing * 3,
                                                button_width, button_height)
    
    def get_food_spawn_chances(self):
        score = self.snake.score
        
        if score < 10:
            return [85, 15, 0, 0]
        elif score < 25:
            return [70, 25, 5, 0]
        elif score < 50:
            return [60, 25, 12, 3]
        else:
            return [50, 30, 15, 5]
    
    def spawn_food(self):
        chances = self.get_food_spawn_chances()
        rand = random.randint(1, 100)
        
        if rand <= chances[0]:
            food_type = 1
        elif rand <= chances[0] + chances[1]:
            food_type = 2
        elif rand <= chances[0] + chances[1] + chances[2]:
            food_type = 3
        else:
            food_type = 4
        
        new_food = Food(food_type)
        
        while new_food.position in [pos for pos in self.snake.positions]:
            new_food.randomize_position()
        
        self.foods.append(new_food)
    
    def update_speed(self):
        speed_increase = self.snake.score // SPEED_INTERVAL
        self.current_speed = min(BASE_FPS + speed_increase, MAX_FPS)
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            elif event.type == pygame.VIDEORESIZE:
                if not fullscreen:
                    global SCREEN_WIDTH, SCREEN_HEIGHT, screen
                    SCREEN_WIDTH, SCREEN_HEIGHT = event.size
                    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
                    self.reposition_ui()
            
            elif event.type == pygame.KEYDOWN:
                if self.title_screen:
                    if (event.key == pygame.K_RETURN or event.key == pygame.K_SPACE) and not (self.show_leaderboard or self.show_options):
                        self.title_screen = False
                    elif event.key == pygame.K_ESCAPE:
                        if self.show_leaderboard or self.show_options:
                            self.show_leaderboard = False
                            self.show_options = False
                elif self.show_leaderboard or self.show_options:
                    if event.key == pygame.K_ESCAPE:
                        self.show_leaderboard = False
                        self.show_options = False
                elif self.paused:
                    if event.key == pygame.K_ESCAPE:
                        self.paused = False
                elif not self.game_over and not self.paused:
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        self.snake.change_direction((0, -1))
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self.snake.change_direction((0, 1))
                    elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.snake.change_direction((-1, 0))
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.snake.change_direction((1, 0))
                    elif event.key == pygame.K_ESCAPE:
                        self.paused = True
                    elif event.key == pygame.K_p:
                        self.paused = not self.paused
                    elif event.key == pygame.K_r:
                        self.restart_game()
                elif self.game_over:
                    if event.key == pygame.K_r:
                        self.restart_game()
                    elif event.key == pygame.K_ESCAPE:
                        self.__init__()
                        self.title_screen = True
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                if self.title_screen:
                    if not (self.show_leaderboard or self.show_options):
                        if self.start_button.is_clicked(mouse_pos, event):
                            self.title_screen = False
                        elif self.title_leaderboard_button.is_clicked(mouse_pos, event):
                            self.show_leaderboard = True
                            self.show_options = False
                        elif self.title_options_button.is_clicked(mouse_pos, event):
                            self.show_options = True
                            self.show_leaderboard = False
                        elif self.title_quit_button.is_clicked(mouse_pos, event):
                            return False
                    elif self.show_leaderboard and self.back_button.is_clicked(mouse_pos, event):
                        self.show_leaderboard = False
                    elif self.show_options and self.options_back_button.is_clicked(mouse_pos, event):
                        self.show_options = False
                
                elif self.show_options:
                    if self.mute_sounds_button.is_clicked(mouse_pos, event):
                        global sfx_muted
                        sfx_muted = not self.mute_sounds_button.toggle()
                        if sfx_muted:
                            food_capture_sound.set_volume(0)
                            game_over_sound.set_volume(0)
                        else:
                            food_capture_sound.set_volume(0.5)
                            game_over_sound.set_volume(0.7)
                    elif self.mute_bgm_button.is_clicked(mouse_pos, event):
                        global bgm_muted, game_bg_playing
                        bgm_muted = not self.mute_bgm_button.toggle()
                        if bgm_muted:
                            game_bg.set_volume(0)
                        else:
                            game_bg.set_volume(0.3)
                            if not game_bg_playing:
                                game_bg.play(-1)
                                game_bg_playing = True
                    elif self.fullscreen_button.is_clicked(mouse_pos, event):
                        self.toggle_fullscreen()
                        self.fullscreen_button.toggle()
                
                elif self.paused and not (self.show_leaderboard or self.show_options):
                    if self.resume_button.is_clicked(mouse_pos, event):
                        self.paused = False
                    elif self.leaderboard_button.is_clicked(mouse_pos, event):
                        self.show_leaderboard = True
                        self.show_options = False
                    elif self.options_button.is_clicked(mouse_pos, event):
                        self.show_options = True
                        self.show_leaderboard = False
                    elif self.restart_button.is_clicked(mouse_pos, event):
                        self.restart_game()
                        self.paused = False
                    elif self.quit_button.is_clicked(mouse_pos, event):
                        self.__init__()
                        self.title_screen = True
                        self.paused = False
                
                elif self.show_leaderboard and self.back_button.is_clicked(mouse_pos, event):
                    self.show_leaderboard = False
                
                elif self.game_over:
                    restart_text_rect = pygame.Rect(
                        SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2 + 60, 300, 30
                    )
                    if restart_text_rect.collidepoint(mouse_pos):
                        self.restart_game()
        
        return True
    
    def update(self):
        if self.title_screen or self.game_over or self.paused or self.show_leaderboard or self.show_options:
            if self.game_over and not self.score_submitted:
                if self.leaderboard.is_high_score(self.snake.score):
                    self.leaderboard.add_score(self.snake.score, self.snake.length)
                self.score_submitted = True
            return
        
        game_over = self.snake.update()
        global game_bg_playing 
        if game_over:
            self.game_over = True
            game_bg.stop()
            game_bg_playing = False
            if not sfx_muted:
                game_over_sound.play()
            return
        
        for food in self.foods[:]:
            if not food.update():
                self.foods.remove(food)
        
        head = self.snake.get_head_position()
        head_rect = pygame.Rect(head[0], head[1], BLOCK_SIZE, BLOCK_SIZE)
        
        for food in self.foods[:]:
            food_rect = pygame.Rect(food.position[0], food.position[1], BLOCK_SIZE, BLOCK_SIZE)
            if head_rect.colliderect(food_rect) and food.active:
                self.foods.remove(food)

                if not sfx_muted:
                    food_capture_sound.play()
                
                self.snake.score += food.points
                
                if food.type == 1:
                    self.snake.length += 1
                elif food.type == 2:
                    self.snake.length += 1
                elif food.type == 3:
                    self.snake.length += 2
                elif food.type == 4:
                    self.snake.length += 3
                
                self.spawn_food()
                self.update_speed()
        
        min_foods = min(2 + (self.snake.score // 15), 4)
        while len(self.foods) < min_foods:
            self.spawn_food()
    
    def restart_game(self):
        self.snake.reset()
        self.foods = []
        self.game_over = False
        self.paused = False
        self.score_submitted = False
        self.current_speed = BASE_FPS
        
        self.spawn_food()
        self.spawn_food()

        # When restarting the game:
        global game_bg_playing 
        if not game_bg_playing:
            game_bg.play(-1)
            game_bg_playing = True
            # Restore mute state
            if bgm_muted:
                game_bg.set_volume(0.0)
            else:
                game_bg.set_volume(0.3)
    
    def draw_title_screen(self):
        screen.fill(BLACK)
        
        title_font = pygame.font.Font(None, 72)
        title_text = title_font.render("SNAKE GAME", True, GREEN)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//3))
        screen.blit(title_text, title_rect)
        
        # Draw a sample snake
        snake_length = 10
        for i in range(snake_length):
            x = SCREEN_WIDTH // 3 + i * BLOCK_SIZE
            y = SCREEN_HEIGHT // 2
            color = (0, 255 - (i * 20), 0)
            if i == 0:
                color = CYAN
            pygame.draw.rect(screen, color, (x, y, BLOCK_SIZE, BLOCK_SIZE))
            pygame.draw.rect(screen, BLACK, (x, y, BLOCK_SIZE, BLOCK_SIZE), 1)
        
        # Draw sample food
        pygame.draw.rect(screen, RED, (SCREEN_WIDTH // 3 + snake_length * BLOCK_SIZE + 20, 
                                     SCREEN_HEIGHT // 2, BLOCK_SIZE, BLOCK_SIZE))
        
        mouse_pos = pygame.mouse.get_pos()
        self.start_button.check_hover(mouse_pos)
        self.title_leaderboard_button.check_hover(mouse_pos)
        self.title_options_button.check_hover(mouse_pos)
        self.title_quit_button.check_hover(mouse_pos)
        
        if not (self.show_leaderboard or self.show_options):
            self.start_button.draw(screen)
            self.title_leaderboard_button.draw(screen)
            self.title_options_button.draw(screen)
            self.title_quit_button.draw(screen)
        
        # Show high score on title screen
        high_score = self.leaderboard.get_high_score()
        if high_score > 0:
            hs_font = pygame.font.Font(None, 36)
            hs_text = hs_font.render(f"High Score: {high_score}", True, YELLOW)
            hs_rect = hs_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//3 + 50))
            screen.blit(hs_text, hs_rect)
        
        controls_font = pygame.font.Font(None, 24)
        controls = [
            "Controls:",
            "WASD / Arrow Keys to Move",
            "P to Pause",
            "ESC for Menu",
            "R to Restart"
        ]
        for i, control in enumerate(controls):
            text = controls_font.render(control, True, WHITE)
            screen.blit(text, (50, SCREEN_HEIGHT - 150 + i * 25))
    
    def draw_pause_menu(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))
        
        big_font = pygame.font.Font(None, 72)
        title = big_font.render("GAME PAUSED", True, WHITE)
        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 200)))
        
        mouse_pos = pygame.mouse.get_pos()
        self.resume_button.check_hover(mouse_pos)
        self.leaderboard_button.check_hover(mouse_pos)
        self.options_button.check_hover(mouse_pos)
        self.restart_button.check_hover(mouse_pos)
        self.quit_button.check_hover(mouse_pos)
        
        self.resume_button.draw(screen)
        self.leaderboard_button.draw(screen)
        self.options_button.draw(screen)
        self.restart_button.draw(screen)
        self.quit_button.draw(screen)
    
    def draw_options_menu(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))
        
        big_font = pygame.font.Font(None, 72)
        title = big_font.render("OPTIONS", True, WHITE)
        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 200)))
        
        mouse_pos = pygame.mouse.get_pos()
        self.mute_sounds_button.check_hover(mouse_pos)
        self.mute_bgm_button.check_hover(mouse_pos)
        self.fullscreen_button.check_hover(mouse_pos)
        self.options_back_button.check_hover(mouse_pos)
        
        self.mute_sounds_button.draw(screen)
        self.mute_bgm_button.draw(screen)
        self.fullscreen_button.draw(screen)
        self.options_back_button.draw(screen)
    
    def draw_leaderboard(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        screen.blit(overlay, (0, 0))
        
        big_font = pygame.font.Font(None, 72)
        title = big_font.render("LEADERBOARD", True, CYAN)
        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH//2, 100)))
        
        header_font = pygame.font.Font(None, 48)
        rank_header = header_font.render("RANK", True, YELLOW)
        score_header = header_font.render("SCORE", True, YELLOW)
        length_header = header_font.render("LENGTH", True, YELLOW)
        date_header = header_font.render("DATE", True, YELLOW)
        
        header_y = 180
        screen.blit(rank_header, (200, header_y))
        screen.blit(score_header, (350, header_y))
        screen.blit(length_header, (550, header_y))
        screen.blit(date_header, (700, header_y))
        
        pygame.draw.line(screen, WHITE, (150, header_y + 50), (SCREEN_WIDTH - 150, header_y + 50), 2)
        
        score_font = pygame.font.Font(None, 36)
        scores = self.leaderboard.get_top_scores()
        
        if not scores:
            no_scores_text = score_font.render("No scores yet! Be the first to play!", True, WHITE)
            screen.blit(no_scores_text, no_scores_text.get_rect(center=(SCREEN_WIDTH//2, 300)))
        else:
            for i, entry in enumerate(scores):
                y_pos = 250 + i * 40
                
                color = GREEN if (self.game_over and entry['score'] == self.snake.score and 
                                entry['length'] == self.snake.length) else WHITE
                
                rank_text = score_font.render(f"{i + 1}.", True, color)
                score_text = score_font.render(f"{entry['score']:,}", True, color)
                length_text = score_font.render(f"{entry['length']}", True, color)
                date_text = score_font.render(entry['date'][:10], True, color)
                
                screen.blit(rank_text, (200, y_pos))
                screen.blit(score_text, (350, y_pos))
                screen.blit(length_text, (550, y_pos))
                screen.blit(date_text, (700, y_pos))
        
        mouse_pos = pygame.mouse.get_pos()
        self.back_button.check_hover(mouse_pos)
        self.back_button.draw(screen)
    
    def draw(self, screen):
        screen.fill(BLACK)
        
        if not (self.title_screen or self.show_leaderboard or self.show_options or self.paused or self.game_over):
            # Draw grid
            for x in range(0, SCREEN_WIDTH, BLOCK_SIZE):
                pygame.draw.line(screen, (20, 20, 20), (x, 0), (x, SCREEN_HEIGHT))
            for y in range(0, SCREEN_HEIGHT, BLOCK_SIZE):
                pygame.draw.line(screen, (20, 20, 20), (0, y), (SCREEN_WIDTH, y))
            
            # Draw game elements
            for food in self.foods:
                food.draw(screen)
            self.snake.draw(screen)
            
            # Draw HUD
            font = pygame.font.Font(None, 36)
            score_text = font.render(f'Score: {self.snake.score}', True, WHITE)
            length_text = font.render(f'Length: {self.snake.length}', True, WHITE)
            speed_text = font.render(f'Speed: {self.current_speed}', True, WHITE)
            high_score = self.leaderboard.get_high_score()
            high_score_text = font.render(f'High Score: {high_score}', True, YELLOW)
            
            screen.blit(score_text, (10, 10))
            screen.blit(length_text, (10, 50))
            screen.blit(speed_text, (10, 90))
            screen.blit(high_score_text, (10, 130))
            
            legend_font = pygame.font.Font(None, 20)
            legends = [
                ("Red: +1 point", RED),
                ("Yellow: +2 points", YELLOW),
                ("Blue: +3 points", BLUE),
                ("Purple: +5 points", PURPLE)
            ]
            for i, (text, color) in enumerate(legends):
                legend_text = legend_font.render(text, True, color)
                screen.blit(legend_text, (10, 180 + i * 22))
            
            controls_font = pygame.font.Font(None, 24)
            controls = [
                "WASD: Move",
                "P: Pause",
                "ESC: Menu",
                "R: Restart"
            ]
            for i, control in enumerate(controls):
                text = controls_font.render(control, True, WHITE)
                screen.blit(text, (SCREEN_WIDTH - 180, 10 + i * 25))
        
        if self.title_screen:
            self.draw_title_screen()
        
        if self.show_leaderboard:
            self.draw_leaderboard()
        
        if self.show_options:
            self.draw_options_menu()
        
        if self.paused and not (self.show_leaderboard or self.show_options):
            self.draw_pause_menu()
        
        if self.game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            screen.blit(overlay, (0, 0))
            
            big_font = pygame.font.Font(None, 72)
            small_font = pygame.font.Font(None, 36)
            
            game_over_text = big_font.render('GAME OVER', True, RED)
            score_text = small_font.render(f'Final Score: {self.snake.score}', True, WHITE)
            length_text = small_font.render(f'Final Length: {self.snake.length}', True, WHITE)
            
            if self.leaderboard.is_high_score(self.snake.score) and self.snake.score > 0:
                new_record_text = small_font.render('NEW HIGH SCORE!', True, YELLOW)
                screen.blit(new_record_text, new_record_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 80)))
            
            restart_text = small_font.render('Press R to Restart or Click Here', True, WHITE)
            restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 70))
            screen.blit(restart_text, restart_rect)
            
            quit_text = small_font.render('Press ESC for Main Menu', True, WHITE)
            quit_rect = quit_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 110))
            screen.blit(quit_text, quit_rect)
            
            screen.blit(game_over_text, game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 40)))
            screen.blit(score_text, score_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2)))
            screen.blit(length_text, length_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 30)))

def main():
    game = Game()
    running = True
    
    while running:
        running = game.handle_events()
        game.update()
        game.draw(screen)
        pygame.display.flip()
        clock.tick(game.current_speed)
        
    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()