# Constitution — DKC2 Reforge

> Lido automaticamente pelo big-pickle via AGENTS.md ao abrir este projeto.
> Atualizar sempre que houver mudanca de stack, arquitetura ou restricoes.

## Identidade
- **Projeto:** DKC2 Reforge
- **Descricao:** Port nativo fiel de Donkey Kong Country 2 (SNES) para PC via engenharia reversa. Stack: Defold + Lua.
- **Status:** FASE 2 — Reverse de engine (compressao decodificada)
- **Roadmap:** 7 fases (FASE 0 a FASE 6) no ClickUp, List 901714869571

## Stack Canonica
- Engine: Defold (Lua)
- Reverse: Mesen2, bsnes-plus, Ghidra
- Scripts: Python 3
- Assembler: asar / diztinguish
- Versionamento: Git

## Restricoes — o agente NUNCA deve:
- NUNCA commitar ROMs ou assets extraidos (roms/, assets-raw/ sao gitignored)
- NUNCA distribuir codigo binario ou assets protegidos por copyright
- Tudo extraido de ROM deve ficar em pastas gitignored
- Schema de dump padronizado (docs/memory-map.md) deve ser preenchido antes de qualquer analise
- Pink Loop obrigatorio para TODO card (sem excecao)
- Nao commitar secrets ou env vars

## Principios de Qualidade
- Pseudocodigo revisado antes da implementacao em Lua
- Memory map versionado como JSON schema em docs/memory-map.md
- Commits: Conventional Commits (feat/fix/chore/docs)
- Testes: pytest para ferramentas Python

## Modulos Ativos (previsao)
- tools/dump/ — dump de memoria e automacao
- tools/extract-assets/ — extracao de sprites/audio
- tools/replay-compare/ — diff de replay
- engine/ — projeto Defold com logica do jogo
- docs/pseudocode/ — assembly → pseudocodigo por sistema

## Decisoes Arquiteturais (ADRs)
| # | Decisao | Motivo | Data |
|---|---------|--------|------|
| 1 | Defold como engine alvo | Lua, leve, multiplataforma, sem runtime pesado | 2026-06-30 |
| 2 | Mesen2 + bsnes-plus para debug | Precisao ciclica + ferramentas de debug | 2026-06-30 |
| 3 | Ghidra para disassembly estruturado | Melhor decompilador ASM → C-like disponivel | 2026-06-30 |
| 4 | Schema JSON padronizado para memory map | Rastreabilidade entre endereco, flag M/X e comportamento | 2026-06-30 |
| 5 | ROMs/assets nunca no repo | Compliance legal com copyright da Nintendo | 2026-06-30 |
| 6 | Nibble-pair compression (CMP/PAC1) como formato canonico | 490 amostras validam decoder Python com fallback LO/HI | 2026-07-03 |

## Historico de Sessoes
| Data | Card | Resumo | Arquivos alterados |
|------|------|--------|--------------------|
