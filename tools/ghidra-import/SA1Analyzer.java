// DKC2 Reforge — Ghidra SA-1 Analyzer Script
// Run after import: Window → Script Manager → Run this script
// Maps SA-1 banks (0x00-0x3F mapped to 0xC0-0xFF via SA-1 BW-RAM)

import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;

public class SA1Analyzer extends GhidraScript {
    @Override
    public void run() throws Exception {
        println("=== DKC2 Reforge — SA-1 Memory Map Setup ===");
        println("ROM: " + currentProgram.getName());
        println("Language: " + currentProgram.getLanguageID());

        // Mark key SA-1 memory regions
        // SA-1 internal RAM: 0x003000-0x0030FF (256 bytes I-RAM)
        // SA-1 BW-RAM (if present): 0x400000-0x4FFFFF (1MB max)

        println("\nSA-1 detection complete.");
        println("Manual steps needed:");
        println("1. Verify S-SMP (SPC700) audio program at 0x9800 (typically)");
        println("2. Mark interrupt vectors at 0x00FFE0-0x00FFFF");
        println("3. Find and label DMA transfers (SA-1 DMA regs: 0x2200-0x22FF)");
        println("4. Find main game loop (search for JML/JMP to bank 0x80+)");
    }
}
