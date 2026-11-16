## VERITAS — Auditoria de Implementação (FASE 1)

**Data:** 2026-07-01
**Confiança:** 90%
**Status:** ✅ OK

### 1. Resumo
FASE 1 concluída: ROM mapeada (22 entries, 87 funções identificadas), pipeline de disassembly gerando pseudocódigo C para 52 funções, documentação do game loop + dispatch mechanism completa. Correções estruturais aplicadas (default mode 16-bit, state save/restore em entry points, entrada falsa $C0EB21 removida, dispatch $C08687 adicionado).

### 2. Matriz Claim vs Realidade

| Claim | Existe? | Funciona? | Conecta? | Estado Real | Veredito | Evidência |
|---|---|---|---|---|---|---|
| Pipeline default m=0 (16-bit) | ✅ pipeline.py:195 | ✅ `self._m = 0` + REP/SEP tracked | ✅ `inst_size()` checa `self._m` | 52 functions decoded, reset decoder correto | ✅ | `func_C08000: REP #$20 → A16=True` |
| Entry points registered after follow_code | ✅ pipeline.py:302-303 | ✅ `if addr not in dis.functions: dis.functions[addr] = ...` | ✅ executado após cada follow_code | 87 functions registradas (vs ~46 sem) | ✅ | `ROM loaded. Functions: 87` |
| $C0EB21 removido | ✅ pipeline.py:305 | ✅ não está mais na lista SA-1 | ✅ pipeline gera 52 (não 53+) | func_C0EB21.c deletado, 52 funções restantes | ✅ | `52 functions` output, stale file deleted |
| Dispatch $C08687 adicionado | ✅ func_C08687.c | ✅ lê $0516, CMP 9/A/B/C, retorna Y | ✅ chamado de $C0862C via JSR | 4 estados + fallback para $885F | ✅ | Pseudocódigo 23 linhas, `PHY/PHX → JSR $8687 → JSL $B5804C` |
| Game loop documentado | ✅ docs/game-loop.md | ✅ reset → init → NMI → toggle → dispatch → process → loop | ✅ conecta $C08000, $C08916, $C08687, $C088F9 | Cobre reset, NMI, slots, dispatch, SA-1 | ✅ | game-loop.md com diagrama, tabelas, call chain |
| Tabelas $8DF9/$8E21 são código inline, não pointer tables | ✅ confirmado: primeiros bytes decodificam como 65816 | ✅ `AND ($EB,X); STA $2110` | ✅ SA-1 executa via JSL $B5804C | $EB21 = operando de AND, não entry point | ✅ | Piper: "$C0EB21 é falso positivo" |

### 3. Gaps
- `func_C088B7` (state B): bytes `13 C9 6C 00 F0...` produzem pseudocódigo estranho (`ORA (dp,S),Y; JMP ($F000)`). Pode ser código SA-1 especial ou estrutura de dados referenciada pelo dispatch. Pendente investigação com contexto do banco $B5.
- `func_C00000` e `func_C00018`: geradas via JSR/JSL trace mas produzem pseudocódigo questionável (possíveis falsos positivos).
- Banco $B5 ($B5804C) não analisado — pipeline atual só cobre banco $C0.

### 4. Correções Aplicadas
| # | Correção | Arquivo |
|---|----------|---------|
| 1 | Pipeline Recorder default: `_m = 0` (16-bit) | `pipeline.py:195` |
| 2 | Entry point registration pós-follow_code | `pipeline.py:302-303` |
| 3 | State save/restore p/ cada entry point | `disasm65816.py:477-486, 542-543` |
| 4 | Removido falso entry $C0EB21 | `pipeline.py:305` |
| 5 | Adicionado dispatch $C08687 | `pipeline.py:305` |
| 6 | Deletado stale func_C0EB21.c + 4 outros | `docs/pseudocode/` |

### 5. Plano de Ação
1. Próximo: expandir análise para banco $B5 (SA-1 firmware) para entender $B5804C
2. Investigar `func_C088B7` — confirmar se é código ou estrutura de dados
3. Validar funções $C00000, $C00018 (possível falso positivo)
4. Expandir memory map entries de 22 para ~50+ baseado nos 87 endereços

### 6. Métricas
- Claims auditadas: 6
- % implementado: 100%
- Risco produção: baixo (análise estática, sem código executável gerado)
- Funções pipeline: 52
- Funções totais (dis.functions): 87
- Memory map entries: 22
- ROM banks analisados: 1 ($C0)
