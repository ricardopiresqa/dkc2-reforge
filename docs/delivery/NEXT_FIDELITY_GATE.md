# Pirate Panic — próximo gate de fidelidade

## Estado comprovado

- Fonte: ROM USA v1.0 com payload SHA-256
  `35421a9af9dd011b40b91f792192af9f99c93201d8d394026bdfb42cbf2d8633`.
  A ROM de `roms/` era revisão1; não comparar revisões distintas.
- Sala principal: dados de7136B após32B de prefixo coincidindo integralmente
  com banco7F da RAM capturada. Metatiles também byte a byte iguais.
- Movimento inicial: 10checkpoints caminhada/primeiro salto curto PASS com
  tolerância aprovada1px por eixo/1frame, mesma sequência de inputs original.
- `dist/pirate-panic-native-4x`: build fresco e runtime220frames exit0,
  render log sem erros, viewport256x224/janela1024x896/escala4 medidos.
- Céu/oceano BG2 4bpp e cordas BG3 2bpp exportados de VRAM/CGRAM/PPU e
  integrados. Isso comprova pixels/fontes, **não** scroll/composição original.
- 53testes `tools/tests` passam. Bundle secure audit and runtime220frames,
  screenshots9/9 verified. Não há auditoria RRE PASS independente da fase inteira.
- Último bundle testado: `dist/pirate-panic-final-secure-current`; audit não
  encontrou ROM/raw dumps/signing material; runtime QA220frames e9/9 captures.

## Delta imediato

`assets-raw/pirate/reference-camera.csv` contém1034estados originais por frame,
incluindo câmera X/Y e scroll BG2/BG3. Exemplo: parado, câmeraY oscila295..304
e BG2 horizontal muda; modelo proporcional ao player não é suficiente.

1. Portar consumidores originais de câmera/scroll, não reproduzir o CSV como
   animação de gameplay. Trace é referência de teste, não lógica de produção.
2. Integrar ondas/HDMA, prioridade e color math; BG3 é camada3 em **Mode1**,
   não PPU Mode3. Snapshot final de PPU pode refletir última banda de scanline.
3. Capturar checkpoints de câmera e pixels do port: gate visual permanece
   aberto sem comparação renderizada com a referência original.
4. Separar padrões de input adicionais: pulo sustentado, roll/reversal,
   colisão de slopes/tetos, Dixie/parceiro e Rambi.
5. Objetos/AI restantes, HUD original, áudio/loops/SFX, bônus/cabine/warp,
   goal/restart e percurso completo continuam em aberto.
6. Tentativas QA mistas com run/jump ainda morrem/reiniciam antes da rota total;
   `LevelEndGoal` original ainda não foi implementado. Não avaliar run sintético
   como fidelidade nem chamar nível de concluído.

## Resultado do rastreamento das subáreas (2026-10-15)

- `CODE_B5BCA8` usa `$0523` como índice de `DATA_B5BAEF`. Main (`03`), Bonus 1
  (`6F`), Bonus 2 (`70`) e Warp (`1D`) selecionam índice `3` → `DATA_E3E006` /
  `ShipDeckLevels.bin`. O arquivo CMP decodifica para 29.568 bytes (924 colunas);
  só a fatia principal, offset `32`, tamanho `7.136`, foi validada byte a byte.
- Cabin (`1B`) seleciona índice `16`, cuja entrada em `DATA_B5BAEF` é nula e
  tem comentário “Kaptain's Kabin levels”. Há assets dedicados: tilemap CMP
  decodificado para 1.792B, GFX para 21.024B e paleta raw de 256B; o importer
  agora preserva bytes e hashes. Isso prova os streams, não layout, colisão,
  limites ou uso pelo runtime.
- Headers comprovados: Main `FD4C8A`, Cabin `FD51B5`, Bonus 1 `FD56D8`, Bonus 2
  `FD56F2`, Warp `FD51F5`. A lista pós-registros do Main contém os IDs
  `1B, 6F, 70, 1D`; sem semântica adicional, preservar como palavras fonte.
- `reference_capture.lua` injeta apenas a sequência fixa existente, observa
  gameplay quando o LevelID é `03` e escreve sobre arquivos em
  `assets-raw/pirate`. Não usar esse script para áreas especiais: ele não
  captura esses IDs e poderia sobrescrever a referência aprovada.
- **Ainda sem prova:** offsets/limites dos segmentos de bonus/warp, consumidor e
  colisão da Cabin, triggers de entrada/saída e localização original da DK Coin.
  Não implementar geometria nem tratar a lista de IDs como triggers.

## Guardas

- Copiar fontes game-specific para `tools/vendor`; originais preservados.
- Não versionar ROM/VRAM/CGRAM/PNG extraído/bundle, nem signing private key.
- Mesen isolado local; I/O Lua autorizado pelo owner apenas para scripts
  revisados; rede desativada. Configuração OneDrive não alterada.
- Não fechar cards por conta de PNGs ou por PASS de dez checkpoints.
- Não usar fixtures sintéticas como referência SNES nem relaxar tolerância.
- Revisores anteriores fizeram afirmações incorretas sobre BG3/constantes;
  confrontar parecer com código e runtime, sem promovê-lo a aprovação total.

## Câmera/scroll — pipeline original portado (2026-10-17)

- `main/original_camera.lua` agora traduz B5E4ED→E5EC/E5AC (alvo X: ator com
  subpixel − onda − lookahead `$0AEA`/`$0AEC` pelo bit14 de `$0012`), E73B/E652
  (alvo Y mira o chão abaixo via `$000E`; subindo só levanta o alvo), E7B7
  (limites globais, troca de região E7DB/EC55/ED2C, limites herdados de vizinhas
  E810–E8F5), E9EA (clamp preservando subpixel) e ED92/EDFC (spring EEB1, passo
  ±`$0800`, Y antes de X). Hit-stop `$0A36` bit `$80`: alvo recalculado, spring pulado.
- Causas do erro anterior: entrada sem subpixel, `direction` lido de `$B8` em vez do
  facing, alvo Y heurístico e limites sem vizinhas. O spring já estava correto.
- Prova: `tools/replay-compare/replay_camera_offline.py` executa o Lua real (lupa
  LuaJIT) com entradas originais da mesma captura: **1033/1033 frames exatos (0 px)**.
  Sem hit-stop: falha só nas janelas de quique 566–568/938–941. Mutação (ignorar
  vizinhas) quebra o replay. Coberto em `tools/tests/test_original_camera.py`.
- Runtime: `game.lua` chama `camera.follow` após o tratamento de contato (ordem
  original comprovada pelo freeze no frame do impacto); `camera.lua` passa facing,
  `collision.ground_distance` (sonda ≤`$50`) e `player.hitpause_frames`.
- Runtime real: `dist/pirate-panic-camera-source-pipeline` (engine QA nativo, audit
  PASS, 220 frames exit0, `dkc2.original_clock=786`): player 10/10 PASS; câmera
  10/10 PASS (8 exatos, 165/173 com dy=1). Antes: FAIL com dy=2 em 173/180.
  Hit-stop no runtime (566/938) não exercitado: a rota de 220 frames não chega lá.
- **Ainda sem prova:** escritor original de
  `$000E` (a sonda é aproximação); EF89 (parâmetros Y rápidos), EE6B (shake),
  gates `$0D4E`/`$6E`/`$B8`; vizinhos verticais não exercitados no trace;
  scroll BG2/BG3 (colunas já em `reference-camera.csv`) e HDMA não tocados.

## BG3 enxárcia — mapa e scroll originais (2026-10-18)

- Scroll de `80E4EB`: H = (L1X + L1X>>2) mod 1024 (1,25×), V = L1Y − 257, ambos com a
  RAM do frame anterior (NMI). 1033/1033 frames iguais aos registradores capturados.
- Mapa: `DATA_F526A7` (40 colunas × 16 linhas de metatiles, coluna-major) + metatiles
  `DATA_F52087` (4×4 tiles, linha-major, flips `$4000`/`$8000`) → mapa periódico
  1280×512 (`tools/replay-compare/export_bg3_rigging.py`). VRAM `$7800` em 9 frames:
  780/780 células interiores iguais. Todos os tiles visíveis têm prioridade 1:
  Mode 1 + prioridade de BG3 ⇒ acima dos sprites (`Z_FRONT` no renderer).
- Pixels vs screenshots originais (overscan Mesen de 7 linhas recortado): 100% nos
  frames 40/60/100/173/180. **Correção (2026-10-18):** a divergência inicial em
  165/173 NÃO era streaming de borda: os screenshots do Mesen atrasam 1–6 frames em
  relação à RAM capturada (variável); com o atraso estimado, 173 bate 210/210.
- Runtime `dist/pirate-panic-bg3-rigging` (audit PASS, 220 frames exit0, 9/9 capturas):
  player PASS, câmera PASS, enxárcia 100% conforme a câmera do port. Diferença contra
  o screenshot do mesmo frame = latência global de apresentação (SNES exibe f−1).
- Replay offline roda LuaJIT com `jit.off()` (abortos de trace geravam dumps SEH no
  faulthandler; semântica idêntica sem JIT).
- **Ainda sem prova:** latência de apresentação de 1 frame.

## BG2 céu/mar — HDMA por scanline e color math (2026-10-18)

- Init real `BBA655` (`$059B=$0601`): canal 1 → BG2HOFS modo 2, tabela `$7E8012`
  (faixas de céu 24/24/56 linhas + bloco repeat de 127 linhas de mar); canal 2 →
  COLDATA modo 0, tabela estática `DATA_BBA6C6` (linhas 0–111 sem soma; a partir da
  112, verde 12→31 e depois verde+vermelho, em blocos de 7 linhas). V fixo em −1.
- `main/original_bg2.lua` porta `80E540` byte a byte (céu = `$2A`>>1, >>2, >>4; mar =
  acumulador 8.8 de L1X+`$2A` em endereços ímpares; laços de onda `INC`). Replay do
  trace: registrador da última linha (224) igual em **1029/1029** frames e estado
  final idêntico ao snapshot de WRAM (**0 bytes**).
- Faixas `export_bg2_strips.py` com color math assado (soma 5 bits, saturação 31):
  390/390 linhas de mar visíveis batem ±1 px contra os screenshots (atraso de captura
  estimado pelo céu); céu 87,5% dos pixels (resto coberto por mastro/sprites/BG3).
  O ±1 restante é corrida CPU×HDMA do original (tabela reescrita durante o quadro).
- Runtime `dist/pirate-panic-bg2-hdma` (audit PASS, 220 frames exit0, 9/9 capturas):
  player/câmera PASS; todas as linhas de BG2 visíveis (123–183 por captura) com o H
  previsto no próprio frame; ~250 sprites/frame, 0 pool_drops, frame_dt 16,7 ms.
- **Ainda sem prova:** soma via subscreen OBJ (pixel de sprite no subscreen troca a cor
  fixa) não modelada; latência de apresentação de 1 frame.

## Ambiente — crash nativo intermitente na suíte (2026-10-18, causa NÃO provada)

- `tools/tests` (80 testes): 7/8 execuções limpas; ~1/8 termina com access violation
  ou objetos Python corrompidos (ex.: int virando `range_iterator`) em código Python
  puro, quase sempre em `import_pirate_panic.render_level`. Ocorre também com o
  importador sozinho e fora do pytest (antes 3/5; após trocar `putpixel` por
  `PixelAccess`, 0/10 isolado). Reprodutor mínimo de `putpixel` falhou 1/4 e depois
  8/8 limpo em Pillow 12.2.0 e 12.1.1: não discrimina versão. Sem bug conhecido
  publicado. Python 3.11.15 falha na mesma taxa (5/10 vs 5/10); nenhuma DLL de
  terceiro no processo. **Pista mais concreta:** memória comprometível esgotada
  (146 GB de commit, ~3 GB livres; JVM do bob.jar falhou ao mapear 1 GB), ocupada por
  8 processos `run_e2e.py` em background via `nohup` (~65 GB, de fora do dkc2).
  Hardware não descartado. Não declarar PASS de suíte por uma única execução.

## Bananas — formações originais (2026-10-18)

- `BananaFormations/PiratePanic_Main.bin` decodificado como `B5F10B` (tema `$0AB4=0`):
  X = (palavra(b0,b1)>>1 & $3FF8) + $100, Y = (palavra(b1,b2)>>4 & $03F8) + $100,
  formação `b3` → bitstream de máscaras por coluna (bit 15 = linha de cima, 8 px).
  18 grupos, 148 colunas, 97 bananas. **146/148 colunas idênticas à lista que o
  próprio jogo montou em `$7F:B232`** (snapshot WRAM); as 2 restantes só têm bits
  apagados = bananas coletadas no trace.
- Desenho `B5F5BD/B5F637`: sprite 16×16, tile `$0D2C=$21E0` + 2·quadro, paleta OBJ 0,
  quadro = (P>>1 + col + linha) mod 8, P = ((clk>>1)·4 + gx + gy)>>2. Pixels vs
  screenshots: 99% (40/60/100), 93% (140), 100% (153–180), com atraso de captura.
- Coleta (`B5F79A`, célula + 1 coluna/linha = 16×16): a rota original coleta
  exatamente as 2 bananas que o jogo apagou (frames 197 e 208). Hitbox do port
  (16×24) é aproximação; o oráculo não discrimina variantes de caixa.
- Runtime `dist/pirate-panic-bananas2` (audit PASS, 220 frames exit0): bananas
  98,6–100% conforme câmera/clock do port; diferença de quadro inteiro caiu
  (ex. frame 40: 1,9%→1,4%). Primeiro bundle saiu sem bananas: `pcall(require, …)`
  não é visto pela varredura do bob; corrigido com `require("…")` literal.
- **Ainda sem prova:** HUD original (contador/vidas no topo), bananas de bônus/warp,
  banana bunches/moedas como sprites.

## HUD original — contador de bananas e painel de vidas (2026-10-18)

- Nova captura própria (Mesen `--testrunner`, script só-leitura
  `reference_hud_capture.lua` → `reference-hud-trace.csv`, clock alinhado 401/401 com
  a referência aprovada): `$096D/$096B/$096F/$0973/$0979/$08C0` por frame.
- `main/original_hud.lua` traduz `BEC840` (contador BCD 1 a 1, timer $3C/$78, ocultar
  ao zerar) e `BEC70E` (painel de vidas: desliza +$30/frame até $200, conta, desliza
  −$30 e some). Máquina de estados = captura em **401/401 frames** (dados os eventos
  de coleta 197/206 e de chegada 229/238).
- Sprites: ícone = quadro de giro da banana `(clk & $1C)>>1` em OAM (8,8); dígitos 8×16
  (`$1CC+d` / `+$0A`) a partir de x=$18; vidas em x=$E4 (ou $DF/$E7), y do deslize.
  Linha exibida = Y da OAM (medido; o caminho das bananas do nível compensa o DEC
  com `SEP #$21`). Pixels vs screenshots: 100% (40/60/140), 94% (100, enxárcia acima).
  Runtime `dist/pirate-panic-hud`: HUD 100% no mesmo frame; diferença de quadro inteiro
  frame 40 1,37%→0,90%.
- Caixa de coleta de bananas: `$09B3..$09BA` capturada (`reference-banana-box.csv`)
  varia por animação (parado/andando/no ar) e espelha pela direção; com ela a rota
  original coleta exatamente nos frames 197 e 206 (antes 197/208 com caixa fixa).
- Cabeça do painel: pose `GFX_Diddy_LifeIcon.bin` + paleta `Sprite_Diddy_Active`
  (`DATA_FD6484`), origem medida (212, Y dos dígitos + 16): 142/142 px inclusive com o
  painel deslizando (frame 140). A âncora de `B59CAE` (X=$1D40, Y=deslize+$1000) não
  foi traduzida; a origem é medida.
- Voo da banana (`B5F899`/`B5F9D1`): sai da posição de tela, velocidade $40−pos·8,
  chega em (8,8) em 32 passos; soma `$096D` ao cruzar Y=$0800. Cadeia rota → caixa →
  coleta → voo → HUD = captura em **401/401 frames sem eventos injetados**. Runtime
  `dist/pirate-panic-hud3` (260 frames): contador 0 → bananas voando → 1 → 2.
- **Ainda sem prova:** 1-up a cada 100 bananas (`BEC84E`) só esboçado; tabela de
  recorte por quadro da ROM; suíte completa instável por memória (sem o importador:
  54 passed).

## Itens — spawn, animação e ciclo de vida originais (2026-10-18)

- `export_items.py` segue o script de spawn de cada `param` (`$0000` SpriteID, `$8100`
  animação F9, `$8D00` índice em `DATA_FD5FEE`) e exporta 51 quadros com a origem real
  da pose. Identificação corrigida (o importador nomeava pelo 1º `$0000` antes do salto):
  2102 Banana Coin ($1C1), 2106/2110 Kremkoin ($1C2), **2112 DK Coin** ($1C3, paleta
  inferida = única de moedas), 2046 caixote ($2E6), **2042 barril estrela** ($2B5),
  2638 barril DK ($2E1). Letras KONG (2114/2116/2120, ponteiros `$42..$48`) pendentes.
- Nova captura própria `reference-sprites-trace.csv` (tabela de sprites vivos, 1033
  frames): só `script = 1` nasce no nível principal (Kremkoins `script = 10` nunca); spawn
  no frame seguinte a câmera ≥ x−$120; despawn a x−câmera ≤ −$28; 1º passo da animação no
  frame do spawn; animações congelam com o ator no hit-stop (567–568, 939–940).
  `main/original_items.lua` = trace em **527/527 frames** (barril DK e caixote: spawn,
  pose, despawn). Hipótese (1 ponto): `$5C` limita o spawn vertical (moeda do cordame).
- Barril DK: a logo "DK" é o sprite companheiro $11C (anim $2BF), mesma origem e ciclo de
  vida; trace 388/388 frames. Paletas provadas pela CGRAM capturada: OBJ 4 =
  `Sprite_Barrel` (barril), OBJ 0 = `Sprite_HUDNumbers` (logo).
- Pixels: captura própria `reference_items_frames_capture.lua` (telas + CGRAM nos frames
  600/700/800/900/950/1000). Barril, logo e caixote = **100%** dos pixels nos 5 frames com
  item visível, desde que o canto fique 1 px à esquerda da origem da pose (regra medida,
  constante em todos os casos). O atraso de captura chega a 8 frames aqui.
- Runtime `dist/pirate-panic-items`: audit PASS, 220 frames, player/câmera PASS.
- Letras KONG: K = 2114 (anim $2BB), O = 2116 ($2BC), N = 2120 ($2BD); `$4C` = bit da
  letra (1/2/4; G = 8 não está no nível principal), paleta 0 = `Sprite_HUDNumbers`.
  Correções do decodificador: `$8300` é CHAMADA de sub-script (o script base continua
  depois), `$82` fecha o laço da animação e `$8F` é desvio condicional (5 bytes). Os
  itens já validados não mudaram (mesmas animações e paletas).
- **Ainda sem prova:** comportamento (coleta de moedas/letras, quebra do caixote, barril
  DK/estrela) e pixels das moedas/letras — nada disso acontece ou aparece no percurso
  de referência; exige capturas com rotas novas.

## Item 2 — capturas com rota-bot (2026-10-18)

- `tools/replay-compare/route_bot_capture.lua` (Mesen, só-leitura, arquivo novo): entradas
  de referência até o frame 1033 e depois um bot de QA fixo (DIREITA+Y, B 12 de cada 48
  frames) até o frame 6000 → `assets-raw/pirate/route-bot-trace.csv` (player + todos os
  sprites vivos por frame). Chega a x≈6385; 4 mortes; quebra caixote (1230: BurstEffect,
  BarrelPieces, lascas), letras KONG, moedas, barril estrela (2853), Klobber (3198),
  caixa do Rambi (3313) e Rambi (3399), parede quebrável (3625).
  `summarize_route_bot.py` lista spawn/despawn, estados e vidas.
- Neek e Klomp usam a MESMA rotina (`B3A436`), parâmetros por espécie (Klomp
  `DATA_FF0294`). Trace: Neek só anda à esquerda e cai das bordas; Klomp vira na borda
  da plataforma (+75, +178, −168, −176 px do spawn) e acelera (0,5 → ~1,5 px/frame).
- Dixie fica parada em (304,465) na gravação: o Diddy está sozinho; 1 toque = morte
  (estado 5 no impacto, vida −1 60 frames depois, fade, `MapPlayer`, reinício).
- **Próximo:** traduzir o andador genérico (`B3A345`, `B3A441/501/589/58F`, `BEF05C`,
  `B3A37F`, `B3A603`) e validar frame a frame contra este trace; o port atual do Neek
  (velocidade constante por dt, sem virada) será substituído.
- Andador (fonte): `$52` = tipo de movimento (Neek $22: anda e inverte em parede; Klomp $23:
  patrulha por FAIXA em torno da origem `$42`, `$46` = esquerda<<8 | direita, ex. $4848 =
  72/72, $B0 = 176 à direita — explica todas as viradas medidas com 1–3 px de sobra);
  `$26` = velocidade-alvo (Neek −1,0; Klomp ±1,25); física `BEF7CE` = terreno `B8D4F8` +
  limites `BEF7A3` + aceleração `B8CF2C` (passo = f_k(|alvo−v|), Klomp k=8: d>>4+d>>6) +
  gravidade `BEFB72` ($70/frame, máx $800) + `B8D15E`.
- Protótipo só-horizontal NÃO bate: no trace o Klomp anda 0,5 px/frame constante por
  muito tempo. Falta entender `B8D15E`/`$2C` → próxima captura: estrutura completa do
  sprite (0x5E bytes) de Klomps/Neeks para comparar campo a campo.

## Item 2 — andadores Neek/Klomp portados (2026-10-18)

- Captura nova (só-leitura): `tools/replay-compare/route_bot_walkers_capture.lua` → struct
  completo ($5E bytes) de todo Neek/Klomp vivo, frames 1–3200 da rota-bot
  (`assets-raw/pirate/route-bot-walkers.csv`, não versionado).
- `tools/replay-compare/export_walkers.py` → `data/original/pirate/walkers.lua` (campos de
  spawn de todos os params Neek/Klomp do nível, tabela da espécie, scripts F9 como lista de
  ops) + 31 poses em `assets/images/pirate/walkers` (atlas `original_walker_*`).
- `main/original_walkers.lua`: tradução de B3A436. Animação antes do movimento no estado 0
  (B3B8A7 → BEF05C) e depois no derrotado (B3A50B); callbacks B9E67B (vx>>2), B9E688
  (vx*1,5), B9E694/B9E5AD (vira se $26 discorda da face), B9EF1F (vx=0 na virada), B9E01B;
  `$83` com contador acumulativo (B9D115: pose seguinte dura n−1). Aceleração B8CF2C (k=8:
  |d|>>4 + |d|>>6, truncada para zero). Patrulha BEF848 (origem $42 ± faixa $46), parede →
  BEF8B5 (recentra e inverte); Neek BEF812 inverte o alvo na parede. Pisão B3A539: vira para o
  jogador, vx = ∓$100, vy = −$800, tipo 4 (teto de queda $0C00 observado).
- Ciclo de vida traduzido de BBBB8C/BBB622/BBBC96 (só eixo x): caixa 0 (origem,
  `cam−$20 < x ≤ cam+$120`) e caixa +8 (sprite, `cam−$28 < x ≤ cam+$128`); some quando sprite
  E origem saem; grupos por `type` do objeto (controlador $8C spawna todos e só despacha o
  grupo quando nenhum membro vivo está no alcance); morto não reaparece até reiniciar.
- **Evidência:** `tools/tests/test_original_walkers.py` — Neek 2257/2257 e Klomp 882/882
  frames exatos (x com subpixel, y, vx, pose). Entradas tiradas do trace (não derivadas):
  câmera x, frames de congelamento (struct parado, $18 ignorado — `$0A36` não capturado) e
  frames de pisão com a face do jogador.
- **Hipóteses marcadas no código:** terreno B8D4F8 não traduzido (pé segue a superfície mais
  alta da coluna — `collision.surface_at`; pouso no frame seguinte); parede = tile de 32 px
  íngreme (`collision.steep_tile`, 1 evento: frame 2903); contato BEBE09 não traduzido (caixa
  24×24 + regra de pisão antiga, validada em 566/938; lateral = dano); eixo y do ciclo de vida
  ignorado (falta câmera y na captura).
- Motor: bundle `dist/pirate-panic-walkers` (replay de referência) mostra o Neek andando (540)
  e derrotado no mesmo ponto que o Mesen (600). Diferença vista, fora deste módulo: a pose do
  Diddy no quique do pisão (original encolhido).
- **Próximo:** traduzir BEBE09 (contato/dano) e B8D4F8 (terreno), capturar `$0A36`/câmera y;
  depois Klobber/Kloak e o resto do item 2.
