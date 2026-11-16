# RAM Map — DKC2 Player

Mapeamento dos enderecos WRAM relacionados ao jogador (player slot).
Dois slots stride=6: Slot0 = personagem ativo (DK/Diddy), Slot1 = parceiro.
Indexado por `frame_index` ($0082), alterna 0/6 a cada NMI.

## Convencoes

- Enderecos `0x7EXXXX` em SNES mapping (LoROM)
- `byte` = 8 bits, `word` = 16 bits little-endian
- Flags M/X: M=0 (16-bit acc), M=1 (8-bit acc); X=0 (16-bit index), X=1 (8-bit index)
- `stride=6`: offset entre Slot0 e Slot1

## Player Slot Arrays (stride=6, indexado por `$82` = 0 ou 6)

| Address | Slot0 | Slot1 | Name | Type | Descricao |
|---------|-------|-------|------|------|-----------|
| +$0B19 | `0x7E0B19` | `0x7E0B1F` | `slot_x_position` | word | Posicao X do slot no mapa (pixels) |
| +$0B8D | `0x7E0B8D` | `0x7E0B93` | `slot_sprite_type` | word | Tipo de sprite/variante. Init=$0100. Valores obs: $00D8, $00DC, $00E4 |
| +$0B8F | `0x7E0B8F` | `0x7E0B95` | `slot_x_position_ext` | word | Posicao X estendida (subpixel ou camera-relative) |
| +$0BC1 | `0x7E0BC1` | `0x7E0BC7` | `slot_y_position` | word | Posicao Y do slot no mapa (pixels) |
| +$0C69 | `0x7E0C69` | `0x7E0C6F` | `slot_attr_flags` | word | Atributos do slot (bitmask, XOR merge). Init=$2800/$2A40 |
| +$0C6B | `0x7E0C6B` | `0x7E0C71` | `slot_y_position_ext` | word | Posicao Y estendida (subpixel ou modificador) |
| +$0D45 | `0x7E0D45` | `0x7E0D4B` | `slot_spawn_state` | word | Estado de spawn. Init=$0004. Scan por primeiro zero |
| +$0D47 | `0x7E0D47` | `0x7E0D4D` | `slot_spawn_param_ext` | word | Parametro estendido de spawn |
| +$1029 | `0x7E1029` | `0x7E102F` | `slot_timer` | word | Timer do slot. Init=$0030/$002B. Valores: $0030, $002B, $0060, $0014 |
| +$1375 | `0x7E1375` | `0x7E137B` | `slot_sprite_mapping` | word | Mapeamento sprite/objeto do slot |

### Write Sources

| Address | Escrito por | Descricao |
|---------|-------------|-----------|
| `0x7E0B8D` | func_C0EDCE ($C0EDD1), func_C0852D ($C0854C) | Init player / NMI slot init |
| `0x7E0B8F` | func_C0EDCE ($C0EDD7) | Init player |
| `0x7E0BC1` | (referenciado em func_C0A14B) | Usado em calculo de camera |
| `0x7E0C69` | func_C0EDCE ($C0EDE9) | Init player, valores variam por personagem |
| `0x7E0C6B` | func_C0EDCE ($C0EE03/$C0EE23) | Init player, complemento attr |
| `0x7E0D45` | func_C0EDCE ($C0EDE3) | Init spawn param |
| `0x7E0D47` | func_C0EDCE ($C0EDFD) | Init spawn param ext |
| `0x7E1029` | func_C0852D ($C0853D/$C08553) | NMI slot init |
| `0x7E1375` | (referenciado em func_C08640) | Slot dispatch |

## Player Spawn Data

| Address | Name | Type | Descricao | Init Value |
|---------|------|------|-----------|------------|
| `0x7E1105` | `player_spawn_x` | word | Posicao X de spawn | $0032 ou $0034 (por personagem) |
| `0x7E1107` | `player_spawn_y` | word | Posicao Y de spawn | $0032 (DK) ou $0034 (Diddy) |

## Engine Registers (DP, $00-$FF via Direct Page = $0000)

| Address | Name | Type | System | Descricao |
|---------|------|------|--------|-----------|
| `0x000022` | `dp_init_FF00` | word | engine | Init com $FF00. Funcao desconhecida |
| `0x000032` | `sa1_state_reg` | word | engine | SA-1 state register, comparado com $0004/$0008 |
| `0x000034` | `dp_init_1234` | word | unknown | Init com $1234 |
| `0x000038` | `prng_lfsr_lo` | word | engine | LFSR baixa para PRNG. Init=$AA55 |
| `0x00003A` | `prng_lfsr_hi` | word | engine | LFSR alta para PRNG. Init=$3765 |
| `0x00003C` | `prng_counter` | word | engine | Contador/seed PRNG. Init=$002C |
| `0x00003E` | `dp_sa1_state` | word | engine | State dispatch SA-1 |
| `0x000042` | `joypad_edge_prev` | word | input | Frame anterior do joypad (edge detect) |
| `0x000044` | `joypad_edge_curr` | word | input | Frame atual do joypad (edge detect) |
| `0x00004C` | `dma_vram_addr` | word | video | Endereco VRAM temporario para DMA |
| `0x00006C` | `div_tmp_quotient` | word | engine | Temp para divisao por hardware |
| `0x000076` | `temp_slot_state` | word | engine | Temp storage para slot state durante swap |
| `0x000082` | `frame_index` | word | engine | Frame index (0/6), toggle a cada NMI |
| `0x000084` | `frame_index_minus_2` | word | engine | frame_index - 2 |
| `0x000086` | `frame_index_secondary` | word | engine | Secondary index usado durante processamento |

## Input Registers ($7E0500-$7E0510)

| Address | Name | Type | Descricao |
|---------|------|------|-----------|
| `0x7E0500` | `controller_hold_1` | word | Estado hold do controller 1 (lido de $4218) |
| `0x7E0502` | `controller_hold_2` | word | Estado hold do controller 2 (lido de $421A) |
| `0x7E0504` | `controller_edge_1` | word | Borda de subida do controller 1 |
| `0x7E0506` | `controller_edge_2` | word | Borda de subida do controller 2 |
| `0x7E050E` | `controller_raw_1` | word | Raw read controller 1 (pos-edge processing) |
| `0x7E0510` | `controller_raw_2` | word | Raw read controller 2 (pos-edge processing) |

### Input Mapping (bitmask SNES controller)

| Bit | Button | DKC2 Use |
|-----|--------|----------|
| 0 | B | Jump, Confirm |
| 1 | Y | Roll, Cancel |
| 2 | Select | (unknown) |
| 3 | Start | Pause |
| 4 | Up | D-Pad |
| 5 | Down | D-Pad |
| 6 | Left | D-Pad |
| 7 | Right | D-Pad |
| 8 | A | (action button, specific use) |
| 9 | X | (action button, specific use) |
| 10 | L | (shoulder, specific use) |
| 11 | R | (shoulder, specific use) |

## Engine State ($7E0512-$7E0521)

| Address | Name | Type | Descricao |
|---------|------|------|-----------|
| `0x7E0512` | `slot_active` | word | Slot active state (por slot index). Non-zero = ocupado |
| `0x7E0516` | `game_phase` | word | Fase do jogo: 9=menu, A=load, B=gameplay, C=transition |
| `0x7E051A` | `frame_counter_hi` | word | Frame counter high word (32-bit) |
| `0x7E051C` | `frame_counter_lo` | byte | Frame counter low byte |
| `0x7E0521` | `init_flag_FFFF` | word | Init com $FFFF |

## Game State ($7E056F-$7E0AE5)

| Address | Name | Type | System | Descricao |
|---------|------|------|--------|-----------|
| `0x7E056F` | `init_flag_0001` | word | engine | Init com $0001. Usado para check de modo |
| `0x7E0579` | `sprite_group_flags` | word | engine | Flags de grupo de sprite. Bit 0 testado no player init |
| `0x7E0610` | `sprite_gen_index` | word | engine | Shift register para geracao de sprite |
| `0x7E0687` | `sprite_code_id` | word | engine | Sprite code ID array (por slot) |
| `0x7E06A7` | `sprite_gfx_bank` | word | video | Sprite graphics bank/offset array (por slot) |
| `0x7E088B` | `brightness_value` | word | video | Brightness para HDMA fade |
| `0x7E088C` | `brightness_color_shift` | word | video | Color shift para fade |
| `0x7E0895` | `palette_cycle_timer` | word | video | Timer para ciclo de paleta |
| `0x7E0896` | `palette_cycle_step` | word | video | Segundo timer de ciclo de paleta |
| `0x7E0AE5` | `slot_flag_array` | word | engine | Array de flags por slot |
| `0x7E0AB1` | `sprite_prop_array` | word | enemy | Sprite property array (por slot X) |
| `0x7E0D11` | `slot_enable_array` | word | engine | Array de enable flags por slot |
| `0x7E0E89` | `slot_misc_array_1` | word | engine | Array miscelanea por slot |
| `0x7E0EF1` | `slot_misc_array_2` | word | engine | Segundo set miscelanea |

## State Machine / Event System ($7E1B17-$7E1E45)

| Address | Name | Type | Descricao |
|---------|------|------|-----------|
| `0x7E1B17` | `state_machine_var_a` | word | Variavel A do state machine (func_C09BE7) |
| `0x7E1B19` | `state_machine_var_b` | word | Variavel B do state machine |
| `0x7E1B29` | `event_queue_count` | word | Contador de eventos na fila |
| `0x7E1B2B` | `event_queue` | word | Fila de eventos (array) |
| `0x7E1DF1` | `timer_global_a` | word | Timer global A |
| `0x7E1DF3` | `timer_global_b` | word | Timer global B |
| `0x7E1DFF` | `level_timer` | word | Level/area timer |
| `0x7E1E15` | `irq_flags` | word | IRQ/flags register (bits para fade control) |
| `0x7E1E1D` | `fade_timer` | word | Timer de fade |
| `0x7E1E29` | `state_machine_trigger` | word | Trigger do state machine |
| `0x7E1E45` | `sprite_total_count` | word | Contagem total de sprites na area |

## Sa-1 Dispatch Table

| Address | Name | Type | Descricao |
|---------|------|------|-----------|
| `0x008DF9` | `sa1_func_table_0038` | word | Ponteiro SA-1 para state $0038 → func_state_A |
| `0x008E21` | `sa1_func_table_003B` | word | Ponteiro SA-1 para state $003B → func_C0EB21 |

## Player State Speculation (To Verify)

Enderecos mencionados em notas anteriores que requerem verificacao empirica no emulador:

| Address | Suspect Name | Suspect Type | Metodo de Verificacao |
|---------|-------------|-------------|----------------------|
| `0x7E0D30` | `player_pos_x` | word | Watch no Mesen2, mover o jogador |
| `0x7E0D32` | `player_pos_y` | word | Watch no Mesen2, mover o jogador |
| `0x7E0D34` | `player_vel_x` | word (signed) | Watch, aplicar movimento horizontal |
| `0x7E0D35` | `player_vel_y` | word (signed) | Watch, pular |
| `0x7E0D36` | `player_state` | byte | Watch, trocar de estado (idle→roll→jump) |
| `0x7E0D44` | `player_direction` | byte | Watch, virar para esquerda/direita |
| `0x7E0D5C` | `player_health` | word | Watch, tomar dano |
| `0x7E0D7E` | `player_bananas` | byte | Watch, coletar banana |

## Referencias de Codigo

Fontes para os enderecos mapeados:

| Funcao | Endereco | Descricao |
|--------|----------|-----------|
| func_C0EDCE | $C0EDCE | Player init: configura sprite type, spawn, atributos |
| func_C0852D | $C0852D | NMI slot init: verifica slot active, seta timer, sprite type |
| func_C0A252 | $C0A252 | Input read: le $4218/$421A, computa hold/edge |
| func_C0A14B | $C0A14B | Area init: carrega config de fase, inicializa work areas |
| func_C08687 | $C08687 | Game phase dispatch: mapeia game_phase → handler |
| func_C088F9 | $C088F9 | SA-1 dispatch: roteia comando SA-1 por estado |
| func_C0E696 | $C0E696 | Slot scan: busca primeiro slot com spawn_state=0 |
| func_C085B8 | $C085B8 | Sprite init type C: le slot_spawn_state |
| func_C09BE7 | $C09BE7 | State machine: processa eventos, triggers |
| func_C0A7B5 | $C0A7B5 | Event queue: processa fila de eventos |
| func_C08E87 | $C08E87 | Vblank/Fade: ciclo de fade in/out |
| func_C0C21C | $C0C21C | PRNG: LFSR step para geracao pseudoaleatoria |
