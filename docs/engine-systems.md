# Engine Systems — DKC2 (SNES)

## System Architecture Overview

```
Reset ($C08000)
  └─ Init ($C0A8CF) ──► Idle (WAI/BRA @ $C0C0B4)
                              │
                         NMI fires (60fps)
                              │
                              ▼
                    ┌─────────────────────┐
                    │  NMI Handler        │
                    │  ($C08916)          │
                    │                     │
                    │  1. Save context    │
                    │  2. Toggle $82 (0↔6)│
                    │  3. Set slot timer  │
                    │  4. SA-1 dispatch   │
                    └─────────────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │  Slot Dispatch      │
                    │  ($C0852D)          │
                    │                     │
                    │  Reads $0512 slot   │
                    │  state → dispatches │
                    │  via game_phase     │
                    └─────────────────────┘
```

## 1. Main Game Loop (Physics Tick)

### Frame Sequence
Each NMI (16.67ms at 60fps):

```
$C08916 (NMI):
  └─ JSR $852D          ; save context (DP regs, SNES state)
  └─ LDA $82 → EOR #6   ; toggle frame_index (0 or 6)
  └─ STA $82
  └─ LDA $82 → DEC/DEC  ; $84 = $82 - 2 (partner index)
  └─ JSR $8559          ; SA-1 sync: JSL $B8822B
  └─ LDX $82
  └─ LDA #$00D8
  └─ STA $0B8D,X        ; set slot timer
  └─ RTI
```

### Slot Dispatch ($C0852D)
```
$C0852D:
  └─ LDX $82               ; current slot index
  └─ LDA $82 → DEC/DEC     ; Y = $84 (other slot)
  └─ LDA $0512,Y           ; read previous frame's dispatch result
  └─ if Z:                  ; slot was idle
  │    └─ LDA #$0030 → STA $1029,X   ; parameter = 0x30
  │    └─ JMP $862C        ; dispatch to handler
  └─ if NZ:                 ; slot has work
       └─ LDA #$002B → STA $1029,X   ; parameter = 0x2B
       └─ JSL $BE80A4      ; far call (bank BE)
       └─ LDA #$00E4 → STA $0B8D,X   ; set timer
```

### Game Phase Dispatch ($C08687)
```
$C08687:
  └─ LDA $0516     ; global game state
  └─ CMP #9  ───► Y = $885F  (State 9:  title/demo?)
  └─ CMP #$A ───► Y = $888B  (State A: unknown)
  └─ CMP #$B ───► Y = $88B0  (State B: SA-1 dispatched)
  └─ CMP #$C ───► Y = $88E3  (State C: gameplay init)
  └─ default  ──► Y = $885F
```

### Dispatch Call ($C0862C)
```
$C0862C:
  └─ PHY / PHX          ; save slot context
  └─ JSR $8687          ; dispatch → Y = handler address
  └─ JSL $B5804C        ; execute handler on SA-1
  └─ PLX / PLY          ; restore context
  └─ LDA $86
  └─ STA $0512,Y        ; store result to slot array
```

### State Handlers

| Phase | Handler | Description |
|-------|---------|-------------|
| 9 ($885F) | TBD | Title/demo loop |
| A ($888B) | STA $0C69,Y; STA $1929=1 | Sets state A result, flags as active |
| B ($88B0) | RTS | No-op placeholder |
| C ($88E3) | JSR $85B8 → toggle $82 → JSR $855E → JMP $88F9 | Init frame, swap slot, chain to SA-1 |

### SA-1 Shared Handler ($C088F9)
```
$C088F9:
  └─ LDA $3E           ; SA-1 internal state
  └─ CMP #$38 ────► LDY #$8DF9 ──► JSL $B5804C  ; table A
  └─ CMP #$3B ────► LDY #$8E21 ──► JSL $B5804C  ; table B
  └─ default: RTS
```

The tables at `$8DF9` / `$8E21` contain inline 65816 code executed by SA-1.

## 2. Camera / Scroll System

### Camera Setup ($C0A14B — Area Init)

```
$C0A14B:
  └─ JSL $B88347              ; far init (level data load)
  └─ LDA #$0200 → STA $8E    ; camera boundary X?
  └─ LDA #$0400 → STA $6E    ; camera boundary Y?
  └─ STZ $0400-$041E          ; clear camera/scroll vars (16 words)
  └─ LDA $32                  ; check submode
  └─ CMP #4
  │   └─ if Z: submode 4 path (menu/overworld)
  │   │   └─ LDA $1DF1       ; check flag
  │   │   └─ if Z:  $3C = 0x14
  │   │   └─ if NZ: $3C = 0x2C
  │   └─ if NZ: gameplay path
  │       └─ LDA $0535       ; flag check
  │       └─ if NZ:
  │       │   └─ JSR $A4FA   ; init processes
  │       │   └─ JSR $A33C   ; init more
  │       │   └─ JSL $B8B52C ; far engine init
  │       │   └─ JSL $B8870B ; far objects init
  │       │   └─ JSL $BBA849 ; far collision init
  │       │   └─ JMP $A494   ; continue
  │       └─ if Z: (camera follow setup)
  │           └─ LDX $1E45   ; load player slot
  │           └─ LDA $0B19,X ; player X
  │           └─ SBC $088B   ; - camera scroll X
  │           └─ STA $76     ; → relative X
  │           └─ LDA $4A    ; player Y
  │           └─ SBC $0BC1,X ; - slot Y
  │           └─ SBC $0895   ; - camera scroll Y
  │           └─ STA $77     ; → relative Y
  │           └─ LDX $76
  │           └─ LDY $8E
  │           └─ JSL $BCB38E ; camera clamp/move
  │           └─ STY $8E     ; update boundary
```

### Scroll Registers ($C08E87 — VBlank/Fade)

```
$C08E87:
  └─ Writes BG1 scroll X ($2111) from $088B
  └─ Writes BG1 scroll Y ($2110/$2112) from $0895
     - Clamps at 0x011F (max scroll)
     - Uses hardware scroll registers with HW scaling (>>3)
  └─ Reads $1E15 (screen mode flags)
     └─ If bit 3 set: configures color math ($212C/$2130)
     └─ If bit 2 set: fade effect via CGRAM ($2121/$2122)
         - Decrements $1E1D (fade timer)
         - Writes palette from $808F1D table
  └─ Color math on/off toggle via $212C/$2130
```

### Camera Memory Map

| Address | Size | Description |
|---------|------|-------------|
| $088B | 2 bytes | BG1 scroll X (camera X position) |
| $0895 | 2 bytes | BG1 scroll Y (camera Y position) |
| $8E | 2 bytes | Camera boundary X (viewport width) |
| $6E | 2 bytes | Camera boundary Y (viewport height) |
| $76 | 2 bytes | Player relative X (camera target offset) |
| $77 | 2 bytes | Player relative Y (camera target offset) |
| $0400-$041E | 32 bytes | Camera/scroll variables (16 words cleared on area init) |
| $1E15 | 2 bytes | Screen mode flags (bit 3=color math, bit 2=fade) |
| $1E1D | 2 bytes | Fade timer counter |
| $0535 | 2 bytes | Camera mode flag |

### Scroll Hardware

| PPU Register | Function | Source |
|--------------|----------|--------|
| $2110 | BG1 scroll Y (high) | $0895 >> 3 |
| $2111 | BG1 scroll X | $088B (scaled: $088B * 1.5) |
| $2112 | BG1 scroll Y (low) | $0896 |

## 3. Sprite / Object Manager

### Sprite Slot System

The engine uses **timed sprite slots** indexed by `$82` (frame_index, toggles 0↔6).

### Sprite Spawner ($C085B8)

Main entry point for creating sprites/objects:

```
$C085B8 (input: A = sprite type ID):
  └─ STA $76               ; save type
  └─ LDX $82               ; current slot
  └─ LDA $82 → DEC/DEC → STA $84
  └─ TAY                   ; Y = other slot
  └─ LDA $0512,Y           ; check if slot active
  └─ if Z: (idle slot)
  │   └─ LDX $82
  │   └─ select param:
  │   │   type=1 → $1029=0x14, timer=0xE4, JSL $BE80A4 (load)
  │   │   type=2 → check $0D45 (slot data)
  │   │            if =2: $1029=0x09
  │   │            if ≠2: $1029=0x01
  │   │   type=3 → $1029=0x46, param=3
  │   │   other  → $1029=0x41, param=2
  │   └─ JSR $862C (dispatch)
  │   └─ LDX $86 (dispatch result)
  │   └─ LDY $82
  │   └─ TYA → STA $1375,X (store slot to spawn)
  │   └─ LDY $82
  │   └─ LDA $0C69,Y → STA $76 (save attr)
  │   └─ transfer attrs with bitmask 0x0E00
  │   └─ copy positions: $0B19 → $0B19, $0BC1 → $0BC1
  │   └─ set timers: $0B8D,Y = 0xDC, $0B8D,X = 0xE4
  │   └─ JSL $BE8092 (sound?)
  │
  └─ if NZ: (busy slot)
      └─ LDX $82
      └─ LDA #$00E4 → STA $0B8D,X (extend timer)
      └─ type-based init:
          type=1 → JSL $BE80A4 (far load)
          type=2 → $1029=0x31, param=3
          type=3 → $1029=0x46, param=2
          other  → $1029=0x41, param=2
```

### Sprite Init Type B ($C0855E)

Alternative init path for "partner" sprites:

```
$C0855E (input: A = type):
  └─ STA $76
  └─ LDX $82 / TAY (Y = other slot)
  └─ LDX $82
  └─ LDA #$00D8 → STA $0B8D,X   ; set timer 0xD8
  └─ LDA $0579                   ; check character flag
  └─ AND #1
  └─ if NZ: (partner mode)
  │   └─ STZ $0D11,X ; STZ $0AE5,X ; STZ $11A1,X  ; clear slot vars
  │   └─ LDA #$000C → STA $1029,X ; param = 0x0C
  └─ if Z: (normal mode)
      └─ type=1 → $1029=0x32, param=3
      └─ type=3 → $1029=0x32, param=2
      └─ other  → $1029=0x32, param=2
```

### Sprite Slot Memory

| Array | Base | Stride | Description |
|-------|------|--------|-------------|
| $1029 | $1029 | 6 | Slot parameter (sprite type/action) |
| $0B8D | $0B8D | 6 | Slot timer (counts down each frame) |
| $0B19 | $0B19 | 6 | Slot X position / state A |
| $0BC1 | $0BC1 | 6 | Slot Y position / state B |
| $0C69 | $0C69 | 6 | Attributes (bitmask 0x0E00 tested) |
| $1375 | $1375 | 6 | Slot spawn reference |
| $0D45 | $0D45 | 6 | Slot data / type check |
| $0D11 | $0D11 | 6 | Slot flag A |
| $0AE5 | $0AE5 | 6 | Slot flag B |
| $11A1 | $11A1 | 6 | Slot flag C |
| $0512 | $0512 | 6 | Dispatch result from $86 |

## 4. Object State Machine

### Main State Machine ($C09BE7)

```
$C09BE7:
  └─ JSR $9BAB          ; pre-state check
  └─ LDA $1929          ; global state flags
  └─ if N set:
  │   └─ AND #1
  │   │   if Z:
  │   │       └─ JSR $9B9B      ; get state pointer
  │   │       └─ LDA $1E29      ; state timer
  │   │       └─ if Z: continue state
  │   │       └─ if NZ: decrement timer, check events
  │   │           └─ LDA $0579   ; flag byte
  │   │           └─ AND $80     ; event bit
  │   │           └─ if NZ: advance state
  │   │               └─ STZ $1B1B
  │   │               └─ LDA #3 → STA $1B17 (state table index)
  │   │               └─ LDA #5 → STA $1B19 (state table param)
  │   │               └─ JSR $9CCB (state transition)
  │   │               └─ JSR $A056 (execute state)
  │   │               └─ JSR $9C8A (cleanup)
  │   │           └─ if Z: (normal state update)
  │   │               └─ XOR $0579 (toggle flag)
  │   │               └─ LDA $1B1B
  │   │               └─ CMP #15 → if Z: increment
  │   │               └─ if NZ: table lookup
  │   │                   └─ ASL / ASL → TAX
  │   │                   └─ LDA table[$9C4A],X → $1B17
  │   │                   └─ LDA table[$9C4C],X → $1B19
  │   └─ if NZ: skip (already processing)
  └─ if N clear: RTS (no state active)
```

### State Machine Memory

| Address | Size | Description |
|---------|------|-------------|
| $1929 | 2 bytes | Global state flags (bit 15 = active, bit 0 = busy) |
| $1E29 | 2 bytes | State timer (countdown) |
| $0579 | 2 bytes | Event flag byte (bit 7 = state trigger) |
| $1B17 | 2 bytes | Current state index (lookup in table at $9C4A) |
| $1B19 | 2 bytes | Current state parameter |
| $1B1B | 2 bytes | State sub-index / counter |

## 5. Input System

### Input Read ($C0C15A)

```
$C0C15A:
  └─ Wait for HBlank ($4212 bit 0 clear)
  │
  └─ LDA $4218               ; joypad 1 data register
  └─ EOR $0500               ; edge detect: XOR with previous hold
  └─ AND $4218               ; mask with current read → rising edge
  └─ STA $0504               ; → edge (newly pressed)
  └─ LDA $4218
  └─ STA $0500               ; → hold (currently pressed)
  │
  └─ Same for joypad 2 ($421A):
  └─ LDA $421A → EOR $0502 → AND $421A → STA $0506 (edge2)
  └─ LDA $421A → STA $0502 (hold2)
  │
  └─ JSR $C0FB               ; serial read from $4016/$4017
  └─ Controller routing:
  │   └─ LDA $42
  │   └─ CMP #2 → route based on $056F (multi-tap flag)
  │   └─ CMP #1 → route based on $44 (player index)
  │   └─ else  → default (port 1)
  │
  └─ Store final to $050E (hold) / $0510 (edge)
```

### Input Memory Map

| Address | Size | Description |
|---------|------|-------------|
| $0500 | 2 bytes | Joypad 1 hold (current frame) |
| $0502 | 2 bytes | Joypad 2 hold |
| $0504 | 2 bytes | Joypad 1 edge (newly pressed this frame) |
| $0506 | 2 bytes | Joypad 2 edge |
| $050E | 2 bytes | Routed hold (active player) |
| $0510 | 2 bytes | Routed edge (active player) |
| $42 | 2 bytes | Controller mode (0=1P, 1=2P, 2=multi-tap) |
| $44 | 2 bytes | Player index for 2P mode |
| $056F | 2 bytes | Multi-tap flag (bit 1 = 5-player adapter) |

### Input Bit Mapping (Standard SNES)

| Bit | Button |
|-----|--------|
| 0 | B |
| 1 | Y |
| 2 | Select |
| 3 | Start |
| 4 | Up |
| 5 | Down |
| 6 | Left |
| 7 | Right |
| 8 | A |
| 9 | X |
| 10 | L |
| 11 | R |

### Serial Read ($C0C0FB)

```
$C0C0FB:
  └─ LDA $0500 (hold1) AND #7 → if NZ:
  │   └─ Serial read $4016 (16 bits) → shift register
  │   └─ Clear $0500/$0504
  └─ LDA $0502 (hold2) AND #7 → if NZ:
      └─ Serial read $4017 (16 bits) → shift register
      └─ Clear $0502/$0506
```

This reads the SNES controller serial protocol directly from $4016/$4017, bypassing the automatic $4218/$421A registers. This suggests multi-tap adapter or special controller support.

## 6. SA-1 Co-Processor System

### Architecture
The SA-1 coprocessor is a second CPU that executes code from the same ROM. The C0 bank orchestrates SA-1 execution:

```
SNES CPU (C0 bank)                SA-1 (Bx banks)
       │                                │
       │  JSL $B5804C ──────────────────►  Execute at Y
       │                                │
       │  (continues after SA-1 done)◄──  RTI/RTL
```

### SA-1 State Dispatch

| $3E value | Handler | Description |
|-----------|---------|-------------|
| 0x0038 | Table at $8DF9 | Physics/object processing? |
| 0x003B | Table at $8E21 | Level processing? |
| other | RTS (no-op) | — |

### SA-1 Banks Referenced

| Bank | Role |
|------|------|
| B5 | SA-1 execution entry ($B5804C) |
| B8 | Area init, sprite init code |
| BC | Camera/movement processing ($BCB38E) |
| BE | Timer/sound utilities ($BE8092, $BE80A4) |
| BA | Object logic? (67 PAC1, code) |
| BC | Object/collision? (80 PAC1, code) |
| BB | Additional logic (17 PAC1, code) |
| BD | Additional engine (21 PAC1, code) |

## 7. Timing & Synchronization

### Frame Budget

| Phase | Cycles (est.) | Description |
|-------|---------------|-------------|
| NMI entry | ~100 | Save regs, toggle slot |
| SA-1 sync ($8559) | ~200 | Wait/distribute to SA-1 |
| Slot dispatch | ~500-2000 | State processing |
| VBlank writes ($C08E87) | ~2000 | Scroll, palettes, color math |
| Total: | ~4000 | (VBlank = ~2273 scanlines × 4 cycles = ~9092 usable) |

### Timer System

- Slot timer (`$0B8D`): counts down each frame from preset value
  - 0x00D8 = 216 frames (~3.6s)
  - 0x00DC = 220 frames (~3.67s)
  - 0x00E4 = 228 frames (~3.8s)
- State timer ($1E29): counts down during state machine operations
- Fade timer ($1E1D): controls palette fade duration

## Function Reference

| Address | Name | System | Description |
|---------|------|--------|-------------|
| $C08916 | NMI | Core | Main interrupt handler, toggles $82 |
| $C0852D | NMI_Slot | Core | Slot context save/dispatch |
| $C08687 | PhaseDispatch | Core | Route $0516 → handler address |
| $C0862C | DispatchCall | Core | Save context, JSR dispatch, JSL SA-1 |
| $C085B8 | SpriteSpawn | Object | Spawn sprite by type ID |
| $C0855E | SpriteInit | Object | Init partner/alt sprites |
| $C08559 | SASync | SA-1 | JSL $B8822B sync point |
| $C088F9 | SAShared | SA-1 | Dispatch SA-1 table by $3E |
| $C0C15A | InputRead | Input | Read joypad $4218/$421A → hold/edge |
| $C0C0FB | InputSerial | Input | Serial read $4016/$4017 |
| $C0A14B | AreaInit | Camera | Area/camera init, clear scroll vars |
| $C08E87 | VBlankWrite | Camera | Write scroll regs, fade |
| $C09BE7 | StateMachine | Object | Object state machine update |
| $C0C1E7 | DMA | Core | DMA transfer setup |
| $C0CC95 | DMA2 | Core | DMA transfer setup (alt) |
| $C0A909 | WRAMWrite | Core | WRAM DMA write |
| $C0C21C | PRNG | Core | Pseudo-random number generator |

## Engine Interaction Summary

```
NMI
 └─► Input Read ($C0C15A) — reads joypads, stores to $0500-$0510
      └─► SA-1 Sync ($C08559) — wait for SA-1 ready
           └─► Slot Dispatch ($C0852D)
                ├─► Phase Dispatch ($C08687)
                │    └─► SA-1 Execute (JSL $B5804C)
                │         ├─► Area/Camera ($C0A14B)
                │         ├─► Object Logic (bank B8/BA/BC)
                │         ├─► State Machine ($C09BE7)
                │         └─► Enemy AI (bank BB/BD)
                └─► VBlank Write ($C08E87)
                     ├─► Scroll Registers ($2110-$2112)
                     ├─► Color Math ($212C/$2130)
                     └─► Palette Fade ($2121/$2122)
```
