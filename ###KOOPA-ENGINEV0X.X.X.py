#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                        AC!'S KOOPA ENGINE 1.1                                 ║
║═══════════════════════════════════════════════════════════════════════════════║
║  Team Flames / Samsoft / Flames Co. 20XX                                      ║
║  1:1 Super Mario Bros. Physics + Lunar Magic-Style Level Editor               ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║  FEATURES:                                                                    ║
║  • SMB1-accurate physics (gravity, jump, acceleration)                        ║
║  • Title screen with animated logo                                            ║
║  • World map with 8 worlds                                                    ║
║  • Lunar Magic-style level editor                                             ║
║  • Export standalone .py games                                                ║
║  • Save/Load custom levels                                                    ║
║  • Undo/Redo system                                                           ║
║  • 8 world themes                                                             ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║  CONTROLS:                                                                    ║
║  [MENU] Arrows: Navigate | Enter: Select | Escape: Back                       ║
║  [GAME] Arrows/WASD: Move | Space/Z: Jump | Shift/X: Run | Enter: Pause       ║
║  [EDITOR] Tab: Toggle | H: Help | See help for full controls                  ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

import pygame
import sys
import math
import random
import os
import copy
import datetime
from pygame.locals import *

# ╔═══════════════════════════════════════════════════════════════════════════════╗
# ║ SMB1 CONSTANTS (NES Accurate)                                                 ║
# ╚═══════════════════════════════════════════════════════════════════════════════╝
SCALE = 2
TILE = 16
WIDTH = 256 * SCALE
HEIGHT = 240 * SCALE
FPS = 60

# SMB1 Physics (converted from NES subpixels)
GRAVITY = 0.4375
GRAVITY_HOLD = 0.1875
MAX_FALL = 4.5
JUMP_WALK = -4.0
JUMP_RUN = -5.0
JUMP_HOLD_TIME = 0.25
WALK_SPEED = 1.3
RUN_SPEED = 2.5
WALK_ACCEL = 0.15
RUN_ACCEL = 0.2
DECEL = 0.1
SKID_DECEL = 0.25
AIR_ACCEL = 0.1
GOOMBA_SPEED = 0.5
KOOPA_SPEED = 0.5
SHELL_SPEED = 4.0

# NES 2C02 PPU Palette
PAL = [
    (84,84,84),(0,30,116),(8,16,144),(48,0,136),(68,0,100),(92,0,48),(84,4,0),(60,24,0),
    (32,42,0),(8,58,0),(0,64,0),(0,60,0),(0,50,60),(0,0,0),(0,0,0),(0,0,0),
    (152,150,152),(8,76,196),(48,50,236),(92,30,228),(136,20,176),(160,20,100),(152,34,32),(120,60,0),
    (84,90,0),(40,114,0),(8,124,0),(0,118,40),(0,102,120),(0,0,0),(0,0,0),(0,0,0),
    (236,238,236),(76,154,236),(120,124,236),(176,98,236),(228,84,236),(236,88,180),(236,106,100),(212,136,32),
    (160,170,0),(116,196,0),(76,208,32),(56,204,108),(56,180,204),(60,60,60),(0,0,0),(0,0,0),
    (236,238,236),(168,204,236),(188,188,236),(212,178,236),(236,174,236),(236,174,212),(236,180,176),(228,196,144),
    (204,210,120),(180,222,120),(168,226,144),(152,226,180),(160,214,228),(160,162,160),(0,0,0),(0,0,0)
]

# Color shortcuts
SKY = PAL[34]
BRICK = PAL[22]
QBLOCK = PAL[39]
PIPE_G = PAL[26]
MARIO_R = PAL[22]
MARIO_S = PAL[54]
GOOMBA = PAL[23]
KOOPA_G = PAL[26]

# ╔═══════════════════════════════════════════════════════════════════════════════╗
# ║ GAME STATE                                                                    ║
# ╚═══════════════════════════════════════════════════════════════════════════════╝
class GameState:
    def __init__(self):
        self.reset()
        self.high_score = 0
        
    def reset(self):
        self.score = 0
        self.coins = 0
        self.lives = 3
        self.world = 1
        self.level = 1
        self.time = 400
        self.powerup = 0
        
    def add_coin(self):
        self.coins += 1
        self.score += 200
        if self.coins >= 100:
            self.coins = 0
            self.lives += 1

state = GameState()

# ╔═══════════════════════════════════════════════════════════════════════════════╗
# ║ WORLD THEMES                                                                  ║
# ╚═══════════════════════════════════════════════════════════════════════════════╝
THEMES = {
    1: {"name": "GRASS LAND", "sky": 34, "ground": 23, "brick": 22, "pipe": 26},
    2: {"name": "DESERT HILL", "sky": 39, "ground": 23, "brick": 22, "pipe": 26},
    3: {"name": "OCEAN SIDE", "sky": 34, "ground": 27, "brick": 17, "pipe": 26},
    4: {"name": "GIANT LAND", "sky": 24, "ground": 23, "brick": 22, "pipe": 10},
    5: {"name": "SKY WORLD", "sky": 34, "ground": 32, "brick": 45, "pipe": 26},
    6: {"name": "ICE WORLD", "sky": 32, "ground": 32, "brick": 45, "pipe": 27},
    7: {"name": "PIPE MAZE", "sky": 13, "ground": 7, "brick": 6, "pipe": 10},
    8: {"name": "DARK LAND", "sky": 13, "ground": 0, "brick": 6, "pipe": 0},
}

# ╔═══════════════════════════════════════════════════════════════════════════════╗
# ║ ENTITY BASE                                                                   ║
# ╚═══════════════════════════════════════════════════════════════════════════════╝
class Entity:
    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = 0.0, 0.0
        self.w, self.h = TILE, TILE
        self.on_ground = False
        self.facing_right = True
        self.active = True
        
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)
        
    def collides(self, other):
        return self.rect().colliderect(other.rect())

# ╔═══════════════════════════════════════════════════════════════════════════════╗
# ║ PLAYER (SMB1 Accurate)                                                        ║
# ╚═══════════════════════════════════════════════════════════════════════════════╝
class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.w = 12
        self.dead = False
        self.death_timer = 0
        self.invincible = 0
        self.victory = False
        self.victory_timer = 0
        self.flag_slide = False
        self.flag_y = 0
        self.jump_held = False
        self.jump_timer = 0
        self.coyote = 0
        self.skidding = False
        self.anim = 0
        self.anim_t = 0
        self.update_size()
        
    def update_size(self):
        self.h = 32 if state.powerup >= 1 else 16
        
    def update(self, keys, tmap, enemies, items, dt):
        if self.dead:
            self.death_timer -= dt
            self.vy += GRAVITY * dt * 60
            self.y += self.vy * dt * 60
            return
        if self.victory:
            self._victory_update(dt)
            return
            
        # Input
        left = keys[K_LEFT] or keys[K_a]
        right = keys[K_RIGHT] or keys[K_d]
        jump = keys[K_SPACE] or keys[K_z] or keys[K_UP] or keys[K_w]
        run = keys[K_LSHIFT] or keys[K_RSHIFT] or keys[K_x]
        
        max_spd = RUN_SPEED if run else WALK_SPEED
        accel = RUN_ACCEL if run else WALK_ACCEL
        
        # Horizontal
        if left and not right:
            if self.vx > 0 and self.on_ground:
                self.skidding = True
                self.vx -= SKID_DECEL * dt * 60
                if self.vx < 0: self.vx, self.skidding = 0, False
            else:
                self.skidding = False
                self.vx -= (accel if self.on_ground else AIR_ACCEL) * dt * 60
            self.facing_right = False
        elif right and not left:
            if self.vx < 0 and self.on_ground:
                self.skidding = True
                self.vx += SKID_DECEL * dt * 60
                if self.vx > 0: self.vx, self.skidding = 0, False
            else:
                self.skidding = False
                self.vx += (accel if self.on_ground else AIR_ACCEL) * dt * 60
            self.facing_right = True
        else:
            self.skidding = False
            if self.on_ground:
                if self.vx > 0:
                    self.vx = max(0, self.vx - DECEL * dt * 60)
                elif self.vx < 0:
                    self.vx = min(0, self.vx + DECEL * dt * 60)
        self.vx = max(-max_spd, min(max_spd, self.vx))
        
        # Coyote time
        if self.on_ground:
            self.coyote = 0.1
        else:
            self.coyote -= dt
            
        # Jump
        if jump:
            if (self.on_ground or self.coyote > 0) and not self.jump_held:
                self.vy = JUMP_RUN if abs(self.vx) > WALK_SPEED * 0.8 else JUMP_WALK
                self.on_ground = False
                self.coyote = 0
                self.jump_held = True
                self.jump_timer = JUMP_HOLD_TIME
            elif self.jump_timer > 0 and self.vy < 0:
                self.jump_timer -= dt
        else:
            self.jump_held = False
            self.jump_timer = 0
            
        # Gravity
        grav = GRAVITY_HOLD if (self.vy < 0 and jump and self.jump_timer > 0) else GRAVITY
        self.vy = min(self.vy + grav * dt * 60, MAX_FALL)
        
        # Move and collide
        self._move(tmap, dt)
        self._animate(dt)
        
        if self.invincible > 0:
            self.invincible -= dt
            
        # Enemies
        for e in enemies:
            if e.active and self.collides(e):
                if self.vy > 0 and self.y + self.h - 8 < e.y + 8:
                    e.stomp(self)
                    self.vy = JUMP_WALK * 0.6
                    state.score += 100
                elif self.invincible <= 0:
                    if isinstance(e, Koopa) and e.shell and not e.shell_moving:
                        e.kick(self.x < e.x)
                    else:
                        self.damage()
                        
        # Items
        for item in items:
            if item.active and item.emerged and self.collides(item):
                item.collect(self)
                
        if self.y > tmap.height + 32:
            self.die()
            
    def _move(self, tmap, dt):
        self.x += self.vx * dt * 60
        for r in tmap.colliders:
            if self.rect().colliderect(r):
                if self.vx > 0: self.x = r.left - self.w
                elif self.vx < 0: self.x = r.right
                self.vx = 0
        if self.x < 0: self.x, self.vx = 0, 0
        
        self.y += self.vy * dt * 60
        self.on_ground = False
        for r in tmap.colliders:
            if self.rect().colliderect(r):
                if self.vy > 0:
                    self.y = r.top - self.h
                    self.vy = 0
                    self.on_ground = True
                elif self.vy < 0:
                    self.y = r.bottom
                    self.vy = 0
                    tmap.hit_block(r.x, r.y, self)
                    
    def _animate(self, dt):
        if self.on_ground:
            if self.skidding:
                self.anim = 4
            elif abs(self.vx) > 0.1:
                self.anim_t += dt * abs(self.vx) * 8
                if self.anim_t > 1:
                    self.anim_t = 0
                    self.anim = (self.anim + 1) % 3
            else:
                self.anim = 0
        else:
            self.anim = 5
            
    def _victory_update(self, dt):
        if self.flag_slide:
            self.y += 2 * dt * 60
            if self.y >= self.flag_y:
                self.y = self.flag_y
                self.flag_slide = False
                self.facing_right = True
                self.victory_timer = 0
        else:
            self.victory_timer += dt
            self.x += 1.5 * dt * 60
            self.anim_t += dt * 4
            if self.anim_t > 0.15:
                self.anim_t = 0
                self.anim = (self.anim + 1) % 3
                
    def damage(self):
        if self.invincible > 0: return
        if state.powerup > 0:
            state.powerup -= 1
            self.update_size()
            self.invincible = 2
        else:
            self.die()
            
    def die(self):
        self.dead = True
        self.death_timer = 3.0
        self.vy = JUMP_WALK
        state.lives -= 1
        
    def start_victory(self, ground_y):
        self.victory = True
        self.flag_slide = True
        self.flag_y = ground_y - self.h
        self.vx = self.vy = 0
        state.score += int(state.time) * 50
        
    def draw(self, surf, cam):
        if self.invincible > 0 and int(self.invincible * 10) % 2 == 0:
            return
        x, y = int(self.x - cam), int(self.y)
        if state.powerup >= 1:
            self._draw_big(surf, x, y)
        else:
            self._draw_small(surf, x, y)
            
    def _draw_small(self, surf, x, y):
        pygame.draw.rect(surf, MARIO_R, (x+2, y, 8, 5))
        pygame.draw.rect(surf, MARIO_S, (x+2, y+5, 8, 5))
        pygame.draw.rect(surf, MARIO_R, (x+1, y+10, 10, 4))
        if self.anim == 5:
            pygame.draw.rect(surf, PAL[23], (x, y+12, 5, 4))
            pygame.draw.rect(surf, PAL[23], (x+7, y+14, 5, 2))
        elif self.anim in [1, 2]:
            pygame.draw.rect(surf, PAL[23], (x, y+14, 5, 2))
            pygame.draw.rect(surf, PAL[23], (x+7, y+12, 5, 4))
        else:
            pygame.draw.rect(surf, PAL[23], (x+1, y+14, 4, 2))
            pygame.draw.rect(surf, PAL[23], (x+7, y+14, 4, 2))
            
    def _draw_big(self, surf, x, y):
        pygame.draw.rect(surf, MARIO_R, (x+1, y, 10, 5))
        pygame.draw.rect(surf, MARIO_S, (x+2, y+5, 8, 6))
        pygame.draw.rect(surf, PAL[23], (x+2, y+3, 3, 2))
        pygame.draw.rect(surf, MARIO_R, (x, y+11, 12, 8))
        pygame.draw.rect(surf, PAL[23], (x+3, y+13, 6, 3))
        pygame.draw.rect(surf, MARIO_S, (x-1, y+13, 3, 6))
        pygame.draw.rect(surf, MARIO_S, (x+10, y+13, 3, 6))
        if self.anim == 5:
            pygame.draw.rect(surf, PAL[23], (x, y+19, 5, 8))
            pygame.draw.rect(surf, PAL[23], (x+7, y+23, 5, 9))
        elif self.anim in [1, 2]:
            pygame.draw.rect(surf, PAL[23], (x, y+19, 5, 13))
            pygame.draw.rect(surf, PAL[23], (x+7, y+19, 5, 11))
        else:
            pygame.draw.rect(surf, PAL[23], (x+1, y+19, 4, 13))
            pygame.draw.rect(surf, PAL[23], (x+7, y+19, 4, 13))

# ╔═══════════════════════════════════════════════════════════════════════════════╗
# ║ ENEMIES                                                                       ║
# ╚═══════════════════════════════════════════════════════════════════════════════╝
class Goomba(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.vx = -GOOMBA_SPEED
        self.anim = 0
        self.anim_t = 0
        self.squished = False
        self.squish_t = 0
        
    def update(self, tmap, dt):
        if not self.active: return
        if self.squished:
            self.squish_t -= dt
            if self.squish_t <= 0: self.active = False
            return
        self.vy = min(self.vy + GRAVITY * dt * 60, MAX_FALL)
        self.x += self.vx * dt * 60
        for r in tmap.colliders:
            if self.rect().colliderect(r):
                self.vx = GOOMBA_SPEED if self.vx < 0 else -GOOMBA_SPEED
        self.y += self.vy * dt * 60
        self.on_ground = False
        for r in tmap.colliders:
            if self.rect().colliderect(r):
                if self.vy > 0:
                    self.y = r.top - self.h
                    self.vy = 0
                    self.on_ground = True
                elif self.vy < 0:
                    self.y = r.bottom
                    self.vy = 0
        self.anim_t += dt
        if self.anim_t > 0.15:
            self.anim_t = 0
            self.anim = 1 - self.anim
        if self.y > tmap.height + 64:
            self.active = False
            
    def stomp(self, player):
        self.squished = True
        self.squish_t = 0.5
        self.h = 8
        self.y += 8
        
    def draw(self, surf, cam):
        if not self.active: return
        x, y = int(self.x - cam), int(self.y)
        if self.squished:
            pygame.draw.ellipse(surf, GOOMBA, (x, y, 16, 8))
        else:
            pygame.draw.ellipse(surf, GOOMBA, (x+1, y+2, 14, 12))
            fy = 2 if self.anim == 0 else -2
            pygame.draw.rect(surf, PAL[0], (x+1, y+12, 5, 4))
            pygame.draw.rect(surf, PAL[0], (x+10, y+12+fy, 5, 4))
            pygame.draw.rect(surf, PAL[32], (x+3, y+4, 3, 4))
            pygame.draw.rect(surf, PAL[32], (x+10, y+4, 3, 4))
            pygame.draw.rect(surf, PAL[0], (x+4, y+5, 2, 2))
            pygame.draw.rect(surf, PAL[0], (x+11, y+5, 2, 2))

class Koopa(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.vx = -KOOPA_SPEED
        self.anim = 0
        self.anim_t = 0
        self.shell = False
        self.shell_moving = False
        self.shell_timer = 0
        
    def update(self, tmap, dt):
        if not self.active: return
        if self.shell and not self.shell_moving:
            self.shell_timer += dt
            if self.shell_timer > 5:
                self.shell = False
                self.shell_timer = 0
                self.vx = -KOOPA_SPEED
        self.vy = min(self.vy + GRAVITY * dt * 60, MAX_FALL)
        if self.shell_moving or not self.shell:
            self.x += self.vx * dt * 60
        for r in tmap.colliders:
            if self.rect().colliderect(r):
                self.vx *= -1
                self.facing_right = self.vx > 0
        if not self.shell and self.on_ground:
            edge_x = self.x + (self.w + 2 if self.vx > 0 else -2)
            edge_r = pygame.Rect(edge_x, self.y + self.h + 2, 4, 4)
            if not any(edge_r.colliderect(r) for r in tmap.colliders):
                self.vx *= -1
                self.facing_right = self.vx > 0
        self.y += self.vy * dt * 60
        self.on_ground = False
        for r in tmap.colliders:
            if self.rect().colliderect(r):
                if self.vy > 0:
                    self.y = r.top - self.h
                    self.vy = 0
                    self.on_ground = True
                elif self.vy < 0:
                    self.y = r.bottom
                    self.vy = 0
        if not self.shell:
            self.anim_t += dt
            if self.anim_t > 0.15:
                self.anim_t = 0
                self.anim = 1 - self.anim
        if self.y > tmap.height + 64:
            self.active = False
            
    def stomp(self, player):
        if self.shell:
            self.kick(player.x < self.x)
        else:
            self.shell = True
            self.shell_moving = False
            self.vx = 0
            self.shell_timer = 0
            self.h = 14
            self.y += 8
            
    def kick(self, kick_right):
        self.shell_moving = True
        self.vx = SHELL_SPEED if kick_right else -SHELL_SPEED
        self.shell_timer = 0
        
    def draw(self, surf, cam):
        if not self.active: return
        x, y = int(self.x - cam), int(self.y)
        if self.shell:
            pygame.draw.ellipse(surf, KOOPA_G, (x, y+2, 16, 12))
            pygame.draw.rect(surf, PAL[40], (x+3, y+5, 10, 6))
            pygame.draw.rect(surf, PAL[0], (x+5, y+4, 2, 8))
            pygame.draw.rect(surf, PAL[0], (x+9, y+4, 2, 8))
        else:
            pygame.draw.ellipse(surf, KOOPA_G, (x+2, y+8, 12, 14))
            pygame.draw.ellipse(surf, PAL[40], (x+3, y+2, 10, 10))
            pygame.draw.rect(surf, PAL[32], (x+5, y+4, 3, 4))
            pygame.draw.rect(surf, PAL[0], (x+6, y+5, 2, 2))
            fy = 2 if self.anim == 0 else 0
            pygame.draw.rect(surf, PAL[40], (x+2, y+20+fy, 5, 4))
            pygame.draw.rect(surf, PAL[40], (x+9, y+20-fy, 5, 4))

class PiranhaPlant(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.base_y = y
        self.timer = random.random() * 3
        self.state = "hiding"
        self.offset = 0
        
    def update(self, tmap, dt):
        self.timer += dt
        if self.state == "hiding":
            if self.timer > 2:
                self.state = "rising"
                self.timer = 0
        elif self.state == "rising":
            self.offset += 30 * dt
            if self.offset >= 24:
                self.offset = 24
                self.state = "showing"
                self.timer = 0
        elif self.state == "showing":
            if self.timer > 1.5:
                self.state = "lowering"
                self.timer = 0
        elif self.state == "lowering":
            self.offset -= 30 * dt
            if self.offset <= 0:
                self.offset = 0
                self.state = "hiding"
                self.timer = 0
        self.y = self.base_y - self.offset
        
    def stomp(self, player):
        pass
        
    def draw(self, surf, cam):
        if self.offset <= 0: return
        x, y = int(self.x - cam), int(self.y)
        pygame.draw.ellipse(surf, PAL[22], (x, y, 16, 12))
        pygame.draw.rect(surf, PAL[32], (x+2, y+8, 3, 4))
        pygame.draw.rect(surf, PAL[32], (x+11, y+8, 3, 4))
        stem_h = int(self.offset) - 12
        if stem_h > 0:
            pygame.draw.rect(surf, PAL[26], (x+5, y+12, 6, stem_h))

def create_enemy(etype, x, y):
    return {"goomba": Goomba, "koopa": Koopa, "piranha": PiranhaPlant}.get(etype, Goomba)(x, y)

# ╔═══════════════════════════════════════════════════════════════════════════════╗
# ║ ITEMS                                                                         ║
# ╚═══════════════════════════════════════════════════════════════════════════════╝
class Mushroom(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.vx = 1.0
        self.emerge_t = 1.0
        self.start_y = y
        self.emerged = False
        
    def update(self, tmap, dt):
        if not self.active: return
        if self.emerge_t > 0:
            self.emerge_t -= dt
            self.y = self.start_y - (1 - self.emerge_t) * TILE
            return
        self.emerged = True
        self.vy = min(self.vy + GRAVITY * dt * 60, MAX_FALL)
        self.x += self.vx * dt * 60
        for r in tmap.colliders:
            if self.rect().colliderect(r):
                self.vx *= -1
        self.y += self.vy * dt * 60
        for r in tmap.colliders:
            if self.rect().colliderect(r):
                if self.vy > 0:
                    self.y = r.top - self.h
                    self.vy = 0
                elif self.vy < 0:
                    self.y = r.bottom
                    self.vy = 0
                    
    def collect(self, player):
        self.active = False
        if state.powerup < 1:
            state.powerup = 1
            player.update_size()
        state.score += 1000
        
    def draw(self, surf, cam):
        if not self.active: return
        x, y = int(self.x - cam), int(self.y)
        pygame.draw.ellipse(surf, PAL[22], (x, y, 16, 12))
        pygame.draw.circle(surf, PAL[32], (x+4, y+4), 3)
        pygame.draw.circle(surf, PAL[32], (x+12, y+4), 3)
        pygame.draw.rect(surf, PAL[54], (x+4, y+10, 8, 6))

class CoinEffect:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.vy = -8
        self.life = 0.4
        self.active = True
        self.anim = 0
        self.anim_t = 0
        
    def update(self, dt):
        self.y += self.vy * dt * 60
        self.vy += 0.5 * dt * 60
        self.anim_t += dt
        if self.anim_t > 0.05:
            self.anim_t = 0
            self.anim = (self.anim + 1) % 4
        self.life -= dt
        if self.life <= 0:
            self.active = False
            
    def draw(self, surf, cam):
        x, y = int(self.x - cam), int(self.y)
        w = [12, 8, 4, 8][self.anim]
        pygame.draw.ellipse(surf, PAL[39], (x + (8 - w//2), y, w, 14))

# ╔═══════════════════════════════════════════════════════════════════════════════╗
# ║ TILEMAP                                                                       ║
# ╚═══════════════════════════════════════════════════════════════════════════════╝
class TileMap:
    def __init__(self, data, effects, items):
        self.effects = effects
        self.items = items
        self.tiles = []
        self.colliders = []
        self.qblocks = {}
        self.bricks = set()
        self.theme_id = data.get("theme", 1)
        self.theme = THEMES.get(self.theme_id, THEMES[1])
        tiles = data["tiles"]
        self.width = data.get("width", len(tiles[0]) * TILE)
        self.height = len(tiles) * TILE
        bc = data.get("block_contents", {})
        
        for y, row in enumerate(tiles):
            for x, c in enumerate(row):
                if c == " ": continue
                px, py = x * TILE, y * TILE
                self.tiles.append((px, py, c))
                if c in "GDBPT?":
                    self.colliders.append(pygame.Rect(px, py, TILE, TILE))
                if c == "?":
                    self.qblocks[(px, py)] = {"hit": False, "contents": bc.get(f"{x},{y}", "coin")}
                elif c == "B":
                    self.bricks.add((px, py))
                    
    def hit_block(self, bx, by, player):
        pos = (bx, by)
        if pos in self.qblocks:
            b = self.qblocks[pos]
            if not b["hit"]:
                b["hit"] = True
                if b["contents"] == "coin":
                    state.add_coin()
                    self.effects.append(CoinEffect(bx + 4, by - TILE))
                elif b["contents"] == "mushroom":
                    self.items.append(Mushroom(bx, by - TILE))
        if pos in self.bricks and state.powerup > 0:
            self.bricks.discard(pos)
            self.tiles = [(tx, ty, c) for tx, ty, c in self.tiles if not (tx == bx and ty == by)]
            self.colliders = [r for r in self.colliders if not (r.x == bx and r.y == by)]
            state.score += 50
            
    def draw(self, surf, cam):
        surf.fill(PAL[self.theme["sky"]])
        # Hills
        for i in range(10):
            hx = (i * 200 - int(cam * 0.3)) % (self.width + 300) - 100
            pygame.draw.polygon(surf, PAL[26], [(hx, HEIGHT - 60), (hx + 50, HEIGHT - 120), (hx + 100, HEIGHT - 60)])
        # Bushes
        for i in range(15):
            bx = (i * 120 - int(cam * 0.5)) % (self.width + 200) - 50
            pygame.draw.ellipse(surf, PAL[26], (bx, HEIGHT - 70, 60, 30))
        # Clouds
        for i in range(8):
            cx = (i * 180 - int(cam * 0.2)) % (self.width + 300) - 100
            cy = 40 + (i % 3) * 30
            pygame.draw.ellipse(surf, PAL[32], (cx, cy, 48, 24))
            pygame.draw.ellipse(surf, PAL[32], (cx + 24, cy - 10, 40, 28))
        # Tiles
        for tx, ty, c in self.tiles:
            dx = tx - cam
            if dx < -TILE or dx > WIDTH + TILE: continue
            self._draw_tile(surf, dx, ty, c, tx, ty)
            
    def _draw_tile(self, surf, dx, dy, c, tx, ty):
        t = self.theme
        if c == "G":
            pygame.draw.rect(surf, PAL[t["ground"]], (dx, dy, TILE, TILE))
            pygame.draw.rect(surf, PAL[26], (dx, dy, TILE, 4))
        elif c == "D":
            pygame.draw.rect(surf, PAL[max(0, t["ground"]-1)], (dx, dy, TILE, TILE))
        elif c == "B":
            if (tx, ty) in self.bricks:
                pygame.draw.rect(surf, PAL[t["brick"]], (dx, dy, TILE, TILE))
                pygame.draw.rect(surf, PAL[0], (dx, dy+7, TILE, 2))
                pygame.draw.rect(surf, PAL[0], (dx+7, dy, 2, TILE))
        elif c == "?":
            if (tx, ty) in self.qblocks and self.qblocks[(tx, ty)]["hit"]:
                pygame.draw.rect(surf, PAL[23], (dx, dy, TILE, TILE))
            else:
                pygame.draw.rect(surf, PAL[39], (dx, dy, TILE, TILE))
                pygame.draw.rect(surf, PAL[40], (dx+2, dy+2, 12, 12))
                pygame.draw.rect(surf, PAL[23], (dx+5, dy+3, 6, 2))
                pygame.draw.rect(surf, PAL[23], (dx+9, dy+5, 2, 3))
                pygame.draw.rect(surf, PAL[23], (dx+5, dy+8, 6, 2))
                pygame.draw.rect(surf, PAL[23], (dx+7, dy+12, 2, 2))
        elif c == "P":
            pygame.draw.rect(surf, PAL[t["ground"]], (dx, dy, TILE, TILE))
            pygame.draw.rect(surf, PAL[0], (dx+2, dy+2, 12, 12))
        elif c == "T":
            pygame.draw.rect(surf, PAL[t["pipe"]], (dx, dy, TILE, TILE))
            pygame.draw.rect(surf, PAL[26], (dx+2, dy, 4, TILE))

# ╔═══════════════════════════════════════════════════════════════════════════════╗
# ║ LEVEL GENERATOR                                                               ║
# ╚═══════════════════════════════════════════════════════════════════════════════╝
def generate_level(world=1, level=1, seed=None):
    if seed is None:
        seed = world * 100 + level
    random.seed(seed)
    
    w = 150 + world * 20
    h = 15
    tiles = [[" "] * w for _ in range(h)]
    gy = h - 2
    
    # Ground
    for x in range(w):
        if random.random() < 0.02 * world and 20 < x < w - 30:
            gap = random.randint(2, 3)
            for gx in range(gap):
                if x + gx < w: pass
            continue
        tiles[gy][x] = "G"
        tiles[gy + 1][x] = "D"
        
    # Fill gaps
    for x in range(w):
        if tiles[gy][x] == " " and x > 0 and x < w - 1:
            if tiles[gy][x-1] == "G" or tiles[gy][x+1] == "G":
                if random.random() > 0.4:
                    tiles[gy][x] = "G"
                    tiles[gy + 1][x] = "D"
                    
    # Platforms
    for _ in range(w // 15):
        px = random.randint(10, w - 20)
        py = random.randint(gy - 7, gy - 3)
        pw = random.randint(3, 6)
        for i in range(pw):
            if 0 <= px + i < w and 0 <= py < h:
                tiles[py][px + i] = "P"
                
    # ? Blocks
    qblocks = []
    for _ in range(w // 12):
        qx = random.randint(10, w - 15)
        qy = random.randint(gy - 6, gy - 3)
        if 0 <= qx < w and 0 <= qy < h:
            tiles[qy][qx] = "?"
            qblocks.append((qx, qy))
            
    # Bricks
    for _ in range(w // 8):
        bx = random.randint(10, w - 15)
        by = random.randint(gy - 5, gy - 3)
        bl = random.randint(1, 4)
        for i in range(bl):
            if 0 <= bx + i < w and 0 <= by < h:
                tiles[by][bx + i] = "B"
                
    # Pipes
    for _ in range(w // 25):
        px = random.randint(15, w - 20)
        ph = random.randint(2, 4)
        for py in range(gy - ph, gy):
            if 0 <= py < h:
                tiles[py][px] = "T"
                tiles[py][px + 1] = "T"
                
    # Stairs at end
    for i in range(8):
        for j in range(i + 1):
            sx = w - 25 + i
            sy = gy - j - 1
            if 0 <= sx < w and 0 <= sy < h:
                tiles[sy][sx] = "B"
                
    # Flagpole
    for i in range(8):
        fx = w - 12
        fy = gy - i - 1
        if 0 <= fy < h:
            tiles[fy][fx] = "P"
            
    tile_strs = ["".join(row) for row in tiles]
    
    # Enemies
    enemies = []
    enemy_types = ["goomba", "goomba", "koopa"]
    for _ in range(8 + world * 2):
        ex = random.randint(20, w - 30) * TILE
        ey = (gy - 1) * TILE
        enemies.append({"x": ex, "y": ey, "type": random.choice(enemy_types)})
        
    # Block contents
    bc = {}
    for qx, qy in qblocks:
        bc[f"{qx},{qy}"] = "mushroom" if random.random() < 0.25 else "coin"
        
    return {
        "tiles": tile_strs,
        "enemies": enemies,
        "player_start": (3 * TILE, (gy - 1) * TILE),
        "flag_pos": ((w - 12) * TILE, (gy - 9) * TILE),
        "width": w * TILE,
        "block_contents": bc,
        "theme": world
    }

# ╔═══════════════════════════════════════════════════════════════════════════════╗
# ║ EDITABLE LEVEL                                                                ║
# ╚═══════════════════════════════════════════════════════════════════════════════╝
class EditableLevel:
    def __init__(self, w=100, h=15, theme=1):
        self.w, self.h, self.theme = w, h, theme
        self.tiles = {}
        self.enemies = []
        self.player_start = (3, h - 3)
        self.flag_pos = (w - 10, h - 10)
        self.block_contents = {}
        self.name = "Custom Level"
        for x in range(w):
            self.tiles[(x, h - 2)] = "G"
            self.tiles[(x, h - 1)] = "D"
            
    def set_tile(self, x, y, tid):
        if 0 <= x < self.w and 0 <= y < self.h:
            if tid in (" ", None):
                self.tiles.pop((x, y), None)
                self.block_contents.pop((x, y), None)
            elif tid == "?M":
                self.tiles[(x, y)] = "?"
                self.block_contents[(x, y)] = "mushroom"
            elif tid == "?C":
                self.tiles[(x, y)] = "?"
                self.block_contents[(x, y)] = "coin"
            else:
                self.tiles[(x, y)] = tid
                if tid == "?":
                    self.block_contents[(x, y)] = "coin"
                    
    def add_enemy(self, x, y, etype):
        self.enemies = [e for e in self.enemies if not (e["x"] == x and e["y"] == y)]
        self.enemies.append({"x": x, "y": y, "type": etype})
        
    def remove_at(self, x, y):
        self.tiles.pop((x, y), None)
        self.block_contents.pop((x, y), None)
        self.enemies = [e for e in self.enemies if not (e["x"] == x and e["y"] == y)]
        
    def to_game(self):
        rows = []
        for y in range(self.h):
            row = ""
            for x in range(self.w):
                row += self.tiles.get((x, y), " ")
            rows.append(row)
        enemies = [{"x": e["x"] * TILE, "y": e["y"] * TILE, "type": e["type"]} for e in self.enemies]
        bc = {f"{x},{y}": c for (x, y), c in self.block_contents.items()}
        return {
            "tiles": rows,
            "enemies": enemies,
            "player_start": (self.player_start[0] * TILE, self.player_start[1] * TILE),
            "flag_pos": (self.flag_pos[0] * TILE, self.flag_pos[1] * TILE),
            "width": self.w * TILE,
            "block_contents": bc,
            "theme": self.theme
        }
        
    def to_code(self):
        """Generate Python code for standalone game"""
        data = self.to_game()
        return f'''LEVEL_DATA = {{
    "tiles": {data["tiles"]!r},
    "enemies": {data["enemies"]!r},
    "player_start": {data["player_start"]!r},
    "flag_pos": {data["flag_pos"]!r},
    "width": {data["width"]},
    "block_contents": {data["block_contents"]!r},
    "theme": {data["theme"]}
}}'''

# ╔═══════════════════════════════════════════════════════════════════════════════╗
# ║ UNDO SYSTEM                                                                   ║
# ╚═══════════════════════════════════════════════════════════════════════════════╝
class Undo:
    def __init__(self, max_h=50):
        self.hist = []
        self.future = []
        self.max = max_h
        
    def save(self, lv):
        s = {"tiles": dict(lv.tiles), "enemies": list(lv.enemies),
             "ps": lv.player_start, "fp": lv.flag_pos, "bc": dict(lv.block_contents)}
        self.hist.append(s)
        self.future.clear()
        if len(self.hist) > self.max:
            self.hist.pop(0)
            
    def undo(self, lv):
        if len(self.hist) > 1:
            self.future.append(self.hist.pop())
            s = self.hist[-1]
            lv.tiles, lv.enemies = dict(s["tiles"]), list(s["enemies"])
            lv.player_start, lv.flag_pos = s["ps"], s["fp"]
            lv.block_contents = dict(s["bc"])
            
    def redo(self, lv):
        if self.future:
            s = self.future.pop()
            self.hist.append(s)
            lv.tiles, lv.enemies = dict(s["tiles"]), list(s["enemies"])
            lv.player_start, lv.flag_pos = s["ps"], s["fp"]
            lv.block_contents = dict(s["bc"])

# ╔═══════════════════════════════════════════════════════════════════════════════╗
# ║ PALETTE                                                                       ║
# ╚═══════════════════════════════════════════════════════════════════════════════╝
PALETTE = {
    "terrain": [("G", "Ground"), ("D", "Dirt"), ("P", "Platform"), ("T", "Pipe"), (" ", "Eraser")],
    "blocks": [("B", "Brick"), ("?", "? Block"), ("?C", "? Coin"), ("?M", "? Mushroom")],
    "enemies": [("goomba", "Goomba"), ("koopa", "Koopa"), ("piranha", "Piranha")],
    "special": [("player", "Player"), ("flag", "Flag")]
}
PAL_CATS = ["terrain", "blocks", "enemies", "special"]

# ╔═══════════════════════════════════════════════════════════════════════════════╗
# ║ GAME ENGINE                                                                   ║
# ╚═══════════════════════════════════════════════════════════════════════════════╝
class KoopaEngine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("AC!'s KOOPA ENGINE 1.1 — Team Flames / Samsoft")
        self.clock = pygame.time.Clock()
        self.running = True
        self.mode = "title"
        self.editor_active = False
        self.paused = False
        
        # Editor
        self.edit_lv = EditableLevel()
        self.undo = Undo()
        self.undo.save(self.edit_lv)
        self.pal_cat = 0
        self.pal_idx = 0
        self.edit_cam = 0
        self.show_grid = True
        self.show_help = False
        
        # Title
        self.title_timer = 0
        self.title_idx = 0
        self.title_opts = ["START GAME", "LEVEL EDITOR", "QUIT"]
        
        # World map
        self.map_world = 1
        
        # Game
        self.effects = []
        self.items = []
        
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()
            pygame.display.flip()
        pygame.quit()
        
    def handle_events(self):
        events = pygame.event.get()
        keys = pygame.key.get_pressed()
        mods = pygame.key.get_mods()
        
        for e in events:
            if e.type == QUIT:
                self.running = False
            elif e.type == KEYDOWN:
                if self.mode == "title":
                    self._title_key(e.key)
                elif self.mode == "map":
                    self._map_key(e.key)
                elif self.mode == "game":
                    self._game_key(e.key, mods)
                elif self.mode == "editor":
                    self._editor_key(e.key, mods)
            elif e.type == MOUSEBUTTONDOWN and self.mode == "editor":
                self._editor_mouse(e)
            elif e.type == MOUSEMOTION and self.mode == "editor":
                if e.buttons[0]:
                    self._editor_place(e.pos)
                elif e.buttons[2]:
                    self._editor_erase(e.pos)
                    
        if self.mode == "editor":
            if keys[K_a] or keys[K_LEFT]:
                self.edit_cam = max(0, self.edit_cam - 8)
            if keys[K_d] or keys[K_RIGHT]:
                self.edit_cam = min(self.edit_lv.w * TILE - WIDTH, self.edit_cam + 8)
                
    def _title_key(self, key):
        if key in (K_UP, K_w):
            self.title_idx = (self.title_idx - 1) % len(self.title_opts)
        elif key in (K_DOWN, K_s):
            self.title_idx = (self.title_idx + 1) % len(self.title_opts)
        elif key in (K_RETURN, K_SPACE):
            if self.title_idx == 0:
                state.reset()
                self.mode = "map"
            elif self.title_idx == 1:
                self.mode = "editor"
            elif self.title_idx == 2:
                self.running = False
        elif key == K_ESCAPE:
            self.running = False
            
    def _map_key(self, key):
        if key in (K_LEFT, K_a):
            self.map_world = max(1, self.map_world - 1)
        elif key in (K_RIGHT, K_d):
            self.map_world = min(8, self.map_world + 1)
        elif key in (K_RETURN, K_SPACE):
            state.world = self.map_world
            state.level = 1
            self._load_level(generate_level(state.world, state.level))
            self.mode = "game"
        elif key == K_ESCAPE:
            self.mode = "title"
            
    def _game_key(self, key, mods):
        if key == K_ESCAPE:
            self.mode = "map"
        elif key == K_RETURN:
            self.paused = not self.paused
        elif key == K_TAB:
            self.mode = "editor"
            
    def _editor_key(self, key, mods):
        if key == K_ESCAPE:
            self.mode = "title"
        elif key == K_TAB:
            self._load_level(self.edit_lv.to_game())
            self.mode = "game"
            state.reset()
        elif key == K_g:
            self.show_grid = not self.show_grid
        elif key == K_h:
            self.show_help = not self.show_help
        elif key == K_t:
            self.edit_lv.theme = (self.edit_lv.theme % 8) + 1
        elif key == K_e:
            self._load_level(self.edit_lv.to_game())
            self.mode = "game"
            state.reset()
        elif key == K_n and (mods & KMOD_CTRL):
            self.edit_lv = EditableLevel()
            self.undo = Undo()
            self.undo.save(self.edit_lv)
        elif key == K_z and (mods & KMOD_CTRL):
            self.undo.undo(self.edit_lv)
        elif key == K_y and (mods & KMOD_CTRL):
            self.undo.redo(self.edit_lv)
        elif key == K_s and (mods & KMOD_CTRL):
            self._save_level()
        elif key == K_e and (mods & KMOD_CTRL):
            self._export_game()
        elif key in (K_1, K_2, K_3, K_4):
            self.pal_cat = key - K_1
            self.pal_idx = 0
            
    def _editor_mouse(self, e):
        if e.button == 1:
            self._editor_place(e.pos)
        elif e.button == 3:
            self._editor_erase(e.pos)
        elif e.button == 4:
            self.pal_idx = max(0, self.pal_idx - 1)
        elif e.button == 5:
            cat = PAL_CATS[self.pal_cat]
            self.pal_idx = min(len(PALETTE[cat]) - 1, self.pal_idx + 1)
            
    def _editor_place(self, pos):
        tx = int((pos[0] + self.edit_cam) // TILE)
        ty = int(pos[1] // TILE)
        cat = PAL_CATS[self.pal_cat]
        item = PALETTE[cat][self.pal_idx][0]
        if cat in ("terrain", "blocks"):
            if self.edit_lv.tiles.get((tx, ty)) != item:
                self.edit_lv.set_tile(tx, ty, item)
                self.undo.save(self.edit_lv)
        elif cat == "enemies":
            self.edit_lv.add_enemy(tx, ty, item)
            self.undo.save(self.edit_lv)
        elif cat == "special":
            if item == "player":
                self.edit_lv.player_start = (tx, ty)
            elif item == "flag":
                self.edit_lv.flag_pos = (tx, ty)
            self.undo.save(self.edit_lv)
            
    def _editor_erase(self, pos):
        tx = int((pos[0] + self.edit_cam) // TILE)
        ty = int(pos[1] // TILE)
        self.edit_lv.remove_at(tx, ty)
        self.undo.save(self.edit_lv)
        
    def _save_level(self):
        os.makedirs("levels", exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        fn = f"levels/level_{ts}.kpl"
        data = self.edit_lv.to_game()
        with open(fn, "w") as f:
            f.write(repr(data))
        print(f"Saved: {fn}")
        
    def _export_game(self):
        os.makedirs("games", exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        fn = f"games/koopa_game_{ts}.py"
        
        # Read this file
        with open(__file__, "r") as f:
            engine = f.read()
            
        # Find the level data section and replace
        level_code = self.edit_lv.to_code()
        
        # Create standalone game
        game_code = f'''#!/usr/bin/env python3
"""
KOOPA ENGINE GAME
Exported: {ts}
Created with AC!'s Koopa Engine 1.1
Team Flames / Samsoft / Flames Co.
"""

{level_code}

# Engine code below - paste from koopa_engine.py or import it
# To run: python3 {os.path.basename(fn)}

import pygame
import sys
import math
import random
from pygame.locals import *

SCALE = 2
TILE = 16
WIDTH = 256 * SCALE
HEIGHT = 240 * SCALE
FPS = 60

GRAVITY = 0.4375
GRAVITY_HOLD = 0.1875
MAX_FALL = 4.5
JUMP_WALK = -4.0
JUMP_RUN = -5.0
JUMP_HOLD_TIME = 0.25
WALK_SPEED = 1.3
RUN_SPEED = 2.5
WALK_ACCEL = 0.15
RUN_ACCEL = 0.2
DECEL = 0.1
SKID_DECEL = 0.25
AIR_ACCEL = 0.1
GOOMBA_SPEED = 0.5
KOOPA_SPEED = 0.5
SHELL_SPEED = 4.0

PAL = [
    (84,84,84),(0,30,116),(8,16,144),(48,0,136),(68,0,100),(92,0,48),(84,4,0),(60,24,0),
    (32,42,0),(8,58,0),(0,64,0),(0,60,0),(0,50,60),(0,0,0),(0,0,0),(0,0,0),
    (152,150,152),(8,76,196),(48,50,236),(92,30,228),(136,20,176),(160,20,100),(152,34,32),(120,60,0),
    (84,90,0),(40,114,0),(8,124,0),(0,118,40),(0,102,120),(0,0,0),(0,0,0),(0,0,0),
    (236,238,236),(76,154,236),(120,124,236),(176,98,236),(228,84,236),(236,88,180),(236,106,100),(212,136,32),
    (160,170,0),(116,196,0),(76,208,32),(56,204,108),(56,180,204),(60,60,60),(0,0,0),(0,0,0),
    (236,238,236),(168,204,236),(188,188,236),(212,178,236),(236,174,236),(236,174,212),(236,180,176),(228,196,144),
    (204,210,120),(180,222,120),(168,226,144),(152,226,180),(160,214,228),(160,162,160),(0,0,0),(0,0,0)
]

THEMES = {{
    1: {{"name": "GRASS LAND", "sky": 34, "ground": 23, "brick": 22, "pipe": 26}},
    2: {{"name": "DESERT HILL", "sky": 39, "ground": 23, "brick": 22, "pipe": 26}},
    3: {{"name": "OCEAN SIDE", "sky": 34, "ground": 27, "brick": 17, "pipe": 26}},
    4: {{"name": "GIANT LAND", "sky": 24, "ground": 23, "brick": 22, "pipe": 10}},
    5: {{"name": "SKY WORLD", "sky": 34, "ground": 32, "brick": 45, "pipe": 26}},
    6: {{"name": "ICE WORLD", "sky": 32, "ground": 32, "brick": 45, "pipe": 27}},
    7: {{"name": "PIPE MAZE", "sky": 13, "ground": 7, "brick": 6, "pipe": 10}},
    8: {{"name": "DARK LAND", "sky": 13, "ground": 0, "brick": 6, "pipe": 0}},
}}

class GameState:
    def __init__(self):
        self.score = 0
        self.coins = 0
        self.lives = 3
        self.time = 400
        self.powerup = 0
    def add_coin(self):
        self.coins += 1
        self.score += 200
        if self.coins >= 100:
            self.coins = 0
            self.lives += 1

state = GameState()

class Entity:
    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = 0.0, 0.0
        self.w, self.h = TILE, TILE
        self.on_ground = False
        self.active = True
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)
    def collides(self, other):
        return self.rect().colliderect(other.rect())

class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.w = 12
        self.dead = False
        self.death_timer = 0
        self.invincible = 0
        self.victory = False
        self.jump_held = False
        self.jump_timer = 0
        self.coyote = 0
        self.anim = 0
        self.h = 16 if state.powerup == 0 else 32
        
    def update(self, keys, tmap, enemies, items, dt):
        if self.dead:
            self.death_timer -= dt
            self.vy += GRAVITY * dt * 60
            self.y += self.vy * dt * 60
            return
        if self.victory:
            self.x += 1.5 * dt * 60
            return
        left = keys[K_LEFT] or keys[K_a]
        right = keys[K_RIGHT] or keys[K_d]
        jump = keys[K_SPACE] or keys[K_z]
        run = keys[K_LSHIFT] or keys[K_x]
        max_spd = RUN_SPEED if run else WALK_SPEED
        accel = RUN_ACCEL if run else WALK_ACCEL
        if left: self.vx -= accel * dt * 60
        elif right: self.vx += accel * dt * 60
        else:
            if self.vx > 0: self.vx = max(0, self.vx - DECEL * dt * 60)
            elif self.vx < 0: self.vx = min(0, self.vx + DECEL * dt * 60)
        self.vx = max(-max_spd, min(max_spd, self.vx))
        if self.on_ground: self.coyote = 0.1
        else: self.coyote -= dt
        if jump:
            if (self.on_ground or self.coyote > 0) and not self.jump_held:
                self.vy = JUMP_RUN if abs(self.vx) > WALK_SPEED else JUMP_WALK
                self.on_ground = False
                self.coyote = 0
                self.jump_held = True
                self.jump_timer = JUMP_HOLD_TIME
            elif self.jump_timer > 0 and self.vy < 0:
                self.jump_timer -= dt
        else:
            self.jump_held = False
            self.jump_timer = 0
        grav = GRAVITY_HOLD if (self.vy < 0 and jump and self.jump_timer > 0) else GRAVITY
        self.vy = min(self.vy + grav * dt * 60, MAX_FALL)
        self.x += self.vx * dt * 60
        for r in tmap.colliders:
            if self.rect().colliderect(r):
                if self.vx > 0: self.x = r.left - self.w
                elif self.vx < 0: self.x = r.right
        if self.x < 0: self.x = 0
        self.y += self.vy * dt * 60
        self.on_ground = False
        for r in tmap.colliders:
            if self.rect().colliderect(r):
                if self.vy > 0:
                    self.y = r.top - self.h
                    self.vy = 0
                    self.on_ground = True
                elif self.vy < 0:
                    self.y = r.bottom
                    self.vy = 0
                    tmap.hit_block(r.x, r.y)
        if self.invincible > 0: self.invincible -= dt
        for e in enemies:
            if e.active and self.collides(e):
                if self.vy > 0 and self.y + self.h - 8 < e.y + 8:
                    e.stomp()
                    self.vy = JUMP_WALK * 0.6
                    state.score += 100
                elif self.invincible <= 0:
                    if state.powerup > 0:
                        state.powerup -= 1
                        self.h = 16
                        self.invincible = 2
                    else:
                        self.dead = True
                        self.death_timer = 3
                        self.vy = JUMP_WALK
                        state.lives -= 1
        for item in items:
            if item.active and item.emerged and self.collides(item):
                item.active = False
                if state.powerup < 1:
                    state.powerup = 1
                    self.h = 32
                state.score += 1000
        if self.y > tmap.height + 32:
            self.dead = True
            self.death_timer = 3
            self.vy = JUMP_WALK
            state.lives -= 1
            
    def draw(self, surf, cam):
        if self.invincible > 0 and int(self.invincible * 10) % 2 == 0: return
        x, y = int(self.x - cam), int(self.y)
        pygame.draw.rect(surf, PAL[22], (x+2, y, 8, 5))
        pygame.draw.rect(surf, PAL[54], (x+2, y+5, 8, 5))
        pygame.draw.rect(surf, PAL[22], (x+1, y+10, 10, self.h - 10))

class Goomba(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.vx = -GOOMBA_SPEED
        self.squished = False
        self.squish_t = 0
    def update(self, tmap, dt):
        if not self.active: return
        if self.squished:
            self.squish_t -= dt
            if self.squish_t <= 0: self.active = False
            return
        self.vy = min(self.vy + GRAVITY * dt * 60, MAX_FALL)
        self.x += self.vx * dt * 60
        for r in tmap.colliders:
            if self.rect().colliderect(r): self.vx *= -1
        self.y += self.vy * dt * 60
        for r in tmap.colliders:
            if self.rect().colliderect(r) and self.vy > 0:
                self.y = r.top - self.h
                self.vy = 0
    def stomp(self):
        self.squished = True
        self.squish_t = 0.5
        self.h = 8
        self.y += 8
    def draw(self, surf, cam):
        if not self.active: return
        x, y = int(self.x - cam), int(self.y)
        pygame.draw.ellipse(surf, PAL[23], (x+1, y+2 if not self.squished else y, 14, 8 if self.squished else 12))

class Koopa(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.vx = -KOOPA_SPEED
        self.shell = False
        self.shell_moving = False
    def update(self, tmap, dt):
        if not self.active: return
        self.vy = min(self.vy + GRAVITY * dt * 60, MAX_FALL)
        if self.shell_moving or not self.shell:
            self.x += self.vx * dt * 60
        for r in tmap.colliders:
            if self.rect().colliderect(r): self.vx *= -1
        self.y += self.vy * dt * 60
        for r in tmap.colliders:
            if self.rect().colliderect(r) and self.vy > 0:
                self.y = r.top - self.h
                self.vy = 0
    def stomp(self):
        if self.shell:
            self.shell_moving = True
            self.vx = SHELL_SPEED
        else:
            self.shell = True
            self.vx = 0
            self.h = 14
            self.y += 8
    def draw(self, surf, cam):
        if not self.active: return
        x, y = int(self.x - cam), int(self.y)
        pygame.draw.ellipse(surf, PAL[26], (x+2, y+4, 12, 12))

class Mushroom(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.vx = 1.0
        self.emerge_t = 1.0
        self.start_y = y
        self.emerged = False
    def update(self, tmap, dt):
        if not self.active: return
        if self.emerge_t > 0:
            self.emerge_t -= dt
            self.y = self.start_y - (1 - self.emerge_t) * TILE
            return
        self.emerged = True
        self.vy = min(self.vy + GRAVITY * dt * 60, MAX_FALL)
        self.x += self.vx * dt * 60
        for r in tmap.colliders:
            if self.rect().colliderect(r): self.vx *= -1
        self.y += self.vy * dt * 60
        for r in tmap.colliders:
            if self.rect().colliderect(r) and self.vy > 0:
                self.y = r.top - self.h
                self.vy = 0
    def draw(self, surf, cam):
        if not self.active: return
        x, y = int(self.x - cam), int(self.y)
        pygame.draw.ellipse(surf, PAL[22], (x, y, 16, 12))

class CoinEffect:
    def __init__(self, x, y):
        self.x, self.y, self.vy = x, y, -8
        self.life = 0.4
        self.active = True
    def update(self, dt):
        self.y += self.vy * dt * 60
        self.vy += 0.5 * dt * 60
        self.life -= dt
        if self.life <= 0: self.active = False
    def draw(self, surf, cam):
        pygame.draw.ellipse(surf, PAL[39], (int(self.x - cam), int(self.y), 12, 14))

class TileMap:
    def __init__(self, data, effects, items):
        self.effects, self.items = effects, items
        self.tiles, self.colliders = [], []
        self.qblocks, self.bricks = {{}}, set()
        self.theme = THEMES.get(data.get("theme", 1), THEMES[1])
        tiles = data["tiles"]
        self.width = data.get("width", len(tiles[0]) * TILE)
        self.height = len(tiles) * TILE
        bc = data.get("block_contents", {{}})
        for y, row in enumerate(tiles):
            for x, c in enumerate(row):
                if c == " ": continue
                px, py = x * TILE, y * TILE
                self.tiles.append((px, py, c))
                if c in "GDBPT?":
                    self.colliders.append(pygame.Rect(px, py, TILE, TILE))
                if c == "?":
                    self.qblocks[(px, py)] = {{"hit": False, "contents": bc.get(f"{{x}},{{y}}", "coin")}}
                elif c == "B":
                    self.bricks.add((px, py))
    def hit_block(self, bx, by):
        if (bx, by) in self.qblocks:
            b = self.qblocks[(bx, by)]
            if not b["hit"]:
                b["hit"] = True
                if b["contents"] == "coin":
                    state.add_coin()
                    self.effects.append(CoinEffect(bx + 4, by - TILE))
                elif b["contents"] == "mushroom":
                    self.items.append(Mushroom(bx, by - TILE))
        if (bx, by) in self.bricks and state.powerup > 0:
            self.bricks.discard((bx, by))
            self.tiles = [(tx, ty, c) for tx, ty, c in self.tiles if not (tx == bx and ty == by)]
            self.colliders = [r for r in self.colliders if not (r.x == bx and r.y == by)]
    def draw(self, surf, cam):
        surf.fill(PAL[self.theme["sky"]])
        for tx, ty, c in self.tiles:
            dx = tx - cam
            if dx < -TILE or dx > WIDTH + TILE: continue
            if c == "G":
                pygame.draw.rect(surf, PAL[self.theme["ground"]], (dx, ty, TILE, TILE))
                pygame.draw.rect(surf, PAL[26], (dx, ty, TILE, 4))
            elif c == "D":
                pygame.draw.rect(surf, PAL[max(0, self.theme["ground"]-1)], (dx, ty, TILE, TILE))
            elif c == "B":
                if (tx, ty) in self.bricks:
                    pygame.draw.rect(surf, PAL[self.theme["brick"]], (dx, ty, TILE, TILE))
            elif c == "?":
                if (tx, ty) in self.qblocks and self.qblocks[(tx, ty)]["hit"]:
                    pygame.draw.rect(surf, PAL[23], (dx, ty, TILE, TILE))
                else:
                    pygame.draw.rect(surf, PAL[39], (dx, ty, TILE, TILE))
            elif c == "P":
                pygame.draw.rect(surf, PAL[self.theme["ground"]], (dx, ty, TILE, TILE))
            elif c == "T":
                pygame.draw.rect(surf, PAL[self.theme["pipe"]], (dx, ty, TILE, TILE))

def create_enemy(etype, x, y):
    if etype == "koopa": return Koopa(x, y)
    return Goomba(x, y)

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("KOOPA ENGINE GAME")
    clock = pygame.time.Clock()
    effects, items = [], []
    tmap = TileMap(LEVEL_DATA, effects, items)
    ps = LEVEL_DATA["player_start"]
    player = Player(ps[0], ps[1])
    enemies = [create_enemy(e["type"], e["x"], e["y"]) for e in LEVEL_DATA.get("enemies", [])]
    flag_pos = LEVEL_DATA.get("flag_pos", (100 * TILE, 5 * TILE))
    cam = 0
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        for e in pygame.event.get():
            if e.type == QUIT: running = False
            elif e.type == KEYDOWN and e.key == K_ESCAPE: running = False
        keys = pygame.key.get_pressed()
        state.time -= dt
        if state.time <= 0 and not player.dead:
            player.dead = True
            player.death_timer = 3
            player.vy = JUMP_WALK
            state.lives -= 1
        player.update(keys, tmap, enemies, items, dt)
        if player.dead and player.death_timer <= 0:
            if state.lives <= 0: running = False
            else:
                state.time = 400
                player = Player(ps[0], ps[1])
                enemies = [create_enemy(e["type"], e["x"], e["y"]) for e in LEVEL_DATA.get("enemies", [])]
        for e in enemies:
            if e.active: e.update(tmap, dt)
        for item in items:
            if item.active: item.update(tmap, dt)
        for eff in effects[:]:
            eff.update(dt)
            if not eff.active: effects.remove(eff)
        cam += (player.x - WIDTH // 3 - cam) * 0.1
        cam = max(0, min(cam, tmap.width - WIDTH))
        if not player.victory and player.x >= flag_pos[0] - 20:
            player.victory = True
            state.score += int(state.time) * 50
        tmap.draw(screen, cam)
        fx = flag_pos[0] - cam
        fy = flag_pos[1]
        pygame.draw.rect(screen, PAL[0], (fx + 6, fy, 4, TILE * 9))
        pygame.draw.polygon(screen, PAL[22], [(fx + 10, fy + 4), (fx + 34, fy + 16), (fx + 10, fy + 28)])
        for e in enemies: e.draw(screen, cam)
        for item in items: item.draw(screen, cam)
        for eff in effects: eff.draw(screen, cam)
        player.draw(screen, cam)
        font = pygame.font.SysFont(None, 24)
        screen.blit(font.render(f"SCORE: {{state.score:06d}}", True, PAL[32]), (10, 10))
        screen.blit(font.render(f"COINS: {{state.coins:02d}}", True, PAL[32]), (200, 10))
        screen.blit(font.render(f"TIME: {{int(max(0, state.time)):03d}}", True, PAL[32]), (350, 10))
        screen.blit(font.render(f"LIVES: {{state.lives}}", True, PAL[32]), (480, 10))
        if player.victory:
            screen.blit(font.render("LEVEL COMPLETE!", True, PAL[32]), (WIDTH//2 - 80, HEIGHT//2))
        pygame.display.flip()
        if player.victory and player.x > tmap.width: running = False
    pygame.quit()
    print(f"Final Score: {{state.score}}")

if __name__ == "__main__":
    main()
'''
        
        with open(fn, "w") as f:
            f.write(game_code)
        print(f"Exported: {fn}")
        print(f"Run with: python3 {fn}")
        
    def _load_level(self, data):
        self.effects = []
        self.items = []
        self.tmap = TileMap(data, self.effects, self.items)
        ps = data["player_start"]
        self.player = Player(ps[0], ps[1])
        self.enemies = [create_enemy(e["type"], e["x"], e["y"]) for e in data.get("enemies", [])]
        self.cam = 0
        state.time = 400
        self.flag_pos = data.get("flag_pos", (100 * TILE, 5 * TILE))
        self.complete = False
        self.complete_t = 0
        
    def update(self, dt):
        self.title_timer += dt
        
        if self.mode == "game" and not self.paused:
            keys = pygame.key.get_pressed()
            if not self.complete:
                state.time -= dt
                if state.time <= 0:
                    self.player.die()
            self.player.update(keys, self.tmap, self.enemies, self.items, dt)
            if self.player.dead and self.player.death_timer <= 0:
                if state.lives <= 0:
                    state.reset()
                    self.mode = "title"
                else:
                    self._load_level(generate_level(state.world, state.level))
                return
            for e in self.enemies:
                if e.active:
                    e.update(self.tmap, dt)
            for item in self.items:
                if item.active:
                    item.update(self.tmap, dt)
            for eff in self.effects[:]:
                eff.update(dt)
                if not eff.active:
                    self.effects.remove(eff)
            self.cam += (self.player.x - WIDTH // 3 - self.cam) * 0.1
            self.cam = max(0, min(self.cam, self.tmap.width - WIDTH))
            if not self.complete and self.player.x >= self.flag_pos[0] - 20:
                self.complete = True
                gy = (len(self.tmap.tiles) // (self.tmap.width // TILE) + 13) * TILE
                self.player.start_victory(gy)
            if self.complete and self.player.victory and not self.player.flag_slide:
                self.complete_t += dt
                if self.complete_t > 4:
                    state.level += 1
                    if state.level > 4:
                        state.level = 1
                        state.world = min(8, state.world + 1)
                    self._load_level(generate_level(state.world, state.level))
                    
    def draw(self):
        if self.mode == "title":
            self._draw_title()
        elif self.mode == "map":
            self._draw_map()
        elif self.mode == "game":
            self._draw_game()
        elif self.mode == "editor":
            self._draw_editor()
            
    def _draw_title(self):
        self.screen.fill(PAL[34])
        
        # Animated clouds
        for i in range(8):
            cx = (i * 80 + int(self.title_timer * 20)) % (WIDTH + 60) - 30
            cy = HEIGHT - 100 + (i % 3) * 30
            pygame.draw.ellipse(self.screen, PAL[32], (cx, cy, 50, 30))
            
        # Hills
        for i in range(5):
            hx = i * 150 - 50
            pygame.draw.polygon(self.screen, PAL[26], [(hx, HEIGHT), (hx + 75, HEIGHT - 80), (hx + 150, HEIGHT)])
            
        # Logo
        font_big = pygame.font.SysFont("arial", 48, bold=True)
        font_med = pygame.font.SysFont("arial", 24)
        font_sm = pygame.font.SysFont("arial", 18)
        
        # Shadow
        title = font_big.render("KOOPA ENGINE", True, PAL[0])
        self.screen.blit(title, (WIDTH//2 - title.get_width()//2 + 3, 60 + 3))
        # Title
        title = font_big.render("KOOPA ENGINE", True, PAL[22])
        self.screen.blit(title, (WIDTH//2 - title.get_width()//2, 60))
        
        # Version
        ver = font_sm.render("Version 1.1 — SMB1 Accurate + Lunar Magic Editor", True, PAL[26])
        self.screen.blit(ver, (WIDTH//2 - ver.get_width()//2, 115))
        
        # Credits
        cred = font_sm.render("Team Flames / Samsoft / Flames Co.", True, PAL[45])
        self.screen.blit(cred, (WIDTH//2 - cred.get_width()//2, 140))
        
        # Menu
        for i, opt in enumerate(self.title_opts):
            color = PAL[39] if i == self.title_idx else PAL[45]
            text = font_med.render(opt, True, color)
            y = 200 + i * 45
            self.screen.blit(text, (WIDTH//2 - text.get_width()//2, y))
            if i == self.title_idx:
                marker = "►" if int(self.title_timer * 4) % 2 == 0 else "▸"
                m = font_med.render(marker, True, PAL[22])
                self.screen.blit(m, (WIDTH//2 - text.get_width()//2 - 30, y))
                
        # Controls
        ctrl = font_sm.render("Arrows: Navigate | Enter: Select", True, PAL[45])
        self.screen.blit(ctrl, (WIDTH//2 - ctrl.get_width()//2, HEIGHT - 40))
        
    def _draw_map(self):
        theme = THEMES.get(self.map_world, THEMES[1])
        self.screen.fill(PAL[theme["sky"]])
        
        font_big = pygame.font.SysFont("arial", 36, bold=True)
        font_med = pygame.font.SysFont("arial", 24)
        font_sm = pygame.font.SysFont("arial", 18)
        
        # World name
        title = font_big.render(f"WORLD {self.map_world}", True, PAL[32])
        self.screen.blit(title, (WIDTH//2 - title.get_width()//2, 40))
        
        name = font_med.render(theme["name"], True, PAL[39])
        self.screen.blit(name, (WIDTH//2 - name.get_width()//2, 85))
        
        # World boxes
        box_sz = 55
        start_x = WIDTH//2 - (4 * box_sz + 3 * 12) // 2
        
        for i in range(8):
            row = i // 4
            col = i % 4
            x = start_x + col * (box_sz + 12)
            y = 140 + row * (box_sz + 25)
            
            wt = THEMES[i + 1]
            color = PAL[wt["ground"]] if i + 1 == self.map_world else PAL[45]
            pygame.draw.rect(self.screen, color, (x, y, box_sz, box_sz))
            pygame.draw.rect(self.screen, PAL[0], (x, y, box_sz, box_sz), 2)
            
            num = font_med.render(str(i + 1), True, PAL[32])
            self.screen.blit(num, (x + box_sz//2 - num.get_width()//2, y + box_sz//2 - num.get_height()//2))
            
            if i + 1 == self.map_world:
                pygame.draw.polygon(self.screen, PAL[22], [
                    (x + box_sz//2, y + box_sz + 8),
                    (x + box_sz//2 - 10, y + box_sz + 18),
                    (x + box_sz//2 + 10, y + box_sz + 18)
                ])
                
        # Stats
        stats = f"Lives: {state.lives}   Score: {state.score:06d}   Coins: {state.coins:02d}"
        st = font_sm.render(stats, True, PAL[32])
        self.screen.blit(st, (WIDTH//2 - st.get_width()//2, HEIGHT - 70))
        
        # Instructions
        inst = font_sm.render("← → Select | ENTER Start | ESC Back", True, PAL[45])
        self.screen.blit(inst, (WIDTH//2 - inst.get_width()//2, HEIGHT - 35))
        
    def _draw_game(self):
        self.tmap.draw(self.screen, self.cam)
        
        # Flag
        fx = self.flag_pos[0] - self.cam
        fy = self.flag_pos[1]
        pygame.draw.rect(self.screen, PAL[0], (fx + 6, fy, 4, TILE * 9))
        pygame.draw.circle(self.screen, PAL[26], (int(fx + 8), int(fy)), 6)
        pygame.draw.polygon(self.screen, PAL[22], [(fx + 10, fy + 4), (fx + 34, fy + 16), (fx + 10, fy + 28)])
        
        for e in self.enemies:
            e.draw(self.screen, self.cam)
        for item in self.items:
            item.draw(self.screen, self.cam)
        for eff in self.effects:
            eff.draw(self.screen, self.cam)
        self.player.draw(self.screen, self.cam)
        
        # HUD
        font = pygame.font.SysFont("arial", 16)
        self.screen.blit(font.render(f"WORLD {state.world}-{state.level}", True, PAL[32]), (10, 10))
        self.screen.blit(font.render(f"SCORE: {state.score:06d}", True, PAL[32]), (130, 10))
        pygame.draw.ellipse(self.screen, PAL[39], (280, 8, 10, 14))
        self.screen.blit(font.render(f"x{state.coins:02d}", True, PAL[32]), (292, 10))
        self.screen.blit(font.render(f"TIME: {int(max(0, state.time)):03d}", True, PAL[32]), (370, 10))
        self.screen.blit(font.render(f"♥x{state.lives}", True, PAL[22]), (470, 10))
        
        hint = font.render("TAB: Editor", True, PAL[45])
        self.screen.blit(hint, (WIDTH - 90, HEIGHT - 20))
        
        if self.paused:
            ov = pygame.Surface((WIDTH, HEIGHT))
            ov.fill((0, 0, 0))
            ov.set_alpha(150)
            self.screen.blit(ov, (0, 0))
            font_b = pygame.font.SysFont("arial", 32, bold=True)
            t = font_b.render("PAUSED", True, PAL[32])
            self.screen.blit(t, (WIDTH//2 - t.get_width()//2, HEIGHT//2 - 16))
            
    def _draw_editor(self):
        theme = THEMES.get(self.edit_lv.theme, THEMES[1])
        self.screen.fill(PAL[theme["sky"]])
        
        # Grid
        if self.show_grid:
            for x in range(0, WIDTH + TILE, TILE):
                gx = x - (self.edit_cam % TILE)
                pygame.draw.line(self.screen, (80, 80, 80), (gx, 0), (gx, HEIGHT - 60))
            for y in range(0, HEIGHT - 60, TILE):
                pygame.draw.line(self.screen, (80, 80, 80), (0, y), (WIDTH, y))
                
        # Tiles
        for (tx, ty), c in self.edit_lv.tiles.items():
            dx = tx * TILE - self.edit_cam
            dy = ty * TILE
            if -TILE <= dx <= WIDTH + TILE and dy < HEIGHT - 60:
                self._draw_ed_tile(dx, dy, c, theme)
                
        # Enemies
        for e in self.edit_lv.enemies:
            ex = e["x"] * TILE - self.edit_cam
            ey = e["y"] * TILE
            if -TILE <= ex <= WIDTH + TILE:
                self._draw_ed_enemy(ex, ey, e["type"])
                
        # Player start
        px = self.edit_lv.player_start[0] * TILE - self.edit_cam
        py = self.edit_lv.player_start[1] * TILE
        pygame.draw.rect(self.screen, PAL[22], (px + 2, py, 12, 16))
        pygame.draw.rect(self.screen, PAL[54], (px + 4, py + 4, 8, 6))
        
        # Flag
        fx = self.edit_lv.flag_pos[0] * TILE - self.edit_cam
        fy = self.edit_lv.flag_pos[1] * TILE
        pygame.draw.rect(self.screen, PAL[0], (fx + 6, fy, 4, 32))
        pygame.draw.polygon(self.screen, PAL[22], [(fx + 10, fy + 4), (fx + 26, fy + 12), (fx + 10, fy + 20)])
        
        # Palette bar
        self._draw_palette()
        
        # Help
        if self.show_help:
            self._draw_help()
            
    def _draw_ed_tile(self, dx, dy, c, t):
        if c == "G":
            pygame.draw.rect(self.screen, PAL[t["ground"]], (dx, dy, TILE, TILE))
            pygame.draw.rect(self.screen, PAL[26], (dx, dy, TILE, 4))
        elif c == "D":
            pygame.draw.rect(self.screen, PAL[max(0, t["ground"]-1)], (dx, dy, TILE, TILE))
        elif c == "B":
            pygame.draw.rect(self.screen, PAL[t["brick"]], (dx, dy, TILE, TILE))
            pygame.draw.rect(self.screen, PAL[0], (dx, dy+7, TILE, 2))
            pygame.draw.rect(self.screen, PAL[0], (dx+7, dy, 2, TILE))
        elif c == "?":
            pygame.draw.rect(self.screen, PAL[39], (dx, dy, TILE, TILE))
            pygame.draw.rect(self.screen, PAL[40], (dx+4, dy+4, 8, 8))
        elif c == "P":
            pygame.draw.rect(self.screen, PAL[t["ground"]], (dx, dy, TILE, TILE))
            pygame.draw.rect(self.screen, PAL[0], (dx+2, dy+2, 12, 12))
        elif c == "T":
            pygame.draw.rect(self.screen, PAL[t["pipe"]], (dx, dy, TILE, TILE))
            pygame.draw.rect(self.screen, PAL[26], (dx+2, dy, 4, TILE))
            
    def _draw_ed_enemy(self, ex, ey, etype):
        if etype == "goomba":
            pygame.draw.ellipse(self.screen, GOOMBA, (ex+1, ey+2, 14, 12))
        elif etype == "koopa":
            pygame.draw.ellipse(self.screen, KOOPA_G, (ex+2, ey+4, 12, 12))
            pygame.draw.ellipse(self.screen, PAL[40], (ex+4, ey, 8, 8))
        elif etype == "piranha":
            pygame.draw.ellipse(self.screen, PAL[22], (ex, ey+4, 16, 12))
            
    def _draw_palette(self):
        pygame.draw.rect(self.screen, PAL[0], (0, HEIGHT - 60, WIDTH, 60))
        
        font = pygame.font.SysFont("arial", 14)
        cat = PAL_CATS[self.pal_cat]
        
        # Category tabs
        for i, c in enumerate(PAL_CATS):
            color = PAL[32] if i == self.pal_cat else PAL[45]
            text = font.render(c.upper(), True, color)
            self.screen.blit(text, (10 + i * 100, HEIGHT - 58))
            
        # Items
        items = PALETTE[cat]
        for i, (item_id, name) in enumerate(items):
            x = 10 + i * 55
            y = HEIGHT - 38
            if i == self.pal_idx:
                pygame.draw.rect(self.screen, PAL[32], (x - 2, y - 2, 24, 24), 2)
            self._draw_pal_item(x, y, item_id, cat)
            
        # Name
        if items:
            n = items[self.pal_idx][1]
            nt = font.render(n, True, PAL[32])
            self.screen.blit(nt, (WIDTH - 130, HEIGHT - 30))
            
        # Theme indicator
        ti = font.render(f"Theme: {self.edit_lv.theme}", True, PAL[45])
        self.screen.blit(ti, (WIDTH - 130, HEIGHT - 50))
        
    def _draw_pal_item(self, x, y, item_id, cat):
        if cat == "terrain":
            if item_id == "G":
                pygame.draw.rect(self.screen, PAL[23], (x, y, 20, 20))
                pygame.draw.rect(self.screen, PAL[26], (x, y, 20, 4))
            elif item_id == "D":
                pygame.draw.rect(self.screen, PAL[22], (x, y, 20, 20))
            elif item_id == "P":
                pygame.draw.rect(self.screen, PAL[23], (x, y, 20, 20))
                pygame.draw.rect(self.screen, PAL[0], (x+2, y+2, 16, 16))
            elif item_id == "T":
                pygame.draw.rect(self.screen, PAL[26], (x, y, 20, 20))
            elif item_id == " ":
                pygame.draw.rect(self.screen, PAL[32], (x, y, 20, 20), 1)
                pygame.draw.line(self.screen, PAL[22], (x, y), (x+20, y+20))
        elif cat == "blocks":
            if item_id == "B":
                pygame.draw.rect(self.screen, PAL[22], (x, y, 20, 20))
                pygame.draw.rect(self.screen, PAL[0], (x, y+9, 20, 2))
                pygame.draw.rect(self.screen, PAL[0], (x+9, y, 2, 20))
            elif item_id in ("?", "?C", "?M"):
                pygame.draw.rect(self.screen, PAL[39], (x, y, 20, 20))
                pygame.draw.rect(self.screen, PAL[40], (x+4, y+4, 12, 12))
        elif cat == "enemies":
            if item_id == "goomba":
                pygame.draw.ellipse(self.screen, GOOMBA, (x+2, y+4, 16, 14))
            elif item_id == "koopa":
                pygame.draw.ellipse(self.screen, KOOPA_G, (x+2, y+4, 16, 14))
            elif item_id == "piranha":
                pygame.draw.ellipse(self.screen, PAL[22], (x+2, y+6, 16, 12))
        elif cat == "special":
            if item_id == "player":
                pygame.draw.rect(self.screen, PAL[22], (x+4, y+2, 12, 16))
            elif item_id == "flag":
                pygame.draw.rect(self.screen, PAL[0], (x+8, y+2, 3, 18))
                pygame.draw.polygon(self.screen, PAL[22], [(x+11, y+4), (x+20, y+8), (x+11, y+12)])
                
    def _draw_help(self):
        ov = pygame.Surface((WIDTH, HEIGHT))
        ov.fill((0, 0, 0))
        ov.set_alpha(220)
        self.screen.blit(ov, (0, 0))
        
        font = pygame.font.SysFont("arial", 16)
        lines = [
            "═══ KOOPA ENGINE EDITOR ═══",
            "",
            "Left Click: Place tile/enemy",
            "Right Click: Erase",
            "Mouse Wheel: Scroll palette",
            "1-4: Switch categories",
            "WASD/Arrows: Pan camera",
            "",
            "E / TAB: Play test level",
            "G: Toggle grid",
            "T: Change theme (1-8)",
            "H: Toggle this help",
            "",
            "Ctrl+S: Save level (.kpl)",
            "Ctrl+E: Export standalone game (.py)",
            "Ctrl+Z: Undo | Ctrl+Y: Redo",
            "Ctrl+N: New level",
            "",
            "ESC: Back to title"
        ]
        
        for i, line in enumerate(lines):
            color = PAL[39] if i == 0 else PAL[32]
            t = font.render(line, True, color)
            self.screen.blit(t, (WIDTH//2 - t.get_width()//2, 25 + i * 22))

# ╔═══════════════════════════════════════════════════════════════════════════════╗
# ║ MAIN                                                                          ║
# ╚═══════════════════════════════════════════════════════════════════════════════╝
if __name__ == "__main__":
    print("╔" + "═" * 58 + "╗")
    print("║" + "  AC!'s KOOPA ENGINE 1.1".center(58) + "║")
    print("║" + "  SMB1 Accurate + Lunar Magic Editor".center(58) + "║")
    print("║" + "  Team Flames / Samsoft / Flames Co.".center(58) + "║")
    print("╠" + "═" * 58 + "╣")
    print("║" + "  Controls:".ljust(58) + "║")
    print("║" + "    Arrows/WASD: Move | Space/Z: Jump | Shift/X: Run".ljust(58) + "║")
    print("║" + "    TAB: Toggle Editor | H: Help (in editor)".ljust(58) + "║")
    print("║" + "    Ctrl+E: Export game | Ctrl+S: Save level".ljust(58) + "║")
    print("╚" + "═" * 58 + "╝")
    
    engine = KoopaEngine()
    engine.run()
