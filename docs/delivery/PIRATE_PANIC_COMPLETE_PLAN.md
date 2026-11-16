# Pirate Panic jogável de ponta a ponta — plano (2026-10-19)

Pedido do owner: nesta sessão, deixar pronto o caminho **abertura → menu → Novo Jogo →
Pirate Panic** com gameplay completo (controles, inimigos, bônus, barril de atalho,
trilha sonora), em `/loop`.

Regra de fidelidade (inalterada): o que tiver evidência do original (ROM/desmontagem +
captura Mesen) é traduzido e testado; o que ainda não tiver é implementado como
**aproximação marcada no código** e listado aqui — nunca apresentado como fiel.

## DAG

| Nó | Entrega | Arquivos | Depende de |
|----|---------|----------|------------|
| N1 Fluxo | abertura (tela-título do original) → menu NOVO JOGO → Pirate Panic; fim de fase / game over → título | `main/menu.lua`, `main/game.lua`, `main/level_select.lua`, `main/main.collection` | — |
| N2 Contato/dano | contato traduzido (BCFD61/BEBF18) ligado ao jogador; perda de Kong | `main/original_walkers.lua`, `main/game.lua` | — (feito) |
| N3 Morte/respawn | animação de morte, vida −1, reinício (início ou barril-estrela), game over | `main/game.lua`, `main/player.lua` | N2 |
| N4 Fim de fase | LevelEndGoal (x 6984) → sequência de vitória → próxima tela | `main/game.lua`, módulo novo | N1 |
| N5 Itens | letras KONG, moedas, caixote (carregar/arremessar/quebrar), barril-estrela, barril DK, canhões-barril | `main/original_items.lua` + módulos novos | N2 |
| N6 Inimigos restantes | Klobber ×2 (o "Kloak" era um cacho de bananas) | módulo novo | N2 |
| N7 Dixie | parceira seguindo, troca, perda ao levar golpe | `main/player*.lua` | N2, N5 (barril DK) |
| N8 Rambi | caixa, montaria, parede quebrável, placa "sem animal" | módulo novo | N5 |
| N9 Subáreas | barris bônus (Kremkoin), barril de atalho (warp), cabine | decodificar mapas das salas | N5 |
| N10 Áudio | trilha da fase (Klomp's Romp) + efeitos, renderizados localmente da ROM | `assets/music`, `main/sound.lua` | — |

Paralelo: N1 ∥ N10 ∥ (N3→N4) ∥ N5/N6. Ordem de execução no loop: N1 → N3 → N4 → N5 →
N6 → N7 → N8 → N10 → N9 (subáreas por último: mapas ainda não decodificados).

## Estado

- N2: decisão de contato 35/35 contra o original; integrado (`game.lua`).
- N1 (2026-10-19): abertura original (quadros da ROM capturados no Mesen, boot sem entrada:
  `opening_frames_capture.lua`/`opening_title_capture.lua` → `export_opening.py` →
  `main/opening.lua`), título com "APERTE START", menu NOVO JOGO → Pirate Panic direto.
  Labels de menu passaram a ser desenhados (predicado `text` no `native.render_script`,
  fonte `main/fonts/menu.font`, posições em 256×224). `game.project start_level` vazio (QA usa
  `--config=dkc2.start_level=level_1_1`). Aproximação: quadros a cada 10 frames (6 fps).
- Diddy: 28 scripts F9 (virar, rolar, morrer, agachar, carregar/arremessar, canhão, quique,
  golpe, fim de fase) via `export_diddy_moves.py` (opcodes $8B/$89/$8F/$90), 117 poses novas
  no mesmo canvas 88×88 (origem 31,62). VM: `$8B/$89/$8F/$90`, `force/release`.
- Jogador: pé na superfície da coluna do x (756/756 frames no chão da referência), controle
  aéreo aplicado antes do movimento, pausa de 1 frame ao pousar do quique (estado 22).
  **Resultado no motor (`dist/pirate-panic-qa-12`, replay de referência): 1001/1034 quadros dentro
  de 1 px; 2º pisão no f939 (original 938) — o "1033/1033" registrado antes estava errado, ver correção.**
- N3: morte original (animação $0A; física medida no trace 1260–1490 — aproximação marcada),
  vida −1 aos 60 frames, reinício aos 230 (no barril-estrela, se tocado), game over.
- N4: alvo de fim de fase (B3A275: no ar, caindo, caixa do jogador × caixa da pose do alvo) →
  GotPrize ($45) → LEVEL_COMPLETE → título. Rota-bot QA (invulnerável) chega ao fim (≈2850).
- N5 parcial: letras KONG, moedas (banana/Kremkoin/DK), barril-estrela (checkpoint), barril DK
  (quebra) por caixa de pose (aproximação: rotinas próprias não traduzidas).
- N10 em andamento: `music_spc_capture.lua` grava o estado do SPC700 (`assets-raw/pirate/pirate-panic-music2.spc`,
  registradores de E/S reconstruídos); `ffmpeg -f libgme` toca e gera som com estrutura musical, mas o
  ponto de loop não foi achado (melhor correlação espectral 0,49 até 500 s). Suspeita: estado do driver incompleto no
  instantâneo. `render_music.py` existe, mas as saídas em `assets/music/pirate/` ainda não valem.
  Falta: corrigir o instantâneo (ou gravar o áudio do jogo) e ligar componentes de som no `main.collection`/`sound.lua`.
- Pendentes: N6 Klobber/Kloak, N7 Dixie, N8 Rambi/canhões/parede, N9 subáreas, efeitos sonoros originais.
- N10 (aproximação entregue): `assets/music/pirate/pirate_panic.ogg` = 5 min renderizados do instantâneo
  SPC (ffmpeg libgme) com fade de 4 s, componente `music_pirate` (looping) no `main.collection`, tocado por
  `sound.set_original_semantics` e parado ao voltar ao título. Bundle `qa-13`: arquivo no `game.arcd`
  (+3,36 MB), replay sem mudança em relação ao qa-12 (ver correção abaixo). Não verificado de ouvido. Loop exato e efeitos sonoros pendentes.
  (`pirate_panic_intro.ogg`/`pirate_panic_loop.ogg` são saídas da tentativa de loop; não usadas.)
- N6 Klobber: `export_klobber.py` → `data/original/pirate/klobber.lua` (scripts $2E2/$1F4–$1F7 com `$8D`
  corpo+barril, 54 poses, caixas) e `main/original_klobber.lua`: despertar BEF50B (|dx|<$A0, |dy|<$60,
  tremor $0F) / BEF4C8 (contagem $1E), corrida $400 (DATA_FF0260+6), pulo −$380, palavra de contato $020F
  (toque inofensivo, pisão quebra o barril). Aproximações: duração da corrida 147 frames (trace), virar com
  32 px de folga, rearmar após $96. Motor `qa-14`: sai do barril e corre (capturas 1880–2030).
  "Kloak": era o cacho de bananas (param 3188, sprite $170) — nome errado do exportador; resolvido.
- N9 subáreas (bônus 1, bônus 2, warp): mapas decodificados do MESMO `ShipDeckLevels.bin` via tabela de áreas
  `DATA_B5BE25` (área = byte do preâmbulo do cabeçalho: principal 0, warp 4, bônus 1 5, bônus 2 6; o tamanho
  total $7380 bate com o mapa). Coordenadas locais = x/y_raw − $100 a partir do início da área: todos os objetos
  e spawns apoiados caem exatamente numa superfície. `export_subareas.py` → `data/original/pirate/subarea_*.lua`
  + `area_links.lua` (portais: canhão 332 → bônus 1/registro 3, canhão 398 → warp/registro 5; registros de
  retorno do cabeçalho; controles D354: bônus 1 tipo 0 20 s, bônus 2 tipo 1, 7 alvos, 20 s). Módulos de fase
  `data/levels/pirate_{bonus_1,bonus_2,warp}.lua`; `main/original_areas.lua` (portais, contador, Kremkoin,
  saída). Motor `qa-15` (início direto no bônus 2): sala desenhada, contador 19→3, volta à fase principal.
  Aproximações: entrada no canhão imediata (sem animação de disparo), câmera de seguir nas salas, retorno
  caindo do registro, saída do warp em x ≥ 200. Pendentes: cabine (outro cenário, DATA_FD4BB8), canhão 768,
  entrada do bônus 2 (parede quebrável → Rambi; sem Rattly nesta fase), alcance do warp (canhão no alto, x 1176).
- Efeitos sonoros originais (2026-10-19): `sfx_base_spc_capture.lua` (instantâneo SPC no frame 1440 da rota-bot,
  depois da primeira morte: música parada, amostras da fase carregadas, −91 dB) + `render_sfx.py`: grava no
  instantâneo o pedido exato de B581FB (portas $F4+1, id, canal) → ffmpeg/libgme → 24 efeitos em
  `assets/sfx/pirate` (pisão, matar Neek, golpe/morte do Diddy, banana, moedas, letras K/O/N/G, barris,
  parede, Klobber, Rambi, Kremkoin, tique do contador…), componentes `sfx_*` no `main.collection`;
  `sound.lua` toca os originais no modo original; módulos publicam pedidos (guincho do Neek a cada 64 frames,
  Klobber, parede, contador). Os 2 de menu saíram vazios (amostras não carregadas) e não são usados.
- Efeitos visuais: `export_effects.py` → estouro (anim $168) e fumaça (anim $1BB) com a paleta OBJ 0;
  `main/original_effects.lua`. Estouro no ponto de contato em pisão e golpe (trace 566/938/1260), estouro+fumaça
  ao quebrar barril-estrela, barril DK, caixa do Rambi, Klobber e parede. Lascas de barril (gráficos fixos) pendentes.
- Rambi (aproximação): `export_rambi.py`/`main/original_rambi.lua` — caixa pisada solta o Rambi, tocar monta,
  montado pisoteia andadores, parede quebrada (destino $42=3 → bônus 2, retorno 4), placa "sem animal" desmonta.
  Cavaleiro na pose original $211C na origem do animal.
- Motor `qa-19`: build ok, replay de referência igual ao qa-12 (ver correção abaixo).

## Correção 2026-10-20 — replay de referência

A medida "1033/1033 dentro de 1 px; pisões 566/938" registrada para o qa-12 não se reproduz:
rodando de novo o mesmo bundle (determinístico, 2 execuções), qa-12 … qa-39 dão **1001/1034**
quadros dentro de 1 px e o segundo pisão no frame **939** (original 938). O desvio dura 33 quadros
(até 14 px em y, f939–972) e a trajetória volta a bater. Causa localizada: o 2º Neek (nasce no f877)
está ~1 px mais à esquerda no f938 (port 963 vs original 964), então a caixa do Diddy só o alcança
um quadro depois. **Corrigido (qa-42):** o Neek nascia no f863 (original 864) porque o ciclo de vida
dos andadores lia a câmera um quadro adiantada; com a câmera do quadro anterior a trajetória fica
**1034/1034** dentro de 1 px, pisões em 566/938, e os andadores exatos sobem de 34 para 104 quadros
(contagem divergente 155→159, dominada pelo eixo y não modelado). O giro segue 100/100 (qa-39).

## Checklist completa (o que o jogador encontra em Pirate Panic) — atualizada a cada rodada

Legenda: [x] pronto e verificado · [~] aproximação marcada · [ ] falta

Fluxo
- [x] abertura: logos (Rare, Nintendo, copyright) a 60 fps (`opening60_capture.lua`: 651 quadros, 182 distintos, recortados — `export_opening.py --full-rate`; motor qa-57 = original, 100/600 exatos) · [~] fade/brilhos do título ainda a cada 10 quadros (APROXIMADO) · [x] menu original (`main/original_menu.lua`, `export_menu.py`, capturas `menu_nav_capture.lua` t2–t6): título → Select Game (arquivos 1–3, Copy/Erase, Mono↔Stereo, English↔Français; item do cursor aceso) → modo (ONE / TWO Team / TWO Contest) → ilha "Gangplank Galleon" (espera START) → cartão "Pirate Panic" (espera START) → fase; fades medidos pelo brilho; motor qa-59 percorre tudo até a fase. APROXIMADO: movimentos não capturados espelhados, Copy/Erase sem efeito (arquivos sempre vazios), modos de 2 jogadores iniciam o de 1, Français só troca o rótulo, ilha/cartão estáticos e sem música · [x] título/menu NOVO JOGO → fase · [x] game over → título
- [x] fim de fase / "roleta" (`main/original_goal.lua`; sonda `goal_probe_capture.lua` com escrita de y: t4 golpe baixo, t6 golpe alto): o prêmio desta fase é FIXO (tabela de 1 entrada: cacho de 10 bananas, pose $1944 — não gira); golpe alto = pulo com pico ≥ $68 acima do alvo ($0935 = y mais alto do pulo); pausa de 8 quadros; barril sobe o poste (vy −9/−7, g $50), no alto quebra (lascas + fumaça) e solta o prêmio (cai a partir de H+24, vira cacho em H+44, coletado em H+81); Kong quica (vx 392/416, vy −1536, g 112), pose $45 (alto) ou anda 3 px até alvo+144 com $46 (baixo); fim em H+411/H+127. Motor qa-44/49: tempos batem (prêmio pousa 1 quadro depois). APROXIMADO: vx do quique (1 medida cada), sprite $1CC não portado · [ ] fade/saída original

Controles do Diddy
- [x] andar/correr (Y) · [x] pular (B, altura variável) · [x] quique ao pisar
- [x] estrela/cartwheel (Y no chão): 99/99 frames iguais ao original (`cartwheel_capture.lua`, motor qa-21)
- [~] carregar/arremessar caixote (`main/original_carry.lua`: pegar com Y segurado, +12/−9 px, anim $0F 8 quadros — medidos; arremesso vx 4/vy −2/gravidade $40/60 quadros — APROXIMADO; motor qa-27: pega f65, arremessa f151) · [x] barril DK carregável (mesmo módulo; motor qa-28) · [~] agachar (animação original: $0C → B9DEE9 → $0D, ao soltar $0E até B9DFE7; física do estado CROUCH legado, NÃO medida)
- [~] parceira (Dixie, `main/original_partner.lua` + `export_dixie.py`, anim = id + $A3 por B9D0B8): [x] sai do barril DK (arco medido) · [x] seguir 31 quadros atrás (medido, motor qa-28) · [x] trocar com Select animado (`swap-route-t1.csv`: $49 / salto $4B em S+45 vy −624 g $50 / caminhada 1,75 px em S+58 / $4A; motor qa-56; medido só Dixie→Diddy) · [~] perder a Kong no golpe ($29 30 quadros, foge 4 px/quadro, parceira assume — medido; tempo de alcance aproximado) · [~] arremesso em dupla (A monta $40/$1D/$1F, Y $26 → $27; vx 3000/256 ×15/16, vy −400/256, g 112/256 medidos em `team-throw-probe.csv`; motor qa-30; arco de montar e espera de 30 quadros APROXIMADOS) · [x] física própria da Dixie (DATA_FF012A: pulo $F8C8, gravidade segurada $48, andar/correr $200/$300; `original_motion.set_kong`) · [~] hélice da Dixie (planar): física da ROM (B8C95B: queda máx. +$2E = $0100, vy +$30 = $FF00, anim $0B; motor qa-56 desce 1 px/quadro) — APROXIMADO: gatilho não reproduzido em captura (3 sondas; teste de B8C950 com $16F2 fica falso), uso B novo caindo · [x] arremesso para cima (CIMA+Y; `upthrow-route-t2..t6.csv`: vx 0, vy $F880, g $40, sai 24 px acima; líder fica pendurado no ar)

Inimigos
- [x] Neek · [x] Klomp (movimento exato) · [~] Klobber · [x] "Kloak" (x 1248) **não é inimigo**: o objeto param 3188 é o cacho de bananas (sprite $170, parado em 1504/384 no route-bot-trace); portado como item `banana_bunch` (+10 bananas; motor qa-38) — voo das 10 bananas APROXIMADO
- [x] contato/dano traduzido · [x] pisão · [~] cartwheel/Rambi derrubam inimigos

Itens e objetos
- [x] bananas · [x] moedas banana/DK · [x] Kremkoin (bônus) · [~] letras K/O/N (+ G) · [x] barril-estrela (checkpoint)
- [x] barril DK carregável (trace 2036-2042), quebra e solta a parceira (motor qa-28) · [?] quebrar pulando em cima (mantido, não conferido) · [~] caixote de madeira (pegar, jogar, quebrar — arremesso aproximado)
- [~] caixa do Rambi → Rambi montável · [~] parede quebrável · [~] placa "sem animal" · [ ] canhão comum (x 32)

Áreas
- [x] cabine do capitão: tela original (tilemap DATA_FD4BB8), bilhete do K. Rool; colisão MEDIDA (`kabin-route-t1..t3.csv`): chão plano em 192, parede esquerda (para em x 16); portas atravessadas andando (não CIMA): ≤21 px andando para a porta → caminhada automática 1,5 px/quadro, anim $3C, 46 quadros (motor qa-55) · [ ] fade da porta (45–130 quadros, não portado)
- [~] bônus 1 (canhão x 3890) · [~] bônus 2 (parede quebrada pela super-investida do Rambi: segurar A ≥ 75 quadros, B9E387; entra montado no Rambi em x 44/pé 209 — `animal-route-t7..t10.csv`; **não há Rattly no Pirate Panic**: o objeto 'Rattly' param 1190 era nome errado do exportador e nunca aparece) · [x] super-investida do Rambi no port (`original_rambi.lua`: carga 75 quadros, investida vx $700, travessia $180 × 46; motor qa-35: quebra em x 4987 vs 4989 original, entra no bônus 2 em 44/209 montado) · [ ] altura na travessia (port sobe a rampa; original desce ~11 px) · [ ] investida sem parede (para em 40 quadros, APROXIMADO) · [x] warp: canhão INVISÍVEL (spawn $8A bit $0008) acima da 1ª plataforma de barris; acesso = Team-up, pular e arremessar para cima perto do ápice (`upthrow-route-t6.csv`: a parceira entra com o pé em 283; o líder é puxado (256+96k)/256 px por quadro e entra 21 quadros depois); a captura antiga `team-throw-up.csv` foi feita colada numa parede e não provava nada. Motor qa-53/54 chega à sala do warp · [x] disparo do canhão (`cannon-route-t1.csv`, `warp-route-t1.csv`: espera 22, sobe a vy −1976 sem gravidade, anim $19, fumaça subindo 1 px; área troca 49 depois; motor qa-52) · [ ] fade antes da sala

HUD
- [x] bananas/vidas · [x] letras KONG no HUD (`original_kong_hud.lua`, $097B/BEC8ED: voo 1/8 por quadro até x 93+18i/y 24, entrada/saída 2 px por quadro — `hud-sprites-trace.csv`; motor qa-36: voo 25/espera 125/saída 15; espera de 125 e desenho com o 1º quadro do item APROXIMADOS) · [x] contador de moedas ($097D; `coin_probe_capture.lua` com escrita de y: voo 1/8 até (112,32), dígito $1CC/$1D6 em x 132 deslizando 2 px, conta +3 após chegar, sai em +218; `main/original_coin_hud.lua`, motor qa-50; 2 dígitos APROXIMADOS) · [~] contador do bônus

Som e efeitos
- [~] música (5 min em loop do instantâneo) · [ ] loop exato · [ ] música do bônus · [ ] jingle de morte/fim
- [x] 24 efeitos sonoros originais · [ ] efeitos de pulo/passos que o jogo tiver
- [x] estouro no contato · [x] fumaça na quebra · [x] lascas de barril (física medida; gráfico das poses estáticas renderizado da VRAM capturada `goal-t7-frame-4946` — tiles OBJ $80/$60, base 0, paleta Sprite_Barrel; vida 78 quadros; em caixotes/barris e no alvo) · [~] golpe com parceira (Kong foge)

## Correção 2026-10-20 (tarde) — regressão de atlas

- Do qa-24 ao qa-48, todo sprite tocado pelo nome da imagem dentro de um grupo do atlas
  (`original_banana_0`, `original_bg2_line_*`, `original_item_*_0`…) caía na 1ª animação
  do atlas (`an_enguarde`, o "peixe azul"): céu, mar, bananas, HUD, itens e o alvo sumiam.
  Não era tamanho de textura (testado com páginas 4096 e com o atlas cabendo em 1 página).
  Correção: cada imagem também declarada como animação própria (`insert_atlas_groups` e
  `write_atlas`); `original_bg3_rigging` (o renderer usa esse id) apontado para `_p1`.
  Motor qa-49: tela igual à captura antiga do bananas2; replay de referência 1034/1034.

## Rodada 2026-10-20 (noite) — itens apontados pelo owner

- [x] Nintendo na abertura: os quadros 430–590 são de alta resolução (512×478); o export
  recortava só o quarto superior esquerdo ("Ninte"). Agora mantidos em 512 e desenhados em
  escala 0,5 — "Nintendo PRESENTS" inteiro.
- [x] Título: fade (rampa de brilho medida, `title60_capture.lua`) e brilhos do baú a 60 fps
  (213 retalhos numa caixa 91×59). APROXIMADO: sem período no original; loop dos 850 quadros.
- [x] Select/modo: Music Test e Cheat Mode (CODE_809A44: 5 BAIXO em Contest/Music Test;
  `menu_nav_capture` t8–t13). Music Test com os 31 nomes (DATA_809C59) na fonte de área
  (pixel a pixel = captura) e as 31 faixas renderizadas do SPC (`music_test_spc_capture.lua`,
  `render_music_test.py`; APROXIMADO: 180 s sem loop, 4 s iniciais perdidos). Cheat Mode:
  B A → → A ← A X (sem barris DK) e Y A Start A ↓ ← A ↓ (50 vidas). APROXIMADO: rolagem da
  lista em corte seco; sem o som do código.
- [x] Mapa: ilha e cartão animados (t14: base + 8/1 regiões, loop dos 560/600 quadros).
- [x] Cabine: HUD (painel de vidas) desenhado em todas as áreas originais; vidas = contador
  real; balão de vida extra ($178, voo 1/8 até (212,40), +1 vida); texto do K. Rool ao passar
  pelo bilhete (`kabin-route-t5.csv`: aparece de uma vez no toque e fica).
- [x] Diddy carregando: deslocamento do objeto por quadro ($8B: −8 parado, −11/−9 andando).
- [x] Controle de Xbox (XInput) mapeado por posição do SNES; analógico com limiar de 50%.
  NÃO testado com o controle físico.
- [x] Morte: o Diddy cai, quica e fica no chão visível (o pisca de dano congelava apagado);
  a câmera acompanha a queda (`route-bot-trace.csv` 1260–1335); guarda contra morte dupla no
  mesmo quadro.
- Motor qa-69: replay de referência 1034/1034; 30 testes do recorte.

## Rodada 2026-10-20 (madrugada) — teste do owner, 15 itens

Medido no original com sondas novas: `menu_sound_capture.lua` (pedidos ao APU via hook em
B581FB + música $1C), `music_test_order_capture.lua`, `boot_music_spc_capture.lua`,
`menu_sfxbase_capture.lua`, `left_edge_probe_capture.lua`, `carry_probe_capture.lua` (t1/t2),
`kabin_probe_capture.lua` t6, `goal_probe_capture.lua` t8/t9.

- [x] Música da abertura: Opening (id 17) do quadro 145; título MAIN THEME (2) do 766.
- [x] Música do menu errada: os lotes 08–31 do Music Test tinham sido salvos com número
  errado (START durante upload é ignorado; 24 toques = id 15). Snapshots refeitos guiados
  por $1C (`music-test3/`); 2 e 17 tirados do boot desde o 1º quadro.
- [x] Efeitos do menu: cursor $33, confirmar/START do título/slot/modo $34 (canal 6), base
  SPC do menu (`menu-sfxbase.spc`).
- [x] Animações rápidas: `display.update_frequency = 60` (monitor >60 Hz rodava mais passos).
  Poses quadro a quadro contra `reference-poses.csv`: 288 → 814/1032 iguais.
- [x] Pulo "não fluido": B9D570 (aterrissagem começa a < $48 px do chão), virada $02/$12
  (B9E023, sprite vira em B9E01B), troca parado/andar/correr nos pontos do script (|vx|&$FFE0),
  ritmo da corrida (B9DA32), quique do pisão $1C com hit-stop. APROXIMADO: fase da caminhada
  1 quadro defasada depois de virar.
- [x] Borda esquerda: x 16 com vx mantido (`left-edge-t1.csv`).
- [x] Agachar e soltar afundava 8 px por vez (caixa ancorada no topo).
- [x] Porta da cabine: o batente esconde a Kong (material `clip_sprite`, x < porta−10).
  APROXIMADO: saída da cabine espelhada; sem fade de porta.
- [x] Sons: bilhete $2E, balão $2C, vida no contador $38 (painel $3C).
- [x] Barril carregado atrás da Kong (a mão fica na frente).
- [x] Arremesso: $14 com B9D8AC (Kong parada) / B9D967 (solta: vx $0C00 → $0400 em 1/16,
  vy −$100 +$50) / B9DFD5; sem som (o original não toca).
- [x] Sala do atalho: "!" de bananas (`PiratePanic_Warp.bin`, também Bonus1); relógio do giro
  nas subáreas.
- [x] Alvo: rádio ($89 pose2, `GFX_BoomboxAndSunglasses`) no golpe alto; música da vitória
  ($FB 3: parte de vitória da música da fase). APROXIMADO: 180 s sem ponto de loop.
- Motor qa-82: replay 1034/1034; 30 testes; boot → fase sem queda; revisão argus (3 pacotes):
  aplicadas saídas de segurança do arremesso e reset do estado de virada.
