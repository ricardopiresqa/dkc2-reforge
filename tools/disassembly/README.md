# DiztinGUIsh Disassembly — DKC2 Reforge

## Setup

1. Abrir DIZ.exe: `tools/bin/DiztinGUIsh/DIZ.exe`
2. File → Open → selecionar `roms/dkc2.sfc`
3. Config:
   - **Cartridge Type:** LoROM
   - **ROM Size:** 4 MB
   - **Mapping:** SA-1 (Custom — ver notas abaixo)
   - **Header:** Standard SNES Header at 0x00FFC0
4. OK → vai mostrar os bancos de ROM mapeados

## Notas sobre SA-1

DKC2 usa chip SA-1 (mapper $31). Isso significa:
- CPU principal (65816) roda a ROM normalmente, mas algumas areas sao aceleradas pelo SA-1
- DiztinGUIsh pode nao reconhecer SA-1 perfeitamente — usar modo LoROM padrao
- Bancos SA-1 acelerados: tipicamente 0xC0-0xCF (dados graficos/audio)

## Output esperado

Apos import, exportar disassembly:
- File → Export → selecionar *all banks*
- Formato: CSV (com enderecos, bytes, mnemonics)
- Salvar em: `tools/disassembly/dkc2-disasm.csv`

## Workflow sugerido

1. Primeiro DiztinGUIsh → CSV bruto (cobertura completa)
2. Depois Ghidra → analise estruturada (funcoes, tipos, grafos)
3. Script Python em `tools/asm-pipeline/` → cruza ambos
