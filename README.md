# DKC2 Reforge

Reengenharia de **Donkey Kong Country 2 (SNES)** para PC em Defold + Lua, guiada por
engenharia reversa: cada comportamento é traduzido da disassembly e validado contra
capturas do emulador Mesen2 (trajetória, poses, câmera, áudio).

> **Projeto de fã, sem fins comerciais, sem vínculo com Nintendo ou Rare.**
> Este repositório **não contém a ROM nem nenhum asset extraído dela** (gráficos,
> música, sons, dados de fase). Para rodar o recorte original você precisa da **sua
> própria cópia** da ROM e gerar os assets localmente. Donkey Kong Country é marca
> da Nintendo.

## Estado

| Área | Estado |
|---|---|
| Fase 1-1 **Pirate Panic** | jogável do início ao alvo: título, menu, gameplay, Diddy + Dixie, barris, canhões, Rambi, warp, cabine, bananas/moedas, HUD, morte e vitória |
| Fidelidade | trajetória do player 1034/1034 frames idêntica à referência; poses 814/1032 idênticas |
| Áudio | música e SFX renderizados de snapshots SPC capturados do jogo original |
| Demais fases | esqueleto/placeholder; não jogáveis |

Lacunas conhecidas e o plano por rodada ficam em `docs/delivery/PIRATE_PANIC_COMPLETE_PLAN.md`.

## Stack

| Peça | Versão validada | Onde fica | Versionado? |
|---|---|---|---|
| Windows 10/11 x64 | — | — | — |
| Defold `bob.jar` | 1.13.0 | `./bob.jar` | não |
| JDK Temurin | 25.0.3+9 | `tools/jdk-25.0.3+9/` | não |
| Python | 3.12+ | `venv/` | não |
| Git (+ Git Bash) | qualquer recente | sistema | — |
| ffmpeg com `libgme` | build "full" | `PATH` | — |
| Mesen2 | 2.x | `tools/bin/Mesen2/` | não |
| Disassembly DKC2 | commit `bc1138f` | `tools/vendor/DKC2-disasm/` | não |
| ROM DKC2 **USA V1.0** | sua cópia | `tools/vendor/DKC2-disasm/DKC2/Donkey Kong Country 2 (USA V1.0).sfc` | **nunca** |
| Defold Editor (opcional) | 1.13.0 | sistema | — |

Opcionais para pesquisa: Ghidra (`tools/bin/Ghidra/`), DiztinGUIsh (`tools/bin/DiztinGUIsh/`),
[DKC2Recomp](https://github.com/elliotttate/DKC2Recomp) e
[SNES-ROM-Framework](https://github.com/Yoshifanatic1/SNES-ROM-Framework) em `tools/vendor/`.

## Instalação passo a passo (PowerShell)

```powershell
# 1. Código
git clone https://github.com/ricardopiresqa/dkc2-reforge.git
cd dkc2-reforge

# 2. Python
py -3.12 -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt

# 3. JDK 25 local (Temurin, zip x64) -> tools\jdk-25.0.3+9
#    https://adoptium.net/temurin/releases/?version=25  (extraia o zip em tools\)

# 4. bob.jar 1.13.0 na raiz do repo
#    https://github.com/defold/defold/releases  (asset "bob.jar" da versão 1.13.0)

# 5. Disassembly (fonte das rotinas, tabelas e bytecode de animação)
git clone https://github.com/Yoshifanatic1/Donkey-Kong-Country-2-Disassembly.git tools\vendor\DKC2-disasm
git -C tools\vendor\DKC2-disasm checkout bc1138ffa5568b4f74deba1a5ff6af8e562c06a1

# 6. Sua ROM (USA V1.0, sem header) com este nome exato:
#    tools\vendor\DKC2-disasm\DKC2\Donkey Kong Country 2 (USA V1.0).sfc

# 7. ffmpeg com libgme no PATH (ex.: winget install Gyan.FFmpeg) e confira:
ffmpeg -hide_banner -formats | Select-String gme

# 8. Mesen2 portátil em tools\bin\Mesen2\ (https://github.com/SourMesen/Mesen2/releases)
```

### Gerar os assets locais (derivados da ROM, ignorados pelo Git)

Os módulos de gameplay carregam `data.original.*` e o atlas/áudio de `assets/*/pirate/`.
Tudo isso é gerado a partir da ROM/disassembly pelas ferramentas em `tools/`:

```powershell
$py = "venv\Scripts\python.exe"
& $py tools\import_pirate_panic.py --source tools\vendor\DKC2-disasm\DKC2   # sprites base, paleta, nível
& $py tools\replay-compare\export_animation_scripts.py                    # bytecode de animação (data/original)
# exportadores por sistema (rode todos; cada um explica o que gera no docstring):
#   export_diddy_moves, export_dixie, export_walkers, export_klobber, export_rambi,
#   export_items, export_effects, export_bananas (--subareas), export_subareas,
#   export_menu, export_opening, export_victory_radio
```

Música e SFX: `render_music.py`, `render_music_test.py` e `render_sfx.py` convertem
snapshots `.spc` em `.ogg` (ffmpeg/libgme). Os snapshots vêm de capturas no Mesen2
feitas pelos scripts Lua `tools/replay-compare/*_capture.lua` (rodam no testrunner do
Mesen e **nunca sobrescrevem** saídas existentes). As referências de comparação
(`assets-raw/pirate/reference-*.csv`) também vêm dessas capturas.

Regras do pipeline:
- **Não rode** `write_atlas` nem regenere `main/game.atlas` do zero depois de inserir
  sprites: ele funde sprites `*_N`. Exportadores novos inserem entradas no atlas
  existente (`insert_atlas` / `insert_atlas_groups`).
- Nada derivado da ROM entra no Git: `assets-raw/`, `data/original/`, `assets/images/pirate/`,
  `assets/music/pirate/`, `assets/sfx/pirate/`, `samples/`, `tools/vendor/`, `*.atlas`.

> Aviso honesto: a ordem exata de todos os exportadores num ambiente zerado ainda
> não foi reproduzida ponta a ponta numa máquina nova. Se algum exportador reclamar
> de entrada ausente, a mensagem diz qual arquivo falta; rode antes o exportador ou a
> captura que o produz.

## Build e execução

```powershell
.\package.ps1 -OutDir dist/pirate-panic-dev     # build + bundle Windows (recusa sobrescrever)
.\play.ps1 -BundleDir dist/pirate-panic-dev      # roda o .exe
```

Controles: setas movem, `S`/espaço = B (pular), `Z` = Y (correr/pegar), `A` = A (trocar Kong),
`X` = X, `Q`/`W` = L/R, `Enter`/`Esc` = START, `C` = SELECT. Gamepad: botões na posição
do SNES (inferior B, esquerdo Y, direito A, superior X) — mapeado, não testado em Xbox.

### Flags de desenvolvimento (`--config=dkc2.<flag>=...` ou seção `[dkc2]` do `game.project`)

| Flag | Efeito |
|---|---|
| `start_level=level_1_1` | entra direto na fase |
| `autopilot=1` | o jogo se controla sozinho e grava trace do player |
| `capture_qa=1`, `qa_frames=N`, `qa_script="f=mask,..."` | QA determinístico por frame (máscaras: B1 Y2 SELECT4 START8 UP16 DOWN32 LEFT64 RIGHT128 A256 X512) |
| `qa_spawn_x`, `qa_spawn_feet`, `qa_invulnerable`, `reference_replay=1` | posicionamento e replay de referência para comparação |

## Testes

```powershell
venv\Scripts\python.exe -m pytest tools/tests -q
```

Testes que dependem da ROM, da disassembly ou de evidências locais são **pulados**
quando esses arquivos não existem — um clone limpo passa só o que não depende deles.

## Como o trabalho é validado

1. Ler a rotina original na disassembly (`Routine_Macros_DKC2.asm`) e traduzir para Lua
   (comentário com o endereço, ex.: `B9D570`).
2. Capturar o comportamento no Mesen2 com um script `*_capture.lua`.
3. Rodar o port com `capture_qa`/`reference_replay` e comparar trace/poses/framebuffer
   (`tools/replay-compare/`).
4. Só marcar como pronto com evidência (frames idênticos ou diferença documentada).

## Estrutura

```
main/                 engine Defold (Lua): game loop, player, câmera, colisão, render, HUD, som
main/original_*.lua   sistemas traduzidos do jogo original (animação, câmera, carry, menu...)
data/levels/          definição das fases (as do recorte original leem data/original/*)
tools/replay-compare/ exportadores, capturas Mesen, render de áudio, comparadores
tools/tests/          suíte pytest
tools/analysis, tools/asm-pipeline, tools/extract_assets  pesquisa/descompressão
docs/                 engenharia reversa (RAM map, sistemas) e docs/delivery (planos, gates)
```

O mundo usa a convenção do SNES: **Y cresce para baixo**; o render converte com
`to_screen_y` em `renderer.lua`. Coordenada "raw" do original = coordenada do port + 256.

## Prompt para preparar o ambiente com uma IA

Copie e cole num agente de código (Claude Code, Codex, OpenCode...) aberto na pasta do clone:

```text
Você vai preparar o ambiente de desenvolvimento do projeto DKC2 Reforge neste
repositório, no Windows, seguindo o README.md (seções "Stack", "Instalação passo a
passo" e "Gerar os assets locais").

Regras:
- Leia o README.md inteiro antes de agir. Mostre o plano e peça minha confirmação
  antes de baixar ou instalar qualquer coisa.
- Nunca baixe, procure ou peça a ROM: eu forneço o caminho da minha cópia. Se ela não
  estiver em tools\vendor\DKC2-disasm\DKC2\Donkey Kong Country 2 (USA V1.0).sfc,
  pare e me pergunte. Confira o SHA-1 que eu informar, se informar.
- Nunca apague arquivos nem pastas; nunca sobrescreva saídas (os scripts recusam).
- Nunca faça commit de nada derivado da ROM (veja o .gitignore) nem de segredos.
- Não rode write_atlas nem regenere main/game.atlas do zero.

Passos:
1. Verifique o que já existe: venv\, tools\jdk-25.0.3+9\, bob.jar, ffmpeg com libgme,
   tools\bin\Mesen2\, tools\vendor\DKC2-disasm (no commit bc1138f) e a ROM.
2. Instale só o que falta, nas versões da tabela "Stack".
3. Crie o venv e instale requirements.txt.
4. Gere os assets locais rodando o importador e os exportadores listados no README;
   leia o docstring de cada um para a ordem e as entradas. Se faltar uma entrada que
   vem de captura no Mesen2, me diga qual script *_capture.lua a produz.
5. Rode `venv\Scripts\python.exe -m pytest tools/tests -q` e mostre o resultado.
6. Gere o bundle com `.\package.ps1 -OutDir dist/pirate-panic-dev` e me diga como
   rodar com play.ps1.
7. No fim, liste o que foi instalado, o que foi gerado, o que falhou e o que ficou
   pendente, com a saída dos comandos como evidência.
```

## Licença

Código sob MIT (`LICENSE`). A licença **não** cobre a ROM, a marca nem qualquer
conteúdo do jogo original, que não fazem parte deste repositório.
