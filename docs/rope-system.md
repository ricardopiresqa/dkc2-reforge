# Rope System — DKC2 (SNES)

## Overview

DKC2 features unique rope/vine climbing mechanics distinct from DKC1.
Ropes are vertical climbable surfaces where the player can ascend,
descend, and jump off.

## Architecture

Rope handling is part of the SA-1 object system:

```
SA-1 Object Dispatch
  └─ Rope object type (bank BD handler)
       ├─ Collision detection (player ↔ rope)
       ├─ Climb state management
       ├─ Animation control
       └─ Disconnect detection
```

Ropes use a **zone-based collision** model:
- Rope collider is a vertical strip (~16px wide)
- Player enters climb state when overlapping rope zone + pressing Up/Down
- While climbing, player position snaps to rope X

## Rope Object Data (ROM Bank BD)

From the BD dispatch table at `$BD8000`, specific rope-handler entries
process climb logic. Each rope in the level is a sprite slot with:

```
typedef struct {
    u16 type_id;           // Rope = specific type in [2..5]
    u16 x_position;        // Rope center X
    u16 y_top;             // Top of rope (world Y)
    u16 y_bottom;          // Bottom of rope (world Y)
    u16 width;             // Collision width (~16px)
    u16 flags;             // Behavior flags
    u16 timer;             // Animation timer
} RopeObject;
```

## Climb Mechanics

### Entering Climb State
```
Player overlaps rope zone
  AND (Up pressed OR Down pressed)
    → state = CLIMB (0x08)
    → snap player X to rope center X
    → reset vel_x/vel_y to zero
    → set climb animation
```

### Climbing
```
Up pressed:    vel_y = -climb_speed (~-0x0020)
Down pressed:  vel_y = +climb_speed (~0x0020)
No input:      vel_y = 0 (grip, no sliding)
```

### Disconnecting
```
Release:      if no D-Pad vertical → check inputs next frame
Jump (B):     exit climb state → enter JUMP/FALL with vel_y = -jump_vel
Lateral move: if clear of rope sides → enter FALL
Enemy hit:    knockback → enter FALL
Leaving zone: auto-detect via collision bounds
```

### Climb Parameters (ROM candidate values)
```
Climb speed up:    0x0020 (32 subpixels/frame ≈ 2 px/frame)
Climb speed down:  0x0030 (48)
Jump from rope:    0xFC00 (-1024, same as ground jump)
Rope collision:    16px wide, variable height
Snap threshold:    ~8px from rope center
```

## Rope Types in DKC2

| Type | Desc | Behavior |
|------|------|----------|
| **Chain** | Vertical chain links | Climb only (no swing), metallic look |
| **Vine** | Thick jungle vine | Climb + subtle sway animation |
| **Rope** | Standard hemp rope | Climb, wider collision |
| **Peg** | Wooden peg on wall | Grip point, no vertical movement |

## Multi-Rope Levels

Some levels (e.g., Barrel Shield Bust-Up, Rope Bridge Rumble) feature
sequences of ropes. The engine handles:
- **Rope-to-rope jump**: Player can jump from one rope to adjacent one
- **Rope spacing**: ~48-64px horizontal gap for plausible jumps
- **Chain zipline**: Some horizontal ropes act as ziplines

## RAM Variables (Climb-specific)

| WRAM Addr | Size | Name | Desc |
|-----------|------|------|------|
| `$0D36` | byte | `player_state` | State = 0x08 when climbing |
| `$0D34` | word | `vel_x` | Forced to 0 while climbing |
| `$0D35` | word | `vel_y` | Climb speed (signed) |
| `$0D30` | word | `pos_x` | Snapped to rope center |
| `$11A1` | word | `slot_flag_c` | Climb grip flag (non-zero = on rope) |

## Animation States

| State | Frame | Desc |
|-------|-------|------|
| Idle grip | 0 | Holding rope, no movement |
| Climb up | 1-3 | Ascending hand-over-hand |
| Climb down | 3-1 | Descending (reverse sequence) |
| Jump off | 4 | Leap away from rope |

## Edge Cases

- **Rope at screen edge**: Player can still climb, camera adjusts
- **Rope + hazard**: Some ropes have spikes at bottom → auto-release
- **DK/Diddy differences**: Both climb identically (no speed diff)
- **Water rope**: Underwater ropes have reduced climb speed
