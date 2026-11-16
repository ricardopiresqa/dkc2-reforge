# Player Controller — DKC2 (SNES)

## Architecture Overview

Player controller is split across 2 CPUs:

```
SNES CPU (bank C0)                SA-1 CPU (banks BA, BB, BC, BD)
  ├─ Input read ($C0A252/C0C15A)   ├─ Object dispatch (BD jump table at $BD8000)
  ├─ NMI slot dispatch              ├─ Player physics/state
  ├─ State machine ($C09BE7)        ├─ Collision detection
  └─ Camera/scroll                  └─ AI processing
```

The 32-entry jump table at `$BD8000` dispatches to object-specific handlers in bank BD. Each entry is a 16-bit offset within bank BD.

## BD Object Dispatch Table

| Entry | SNES Addr | Handler | Likely Object |
|-------|-----------|---------|---------------|
| 0 | `$BD8000` | `$BD4BE2` | Null/empty object |
| 1 | `$BD8002` | `$BD4C1F` | Player (DK/Diddy) |
| 2 | `$BD8004` | `$BD4C52` | Unk object type 2 |
| 3 | `$BD8006` | `$BD4C8A` | Unk object type 3 |
| 4 | `$BD8008` | `$BD4CC9` | Unk object type 4 |
| 5 | `$BD800A` | `$BD4D05` | Unk object type 5 |
| 6 | `$BD800C` | `$BD4D48` | Unk object type 6 |
| 7 | `$BD800E` | `$BD4D71` | Unk object type 7 |
| 8 | `$BD8010` | `$BD4DB8` | Unk object type 8 |
| 9 | `$BD8012` | `$BD4DF4` | Unk object type 9 |
| 10-31 | `$BD8014+` | various | Remaining object types |

### Object Handler Data Format

Each handler entry at `$BDxxxx` contains structured data:

```
typedef struct {
    u16 field_00;
    u16 field_02;
    u16 field_04;
    u16 field_06;   // sprite type id?
    u16 field_08;   // behavior flags?
    u16 field_0A;   // speed/vel X
    u16 field_0C;   // speed/vel Y
    u16 field_0E;   // acceleration?
    // ... more fields, format varies by type
} ObjectDef;
```

Entry 0 (`$BD4BE2`): null handler, mostly zeros.
Entry 1 (`$BD4C1F`): Player handler (DK/Diddy), contains behavior data.

## Player States

Based on RAM analysis and ROM data, DKC2 player uses these states:

### Ground States
| State | Desc | Transition To |
|-------|------|---------------|
| **Idle** | Standing still, facing direction | Run (D-Pad), Roll (Y), Jump (B), Crouch (Down) |
| **Run** | Horizontal movement, 2 speeds | Idle (release), Jump (B), Roll (Y), Skid (reverse) |
| **Crouch** | Down + idle, reduced hitbox | Idle (release), Roll (Y→release) |
| **Skid** | Quick reverse direction | Run (opposite dir), Idle (release) |
| **Roll** | Y button, invincible roll attack | Idle (ends), Run (button during) |

### Air States
| State | Desc | Transition To |
|-------|------|---------------|
| **Jump** | B press, height varies by hold | Fall (apex), Roll (land), Idle (land) |
| **Double Jump** | Jump again mid-air (Diddy only) | Fall (apex2), Land |
| **Fall** | Descending after jump/from ledge | Land |
| **Land** | 1-frame transition on ground contact | Idle/Run (next frame) |

### Special States
| State | Desc | Transition To |
|-------|------|---------------|
| **Climb** | On rope/vine (Up/Down) | Idle (release), Jump (B) |
| **Swim** | Underwater | Surface, Land |
| **Barrel** | Inside barrel cannon | Launch (auto), Exit |
| **Team Throw** | Pick up partner | Idle (throw), Roll |

## Player Physics (ROM-derived candidate values)

### Movement Parameters (Candidates from bank C0)
```
Walk speed:       ~0x0030 (48 subpixels/frame)
Run speed:        ~0x0050 (80)
Roll speed:       ~0x0080 (128)
Gravity:          ~0x0030-0x0040 (48-64 per frame^2)
Jump velocity:    ~0xFC00-0xFD00 (-1024 to -768, signed)
Double jump vel:  ~0xFE00 (-512, Diddy only)
Terminal vel:     ~0x0400 (1024, max fall speed)
Friction:         ~0x0004-0x0008 (decel when no input)
Skid decel:       ~0x0010 (quick stop when reversing)
```

### Jump Mechanics
- **Variable height**: B hold extends jump, gravity reduced while rising
- **Diddy double jump**: Bonus jump mid-air with reduced height
- **Roll jump**: Roll off ledge preserves momentum upward
- **Water jump**: Reduced gravity, slower ascent

### Collision Constants
```
Player width:     ~0x0010 (16 pixels)
Player height:    ~0x0018 (24 pixels standing)
Crouch height:    ~0x0010 (16 pixels)
Grounded check:   test tile below feet (1px)
Ledge grab:       fall-off timer ~0x0005 (5 frames grace)
```

## SRAM Variables (Player-specific)

From ROM analysis + RAM map:

| WRAM Addr | Size | Name | Desc |
|-----------|------|------|------|
| `$0D30` | word | `pos_x` | Absolute X position (pixels) |
| `$0D32` | word | `pos_y` | Absolute Y position |
| `$0D34` | word | `vel_x` | Signed X velocity (subpixels/frame) |
| `$0D35` | word | `vel_y` | Signed Y velocity |
| `$0D36` | byte | `state` | Current player state ID |
| `$0D44` | byte | `direction` | Facing: 0=right, 1=left |
| `$0D5C` | word | `health` | Current HP |
| `$0D7E` | byte | `bananas` | Banana count |
| `$0D11` | word | `slot_flag` | Slot enable/active flag |
| `$0AE5` | word | `slot_flag_b` | Secondary slot flag |
| `$0B19` | word | `slot_x` | Slot X (camera-relative?) |
| `$0BC1` | word | `slot_y` | Slot Y |
| `$1029` | word | `slot_param` | Slot parameter/timer |
| `$0B8D` | word | `slot_timer` | Slot lifetime timer |
| `$0C69` | word | `attr_flags` | Attribute bitmask |

### State ID Values (Speculative)
```
0x00 = Null/inactive
0x01 = Idle
0x02 = Run
0x03 = Jump (rising)
0x04 = Fall
0x05 = Roll
0x06 = Crouch
0x07 = Skid
0x08 = Climb
0x09 = Swim
0x0A = Barrel
0x0B = Team throw
0x0C = Damage knockback
0x0D = Death
```

## State Transition Diagram

```
                      ┌─────────────┐
                      │   IDLE      │◄──────────┐
                      │  (state 1)  │            │
                      └──┬──┬──┬───┘            │
             ┌───────────┘  │  │                 │
             ▼              ▼  ▼                  │
        ┌─────────┐   ┌─────────┐   ┌─────────┐  │
        │  RUN    │   │ CROUCH  │   │  JUMP   │  │
        │ (state2)│   │ (state6)│   │ (state3)│  │
        └──┬──────┘   └──┬──────┘   └──┬──────┘  │
           │             │             │         │
           │      ┌──────┘             │         │
           ▼      ▼                    ▼         │
        ┌─────────────┐          ┌─────────────┐  │
        │    SKID     │          │    FALL     │  │
        │  (state 7)  │          │  (state 4)  │  │
        └──────┬──────┘          └──────┬──────┘  │
               │                        │         │
               ▼                        ▼         │
        ┌─────────────┐          ┌─────────────┐  │
        │    ROLL     │          │   LAND      │──┘
        │  (state 5)  │          │  (implicit) │
        └─────────────┘          └─────────────┘
```

## SA-1 Interaction

Player physics runs on SA-1 via object dispatch:
1. SNES toggles `$82` (0/6) each NMI → selects active slot
2. SA-1 reads slot state from `$0512,Y`
3. SA-1 dispatches to bank BD handler based on object type
4. Handler updates position, velocity, state from slot data
5. Result stored back to `$0512` for SNES to read next frame

This allows 65816 code in bank BD/BB/BC to process player physics,
collision, and animation on the coprocessor while SNES handles
rendering and input.
