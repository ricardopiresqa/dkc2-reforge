# DKC2 Reforge — Delivery Acceptance Checklist

Estado por **evidência**, não por intenção. Itens sem evidência coletada ficam
**PENDENTE** — nunca PASS. Aceite geral só com bundle gerado + executável rodando.

**Veredito geral: FIDELIDADE COMPLETA PENDENTE.** Build fresco e sprites extraídos
não comprovam comportamento igual ao SNES. Evidências atuais abaixo prevalecem
sobre registros históricos de tentativas anteriores.

## Status desta sessão (2026-10-12)

| Item | Status | Evidência |
|---|---|---|
| JDK 25 local | OK | `tools\jdk-25.0.3+9\bin\java.exe -version` → `openjdk 25.0.3` (Temurin 25.0.3+9 LTS) |
| bob.jar local | OK | `tools\jdk-25.0.3+9\bin\java.exe -jar bob.jar --version` → `bob.jar version: 1.13.0` |
| Consolidação vendor (cópia) | OK | `python tools\project_dependencies.py` → DKC2-disasm: copiados=0 pulados=6306; DKC2Recomp: copiados=3 pulados=3914; SNES-ROM-Framework: copiados=0 pulados=90 |
| Idempotência da cópia | OK | 2ª execução: `copiados=0` nas 3 fontes (tudo pulado por hash igual) |
| Manifest copy/hash | OK | `tools/vendor/<nome>-manifest.json` gerados (path, hash, size) |
| Fontes externas intactas | OK | cópia é read-only nas fontes; nada deletado (script não tem delete) |
| package.ps1 sem absoluto / sem delete | OK | grep: nenhum `C:\Projetos` e nenhum `Remove-Item` (apenas comentário que o proíbe) |
| play.ps1 relativo ao bundle | OK (estático) | grep: sem `C:\Projetos`; aponta `dist/pirate-panic` + `.exe` do bundle |
| Build de bundle / `.exe` / runtime | **PENDENTE** | não executados nesta sessão — build só depois da integração |

## Build System

| Componente | Status | Evidência |
|---|---|---|
| Java Environment | OK | verificado nesta sessão (acima) |
| bob.jar | OK | 1.13.0 verificado nesta sessão (acima) |
| Compilação (`bob build`) | OK (evidência anterior) | `.luac`/`.goc` gerados em `build\default\main\` em sessão anterior; não re-executado nesta sessão (build adiado até integração) |
| Resource Processing | PENDENTE | `game.arci` não gerado — causa do bundling falhar |
| Bundling (`package.ps1`) | **PENDENTE** | bundle `dist/pirate-panic` não tentado nesta sessão; tentativa anterior falhou (`game.arci` ausente) |
| Executable Output | **PENDENTE** | nenhum `.exe` de bundle produzido ainda |

## Runtime

| Componente | Status | Evidência |
|---|---|---|
| dmengine (dev) | PENDENTE | `dmengine` não está no repo; deve casar com bob 1.13.0 |
| Executável do bundle (`play.ps1`) | **PENDENTE** | depende do bundle; não validado |
| Inicialização / gameplay | **PENDENTE** | não testável sem executável |

## Assets

| Componente | Status | Evidência |
|---|---|---|
| Placeholder sprites (CLI) | OK | `python tools\gen_placeholder_sprites.py` existe e gera `assets/images/gen/**` |
| Atlas (CLI) | OK | `python tools\gen_atlas.py` gera `main/game.atlas` |
| Assets derivados fora do Git | OK | `.gitignore` cobre `assets-raw/`, `samples/`, `outputs/`, `assets/images/gen/`, `main/game.atlas` |
| Assets derivados da ROM | EXCLUÍDO (por regra) | nada extraído da ROM versionado (constitution regra 1) |
| Áudio | PENDENTE | sem evidência de processamento de áudio |

## Codebase

| Componente | Status | Evidência |
|---|---|---|
| Lógica Lua | OK (parcial) | `main/` com player/câmera/colisão/objetos/HUD parciais |
| Componente Go | OK (parcial) | `main/render/entity.go` (protótipo de sprite) |
| Config Defold | OK | `game.project` válido |
| Fases do jogo completas | **NENHUMA** | estado de protótipo declarado no README |

## Dependencies

| Componente | Status | Evidência |
|---|---|---|
| DKC2-disasm → tools/vendor | OK | 6306 arquivos no snapshot; manifest presente |
| DKC2Recomp → tools/vendor | OK | 3917 arquivos no snapshot; manifest presente |
| SNES-ROM-Framework → tools/vendor | OK | 90 arquivos no snapshot; manifest presente |
| JDK local | OK | `tools/jdk-25.0.3+9` (gitignored — binários não commitados) |
| bob.jar | OK | raiz do repo |
| `C:\Projetos\tools\defold-mcp` | **FORA DE ESCOPO** | recurso compartilhado entre projetos; não copiado, não modificado, não gerenciado por este repo |

## Gates de aceite (checklist — todos PENDENTES até evidência)

- [ ] `.\package.ps1` gera `dist/pirate-panic` com `.exe` dentro — **PENDENTE** (após integração)
- [ ] `.\play.ps1` executa o `.exe` do bundle por caminho relativo — **PENDENTE**
- [ ] Janela abre e inicializa (título visível) — **PENDENTE**
- [ ] Smoke de gameplay (flag `autopilot = 1` roda 600 frames sem crash) — **PENDENTE**
- [ ] Regressão de colisão/física básica — **PENDENTE** (sem suíte automatizada)
- [ ] Áudio toca (ou ausência documentada) — **PENDENTE**

## Known Limitations

1. **Bundling**: tentativa anterior falhou com `game.arci` ausente; investigação pendente.
2. **Sem executável**: `play.ps1` só funciona após bundle bem-sucedido.
3. **Java 25 específico**: usar o JDK local (`tools\jdk-25.0.3+9`); Java do sistema não serve.
4. **Plataforma**: target atual `x86_64-win32` apenas.
5. **Testes**: sem suíte automatizada ampla; checks pontuais + smoke manual.

## Build Facts

| Fact | Status | Evidence |
|---|---|---|
| Dependency copy/hash | OK | Verified via manifest files in tools/vendor |
| Diddy | EXTRAÍDO/INTEGRADO | 101 poses OAM; scripts F9 originais; sampled pose/mode10/10 PASS |
| Neek/Klomp | EXTRAÍDO/INTEGRADO | 8 + 9 frames com paletas e hashes de fontes; IA e timings não validados |
| Testes focados atuais | OK | `pytest tools/tests -q`: 53 passed; outputs unit fixtures isolados |
| Exclusion ROM/raw/signing keys | PASS | `.defignore` excludes `/assets-raw`, `/roms`, `/tools`, `/manifest.private.der`; `audit_safe_bundle.py`: no forbidden strings/raw tree files |
| Bundle seguro atual | PASS | `dist/pirate-panic-final-secure-current`; raw/signing audit pass, runtime220frames, input QA true, captures9/9 |
| Decoder | PARCIAL | 918 tiles, 376 metatiles, mapa compartilhado de 924 colunas; não significa 924 colunas de Pirate Panic |
| Recorte da sala | BYTE-VERIFICADO | Snapshot USA v1.0: banco7F, base0, definições7136; mapa sala7136B coincide com source após deslocamento32B. Metatiles coincidem byte a byte; valores de câmera7104/528 lidos da RAM. Importador rejeita hashes e metadata contraditórios |
| Atlas | CORRIGIDO | Recursos `/assets/...`, sem `/C:/...`; caminhos de raiz do projeto Defold |
| Transparência do cenário | CORRIGIDA | Mapas/chunks RGBA; índice 0 mantém alpha 0. Tile sheet de inspeção pode continuar RGB |
| Build fresco | OK | PTY `pty_927f4fd0`, exit 0; log mostra Building e createArchive. `dist/pirate-panic-art-verified-build` |
| Build QA | OK | PTY `pty_9fe0afdf`, exit 0; `dist/pirate-panic-art-qa`; instrumentação de 600 frames opt-in |
| Runtime novo | SMOKE VERIFICADO | PTY `pty_60a59572` exit 0, sem timeout; `dist/pirate-panic-art-qa/dkc2-reforge/qa-runtime.json`: 600 frames, fase gameplay, estados idle/run/fall/jump, sem morte, sprites até 17 e pool_drops=0. Não prova conclusão da fase |
| Auditoria independente | INCONCLUSIVA | Parecer VERITAS inicial tem divergências confrontadas com código; rota de reconciliação falhou. Nenhum PASS promovido |

### Incremento de movimento observado

- Input manual: teste Lua reproduz `on_input -> update -> post_update`; falha
  inicial corrigida e `input_check=true` observado no bundle input-fixed.
- Baseline replay original: FAIL, até242px em X e17px em Y.
- Superfícies planas: handlers reais `LDA #altura; RTS` da tabela de80 funções
  `DATA_B5CA38`; piso original com property5 retorna15, superfície mundial209.
  Shapes complexos/flags desconhecidos continuam fallback, **não verificados**.
- Caminhada: rampa8.8 e limites da tabela Diddy original; 5checkpoints reais
  PASS dentro1px/1frame em `dist/pirate-panic-ground-aligned`.
  Recibo: `docs/delivery/ground-walk-receipt.json`.
- Primeiro salto curto: gravidade/impulso e windup extraídos/observados;
  10checkpoints caminhada+salto PASS1px/1frame, bundle `pirate-panic-short-jump`.
  Recibo `walk-short-jump-receipt.json`. Não prova salto longo ou outros contextos.
- OAM Diddy: canvas comum conserva origem das poses, sem recentralização por
  frame. Raster da origem quantizado como OAM; simulação subpixel é outro gate.
- Diddy: captura original same-ROM e bytecode F9/BC8000; pose/mode identity10/10
  sampled checkpoints PASS. Não implica player completo nem todos callbacks.
- Câmera: o último bundle passa X/Y nos8 primeiros pontos em1px, mas frames
  173/180 divergem2px Y. Câmera FAIL/PENDENTE; não relaxar tolerância.
- VM de animação carrega bytecode F9 original e lookup BC8000;10/10 pose IDs
  amostrados coincidem no bundle atual. Near-ground condition é parcial.
- Câmera usa perfil de18 regions capturado da RAM do mesmo ROM hash. X offsets
  e Y offsets passam8/10 checkpoints até1px; frames173/180 ainda divergem2px
  em Y. Vizinhos/interpolação/airborne predictor não terminados; câmera FAIL.
- CPU Lua: `os.clock` no callback input+game, não GPU; granularidade pode produzir
  amostras0ms e isso não significa custo zero. Tempo `dt` não é tempo de CPU.

## Lacunas que bloqueiam “todos os elementos fiéis”

**Critério aprovado pelo owner (2026-10-13):** desvio máximo de 1 pixel por
eixo e 1 frame nos checkpoints semânticos definidos. Origem e sequência de
inputs devem coincidir. `tools/replay-compare/compare_checkpoints.py` rejeita
capturas vazias, IDs duplicados, estados divergentes e proveniência distinta.
Seis testes sintéticos validam o comparador; não são prova de fidelidade do jogo.

Mesen foi isolado via configuração portátil em `tools/bin/Mesen2/`; script
headless e smoke de 120 frames da ROM local terminaram com exit 0. Captura de
rota ainda não aceita: inicialização não significa entrada em Pirate Panic.

Owner autorizou I/O Lua apenas na cópia portátil do projeto para scripts de
captura revisados. `Debug.ScriptWindow.AllowIoOsAccess=true`,
`AllowNetworkAccess=false`. Configuração externa/OneDrive não alterada.

- Física completa/câmera e timings sem aceite. Replay cobre caminhada inicial e
  primeiro short-jump, não toda fase nem partner/enemies/roll contexts.
- Colisão tem backend parcial de alturas planas originais; slopes, tetos,
  flags e rotinas condicionais não estão completos. Flag `$4000` não comprovada.
- Dixie/parceiro, IA original, Rambi, barris/objetos restantes, HUD original,
  bônus/cabine/warp e conclusão ponta a ponta não aprovados.
- BG2 map/GFX do frame gameplay coincide com fonte decodificada, mas framebuffer
  não aprovado. Comparação frame40:54742/57344 pixels visíveis diferem;
  `framebuffer-comparison.json` registra FAIL/NOT_PROVEN.
- Palette `Sprite_Diddy_Active` confere15/15 cores em CGRAM145 nos frames
  40,60,100,140,153,180. Outras palettes dos sprites permanecem sem atribuição.
- BG1 viewport frame40 exportado só como artefato QA; não substitui o stream
  de mapas da fase e não é render de produção.
- PPU snapshot tardio difere do gameplay: VRAM7665bytes e CGRAM83bytes.
  Palette Diddy Active bate exatamente15words em CGRAM[145..159] nos5frames.
  BG3 map ainda não corresponde à fonte incbin; não chamar cordas integradas
  fiéis. HDMA/color math/scroll continuam pendentes.
- Native256x224 aprovado pelo owner; janela4x1024x896 medida, sem render errors,
  220frames e regressão motionPASS. `native-view-receipt.json`.
- HUDoriginal ainda não pronto; contadores SCORE/HP/inglês provisórios ocultos.
- Pirate Panic suprime sons protótipo para não fingir fidelidade; música e
  efeitos originais permanecem ausentes.
- Escopo deste aceite é Pirate Panic, não o jogo inteiro.
- Qualidade: Lizard1.23.0 mediu `main/player.lua:M.update` com CC224; outras
  funções tocadas de colisão/renderer também excedem10. Helpers novos de motion
  e testes estão≤10. Gate global de CC não aprovado; não houve refactor amplo
  de estados provisórios para esconder esse problema.
- QA visual automatizado via extensão opt-in `screenshot.png`; somente captura
  framebuffer do jogo, sem acesso ao desktop. Resultado visual atual: FAIL.

## Comandos verificados nesta sessão

```powershell
tools\jdk-25.0.3+9\bin\java.exe -version
tools\jdk-25.0.3+9\bin\java.exe -jar bob.jar --version
python tools\project_dependencies.py
```

## Comandos adiados (executar após a integração)

```powershell
.\package.ps1          # bundle dist/pirate-panic
.\play.ps1             # roda .exe do bundle
tools\jdk-25.0.3+9\bin\java.exe -jar bob.jar build
```
