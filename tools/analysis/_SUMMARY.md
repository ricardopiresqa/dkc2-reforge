# DKC2 Reversal Status

## ROM Info
- Size: 4MB HiROM + SA-1 coprocessor
- Title: "DIDDY'S KING QUEST" (header at $00FFC0)
- SA-1 registers: $2200-$22FF (mapped at SNES $2200)

## SA-1 Usage in DKC2
- SA-1 **nunca** usado como co-processador (core 65816 nunca sai de reset)
- SA-1 usado APENAS como "glue logic":
  - FastROM timing (85ns acesso ROM)
  - Memory mapping via $2224 (controle da janela $B4-$B5)
- $2224 default = $00 (mapeia $B4-$B5 para bank ROM $80)
- Writes em $2200 (STZ $2200 em 0x36F5BA) e $2201 (STZ em 0x3A9FF4)
- **Zero writes** para SA-1 DMA ($2230-$2238) ou SA-1 IRQ ($2202-$2205)
- $B06000: write-test SRAM, não origem de copy

## SA-1 Memory Mapping (confirmado experimentalmente)
**Fórmula linear de 64KB**, NÃO o interleave padrão HiROM:
```
ROM offset = (bank & 0x3F) * 0x10000 + addr
```
- $80:yyyy → ROM 0x008000-0x00FFFF (upper half)
- $B5:8000 → ROM 0x358000
- $BB:91D9 → ROM 0x3B91D9
- $80:90DA → ROM 0x0090DA
- Banco $B4 via $2224: default mapeia bank $80

## Boot/Init Flow Completo
### Fase 1: Reset Handler ($83F7)
```
SNES liga → lê reset vector $00:FFFC-D = $83F7
→ Pula para SNES $80:83F7 (ROM 0x83F7)
```
1. SEI, Force Blank ($2100=$80), NMI ($4200=$01), FastROM ($420D=$01), HDMA off ($420C=$00)
2. CLC+XCE → modo nativo
3. REP #$30 → 16-bit A/X
4. Checksum test (ADC #$FFFF, sempre passa pelo carry)
5. Stack/SRAM test: busca opcodes, write-test em $B06000, bit4 de $213F
6. Init vetores: copia 4 words de $83C0→WRAM $0907
7. TCD=0, SP=$01FF, PEA para ajuste de pilha

### Fase 2: SNES Register Init (0x84F8)
- STZ loop: $2101-$2134 (PPU) e $4202-$420C (CPU)

### Fase 3: VRAM Clear via DMA (0x8591)
- DMA channel 0: source fixo = BRK #$00 (bytes 0x00 0x00 em 0x858F)
- Preenche 64KB VRAM com $0000

### Fase 4: WRAM Clear via MVN (0x85B9)
- STZ $00, MVN $7E,$7E → propaga $00 por 64KB $7E
- MVN $7F,$7E → copia bloco zerado para $7F (128KB total)

### Fase 5: Post-boot calls
```
0x85D5: JSL $B58000   → Entry 0 da tabela $B5 ($B5:818D)
                          PHK/PLB, JSR $8191, RTL
0x85D9: JSL $BB91D9   → Init complementar bank $BB
                          SEP #$20, HDMA off, NMI on, screen brightness
                          RTL
0x85DD: JSR $8EAE     → Subrotina curta no bank $80
0x85E0: JML $8090DA   → MAIN GAME ENTRY 🎯
```

### Fase 6: Game-Specific Init ($8090DA)
```
$80:90DA:
  JSR $90CD              → clear $060F, $060D
  LDA #$002C, STA $78
  JSR $84F8              → RE-init SNES regs
  JSR $8591              → RE-clear VRAM
  STZ $2A
  LDA #$AA55, STA $2E
  LDA #$3765, STA $30
  LDA #$0011
  JSL $B58006            → Entry 2 (PHK/PLB, init DP vars)
  SEP #$20
  LDA #$01, STA $4200    → NMI enable + auto-joypad
  LDA #$8F, STA $2100    → screen brightness
  STZ $2101, STZ $2133   → sprite tile base zero, normal mode
  REP #$30               → 16-bit
  LDA #$0003, STA $2105  → Video Mode 3
  LDA #$0102, STA $212C  → main screen enable
  LDA #$0202, STA $2130  → window mask
  LDA #$0364, STA $210B  → tilemap config
  LDA #$787C, STA $2107  → screen map base
  STZ $2116              → VRAM addr = 0
  ... setup de cores, paletas, carregamento de dados via JSL $BB8D91 + JSL $80895F ...
```

## Game Loop Architecture (Main Loop)

### Arquitetura: Two-Level Dispatch ($20 + $24)
O game loop usa **dispatcher de dois níveis** com ponteiros em DP $20 e $24:

| DP Var | Função | Setado por |
|---|---|---|
| `$20` | **NMI dispatch** — JMP ($0020) no NMI handler | Init + $8C82 |
| `$24` | **Game loop dispatch** — JMP ($0024) em $8608 | Init + handlers |
| `$2C` | Frame counter (inc por NMI) | NMI handler |
| `$0993` | State counter | Init + transições |

### NMI Handler ($80:F3C1) — Completo
```
F3C1: REP #$30, PHD, PHA, PHX, PHY  ; save regs (16-bit)
F3C8: LDA #$0000, TCD                ; DP = $0000
F3CC: SEP #$20                       ; 8-bit A
F3CE: LDA $4210                      ; ack NMI (clear bit 7)
F3D2: LDA #$8F
F3D4: STA $2100                      ; screen brightness max
F3D8: REP #$20                       ; 16-bit A
F3DA: LDA $002C
F3DE: INC A
F3DF: STA $002C                      ; frame counter++
F3E3: 6C 20 00    JMP ($0020)        ; → dispatch para handler em DP $20!
F3E6: E2 20       SEP #$20           ; ← NMI TAIL (retorno do handler)
F3E8: AF 12 05 00 LDA $000512        ; load brightness value
F3EC: 8F 00 21 00 STA $002100        ; set screen brightness
F3F2: C2 20       REP #$20           ; 16-bit A
F3F4: C2 30       REP #$30           ; 16-bit X/Y
F3F6: 7A          PLY                ; restore regs
F3F7: FA          PLX
F3F8: 68          PLA
F3F9: 2B          PLD
F3FA: 40          RTI                ; return from NMI → WAI
```

**Ponto chave:** JMP ($0020) é tail-call — handler NUNCA retorna ao NMI handler.
O handler DEVE terminar com PLY, PLX, PLA, PLD, RTI ou JMP para $F3E6 (NMI tail).

### Main Loop Primário: $8C82 Dispatcher
```
$8C82: STA $20       ; set NMI handler (chamado com handler addr em A)
$8C84: SEP #$20      ; 8-bit A
$8C86: LDA $4211     ; clear IRQ flag
$8C89: LDA $4210     ; clear NMI flag
$8C8C: LDA $4210     ; read again
$8C8F: AND #$80
$8C91: BNE $8C8C     ; spin until NMI clear
$8C93: LDA #$81
$8C95: STA $4200     ; NMI enable + auto-joypad
$8C98: STZ $4016     ; joypad strobe reset
$8C9B: WAI           ; wait for VBlank/NMI
$8C9C: BRA $8C9B     ; loop (NMI → RTI retorna aqui)
```

### Bridge Handler: $8608 (primary NMI target)
Executado a cada VBlank via JMP ($0020):
```
$8608: LDA #$01FF
$860B: TCS            ; reset stack pointer ($01FF)
$860C: LDA #$F3E6     ; NMI tail return address
$860F: STA $20        ; DP $20 = $F3E6 (troca NMI dispatch pro tail)
$8611: INC $2A        ; frame counter++ (redundante ao NMI handler)
$8613: 6C 24 00 JMP ($0024) ; dispatch to game logic via DP $24!
```

**O que $8608 faz:**
1. Reseta ponteiro de pilha a cada frame
2. Redireciona $20 para $F3E6 (NMI tail de restore)
3. Incrementa frame counter
4. Dispara game loop via JMP ($0024)

**Game loop callback ($24) DEVE:**
- Executar lógica do frame atual
- Setar DP $20 para o handler do PRÓXIMO frame (ex: de volta $8608)
- Ao final, JMP para $F3E6 (NMI tail que restaura regs + RTI)

### Fluxo Pós-Init — Chain Completa
```
Init Fim ($90DA → $93AF):
  LDA #$93B8 → JMP $B0EE → STA $20  → WAI

Frame 0-379 (Intro/Boot Loader Handler):
  NMI → JMP ($0020) → $93B8
  $93B8: preenche paletas, tilemaps, VRAM
         checks $2A vs valores específicos ($E0, $110, $111, $112...)
         cada valor: setup específico (paleta, JSL loading, etc)
         Bottom: $9502-$9505-$9508-$950B
           LDA $2A - $0121 → CMP $005B
           BCC $9510  → se < threshold, vai pra handler reducido
           JMP $95B3  → se >= threshold ($17C frames), avança fase
  $95B3: segunda fase do loader
         checks $2A novamente para próximos thresholds
         eventualmente JMP $964C ou JMP $96FB
         ...
         $9678: JML $8085EF → transição para game loop

  **Obs:** $93B8 NÃO muda $20! Retorna via RTI.
  Próximo NMI sempre dispatches para $93B8 novamente.
  $93B8 usa JMP interno ($950D, $95BE, etc) para FLUXO local.

Transição pós-Intro ($8085EF):
  $85EF: LDA #$FFFF / STA $090F
  $85F6: JSL $BB91D9    → re-init hardware (HDMA off, brightness, etc)
  $85FA: LDA #$B3D7 / STA $24  → set game loop handler
  $85FF: STZ $2102              → OAM addr reset
  $8602: LDA #$8608
  $8605: JMP $8C82 → STA $20 (NMI handler = $8608), WAI

Frame 380+ (Game Loop):
  NMI → JMP ($0020) → $8608
  $8608: TCS reset, $20=$F3E6, INC $2A, JMP ($0024) → $B3D7
  $B3D7: JSL $BB91D9 (init!), STZ vars, JSR subs
         : set DP $20 for next frame
         : → NMI tail ($F3E6)
  $F3E6: set brightness → PLY, PLX, PLA, PLD → RTI
```

### Handler Chain Timeline (Boot → Title)
```
Frame    Handler     Event
─────────────────────────────────────
0        $93B8       Inicio: setup paletas
~224     $93B8+$93F3 $2A=$E0: JSL $80B15E
~272     $93B8+$9416 $2A=$110: carrega dados em VRAM via JSL $80895F
~273     $93B8+$9430 $2A=$111: carrega mais dados VRAM
~274     $93B8+$9458 $2A=$112: carrega mais dados
~380     $95B3       Transição: segunda fase de loader
~440+    $964C/etc   Trabalho adicional da intro
fim      $8085EF     Transição: re-init, set $24=$B3D7, set $20=$8608
         $8608→$B3D7 Game loop ativo: title screen
```

### Vectors
| Vector | Address | Handler |
|---|---|---|
| Reset (emu) | $00:FFFC → $83F7 | Boot/init code |
| NMI (native) | $00:FFEA → $00:F3BD | JML $80:F3C1 |

## Code Organization (Bank $80)
| Range | Content |
|---|---|
| $8000-$83BF | Header/data/vectors |
| $83F7-$85E0 | Boot code (reset handler + init) |
| $84F8-$8563 | SNES register init subroutine |
| $856A-$858A | DMA channels clear |
| $8591-$85B4 | VRAM clear via DMA |
| $85B9-$85CE | WRAM clear via MVN |
| $85D1-$85DE | Vector copy to WRAM |
| $85EF-$8605 | **Transição pós-intro → game loop** (JSL $BB91D9, set $24=$B3D7) |
| $8608-$8615 | **Bridge handler** (reseta stack, set $20=$F3E6, JMP ($0024)) |
| $862A+     | DB validation + loader cont |
| $895F | Data load function |
| $897C | Common return/yield function |
| $8C32 | **Brightness set** (STZ $0513 + STA $0512 + RTS) |
| $8C3D-$8C7F | **Fade controller** — $0513 = duração (pos = fade in, neg = fade out), $0514 = contador, INC/DEC $0512 (brightness), clamped $0F |
| $8C82-$8C9C | **Main loop dispatcher** (STA $20, clear NMI, WAI/BRA) |
| $8C9E-$8CA5 | **Dispatch set $24** (PHK/PLB, STA $24, JSR $8CAC, JMP $862A) |
| $8CAC-$8CC8 | **DMA init ($4300-4308)** — M=0 (16-bit). LDA #$0200→$4302/$4308, LDA #$0220→$4305, LDA #$0400→$4300 (modo 4), SEP #$20 |
| $8CC9-$8CFF | **Event dispatch table** — 5+ entries: JSL $BAB31B (menu), JSL $B4BE60, JML $B5D13B/$B5D4A7/$B5D334, JSL $B491D7 |
| $8EAC+    | Subrotinas de setup |
| $90DA-$93AF | Main game init + carga de dados |
| $93B8-$950D | **Primeiro event handler** (intro loader, checks $2A) |
| $95B3-$9678 | **Segundo event handler** (intro loader phase 2 → JML $8085EF) |
| $967C-$99C0 | Handler chain continuations → eventualmente $8085EF |
| $99C3-$99FF+ | **Menu/gameplay handler** (set por $99BD: STA $20 + JMP $B0EE) — checa $060D pointer de menu, Select/L/R navega nível, timer $36/$38 confirma seleção |
| $A5F1-$A800 | **Gameplay entry** — JSL $BB91D9, check $0613 → carrega tabela $80ABE8,Y via [$32],Y. Se $0613=0: screen mode/window/HDMA/color math, decompress tiles, HDMA table $7E8012-24, DMA ch3 ($2601) |
| $A2CF-$A2FF+ | **Attract/Level Select** — color anim, JSL $BB8089/$B5A919, loop sprite com $2A timer. ≥$0500 ou $0512 neg → transição $820F |
| $A86C-$AC3B | **HDMA controller** — DMA ch1+2, check $0613&$E4, $2A timing → efeito wavy $2110. $0613&$80 → JSR $AC3C |
| $B0EE-$B107 | **Entry dispatcher** (STA $20, clear NMI, NMI enable + WAI/BRA) |
| $B15E+     | Subrotina de loading |
| $B3D7-$B45E | **Main Game Loop Handler** — init + title screen dispatch |
| $B461-$B55C | **Title Screen Handler** — anim, input, transition to next state |
| $B560-$B5F9 | **Video Mode Setup** — mode 1, palettes, tilemap, data loading |
| $B5FA-$B67E | **Second Handler** — gameplay init, data load, set $B681 |
| $B681-$B6BF | **Fade/Wait Handler** — $2A timer, brightness control, JML $8085EF |
| $F3C1-$F3E3 | NMI handler (PHD/PHA/PHX/PHY, ack NMI, inc $2C, JMP ($0020)) |
| $F3E6-$F3FA | **NMI tail** (set brightness, PLY/PLX/PLA/PLD, RTI) |

### Bank $B5 — Sub-handlers (via JSL/JML)
Bank $B5 contém handlers auxiliares chamados de bank $80 via JSL/JML. Entram com M=0, X=0 (16-bit).

| Entry | Endereço | Origem | Função |
|---|---|---|---|
| JMP table (12) | $B5:8000 | Indexado por seletor | Jump table para handlers abaixo |
| 0 ($818D) | $B5:818D | | PHX/PHY, JSL $BB8089, PLY/PLX, RTL (Data Load?) |
| 1 ($8030) | $B5:8030 | | Handler init |
| 2 ($80D5) | $B5:80D5 | | Handler init |
| 3 ($80EE) | $B5:80EE | | Handler init |
| 4 ($8106) | $B5:8106 | JSL $B5800C (de $B3D7) | JSR $8213/$828F/$82A9, set $32/$34 ptrs, JSR $83FB (data load), RTS |
| $B5:A8DA | $B5:A800+ | JSL $B5A8DA (de $B461 title) | Title screen sub — ADC #$0008, SEP #$20, DEC $37, BMI flow |
| $B5:D13B | $B5:D13B | JML $B5D13B (dispatch $8CE9) | Game mode entry? LDX #$01FF → TXS, STZ $2102, LDA #$1E01 → $420B |
| $B5:D4A7 | $B5:D4A7 | JML $B5D4A7 (dispatch $8CED) | Game mode entry |
| $B5:D334 | $B5:D334 | JML $B5D334 (dispatch $8CF1) | Game mode entry |

### Dispatch Table $8CC9-$8CFF
6 entries de mode handlers, acessadas via $8C9E (PHK/PLB → STA $24 → JSR $8CAC → JMP $862A).

| Entry | Addr | Type | Target | Descrição |
|---|---|---|---|---|
| 0 | $8CC9 | JSL | $BAB31B | Init (LDX #$01FF/TXS) → handler → JSL $80897C → BRA $8D1C |
| 1 | $8CD9 | JSL | $B4BE60 | Init → handler → JSL $80897C → BRA $8D1C |
| 2 | $8CE9 | JML | $B5D13B | Direct jump (ZERO stack reset, hands off) |
| 3 | $8CED | JML | $B5D4A7 | Direct jump |
| 4 | $8CF1 | JML | $B5D334 | Direct jump |
| 5 | $8CF5 | JSL | $B491D7 | Init → handler → JSL $80897C → BRL $8D1C |

Padrão: entries 0/1/5 fazem init completo (LDX #$01FF / TXS + JSL handler + JSL $80897C), entries 2/3/4 são hot-swap via JML (sem yield).

⚠️ **M/X fix aplicado:** override {0x8CC9: (False, False)} força X=0 (16-bit) na dispatch table. Anteriormente X=1 mostrava ORA ($9a,X) em vez de TXS. Entries agora corretas: `LDX #$01FF, TXS, INC $2A, JSL ...`.

### Bank $BB — Utility Functions (via JSL)
Bank $BB contém funções utilitárias (DMA, decompress, init) chamadas de bank $80/$B5.

| Entry | Função | Entrada | Descrição |
|---|---|---|---|
| $BB:8089 | Palette DMA Load | JSL de bank $80/$B5 | STA $4302 (VRAM dest), TXA×3→$4305 (size), LDA #$2200→$4300 (mode 4), SEP, LDA #$FD→$4304 (bank), TYA→$2121 (CGRAM addr), LDA #$01→$420B (DMA ch0 start), REP, RTL |
| $BB:8D91 | Decompress Data | A=src_ptr, X=dst_ptr, Y=flags | Save params, setup VRAM pointers ($2100/$7E), JSL $BB91AF, read 8-byte header [$34]+1, dispatch via high nibble of header[$27] to decode routines. Uses computed RTS (PEI+RTS) as jump table |
| $BB:91D9 | System Init | JSL de múltiplos locais | SEP #$20, STA $00420C=$00 (SA-1 ctrl), STA $004200=$01 (NMI), STA $002100=$8F (force blank max brt), REP, STZ $059B, RTL |
| $BB:91F7 | Sprite Table Init | JSL de $B3D7/$B5FA | JSR $91FB (init loop $16FE table: write $0D84+$5E×i for 25 entries), RTL |
| $BB:91AF | Sub-setup | JSL de $BB:8D91 | (sub-rotina da decompress) |

### WRAM Map
Documentação completa em `_wram_map.md`.

Highlights:
- **$0020**: NMI handler vector (JML target)
- **$0024**: Dispatch/mode selector
- **$002A**: Frame counter
- **$0512**: Brightness shadow (→ $2100)
- **$0513**: Fade duration
- **$0DE2-$0F5A**: Sprite table (25 entries × $5E = $0F5A)
- **$0619-$0636**: Channel handler system (8 slots)
- **$0032-$0057**: Decompress function temp vars

### Main Game Loop Handler ($B3D7+) — Detalhes
Entry: called via JMP ($0024) from bridge handler $8608. M=0, X=0 (16-bit A/X).

```
$B3D7: JSL $BB91D9      → init complementar (HDMA off, brightness)
       PHK/PLB           → DB = $80
       STZ $099B         → clear transition state
       STZ $060B         → clear gameplay flag
       JSR $8591         → VRAM clear via DMA
       JSL $80858B       → more init
       JSL $8088D2       → more init
       JSL $BB91F7       → more init
       JSL $B5800C       → bank $B5 entry 1
       STZ $2A           → frame counter = 0
       JSR $B560         → video mode setup (mode 1, tilemaps, palettes, data)
       LDA #$55AA/$FF00  → init $2E/$30 (magic signatures)
       Init sprite entries $0DE2-$0F5A (step $5E, 30 entries)
         Each: $01→[0], $0180→[6], $FF88→[$0A], $2000→[$12], Y×8+$0100→[$1A]
       SEP #$20, IRQ ack, FastROM on ($420D=$01)
       LDA #$0400 → JSR $8C32 (brightness set)
       JSR $8CAC → DMA init ($4300+)
       LDA #$0001 → STA $420B (enable DMA)
       JSR $8CAC → DMA init again
       LDA #$B461 → JMP $B0EE (entry dispatcher)
```

$B0EE entry dispatcher:
```
       STA $20           → set NMI handler for next frame
       SEP #$20          → 8-bit A
       LDA $4210 (×2)    → clear NMI flag
       AND #$80 / BNE    → spin until NMI clear
       LDA #$81/B1
       STA $4200         → NMI enable + auto-joypad
       STZ $4016         → joypad strobe reset
       WAI / BRA ←$B106  → wait for NMI
```

**Sub-handlers apontados por $B3D7→$B0EE:**

| Addr | Função |
|---|---|
| $B461 | **Title Screen** — animação de sprites ($0DE2+), JSL $B5A8DA, check $0512 vs $0F, input $0502 ($80D0), INC $099B on input, JSR $8C32 set transition |
| $B560 | **Video Mode Setup** (JSR) — mode 1 ($2105=$01), main screen $212C=$1001, tilemap $210B=$0024, window $2130=$0102, screen map $2107=$4C1C, color math (SEP #$20 PPU writes), load tiles via JSL $BB8D91 + DMA $80895F, load palette via JSL $BB8089, RTS |
| $B5FA | **Gameplay Init** — JSL $BB91D9/$808591/$80858B/$BB91F7, mode 1, load tileset ($0FA6+), load palette ($27CE+), set $0512=$0200, STZ $2A, LDA #$B681 → JMP $B0EE |
| $B681 | **Fade/Wait** — reset SP, color math, brightness restore, INC $2A, JSR $B061 (joypad)/$8C3D (fade), when $2A=$70 set $0513=$0082 (fade out), wait brightness=0 → JML $8085EF (back to boot flow) |

## Key Tools
- `tools/analysis/_boot_disasm_v2.txt` — Boot code disasm (0x83F7-0x85FD)
- `tools/analysis/_disasm_boot.py` — 65816 disassembler com tracking m/x
- `tools/analysis/_find_sa1_init.py` — Scan SA-1 writes first 2MB
- `tools/analysis/_find_sa1_reset.py` — Full ROM SA-1 scan
- `tools/analysis/_find_bwram_copy.py` — SA-1 DMA pattern search
- `tools/analysis/_map_verify.py` — Mapping verification scripts
- `tools/analysis/_trace_main*.py` — Main entry disassembly
- `tools/analysis/_trace_postload*.py` — Post-VRAM-clear disassembly
- `tools/analysis/_trace_handlers.py` — Event handler disassembly ($93B8+)
- `tools/analysis/_trace_nmi.py` — NMI handler analysis
- `tools/analysis/_find_handler_chain.py` — Handler transition scan
- `tools/analysis/_find_rti_and_sta20.py` — RTI/STA $20 pattern search
- `tools/analysis/_final_check*.py` — Dispatch table parsing
- `tools/analysis/_handler_disasms.txt` — Full handler disassembly output
- `tools/analysis/_disasm_all.txt` — Disassembly atualizado de todos os handlers ($99C3, $8C3D, $A5F1, $A2CF, $A86C)

## Legend
- ✅ = completo
- Em aberto = pendente

## Next Possible Steps
1. ✅ **Disassemblar $B5 functions** — entender init API completa
2. ✅ **Disassemblar $BB functions** ($8D91, $91D9) — entender sistema de loading
3. ✅ **Analisar dispatch table $8CCE** — mapear eventos do jogo (6 entries)
4. ✅ **Main game loop localizado** — NMI-driven dispatch via JMP ($0020) + ($0024)
5. ✅ **Cadeia de handlers mapeada** — $93B8 → $95B3 → $964C → $8085EF → $8608 → $B3D7
6. ✅ **NMI handler completo** — $F3C1-$F3FA
7. ✅ **Title handler $B461** — disassemblado
8. ✅ **Gameplay entry $A5F1** — disassemblado até $A800
9. ✅ **Attract/Level Select $A2CF** — disassemblado
10. ✅ **HDMA controller $A86C** — disassemblado
11. ✅ **Menu handler $99C3** — disassemblado
12. ✅ **Fade controller $8C3D** — disassemblado (mecanismo de transição brightness)
13. ✅ **Disassemblar $B3D7+** — game loop principal (title screen, menu)
14. ✅ **Compression format analyzed** — $BB:8D91 is a custom bytecode VM
    - 16 primary opcodes (high nibble), 16 secondary (low nibble)
    - Header: 4 context bytes + 16-bit word + 32-byte data pool
    - Format byte at offset $27 selects opcode pair
    - Uses PEI/RTS computed jump dispatch via $BB:8000 table
    - Direct VRAM DMA on termination when $32 ≠ $FFFF
    - Documented in `_compression.md`
    - Python decoder at `_decompress.py` (14/16 primaries, 12/16 secondaries)
    - Table abstraction: `table1` ($7E:2000, count/offset) and `table2` ($7E:2100, OR-mask)
    - Opcodes needing WRAM tables: primary 1/2 (OR-copy), secondary 0/3/4/5 (indirect fill/copy)
15. ✅ **Mapear WRAM layout** — $090F (flags), $0512 (brightness), $0502/$0506 (joypad)
16. ✅ **Corrigir disassembler** — override M/X via dict, propagação para JSR/JSL targets
17. ✅ **Joypad handler $B061 disassembled** — JSR de $B3D7 process chain, reads $0502/$0506
18. 🔄 **Decoder secondary ops 9-12 implemented** (BackRefExtra2, TwoExt, Var, 16Shift) — need WRAM table context to test

