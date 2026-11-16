# Ghidra Import — DKC2 Reforge

## Setup

1. Abrir Ghidra GUI: `tools/bin/Ghidra/ghidra_12.1.2_PUBLIC/ghidraRun.bat`
2. File → New Project → Non-Shared → salvar em `tools/ghidra-import/dkc2-reforge.gpr`
3. File → Import File → selecionar `roms/dkc2.sfc`
   - Formato: Raw Binary
   - Language: 65816 Little Endian (SA-1 aware)
   - Options: marcar "Analyze immediately"
4. Rodar auto-analysis (sim ou nao agora — pode rodar depois)

## Headless (opcional, futuramente)

```powershell
& "tools/bin/Ghidra/ghidra_12.1.2_PUBLIC/support/analyzeHeadless.bat" ^
    tools/ghidra-import/ ^
    dkc2-reforge ^
    -import roms/dkc2.sfc ^
    -processor "SuperH4" ^
    -cspec "default"
```
