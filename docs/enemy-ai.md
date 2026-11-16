# Enemy AI — DKC2 (SNES)

## Architecture

Enemy AI runs on the SA-1 coprocessor via the object dispatch system
in bank BD. Each enemy type has a dedicated handler in the 32-entry
jump table at `$BD8000`.

```
Level Data
  └─ Sprite spawner sets type + position
       └─ SA-1 object dispatch (table at $BD8000)
            └─ Enemy-type handler (bank BD $4xxx-$5xxx)
                 ├─ Init routine (set params)
                 ├─ Update routine (called each frame)
                 │    ├─ Patrol logic
                 │    ├─ Aggro check
                 │    ├─ Attack execution
                 │    └─ Collision response
                 └─ Death routine
```

## Enemy Types in DKC2

| ID | Enemy | Behavioral Pattern |
|----|-------|-------------------|
| 1 | Kritter | Patrol left-right, stop at edge |
| 2 | Klobber | Patrol, charges when facing player |
| 3 | Klump | Patrol, throws projectiles |
| 4 | Krusha | Stationary, pound ground on approach |
| 5 | Kaboing | Hop in arc, bounces off walls |
| 6 | Kannon | Stationary cannon, fires at intervals |
| 7 | Zinger | Flying, sinusoidal patrol path |
| 8 | Flitter | Flying, follows player Y |
| 9 | Clambo | Stationary, shoots bubbles/spikes |
| 10 | Lockjaw | Water patrol, horizontal |
| 11 | Screech | Flying boss, swoop attack |
| 12 | Kutlass | Patrol, swings sword |
| 13 | Kroc | Stationary, shoots fireballs |
| 14 | Coin | Collectible (not enemy) |
| 15 | Banana Bunch | Collectible cluster |
| 16-31 | Other | Misc objects (barrels, ropes, etc.) |

## AI State Machine

Each enemy has a 3-state AI core:

```
              ┌─────────┐
              │  PATROL │◄────────────────┐
              │ (state0)│                  │
              └────┬────┘                  │
                   │ player in range        │
                   ▼                        │
              ┌─────────┐                  │
              │  AGGRO  │                  │
              │ (state1)│                  │
              └────┬────┘                  │
                   │ attack condition       │
                   ▼                        │
              ┌─────────┐                  │
              │ ATTACK  │                  │
              │ (state2)│──────────────────┘
              └─────────┘  (cooldown/return)
```

### State 0: Patrol
```
Default behavior:
  └─ Move at patrol_speed in current direction
  └─ On edge (no ground ahead) → reverse direction
  └─ On wall collision → reverse direction
  └─ On aggro trigger → switch to AGGRO

Patrol parameters (per enemy type):
  patrol_speed:   ~0x0010-0x0040 subpixels/frame
  patrol_range:   ~64-256 pixels (some enemies patrol full platform)
  edge_detect:    1-2 pixels ahead, 1-2 pixels below
```

### State 1: Aggro
```
Player detection:
  └─ Check distance: |player_x - enemy_x| < aggro_range
  └─ Check line-of-sight: same platform, no walls between
  └─ Face player direction

Aggro parameters:
  aggro_range:    ~128-256 pixels (varies by type)
  charge_speed:   ~0x0080-0x0180 (2-6x patrol speed)
  turn_rate:      immediate (instant direction flip)
```

### State 2: Attack
```
Attack execution:
  └─ Execute type-specific attack (contact, projectile, charge)
  └─ Attack animation plays
  └─ On hit player → damage + knockback
  └─ On miss/end → cooldown timer
  └─ Cooldown expires → return to PATROL

Attack parameters:
  damage:         ~1-2 HP per hit
  knockback:      ~0x0100-0x0300 launch velocity
  stun_frames:    ~15-30 frames (player invincible after hit)
  cooldown:       ~30-90 frames between attacks
```

## Enemy Data Format (ROM Bank BD)

From BD dispatch table entries, each enemy handler stores:

```
typedef struct {
    u16 type_id;            // Object type
    u16 x_position;         // World X
    u16 y_position;         // World Y
    u16 vel_x;              // Signed velocity X (patrol/charge)
    u16 vel_y;              // Signed velocity Y (gravity/jump)
    u16 ai_state;           // 0=patrol, 1=aggro, 2=attack
    u16 ai_timer;           // State timer (cooldown counter)
    u16 direction;          // Facing (0=right, 1=left)
    u16 health;             // HP (most enemies = 1 hit)
    u16 collision_flags;    // What it collides with
    u16 anim_frame;         // Current animation
    u16 spawn_flags;        // Level spawn config
} EnemyObject;
```

### Enemy-Specific Data (ROM candidates)

From data regions near BD handlers:

**Kritter (type 1)** at BD $4C00:
```
Patrol speed:   0x0002 (2 subpixels/frame)
Aggro range:    0x0028 (40 pixels)
Edge sensitivity: 0x08 (8 pixels from edge)
Animation delay: 0x04 (frames per frame)
```

**Klobber (type 2)** at BD $4C52:
```
Patrol speed:   0x0002
Charge speed:   0x00F0 (240)
Aggro range:    0x0071 (113)
Charge duration: 0x0A (10 frames)
```

**Klump (type 3)** at BD $4C8A:
```
Patrol speed:   0x0002
Projectile speed: 0x02F0 (752)
Fire interval:  0x0028 (40 frames)
Projectile type: barrel/cannonball
```

## Collision System

### Player vs Enemy
```
Check bounds overlap:
  └─ If player rolling → enemy dies (roll attack)
  └─ If player jumping → enemy dies (stomp)
  └─ If player normal → player takes damage
       └─ Knockback direction: opposite of facing
       └─ Invincibility frames: ~30 frames
       └─ Health decrement: 1 HP (2 with DK)
```

### Enemy vs Terrain
```
  └─ Wall collision → reverse direction
  └─ Edge detection → reverse at platform edge
  └─ Ceiling collision → reverse (flying enemies)
  └─ Water entry → special behavior (some enemies die, some swim)
```

### Player Invincibility
```
After hit:
  └─ Set invincibility flag (WRAM $0D7E bit?)
  └─ Flash animation (blink every 4 frames)
  └─ Duration: ~30 frames (0.5s)
  └─ Cleared after: duration expires OR death
```

## SA-1 AI Processing

Enemy AI executes on SA-1 during slot dispatch:

```
1. SNES sets $0512,Y = current slot state
2. SA-1 reads slot index, object type
3. SA-1 dispatches via BD table to type handler
4. Handler:
   a. Apply gravity (bank BB/BC gravity tables)
   b. Collision vs terrain (bank BC collision)
   c. AI state update (patrol/bait/attack)
   d. Write updated position/vel to slot data
5. SA-1 returns, SNES reads result
```

This decoupling allows 32 enemy handlers to process simultaneously
on the co-processor while SNES handles rendering.

## RAM Variables (Enemy Slots)

Enemy slots share the same array system as player:

| WRAM Addr | Name | Desc |
|-----------|------|------|
| `$0AB1` | `sprite_prop_array` | Per-slot property flags |
| `$0AE5` | `slot_flag_array` | Per-slot flag (active/inactive) |
| `$0D11` | `slot_enable_array` | Enable state |
| `$0E89` | `slot_misc_array_1` | AI state storage |
| `$0EF1` | `slot_misc_array_2` | Secondary AI storage |
| `$1B17` | `state_machine_var_a` | Global AI state index |
| `$1B19` | `state_machine_var_b` | Global AI param |

Slot stride = 6 bytes per array, indexed by `$82` (0 or 6).
Multiple enemy slots = multiple stride instances.
