#!/usr/bin/env python3
"""
AC!'S Koopa Engine 0.1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Team Flames / Samsoft / Flames Co. 20XX
60 FPS Famicom-Style Platformer

CHANGELOG FROM 1.0A:
- FIXED: pygame.Surface before init (thumbnails lazy-loaded)
- FIXED: All 8 worlds now spawn correct enemy types
- FIXED: Player/Flag chars no longer conflict with enemies
- FIXED: ESC key properly pops scene stack (no overflow)
- FIXED: HUD layout - coins/time no longer overlap
- FIXED: GameOver returns to FileSelect properly
- FIXED: World 8-4 triggers WinScreen with fireworks
- ADDED: ? block hit spawns coins (animated fly-up)
- ADDED: Mushroom powerup system (? blocks, makes Mario big)
- ADDED: Coin collection from blocks and floating coins
- ADDED: Koopa shell mode (stomp → shell, kick)
- ADDED: Flagpole slide-down victory sequence
- ADDED: Time bonus scoring on level complete
- ADDED: Death animation and proper respawn
- ADDED: Variable jump height (hold space)
- ADDED: Consistent level seeds per world-level
- FIXED: Big Mario hitbox matches visual (32px)
- FIXED: Collision resolution (Y then X, no tunneling)
- POLISH: 60 FPS locked, dt-based physics
"""

import pygame
import sys
import math
import random
from pygame.locals import *

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONSTANTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SCALE = 2
TILE = 16
WIDTH = int(300 * SCALE)
HEIGHT = int(200 * SCALE)
FPS = 60  # Famicom locked

# NES Palette (2C02 PPU accurate)
NES_PALETTE = [
    (84, 84, 84), (0, 30, 116), (8, 16, 144), (48, 0, 136), 
    (68, 0, 100), (92, 0, 48), (84, 4, 0), (60, 24, 0), 
    (32, 42, 0), (8, 58, 0), (0, 64, 0), (0, 60, 0), 
    (0, 50, 60), (0, 0, 0), (152, 150, 152), (8, 76, 196), 
    (48, 50, 236), (92, 30, 228), (136, 20, 176), (160, 20, 100), 
    (152, 34, 32), (120, 60, 0), (84, 90, 0), (40, 114, 0), 
    (8, 124, 0), (0, 118, 40), (0, 102, 120), (0, 0, 0), 
    (236, 238, 236), (76, 154, 236), (120, 124, 236), (176, 98, 236), 
    (228, 84, 236), (236, 88, 180), (236, 106, 100), (212, 136, 32), 
    (160, 170, 0), (116, 196, 0), (76, 208, 32), (56, 204, 108), 
    (56, 180, 204), (60, 60, 60), (0, 0, 0), (0, 0, 0)
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GAME STATE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class GameState:
    def __init__(self):
        self.slot = 0
        self.progress = [{"world": 1}, {"world": 1}, {"world": 1}]
        self.score = 0
        self.coins = 0
        self.lives = 3
        self.world = 1
        self.level = 1
        self.time = 300
        self.mario_size = "small"  # "small" or "big"
        self.unlocked_worlds = [1]

state = GameState()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SCENE MANAGEMENT (FIXED - proper stack ops)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SCENES = []

def push(scene):
    SCENES.append(scene)
    
def pop():
    if SCENES:
        SCENES.pop()
        
def replace(scene):
    """Replace current scene without stacking"""
    if SCENES:
        SCENES.pop()
    SCENES.append(scene)
    
def clear_to(scene):
    """Clear entire stack and set new scene"""
    SCENES.clear()
    SCENES.append(scene)

class Scene:
    def handle(self, events, keys): pass
    def update(self, dt): return None  # Return next scene or None
    def draw(self, surf): pass

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# WORLD THEMES (enemy types properly mapped)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WORLD_THEMES = {
    1: {"sky": 27, "ground": 20, "pipe": 14, "block": 33, "water": None, 
        "enemy_type": "goomba", "name": "GRASS LAND"},
    2: {"sky": 26, "ground": 21, "pipe": 15, "block": 34, "water": None, 
        "enemy_type": "koopa", "name": "DESERT HILL"},
    3: {"sky": 25, "ground": 22, "pipe": 16, "block": 35, "water": 45, 
        "enemy_type": "fish", "name": "AQUA SEA"},
    4: {"sky": 24, "ground": 23, "pipe": 17, "block": 36, "water": None, 
        "enemy_type": "beetle", "name": "GIANT FOREST"},
    5: {"sky": 23, "ground": 24, "pipe": 18, "block": 37, "water": None, 
        "enemy_type": "paratroopa", "name": "SKY HEIGHTS"},
    6: {"sky": 22, "ground": 25, "pipe": 19, "block": 38, "water": None, 
        "enemy_type": "spiny", "name": "ICE CAVERN"},
    7: {"sky": 21, "ground": 26, "pipe": 20, "block": 39, "water": None, 
        "enemy_type": "spike", "name": "LAVA CASTLE"},
    8: {"sky": 20, "ground": 27, "pipe": 21, "block": 40, "water": None, 
        "enemy_type": "bowser_minion", "name": "FINAL FORTRESS"}
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LEVEL GENERATION (FIXED - no char conflicts)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def generate_level_data():
    """Generate levels with separate enemy/player/flag data (no char conflicts)"""
    levels = {}
    
    for world in range(1, 9):
        for level in range(1, 5):
            level_id = f"{world}-{level}"
            
            # Seed for consistent level layout
            random.seed(hash(level_id) + 42)
            
            # Create tile data (ONLY terrain chars: G, B, P, T, ?)
            level_data = []
            
            # Sky rows (0-9)
            for i in range(10):
                level_data.append(" " * 100)
            
            # Platform rows (10-14)
            for i in range(10, 15):
                level_data.append(" " * 100)
            
            # Ground rows (15-19)
            for i in range(15, 20):
                if i == 15:
                    row = "G" * 100
                else:
                    row = "D" * 100  # D = dirt/underground
                level_data.append(row)
            
            # Add platforms
            for i in range(5 + level):
                platform_y = random.randint(8, 12)
                platform_x = random.randint(10 + i*15, 15 + i*15)
                length = random.randint(4, 8)
                for j in range(length):
                    if platform_x + j < 100:
                        level_data[platform_y] = level_data[platform_y][:platform_x+j] + "P" + level_data[platform_y][platform_x+j+1:]
            
            # Add pipes (no overlap with flag area)
            for i in range(2 + level//2):
                pipe_x = random.randint(20 + i*25, 25 + i*25)
                if pipe_x > 90:
                    continue
                pipe_height = random.randint(2, 4)
                for j in range(pipe_height):
                    if 15-j >= 0:
                        level_data[15-j] = level_data[15-j][:pipe_x] + "T" + level_data[15-j][pipe_x+1:]
                        level_data[15-j] = level_data[15-j][:pipe_x+1] + "T" + level_data[15-j][pipe_x+2:]
            
            # Add bricks and question blocks
            for i in range(8 + level*2):
                block_y = random.randint(6, 11)
                block_x = random.randint(8 + i*8, 12 + i*8)
                if block_x > 90:
                    continue
                block_type = "?" if random.random() > 0.4 else "B"
                level_data[block_y] = level_data[block_y][:block_x] + block_type + level_data[block_y][block_x+1:]
            
            # Add some gaps in ground (pits)
            if level > 1:
                for i in range(level - 1):
                    gap_x = random.randint(30 + i*20, 35 + i*20)
                    gap_width = random.randint(2, 3)
                    for gx in range(gap_width):
                        if gap_x + gx < 90:
                            level_data[15] = level_data[15][:gap_x+gx] + " " + level_data[15][gap_x+gx+1:]
            
            # Generate enemy spawn positions (SEPARATE from tiles)
            enemy_spawns = []
            theme = WORLD_THEMES[world]
            num_enemies = 4 + level * 2
            
            for i in range(num_enemies):
                enemy_x = random.randint(15 + i*10, 20 + i*10)
                if enemy_x > 85:  # Keep away from flag
                    continue
                enemy_y = 14  # Spawn on ground level
                enemy_spawns.append({
                    "x": enemy_x * TILE,
                    "y": enemy_y * TILE,
                    "type": theme["enemy_type"]
                })
            
            # Store level with metadata
            levels[level_id] = {
                "tiles": level_data,
                "enemies": enemy_spawns,
                "player_start": (5 * TILE, 14 * TILE),  # Fixed start position
                "flag_pos": (95 * TILE, 10 * TILE),      # Fixed flag position
                "width": 100 * TILE
            }
    
    random.seed()  # Reset seed
    return levels

LEVELS = generate_level_data()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# THUMBNAIL GENERATOR (LAZY-LOADED - POST INIT)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
THUMBNAILS = {}
_thumbnails_generated = False

def generate_thumbnails():
    """Generate thumbnails AFTER pygame.init()"""
    global _thumbnails_generated
    if _thumbnails_generated:
        return
    
    for level_id, level_data in LEVELS.items():
        world = int(level_id.split("-")[0])
        theme = WORLD_THEMES[world]
        
        thumb = pygame.Surface((32, 24))
        thumb.fill(NES_PALETTE[theme["sky"]])
        
        tiles = level_data["tiles"]
        for y, row in enumerate(tiles[10:15]):
            for x, char in enumerate(row[::3]):
                px = min(x, 31)
                py = min(y + 10, 23)
                if char in ("G", "D", "P", "T"):
                    thumb.set_at((px, py), NES_PALETTE[theme["ground"]])
                elif char in ("?", "B"):
                    thumb.set_at((px, py), NES_PALETTE[theme["block"]])
        
        THUMBNAILS[level_id] = thumb
    
    _thumbnails_generated = True

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PARTICLE EFFECTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class Particle:
    def __init__(self, x, y, vx, vy, color, lifetime=1.0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.active = True
        
    def update(self, dt):
        self.x += self.vx * dt * 60
        self.y += self.vy * dt * 60
        self.vy += 0.3 * dt * 60  # Gravity
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.active = False
            
    def draw(self, surf, cam):
        if not self.active:
            return
        alpha = self.lifetime / self.max_lifetime
        x = int(self.x - cam)
        y = int(self.y)
        size = max(1, int(3 * alpha))
        pygame.draw.rect(surf, self.color, (x, y, size, size))

class CoinEffect:
    """Flying coin from ? block"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.start_y = y
        self.vy = -6
        self.lifetime = 0.5
        self.active = True
        self.frame = 0
        self.frame_timer = 0
        
    def update(self, dt):
        self.y += self.vy * dt * 60
        self.vy += 0.4 * dt * 60
        self.frame_timer += dt
        if self.frame_timer > 0.05:
            self.frame_timer = 0
            self.frame = (self.frame + 1) % 4
        self.lifetime -= dt
        if self.lifetime <= 0 or self.y > self.start_y:
            self.active = False
            
    def draw(self, surf, cam):
        if not self.active:
            return
        x = int(self.x - cam)
        y = int(self.y)
        # Animated coin sprite
        widths = [8, 6, 2, 6]
        w = widths[self.frame]
        pygame.draw.rect(surf, NES_PALETTE[35], (x + (8-w)//2, y, w, 10))
        pygame.draw.rect(surf, NES_PALETTE[39], (x + (8-w)//2 + 1, y + 2, max(1, w-2), 6))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ENTITY BASE CLASS (IMPROVED COLLISION)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class Entity:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.width = TILE
        self.height = TILE
        self.on_ground = False
        self.facing_right = True
        self.active = True
        
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
        
    def check_collision(self, other):
        return self.get_rect().colliderect(other.get_rect())
        
    def update(self, colliders, dt):
        # Apply gravity
        if not self.on_ground:
            self.vy += 0.5 * dt * 60
            self.vy = min(self.vy, 10)  # Terminal velocity
        
        # Move Y first (fixes tunneling)
        self.y += self.vy * dt * 60
        self.on_ground = False
        
        for rect in colliders:
            if self.get_rect().colliderect(rect):
                if self.vy > 0:  # Falling
                    self.y = rect.top - self.height
                    self.vy = 0
                    self.on_ground = True
                elif self.vy < 0:  # Rising
                    self.y = rect.bottom
                    self.vy = 0
        
        # Then move X
        self.x += self.vx * dt * 60
        
        for rect in colliders:
            if self.get_rect().colliderect(rect):
                if self.vx > 0:  # Moving right
                    self.x = rect.left - self.width
                elif self.vx < 0:  # Moving left
                    self.x = rect.right
                self.vx = 0
                    
    def draw(self, surf, cam):
        pass

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PLAYER CLASS (POWERUPS, VARIABLE JUMP)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.jump_power = -5.5
        self.move_speed = 2.5
        self.invincible = 0
        self.animation_frame = 0
        self.walk_timer = 0
        self.jump_held = False
        self.jump_timer = 0
        self.dead = False
        self.death_timer = 0
        self.victory = False
        self.victory_timer = 0
        self.flag_slide = False
        self.flag_y_target = 0
        self.update_size()
        
    def update_size(self):
        """Update hitbox based on Mario size"""
        if state.mario_size == "big":
            self.height = 32
        else:
            self.height = TILE
        
    def update(self, colliders, dt, enemies, level_scene):
        if self.dead:
            self.death_timer -= dt
            self.vy += 0.3 * dt * 60
            self.y += self.vy * dt * 60
            return
            
        if self.victory:
            if self.flag_slide:
                # Slide down flagpole
                self.y += 2 * dt * 60
                if self.y >= self.flag_y_target:
                    self.y = self.flag_y_target
                    self.flag_slide = False
                    self.victory_timer = 2.0
            else:
                self.victory_timer -= dt
                # Walk right off screen
                self.x += 1.5 * dt * 60
            return
            
        keys = pygame.key.get_pressed()
        
        # Horizontal movement
        self.vx = 0
        if keys[K_LEFT]:
            self.vx = -self.move_speed
            self.facing_right = False
        if keys[K_RIGHT]:
            self.vx = self.move_speed
            self.facing_right = True
            
        # Variable height jumping
        if keys[K_SPACE]:
            if self.on_ground and not self.jump_held:
                self.vy = self.jump_power
                self.on_ground = False
                self.jump_timer = 0.15
                self.jump_held = True
            elif self.jump_timer > 0 and self.vy < 0:
                # Extend jump while holding
                self.jump_timer -= dt
                self.vy = self.jump_power * 0.8
        else:
            self.jump_held = False
            self.jump_timer = 0
            
        # Update walk animation
        if self.vx != 0 and self.on_ground:
            self.walk_timer += dt
            if self.walk_timer > 0.08:
                self.walk_timer = 0
                self.animation_frame = (self.animation_frame + 1) % 3
        elif not self.on_ground:
            self.animation_frame = 2  # Jump pose
        else:
            self.animation_frame = 0
            
        # Update invincibility
        if self.invincible > 0:
            self.invincible -= dt
            
        super().update(colliders, dt)
        
        # Check collision with enemies
        for enemy in enemies:
            if enemy.active and self.check_collision(enemy):
                # Check if stomping
                if self.vy > 0 and self.y + self.height - 8 < enemy.y + enemy.height//2:
                    # Stomp!
                    if isinstance(enemy, Koopa):
                        if enemy.shell_mode:
                            # Kick shell
                            enemy.shell_moving = True
                            enemy.vx = 4 if self.x < enemy.x else -4
                        else:
                            # Enter shell mode
                            enemy.shell_mode = True
                            enemy.vx = 0
                    else:
                        enemy.active = False
                    self.vy = self.jump_power * 0.5
                    state.score += 100
                # Hit by enemy
                elif self.invincible <= 0:
                    if isinstance(enemy, Koopa) and enemy.shell_mode and not enemy.shell_moving:
                        # Can kick stopped shell safely
                        enemy.shell_moving = True
                        enemy.vx = 4 if self.x < enemy.x else -4
                    else:
                        self.take_damage(level_scene)
        
        # Collect coins (check ? blocks hit from below handled in tilemap)
        
        # Check pit death
        if self.y > HEIGHT + 50:
            self.die()
            
    def take_damage(self, level_scene):
        if state.mario_size == "big":
            state.mario_size = "small"
            self.update_size()
            self.invincible = 2
        else:
            self.die()
            
    def die(self):
        self.dead = True
        self.death_timer = 2.0
        self.vy = -6
        state.lives -= 1
        
    def start_victory(self, flag_y):
        self.victory = True
        self.flag_slide = True
        self.flag_y_target = flag_y
        self.vx = 0
        self.vy = 0
                    
    def draw(self, surf, cam):
        if self.invincible > 0 and int(self.invincible * 10) % 2 == 0:
            return  # Blink
            
        x = int(self.x - cam)
        y = int(self.y)
        
        if state.mario_size == "big":
            # Big Mario (32px tall)
            # Body
            pygame.draw.rect(surf, NES_PALETTE[33], (x+4, y+12, 8, 12))
            
            # Head
            pygame.draw.rect(surf, NES_PALETTE[39], (x+4, y+4, 8, 8))
            
            # Hat
            pygame.draw.rect(surf, NES_PALETTE[33], (x+2, y, 12, 4))
            
            # Arms
            arm_offset = 0
            if self.animation_frame == 1 and self.vx != 0:
                arm_offset = 2 if self.facing_right else -2
            pygame.draw.rect(surf, NES_PALETTE[39], (x+arm_offset, y+14, 4, 6))
            pygame.draw.rect(surf, NES_PALETTE[39], (x+12-arm_offset, y+14, 4, 6))
            
            # Legs
            leg_offset = 0
            if self.animation_frame == 2:
                leg_offset = 2
            pygame.draw.rect(surf, NES_PALETTE[21], (x+2, y+24, 5, 8))
            pygame.draw.rect(surf, NES_PALETTE[21], (x+9, y+24-leg_offset, 5, 8+leg_offset))
        else:
            # Small Mario (16px tall)
            # Body
            pygame.draw.rect(surf, NES_PALETTE[33], (x+4, y+8, 8, 8))
            
            # Head
            pygame.draw.rect(surf, NES_PALETTE[39], (x+4, y, 8, 8))
            
            # Hat
            pygame.draw.rect(surf, NES_PALETTE[33], (x+2, y, 12, 3))
            
            # Feet
            if self.animation_frame == 1:
                pygame.draw.rect(surf, NES_PALETTE[21], (x+2, y+14, 4, 2))
                pygame.draw.rect(surf, NES_PALETTE[21], (x+10, y+12, 4, 4))
            else:
                pygame.draw.rect(surf, NES_PALETTE[21], (x+3, y+14, 4, 2))
                pygame.draw.rect(surf, NES_PALETTE[21], (x+9, y+14, 4, 2))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ENEMY CLASSES (ALL 8 WORLDS)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class Goomba(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.vx = -0.5
        self.animation_frame = 0
        self.walk_timer = 0
        
    def update(self, colliders, dt):
        if not self.active:
            return
            
        # Turn at edges
        if self.on_ground:
            edge_x = self.x + (self.width + 2 if self.vx > 0 else -2)
            edge_check = pygame.Rect(edge_x, self.y + self.height + 2, 4, 4)
            edge_found = any(edge_check.colliderect(r) for r in colliders)
            if not edge_found:
                self.vx *= -1
                
        super().update(colliders, dt)
        
        self.walk_timer += dt
        if self.walk_timer > 0.15:
            self.walk_timer = 0
            self.animation_frame = (self.animation_frame + 1) % 2
            
    def draw(self, surf, cam):
        if not self.active:
            return
        x = int(self.x - cam)
        y = int(self.y)
        
        # Body
        pygame.draw.ellipse(surf, NES_PALETTE[21], (x+2, y+4, 12, 12))
        
        # Feet
        foot_offset = 2 if self.animation_frame == 0 else -2
        pygame.draw.rect(surf, NES_PALETTE[21], (x+2, y+14, 4, 2))
        pygame.draw.rect(surf, NES_PALETTE[21], (x+10, y+14+foot_offset, 4, 2))
        
        # Eyes
        pygame.draw.rect(surf, NES_PALETTE[0], (x+4, y+6, 2, 2))
        pygame.draw.rect(surf, NES_PALETTE[0], (x+10, y+6, 2, 2))

class Koopa(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.vx = -0.5
        self.animation_frame = 0
        self.walk_timer = 0
        self.shell_mode = False
        self.shell_moving = False
        
    def update(self, colliders, dt):
        if not self.active:
            return
            
        if self.shell_mode and self.shell_moving:
            # Shell slides fast
            super().update(colliders, dt)
            # Bounce off walls
            for rect in colliders:
                if self.get_rect().colliderect(rect):
                    self.vx *= -1
                    break
        elif self.shell_mode:
            # Stationary shell
            pass
        else:
            # Normal walking
            if self.on_ground:
                edge_x = self.x + (self.width + 2 if self.vx > 0 else -2)
                edge_check = pygame.Rect(edge_x, self.y + self.height + 2, 4, 4)
                edge_found = any(edge_check.colliderect(r) for r in colliders)
                if not edge_found:
                    self.vx *= -1
            super().update(colliders, dt)
            
            self.walk_timer += dt
            if self.walk_timer > 0.15:
                self.walk_timer = 0
                self.animation_frame = (self.animation_frame + 1) % 2
            
    def draw(self, surf, cam):
        if not self.active:
            return
        x = int(self.x - cam)
        y = int(self.y)
        
        # Shell
        pygame.draw.ellipse(surf, NES_PALETTE[14], (x+2, y+4, 12, 12))
        
        if not self.shell_mode:
            # Head and feet
            pygame.draw.rect(surf, NES_PALETTE[39], (x+4, y, 8, 4))
            pygame.draw.rect(surf, NES_PALETTE[14], (x+2, y+14, 4, 2))
            pygame.draw.rect(surf, NES_PALETTE[14], (x+10, y+14, 4, 2))
        else:
            # Shell pattern
            pygame.draw.rect(surf, NES_PALETTE[8], (x+4, y+6, 8, 8))

class Fish(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.vx = -0.8
        self.swim_timer = 0
        self.base_y = y
        
    def update(self, colliders, dt):
        self.swim_timer += dt
        self.x += self.vx * dt * 60
        self.y = self.base_y + math.sin(self.swim_timer * 4) * 20
        
    def draw(self, surf, cam):
        if not self.active:
            return
        x = int(self.x - cam)
        y = int(self.y)
        
        pygame.draw.ellipse(surf, NES_PALETTE[31], (x, y+2, 16, 12))
        pygame.draw.polygon(surf, NES_PALETTE[31], [(x, y+8), (x-6, y+2), (x-6, y+14)])
        pygame.draw.circle(surf, NES_PALETTE[0], (x+12, y+6), 2)

class Beetle(Entity):
    """World 4 - Buzzy Beetle (can't be killed by fireballs)"""
    def __init__(self, x, y):
        super().__init__(x, y)
        self.vx = -0.6
        self.animation_frame = 0
        self.walk_timer = 0
        
    def update(self, colliders, dt):
        if not self.active:
            return
        if self.on_ground:
            edge_x = self.x + (self.width + 2 if self.vx > 0 else -2)
            edge_check = pygame.Rect(edge_x, self.y + self.height + 2, 4, 4)
            edge_found = any(edge_check.colliderect(r) for r in colliders)
            if not edge_found:
                self.vx *= -1
        super().update(colliders, dt)
        self.walk_timer += dt
        if self.walk_timer > 0.12:
            self.walk_timer = 0
            self.animation_frame = (self.animation_frame + 1) % 2
            
    def draw(self, surf, cam):
        if not self.active:
            return
        x = int(self.x - cam)
        y = int(self.y)
        # Dark blue shell
        pygame.draw.ellipse(surf, NES_PALETTE[2], (x+1, y+2, 14, 14))
        pygame.draw.rect(surf, NES_PALETTE[2], (x+3, y+12, 4, 4))
        pygame.draw.rect(surf, NES_PALETTE[2], (x+9, y+12, 4, 4))

class Paratroopa(Entity):
    """World 5 - Flying Koopa"""
    def __init__(self, x, y):
        super().__init__(x, y)
        self.vx = -0.4
        self.base_y = y
        self.fly_timer = random.random() * 6.28
        
    def update(self, colliders, dt):
        self.fly_timer += dt * 3
        self.x += self.vx * dt * 60
        self.y = self.base_y + math.sin(self.fly_timer) * 30
        
    def draw(self, surf, cam):
        if not self.active:
            return
        x = int(self.x - cam)
        y = int(self.y)
        # Body
        pygame.draw.ellipse(surf, NES_PALETTE[14], (x+2, y+6, 12, 10))
        pygame.draw.rect(surf, NES_PALETTE[39], (x+4, y+2, 8, 4))
        # Wings
        wing_y = int(math.sin(self.fly_timer * 4) * 2)
        pygame.draw.ellipse(surf, NES_PALETTE[31], (x-4, y+4+wing_y, 8, 6))
        pygame.draw.ellipse(surf, NES_PALETTE[31], (x+12, y+4-wing_y, 8, 6))

class Spiny(Entity):
    """World 6 - Can't be stomped"""
    def __init__(self, x, y):
        super().__init__(x, y)
        self.vx = -0.5
        
    def update(self, colliders, dt):
        if not self.active:
            return
        if self.on_ground:
            edge_x = self.x + (self.width + 2 if self.vx > 0 else -2)
            edge_check = pygame.Rect(edge_x, self.y + self.height + 2, 4, 4)
            edge_found = any(edge_check.colliderect(r) for r in colliders)
            if not edge_found:
                self.vx *= -1
        super().update(colliders, dt)
            
    def draw(self, surf, cam):
        if not self.active:
            return
        x = int(self.x - cam)
        y = int(self.y)
        # Red spiky shell
        pygame.draw.ellipse(surf, NES_PALETTE[6], (x+2, y+6, 12, 10))
        # Spikes
        for i in range(3):
            sx = x + 4 + i * 4
            pygame.draw.polygon(surf, NES_PALETTE[39], [(sx, y+6), (sx-2, y), (sx+2, y)])

class Spike(Entity):
    """World 7 - Static spike hazard"""
    def __init__(self, x, y):
        super().__init__(x, y)
        
    def update(self, colliders, dt):
        pass  # Static
        
    def draw(self, surf, cam):
        x = int(self.x - cam)
        y = int(self.y)
        pygame.draw.rect(surf, NES_PALETTE[6], (x, y+8, TILE, 8))
        pygame.draw.polygon(surf, NES_PALETTE[6], [(x+2, y+8), (x+8, y), (x+14, y+8)])

class BowserMinion(Entity):
    """World 8 - Hammer Bro style"""
    def __init__(self, x, y):
        super().__init__(x, y)
        self.vx = -0.3
        self.jump_timer = random.random() * 2
        
    def update(self, colliders, dt):
        if not self.active:
            return
        self.jump_timer -= dt
        if self.jump_timer <= 0 and self.on_ground:
            self.vy = -4
            self.jump_timer = 1.5 + random.random()
        super().update(colliders, dt)
            
    def draw(self, surf, cam):
        if not self.active:
            return
        x = int(self.x - cam)
        y = int(self.y)
        # Body
        pygame.draw.rect(surf, NES_PALETTE[14], (x+2, y+4, 12, 12))
        # Head
        pygame.draw.rect(surf, NES_PALETTE[39], (x+4, y, 8, 6))
        # Eyes
        pygame.draw.rect(surf, NES_PALETTE[0], (x+5, y+2, 2, 2))
        pygame.draw.rect(surf, NES_PALETTE[0], (x+9, y+2, 2, 2))

def create_enemy(enemy_type, x, y):
    """Factory function for enemy creation"""
    enemy_classes = {
        "goomba": Goomba,
        "koopa": Koopa,
        "fish": Fish,
        "beetle": Beetle,
        "paratroopa": Paratroopa,
        "spiny": Spiny,
        "spike": Spike,
        "bowser_minion": BowserMinion
    }
    cls = enemy_classes.get(enemy_type, Goomba)
    return cls(x, y)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MUSHROOM POWERUP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class Mushroom(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.vx = 1.0
        self.emerge_timer = 0.5
        self.start_y = y
        self.emerged = False
        
    def update(self, colliders, dt):
        if self.emerge_timer > 0:
            self.emerge_timer -= dt
            self.y = self.start_y + (self.emerge_timer / 0.5) * TILE
            return
        self.emerged = True
        super().update(colliders, dt)
        # Reverse at walls
        for rect in colliders:
            if self.get_rect().colliderect(rect):
                self.vx *= -1
                break
                
    def draw(self, surf, cam):
        if not self.active:
            return
        x = int(self.x - cam)
        y = int(self.y)
        # Cap
        pygame.draw.ellipse(surf, NES_PALETTE[6], (x, y, 16, 10))
        # Spots
        pygame.draw.circle(surf, NES_PALETTE[31], (x+4, y+4), 2)
        pygame.draw.circle(surf, NES_PALETTE[31], (x+12, y+4), 2)
        # Stem
        pygame.draw.rect(surf, NES_PALETTE[39], (x+4, y+8, 8, 8))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TILEMAP (FIXED BLOCK INTERACTION)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class TileMap:
    def __init__(self, level_data, level_id):
        self.tiles = []
        self.colliders = []
        self.question_blocks = {}  # {(x, y): {"hit": False, "contains": "coin"|"mushroom"}}
        self.brick_blocks = set()
        tiles_data = level_data["tiles"]
        self.width = level_data["width"]
        self.height = len(tiles_data) * TILE
        self.level_id = level_id
        world = int(level_id.split("-")[0])
        self.theme = WORLD_THEMES[world]
        
        for y, row in enumerate(tiles_data):
            for x, char in enumerate(row):
                if char != " ":
                    rect = pygame.Rect(x * TILE, y * TILE, TILE, TILE)
                    self.tiles.append((x * TILE, y * TILE, char))
                    
                    if char in ("G", "D", "P", "T", "?", "B"):
                        self.colliders.append(rect)
                        
                    if char == "?":
                        # Random contents
                        contents = "mushroom" if random.random() < 0.3 else "coin"
                        self.question_blocks[(x * TILE, y * TILE)] = {
                            "hit": False, 
                            "contains": contents
                        }
                    elif char == "B":
                        self.brick_blocks.add((x * TILE, y * TILE))
    
    def hit_block(self, x, y, player, effects, mushrooms):
        """Check if player hit a block from below"""
        # Find block above player
        block_x = int((x + player.width // 2) // TILE) * TILE
        block_y = int((y - 1) // TILE) * TILE
        
        pos = (block_x, block_y)
        
        if pos in self.question_blocks:
            block = self.question_blocks[pos]
            if not block["hit"]:
                block["hit"] = True
                if block["contains"] == "coin":
                    state.coins += 1
                    state.score += 200
                    effects.append(CoinEffect(block_x + 4, block_y - TILE))
                elif block["contains"] == "mushroom":
                    mushrooms.append(Mushroom(block_x, block_y - TILE))
                return True
                
        if pos in self.brick_blocks and state.mario_size == "big":
            # Big Mario breaks bricks
            self.brick_blocks.discard(pos)
            # Remove from tiles and colliders
            self.tiles = [(tx, ty, c) for tx, ty, c in self.tiles if not (tx == block_x and ty == block_y)]
            self.colliders = [r for r in self.colliders if not (r.x == block_x and r.y == block_y)]
            # Particle effect
            for _ in range(4):
                effects.append(Particle(
                    block_x + 8, block_y + 8,
                    random.uniform(-2, 2), random.uniform(-4, -1),
                    NES_PALETTE[self.theme["block"]], 0.5
                ))
            state.score += 50
            return True
            
        return False
    
    def draw(self, surf, cam):
        # Sky
        surf.fill(NES_PALETTE[self.theme["sky"]])
        
        # Parallax clouds
        for i in range(15):
            cx = (i * 120 - int(cam * 0.3)) % (self.width + 400) - 200
            cy = 30 + (i % 4) * 25
            pygame.draw.ellipse(surf, NES_PALETTE[31], (cx, cy, 40, 20))
            pygame.draw.ellipse(surf, NES_PALETTE[31], (cx + 20, cy - 8, 30, 18))
        
        # Tiles
        for tx, ty, char in self.tiles:
            draw_x = tx - cam
            if draw_x < -TILE or draw_x > WIDTH + TILE:
                continue
                
            if char == "G":  # Ground top
                pygame.draw.rect(surf, NES_PALETTE[self.theme["ground"]], (draw_x, ty, TILE, TILE))
                pygame.draw.rect(surf, NES_PALETTE[max(0, self.theme["ground"]-1)], (draw_x, ty+10, TILE, 6))
                # Grass detail
                pygame.draw.rect(surf, NES_PALETTE[14], (draw_x+2, ty+2, 4, 4))
                pygame.draw.rect(surf, NES_PALETTE[14], (draw_x+10, ty+2, 4, 4))
            elif char == "D":  # Dirt
                pygame.draw.rect(surf, NES_PALETTE[max(0, self.theme["ground"]-2)], (draw_x, ty, TILE, TILE))
            elif char == "P":  # Platform
                pygame.draw.rect(surf, NES_PALETTE[self.theme["ground"]], (draw_x, ty, TILE, TILE))
                pygame.draw.rect(surf, NES_PALETTE[max(0, self.theme["ground"]-1)], (draw_x+2, ty+2, TILE-4, TILE-4))
            elif char == "T":  # Pipe
                pygame.draw.rect(surf, NES_PALETTE[self.theme["pipe"]], (draw_x, ty, TILE, TILE))
                pygame.draw.rect(surf, NES_PALETTE[max(0, self.theme["pipe"]+2)], (draw_x+2, ty, 4, TILE))
            elif char == "?":  # Question block
                pos = (tx, ty)
                if pos in self.question_blocks and self.question_blocks[pos]["hit"]:
                    # Used block
                    pygame.draw.rect(surf, NES_PALETTE[21], (draw_x, ty, TILE, TILE))
                    pygame.draw.rect(surf, NES_PALETTE[20], (draw_x+2, ty+2, TILE-4, TILE-4))
                else:
                    # Active block
                    pygame.draw.rect(surf, NES_PALETTE[35], (draw_x, ty, TILE, TILE))
                    pygame.draw.rect(surf, NES_PALETTE[39], (draw_x+2, ty+2, TILE-4, TILE-4))
                    # ? symbol
                    pygame.draw.rect(surf, NES_PALETTE[21], (draw_x+5, ty+3, 6, 2))
                    pygame.draw.rect(surf, NES_PALETTE[21], (draw_x+9, ty+5, 2, 4))
                    pygame.draw.rect(surf, NES_PALETTE[21], (draw_x+5, ty+9, 6, 2))
                    pygame.draw.rect(surf, NES_PALETTE[21], (draw_x+5, ty+9, 2, 2))
                    pygame.draw.rect(surf, NES_PALETTE[21], (draw_x+6, ty+13, 4, 2))
            elif char == "B":  # Brick
                if (tx, ty) in self.brick_blocks:
                    pygame.draw.rect(surf, NES_PALETTE[self.theme["block"]], (draw_x, ty, TILE, TILE))
                    pygame.draw.rect(surf, NES_PALETTE[0], (draw_x, ty+7, TILE, 2))
                    pygame.draw.rect(surf, NES_PALETTE[0], (draw_x+7, ty, 2, TILE))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SCENES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class TitleScreen(Scene):
    def __init__(self):
        self.timer = 0
        self.animation_frame = 0
        self.logo_y = -50
        self.logo_target_y = HEIGHT // 2 - 80
        
    def handle(self, events, keys):
        for e in events:
            if e.type == KEYDOWN and e.key == K_RETURN:
                push(FileSelect())
                
    def update(self, dt):
        self.timer += dt
        if self.timer > 0.1:
            self.timer -= 0.1
            self.animation_frame = (self.animation_frame + 1) % 4
            
        if self.logo_y < self.logo_target_y:
            self.logo_y += 4
        return None
            
    def draw(self, surf):
        surf.fill(NES_PALETTE[27])
        
        # Logo box
        box_w, box_h = 280, 120
        box_x = (WIDTH - box_w) // 2
        box_y = int(self.logo_y)
        
        pygame.draw.rect(surf, NES_PALETTE[0], (box_x-4, box_y-4, box_w+8, box_h+8))
        pygame.draw.rect(surf, NES_PALETTE[33], (box_x, box_y, box_w, box_h))
        
        # Title
        title_font = pygame.font.SysFont(None, 36)
        title = title_font.render("AC!'S Koopa Engine 0.1", True, NES_PALETTE[39])
        surf.blit(title, (box_x + (box_w - title.get_width()) // 2, box_y + 20))
        
        subtitle_font = pygame.font.SysFont(None, 18)
        subtitle = subtitle_font.render("8 WORLDS", True, NES_PALETTE[21])
        surf.blit(subtitle, (box_x + (box_w - subtitle.get_width()) // 2, box_y + 55))
        
        # Copyright
        cr_font = pygame.font.SysFont(None, 12)
        cr1 = cr_font.render("(C) AC Computing 1999-2026", True, NES_PALETTE[0])
        cr2 = cr_font.render("(C) 1985 - 2026 Nintendo", True, NES_PALETTE[0])
        cr3 = cr_font.render("(C) Samsoft 2000-2026", True, NES_PALETTE[0])
        surf.blit(cr1, (box_x + (box_w - cr1.get_width()) // 2, box_y + 82))
        surf.blit(cr2, (box_x + (box_w - cr2.get_width()) // 2, box_y + 96))
        surf.blit(cr3, (box_x + (box_w - cr3.get_width()) // 2, box_y + 110))
        
        # Characters
        if self.logo_y >= self.logo_target_y:
            char_y = box_y + box_h + 40
            
            # Mario
            mx = WIDTH//2 - 80
            pygame.draw.rect(surf, NES_PALETTE[33], (mx+4, char_y+8, 8, 16))
            pygame.draw.rect(surf, NES_PALETTE[39], (mx+4, char_y+4, 8, 4))
            pygame.draw.rect(surf, NES_PALETTE[33], (mx+2, char_y, 12, 4))
            
            # Goomba
            gx = WIDTH//2 + 20
            pygame.draw.ellipse(surf, NES_PALETTE[21], (gx+2, char_y+12, 12, 12))
            pygame.draw.rect(surf, NES_PALETTE[0], (gx+4, char_y+14, 2, 2))
            pygame.draw.rect(surf, NES_PALETTE[0], (gx+10, char_y+14, 2, 2))
            
            # Koopa
            kx = WIDTH//2 + 60
            pygame.draw.ellipse(surf, NES_PALETTE[14], (kx+2, char_y+12, 12, 12))
            pygame.draw.rect(surf, NES_PALETTE[39], (kx+4, char_y+8, 8, 4))
            
            # Press Enter
            if int(self.timer * 5) % 2 == 0:
                font = pygame.font.SysFont(None, 24)
                text = font.render("PRESS ENTER", True, NES_PALETTE[39])
                surf.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT - 40))

class FileSelect(Scene):
    def __init__(self):
        self.selected = 0
        self.offset = 0
        
    def handle(self, events, keys):
        for e in events:
            if e.type == KEYDOWN:
                if e.key in (K_1, K_2, K_3):
                    self.selected = e.key - K_1
                elif e.key == K_LEFT:
                    self.selected = max(0, self.selected - 1)
                elif e.key == K_RIGHT:
                    self.selected = min(2, self.selected + 1)
                elif e.key == K_RETURN:
                    state.slot = self.selected
                    state.world = state.progress[state.slot]["world"]
                    push(WorldMapScene())
                elif e.key == K_ESCAPE:
                    pop()  # FIXED: was push(TitleScreen())
                    
    def update(self, dt):
        self.offset += dt
        return None
        
    def draw(self, surf):
        surf.fill(NES_PALETTE[27])
        
        font = pygame.font.SysFont(None, 32)
        title = font.render("SELECT FILE", True, NES_PALETTE[33])
        surf.blit(title, (WIDTH//2 - title.get_width()//2, 30))
        
        for i in range(3):
            x = 80 + i * 150
            y = 100 + int(math.sin(self.offset * 3 + i) * 5)
            
            # Box
            pygame.draw.rect(surf, NES_PALETTE[21], (x-5, y-5, 80, 100))
            pygame.draw.rect(surf, NES_PALETTE[33], (x, y, 70, 90))
            
            # Selection
            if i == self.selected:
                pygame.draw.rect(surf, NES_PALETTE[39], (x-3, y-3, 76, 96), 3)
                
            # Slot number
            slot_font = pygame.font.SysFont(None, 24)
            slot_text = slot_font.render(f"FILE {i+1}", True, NES_PALETTE[39])
            surf.blit(slot_text, (x + 35 - slot_text.get_width()//2, y + 5))
            
            # World progress
            world = state.progress[i]["world"]
            world_font = pygame.font.SysFont(None, 18)
            world_text = world_font.render(f"WORLD {world}", True, NES_PALETTE[39])
            surf.blit(world_text, (x + 35 - world_text.get_width()//2, y + 70))
            
            # Thumbnail
            thumb = THUMBNAILS.get(f"{world}-1")
            if thumb:
                surf.blit(thumb, (x + 19, y + 30))

class WorldMapScene(Scene):
    def __init__(self):
        self.selection = state.world
        self.cursor_timer = 0
        
    def handle(self, events, keys):
        for e in events:
            if e.type == KEYDOWN:
                if e.key == K_LEFT and self.selection > 1:
                    self.selection -= 1
                elif e.key == K_RIGHT and self.selection < 8:
                    self.selection += 1
                elif e.key == K_UP and self.selection > 4:
                    self.selection -= 4
                elif e.key == K_DOWN and self.selection < 5:
                    self.selection += 4
                elif e.key == K_RETURN:
                    if self.selection <= max(state.unlocked_worlds):
                        state.world = self.selection
                        state.progress[state.slot]["world"] = self.selection
                        push(LevelScene(f"{state.world}-1"))
                elif e.key == K_ESCAPE:
                    pop()  # FIXED: was push(FileSelect())
                    
    def update(self, dt):
        self.cursor_timer += dt
        return None
        
    def draw(self, surf):
        surf.fill(NES_PALETTE[27])
        
        font = pygame.font.SysFont(None, 32)
        title = font.render("WORLD MAP", True, NES_PALETTE[33])
        surf.blit(title, (WIDTH//2 - title.get_width()//2, 20))
        
        # World grid
        world_size = 50
        for world in range(1, 9):
            row = (world - 1) // 4
            col = (world - 1) % 4
            x = 50 + col * 80
            y = 80 + row * 80
            
            theme = WORLD_THEMES[world]
            
            if world in state.unlocked_worlds:
                pygame.draw.rect(surf, NES_PALETTE[theme["ground"]], (x, y, world_size, world_size))
                pygame.draw.rect(surf, NES_PALETTE[theme["block"]], (x+5, y+5, world_size-10, world_size-10))
            else:
                pygame.draw.rect(surf, NES_PALETTE[0], (x, y, world_size, world_size))
                pygame.draw.line(surf, NES_PALETTE[33], (x, y), (x+world_size, y+world_size), 3)
                pygame.draw.line(surf, NES_PALETTE[33], (x+world_size, y), (x, y+world_size), 3)
            
            # World number
            num_font = pygame.font.SysFont(None, 24)
            num = num_font.render(str(world), True, NES_PALETTE[39])
            surf.blit(num, (x + world_size//2 - num.get_width()//2, y + world_size//2 - num.get_height()//2))
            
            # Selection cursor
            if world == self.selection:
                offset = int(math.sin(self.cursor_timer * 5) * 3)
                pygame.draw.rect(surf, NES_PALETTE[39], (x-3, y-3+offset, world_size+6, 5))
                pygame.draw.rect(surf, NES_PALETTE[39], (x-3, y+world_size-2+offset, world_size+6, 5))
                
                # World name
                name_font = pygame.font.SysFont(None, 18)
                name = name_font.render(theme["name"], True, NES_PALETTE[39])
                surf.blit(name, (WIDTH//2 - name.get_width()//2, HEIGHT - 60))
        
        # Instructions
        inst_font = pygame.font.SysFont(None, 16)
        inst = inst_font.render("ARROWS: Move  ENTER: Select  ESC: Back", True, NES_PALETTE[39])
        surf.blit(inst, (WIDTH//2 - inst.get_width()//2, HEIGHT - 25))
        
        # Progress
        prog = inst_font.render(f"Worlds Unlocked: {max(state.unlocked_worlds)}/8", True, NES_PALETTE[39])
        surf.blit(prog, (10, HEIGHT - 25))

class LevelScene(Scene):
    def __init__(self, level_id):
        level_data = LEVELS[level_id]
        self.map = TileMap(level_data, level_id)
        
        # Player at fixed start position
        start_x, start_y = level_data["player_start"]
        self.player = Player(start_x, start_y)
        self.player.update_size()
        
        # Enemies from level data
        self.enemies = []
        for enemy_data in level_data["enemies"]:
            enemy = create_enemy(enemy_data["type"], enemy_data["x"], enemy_data["y"])
            self.enemies.append(enemy)
        
        self.mushrooms = []
        self.effects = []
        self.cam = 0.0
        self.level_id = level_id
        self.time = 300
        self.end_level = False
        self.end_timer = 0
        
        world = int(level_id.split("-")[0])
        self.theme = WORLD_THEMES[world]
        self.flag_pos = level_data["flag_pos"]
        
        # Previous player vy for block hit detection
        self.prev_vy = 0
        
    def handle(self, events, keys):
        for e in events:
            if e.type == KEYDOWN and e.key == K_ESCAPE:
                pop()  # FIXED: was push(WorldMapScene())
                
    def update(self, dt):
        # Time
        if not self.end_level:
            self.time -= dt
            if self.time <= 0:
                self.player.die()
        
        # Check block hit (player head hit ceiling while rising)
        if self.prev_vy < 0 and self.player.vy >= 0:
            self.map.hit_block(self.player.x, self.player.y, self.player, self.effects, self.mushrooms)
        self.prev_vy = self.player.vy
        
        # Update player
        self.player.update(self.map.colliders, dt, self.enemies, self)
        
        # Check death
        if self.player.dead and self.player.death_timer <= 0:
            if state.lives <= 0:
                clear_to(GameOverScene())
            else:
                # Restart level
                replace(LevelScene(self.level_id))
            return None
        
        # Update enemies
        for enemy in self.enemies:
            if enemy.active:
                enemy.update(self.map.colliders, dt)
                # Remove enemies that fall off
                if enemy.y > HEIGHT + 100:
                    enemy.active = False
        
        # Update mushrooms
        for mush in self.mushrooms:
            if mush.active:
                mush.update(self.map.colliders, dt)
                # Check player collection
                if mush.emerged and self.player.get_rect().colliderect(mush.get_rect()):
                    mush.active = False
                    if state.mario_size == "small":
                        state.mario_size = "big"
                        self.player.update_size()
                    state.score += 1000
        
        # Update effects
        for effect in self.effects[:]:
            effect.update(dt)
            if not effect.active:
                self.effects.remove(effect)
        
        # Camera
        target = self.player.x - WIDTH // 2
        self.cam += (target - self.cam) * 0.1
        self.cam = max(0, min(self.cam, self.map.width - WIDTH))
        
        # Check victory
        if not self.end_level and self.player.x > self.flag_pos[0] - 20:
            self.end_level = True
            flag_ground_y = 14 * TILE
            self.player.start_victory(flag_ground_y)
            # Time bonus
            time_bonus = int(self.time) * 10
            state.score += time_bonus
            
        # End level transition
        if self.end_level and self.player.victory and not self.player.flag_slide:
            self.end_timer += dt
            if self.end_timer > 2.5:
                world, level = self.level_id.split("-")
                world = int(world)
                level = int(level)
                
                if level < 4:
                    # Next level in world
                    replace(LevelScene(f"{world}-{level+1}"))
                else:
                    # World complete
                    if world < 8:
                        if (world + 1) not in state.unlocked_worlds:
                            state.unlocked_worlds.append(world + 1)
                        replace(WorldMapScene())
                    else:
                        # GAME COMPLETE!
                        clear_to(WinScreen())
        
        return None
        
    def draw(self, surf):
        # Map
        self.map.draw(surf, self.cam)
        
        # Flag (drawn at fixed position)
        flag_x = self.flag_pos[0] - self.cam
        flag_y = self.flag_pos[1]
        # Pole
        pygame.draw.rect(surf, NES_PALETTE[14], (flag_x + 6, flag_y, 4, TILE * 5))
        # Ball on top
        pygame.draw.circle(surf, NES_PALETTE[39], (int(flag_x + 8), int(flag_y)), 4)
        # Flag
        pygame.draw.polygon(surf, NES_PALETTE[33], [
            (flag_x + 10, flag_y + 4),
            (flag_x + 30, flag_y + 14),
            (flag_x + 10, flag_y + 24)
        ])
        
        # Enemies
        for enemy in self.enemies:
            enemy.draw(surf, self.cam)
            
        # Mushrooms
        for mush in self.mushrooms:
            mush.draw(surf, self.cam)
            
        # Effects
        for effect in self.effects:
            effect.draw(surf, self.cam)
            
        # Player
        self.player.draw(surf, self.cam)
        
        # HUD (FIXED layout - no overlap)
        pygame.draw.rect(surf, NES_PALETTE[0], (0, 0, WIDTH, 24))
        
        hud_font = pygame.font.SysFont(None, 18)
        
        # Score (left)
        score_text = hud_font.render(f"SCORE:{state.score:06d}", True, NES_PALETTE[39])
        surf.blit(score_text, (8, 5))
        
        # Coins (left-center)
        coin_text = hud_font.render(f"x{state.coins:02d}", True, NES_PALETTE[39])
        pygame.draw.rect(surf, NES_PALETTE[35], (140, 6, 8, 10))
        surf.blit(coin_text, (150, 5))
        
        # World (center)
        world_text = hud_font.render(f"WORLD {self.level_id}", True, NES_PALETTE[39])
        surf.blit(world_text, (WIDTH//2 - world_text.get_width()//2, 5))
        
        # Time (right-center)
        time_text = hud_font.render(f"TIME:{int(max(0, self.time)):03d}", True, NES_PALETTE[39])
        surf.blit(time_text, (WIDTH - 150, 5))
        
        # Lives (right)
        pygame.draw.rect(surf, NES_PALETTE[33], (WIDTH - 50, 6, 8, 10))
        lives_text = hud_font.render(f"x{state.lives}", True, NES_PALETTE[39])
        surf.blit(lives_text, (WIDTH - 40, 5))
        
        # World theme name
        name_font = pygame.font.SysFont(None, 16)
        name_text = name_font.render(self.theme["name"], True, NES_PALETTE[39])
        surf.blit(name_text, (WIDTH//2 - name_text.get_width()//2, HEIGHT - 18))

class GameOverScene(Scene):
    def __init__(self):
        self.timer = 3
        
    def update(self, dt):
        self.timer -= dt
        if self.timer <= 0:
            # FIXED: Reset state and go to FileSelect
            state.lives = 3
            state.score = 0
            state.coins = 0
            state.mario_size = "small"
            clear_to(FileSelect())
        return None
            
    def draw(self, surf):
        surf.fill(NES_PALETTE[0])
        
        font = pygame.font.SysFont(None, 48)
        text = font.render("GAME OVER", True, NES_PALETTE[33])
        surf.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - 40))
        
        font2 = pygame.font.SysFont(None, 24)
        score_text = font2.render(f"FINAL SCORE: {state.score}", True, NES_PALETTE[39])
        surf.blit(score_text, (WIDTH//2 - score_text.get_width()//2, HEIGHT//2 + 20))

class WinScreen(Scene):
    def __init__(self):
        self.timer = 8
        self.fireworks = []
        
    def update(self, dt):
        self.timer -= dt
        
        # Spawn fireworks
        if random.random() < 0.15:
            self.fireworks.append({
                "x": random.randint(50, WIDTH-50),
                "y": HEIGHT,
                "vy": -4,
                "color": random.choice([NES_PALETTE[33], NES_PALETTE[39], NES_PALETTE[31], NES_PALETTE[35]]),
                "particles": [],
                "exploded": False
            })
        
        # Update fireworks
        for fw in self.fireworks[:]:
            if not fw["exploded"]:
                fw["y"] += fw["vy"]
                if fw["y"] < random.randint(50, HEIGHT//2):
                    fw["exploded"] = True
                    for _ in range(20):
                        angle = random.uniform(0, math.pi * 2)
                        speed = random.uniform(2, 5)
                        fw["particles"].append({
                            "x": fw["x"],
                            "y": fw["y"],
                            "vx": math.cos(angle) * speed,
                            "vy": math.sin(angle) * speed,
                            "life": 1.0
                        })
            else:
                for p in fw["particles"][:]:
                    p["x"] += p["vx"]
                    p["y"] += p["vy"]
                    p["vy"] += 0.1
                    p["life"] -= 0.02
                    if p["life"] <= 0:
                        fw["particles"].remove(p)
                if not fw["particles"]:
                    self.fireworks.remove(fw)
        
        if self.timer <= 0:
            # Reset for new game
            state.lives = 3
            state.score = 0
            state.coins = 0
            state.mario_size = "small"
            state.unlocked_worlds = [1]
            clear_to(TitleScreen())
        return None
            
    def draw(self, surf):
        surf.fill(NES_PALETTE[0])
        
        # Fireworks
        for fw in self.fireworks:
            if not fw["exploded"]:
                pygame.draw.circle(surf, NES_PALETTE[39], (int(fw["x"]), int(fw["y"])), 3)
            for p in fw["particles"]:
                alpha = max(0, min(1, p["life"]))
                size = max(1, int(3 * alpha))
                pygame.draw.circle(surf, fw["color"], (int(p["x"]), int(p["y"])), size)
        
        # Text
        font1 = pygame.font.SysFont(None, 48)
        text1 = font1.render("CONGRATULATIONS!", True, NES_PALETTE[33])
        surf.blit(text1, (WIDTH//2 - text1.get_width()//2, 60))
        
        font2 = pygame.font.SysFont(None, 32)
        text2 = font2.render("YOU SAVED THE PRINCESS!", True, NES_PALETTE[39])
        surf.blit(text2, (WIDTH//2 - text2.get_width()//2, 120))
        
        font3 = pygame.font.SysFont(None, 28)
        text3 = font3.render(f"FINAL SCORE: {state.score}", True, NES_PALETTE[35])
        surf.blit(text3, (WIDTH//2 - text3.get_width()//2, 170))
        
        # Thank you message
        font4 = pygame.font.SysFont(None, 20)
        text4 = font4.render("THANK YOU FOR PLAYING!", True, NES_PALETTE[31])
        surf.blit(text4, (WIDTH//2 - text4.get_width()//2, HEIGHT - 60))
        
        # Credits
        font5 = pygame.font.SysFont(None, 14)
        text5 = font5.render("(C) AC Computing 1999-2026  (C) 1985-2026 Nintendo  (C) Samsoft 2000-2026", True, NES_PALETTE[39])
        surf.blit(text5, (WIDTH//2 - text5.get_width()//2, HEIGHT - 30))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN GAME LOOP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("AC!'S Koopa Engine 0.1 - (C) AC Computing / Nintendo / Samsoft")
    clock = pygame.time.Clock()
    
    # Generate thumbnails AFTER pygame.init() - FIXES PRE-INIT CRASH
    generate_thumbnails()
    
    # Start with title
    push(TitleScreen())
    
    running = True
    while running and SCENES:
        dt = clock.tick(FPS) / 1000.0
        
        events = pygame.event.get()
        keys = pygame.key.get_pressed()
        
        for e in events:
            if e.type == QUIT:
                running = False
                
        # Update current scene
        scene = SCENES[-1]
        scene.handle(events, keys)
        scene.update(dt)
        scene.draw(screen)
        
        pygame.display.flip()
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
