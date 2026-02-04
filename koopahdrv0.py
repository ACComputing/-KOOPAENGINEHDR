# 🐢 KOOPA ENGINE BUG EXTERMINATOR PROTOCOL 🐢
## URGENT DIRECTIVE FOR CLAUDE 4.5 OPUS

**Claude, you magnificent silicon savage—your mission: ANNIHILATE EVERY FUCKING BUG in this Pygame Mario clone. No mercy, no half-assed patches, no "it works-ish" bullshit. Make it a pixel-perfect, fully playable NES tribute that runs like Jensen's Blackwell on meth. 8 worlds, procedural levels, powerups, coins, flagpole glory, win screen—ALL FIXED AND POLISHED.**

### PHASE 1: INTEL DROP - KNOWN FATAL FLAWS (ROASTED)
- **THUMBNAILS PRE-INIT CRASH**: `pygame.Surface` called at module load **BEFORE** `pygame.init()`. Instant RuntimeError. Move that shit post-init or lazy-load.
- **ENEMY SPAWN APOCALYPSE**: Only worlds 1(G),2(K),3(F),5(S) spawn enemies. Worlds 4(B),6(P),7(M),8(W)? ZILCH. No `elif` branches. `theme["enemy"]` chars ignored → ghost levels.
- **FLAG/ENEMY CHAR COLLISION HELL**: Flag "F" at row14 col95 ALWAYS spawns Fish (world3) or Goomba (others) ON THE FLAG. Player "S" gets OVERRIDDEN by sky "S" enemies → spawns at last "S" (enemy pos). Parsing loop sets player to FINAL "S".
- **ESC KEY STACK OVERFLOW**: `handle()` does `push(new_scene)` instead of `pop()`. Stack explodes: Level → WorldMap → WorldMap → ∞. Proper back-nav: `pop()` EVERYWHERE.
- **HUD OVERLAP SHITSHOW**: Coins & Time BOTH `WIDTH//2 - w//2, y=4`. Texts smash together like drunk Goombas.
- **GAMEOVER WRONG POP**: `pop()` from GameOver → back to *dying LevelScene*. Rig keeps cooking, player ghosted. Need multi-pop or stack reset to FileSelect/Title.
- **NO WIN CONDITION**: World8-4 ends → WorldMap. No "CONGRATS" fireworks. Princess unsaved forever.
- **DEAD FEATURES**:
  - Coins displayed but NEVER increment. `state.coins` = eternal 00.
  - `?` blocks: Visual only. No coins/mushrooms/powerups on hit.
  - `self.mushrooms = []`: Defined, unused. Zombie code.
  - Mushrooms make Mario big? Nope.
  - Time runs out? Nada—ghost through.
  - Invincibility: Blinks but no starman logic.
  - Koopa `shell_mode`: Defined, never triggered (no shell kick).
  - No sound/FX (ok for base, but stub ready).
  - Procedural levels: Platforms/pipes/blocks can overlap destructively (rare, but fix collisions).
- **COLLISION JANK**: Sequential collider loop → tunneling thru walls/multi-hit pushback. Edge cases: player clips pipes, enemies phase.
- **BIG MARIO VISUAL MISMATCH**: Entity `height=16`, but draw spans ~32px. Looks squished/stretched.
- **NO FLAGPOLE WIN POSE**: End-level: Boring x>end. Add flag slide-down, score bonus, Mario victory dance.
- **SAVE SYSTEM WEAK**: Progress saves *selected* world, not *cleared*. Unlocked ok, but polish.
- **PERF/EDGE**: Cam clamps ok, but fast right-run skips end. Time float ok. No pause/death anim.
- **RANDOM SEED**: Levels regenerate different each run. Seed for consistency? Optional.

### PHASE 2: EXECUTION ORDERS
1. **ANALYZE FULLY**: Run mentally/simulate. Find HIDDEN bugs (e.g., water Fish no bounds → offscreen forever; Spike static ok; Goomba edge-detect 1px lookahead fails on slopes).
2. **FIX HIERARCHY**:
   - **CRASHES FIRST**: Init order, pre-init code.
   - **CORE LOGIC**: Enemies spawn via `theme["enemy"]` → `enemy_char_to_class` dict. **NO CHARS IN TILE DATA FOR ENEMIES/START/FLAG**. Generate `levels = {id: {"tiles": list[str], "enemies": [(x,y,type), ...], "start_x":5}}`. Parse NO chars for enemies/player. Player fixed row14* TILE, col5*TILE. Flag: Draw at fixed end, interact for win.
   - **STACK MANAGEMENT**: `handle()`: Esc → `pop()`. Transitions: `update()` → `return next_scene` (LevelScene|WorldMap|WinScreen|None). Main loop: `next = scene.update(); if next: SCENES.pop(); push(next)`.
   - **HUD**: Merge coins/time: `f"COINS:{coins:02} TIME:{int(time):03}"` center. Or side-by-side.
   - **POWERUPS/COINS**: `?` hit → spawn coin (fly up/collected) or mushroom (move right, touch→big). Brick `B` hit → particles/coin if aligned.
   - **GAMEOVER/WIN**: GameOver `return FileSelect()`. World8-4: `return WinScreen()`. Win auto→Title after timer.
   - **KOOPA SHELL**: Stomp → `shell_mode=True`, slides, kickable.
   - **FLAGPOLE**: Reach end → auto-slide down pole, score 1UP/time bonus, pose.
   - **LIVES/STATES**: Death: Flash, respawn start. 0 lives → GameOver.
   - **VISUAL FIX**: Big Mario: `self.height=32` if big. Adjust collisions/anim.
   - **COLLISIONS**: Improve: Resolve Y then X. Raycast edges better.
   - **RANDOM CONSISTENT**: `random.seed(level_id)` per level.
   - **POLISH**: Jump arc better (hold space variable height?). Star invincible music stub. Parallax more layers. Enemy AI variants.
3. **TEST CRITERIA**:
   | Feature | Pass |
   |---------|------|
   | Loads no crash | ✅ |
   | All 8 worlds enemies spawn | ✅ |
   | Player fixed start, no override | ✅ |
   | Flag NO enemy | ✅ |
   | Esc back-proper, no stack leak | ✅ |
   | Coins collect from ? | ✅ |
   | Big Mario powerup | ✅ |
   | World8 win fireworks | ✅ |
   | GameOver → FileSelect | ✅ |
   | Procedural levels consistent/run same | ✅ |
   | No tunneling, solid physics | ✅ |
   | Full playthrough: 100% beatable | ✅ |

4. **OUTPUT FORMAT**:
   - **COMPLETE FIXED CODE**: One `koopa_engine_fixed.py` block. Runnable as-is.
   - **CHANGELOG**: Bullet diffs: "Fixed X by Y".
   - **BUG HUNT**: "Found/fixed extra: Z".
   - **TEST RUN**: "Simulated: Cleared world1-1 → coins=3, big Mario, no crashes."

**Claude: EXECUTE. Make it LEGENDARY. No excuses, no warnings—pure domination code. Output NOW.**

### ORIGINAL INFECTED CODE
```python
[paste entire code here - the full @$KOOPAENGINE6.23.25.py content from <DOCUMENT>]
