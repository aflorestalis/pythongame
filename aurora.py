import os
os.environ["SDL_VIDEO_CENTERED"] = "1"

# Configurando o jogo
from typing import TYPE_CHECKING
from enum import Enum
from pgzero.builtins import mouse
import pgzrun

if TYPE_CHECKING:
    from pgzero.actor import Actor
    from pgzero.builtins import screen, music, sounds, keyboard, exit

# Nomeando
class GameState(Enum):
    MENU = "menu"
    PLAYING = "playing"
    GAME_OVER = "gameover"

class AudioStatus(Enum):
    ENABLED = "on"
    DISABLED = "off"

class MotionState(Enum):
    STILL = "idle"
    MOVING = "running"

class Way(Enum):
    LEFT = "left"
    RIGHT = "right"

# Plataforma
class Platform:
    def __init__(self, pos, scale=5.0):
        self.actor = Actor("asset/platform", pos)
        self.actor.scale = scale

    def draw(self):
        self.actor.draw()

# Posicionando plataformas
class Game:
    WIDTH = 900
    HEIGHT = 700
    spawn_points = [
        (500, 500), (100, 200), (700, 150), (300, 100), (250, 400),
        (650, 480), (350, 320), (120, 520), (580, 220), (430, 180)
    ]

    def __init__(self):
        self.manager = SceneManager()
        self.hero = PlayerCharacter()
        self.foes: list[Enemy] = []
        self.blocks: list[Platform] = []
        self._load_objects()

    def _load_objects(self):
        for pos in self.spawn_points:
            self.blocks.append(Platform(pos))
            self.foes.append(Enemy((pos[0], pos[1] - 16)))

# HUD (Interface Menu)
class SceneManager:
    btn_start = Actor("hud/button.png", (400, 200))
    btn_audio = Actor("hud/button.png", (400, 270))
    btn_quit = Actor("hud/button.png", (400, 340))
    music.play("soundtrack.wav")

    def __init__(self):
        self.current_state = GameState.MENU
        self.audio_state = AudioStatus.ENABLED

    def update_scene(self):
        screen.clear()

        if self.audio_state == AudioStatus.DISABLED:
            music.pause()
        else:
            music.unpause()

        if self.current_state == GameState.MENU:
            self.show_menu()
        elif self.current_state == GameState.PLAYING:
            self.show_game()
        elif self.current_state == GameState.GAME_OVER:
            self.show_game_over()

    # Buttons do Menu
    def mouse_click(self, pos, button):
        if button != mouse.LEFT:
            return

        if self.current_state == GameState.MENU:
            if self.btn_start.collidepoint(pos):
                self.current_state = GameState.PLAYING
            elif self.btn_audio.collidepoint(pos):
                self.audio_state = (
                    AudioStatus.DISABLED if self.audio_state == AudioStatus.ENABLED else AudioStatus.ENABLED
                )
            elif self.btn_quit.collidepoint(pos):
                exit()

        elif self.current_state == GameState.GAME_OVER:
            if self.btn_start.collidepoint(pos):
                self.current_state = GameState.MENU

    def show_menu(self):
        screen.blit("hud/background_menu", (0, 0))
        self.btn_start.draw()
        self._draw_button_text("Começar", self.btn_start)

        self.btn_audio.draw()
        text = "Música" if self.audio_state == AudioStatus.ENABLED else "Sem Música"
        self._draw_button_text(text, self.btn_audio)

        self.btn_quit.draw()
        self._draw_button_text("Fechar", self.btn_quit)
# Página do jogo
    def show_game(self):
        screen.blit("asset/background", (0, 0))
        game_instance.hero.update()
        game_instance.hero.draw()

        for block in game_instance.blocks:
            block.draw()

        for foe in game_instance.foes:
            foe.update()
            foe.draw()

    def show_game_over(self):
        screen.draw.text("Game Over", center=(400, 200), fontsize=60, color="white")

    def _draw_button_text(self, label: str, actor: Actor):
        screen.draw.text(label, center=actor.center, color="black", fontsize=30)

# Player (Comportamentos, ações)
class PlayerCharacter:
    run_r = [f"player/right-run/{i}" for i in range(3)]
    run_l = [f"player/left-run/{i}" for i in range(3)]
    idle_r = [f"player/right-idle/{i}" for i in range(3)]
    idle_l = [f"player/left-idle/{i}" for i in range(3)]

    sprite = Actor(idle_r[0], center=(40, 170))
    motion = MotionState.STILL
    sprite.vy = 0

    speed = 3
    gravity = 0.2
    dir_x = 1
    jump_power = -8
    grounded = False

    last_dir_x = dir_x
    frame_tick = 0
    frame_gap = 1
    frame_index = 0

    def draw(self):
        self.sprite.draw()

    def update(self):
        self._move()
        self._animate()
        self._apply_gravity()
        self._keep_inside_screen()
        self._check_enemies()

    def _move(self):
        self.dir_x = 0
        self.motion = MotionState.STILL
        self.last_dir_x = self.dir_x

        if keyboard.left:
            self.motion = MotionState.MOVING
            self.dir_x = -1
        if keyboard.right:
            self.motion = MotionState.MOVING
            self.dir_x = 1
        if (keyboard.up or keyboard.space) and self.grounded:
            self.sprite.vy = self.jump_power
            self.grounded = False

        self.sprite.x += self.dir_x * self.speed

    def _keep_inside_screen(self):
        self.sprite.x = max(0, min(self.sprite.x, Game.WIDTH))
        if self.sprite.y > Game.HEIGHT:
            self.sprite.y = Game.HEIGHT
            self.sprite.vy = 0

    def _apply_gravity(self):
        if not self.grounded:
            self.sprite.vy += self.gravity
        else:
            self.sprite.vy = 0

        self.sprite.y += self.sprite.vy
        self._check_platforms()

    def _check_platforms(self):
        self.grounded = False
        for block in game_instance.blocks:
            if self.sprite.colliderect(block.actor):
                if self.sprite.vy > 0 and self.sprite.bottom <= block.actor.top + self.sprite.vy:
                    self.sprite.bottom = block.actor.top
                    self.sprite.vy = 0
                    self.grounded = True
                elif self.sprite.vy < 0 and self.sprite.top >= block.actor.bottom - abs(self.sprite.vy):
                    self.sprite.top = block.actor.bottom
                    self.sprite.vy = 0

    def _animate(self):
        self.frame_tick += 0.2
        if self.frame_tick >= self.frame_gap:
            self.frame_tick = 0.2
            frames = []

            if self.motion == MotionState.MOVING:
                frames = self.run_r if self.dir_x == 1 else self.run_l
            elif self.motion == MotionState.STILL:
                frames = self.idle_r if self.last_dir_x == 1 else self.idle_l

            if frames:
                self.frame_index = (self.frame_index + 1) % len(frames)
                self.sprite.image = frames[self.frame_index]

    def _check_enemies(self):
        for idx, foe in enumerate(game_instance.foes):
            if self.sprite.colliderect(foe.actor):
                if self.sprite.bottom > foe.actor.top and self.sprite.bottom < foe.actor.centery:
                    if game_instance.manager.audio_state == AudioStatus.ENABLED:
                        sounds.enemy_death.play()
                    game_instance.spawn_points.pop(idx)
                    game_instance.foes.remove(foe)
                else:
                    if game_instance.manager.audio_state == AudioStatus.ENABLED:
                        sounds.player_death.play()
                    music.stop()
                    game_instance.manager.current_state = GameState.GAME_OVER

# Inimigo (Comportamento e etc.)
class Enemy:
    run_r = [f'enemy/run_right/{i}' for i in range(3)]
    run_l = [f'enemy/run_left/{i}' for i in range(3)]

    def __init__(self, start_pos):
        self.origin = start_pos
        self.actor = Actor(self.run_r[0], center=start_pos)
        self.dir = Way.LEFT
        self.frame_tick = 0.1
        self.frame_gap = 0.2
        self.frame_index = 0

    def draw(self):
        self.actor.draw()

    def update(self):
        self._move()
        self._animate()

    def _move(self):
        left_bound = self.origin[0] - 35
        right_bound = self.origin[0] + 45

        if self.actor.x <= left_bound:
            self.dir = Way.RIGHT
        elif self.actor.x >= right_bound:
            self.dir = Way.LEFT

        self.actor.x += -1 if self.dir == Way.LEFT else 1

    def _animate(self):
        self.frame_tick += 0.2
        if self.frame_tick >= self.frame_gap:
            self.frame_tick = 0.1
            frames = self.run_r if self.dir == Way.RIGHT else self.run_l

            if frames:
                self.frame_index = (self.frame_index + 1) % len(frames)
                self.actor.image = frames[self.frame_index]

# Repetição (Loop)
game_instance = Game()

def on_mouse_down(pos):
    game_instance.manager.mouse_click(pos, mouse.LEFT)

def draw():
    game_instance.manager.update_scene()

def update():
    pass

pgzrun.go()
