# Game Loop Architecture — DKC2 (SNES)

## Overview

```
Reset ($C08000)
  │
  ▼
Init Sequence ($C08000 → $C0A8CF)
  ├─ CLC / XCE (native mode)
  ├─ SEI (disable interrupts)
  ├─ REP #$20 (16-bit A)
  ├─ LDA #$0000 → TCD (DP = $0000)
  ├─ SEP #$20 (8-bit A)
  ├─ LDA #$48 → PHA → PLB (DBR = $00)
  ├─ STA $420D (SA-1 enable)
  ├─ STA $4200 (NMI enable)
  ├─ REP #$30 (16-bit A/X)
  ├─ LDA #$01FF → TCS (SP = $01FF)
  └─ JMP $C0A8CF (init continues in bank C0)
        │
        ▼
  Init completes
        │
        ▼
Idle Loop ($C0C0B4)
  ┌─ WAI (wait for interrupt)
  └─ BRA (loop forever)
        │
        ▼
  NMI fires (VBlank)
        │
        ▼
NMI Handler ($C08916)
  ├─ JSR $852D       ; save context (SNES regs)
  ├─ LDA $82
  ├─ EOR #$0006      ; toggle frame_index (0↔6)
  ├─ STA $82
  ├─ DEC / DEC       ; $84 = $82 - 2
  ├─ STA $84
  ├─ JSR $8559       ; SA-1 sync
  ├─ LDX $82
  ├─ LDA #$00D8
  ├─ STA $0B8D,X     ; set slot timer
  └─ RTI
```

## Two-Slot WRAM System

DKC2 uses a **dual slot** system indexed by frame_index (`$82`). Each frame, the index toggles between 0 and 6 (gap of 6 bytes), alternating between SLOT0 and SLOT1.

```
$82 = 0 → SLOT0 (DK)
$82 = 6 → SLOT1 (Diddy)
```

### Slot Arrays (stride = 6 bytes)

| Address | Offset | Size | Description |
|---------|--------|------|-------------|
| $0B8D,X | $0B8D+index | 2 bytes | Slot timer (set to #$00D8 in NMI) |
| $0512,Y | depends on Y | 2 bytes | Post-dispatch result from $86 |
| $1029,X | slot-specific | 2 bytes | Slot parameter |
| $0B19,X | slot-specific | 2 bytes | Object position/state |
| $0BC1,X | slot-specific | 2 bytes | Object position/state |
| $0C69,Y | depends on Y | 2 bytes | State A handler writes here |

## SA-1 Dispatch Mechanism

### State Router (`$C08687`)

Called via `JSR $8687`. Reads `$0516` (global game state) and returns handler address in Y:

```
$0516 == 0x0009 → Y = $885F (state 9)
$0516 == 0x000A → Y = $888B (state A)
$0516 == 0x000B → Y = $88B7 (state B)
$0516 == 0x000C → Y = $88E3 (state C)
default          → Y = $885F
```

### Call Site (`$C0862C`)

```
PHY               ; save slot index
PHX               ; save X
JSR $8687         ; dispatch → Y = handler address
JSL $B5804C       ; SA-1 sync: execute handler at Y
PLX               ; restore X
PLY               ; restore Y
LDA $86           ; post-dispatch value
STA $0512,Y       ; store to slot array
```

### SA-1 Shared Handler (`$C088F9`)

After NMI processing, the SA-1 sync handler checks `$3E` (SA-1 internal state) and dispatches to inline code tables:

```
LDA $3E
CMP #$0038
BEQ → LDY #$8DF9 → JSL $B5804C → RTS   ; state 0x38: table at $8DF9
CMP #$003B
BEQ → LDY #$8E21 → JSL $B5804C → RTS   ; state 0x3B: table at $8E21
RTS                                       ; other states: no-op
```

The tables at `$8DF9` / `$8E21` contain **inline 65816 code** executed directly by the SA-1. They are NOT pointer tables — the SA-1 executes the bytes as instructions at those addresses.

## Memory Map (DP + Slot)

| Address | Size | Description |
|---------|------|-------------|
| $82 | 2 bytes | Frame index (0 or 6), toggled each NMI |
| $84 | 2 bytes | Slot index minus 2 |
| $86 | 2 bytes | Post-dispatch intermediate value |
| $3E | 2 bytes | SA-1 internal state flag |
| $0516 | 2 bytes | Global game state (9/A/B/C) |

## Key Functions

| Address | Name | Description |
|---------|------|-------------|
| $C08000 | Reset | System init: native mode, DP, DBR, SA-1, NMI, SP |
| $C0C0B4 | Idle | WAI / BRA loop |
| $C08916 | NMI | Toggle slot, sync SA-1, set timer |
| $C08687 | State Dispatch | Route $0516 → handler address in Y |
| $C0888B | State A Handler | Write $0C69,Y, set $1929 = 1 |
| $C088B7 | State B Handler | TBD — SA-1 dispatched |
| $C088E3 | State C Handler | Init frame, toggle slot, chain to $88F9 |
| $C088F9 | SA-1 Shared | Dispatch SA-1 inline code by $3E state |
| $C0862C | Dispatch Caller | PHY/PHX → JSR $8687 → JSL $B5804C → PLX/PLY |
