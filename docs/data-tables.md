# Data Tables & Constants

## Immediate Values from Pseudocode

### Sprite Type ID Map

| Value | Name | Used In | Description |
|---|---|---|---|
| `$D8` (216) | `SPRITE_KONG_GENERIC` | func_C0855E, func_C08916 | Generic Kong sprite type |
| `$DC` (220) | `SPRITE_DONKEY_KONG` | func_C085B8 | Donkey Kong sprite type |
| `$E4` (228) | `SPRITE_DIXIE_KONG` | func_C0852D, func_C085B8 | Dixie Kong sprite type |

Written to `slot_sprite_type` ($0B8D+). Values suggest a sprite type enumeration starting at $D8 with gaps.

### Slot Timer Constants

| Value | Frames | Used At | Description |
|---|---|---|---|
| `$14` (20) | ~0.33s | C08626 | Slot timer (func_C085B8) |
| `$2B` (43) | ~0.72s | C0853A | Slot timer (func_C0852D) |
| `$30` (48) | ~0.80s | C08550 | Slot timer (func_C0852D) |
| `$31` (49) | ~0.82s | C085FA, C0861C | Slot timer (func_C085B8) |
| `$46` (70) | ~1.17s | C08605, C08621 | Slot timer (func_C085B8) |
| `$60` (96) | ~1.60s | C08540 | Slot timer (func_C0852D) |

Written to `slot_timer` ($1029+). At 60fps: frames/60 = seconds.

### Animation State IDs (func_C08895)

| Value | Position | Description |
|---|---|---|
| `$0030` (48) | base | Animation group 0 (lowest) |
| `$0040` (64) | +16 | Animation group 1 |
| `$0050` (80) | +32 | Animation group 2 |
| `$0060` (96) | +48 | Animation group 3 |
| `$0070` (112) | +64 | Animation group 4 |
| `$0080` (128) | +80 | Animation group 5 |
| `$0090` (144) | +96 | Animation group 6 |

Each state is loaded conditionally and written to `sprite_anim_state` ($6C). Steps of 16 ($10) between values suggest these are offsets into a flat animation sequence table.

### Area State Dispatch ($0516) — func_C085B8, func_C0855E

| Value | Name | Purpose |
|---|---|---|
| `$0001` (1) | `AREA_STATE_INIT` | Init sprite slots on entry |
| `$0002` (2) | `AREA_STATE_ENTERING` | Player entering area |
| `$0003` (3) | `AREA_STATE_EXITING` | Player exiting area |
| `$0009` (9) | `CARRY_STATE` | Kong carrying object |
| `$000C` (12) | `TIMER_CHECK` | Slot timer decrement/check |
| `$0032` (50) | `CONSTANT_50` | Slot timer load |

Higher values ($0A=10, $11=17, $12=18, $13=19) dispatch to separate handler tables.

---

## SA-1 Function Call Map

### Dispatcher ($B5)

| Address | Purpose |
|---|---|
| `$B5804C` | **SA-1 firmware dispatcher.** Y = address of handler table in ROM bank $00. The SA-1 reads handler data from (Y) and executes internally. NOT 65816 executable code — SA-1 internal firmware. |

Handler tables referenced via Y:

| Table Addr | Trigger | Used By |
|---|---|---|
| `$00:885F` | $0516 != 1, $0516 == 10 | func_C08687 |
| `$00:888B` | $0516 == 17 | func_C08687 |
| `$00:88B7` | $0516 == 18 | func_C08687 |
| `$00:88E3` | $0516 == 19 | func_C08687 |
| `$00:8DF9` | $3E == $0038 | func_C088F9 |
| `$00:8E21` | $3E == $003C | func_C088F9 |

Each table contains handler-specific data (format TBD — likely SA-1 parameters, not SNES addresses).

### BW-RAM Uploaded Handlers (Banks $B8-$BE)

These are NOT in ROM. During SA-1 initialization, code is uploaded to SA-1's internal BW-RAM and mapped to these bank addresses. The SNES CPU calls them via `JSL`, and the SA-1 executes them.

| Address | Called From | Purpose |
|---|---|---|
| `$B8822B` | func_C08559 | Unknown helper (C08559) |
| `$B88347` | func_C0A14B | Area init: clear/scatter |
| `$B8870B` | func_C0A14B | Area init: setup pass |
| `$B8B52C` | func_C0A14B | Area init: config load |
| `$B8819F` | func_C0A8A4 | Unknown helper |
| `$B990E7` | func_C0E9B4 | Attract/menu: timer overlay |
| `$B999AD` | func_C0E9B4, C0E9DD, C0EE3F, C0EDCE | Attract/menu: fade/screen setup |
| `$B999F1` | func_C0E9B4, C0EDCE | Attract/menu: player state init |
| `$BBA849` | func_C0A14B | Area init: tileset load |
| `$BCB38E` | func_C0A14B | Area init: collision/geometry |
| `$BE8092` | func_C085B8 | Slot swap helper |
| `$BE80A4` | func_C0852D, C0855E, C085B8 | Sprite init helper (3 entry points) |

---

## VRAM / CGRAM Constants

### Palette Source Addresses (func_C08E87, func_C0EE3F)

| Value | Purpose | Context |
|---|---|---|
| `$1304` | CGRAM address $1304 | Fade palette destination |
| `$A422` | Source palette data address | Fade source LUT |
| `$6000` | VRAM tilemap base | BG tilemap in func_C0EE3F |
| `$6100` | VRAM tilemap base+$100 | BG tilemap (offset 256 bytes) |
| `$7400` | VRAM tile address | BG tiles (func_C0EE3F) |
| `$7800` | VRAM tile address | BG tiles (func_C0EE3F) |
| `$7C00` | VRAM tile address | BG tiles (func_C0EE3F) |
| `$787C` | VRAM address | Blend/transition target |

### Tilemap Transfer Values (func_C0E9B4, Attract/Menu)

| Value | Purpose | Context |
|---|---|---|
| `$2000` | VRAM write address | Attract screen tilemap |
| `$20A0` | VRAM write address+$A0 | Attract screen tilemap (row offset) |
| `$0300` | Size/value | Attract screen parameter |
| `Y = $0800` | Size (2048 bytes) | Tilemap data transfer size |
| `Y = $04C0` | Size (1216 bytes) | Smaller tilemap transfer |

---

## State Machine Tables ($00:885F area)

ROM data at `$00:885F` (ROM offset 0x00085F):

| Index | Table A | Table B | Table C | Table D |
|---|---|---|---|---|
| 0 | `$0000` | `$4E01` | `$C7F7` | `$8717` |
| 1 | `$0F10` | `$1E80` | `$CFFF` | `$F738` |
| 2 | `$0679` | `$7F00` | `$EFA8` | `$3B32` |
| 3 | `$5B79` | `$FE02` | `$68FC` | `$33CA` |

Table A (entry 0 = $0000) matches the "null" handler for $0516 != 1.
Higher entries ($0F10, $0679, $5B79) appear to be SA-1 firmware opcodes or handler IDs, not SNES addresses.

---

## Palette Data Table (`$00:808F1D`)

Referenced by func_C08E87 for CGRAM palette init during reset/fade. Located in bank $00 ROM at address `$808F1D`. Contains CGRAM palette data read via indexed loop.

---

## WRAM-Based Lookup Tables (Dynamic / Runtime)

The SA-1 uploads several lookup tables to WRAM at runtime:

| WRAM Address | Table | Set By |
|---|---|---|
| $050A / $050C | Work table pointers (word) | func_C0A14B init |
| $0400-$041E | Slot work area (16 words) | func_C0A14B clear |
| $0516 | Area/sprite state dispatch index | Various state functions |
| $088C | Brightness color shift (fade) | func_C0A14B init |
| $0896 | Palette cycle step counter | func_C0A14B init |
| $1B17 / $1B19 | State machine vars | func_C085B8 / C0877C |
| $1E29 | State machine trigger | func_C088F9 |
| $1E45 | Sprite count / active sprites | Area init |

These are populated by SA-1 code (banks $B8+ in BW-RAM) and consumed by the SNES CPU (bank $C0 code).
