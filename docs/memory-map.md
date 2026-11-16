# Memory Map — DKC2 (SNES)

Schema padronizado para registrar enderecos de memoria do DKC2 durante engenharia reversa.

## Formato do Schema (JSON por endereco)

```json
{
  "address": "0x7E0000",
  "name": "player_x_position",
  "type": "word",
  "signed": false,
  "system": "player",
  "description": "Posicao X do jogador no mapa (pixels)",
  "flags_m": false,
  "flags_x": false,
  "notes": "Observacoes sobre comportamento, valores limites, etc.",
  "references": ["0xC0DEAD", "0xBEEF00"],
  "emu_test": {
    "emu": "Mesen2",
    "version": "2.x",
    "initial_value": 0,
    "test_scenario": "Queda do inicio da fase — verificar se zera ao morrer"
  }
}
```

## Campos

| Campo | Tipo | Obrigatorio | Descricao |
|-------|------|-------------|-----------|
| `address` | string (hex) | sim | Endereco no espaco de memoria SNES (formato `0x7EXXXX`) |
| `name` | string | sim | Nome descritivo em snake_case |
| `type` | string | sim | `byte` (8 bits) ou `word` (16 bits) |
| `signed` | boolean | nao | Se o valor e signed (`true`) ou unsigned (`false`, default) |
| `system` | string | sim | Subsistema: `player`, `camera`, `enemy`, `barrel`, `rope`, `input`, `audio`, `video`, `engine`, `unknown` |
| `description` | string | sim | Comportamento do endereco em linguagem natural |
| `flags_m` | boolean | nao | Estado do flag M (memory/accumulator width) no momento da leitura |
| `flags_x` | boolean | nao | Estado do flag X (index register width) no momento da leitura |
| `notes` | string | nao | Observacoes, valores conhecidos, edge cases |
| `references` | array[string] | nao | Enderecos de codigo que leem/escrevem este endereco |
| `emu_test` | object | nao | Teste empirico: emulador usado, versao, valor inicial, cenario |

## Valores para `system`

| system | Descricao |
|--------|-----------|
| `player` | Estado do jogador (posicao, velocidade, vidas, moedas, DK coins, banana bunch, etc.) |
| `camera` | Scroll da camera, boundaries de tela |
| `enemy` | Estado de inimigos (posicao, hp, AI state, spawn) |
| `barrel` | Estado dos barris (posicao, direction, tipo: DK/standard/steel) |
| `rope` | Estado das cordas/vinhas (posicao, estado) |
| `input` | Input lido do controller (buttons, D-pad) |
| `audio` | Estado do engine de audio (music ID, SFX ID, volume) |
| `video` | Estado do video (mode 7, palettes, PPU registers) |
| `engine` | Estado interno da engine (game state, frame counter, IRQ, DMA) |
| `unknown` | Endereco identificado mas sistema nao determinado |
| `flag` | Flag global (ex: modo multiplayer, chave coletada, animal amigo ativo) |

## Convencoes

- Enderecos WRAM (Work RAM) SNES comecam em `0x7E0000`
- Enderecos SRAM (Save RAM) comecam em `0x70xxxx` (se usados)
- Enderecos de registros de hardware (PPU, APU, DMA) em `0x2100`-`0x43FF`
- Usar `byte` para registros de 8 bits, `word` para 16 bits (little-endian)
- `flags_m`/`flags_x` documentam o modo do processador 65C816 no momento:
  - M=0 (16-bit accumulator), M=1 (8-bit accumulator)
  - X=0 (16-bit index), X=1 (8-bit index)
- Ao encontrar um endereco, preencher o maximo de campos possivel, mesmo que parciais

## Entradas Mapeadas

### WRAM — DP Registers ($00-$FF)

```json
{
  "address": "0x000082",
  "name": "frame_index",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "Frame index toggling between 0 and 6 cada NMI. Usado para indexar slot arrays (2 slots: DK + Diddy). Toggle via EOR #$0006 no NMI handler.",
  "references": ["0xC0891B", "0xC08919", "0xC0852D", "0xC0878B"]
},
{
  "address": "0x000084",
  "name": "frame_index_minus_2",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "frame_index - 2. Atualizado via DEC A, DEC A apos frame toggle.",
  "references": ["0xC08532", "0xC08922"]
},
{
  "address": "0x000086",
  "name": "frame_index_secondary",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "Secondary frame/temp index usado durante processamento de slot.",
  "references": ["0xC08637", "0xC08639", "0xC0863C"]
},
{
  "address": "0x000076",
  "name": "temp_slot_state",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "Temp storage para slot state durante swap/processamento entre frames.",
  "references": ["0xC08648", "0xC08665", "0xC085BA"]
},
{
  "address": "0x000022",
  "name": "dp_init_FF00",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "Inicializado com $FF00 no init. Funcao desconhecida.",
  "references": ["0xC0802C"]
},
{
  "address": "0x000034",
  "name": "dp_init_1234",
  "type": "word",
  "signed": false,
  "system": "unknown",
  "description": "Inicializado com $1234 no init. Funcao desconhecida.",
  "references": ["0xC08037"]
},

{
  "address": "0x00003E",
  "name": "dp_sa1_state",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "State para dispatch SA-1. Comparam com $0038 e $003B. Usado no handler compartilhado ($C088F9) para selecionar funcao SA-1 via tabela de ponteiros em ROM.",
  "references": ["0xC0805D", "0xC088FB", "0xC08900"]
}
```

```json
{
  "address": "0x000032",
  "name": "sa1_state_reg",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "SA-1 state register. Comparado com $0004/$0008 no state A handler. Usado em conjunto com $3E (sa1_state) na funcao C08895 para lookup de timer/value.",
  "references": ["0xC0889C", "0xC088B0", "0xC0A14B"]
},
{
  "address": "0x000038",
  "name": "prng_lfsr_lo",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "LFSR baja para PRNG. Inicializado com $AA55 no init. Usado com $39/$3A/$3B em LFSR step (func_C0C21C). Rotacionado a cada poll.",
  "references": ["0xC08066", "0xC0C21C"]
},
{
  "address": "0x00003A",
  "name": "prng_lfsr_hi",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "LFSR alta para PRNG. Inicializado com $3765. Parceiro de $38 no gerador pseudoaleatorio.",
  "references": ["0xC0806B", "0xC0C21C"]
},
{
  "address": "0x00003C",
  "name": "prng_counter",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "Contador/seed para PRNG. Inicializado com $002C em func_BA23.",
  "references": ["0xC0BA34", "0xC0C21C"]
},
{
  "address": "0x000042",
  "name": "joypad_edge_prev",
  "type": "word",
  "signed": false,
  "system": "input",
  "description": "Frame anterior do joypad para deteccao de borda (edge trigger). Usado com $44 em func_C0A252.",
  "references": ["0xC0A252", "0xC0BA23", "0xC0C15A"]
},
{
  "address": "0x000044",
  "name": "joypad_edge_curr",
  "type": "word",
  "signed": false,
  "system": "input",
  "description": "Frame atual do joypad para deteccao de borda. Atualizado apos ler $4218/$421A.",
  "references": ["0xC0A252", "0xC0C15A"]
},
{
  "address": "0x00004C",
  "name": "dma_vram_addr",
  "type": "word",
  "signed": false,
  "system": "video",
  "description": "Endereco VRAM temporario para DMA. STA $2116 via DP. Usado em func_C0C0B7 e func_C0FE4A.",
  "references": ["0xC0C0B7", "0xC0FE4A"]
},
{
  "address": "0x00006C",
  "name": "div_tmp_quotient",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "Temporario para divisao por hardware. Usado em func_C0FDEE (div) e func_C0FE4A (VRAM tile calc).",
  "references": ["0xC0FDEE", "0xC0FE4A"]
}
```

### WRAM — Work Table Pointers ($0500-$050C)

```json
{
  "address": "0x7E050A",
  "name": "slot_work_table_base",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "Base pointer for slot work table. Escrito em func_C081C7. $050C = 0 como low word complement.",
  "references": ["0xC081C7"]
},
{
  "address": "0x7E050C",
  "name": "slot_work_table_low",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "Low word of slot work table ($050A), sempre zerado.",
  "references": ["0xC081CA", "0xC081D2"]
}
```

### WRAM — Sprite Slot Work Area ($0400-$041E)

```json
{
  "address": "0x7E0400",
  "name": "sprite_slot_work_00",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "Per-slot work area. 16 words ($0400-$041E) zerados no area init (func_C0A14B). Cada slot da engine (16) tem 2 bytes de work area contiguos. Gap = 2 bytes.",
  "references": ["0xC0A159", "0xC0A15C", "0xC0A15F", "0xC0A162", "0xC0A165", "0xC0A168", "0xC0A16B", "0xC0A16E", "0xC0A171", "0xC0A174", "0xC0A177", "0xC0A17A", "0xC0A17D", "0xC0A180", "0xC0A183", "0xC0A186"]
}
```

### WRAM — Area Config ($0535)

```json
{
  "address": "0x7E0535",
  "name": "area_id",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "Area/level ID. Lido em func_C0A14B durante area init. Provavelmente usado para lookup de config de fase.",
  "references": ["0xC0A1A1"]
}
```

### WRAM — Sprite Generation ($0610)

```json
{
  "address": "0x7E0610",
  "name": "sprite_gen_index",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "Sprite generation counter/shift register. Deslocado left (<<= 1) em func_C00000 (init sequence).",
  "references": ["0xC00005"]
}
```

### WRAM — Video/Fade Registers ($0887-$0896)

```json
{
  "address": "0x7E0887",
  "name": "bg_layer_config",
  "type": "word",
  "signed": false,
  "system": "video",
  "description": "BG layer configuration flag. Escrito em func_C0EE3F durante setup de background.",
  "references": ["0xC0EE47"]
},
{
  "address": "0x7E088C",
  "name": "brightness_color_shift",
  "type": "word",
  "signed": false,
  "system": "video",
  "description": "Color shift component para fade. Usado em func_C08E87 com AND $000F e OR $00E0 para calcular valor do register $2132 (color math).",
  "references": ["0xC08EC8"]
},
{
  "address": "0x7E0896",
  "name": "palette_cycle_step",
  "type": "word",
  "signed": false,
  "system": "video",
  "description": "Segundo timer/counter de ciclo de paleta. Escrito em $2112 (CGADD) junto com $0895.",
  "references": ["0xC08EB8"]
}
```

### WRAM — Sprite Property Arrays ($0AB1-$11A1)

```json
{
  "address": "0x7E0AB1",
  "name": "sprite_prop_array",
  "type": "word",
  "signed": false,
  "system": "enemy",
  "description": "Sprite property array, indexado por slot X. Escrito em func_C0A1EF.",
  "references": ["0xC0A1F3"]
},
{
  "address": "0x7E0B8F",
  "name": "slot_x_position_ext",
  "type": "word",
  "signed": false,
  "system": "player",
  "description": "Extended X position do slot (provavelmente subpixel ou camera-relative). Escrito em func_C0EDCE (player init).",
  "references": ["0xC0EDD7"]
},
{
  "address": "0x7E0C6B",
  "name": "slot_y_position_ext",
  "type": "word",
  "signed": false,
  "system": "player",
  "description": "Extended Y position do slot (subpixel ou modificador). Escrito em func_C0EDCE.",
  "references": ["0xC0EE03", "0xC0EE23"]
},
{
  "address": "0x7E0D47",
  "name": "slot_spawn_param_ext",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "Extended spawn parameter do slot. Escrito em func_C0EDCE junto com $0D45.",
  "references": ["0xC0EDFD"]
},
{
  "address": "0x7E11A1",
  "name": "slot_group_mask",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "Slot group mask array, zerado em sprite init type B (func_855E). Provavelmente controla qual grupo grafico o sprite pertence.",
  "references": ["0xC0857E"]
},
{
  "address": "0x7E0AE5",
  "name": "slot_flag_array",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "Array de flags por slot, zerado em sprite init type B (func_855E). Indexado por frame_index ($82).",
  "references": ["0xC0855E"]
},
{
  "address": "0x7E0D11",
  "name": "slot_enable_array",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "Array de enable flags por slot, zerado em sprite init type B.",
  "references": ["0xC0855E"]
}
```

### WRAM — Sprite Data Arrays ($0687, $06A7)

```json
{
  "address": "0x7E0687",
  "name": "sprite_code_id",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "Sprite code ID array, indexado por slot. Escrito em func_C0EE3F durante setup grafico.",
  "references": ["0xC0EE88"]
},
{
  "address": "0x7E06A7",
  "name": "sprite_gfx_bank",
  "type": "word",
  "signed": false,
  "system": "video",
  "description": "Sprite graphics bank/offset array, indexado por slot. Escrito em func_C0EE3F.",
  "references": ["0xC0EE99"]
}
```

### WRAM — State Machine ($1B17-$1E29)

```json
{
  "address": "0x7E1B17",
  "name": "state_machine_var_a",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "Variavel A do state machine em func_C09BE7. Usada como accumulator de estado durante update loop.",
  "references": ["0xC09C23", "0xC09C35"]
},
{
  "address": "0x7E1B19",
  "name": "state_machine_var_b",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "Variavel B do state machine. Atualizada junto com $1B17 em func_C09BE7.",
  "references": ["0xC09C2A", "0xC09C3B"]
},
{
  "address": "0x7E1B29",
  "name": "event_queue_count",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "Contador de eventos na fila $1B2B. Decrementado a cada processamento em func_C0A7B5.",
  "references": ["0xC0A7B5"]
},
{
  "address": "0x7E1B2B",
  "name": "event_queue",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "Fila de eventos. Array indexado por X (event index). Zerado apos processamento em func_C0A7B5.",
  "references": ["0xC0A7C6", "0xC0A7DD"]
},
{
  "address": "0x7E1DFF",
  "name": "level_timer",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "Level/area timer. Deslocado left (<<= 1) em func_C005A9. Provavelmente contagem regressiva ou frame counter de fase.",
  "references": ["0xC005B0"]
},
{
  "address": "0x7E1E29",
  "name": "state_machine_trigger",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "Trigger para state machine. Setado como non-zero para iniciar processamento, zerado apos execucao em func_C09BE7.",
  "references": ["0xC09BF7", "0xC09BFC"]
}
```

### WRAM — IRQ/Timers ($1E15-$1E45)

```json
{
  "address": "0x7E1E15",
  "name": "irq_flags",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "IRQ/flags register. Bit 0x0008 e 0x0004 testados em func_C08E87 (vblank/fade). Usado para controle de fluxo de fade.",
  "references": ["0xC08EC0", "0xC08EE2"]
},
{
  "address": "0x7E1E1D",
  "name": "fade_timer",
  "type": "word",
  "signed": false,
  "system": "video",
  "description": "Fade timer. Decrementado a cada frame durante ciclo de fade em func_C08E87. Controle de paleta fade (CGRAM write via $2122).",
  "references": ["0xC08EF6", "0xC08F01"]
},
{
  "address": "0x7E1E45",
  "name": "sprite_total_count",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "Sprite total count. Carregado em X em func_C0A14B durante area init. Define numero de entradas de sprite na area atual.",
  "references": ["0xC0A1BB"]
}
```

### Engine — SA-1 Dispatch

```json
{
  "address": "0x008DF9",
  "name": "sa1_func_table_entry_0038",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "Tabela de ponteiros de funcao SA-1 em ROM. Carregado por LDY $8DF9 quando dp_sa1_state ($3E) == $0038. Valor = $088B = func_state_A ($C0088B).",
  "references": ["0xC08906", "0xC08909"]
},
{
  "address": "0x008E21",
  "name": "sa1_func_table_entry_003B",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "Tabela de ponteiros de funcao SA-1 em ROM. Carregado por LDY $8E21 quando dp_sa1_state ($3E) == $003B. Valor = $EB21 = func_C0EB21 (novo bloco de codigo).",
  "references": ["0xC0890E", "0xC08911"]
}
```

```json
{
  "address": "0x7E0500",
  "name": "controller_hold_1",
  "type": "word",
  "signed": false,
  "system": "input",
  "description": "Estado hold do controller 1. Atualizado em func_C0A252 via hardware $4218. Usado por sprite init e flags.",
  "references": ["0xC0A243", "0xC0A252", "0xC0C0FB", "0xC0C15A"]
},
{
  "address": "0x7E0502",
  "name": "controller_hold_2",
  "type": "word",
  "signed": false,
  "system": "input",
  "description": "Estado hold do controller 2. Atualizado em func_C0A252 via hardware $421A.",
  "references": ["0xC0A252", "0xC0C0FB", "0xC0C15A"]
},
{
  "address": "0x7E0504",
  "name": "controller_edge_1",
  "type": "word",
  "signed": false,
  "system": "input",
  "description": "Bordas de subida do controller 1. Gerado por EOR entre hold atual e anterior.",
  "references": ["0xC0A252", "0xC0C0FB", "0xC0C15A"]
},
{
  "address": "0x7E0506",
  "name": "controller_edge_2",
  "type": "word",
  "signed": false,
  "system": "input",
  "description": "Bordas de subida do controller 2.",
  "references": ["0xC0A252", "0xC0C0FB", "0xC0C15A"]
},
{
  "address": "0x7E0508",
  "name": "slot_work_table_ptr",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "Ponteiro para tabela de trabalho do slot. Usado em func_C081C7 para lookup indexado.",
  "references": ["0xC081C7"]
},
{
  "address": "0x7E050E",
  "name": "controller_raw_1",
  "type": "word",
  "signed": false,
  "system": "input",
  "description": "Raw read do controller 1 antes do edge processing.",
  "references": ["0xC0A252", "0xC0C15A"]
},
{
  "address": "0x7E0510",
  "name": "controller_raw_2",
  "type": "word",
  "signed": false,
  "system": "input",
  "description": "Raw read do controller 2 antes do edge processing.",
  "references": ["0xC0A252", "0xC0C15A"]
},
{
  "address": "0x7E051A",
  "name": "frame_counter_hi",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "Frame counter high word (32-bit). Incrementado em func_C0AF6E. Usado para timeout logic.",
  "references": ["0xC0AF6E", "0xC0E9B4"]
},
{
  "address": "0x7E051C",
  "name": "frame_counter_lo",
  "type": "byte",
  "signed": false,
  "system": "engine",
  "description": "Frame counter low byte. Overflow incrementa $051A. Zerado em init.",
  "references": ["0xC0AF6E"]
},
{
  "address": "0x7E0579",
  "name": "sprite_group_flags",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "Flags de grupo de sprite. Lido/alterado em func_855E (sprite init type B). Usado em EOR/AND mask operations. Controla quais grupos de sprite estao ativos.",
  "references": ["0xC0855E", "0xC09BE7", "0xC0A252", "0xC0EDCE"]
},
{
  "address": "0x7E088B",
  "name": "brightness_value",
  "type": "word",
  "signed": false,
  "system": "video",
  "description": "Valor de brightness para HDMA fade. Usado em func_C08E87 para ciclo de fade in/out. Decrementado ate 0 e entao incrementado ate $0F.",
  "references": ["0xC08E87", "0xC0A14B"]
},
{
  "address": "0x7E0895",
  "name": "palette_cycle_timer",
  "type": "word",
  "signed": false,
  "system": "video",
  "description": "Timer para ciclo de paleta. Usado em func_C08E87 e func_C0A14B. Controle de fade rate.",
  "references": ["0xC08E87", "0xC0A14B", "0xC0EE3F"]
},
{
  "address": "0x7E0AE5",
  "name": "slot_flag_array",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "Array de flags por slot, zerado em sprite init type B (func_855E). Index = frame_index.",
  "references": ["0xC0855E"]
},
{
  "address": "0x7E0D11",
  "name": "slot_enable_array",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "Array de enable flags por slot, zerado em sprite init type B.",
  "references": ["0xC0855E"]
},
{
  "address": "0x7E0D45",
  "name": "slot_spawn_state",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "Array de spawn state por slot. Lido em func_C085B8 (sprite init type C). Usado em func_C0E696 para scan de primeiro zero.",
  "references": ["0xC085B8", "0xC0E696", "0xC0EDCE"]
},
{
  "address": "0x7E0E89",
  "name": "slot_misc_array_1",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "Array miscelanea por slot. Escrito em func_C0877C e func_C08811 (sprite spawners). Indexado por frame_index ($82) e Y.",
  "references": ["0xC0877C", "0xC08811"]
},
{
  "address": "0x7E0EF1",
  "name": "slot_misc_array_2",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "Array miscelanea por slot (segundo set). Zerado no spawn se condicao atendida.",
  "references": ["0xC0877C", "0xC08811"]
},
{
  "address": "0x7E1105",
  "name": "player_spawn_x",
  "type": "word",
  "signed": false,
  "system": "player",
  "description": "Posicao X de spawn do jogador. Escrito em func_C0EDCE (player init).",
  "references": ["0xC0EDCE"]
},
{
  "address": "0x7E1107",
  "name": "player_spawn_y",
  "type": "word",
  "signed": false,
  "system": "player",
  "description": "Posicao Y de spawn do jogador.",
  "references": ["0xC0EDCE"]
},
{
  "address": "0x7E1929",
  "name": "global_event_flag",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "Flag global de evento. Setado em func_C0888B (state A handler) com $0001. Lido em func_C09BE7 (state machine) e func_C0A7B5 (event queue). Resetado apos processamento.",
  "references": ["0xC0877C", "0xC08811", "0xC0888B", "0xC09BE7", "0xC0A7B5"]
},

{
  "address": "0x7E1DF1",
  "name": "timer_global_a",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "Timer global A. Usado em func_C0AF6E (timer/counter) e func_C0A14B (area init).",
  "references": ["0xC0A14B", "0xC0AF6E"]
},
{
  "address": "0x7E1DF3",
  "name": "timer_global_b",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "Timer global B. Escrito quando $051A timeout atinge threshold.",
  "references": ["0xC0AF6E"]
},
{
  "address": "0x7E306057",
  "name": "attract_frame_counter",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "Frame counter para attract mode / title screen. Em $30:6057 (bank $30, extended RAM). Incrementado em func_C0E9B4.",
  "references": ["0xC0E9B4"]
}
```

### WRAM — Slot Arrays (gap = 6 bytes por slot, indexado por frame_index)

```json
{
  "address": "0x7E0512",
  "name": "slot_active",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "Slot active state. Array indexado por frame_index ($82). Slot0=0x0512, Slot1=0x0518 (gap 6). Usado no NMI/IRQ dispatch para verificar se slot esta ativo. Valor non-zero = slot ocupado.",
  "references": ["0xC08535", "0xC08538", "0xC08639"]
},
{
  "address": "0x7E0516",
  "name": "game_phase",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "Global game phase/state. Usado em dispatch table (func_8687) para selecionar handler: 9=$885F, A=$888B, B=$88B0, C=$88E3. Provavelmente loading, menu, gameplay, etc.",
  "references": ["0xC0868A", "0xC0868D", "0xC0868F", "0xC08692", "0xC08694", "0xC08697", "0xC08699", "0xC0869C"]
},
{
  "address": "0x7E0521",
  "name": "init_flag_FFFF",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "Inicializado com $FFFF no init. Funcao desconhecida.",
  "references": ["0xC08031"]
},
{
  "address": "0x7E056F",
  "name": "init_flag_0001",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "Inicializado com $0001 no init. Funcao desconhecida.",
  "references": ["0xC0BA2A"]
},
{
  "address": "0x7E0B19",
  "name": "slot_x_position",
  "type": "word",
  "signed": false,
  "system": "player",
  "description": "Slot X position (pixels). Array indexado por frame_index ($82). Slot0=0x0B19, Slot1=0x0B1F.",
  "references": ["0xC08659", "0xC0865C"]
},
{
  "address": "0x7E0BC1",
  "name": "slot_y_position",
  "type": "word",
  "signed": false,
  "system": "player",
  "description": "Slot Y position (pixels). Array indexado por frame_index ($82). Slot0=0x0BC1, Slot1=0x0BC7.",
  "references": ["0xC0865F", "0xC08662"]
},
{
  "address": "0x7E0B8D",
  "name": "slot_sprite_type",
  "type": "word",
  "signed": false,
  "system": "player",
  "description": "Slot sprite type/variant. Valores observados: $00D8, $00DC, $00E4. Array indexado por frame_index ($82). Slot0=0x0B8D, Slot1=0x0B93.",
  "references": ["0xC08676", "0xC0867C", "0xC0854C", "0xC0892C"]
},
{
  "address": "0x7E0C69",
  "name": "slot_attr_flags",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "Slot attribute flags usando XOR bit blending. Bitmask 0x0E00 e usado para toggle/merge atributos entre slots. Array indexado por frame_index ($82). Slot0=0x0C69, Slot1=0x0C6F.",
  "references": ["0xC08645", "0xC0864A", "0xC08650", "0xC08656", "0xC08667", "0xC08670"]
},
{
  "address": "0x7E1029",
  "name": "slot_timer",
  "type": "word",
  "signed": false,
  "system": "engine",
  "description": "Slot timer/data. Valores observados: $0030, $002B, $0060, $0014, $0031, $0046. Array indexado por frame_index ($82). Slot0=0x1029, Slot1=0x102F.",
  "references": ["0xC08553", "0xC0853D", "0xC08629", "0xC085FD", "0xC08608"]
},
{
  "address": "0x7E1375",
  "name": "slot_sprite_mapping",
  "type": "word",
  "signed": false,
  "system": "player",
  "description": "Slot sprite/object mapping. Array indexado por frame_index ($82). Slot0=0x1375, Slot1=0x137B.",
  "references": ["0xC08640"]
}
```
