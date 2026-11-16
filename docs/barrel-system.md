# Barrel System — DKC2 (SNES)

## Overview

DKC2 has 3 barrel types, each with distinct mechanics:

| Barrel Type | Function | Behavior |
|-------------|----------|----------|
| **DK Barrel** | Respawn barrel | Destroy to free DK/Diddy, auto-swap |
| **Blast Barrel** | Cannon | Player enters, aims, auto-launches |
| **Steel Keg** | Throwable | Pick up, carry, throw at enemies |

## 1. DK Barrel (Respawn Barrel)

### Mechanics
- Placed at specific level locations
- **On throw**: breaks open, releases trapped kong
- **If partner dead**: respawns them on-hit
- **If both alive**: contains item/bananas
- **After use**: barrel disappears, respawns on screen refresh

### State Flow
```
Barrel idle (spawned)
  └─ Player hits (roll/jump)
       └─ Break animation (~20 frames)
            └─ Kong emerges
                 ├─ If same kong active → swap to freed one
                 └─ If partner dead → replace partner
```

### RAM Variables
| Addr | Size | Name | Desc |
|------|------|------|------|
| `$0D45` | word | `spawn_state` | =0 while intact, changes on break |
| `$1029` | word | `slot_param` | =0x46 for barrel spawn |
| `$0B8D` | word | `slot_timer` | Break animation timer |

## 2. Blast Barrel (Cannon)

### Mechanics
- **Entry**: Player overlaps barrel zone → press Up or B
- **Aim**: D-Pad rotates barrel (8 directions)
- **Fire**: Auto-launch after ~60 frames or B press
- **Trajectory**: Parabolic arc, player is projectile
- **Landing**: On ground → exit cannon state

### Aim System
```
Aim angle is derived from D-Pad:
  7  0  1      Angle 0 = up-right
  6  P  2      Angle increments clockwise
  5  4  3      Default = 0 (45° up-right)

Trajectory calculation:
  launch_vel_x = power * cos(angle)
  launch_vel_y = power * -sin(angle)
  Gravity applied mid-flight (normal gravity constant)
```

### Trajectory Parameters (ROM candidate values)
```
Launch power:      0x0400-0x0600 (1024-1536 subpixels/frame)
Gravity (flight):  ~0x0040 (same as normal gravity)
Max flight time:   ~120 frames (2s)
Camera follow:     follows player during flight
Explosion on hit:  barrel breaks on terrain/enemy hit
```

### State Flow
```
Player overlaps barrel zone
  └─ Press Up/B → state = BARREL (0x0A)
       └─ Enter animation (~16 frames)
            └─ Aim phase (~60 frames max)
                 ├─ D-Pad → aim angle
                 ├─ B → fire early
                 └─ Timer expires → fire auto
                      └─ Flight phase
                           ├─ Gravity applied each frame
                           ├─ Collision check vs terrain
                           ├─ Collision check vs enemies
                           └─ On land → explosion → exit state
```

### RAM Variables (Barrel-specific)
| Addr | Size | Name | Desc |
|------|------|------|------|
| `$0D36` | byte | `player_state` | = 0x0A when in barrel |
| `$0D34` | word | `vel_x` | Launch velocity X |
| `$0D35` | word | `vel_y` | Launch velocity Y |
| `$0D30` | word | `pos_x` | Flight position X |
| `$0D32` | word | `pos_y` | Flight position Y |
| `$0D44` | byte | `aim_angle` | 0-7, Barrel aim direction |
| `$1029` | word | `slot_param` | Flight timer |

## 3. Throwable Barrels (Steel Keg / TNT)

### Mechanics
- **Pick up**: Walk over barrel → press Y
- **Carry**: Walk slowly while holding, use as shield
- **Throw**: Press Y again → lob forward
- **On hit**: Barrel breaks, damages enemies
- **TNT**: Same mechanics but explodes after timer

### Carry Physics
```
While holding:
  Move speed:    ~0x0018 (24, ~50% of walk speed)
  Jump height:   ~0xFC80 (reduced jump)
  Throw vel X:   ~0x0100 (256 forward)
  Throw vel Y:   ~0xFE00 (-512 up)
  Can roll:      yes (barrel rolls with player)
```

### Barrel Object Data

From ROM analysis, barrel objects in bank BD handler entries include:

```
typedef struct {
    u16 x_pos;              // World position
    u16 y_pos;
    u16 vel_x;              // Movement
    u16 vel_y;
    u16 state;              // 0=idle, 1=breaking, 2=carried, 3=thrown
    u16 timer;              // Life/fuse timer
    u16 collision_flags;    // What it can hit
    u16 anim_frame;         // Current animation frame
} BarrelObject;
```

## DKC2-Specific Barrel Features

### Barrel Patterns (unique to DKC2)
- **Targeting reticle**: Blast barrels show 8-directional arrow
- **Barrel chains**: Sequences of blast barrels in levels like "Barrel Shield Bust-Up"
- **Kong swap**: Breaking DK barrel = auto character swap
- **Steel keg puzzles**: Some puzzles require keg on switch

### Level Data Integration
Barrels are placed in level data as sprite objects with specific spawn
types. The area init (`$C0A14B`) configures barrel spawn positions
from level tile data. Each barrel type has a unique type ID in the
object dispatch table.
