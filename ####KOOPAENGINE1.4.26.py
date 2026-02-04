#!/usr/bin/env python3
"""
ULTRA KOOPA 2D
A complete platformer with 32 levels (World 1-1 to 8-4) and Ultra Fan Builder level editor
By Team Flames / Samsoft

All assets procedurally generated - no external files required
"""

import pygame
import math
import json
import random
import os
from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
TILE_SIZE = 32
FPS = 60
GRAVITY = 0.4
MAX_FALL_SPEED = 12
PLAYER_SPEED = 4
PLAYER_RUN_SPEED = 6
PLAYER_JUMP_VELOCITY = -11

# Colors
SKY_BLUE = (92, 148, 252)
SKY_NIGHT = (0, 0, 32)
SKY_UNDERGROUND = (0, 0, 0)
SKY_CASTLE = (0, 0, 0)
SKY_WATER = (0, 32, 128)

class GameState(Enum):
    TITLE = auto()
    PLAYING = auto()
    PAUSED = auto()
    EDITOR = auto()
    GAME_OVER = auto()
    LEVEL_COMPLETE = auto()
    CASTLE_COMPLETE = auto()
    GAME_COMPLETE = auto()

class TileType(Enum):
    AIR = 0
    GROUND = 1
    BRICK = 2
    QUESTION = 3
    HARD_BLOCK = 4
    PIPE_TL = 5
    PIPE_TR = 6
    PIPE_BL = 7
    PIPE_BR = 8
    COIN = 9
    FLAG_POLE = 10
    FLAG_TOP = 11
    CASTLE_BLOCK = 12
    WATER = 15
    LAVA = 16
    PLATFORM = 17
    BRIDGE = 18
    AXE = 19
    USED_BLOCK = 21

class EnemyType(Enum):
    GOOMBA = auto()
    KOOPA = auto()
    PIRANHA = auto()
    HAMMER_BRO = auto()
    BUZZY = auto()
    CHEEP = auto()
    BLOOPER = auto()
    BOWSER = auto()
    FIRE_BAR = auto()
    LAKITU = auto()
    SPINY = auto()

class PowerUp(Enum):
    MUSHROOM = auto()
    FIRE_FLOWER = auto()
    STAR = auto()
    ONE_UP = auto()

class PlayerState(Enum):
    SMALL = auto()
    BIG = auto()
    FIRE = auto()

class AssetGenerator:
    @staticmethod
    def create_surface(w, h):
        return pygame.Surface((w, h), pygame.SRCALPHA)
    
    @classmethod
    def generate_player(cls, state, frame=0, facing_right=True):
        height = TILE_SIZE if state == PlayerState.SMALL else TILE_SIZE * 2
        surf = cls.create_surface(TILE_SIZE, height)
        
        hat_color = (255, 255, 255) if state == PlayerState.FIRE else (255, 0, 0)
        skin_color = (255, 200, 150)
        overall_color = (255, 0, 0) if state == PlayerState.FIRE else (0, 0, 200)
        
        if state == PlayerState.SMALL:
            pygame.draw.ellipse(surf, hat_color, (4, 2, 24, 12))
            pygame.draw.ellipse(surf, skin_color, (8, 8, 16, 12))
            pygame.draw.rect(surf, overall_color, (6, 18, 20, 10))
            pygame.draw.rect(surf, overall_color, (4, 26, 8, 6))
            pygame.draw.rect(surf, overall_color, (20, 26, 8, 6))
        else:
            pygame.draw.ellipse(surf, hat_color, (4, 2, 24, 16))
            pygame.draw.ellipse(surf, skin_color, (6, 14, 20, 16))
            pygame.draw.rect(surf, overall_color, (4, 28, 24, 20))
            pygame.draw.rect(surf, overall_color, (2, 46, 12, 18))
            pygame.draw.rect(surf, overall_color, (18, 46, 12, 18))
        
        if not facing_right:
            surf = pygame.transform.flip(surf, True, False)
        return surf
    
    @classmethod
    def generate_tile(cls, tile_type, variant=0):
        surf = cls.create_surface(TILE_SIZE, TILE_SIZE)
        
        if tile_type == TileType.GROUND:
            surf.fill((139, 69, 19))
            pygame.draw.rect(surf, (101, 49, 12), (0, 0, TILE_SIZE, 4))
            pygame.draw.rect(surf, (179, 109, 59), (2, 6, 12, 10))
            pygame.draw.rect(surf, (179, 109, 59), (18, 6, 12, 10))
        elif tile_type == TileType.BRICK:
            surf.fill((200, 76, 12))
            for y in range(0, TILE_SIZE, 8):
                offset = 8 if (y // 8) % 2 else 0
                for x in range(-8 + offset, TILE_SIZE, 16):
                    pygame.draw.rect(surf, (139, 52, 8), (x, y, 16, 8), 1)
        elif tile_type == TileType.QUESTION:
            surf.fill((255, 180, 0))
            pygame.draw.rect(surf, (200, 140, 0), (0, 0, TILE_SIZE, TILE_SIZE), 3)
            pygame.draw.rect(surf, (139, 69, 19), (10, 8, 12, 4))
            pygame.draw.rect(surf, (139, 69, 19), (12, 16, 8, 4))
            pygame.draw.rect(surf, (139, 69, 19), (12, 22, 4, 4))
        elif tile_type == TileType.USED_BLOCK:
            surf.fill((100, 60, 20))
            pygame.draw.rect(surf, (60, 40, 10), (0, 0, TILE_SIZE, TILE_SIZE), 3)
        elif tile_type == TileType.HARD_BLOCK:
            surf.fill((150, 150, 150))
            pygame.draw.rect(surf, (100, 100, 100), (0, 0, TILE_SIZE, TILE_SIZE), 2)
        elif tile_type in [TileType.PIPE_TL, TileType.PIPE_TR, TileType.PIPE_BL, TileType.PIPE_BR]:
            surf.fill((0, 200, 0))
            pygame.draw.rect(surf, (0, 140, 0), (0, 0, 4, TILE_SIZE))
            pygame.draw.rect(surf, (100, 255, 100), (4, 0, 4, TILE_SIZE))
            if tile_type in [TileType.PIPE_TL, TileType.PIPE_TR]:
                pygame.draw.rect(surf, (0, 180, 0), (0, 0, TILE_SIZE, 8))
        elif tile_type == TileType.COIN:
            pygame.draw.ellipse(surf, (255, 200, 0), (8, 4, 16, 24))
            pygame.draw.ellipse(surf, (255, 255, 100), (12, 8, 8, 16))
        elif tile_type == TileType.FLAG_POLE:
            pygame.draw.rect(surf, (100, 100, 100), (14, 0, 4, TILE_SIZE))
        elif tile_type == TileType.FLAG_TOP:
            pygame.draw.rect(surf, (100, 100, 100), (14, 8, 4, TILE_SIZE - 8))
            pygame.draw.circle(surf, (0, 200, 0), (16, 8), 6)
        elif tile_type == TileType.CASTLE_BLOCK:
            surf.fill((80, 80, 80))
            pygame.draw.rect(surf, (60, 60, 60), (0, 0, TILE_SIZE, TILE_SIZE), 2)
        elif tile_type == TileType.WATER:
            surf.fill((0, 100, 200, 180))
        elif tile_type == TileType.LAVA:
            surf.fill((255, 100, 0))
            pygame.draw.rect(surf, (255, 200, 0), (0, 0, TILE_SIZE, 8))
        elif tile_type == TileType.PLATFORM:
            surf.fill((139, 90, 43))
            pygame.draw.rect(surf, (100, 60, 30), (0, 0, TILE_SIZE, 4))
        elif tile_type == TileType.BRIDGE:
            pygame.draw.rect(surf, (139, 90, 43), (0, 8, TILE_SIZE, 8))
        elif tile_type == TileType.AXE:
            pygame.draw.polygon(surf, (150, 150, 150), [(16, 4), (28, 16), (16, 28), (4, 16)])
            pygame.draw.rect(surf, (139, 69, 19), (14, 20, 4, 12))
        return surf
    
    @classmethod
    def generate_enemy(cls, enemy_type, frame=0):
        surf = cls.create_surface(TILE_SIZE, TILE_SIZE)
        
        if enemy_type == EnemyType.GOOMBA:
            pygame.draw.ellipse(surf, (139, 69, 19), (2, 4, 28, 20))
            pygame.draw.ellipse(surf, (255, 255, 255), (8, 8, 6, 8))
            pygame.draw.ellipse(surf, (255, 255, 255), (18, 8, 6, 8))
            pygame.draw.ellipse(surf, (0, 0, 0), (10, 10, 3, 5))
            pygame.draw.ellipse(surf, (0, 0, 0), (20, 10, 3, 5))
            pygame.draw.ellipse(surf, (50, 25, 5), (4, 22, 10, 8))
            pygame.draw.ellipse(surf, (50, 25, 5), (18, 22, 10, 8))
        elif enemy_type == EnemyType.KOOPA:
            pygame.draw.ellipse(surf, (0, 180, 0), (4, 8, 24, 20))
            pygame.draw.ellipse(surf, (255, 220, 150), (20, 2, 12, 12))
            pygame.draw.ellipse(surf, (255, 220, 150), (6, 24, 8, 6))
            pygame.draw.ellipse(surf, (255, 220, 150), (18, 24, 8, 6))
        elif enemy_type == EnemyType.PIRANHA:
            pygame.draw.ellipse(surf, (0, 180, 0), (4, 0, 24, 16))
            pygame.draw.rect(surf, (0, 140, 0), (12, 14, 8, 18))
            pygame.draw.ellipse(surf, (200, 0, 0), (6, 4, 20, 10))
        elif enemy_type == EnemyType.BUZZY:
            pygame.draw.ellipse(surf, (50, 50, 100), (2, 8, 28, 20))
        elif enemy_type == EnemyType.CHEEP:
            pygame.draw.ellipse(surf, (255, 100, 100), (2, 6, 28, 20))
        elif enemy_type == EnemyType.BLOOPER:
            pygame.draw.ellipse(surf, (255, 255, 255), (6, 0, 20, 20))
            pygame.draw.ellipse(surf, (0, 0, 0), (10, 6, 5, 8))
            pygame.draw.ellipse(surf, (0, 0, 0), (17, 6, 5, 8))
        elif enemy_type == EnemyType.HAMMER_BRO:
            pygame.draw.ellipse(surf, (0, 180, 0), (8, 0, 16, 12))
            pygame.draw.rect(surf, (0, 180, 0), (6, 10, 20, 14))
        elif enemy_type == EnemyType.BOWSER:
            surf = cls.create_surface(TILE_SIZE * 2, TILE_SIZE * 2)
            pygame.draw.ellipse(surf, (0, 120, 0), (8, 16, 48, 40))
            pygame.draw.ellipse(surf, (255, 180, 100), (4, 28, 24, 32))
            pygame.draw.ellipse(surf, (0, 150, 0), (48, 8, 24, 28))
            return surf
        elif enemy_type == EnemyType.LAKITU:
            pygame.draw.ellipse(surf, (255, 255, 255), (2, 16, 28, 14))
            pygame.draw.ellipse(surf, (0, 180, 0), (8, 4, 16, 16))
        elif enemy_type == EnemyType.SPINY:
            pygame.draw.ellipse(surf, (200, 50, 50), (4, 10, 24, 18))
            for x in range(6, 26, 6):
                pygame.draw.polygon(surf, (255, 255, 255), [(x, 12), (x + 3, 2), (x + 6, 12)])
        return surf
    
    @classmethod
    def generate_powerup(cls, powerup_type):
        surf = cls.create_surface(TILE_SIZE, TILE_SIZE)
        
        if powerup_type == PowerUp.MUSHROOM:
            pygame.draw.ellipse(surf, (255, 0, 0), (2, 2, 28, 18))
            pygame.draw.ellipse(surf, (255, 255, 255), (6, 6, 8, 8))
            pygame.draw.ellipse(surf, (255, 255, 255), (18, 6, 8, 8))
            pygame.draw.rect(surf, (255, 220, 180), (8, 18, 16, 12))
        elif powerup_type == PowerUp.FIRE_FLOWER:
            pygame.draw.circle(surf, (255, 100, 0), (16, 10), 8)
            for angle in range(0, 360, 45):
                x = 16 + int(math.cos(math.radians(angle)) * 10)
                y = 10 + int(math.sin(math.radians(angle)) * 10)
                pygame.draw.circle(surf, (255, 200, 0), (x, y), 4)
            pygame.draw.rect(surf, (0, 180, 0), (14, 16, 4, 14))
        elif powerup_type == PowerUp.STAR:
            points = []
            for i in range(5):
                angle = math.radians(i * 72 - 90)
                points.append((16 + int(math.cos(angle) * 14), 16 + int(math.sin(angle) * 14)))
                angle = math.radians(i * 72 - 90 + 36)
                points.append((16 + int(math.cos(angle) * 6), 16 + int(math.sin(angle) * 6)))
            pygame.draw.polygon(surf, (255, 255, 0), points)
        elif powerup_type == PowerUp.ONE_UP:
            pygame.draw.ellipse(surf, (0, 200, 0), (2, 2, 28, 18))
            pygame.draw.rect(surf, (255, 220, 180), (8, 18, 16, 12))
        return surf

@dataclass
class Entity:
    x: float
    y: float
    width: int
    height: int
    vel_x: float = 0
    vel_y: float = 0
    on_ground: bool = False
    facing_right: bool = True
    active: bool = True
    
    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

@dataclass
class Player(Entity):
    state: PlayerState = PlayerState.SMALL
    coins: int = 0
    lives: int = 3
    score: int = 0
    invincible: float = 0
    star_power: float = 0
    dead: bool = False
    finished: bool = False
    animation_frame: int = 0

@dataclass 
class Enemy(Entity):
    enemy_type: EnemyType = EnemyType.GOOMBA
    animation_timer: int = 0
    shell_sliding: bool = False

@dataclass
class PowerUpEntity(Entity):
    powerup_type: PowerUp = PowerUp.MUSHROOM
    emerging: bool = True
    emerge_y: float = 0

class LevelGenerator:
    @staticmethod
    def create_empty_level(width=200, height=15):
        return {
            'tiles': [[TileType.AIR.value for _ in range(width)] for _ in range(height)],
            'enemies': [],
            'powerups': [],
            'width': width,
            'height': height,
            'background': 'overworld',
            'time': 400,
            'start_x': 3,
            'start_y': 12
        }
    
    @staticmethod
    def add_ground(level, start_x, end_x, height=2):
        for x in range(start_x, min(end_x, level['width'])):
            for y in range(level['height'] - height, level['height']):
                level['tiles'][y][x] = TileType.GROUND.value
    
    @staticmethod
    def add_platform(level, x, y, width, tile_type=TileType.BRICK):
        for i in range(width):
            if x + i < level['width'] and y >= 0:
                level['tiles'][y][x + i] = tile_type.value
    
    @staticmethod
    def add_pipe(level, x, ground_y, height=2):
        for h in range(height):
            y = ground_y - height + h
            if y >= 0:
                if h == 0:
                    level['tiles'][y][x] = TileType.PIPE_TL.value
                    level['tiles'][y][x + 1] = TileType.PIPE_TR.value
                else:
                    level['tiles'][y][x] = TileType.PIPE_BL.value
                    level['tiles'][y][x + 1] = TileType.PIPE_BR.value
    
    @staticmethod
    def add_stairs(level, x, ground_y, height, right=True):
        for h in range(height):
            stair_width = h + 1 if right else height - h
            start_x = x if right else x + h
            for w in range(stair_width):
                for dy in range(h + 1):
                    ty = ground_y - h - 1 + dy
                    if ty >= 0 and start_x + w < level['width']:
                        level['tiles'][ty][start_x + w] = TileType.HARD_BLOCK.value
    
    @staticmethod
    def add_flag(level, x, ground_y):
        for h in range(8):
            y = ground_y - 8 + h
            if y >= 0:
                level['tiles'][y][x] = TileType.FLAG_TOP.value if h == 0 else TileType.FLAG_POLE.value
    
    @staticmethod
    def add_castle(level, x, ground_y):
        for cy in range(5):
            for cx in range(5):
                y = ground_y - 5 + cy
                if y >= 0 and x + cx < level['width']:
                    level['tiles'][y][x + cx] = TileType.CASTLE_BLOCK.value
    
    @classmethod
    def generate_level(cls, world, lvl):
        level = cls.create_empty_level(212, 15)
        ground_y = 13
        
        # Set background based on level type
        if lvl == 2:
            level['background'] = 'underground'
        elif lvl == 4:
            level['background'] = 'castle'
        elif world >= 5:
            level['background'] = 'night' if lvl == 1 else level['background']
        
        # Generate ground with gaps
        cls.add_ground(level, 0, 70, 2)
        cls.add_ground(level, 73, 90, 2)
        cls.add_ground(level, 93, 212, 2)
        
        # Add platforms
        cls.add_platform(level, 20, 9, 4, TileType.BRICK)
        level['tiles'][9][22] = TileType.QUESTION.value
        level['powerups'].append({'x': 22, 'y': 9, 'type': 'mushroom'})
        
        level['tiles'][5][22] = TileType.QUESTION.value
        level['powerups'].append({'x': 22, 'y': 5, 'type': 'coin'})
        
        # Add pipes
        cls.add_pipe(level, 28, ground_y, 2)
        cls.add_pipe(level, 38, ground_y, 3)
        cls.add_pipe(level, 46, ground_y, 4)
        
        # More platforms
        cls.add_platform(level, 80, 9, 3, TileType.BRICK)
        cls.add_platform(level, 100, 5, 5, TileType.BRICK)
        level['tiles'][5][102] = TileType.QUESTION.value
        level['powerups'].append({'x': 102, 'y': 5, 'type': 'star' if world >= 3 else 'mushroom'})
        
        cls.add_platform(level, 120, 9, 4, TileType.BRICK)
        
        # Stairs and flag
        cls.add_stairs(level, 150, ground_y, 4, True)
        cls.add_stairs(level, 160, ground_y, 4, False)
        cls.add_stairs(level, 175, ground_y, 8, True)
        cls.add_flag(level, 188, ground_y)
        cls.add_castle(level, 195, ground_y)
        
        # Castle levels get lava and bridge
        if lvl == 4:
            for x in range(60, 75):
                level['tiles'][13][x] = TileType.LAVA.value
                level['tiles'][14][x] = TileType.LAVA.value
            cls.add_platform(level, 62, 10, 4, TileType.PLATFORM)
            cls.add_platform(level, 165, 10, 12, TileType.BRIDGE)
            level['tiles'][10][177] = TileType.AXE.value
        
        # Add enemies based on world
        base_enemies = [
            {'x': 25, 'y': 12, 'type': 'goomba'},
            {'x': 40, 'y': 12, 'type': 'goomba'},
            {'x': 60, 'y': 12, 'type': 'koopa'},
            {'x': 85, 'y': 12, 'type': 'goomba'},
            {'x': 110, 'y': 12, 'type': 'goomba'},
            {'x': 130, 'y': 12, 'type': 'koopa'},
        ]
        
        level['enemies'] = base_enemies
        
        # Add more enemies for higher worlds
        if world >= 3:
            level['enemies'].append({'x': 50, 'y': 12, 'type': 'hammer_bro'})
        if world >= 5:
            level['enemies'].append({'x': 95, 'y': 12, 'type': 'buzzy'})
        if world >= 7:
            level['enemies'].append({'x': 140, 'y': 12, 'type': 'hammer_bro'})
        if lvl == 4:
            level['enemies'].append({'x': 170, 'y': 8, 'type': 'bowser'})
            level['enemies'].append({'x': 55, 'y': 10, 'type': 'fire_bar'})
        
        level['time'] = max(250, 400 - world * 15)
        return level

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Ultra Koopa 2D")
        self.clock = pygame.time.Clock()
        self.running = True
        
        self.state = GameState.TITLE
        self.current_world = 1
        self.current_level = 1
        self.level_data = None
        self.camera_x = 0
        
        self.player = None
        self.enemies = []
        self.powerups = []
        self.particles = []
        
        self.tile_cache = {}
        self.enemy_cache = {}
        self.powerup_cache = {}
        
        self.level_time = 0
        self.flag_y = 0
        self.flag_dropping = False
        
        # Editor
        self.editor_level = None
        self.editor_tile = TileType.GROUND
        self.editor_enemy = 'goomba'
        self.editor_camera_x = 0
        self.editor_mode = 'tile'
        
        self._cache_assets()
    
    def _cache_assets(self):
        for tile_type in TileType:
            self.tile_cache[tile_type] = AssetGenerator.generate_tile(tile_type)
        for enemy_type in EnemyType:
            if enemy_type != EnemyType.FIRE_BAR:
                self.enemy_cache[enemy_type] = AssetGenerator.generate_enemy(enemy_type)
        for powerup_type in PowerUp:
            self.powerup_cache[powerup_type] = AssetGenerator.generate_powerup(powerup_type)
    
    def reset_level(self):
        self.level_data = LevelGenerator.generate_level(self.current_world, self.current_level)
        
        saved_state = getattr(self, '_saved_state', PlayerState.SMALL)
        saved_lives = getattr(self, '_saved_lives', 3)
        saved_score = getattr(self, '_saved_score', 0)
        saved_coins = getattr(self, '_saved_coins', 0)
        
        height = TILE_SIZE if saved_state == PlayerState.SMALL else TILE_SIZE * 2
        self.player = Player(
            x=self.level_data['start_x'] * TILE_SIZE,
            y=self.level_data['start_y'] * TILE_SIZE - height + TILE_SIZE,
            width=TILE_SIZE,
            height=height,
            state=saved_state,
            lives=saved_lives,
            score=saved_score,
            coins=saved_coins
        )
        
        self.camera_x = 0
        self.level_time = self.level_data.get('time', 400) * FPS
        self.enemies = []
        self.powerups = []
        self.flag_y = 0
        self.flag_dropping = False
        
        for enemy_data in self.level_data.get('enemies', []):
            enemy_type = {
                'goomba': EnemyType.GOOMBA,
                'koopa': EnemyType.KOOPA,
                'piranha': EnemyType.PIRANHA,
                'hammer_bro': EnemyType.HAMMER_BRO,
                'buzzy': EnemyType.BUZZY,
                'cheep': EnemyType.CHEEP,
                'blooper': EnemyType.BLOOPER,
                'bowser': EnemyType.BOWSER,
                'fire_bar': EnemyType.FIRE_BAR,
                'lakitu': EnemyType.LAKITU,
                'spiny': EnemyType.SPINY,
            }.get(enemy_data['type'], EnemyType.GOOMBA)
            
            size = TILE_SIZE * 2 if enemy_type == EnemyType.BOWSER else TILE_SIZE
            enemy = Enemy(
                x=enemy_data['x'] * TILE_SIZE,
                y=enemy_data['y'] * TILE_SIZE,
                width=size,
                height=size,
                enemy_type=enemy_type,
                vel_x=-1 if enemy_type not in [EnemyType.PIRANHA, EnemyType.FIRE_BAR] else 0
            )
            self.enemies.append(enemy)
    
    def save_player_state(self):
        if self.player:
            self._saved_state = self.player.state
            self._saved_lives = self.player.lives
            self._saved_score = self.player.score
            self._saved_coins = self.player.coins
    
    def get_tile(self, x, y):
        if not self.level_data:
            return TileType.AIR
        if y < 0 or y >= self.level_data['height'] or x < 0 or x >= self.level_data['width']:
            return TileType.AIR
        return TileType(self.level_data['tiles'][y][x])
    
    def set_tile(self, x, y, tile_type):
        if self.level_data and 0 <= y < self.level_data['height'] and 0 <= x < self.level_data['width']:
            self.level_data['tiles'][y][x] = tile_type.value
    
    def is_solid(self, tile):
        return tile in {TileType.GROUND, TileType.BRICK, TileType.QUESTION, TileType.HARD_BLOCK,
                       TileType.PIPE_TL, TileType.PIPE_TR, TileType.PIPE_BL, TileType.PIPE_BR,
                       TileType.CASTLE_BLOCK, TileType.USED_BLOCK, TileType.PLATFORM}
    
    def check_collision(self, rect):
        left_tile = rect.left // TILE_SIZE
        right_tile = (rect.right - 1) // TILE_SIZE
        top_tile = rect.top // TILE_SIZE
        bottom_tile = (rect.bottom - 1) // TILE_SIZE
        
        for ty in range(top_tile, bottom_tile + 1):
            for tx in range(left_tile, right_tile + 1):
                if self.is_solid(self.get_tile(tx, ty)):
                    return True
        return False
    
    def update_player(self):
        if not self.player or self.player.dead or self.player.finished:
            return
        
        keys = pygame.key.get_pressed()
        speed = PLAYER_RUN_SPEED if keys[pygame.K_LSHIFT] or keys[pygame.K_x] else PLAYER_SPEED
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.player.vel_x = -speed
            self.player.facing_right = False
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.player.vel_x = speed
            self.player.facing_right = True
        else:
            self.player.vel_x *= 0.85
            if abs(self.player.vel_x) < 0.1:
                self.player.vel_x = 0
        
        if (keys[pygame.K_SPACE] or keys[pygame.K_z] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.player.on_ground:
            self.player.vel_y = PLAYER_JUMP_VELOCITY
            self.player.on_ground = False
        
        self.player.vel_y += GRAVITY
        if self.player.vel_y > MAX_FALL_SPEED:
            self.player.vel_y = MAX_FALL_SPEED
        
        # Horizontal movement
        self.player.x += self.player.vel_x
        if self.check_collision(self.player.rect):
            if self.player.vel_x > 0:
                self.player.x = (self.player.rect.right // TILE_SIZE) * TILE_SIZE - self.player.width
            else:
                self.player.x = (self.player.rect.left // TILE_SIZE + 1) * TILE_SIZE
            self.player.vel_x = 0
        
        if self.player.x < 0:
            self.player.x = 0
        
        # Vertical movement
        self.player.y += self.player.vel_y
        self.player.on_ground = False
        
        if self.check_collision(self.player.rect):
            if self.player.vel_y > 0:
                self.player.y = (self.player.rect.bottom // TILE_SIZE) * TILE_SIZE - self.player.height
                self.player.on_ground = True
            else:
                self.player.y = (self.player.rect.top // TILE_SIZE + 1) * TILE_SIZE
                hit_x = self.player.rect.centerx // TILE_SIZE
                hit_y = (self.player.rect.top - 1) // TILE_SIZE
                tile = self.get_tile(hit_x, hit_y)
                if tile == TileType.BRICK and self.player.state != PlayerState.SMALL:
                    self.set_tile(hit_x, hit_y, TileType.AIR)
                    self.player.score += 50
                elif tile == TileType.QUESTION:
                    self.set_tile(hit_x, hit_y, TileType.USED_BLOCK)
                    self._spawn_powerup(hit_x, hit_y)
            self.player.vel_y = 0
        
        # Collect coins
        for ty in range(self.player.rect.top // TILE_SIZE, self.player.rect.bottom // TILE_SIZE + 1):
            for tx in range(self.player.rect.left // TILE_SIZE, self.player.rect.right // TILE_SIZE + 1):
                if self.get_tile(tx, ty) == TileType.COIN:
                    self.set_tile(tx, ty, TileType.AIR)
                    self.player.coins += 1
                    self.player.score += 200
                    if self.player.coins >= 100:
                        self.player.coins = 0
                        self.player.lives += 1
        
        # Check flag/axe
        for ty in range(self.player.rect.top // TILE_SIZE, self.player.rect.bottom // TILE_SIZE + 1):
            for tx in range(self.player.rect.left // TILE_SIZE, self.player.rect.right // TILE_SIZE + 1):
                tile = self.get_tile(tx, ty)
                if tile in [TileType.FLAG_POLE, TileType.FLAG_TOP]:
                    self.player.finished = True
                    self.flag_dropping = True
                    self.player.score += 1000
                elif tile == TileType.AXE:
                    self.state = GameState.CASTLE_COMPLETE
        
        # Death
        if self.player.y > self.level_data['height'] * TILE_SIZE:
            self.player_die()
        
        # Camera
        self.camera_x = max(0, self.player.x - SCREEN_WIDTH // 3)
        max_camera = self.level_data['width'] * TILE_SIZE - SCREEN_WIDTH
        self.camera_x = min(self.camera_x, max(0, max_camera))
        
        # Invincibility
        if self.player.invincible > 0:
            self.player.invincible -= 1
        if self.player.star_power > 0:
            self.player.star_power -= 1
    
    def _spawn_powerup(self, x, y):
        for pu_data in self.level_data.get('powerups', []):
            if pu_data['x'] == x and pu_data['y'] == y:
                pu_type = {
                    'coin': None,
                    'mushroom': PowerUp.MUSHROOM if self.player.state == PlayerState.SMALL else PowerUp.FIRE_FLOWER,
                    'fire_flower': PowerUp.FIRE_FLOWER,
                    'star': PowerUp.STAR,
                    '1up': PowerUp.ONE_UP,
                }.get(pu_data['type'], PowerUp.MUSHROOM)
                
                if pu_type is None:
                    self.player.coins += 1
                    self.player.score += 200
                else:
                    powerup = PowerUpEntity(
                        x=x * TILE_SIZE,
                        y=y * TILE_SIZE,
                        width=TILE_SIZE,
                        height=TILE_SIZE,
                        powerup_type=pu_type,
                        emerge_y=y * TILE_SIZE
                    )
                    self.powerups.append(powerup)
                return
        self.player.coins += 1
        self.player.score += 200
    
    def update_enemies(self):
        for enemy in self.enemies:
            if not enemy.active or abs(enemy.x - self.player.x) > SCREEN_WIDTH * 1.5:
                continue
            
            if enemy.enemy_type == EnemyType.FIRE_BAR:
                enemy.animation_timer += 1
                continue
            
            if enemy.enemy_type == EnemyType.PIRANHA:
                enemy.animation_timer += 1
                if enemy.animation_timer < 60:
                    enemy.y -= 0.5
                elif enemy.animation_timer < 120:
                    pass
                elif enemy.animation_timer < 180:
                    enemy.y += 0.5
                else:
                    enemy.animation_timer = 0
                continue
            
            enemy.vel_y += GRAVITY * 0.5
            if enemy.vel_y > MAX_FALL_SPEED:
                enemy.vel_y = MAX_FALL_SPEED
            
            enemy.x += enemy.vel_x
            enemy.y += enemy.vel_y
            
            if self.check_collision(enemy.rect):
                if enemy.vel_y > 0:
                    enemy.y = (enemy.rect.bottom // TILE_SIZE) * TILE_SIZE - enemy.height
                    enemy.vel_y = 0
                    enemy.on_ground = True
            
            test_rect = pygame.Rect(enemy.x + (TILE_SIZE if enemy.vel_x > 0 else -4), enemy.y, 4, enemy.height)
            if self.check_collision(test_rect):
                enemy.vel_x = -enemy.vel_x
            
            if enemy.y > self.level_data['height'] * TILE_SIZE:
                enemy.active = False
    
    def update_powerups(self):
        for powerup in self.powerups[:]:
            if powerup.emerging:
                powerup.y -= 1
                if powerup.y <= powerup.emerge_y - TILE_SIZE:
                    powerup.emerging = False
                continue
            
            if powerup.powerup_type in [PowerUp.MUSHROOM, PowerUp.ONE_UP]:
                powerup.vel_y += GRAVITY * 0.5
                powerup.x += powerup.vel_x
                powerup.y += powerup.vel_y
                
                if self.check_collision(powerup.rect):
                    if powerup.vel_y > 0:
                        powerup.y = (powerup.rect.bottom // TILE_SIZE) * TILE_SIZE - powerup.height
                        powerup.vel_y = 0
                    if self.check_collision(pygame.Rect(powerup.x + powerup.vel_x, powerup.y, powerup.width, powerup.height)):
                        powerup.vel_x = -powerup.vel_x
                
                if powerup.vel_x == 0:
                    powerup.vel_x = 2
            
            if self.player and powerup.rect.colliderect(self.player.rect):
                self.collect_powerup(powerup)
                powerup.active = False
        
        self.powerups = [p for p in self.powerups if p.active]
    
    def collect_powerup(self, powerup):
        if powerup.powerup_type == PowerUp.MUSHROOM:
            if self.player.state == PlayerState.SMALL:
                self.player.state = PlayerState.BIG
                self.player.height = TILE_SIZE * 2
                self.player.y -= TILE_SIZE
            self.player.score += 1000
        elif powerup.powerup_type == PowerUp.FIRE_FLOWER:
            if self.player.state == PlayerState.SMALL:
                self.player.height = TILE_SIZE * 2
                self.player.y -= TILE_SIZE
            self.player.state = PlayerState.FIRE
            self.player.score += 1000
        elif powerup.powerup_type == PowerUp.STAR:
            self.player.star_power = 10 * FPS
            self.player.score += 1000
        elif powerup.powerup_type == PowerUp.ONE_UP:
            self.player.lives += 1
    
    def check_enemy_collision(self):
        if not self.player or self.player.dead or self.player.invincible > 0:
            return
        
        for enemy in self.enemies:
            if not enemy.active:
                continue
            
            if enemy.enemy_type == EnemyType.FIRE_BAR:
                continue
            
            if self.player.rect.colliderect(enemy.rect):
                if self.player.vel_y > 0 and self.player.rect.bottom - enemy.rect.top < TILE_SIZE // 2:
                    if enemy.enemy_type in [EnemyType.GOOMBA, EnemyType.KOOPA, EnemyType.BUZZY]:
                        enemy.active = False
                        self.player.score += 100
                    self.player.vel_y = -8
                elif self.player.star_power > 0:
                    enemy.active = False
                    self.player.score += 200
                else:
                    self.player_hit()
    
    def player_hit(self):
        if self.player.invincible > 0 or self.player.star_power > 0:
            return
        
        if self.player.state == PlayerState.FIRE:
            self.player.state = PlayerState.BIG
            self.player.invincible = 2 * FPS
        elif self.player.state == PlayerState.BIG:
            self.player.state = PlayerState.SMALL
            self.player.height = TILE_SIZE
            self.player.invincible = 2 * FPS
        else:
            self.player_die()
    
    def player_die(self):
        self.player.dead = True
        self.player.vel_y = PLAYER_JUMP_VELOCITY
        self.player.lives -= 1
    
    def update(self):
        if self.state == GameState.PLAYING:
            self.update_player()
            self.update_enemies()
            self.update_powerups()
            self.check_enemy_collision()
            
            self.level_time -= 1
            if self.level_time <= 0:
                self.player_die()
            
            if self.player and self.player.dead:
                self.player.vel_y += GRAVITY
                self.player.y += self.player.vel_y
                if self.player.y > SCREEN_HEIGHT + 100:
                    if self.player.lives <= 0:
                        self.state = GameState.GAME_OVER
                    else:
                        self.reset_level()
            
            if self.player and self.player.finished:
                if self.flag_dropping:
                    self.flag_y += 4
                    if self.flag_y >= 7 * TILE_SIZE:
                        self.flag_dropping = False
                        self.state = GameState.LEVEL_COMPLETE
    
    def get_bg_color(self):
        bg = self.level_data.get('background', 'overworld') if self.level_data else 'overworld'
        return {'overworld': SKY_BLUE, 'underground': SKY_UNDERGROUND, 'castle': SKY_CASTLE, 
                'water': SKY_WATER, 'night': SKY_NIGHT}.get(bg, SKY_BLUE)
    
    def draw_level(self):
        if not self.level_data:
            return
        
        start_x = max(0, int(self.camera_x) // TILE_SIZE)
        end_x = min(self.level_data['width'], start_x + SCREEN_WIDTH // TILE_SIZE + 2)
        
        for y in range(self.level_data['height']):
            for x in range(start_x, end_x):
                tile = self.get_tile(x, y)
                if tile != TileType.AIR:
                    sprite = self.tile_cache.get(tile)
                    if sprite:
                        self.screen.blit(sprite, (x * TILE_SIZE - int(self.camera_x), y * TILE_SIZE))
    
    def draw_player(self):
        if not self.player:
            return
        if self.player.invincible > 0 and (self.player.invincible // 4) % 2:
            return
        
        sprite = AssetGenerator.generate_player(self.player.state, self.player.animation_frame, self.player.facing_right)
        self.screen.blit(sprite, (int(self.player.x - self.camera_x), int(self.player.y)))
    
    def draw_enemies(self):
        for enemy in self.enemies:
            if not enemy.active:
                continue
            if enemy.x < self.camera_x - TILE_SIZE * 2 or enemy.x > self.camera_x + SCREEN_WIDTH + TILE_SIZE * 2:
                continue
            
            if enemy.enemy_type == EnemyType.FIRE_BAR:
                cx = int(enemy.x - self.camera_x + TILE_SIZE // 2)
                cy = int(enemy.y + TILE_SIZE // 2)
                angle = enemy.animation_timer * 0.05
                for i in range(6):
                    bx = cx + int(math.cos(angle) * i * 12)
                    by = cy + int(math.sin(angle) * i * 12)
                    pygame.draw.circle(self.screen, (255, 100, 0), (bx, by), 6)
                continue
            
            sprite = self.enemy_cache.get(enemy.enemy_type)
            if sprite:
                self.screen.blit(sprite, (int(enemy.x - self.camera_x), int(enemy.y)))
    
    def draw_powerups(self):
        for powerup in self.powerups:
            sprite = self.powerup_cache.get(powerup.powerup_type)
            if sprite:
                self.screen.blit(sprite, (int(powerup.x - self.camera_x), int(powerup.y)))
    
    def draw_hud(self):
        font = pygame.font.Font(None, 28)
        score_text = font.render(f"SCORE: {self.player.score if self.player else 0:06d}", True, (255, 255, 255))
        self.screen.blit(score_text, (10, 10))
        
        coin_text = font.render(f"COINS: {self.player.coins if self.player else 0:02d}", True, (255, 255, 0))
        self.screen.blit(coin_text, (200, 10))
        
        world_text = font.render(f"WORLD {self.current_world}-{self.current_level}", True, (255, 255, 255))
        self.screen.blit(world_text, (380, 10))
        
        time_text = font.render(f"TIME: {self.level_time // FPS:03d}", True, (255, 255, 255))
        self.screen.blit(time_text, (550, 10))
        
        lives_text = font.render(f"x {self.player.lives if self.player else 0}", True, (255, 255, 255))
        self.screen.blit(lives_text, (720, 10))
    
    def draw_title(self):
        self.screen.fill((0, 0, 0))
        font_large = pygame.font.Font(None, 72)
        font_medium = pygame.font.Font(None, 36)
        
        title = font_large.render("ULTRA KOOPA 2D", True, (255, 200, 0))
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 150)))
        
        subtitle = font_medium.render("32 Levels - Worlds 1-1 to 8-4", True, (200, 200, 200))
        self.screen.blit(subtitle, subtitle.get_rect(center=(SCREEN_WIDTH // 2, 220)))
        
        player_sprite = AssetGenerator.generate_player(PlayerState.BIG, 0, True)
        self.screen.blit(player_sprite, (SCREEN_WIDTH // 2 - TILE_SIZE // 2, 280))
        
        option1 = font_medium.render("Press ENTER to Start Game", True, (255, 255, 255))
        self.screen.blit(option1, option1.get_rect(center=(SCREEN_WIDTH // 2, 400)))
        
        option2 = font_medium.render("Press E for Ultra Fan Builder", True, (100, 255, 100))
        self.screen.blit(option2, option2.get_rect(center=(SCREEN_WIDTH // 2, 450)))
        
        credits = font_medium.render("By Team Flames / Samsoft", True, (150, 150, 150))
        self.screen.blit(credits, credits.get_rect(center=(SCREEN_WIDTH // 2, 550)))
    
    def draw_game_over(self):
        self.screen.fill((0, 0, 0))
        font_large = pygame.font.Font(None, 72)
        font_medium = pygame.font.Font(None, 36)
        
        text = font_large.render("GAME OVER", True, (255, 0, 0))
        self.screen.blit(text, text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)))
        
        prompt = font_medium.render("Press ENTER to Continue", True, (200, 200, 200))
        self.screen.blit(prompt, prompt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50)))
    
    def draw_level_complete(self):
        self.screen.fill(self.get_bg_color())
        self.draw_level()
        
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.screen.blit(overlay, (0, 0))
        
        font_large = pygame.font.Font(None, 64)
        font_medium = pygame.font.Font(None, 36)
        
        text = font_large.render("LEVEL COMPLETE!", True, (255, 255, 0))
        self.screen.blit(text, text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)))
        
        prompt = font_medium.render("Press ENTER to Continue", True, (200, 200, 200))
        self.screen.blit(prompt, prompt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50)))
    
    def draw_castle_complete(self):
        self.screen.fill((0, 0, 0))
        font_large = pygame.font.Font(None, 64)
        font_medium = pygame.font.Font(None, 36)
        
        if self.current_world == 8 and self.current_level == 4:
            text = font_large.render("CONGRATULATIONS!", True, (255, 200, 0))
            text2 = font_medium.render("You have saved the kingdom!", True, (255, 255, 255))
        else:
            text = font_large.render(f"WORLD {self.current_world} COMPLETE!", True, (255, 200, 0))
            text2 = font_medium.render("But the princess is in another castle...", True, (255, 255, 255))
        
        self.screen.blit(text, text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)))
        self.screen.blit(text2, text2.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20)))
        
        prompt = font_medium.render("Press ENTER to Continue", True, (200, 200, 200))
        self.screen.blit(prompt, prompt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80)))
    
    def draw_game_complete(self):
        self.screen.fill((0, 0, 0))
        font_large = pygame.font.Font(None, 72)
        font_medium = pygame.font.Font(None, 36)
        
        text = font_large.render("YOU WIN!", True, (255, 200, 0))
        self.screen.blit(text, text.get_rect(center=(SCREEN_WIDTH // 2, 150)))
        
        thank = font_medium.render("Thank you for playing Ultra Koopa 2D!", True, (255, 255, 255))
        self.screen.blit(thank, thank.get_rect(center=(SCREEN_WIDTH // 2, 250)))
        
        score = font_medium.render(f"Final Score: {self.player.score if self.player else 0}", True, (255, 255, 0))
        self.screen.blit(score, score.get_rect(center=(SCREEN_WIDTH // 2, 320)))
        
        prompt = font_medium.render("Press ENTER to Return to Title", True, (200, 200, 200))
        self.screen.blit(prompt, prompt.get_rect(center=(SCREEN_WIDTH // 2, 450)))
    
    # =========== ULTRA FAN BUILDER ===========
    
    def init_editor(self):
        self.editor_level = LevelGenerator.create_empty_level(100, 15)
        LevelGenerator.add_ground(self.editor_level, 0, 100, 2)
        self.editor_camera_x = 0
        self.editor_tile = TileType.GROUND
        self.editor_enemy = 'goomba'
        self.editor_mode = 'tile'
    
    def draw_editor(self):
        bg = self.editor_level.get('background', 'overworld') if self.editor_level else 'overworld'
        bg_color = {'overworld': SKY_BLUE, 'underground': SKY_UNDERGROUND, 'castle': SKY_CASTLE,
                    'water': SKY_WATER, 'night': SKY_NIGHT}.get(bg, SKY_BLUE)
        self.screen.fill(bg_color)
        
        # Grid
        for x in range(0, SCREEN_WIDTH + TILE_SIZE, TILE_SIZE):
            pygame.draw.line(self.screen, (100, 100, 100), (x - int(self.editor_camera_x) % TILE_SIZE, 0),
                           (x - int(self.editor_camera_x) % TILE_SIZE, SCREEN_HEIGHT - 100), 1)
        for y in range(0, SCREEN_HEIGHT - 100, TILE_SIZE):
            pygame.draw.line(self.screen, (100, 100, 100), (0, y), (SCREEN_WIDTH, y), 1)
        
        # Tiles
        start_x = max(0, int(self.editor_camera_x) // TILE_SIZE)
        end_x = min(self.editor_level['width'], start_x + SCREEN_WIDTH // TILE_SIZE + 2)
        
        for y in range(self.editor_level['height']):
            for x in range(start_x, end_x):
                tile = TileType(self.editor_level['tiles'][y][x])
                if tile != TileType.AIR:
                    sprite = self.tile_cache.get(tile)
                    if sprite:
                        self.screen.blit(sprite, (x * TILE_SIZE - int(self.editor_camera_x), y * TILE_SIZE))
        
        # Enemies
        for enemy_data in self.editor_level.get('enemies', []):
            ex = enemy_data['x'] * TILE_SIZE - int(self.editor_camera_x)
            ey = enemy_data['y'] * TILE_SIZE
            if -TILE_SIZE < ex < SCREEN_WIDTH + TILE_SIZE:
                enemy_type = {'goomba': EnemyType.GOOMBA, 'koopa': EnemyType.KOOPA,
                             'piranha': EnemyType.PIRANHA, 'hammer_bro': EnemyType.HAMMER_BRO,
                             'buzzy': EnemyType.BUZZY, 'bowser': EnemyType.BOWSER}.get(enemy_data['type'], EnemyType.GOOMBA)
                sprite = self.enemy_cache.get(enemy_type)
                if sprite:
                    self.screen.blit(sprite, (ex, ey))
        
        # Cursor
        mouse_x, mouse_y = pygame.mouse.get_pos()
        if mouse_y < SCREEN_HEIGHT - 100:
            grid_x = (mouse_x + int(self.editor_camera_x)) // TILE_SIZE
            grid_y = mouse_y // TILE_SIZE
            pygame.draw.rect(self.screen, (255, 255, 255),
                           (grid_x * TILE_SIZE - int(self.editor_camera_x), grid_y * TILE_SIZE, TILE_SIZE, TILE_SIZE), 2)
        
        # UI Panel
        pygame.draw.rect(self.screen, (40, 40, 40), (0, SCREEN_HEIGHT - 100, SCREEN_WIDTH, 100))
        pygame.draw.rect(self.screen, (100, 100, 100), (0, SCREEN_HEIGHT - 100, SCREEN_WIDTH, 100), 2)
        
        font = pygame.font.Font(None, 24)
        title = font.render("ULTRA FAN BUILDER", True, (255, 200, 0))
        self.screen.blit(title, (10, SCREEN_HEIGHT - 95))
        
        mode_text = font.render(f"Mode: {self.editor_mode.upper()} | Tile: {self.editor_tile.name}", True, (255, 255, 255))
        self.screen.blit(mode_text, (200, SCREEN_HEIGHT - 95))
        
        controls = font.render("ARROWS: Scroll | 1-9: Tiles | T/E: Mode | S: Save | L: Load | ENTER: Test | ESC: Exit", True, (180, 180, 180))
        self.screen.blit(controls, (10, SCREEN_HEIGHT - 60))
        
        bg_text = font.render(f"Background: {self.editor_level.get('background', 'overworld')} (B to change)", True, (180, 180, 180))
        self.screen.blit(bg_text, (10, SCREEN_HEIGHT - 30))
    
    def editor_update(self):
        keys = pygame.key.get_pressed()
        
        if keys[pygame.K_LEFT]:
            self.editor_camera_x = max(0, self.editor_camera_x - 8)
        if keys[pygame.K_RIGHT]:
            self.editor_camera_x = min(self.editor_level['width'] * TILE_SIZE - SCREEN_WIDTH, self.editor_camera_x + 8)
        
        mouse_buttons = pygame.mouse.get_pressed()
        mouse_x, mouse_y = pygame.mouse.get_pos()
        
        if mouse_y < SCREEN_HEIGHT - 100:
            grid_x = (mouse_x + int(self.editor_camera_x)) // TILE_SIZE
            grid_y = mouse_y // TILE_SIZE
            
            if 0 <= grid_x < self.editor_level['width'] and 0 <= grid_y < self.editor_level['height']:
                if mouse_buttons[0]:
                    if self.editor_mode == 'tile':
                        self.editor_level['tiles'][grid_y][grid_x] = self.editor_tile.value
                    else:
                        exists = any(e['x'] == grid_x and e['y'] == grid_y for e in self.editor_level['enemies'])
                        if not exists:
                            self.editor_level['enemies'].append({'x': grid_x, 'y': grid_y, 'type': self.editor_enemy})
                elif mouse_buttons[2]:
                    if self.editor_mode == 'tile':
                        self.editor_level['tiles'][grid_y][grid_x] = TileType.AIR.value
                    else:
                        self.editor_level['enemies'] = [e for e in self.editor_level['enemies']
                                                        if not (e['x'] == grid_x and e['y'] == grid_y)]
    
    def editor_handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.state = GameState.TITLE
            elif event.key == pygame.K_RETURN:
                self.level_data = {
                    'tiles': [row[:] for row in self.editor_level['tiles']],
                    'enemies': self.editor_level['enemies'][:],
                    'powerups': self.editor_level.get('powerups', [])[:],
                    'width': self.editor_level['width'],
                    'height': self.editor_level['height'],
                    'background': self.editor_level.get('background', 'overworld'),
                    'time': 400,
                    'start_x': 3,
                    'start_y': 12
                }
                self.current_world = 0
                self.current_level = 0
                self._saved_state = PlayerState.SMALL
                self._saved_lives = 3
                self._saved_score = 0
                self._saved_coins = 0
                self.reset_level()
                self.state = GameState.PLAYING
            elif event.key == pygame.K_t:
                self.editor_mode = 'tile'
            elif event.key == pygame.K_e:
                self.editor_mode = 'enemy'
            elif event.key == pygame.K_b:
                bgs = ['overworld', 'underground', 'castle', 'water', 'night']
                current = bgs.index(self.editor_level.get('background', 'overworld'))
                self.editor_level['background'] = bgs[(current + 1) % len(bgs)]
            elif event.key == pygame.K_s:
                try:
                    with open('custom_level.json', 'w') as f:
                        json.dump(self.editor_level, f)
                    print("Level saved!")
                except Exception as e:
                    print(f"Save error: {e}")
            elif event.key == pygame.K_l:
                try:
                    if os.path.exists('custom_level.json'):
                        with open('custom_level.json', 'r') as f:
                            self.editor_level = json.load(f)
                        print("Level loaded!")
                except Exception as e:
                    print(f"Load error: {e}")
            elif event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9]:
                tiles = [TileType.GROUND, TileType.BRICK, TileType.QUESTION, TileType.HARD_BLOCK,
                        TileType.PIPE_TL, TileType.COIN, TileType.PLATFORM, TileType.LAVA, TileType.WATER]
                idx = event.key - pygame.K_1
                if idx < len(tiles):
                    self.editor_tile = tiles[idx]
                    self.editor_mode = 'tile'
            elif event.key == pygame.K_LEFTBRACKET:
                tiles = [t for t in TileType if t != TileType.AIR]
                idx = tiles.index(self.editor_tile) if self.editor_tile in tiles else 0
                self.editor_tile = tiles[(idx - 1) % len(tiles)]
            elif event.key == pygame.K_RIGHTBRACKET:
                tiles = [t for t in TileType if t != TileType.AIR]
                idx = tiles.index(self.editor_tile) if self.editor_tile in tiles else 0
                self.editor_tile = tiles[(idx + 1) % len(tiles)]
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.state == GameState.TITLE:
                    if event.key == pygame.K_RETURN:
                        self.current_world = 1
                        self.current_level = 1
                        self._saved_state = PlayerState.SMALL
                        self._saved_lives = 3
                        self._saved_score = 0
                        self._saved_coins = 0
                        self.reset_level()
                        self.state = GameState.PLAYING
                    elif event.key == pygame.K_e:
                        self.init_editor()
                        self.state = GameState.EDITOR
                elif self.state == GameState.PLAYING:
                    if event.key == pygame.K_ESCAPE:
                        self.state = GameState.PAUSED
                    elif event.key == pygame.K_r:
                        self.reset_level()
                elif self.state == GameState.PAUSED:
                    if event.key == pygame.K_ESCAPE:
                        self.state = GameState.PLAYING
                    elif event.key == pygame.K_q:
                        self.state = GameState.TITLE
                elif self.state == GameState.GAME_OVER:
                    if event.key == pygame.K_RETURN:
                        self.state = GameState.TITLE
                elif self.state == GameState.LEVEL_COMPLETE:
                    if event.key == pygame.K_RETURN:
                        self.save_player_state()
                        self.current_level += 1
                        if self.current_level > 4:
                            self.current_level = 1
                            self.current_world += 1
                        if self.current_world > 8:
                            self.state = GameState.GAME_COMPLETE
                        else:
                            self.reset_level()
                            self.state = GameState.PLAYING
                elif self.state == GameState.CASTLE_COMPLETE:
                    if event.key == pygame.K_RETURN:
                        self.save_player_state()
                        self.current_level = 1
                        self.current_world += 1
                        if self.current_world > 8:
                            self.state = GameState.GAME_COMPLETE
                        else:
                            self.reset_level()
                            self.state = GameState.PLAYING
                elif self.state == GameState.GAME_COMPLETE:
                    if event.key == pygame.K_RETURN:
                        self.state = GameState.TITLE
                elif self.state == GameState.EDITOR:
                    self.editor_handle_input(event)
    
    def draw(self):
        if self.state == GameState.TITLE:
            self.draw_title()
        elif self.state == GameState.PLAYING:
            self.screen.fill(self.get_bg_color())
            self.draw_level()
            self.draw_powerups()
            self.draw_enemies()
            self.draw_player()
            self.draw_hud()
        elif self.state == GameState.PAUSED:
            self.screen.fill(self.get_bg_color())
            self.draw_level()
            self.draw_player()
            self.draw_hud()
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            self.screen.blit(overlay, (0, 0))
            font = pygame.font.Font(None, 72)
            text = font.render("PAUSED", True, (255, 255, 255))
            self.screen.blit(text, text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))
        elif self.state == GameState.GAME_OVER:
            self.draw_game_over()
        elif self.state == GameState.LEVEL_COMPLETE:
            self.draw_level_complete()
        elif self.state == GameState.CASTLE_COMPLETE:
            self.draw_castle_complete()
        elif self.state == GameState.GAME_COMPLETE:
            self.draw_game_complete()
        elif self.state == GameState.EDITOR:
            self.draw_editor()
        
        pygame.display.flip()
    
    def run(self):
        while self.running:
            self.handle_events()
            
            if self.state == GameState.PLAYING:
                self.update()
            elif self.state == GameState.EDITOR:
                self.editor_update()
            
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()
