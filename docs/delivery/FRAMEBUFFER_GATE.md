# Pirate Panic — gate de framebuffer, não aceite da fase

## Captura aprovada e isolada

- Owner aprovou `britzl/defold-screenshot` commit
  `5f3098e3bfc37e8f26bde9428436b4d4499d1d50`, MIT, orçamentoR$0.
- Engine compilado no scaffold `tools/native-build-screenshot`, com binding
  vazio; pacote não contém ROM, arte extraída, Lua/cenas do jogo ou chave privada.
- Nativeengine SHA256:
  `d647fce903f664a1accad16591c9da7b424e1bf366e25fede7ddd97d6f4ef8f5`.
- Jogo compilado localmente; engine instalado somente em bundles novos de QA.
  `.defignore` mantém ferramentas/scaffold fora do grafo de build do jogo.
- Captura por `screenshot.png` do framebuffer **deste jogo**, após render;
  nenhuma leitura do desktop. Desligada por padrão, flag `dkc2.capture_qa=1`.
- Nove capturasPNG1024x896 verificadas, callbacks concluídos (`pending=0`).
- `.defignore` exclui `/assets-raw`, `/roms` e `/tools`; runtime modules foram
  movidos para `data/original/pirate`. Audit do bundle `safe-assetsraw` não
  encontrou strings proibidas nem arquivos raw; bundle executou220frames.
- Signing keys `.der` também ficam fora do bundle via `.defignore`; último
  `dist/pirate-panic-secure-bundle` foi auditado depois da instalação do engine
  QA e não contém nomes de ROM/snapshots/chaves nem raw file tree.

## Referência original

Mesen portátil usa mesma ROMUSA v1.0 da disassembly. PPM40 contém exatamente
183552bytes de payloadRGB, dimensão256x239. Perfil do frontend explicitamente
Top7/Bottom8 exibe256x224. Comparador registra crop em vez de deslocar imagens
para esconder diferenças. Não assumir que crop altera geometria/OAM do jogo.

O primeiro parecer de QA alegou framebuffer240/string e arquivo ausente,
sem medir arquivos reais; contradiz PPM256x239 existente e callback que fornece
tabela de pixels. Parecer não promoveu nenhum PASS de referência.

## Resultado do primeiro confronto

- Escala4x foi replicação inteira exata dos pixels do port.
- Framebuffers originais/port diferem: scroll, ondas, color math, poses e
  objetos ainda incompletos. `framebuffer-comparison.json` é diagnóstico,
  **não** aprovação visual. Nada foi alinhado/warpeado para melhorar métricas.
- Build atual `dist/pirate-panic-final-secure-current`; frame40 mismatch54742
  de57344pixels após crop explícito. Original de referência é frame256x239;
  frame do jogo é1024x896 (nearest integer4). Mismatch visual permanece FAIL.
- Em comparação, camadaBG2 estática exact map/GFX-source, mas layer3/scene em
  runtime não foi validada com PPU por frame. Frames reais40..180 guardam VRAM,
  CGRAM e PPU state. Frame40 vs snapshot tardio tem7665 bytes VRAM e83 bytes
  CGRAM diferentes; BG3 render tardio não pode ser apresentado como layer fiel.
- `Sprite_Diddy_Active.bin` confere15/15 cores no CGRAM bank145 em5frames
  comparados. Diferenças nas demais palettes de sprite (indices177..223)
  continuam sem atribuição por entidade.
- BG1 PPU viewport do frame40 em
  `assets-raw/pirate/reference-layer1-frame-0040-viewport.png` mostra ropes e
  geometria estática real. Usada como referência, não como fundo estático do jogo.
- Original-mode BG3 draw call is disabled pending frame-accurate source.
  Frame40 PNG hash stayed identical to prior bundle, so the prior asset may
  already have been visually inactive; BG3 remains missing/unproven. Overall
  framebuffer mismatch is still FAIL.
- MarcadorB falso vinha de `BarrelCannon -> bonus_barrel`; removida substituição.
  Sinal de animal não vira corda e scripts desconhecidos não viram bananas,
  zingers ou inimigos inventados. Dados preservados; handlers seguem faltantes.

## Animação source-driven

- DATA_F90000 seleciona scripts originais; BC8000 resolve IDs de pose.
- Imported101posesDiddy incluem walk/fall/land/juggling, com origem OAM comum.
- VM usa bytecode original F9, não CSV de replay para produzir animação.
- Posição e pose/ID bateram nos10checkpoints iniciais após corrigir chamada
  faltante no gameplay e callbacks de landing. Isso não é aceite de todos
  callbacks, de inércia completa, som ou personagem parceiro.
- Near-ground está parcial e opcode8E retém SoundID, mas áudio ainda não toca.
- Todos pose IDs referenciados pelos7scripts exportados têm recursos.
- Último bundle reproduz inputs/capturas com fixed tick: checkpoints de posição e
  pose IDs passam10/10. O payload de Idle/Walk/Jump continua source-driven.
- Câmera profile observa18 regiones e baixa discrepância: offsets batem8/10
  checkpoints em1px; Y está2px atrasado em frames173/180. Não aprovar ainda.

## Próximo delta original de câmera

`CODE_B5E4ED`/`B5E5AC`/`B5E5EC`/`B5E73B` calculam targets32bits8.8,
triângulos de balanço via framecounter2A e lookahead56/128px. Regiões/forks
RAM7E8D28..9428 são carregadas por `CODE_B5E0C2` a partir de FD934D.
`B5EEB1`/`B5EF89` implementam springs/damping, não follow por âncora fixa.
Port atual ainda aproximado; **não** reproduzir CSV como lógica de câmera.

Demais gates: HUD, partner/Dixie, AI, Rambi, bananas/KONG/DKCoin, áudio,
bônus/cabine/warp, goal/restart/percurso e revisão independente completa.
