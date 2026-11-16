# Input System — DKC2 (SNES)

## Hardware Overview

DKC2 reads input from two hardware sources:

| Source | Address | Type | Description |
|--------|---------|------|-------------|
| **Auto-read registers** | `$4218`/`$421A` | Read-only | Automatically latched by SNES every frame |
| **Serial protocol** | `$4016`/`$4017` | Read/Write | Direct controller serial protocol (used for multi-tap) |

## Input Read Function

### Main Loop Entry ($C0A252)

Called every frame before game logic processing. Runs at M=1/X=1 (8-bit) for HBlank wait, then M=0 (16-bit) for data processing.

```
Flags: M=[1,0] X=[1,1]
wait for HBlank: $4212 bit 0 clear
```

### Algorithm

```asm
func_C0A252:
  ; Wait for HBlank ($4212 bit 0)
  SEP #$30        ; M=1, X=1 (8-bit)
@loop:
  LDA #$01
  BIT $4212       ; test HBlank flag
  BEQ @loop       ; wait until HBlank active

  REP #$20        ; M=0 (16-bit A), X=1 (8-bit index)

  ; Controller 1 ($4218)
  LDA $4218       ; read joypad 1
  TAX             ; save raw value
  EOR $0500       ; XOR with previous hold → changed bits
  AND $4218       ; mask with current read → rising edge only
  STA $0504       ; → edge1 (newly pressed this frame)
  TXA             ; restore raw value
  STA $0500       ; → hold1 (currently pressed)

  ; Controller 2 ($421A) - same algorithm
  LDA $421A
  TAX
  EOR $0502
  AND $421A
  STA $0506       ; → edge2
  TXA
  STA $0502       ; → hold2

  ; Serial read for multi-tap support
  JSR func_C0C0FB

  ; Route active controller based on mode
  LDA $42         ; controller mode
  CMP #2
  BNE @check_mode1
  ; Mode 2: multi-tap adapter
  LDA $056F       ; multi-tap flag
  AND #2
  TAX
  LDA $0500,X
  STA $050E       ; routed hold
  LDA $0504,X
  STA $0510       ; routed edge
  BRA @done

@check_mode1:
  CMP #1
  BNE @default
  ; Mode 1: player index routing
  LDA $44         ; player index (0 or 2)
  ASL A
  TAX
  LDA $0500,X
  STA $050E
  LDA $0504,X
  STA $0510
  BRA @done

@default:
  ; Mode 0 (default): use controller 1 directly
  LDA $0500
  STA $050E       ; routed hold = controller 1 hold
  LDA $0504
  STA $0510       ; routed edge = controller 1 edge

@done:
  LDA $0579
  AND #$0040      ; check flag bit 6
  RTS
```

## Input Memory Map

### Registers ($7E0500-$7E0510)

| Address | Name | Type | Source | Description |
|---------|------|------|--------|-------------|
| `$0500` | `hold1` | word | `$4218` | Controller 1 currently pressed buttons |
| `$0502` | `hold2` | word | `$421A` | Controller 2 currently pressed buttons |
| `$0504` | `edge1` | word | computed | Controller 1 newly pressed this frame |
| `$0506` | `edge2` | word | computed | Controller 2 newly pressed this frame |
| `$050E` | `routed_hold` | word | routed | Routed hold for active player |
| `$0510` | `routed_edge` | word | routed | Routed edge for active player |

### Edge Detection

The edge calculation isolates **rising edges** (buttons pressed this frame):

```
edge = ($4218 XOR hold_prev) AND $4218
     = (current_frame XOR previous_frame) AND current_frame
```

This produces a 1 for any button that was NOT pressed last frame but IS pressed this frame.

### Controller Mode Registers

| Address | Name | Type | Description |
|---------|------|------|-------------|
| `$42` | `controller_mode` | word | 0 = 1P default, 1 = 2P player index, 2 = multi-tap |
| `$44` | `player_index` | word | Player index for 2P mode (0 or 2 for controller offset) |
| `$056F` | `multi_tap_flags` | word | Multi-tap adapter flags (bit 1 = 5-player adapter active) |

### Controller Mode Routing

| Mode (`$42`) | Routing Logic | Use Case |
|--------------|---------------|----------|
| 0 | `routed_hold = $0500` (controller 1) | Single player (default) |
| 1 | `routed_hold = $0500,X` where X = `$44 << 1` | Two-player, indexed by player |
| 2 | `routed_hold = $0500,X` where X = `$056F AND 2` | Multi-tap adapter (5-player) |

## SNES Button Mapping

### Standard SNES Controller Layout

```
       ┌─────┐
       │  ↑  │
     ┌─┼─┐ ┌─┼─┐   ┌───┐ ┌───┐
     │◄┼─┼─┼─┼─►│   │ Y │ │ X │
     └─┼─┘ └─┼─┘   └───┘ └───┘
       │  ↓  │     ┌───┐ ┌───┐
       └─────┘     │ B │ │ A │
       Select  Start└───┘ └───┘
```

### Bit Mapping

| Bit | Button | DKC2 Action |
|-----|--------|-------------|
| 0 | B | Jump, Confirm menu |
| 1 | Y | Roll, Cancel |
| 2 | Select | (unknown) |
| 3 | Start | Pause |
| 4 | Up | D-Pad Up |
| 5 | Down | D-Pad Down |
| 6 | Left | D-Pad Left |
| 7 | Right | D-Pad Right |
| 8 | A | (action button) |
| 9 | X | (action button) |
| 10 | L | (shoulder) |
| 11 | R | (shoulder) |
| 12-15 | — | Unused (always 0 in standard pad) |

### Player Actions (Speculative from RAM Map)

| Action | Button | Edge/Hold | Description |
|--------|--------|-----------|-------------|
| Jump | B (bit 0) | Edge | Press to jump, hold for height |
| Roll | Y (bit 1) | Edge | Roll attack / dodge |
| Pause | Start (bit 3) | Edge | Toggle pause |
| Move | D-Pad (bits 4-7) | Hold | Directional movement |
| Confirm | B (bit 0) | Edge | Menu confirm |
| Cancel | Y (bit 1) | Edge | Menu cancel |

## Serial Protocol Read ($C0C0FB)

### Purpose

Reads controllers directly via the serial protocol on `$4016`/`$4017`. This is used for **multi-tap adapter support** (5-player adapter).

### How Serial Protocol Works

SNES controllers use a shift register protocol:
1. Write to `$4016` (bit 0) to latch: 0→1→0
2. Read `$4016` (controller 1) or `$4017` (controller 2) 16 times
3. Each read gets one button: bit 0 = data, bits 1-7 = 0

### Implementation

```
func_C0C0FB:
  ; Check if controller 1 needs serial read
  LDA $0500       ; hold1
  AND #$0007      ; test special flag bits
  BNE @do_serial1 ; if any set, do serial read
  BRA @check_2

@do_serial1:
  SEP #$20        ; M=1 (8-bit)
  LDY #$10        ; 16 iterations
@serial_loop_1:
  LDA $4016       ; read serial data
  DEY
  BNE @serial_loop_1
  REP #$20        ; M=0 (16-bit)
  STZ $0500       ; clear hold1
  STZ $0504       ; clear edge1
  BRA @continue

@check_2:
  ; Same for controller 2 ($4017)
  LDA $0502       ; hold2
  AND #$0007
  BNE @do_serial2
  RTS

@do_serial2:
  SEP #$20        ; M=1 (8-bit)
  LDY #$10
@serial_loop_2:
  LDA $4017
  DEY
  BNE @serial_loop_2
  REP #$20        ; M=0 (16-bit)
  STZ $0502
  STZ $0506
  RTS
```

### Dual Read Path

DKC2 supports **two input read paths**:

```
Standard Path (default):
  $4218/$421A auto-read ──► $0500/$0502 (hold) ──► $0504/$0506 (edge)
                                │
                                ▼
                          Controller routing
                          via $42/$44/$056F
                                │
                                ▼
                          $050E (routed hold)
                          $0510 (routed edge)

Serial Path (multi-tap):
  $4016/$4017 serial ──► override $0500/$0502 ──► clear $0504/$0506
```

The check `AND #$0007` on hold values suggests bits 0-2 are used as flags to trigger serial re-read. When these bits are set, the serial protocol is used instead of the auto-read.

## Flow Diagram

```
Frame Start
    │
    ▼
Wait for HBlank (§4212)
    │
    ▼
Read $4218 (joypad 1)
    ├── XOR $0500 (previous hold)
    │   └── AND $4218 → $0504 (edge 1)
    └── STA $0500 (hold 1)
    │
    ▼
Read $421A (joypad 2)
    ├── XOR $0502 (previous hold)
    │   └── AND $421A → $0506 (edge 2)
    └── STA $0502 (hold 2)
    │
    ▼
Serial read via JSR $C0FB
    ├── if $0500 & 7 → read $4016 (16 bits)
    └── if $0502 & 7 → read $4017 (16 bits)
    │
    ▼
Controller routing
    ├── $42 = 2 → multi-tap ($056F & 2)
    ├── $42 = 1 → player index ($44)
    └── $42 = 0 → controller 1 direct
    │
    ▼
$050E = routed hold
$0510 = routed edge
    │
    ▼
Game logic uses $050E/$0510
```

## Key Functions Reference

| Address | Name | Description |
|---------|------|-------------|
| $C0A252 | InputRead | Main input read: HBlank wait, $4218/$421A read, edge detect, routing |
| $C0C0FB | InputSerial | Serial read via $4016/$4017 for multi-tap adapter |
| $C0C15A | InputReadAlt | Copy/synonym of InputRead at different address |

## Initialization

Input system is initialized during `func_C0A14B` (Area Init):
- `$42` (controller_mode) is set based on game configuration
- `$0500-$0510` are zeroed
- `$056F` (multi_tap_flags) is set to 0x0001 by `func_C0BA23`
