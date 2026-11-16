rom = open('roms/dkc2.sfc', 'rb').read()
def r(b,a): return (b&0x3F)*0x10000+a

def disasm_until(addr, target_addrs, max_instr=500):
    """Disassemble from addr until one of target_addrs is reached or max_instr."""
    a = r(0x80, addr)
    offset = a
    m = x = False  # 16-bit tracking
    output = []
    prev_instrs = []
    base_addr = addr  # SNES address
    
    for _ in range(max_instr):
        if offset >= len(rom):
            output.append(f"  END @ {base_addr + (offset - a):04X}")
            break
        
        byte = rom[offset]
        instr_addr = base_addr + (offset - a)
        instr = None
        
        # Track patterns for new handler: LDA #imm + JMP B0EE or STA $20
        if byte == 0xA9:  # LDA #imm
            if m:
                val = rom[offset+1]
                op = f"LDA #{val:02X}"
                offset += 2
            else:
                val = rom[offset+1] | (rom[offset+2]<<8)
                op = f"LDA #{val:04X}"
                offset += 3
            instr = (instr_addr, op)
            prev_instrs.append(('lda_imm', val, instr_addr))
            if len(prev_instrs) > 5: prev_instrs.pop(0)
            
        elif byte == 0x85:  # STA dp
            dp = rom[offset+1]
            op = f"STA ${dp:02X}"
            offset += 2
            instr = (instr_addr, op)
            if dp == 0x20:
                prev_instrs.append(('sta_20', 0, instr_addr))
            else:
                prev_instrs.append(('other', 0, instr_addr))
            if len(prev_instrs) > 5: prev_instrs.pop(0)
            
        elif byte == 0x4C:  # JMP abs
            target = rom[offset+1] | (rom[offset+2]<<8)
            op = f"JMP ${target:04X}"
            instr = (instr_addr, op)
            offset += 3
            
            # Check if this is JMP $B0EE (set new handler pattern)
            if target == 0xB0EE:
                for ptype, val, paddr in prev_instrs:
                    if ptype == 'lda_imm':
                        output.append(f"  ${paddr:04X}: LDA #{val:04X}  <-- new handler addr?")
                        break
            
            output.append(f"  {instr_addr:04X}: {op}")
            if target in target_addrs:
                output.append(f"  ^^^ TARGET REACHED: ${target:04X}")
                break
            # Check if it goes outside our range
            if target < addr or target > addr + 0x200:
                output.append(f"  ^^^ JMP outside range -> ${target:04X}")
                break
            a = r(0x80, target)
            offset = a
            prev_instrs = []
            continue
            
        elif byte == 0x5C:  # JML
            dst = rom[offset+1] | (rom[offset+2]<<8) | (rom[offset+3]<<16)
            op = f"JML ${dst:06X}"
            instr = (instr_addr, op)
            output.append(f"  {instr_addr:04X}: {op}")
            offset += 4
            if dst in target_addrs:
                output.append(f"  ^^^ TARGET REACHED: ${dst:06X}")
                break
            # Follow JML in same bank?
            dst_addr = dst & 0xFFFF
            dst_bank = (dst >> 16) & 0xFF
            if dst_bank != 0x80:
                output.append(f"  ^^^ JML to bank ${dst_bank:02X}, stopping")
                break
            a = r(0x80, dst_addr)
            offset = a
            prev_instrs = []
            continue
            
        elif byte == 0x22:  # JSL
            dst = rom[offset+1] | (rom[offset+2]<<8) | (rom[offset+3]<<16)
            op = f"JSL ${dst:06X}"
            instr = (instr_addr, op)
            offset += 4
            
        elif byte == 0x60:  # RTS
            op = "RTS"
            instr = (instr_addr, op)
            offset += 1
        elif byte == 0x6B:  # RTL
            op = "RTL"
            instr = (instr_addr, op)
            offset += 1
        elif byte == 0x40:  # RTI
            op = "RTI"
            instr = (instr_addr, op)
            offset += 1
        elif byte == 0x0B:  # PHD
            op = "PHD"; offset += 1
            instr = (instr_addr, op)
        elif byte == 0x48:  # PHA
            op = "PHA"; offset += 1
            instr = (instr_addr, op)
        elif byte == 0xDA:  # PHX
            op = "PHX"; offset += 1
            instr = (instr_addr, op)
        elif byte == 0x5A:  # PHY
            op = "PHY"; offset += 1
            instr = (instr_addr, op)
        elif byte == 0x68:  # PLA
            op = "PLA"; offset += 1
            instr = (instr_addr, op)
        elif byte == 0xFA:  # PLX
            op = "PLX"; offset += 1
            instr = (instr_addr, op)
        elif byte == 0x7A:  # PLY
            op = "PLY"; offset += 1
            instr = (instr_addr, op)
        elif byte == 0x2B:  # PLD
            op = "PLD"; offset += 1
            instr = (instr_addr, op)
        elif byte == 0xAB:  # PLB
            op = "PLB"; offset += 1
            instr = (instr_addr, op)
        elif byte == 0x8B:  # PHB
            op = "PHB"; offset += 1
            instr = (instr_addr, op)
        elif byte == 0x4B:  # PHK
            op = "PHK"; offset += 1
            instr = (instr_addr, op)
        elif byte == 0x1B:  # TCS
            op = "TCS"; offset += 1
            instr = (instr_addr, op)
        elif byte == 0x5B:  # TCD
            op = "TCD"; offset += 1
            instr = (instr_addr, op)
        elif byte == 0x7B:  # TDC
            op = "TDC"; offset += 1
            instr = (instr_addr, op)
        elif byte == 0x9A:  # TXS
            op = "TXS"; offset += 1
            instr = (instr_addr, op)
        elif byte == 0xBA:  # TSX
            op = "TSX"; offset += 1
            instr = (instr_addr, op)
        elif byte == 0xAA:  # TAX
            op = "TAX"; offset += 1
            instr = (instr_addr, op)
        elif byte == 0x8A:  # TXA
            op = "TXA"; offset += 1
            instr = (instr_addr, op)
        elif byte == 0x98:  # TYA
            op = "TYA"; offset += 1
            instr = (instr_addr, op)
        elif byte == 0xA8:  # TAY
            op = "TAY"; offset += 1
            instr = (instr_addr, op)
        elif byte == 0x9B:  # TXY
            op = "TXY"; offset += 1
            instr = (instr_addr, op)
        elif byte == 0xBB:  # TYX
            op = "TYX"; offset += 1
            instr = (instr_addr, op)
        elif byte == 0x1A:  # INC A
            op = "INC A"; offset += 1
            instr = (instr_addr, op)
        elif byte == 0x3A:  # DEC A
            op = "DEC A"; offset += 1
            instr = (instr_addr, op)
        elif byte == 0xE8:  # INX
            op = "INX"; offset += 1
            instr = (instr_addr, op)
        elif byte == 0xCA:  # DEX
            op = "DEX"; offset += 1
            instr = (instr_addr, op)
        elif byte == 0xC8:  # INY
            op = "INY"; offset += 1
            instr = (instr_addr, op)
        elif byte == 0x88:  # DEY
            op = "DEY"; offset += 1
            instr = (instr_addr, op)
        elif byte == 0xE6:  # INC dp
            dp = rom[offset+1]
            op = f"INC ${dp:02X}"; offset += 2
            instr = (instr_addr, op)
        elif byte == 0xEE:  # INC abs
            addr = rom[offset+1] | (rom[offset+2]<<8)
            op = f"INC ${addr:04X}"; offset += 3
            instr = (instr_addr, op)
        elif byte == 0xC6:  # DEC dp
            dp = rom[offset+1]
            op = f"DEC ${dp:02X}"; offset += 2
            instr = (instr_addr, op)
        elif byte == 0xCE:  # DEC abs
            addr = rom[offset+1] | (rom[offset+2]<<8)
            op = f"DEC ${addr:04X}"; offset += 3
            instr = (instr_addr, op)
        elif byte == 0xA2:  # LDX imm
            if x:
                val = rom[offset+1]
                op = f"LDX #{val:02X}"; offset += 2
            else:
                val = rom[offset+1] | (rom[offset+2]<<8)
                op = f"LDX #{val:04X}"; offset += 3
            instr = (instr_addr, op)
        elif byte == 0xA0:  # LDY imm
            if x:
                val = rom[offset+1]
                op = f"LDY #{val:02X}"; offset += 2
            else:
                val = rom[offset+1] | (rom[offset+2]<<8)
                op = f"LDY #{val:04X}"; offset += 3
            instr = (instr_addr, op)
        elif byte == 0xA5:  # LDA dp
            op = f"LDA ${rom[offset+1]:02X}"; offset += 2
            instr = (instr_addr, op)
        elif byte == 0xAD:  # LDA abs
            addr = rom[offset+1] | (rom[offset+2]<<8)
            op = f"LDA ${addr:04X}"; offset += 3
            instr = (instr_addr, op)
        elif byte == 0xAF:  # LDA long
            addr = rom[offset+1] | (rom[offset+2]<<8) | (rom[offset+3]<<16)
            op = f"LDA ${addr:06X}"; offset += 4
            instr = (instr_addr, op)
        elif byte == 0x8D:  # STA abs
            addr = rom[offset+1] | (rom[offset+2]<<8)
            op = f"STA ${addr:04X}"; offset += 3
            instr = (instr_addr, op)
        elif byte == 0x8F:  # STA long
            addr = rom[offset+1] | (rom[offset+2]<<8) | (rom[offset+3]<<16)
            op = f"STA ${addr:06X}"; offset += 4
            instr = (instr_addr, op)
        elif byte == 0x64:  # STZ dp
            op = f"STZ ${rom[offset+1]:02X}"; offset += 2
            instr = (instr_addr, op)
        elif byte == 0x9C:  # STZ abs
            addr = rom[offset+1] | (rom[offset+2]<<8)
            op = f"STZ ${addr:04X}"; offset += 3
            instr = (instr_addr, op)
        elif byte == 0x9E:  # STZ abs,X
            addr = rom[offset+1] | (rom[offset+2]<<8)
            op = f"STZ ${addr:04X},X"; offset += 3
            instr = (instr_addr, op)
        elif byte == 0xC2:  # REP
            val = rom[offset+1]
            op = f"REP #{val:02X}"; offset += 2
            instr = (instr_addr, op)
            if val & 0x10: m = False
            if val & 0x20: x = False
        elif byte == 0xE2:  # SEP
            val = rom[offset+1]
            op = f"SEP #{val:02X}"; offset += 2
            instr = (instr_addr, op)
            if val & 0x10: m = True
            if val & 0x20: x = True
        elif byte == 0x0A:  # ASL A
            op = "ASL A"; offset += 1
            instr = (instr_addr, op)
        elif byte == 0x4A:  # LSR A
            op = "LSR A"; offset += 1
            instr = (instr_addr, op)
        elif byte == 0xEB:  # XBA
            op = "XBA"; offset += 1
            instr = (instr_addr, op)
        elif byte == 0x18:  # CLC
            op = "CLC"; offset += 1
            instr = (instr_addr, op)
        elif byte == 0x38:  # SEC
            op = "SEC"; offset += 1
            instr = (instr_addr, op)
        elif byte == 0xD8:  # CLD
            op = "CLD"; offset += 1
            instr = (instr_addr, op)
        elif byte == 0xFB:  # XCE
            op = "XCE"; offset += 1
            instr = (instr_addr, op)
        elif byte == 0xEA:  # NOP
            op = "NOP"; offset += 1
            instr = (instr_addr, op)
        elif byte == 0x00:  # BRK
            op = f"BRK #{rom[offset+1]:02X}"; offset += 2
            instr = (instr_addr, op)
        elif byte == 0xDB:  # STP
            op = "STP"; offset += 1
            instr = (instr_addr, op)
        elif byte == 0xCB:  # WAI
            op = "WAI"; offset += 1
            instr = (instr_addr, op)
        elif byte == 0x80:  # BRA
            disp = rom[offset+1]
            if disp >= 128: disp -= 256
            target = base_addr + offset + 2 - a + disp
            op = f"BRA ${target:04X}"; offset += 2
            instr = (instr_addr, op)
        elif byte == 0x82:  # BRL
            disp = rom[offset+1] | (rom[offset+2]<<8)
            if disp >= 0x8000: disp -= 0x10000
            target = base_addr + offset + 3 - a + disp
            op = f"BRL ${target:04X}"; offset += 3
            instr = (instr_addr, op)
        elif byte == 0xF0:  # BEQ
            disp = rom[offset+1]
            if disp >= 128: disp -= 256
            target = base_addr + offset + 2 - a + disp
            op = f"BEQ ${target:04X}"; offset += 2
            instr = (instr_addr, op)
        elif byte == 0xD0:  # BNE
            disp = rom[offset+1]
            if disp >= 128: disp -= 256
            target = base_addr + offset + 2 - a + disp
            op = f"BNE ${target:04X}"; offset += 2
            instr = (instr_addr, op)
        elif byte == 0xB0:  # BCS
            disp = rom[offset+1]
            if disp >= 128: disp -= 256
            target = base_addr + offset + 2 - a + disp
            op = f"BCS ${target:04X}"; offset += 2
            instr = (instr_addr, op)
        elif byte == 0x90:  # BCC
            disp = rom[offset+1]
            if disp >= 128: disp -= 256
            target = base_addr + offset + 2 - a + disp
            op = f"BCC ${target:04X}"; offset += 2
            instr = (instr_addr, op)
        elif byte == 0x10:  # BPL
            disp = rom[offset+1]
            if disp >= 128: disp -= 256
            target = base_addr + offset + 2 - a + disp
            op = f"BPL ${target:04X}"; offset += 2
            instr = (instr_addr, op)
        elif byte == 0x30:  # BMI
            disp = rom[offset+1]
            if disp >= 128: disp -= 256
            target = base_addr + offset + 2 - a + disp
            op = f"BMI ${target:04X}"; offset += 2
            instr = (instr_addr, op)
        elif byte == 0xE0:  # CPX imm
            if x:
                val = rom[offset+1]; op = f"CPX #{val:02X}"; offset += 2
            else:
                val = rom[offset+1] | (rom[offset+2]<<8); op = f"CPX #{val:04X}"; offset += 3
            instr = (instr_addr, op)
        elif byte == 0xC0:  # CPY imm
            if x:
                val = rom[offset+1]; op = f"CPY #{val:02X}"; offset += 2
            else:
                val = rom[offset+1] | (rom[offset+2]<<8); op = f"CPY #{val:04X}"; offset += 3
            instr = (instr_addr, op)
        elif byte == 0xC9:  # CMP imm
            if m:
                val = rom[offset+1]; op = f"CMP #{val:02X}"; offset += 2
            else:
                val = rom[offset+1] | (rom[offset+2]<<8); op = f"CMP #{val:04X}"; offset += 3
            instr = (instr_addr, op)
        elif byte == 0xCD:  # CMP abs
            addr = rom[offset+1] | (rom[offset+2]<<8)
            op = f"CMP ${addr:04X}"; offset += 3
            instr = (instr_addr, op)
        elif byte == 0xC5:  # CMP dp
            op = f"CMP ${rom[offset+1]:02X}"; offset += 2
            instr = (instr_addr, op)
        elif byte == 0xDD:  # CMP a,X
            addr = rom[offset+1] | (rom[offset+2]<<8)
            op = f"CMP ${addr:04X},X"; offset += 3
            instr = (instr_addr, op)
        elif byte == 0x5D:  # CMP a,X (also)
            addr = rom[offset+1] | (rom[offset+2]<<8)
            op = f"CMP ${addr:04X},X"; offset += 3
            instr = (instr_addr, op)
        elif byte == 0xD9:  # CMP a,Y
            addr = rom[offset+1] | (rom[offset+2]<<8)
            op = f"CMP ${addr:04X},Y"; offset += 3
            instr = (instr_addr, op)
        elif byte == 0x29:  # AND imm
            if m:
                val = rom[offset+1]; op = f"AND #{val:02X}"; offset += 2
            else:
                val = rom[offset+1] | (rom[offset+2]<<8); op = f"AND #{val:04X}"; offset += 3
            instr = (instr_addr, op)
        elif byte == 0x25:  # AND dp
            op = f"AND ${rom[offset+1]:02X}"; offset += 2
            instr = (instr_addr, op)
        elif byte == 0x3D:  # AND a,X
            addr = rom[offset+1] | (rom[offset+2]<<8)
            op = f"AND ${addr:04X},X"; offset += 3
            instr = (instr_addr, op)
        elif byte == 0x09:  # ORA imm
            if m:
                val = rom[offset+1]; op = f"ORA #{val:02X}"; offset += 2
            else:
                val = rom[offset+1] | (rom[offset+2]<<8); op = f"ORA #{val:04X}"; offset += 3
            instr = (instr_addr, op)
        elif byte == 0x05:  # ORA dp
            op = f"ORA ${rom[offset+1]:02X}"; offset += 2
            instr = (instr_addr, op)
        elif byte == 0x0D:  # ORA abs
            addr = rom[offset+1] | (rom[offset+2]<<8)
            op = f"ORA ${addr:04X}"; offset += 3
            instr = (instr_addr, op)
        elif byte == 0x49:  # EOR imm
            if m:
                val = rom[offset+1]; op = f"EOR #{val:02X}"; offset += 2
            else:
                val = rom[offset+1] | (rom[offset+2]<<8); op = f"EOR #{val:04X}"; offset += 3
            instr = (instr_addr, op)
        elif byte == 0x65:  # ADC dp
            op = f"ADC ${rom[offset+1]:02X}"; offset += 2
            instr = (instr_addr, op)
        elif byte == 0x6D:  # ADC abs
            addr = rom[offset+1] | (rom[offset+2]<<8)
            op = f"ADC ${addr:04X}"; offset += 3
            instr = (instr_addr, op)
        elif byte == 0x69:  # ADC imm
            if m:
                val = rom[offset+1]; op = f"ADC #{val:02X}"; offset += 2
            else:
                val = rom[offset+1] | (rom[offset+2]<<8); op = f"ADC #{val:04X}"; offset += 3
            instr = (instr_addr, op)
        elif byte == 0xE5:  # SBC dp
            op = f"SBC ${rom[offset+1]:02X}"; offset += 2
            instr = (instr_addr, op)
        elif byte == 0xED:  # SBC abs
            addr = rom[offset+1] | (rom[offset+2]<<8)
            op = f"SBC ${addr:04X}"; offset += 3
            instr = (instr_addr, op)
        elif byte == 0xE9:  # SBC imm
            if m:
                val = rom[offset+1]; op = f"SBC #{val:02X}"; offset += 2
            else:
                val = rom[offset+1] | (rom[offset+2]<<8); op = f"SBC #{val:04X}"; offset += 3
            instr = (instr_addr, op)
        elif byte == 0xF6:  # INC a,X or SBC a,X? 
            addr = rom[offset+1] | (rom[offset+2]<<8)
            op = f"INC ${addr:04X},X"; offset += 3
            instr = (instr_addr, op)
        elif byte == 0xFE:
            addr = rom[offset+1] | (rom[offset+2]<<8)
            op = f"INC ${addr:04X},X"; offset += 3
            instr = (instr_addr, op)
        elif byte == 0x6C:  # JMP (abs)
            addr = rom[offset+1] | (rom[offset+2]<<8)
            op = f"JMP (${addr:04X})"; offset += 3
            instr = (instr_addr, op)
        elif byte == 0xAE:  # LDX abs
            addr = rom[offset+1] | (rom[offset+2]<<8)
            op = f"LDX ${addr:04X}"; offset += 3
            instr = (instr_addr, op)
        elif byte == 0xAC:  # LDY abs
            addr = rom[offset+1] | (rom[offset+2]<<8)
            op = f"LDY ${addr:04X}"; offset += 3
            instr = (instr_addr, op)
        elif byte == 0x9F:  # STA long,X
            addr = rom[offset+1] | (rom[offset+2]<<8) | (rom[offset+3]<<16)
            op = f"STA ${addr:06X},X"; offset += 4
            instr = (instr_addr, op)
        elif byte == 0xBF:  # LDA long,X
            addr = rom[offset+1] | (rom[offset+2]<<8) | (rom[offset+3]<<16)
            op = f"LDA ${addr:06X},X"; offset += 4
            instr = (instr_addr, op)
        elif byte == 0xBC:  # LDY a,X
            addr = rom[offset+1] | (rom[offset+2]<<8)
            op = f"LDY ${addr:04X},X"; offset += 3
            instr = (instr_addr, op)
        elif byte == 0xB9:  # LDA a,Y
            addr = rom[offset+1] | (rom[offset+2]<<8)
            op = f"LDA ${addr:04X},Y"; offset += 3
            instr = (instr_addr, op)
        elif byte == 0xB1:  # LDA (dp),Y
            op = f"LDA (${rom[offset+1]:02X}),Y"; offset += 2
            instr = (instr_addr, op)
        elif byte == 0xB7:  # LDA [dp],Y
            op = f"LDA [${rom[offset+1]:02X}],Y"; offset += 2
            instr = (instr_addr, op)
        elif byte == 0xA7:  # LDA [dp]
            op = f"LDA [${rom[offset+1]:02X}]"; offset += 2
            instr = (instr_addr, op)
        elif byte == 0xB2:  # LDA (dp)
            op = f"LDA (${rom[offset+1]:02X})"; offset += 2
            instr = (instr_addr, op)
        elif byte == 0x87:  # STA [dp]
            op = f"STA [${rom[offset+1]:02X}]"; offset += 2
            instr = (instr_addr, op)
        elif byte == 0x97:  # STA [dp],Y
            op = f"STA [${rom[offset+1]:02X}],Y"; offset += 2
            instr = (instr_addr, op)
        elif byte == 0x8E:  # STX abs
            addr = rom[offset+1] | (rom[offset+2]<<8)
            op = f"STX ${addr:04X}"; offset += 3
            instr = (instr_addr, op)
        elif byte == 0x8C:  # STY abs
            addr = rom[offset+1] | (rom[offset+2]<<8)
            op = f"STY ${addr:04X}"; offset += 3
            instr = (instr_addr, op)
        elif byte == 0x86:  # STX dp
            op = f"STX ${rom[offset+1]:02X}"; offset += 2
            instr = (instr_addr, op)
        elif byte == 0x84:  # STY dp
            op = f"STY ${rom[offset+1]:02X}"; offset += 2
            instr = (instr_addr, op)
        elif byte == 0xA3:  # LDA dp,S
            op = f"LDA ${rom[offset+1]:02X},S"; offset += 2
            instr = (instr_addr, op)
        elif byte == 0x83:  # STA dp,S
            op = f"STA ${rom[offset+1]:02X},S"; offset += 2
            instr = (instr_addr, op)
        elif byte == 0x89:  # BIT imm
            if m:
                op = f"BIT #{rom[offset+1]:02X}"; offset += 2
            else:
                val = rom[offset+1] | (rom[offset+2]<<8); op = f"BIT #{val:04X}"; offset += 3
            instr = (instr_addr, op)
        elif byte == 0x24:  # BIT dp
            op = f"BIT ${rom[offset+1]:02X}"; offset += 2
            instr = (instr_addr, op)
        elif byte == 0x2C:  # BIT abs
            addr = rom[offset+1] | (rom[offset+2]<<8)
            op = f"BIT ${addr:04X}"; offset += 3
            instr = (instr_addr, op)
        elif byte == 0x54:  # MVN
            src_b = rom[offset+1]; dst_b = rom[offset+2]
            op = f"MVN ${src_b:02X},${dst_b:02X}"; offset += 3
            instr = (instr_addr, op)
        elif byte == 0x44:  # MVP
            src_b = rom[offset+1]; dst_b = rom[offset+2]
            op = f"MVP ${src_b:02X},${dst_b:02X}"; offset += 3
            instr = (instr_addr, op)
        elif byte == 0x08:  # PHP
            op = "PHP"; offset += 1
            instr = (instr_addr, op)
        elif byte == 0x28:  # PLP
            op = "PLP"; offset += 1
            instr = (instr_addr, op)
        elif byte == 0x0D:  # ORA abs
            addr = rom[offset+1] | (rom[offset+2]<<8)
            op = f"ORA ${addr:04X}"; offset += 3
            instr = (instr_addr, op)
        elif byte == 0xDA:  # PHX
            op = "PHX"; offset += 1
            instr = (instr_addr, op)
        elif byte == 0x5A:  # PHY
            op = "PHY"; offset += 1
            instr = (instr_addr, op)
        elif byte == 0xDA:  # PHX
            op = "PHX"; offset += 1
            instr = (instr_addr, op)
        elif byte == 0x3E:  # AND a,X (or INC a,X depending on mode)
            addr = rom[offset+1] | (rom[offset+2]<<8)
            op = f"?AND ${addr:04X},X (or INC)"; offset += 3
            instr = (instr_addr, op)
        elif byte == 0x3C:  # BIT a,X
            addr = rom[offset+1] | (rom[offset+2]<<8)
            op = f"BIT ${addr:04X},X"; offset += 3
            instr = (instr_addr, op)
        elif byte == 0x9E:  # STZ a,X
            addr = rom[offset+1] | (rom[offset+2]<<8)
            op = f"STZ ${addr:04X},X"; offset += 3
            instr = (instr_addr, op)
        elif byte == 0x7C:  # JMP (a,X)
            addr = rom[offset+1] | (rom[offset+2]<<8)
            op = f"JMP (${addr:04X},X)"; offset += 3
            instr = (instr_addr, op)
        elif byte == 0xDC:  # JML [abs]
            addr = rom[offset+1] | (rom[offset+2]<<8)
            op = f"JML [${addr:04X}]"; offset += 3
            instr = (instr_addr, op)
        elif byte == 0x02:  # COP
            op = f"COP #{rom[offset+1]:02X}"; offset += 2
            instr = (instr_addr, op)
        else:
            op = f"?{byte:02X} (unknown)"
            instr = (instr_addr, op)
            offset += 1
        
        if instr:
            if instr[1].startswith('LDA #') or instr[1].startswith('STA $20') or instr[1].startswith('JMP $B0EE') or instr[1].startswith('JMP $B106'):
                output.append(f"  {instr[0]:04X}: {instr[1]}  <--")
            else:
                output.append(f"  {instr[0]:04X}: {instr[1]}")
    
    return '\n'.join(output)

full = open('tools/analysis/_handler_disasms.txt', 'w')

full.write("=== Event Handler $93B8 ===\n")
full.write(disasm_until(0x93B8, [0xB106, 0xB0EE, 0xFFFF], 500))

full.write("\n\n=== Event Handler $95B3 ===\n")
full.write(disasm_until(0x95B3, [0xB106, 0xB0EE, 0xFFFF], 500))

full.write("\n\n=== Event Handler $97C0 (via scan_jmps) ===\n")
full.write(disasm_until(0x97C0, [0xB106, 0xB0EE, 0xFFFF], 400))

full.close()
print("Saved to _handler_disasms.txt")
