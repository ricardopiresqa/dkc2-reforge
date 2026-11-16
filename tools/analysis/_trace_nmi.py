rom = open('roms/dkc2.sfc', 'rb').read()
def r(b,a): return (b&0x3F)*0x10000+a

# Tracing NMI handler from $80:F3C1
print("=== NMI Handler at $80:F3C1 ===")
a = r(0x80, 0xF3C1)

m_flag = False  # 0=16bit, 1=8bit
x_flag = False
    
i = 0
offset = a
while i < 256:
    if offset >= len(rom):
        print("  END OF ROM")
        break
    byte = rom[offset]
    
    if byte == 0x5C:  # JML long
        dst = rom[offset+1] | (rom[offset+2]<<8) | (rom[offset+3]<<16)
        print(f"  $80:{0xF3C1+i:04X}: JML ${dst:06X}")
        offset += 4
        i += 4
        continue
    elif byte == 0x22:  # JSL long
        dst = rom[offset+1] | (rom[offset+2]<<8) | (rom[offset+3]<<16)
        print(f"  $80:{0xF3C1+i:04X}: JSL ${dst:06X}")
        offset += 4
        i += 4
        continue
    elif byte == 0x60:  # RTS
        print(f"  $80:{0xF3C1+i:04X}: RTS")
        break
    elif byte == 0x6B:  # RTL
        print(f"  $80:{0xF3C1+i:04X}: RTL")
        break
    elif byte == 0x40:  # RTI
        print(f"  $80:{0xF3C1+i:04X}: RTI")
        break
    elif byte == 0x0B:  # PHD
        print(f"  $80:{0xF3C1+i:04X}: PHD")
        offset += 1; i += 1
        continue
    elif byte == 0x48:  # PHA
        print(f"  $80:{0xF3C1+i:04X}: PHA")
        offset += 1; i += 1
        continue
    elif byte == 0xDA:  # PHX
        print(f"  $80:{0xF3C1+i:04X}: PHX")
        offset += 1; i += 1
        continue
    elif byte == 0x5A:  # PHY
        print(f"  $80:{0xF3C1+i:04X}: PHY")
        offset += 1; i += 1
        continue
    elif byte == 0x8B:  # PHB
        print(f"  $80:{0xF3C1+i:04X}: PHB")
        offset += 1; i += 1
        continue
    elif byte == 0x2B:  # PLD
        print(f"  $80:{0xF3C1+i:04X}: PLD")
        offset += 1; i += 1
        continue
    elif byte == 0x68:  # PLA
        print(f"  $80:{0xF3C1+i:04X}: PLA")
        offset += 1; i += 1
        continue
    elif byte == 0xFA:  # PLX
        print(f"  $80:{0xF3C1+i:04X}: PLX")
        offset += 1; i += 1
        continue
    elif byte == 0x7A:  # PLY
        print(f"  $80:{0xF3C1+i:04X}: PLY")
        offset += 1; i += 1
        continue
    elif byte == 0xAB:  # PLB
        print(f"  $80:{0xF3C1+i:04X}: PLB")
        offset += 1; i += 1
        continue
    elif byte == 0x9C:  # STZ abs
        addr = rom[offset+1] | (rom[offset+2]<<8)
        print(f"  $80:{0xF3C1+i:04X}: STZ ${addr:04X}")
        offset += 3; i += 3
        continue
    elif byte == 0x64:  # STZ dp
        addr = rom[offset+1]
        print(f"  $80:{0xF3C1+i:04X}: STZ ${addr:02X}")
        offset += 2; i += 2
        continue
    elif byte == 0xC0:  # CPY imm
        val = rom[offset+1] | (rom[offset+2]<<8)
        print(f"  $80:{0xF3C1+i:04X}: CPY #{val:04X}")
        offset += 3; i += 3; continue
    elif byte == 0xC2:  # REP
        val = rom[offset+1]
        print(f"  $80:{0xF3C1+i:04X}: REP #{val:02X}")
        offset += 2; i += 2
        if val & 0x10: m_flag = False
        if val & 0x20: x_flag = False
        continue
    elif byte == 0xE2:  # SEP
        val = rom[offset+1]
        print(f"  $80:{0xF3C1+i:04X}: SEP #{val:02X}")
        offset += 2; i += 2
        if val & 0x10: m_flag = True
        if val & 0x20: x_flag = True
        continue
    elif byte == 0xA9:  # LDA immediate
        if m_flag:
            print(f"  $80:{0xF3C1+i:04X}: LDA #{rom[offset+1]:02X}")
            offset += 2; i += 2
        else:
            val = rom[offset+1] | (rom[offset+2]<<8)
            print(f"  $80:{0xF3C1+i:04X}: LDA #{val:04X}")
            offset += 3; i += 3
        continue
    elif byte == 0xA2:  # LDX immediate
        if x_flag:
            print(f"  $80:{0xF3C1+i:04X}: LDX #{rom[offset+1]:02X}")
            offset += 2; i += 2
        else:
            val = rom[offset+1] | (rom[offset+2]<<8)
            print(f"  $80:{0xF3C1+i:04X}: LDX #{val:04X}")
            offset += 3; i += 3
        continue
    elif byte == 0xA0:  # LDY immediate
        if x_flag:
            print(f"  $80:{0xF3C1+i:04X}: LDY #{rom[offset+1]:02X}")
            offset += 2; i += 2
        else:
            val = rom[offset+1] | (rom[offset+2]<<8)
            print(f"  $80:{0xF3C1+i:04X}: LDY #{val:04X}")
            offset += 3; i += 3
        continue
    elif byte == 0xE8:  # INX
        print(f"  $80:{0xF3C1+i:04X}: INX")
        offset += 1; i += 1; continue
    elif byte == 0x1A:  # INC A
        print(f"  $80:{0xF3C1+i:04X}: INC A")
        offset += 1; i += 1; continue
    elif byte == 0xAD:  # LDA abs
        addr = rom[offset+1] | (rom[offset+2]<<8)
        print(f"  $80:{0xF3C1+i:04X}: LDA ${addr:04X}")
        offset += 3; i += 3; continue
    elif byte == 0xAF:  # LDA long
        addr = rom[offset+1] | (rom[offset+2]<<8) | (rom[offset+3]<<16)
        print(f"  $80:{0xF3C1+i:04X}: LDA ${addr:06X}")
        offset += 4; i += 4; continue
    elif byte == 0x8D:  # STA abs
        addr = rom[offset+1] | (rom[offset+2]<<8)
        print(f"  $80:{0xF3C1+i:04X}: STA ${addr:04X}")
        offset += 3; i += 3; continue
    elif byte == 0x8F:  # STA long
        addr = rom[offset+1] | (rom[offset+2]<<8) | (rom[offset+3]<<16)
        print(f"  $80:{0xF3C1+i:04X}: STA ${addr:06X}")
        offset += 4; i += 4; continue
    elif byte == 0x6C:  # JMP (abs)
        addr = rom[offset+1] | (rom[offset+2]<<8)
        print(f"  $80:{0xF3C1+i:04X}: JMP (${addr:04X})")
        offset += 3; i += 3; continue
    elif byte == 0x4C:  # JMP abs
        addr = rom[offset+1] | (rom[offset+2]<<8)
        print(f"  $80:{0xF3C1+i:04X}: JMP ${addr:04X}")
        break
    elif byte == 0x80:  # BRA
        disp = rom[offset+1]
        if disp >= 128: disp -= 256
        target = offset + 2 + disp - a + 0xF3C1
        print(f"  $80:{0xF3C1+i:04X}: BRA ${target:04X}")
        offset += 2; i += 2; continue
    elif byte == 0xF0:  # BEQ
        disp = rom[offset+1]
        if disp >= 128: disp -= 256
        target = offset + 2 + disp - a + 0xF3C1
        print(f"  $80:{0xF3C1+i:04X}: BEQ ${target:04X}")
        offset += 2; i += 2; continue
    elif byte == 0xD0:  # BNE
        disp = rom[offset+1]
        if disp >= 128: disp -= 256
        target = offset + 2 + disp - a + 0xF3C1
        print(f"  $80:{0xF3C1+i:04X}: BNE ${target:04X}")
        offset += 2; i += 2; continue
    elif byte == 0x90:  # BCC
        disp = rom[offset+1]
        if disp >= 128: disp -= 256
        target = offset + 2 + disp - a + 0xF3C1
        print(f"  $80:{0xF3C1+i:04X}: BCC ${target:04X}")
        offset += 2; i += 2; continue
    elif byte == 0xA5:  # LDA dp
        print(f"  $80:{0xF3C1+i:04X}: LDA ${rom[offset+1]:02X}")
        offset += 2; i += 2; continue
    elif byte == 0x85:  # STA dp
        print(f"  $80:{0xF3C1+i:04X}: STA ${rom[offset+1]:02X}")
        offset += 2; i += 2; continue
    elif byte == 0xE6:  # INC dp
        print(f"  $80:{0xF3C1+i:04X}: INC ${rom[offset+1]:02X}")
        offset += 2; i += 2; continue
    elif byte == 0xC6:  # DEC dp
        print(f"  $80:{0xF3C1+i:04X}: DEC ${rom[offset+1]:02X}")
        offset += 2; i += 2; continue
    elif byte == 0x3A:  # DEC A
        print(f"  $80:{0xF3C1+i:04X}: DEC A")
        offset += 1; i += 1; continue
    elif byte == 0xCA:  # DEX
        print(f"  $80:{0xF3C1+i:04X}: DEX")
        offset += 1; i += 1; continue
    elif byte == 0x88:  # DEY
        print(f"  $80:{0xF3C1+i:04X}: DEY")
        offset += 1; i += 1; continue
    elif byte == 0x5B:  # TCD
        print(f"  $80:{0xF3C1+i:04X}: TCD")
        offset += 1; i += 1; continue
    elif byte == 0x7B:  # TDC
        print(f"  $80:{0xF3C1+i:04X}: TDC")
        offset += 1; i += 1; continue
    elif byte == 0xAA:  # TAX
        print(f"  $80:{0xF3C1+i:04X}: TAX")
        offset += 1; i += 1; continue
    elif byte == 0xA8:  # TAY
        print(f"  $80:{0xF3C1+i:04X}: TAY")
        offset += 1; i += 1; continue
    elif byte == 0x8A:  # TXA
        print(f"  $80:{0xF3C1+i:04X}: TXA")
        offset += 1; i += 1; continue
    elif byte == 0x9A:  # TXS
        print(f"  $80:{0xF3C1+i:04X}: TXS")
        offset += 1; i += 1; continue
    elif byte == 0xBA:  # TSX
        print(f"  $80:{0xF3C1+i:04X}: TSX")
        offset += 1; i += 1; continue
    elif byte == 0x98:  # TYA
        print(f"  $80:{0xF3C1+i:04X}: TYA")
        offset += 1; i += 1; continue
    elif byte == 0x9B:  # TXY
        print(f"  $80:{0xF3C1+i:04X}: TXY")
        offset += 1; i += 1; continue
    elif byte == 0xBB:  # TYX
        print(f"  $80:{0xF3C1+i:04X}: TYX")
        offset += 1; i += 1; continue
    elif byte == 0x1B:  # TCS
        print(f"  $80:{0xF3C1+i:04X}: TCS")
        offset += 1; i += 1; continue
    elif byte == 0x21:  # AND dp,X
        print(f"  $80:{0xF3C1+i:04X}: AND ${rom[offset+1]:02X},X")
        offset += 2; i += 2; continue
    elif byte == 0x3D:  # AND a,X
        addr = rom[offset+1] | (rom[offset+2]<<8)
        print(f"  $80:{0xF3C1+i:04X}: AND ${addr:04X},X")
        offset += 3; i += 3; continue
    elif byte == 0x29:  # AND imm
        if m_flag:
            print(f"  $80:{0xF3C1+i:04X}: AND #{rom[offset+1]:02X}")
            offset += 2; i += 2
        else:
            val = rom[offset+1] | (rom[offset+2]<<8)
            print(f"  $80:{0xF3C1+i:04X}: AND #{val:04X}")
            offset += 3; i += 3
        continue
    elif byte == 0x09:  # ORA imm
        if m_flag:
            print(f"  $80:{0xF3C1+i:04X}: ORA #{rom[offset+1]:02X}")
            offset += 2; i += 2
        else:
            val = rom[offset+1] | (rom[offset+2]<<8)
            print(f"  $80:{0xF3C1+i:04X}: ORA #{val:04X}")
            offset += 3; i += 3
        continue
    elif byte == 0x18:  # CLC
        print(f"  $80:{0xF3C1+i:04X}: CLC")
        offset += 1; i += 1; continue
    elif byte == 0x38:  # SEC
        print(f"  $80:{0xF3C1+i:04X}: SEC")
        offset += 1; i += 1; continue
    elif byte == 0xFB:  # XCE
        print(f"  $80:{0xF3C1+i:04X}: XCE")
        offset += 1; i += 1; continue
    elif byte == 0x02:  # COP
        print(f"  $80:{0xF3C1+i:04X}: COP #{rom[offset+1]:02X}")
        offset += 2; i += 2; continue
    elif byte == 0x00:  # BRK
        print(f"  $80:{0xF3C1+i:04X}: BRK #{rom[offset+1]:02X}")
        offset += 2; i += 2; continue
    elif byte == 0xEA:  # NOP
        print(f"  $80:{0xF3C1+i:04X}: NOP")
        offset += 1; i += 1; continue
    elif byte == 0x4B:  # PHK
        print(f"  $80:{0xF3C1+i:04X}: PHK")
        offset += 1; i += 1; continue
    elif byte == 0xAB:  # PLB
        print(f"  $80:{0xF3C1+i:04X}: PLB")
        offset += 1; i += 1; continue
    elif byte == 0x0A:  # ASL A
        print(f"  $80:{0xF3C1+i:04X}: ASL A")
        offset += 1; i += 1; continue
    elif byte == 0x4A:  # LSR A
        print(f"  $80:{0xF3C1+i:04X}: LSR A")
        offset += 1; i += 1; continue
    elif byte == 0x6D:  # ADC abs
        addr = rom[offset+1] | (rom[offset+2]<<8)
        print(f"  $80:{0xF3C1+i:04X}: ADC ${addr:04X}")
        offset += 3; i += 3; continue
    elif byte == 0xED:  # SBC abs
        addr = rom[offset+1] | (rom[offset+2]<<8)
        print(f"  $80:{0xF3C1+i:04X}: SBC ${addr:04X}")
        offset += 3; i += 3; continue
    elif byte == 0x65:  # ADC dp
        print(f"  $80:{0xF3C1+i:04X}: ADC ${rom[offset+1]:02X}")
        offset += 2; i += 2; continue
    elif byte == 0xE5:  # SBC dp
        print(f"  $80:{0xF3C1+i:04X}: SBC ${rom[offset+1]:02X}")
        offset += 2; i += 2; continue
    elif byte == 0x69:  # ADC imm
        if m_flag:
            print(f"  $80:{0xF3C1+i:04X}: ADC #{rom[offset+1]:02X}")
            offset += 2; i += 2
        else:
            val = rom[offset+1] | (rom[offset+2]<<8)
            print(f"  $80:{0xF3C1+i:04X}: ADC #{val:04X}")
            offset += 3; i += 3
        continue
    elif byte == 0xE9:  # SBC imm
        if m_flag:
            print(f"  $80:{0xF3C1+i:04X}: SBC #{rom[offset+1]:02X}")
            offset += 2; i += 2
        else:
            val = rom[offset+1] | (rom[offset+2]<<8)
            print(f"  $80:{0xF3C1+i:04X}: SBC #{val:04X}")
            offset += 3; i += 3
        continue
    elif byte == 0x5D:  # CMP a,X
        addr = rom[offset+1] | (rom[offset+2]<<8)
        print(f"  $80:{0xF3C1+i:04X}: CMP ${addr:04X},X")
        offset += 3; i += 3; continue
    elif byte == 0xDD:  # CMP a,X
        addr = rom[offset+1] | (rom[offset+2]<<8)
        print(f"  $80:{0xF3C1+i:04X}: CMP ${addr:04X},X")
        offset += 3; i += 3; continue
    elif byte == 0xFE:  # INC abs,X
        addr = rom[offset+1] | (rom[offset+2]<<8)
        print(f"  $80:{0xF3C1+i:04X}: INC ${addr:04X},X")
        offset += 3; i += 3; continue
    elif byte == 0xCE:  # DEC abs
        addr = rom[offset+1] | (rom[offset+2]<<8)
        print(f"  $80:{0xF3C1+i:04X}: DEC ${addr:04X}")
        offset += 3; i += 3; continue
    elif byte == 0x9E:  # STZ abs,X
        addr = rom[offset+1] | (rom[offset+2]<<8)
        print(f"  $80:{0xF3C1+i:04X}: STZ ${addr:04X},X")
        offset += 3; i += 3; continue
    elif byte == 0xC9:  # CMP imm
        if m_flag:
            print(f"  $80:{0xF3C1+i:04X}: CMP #{rom[offset+1]:02X}")
            offset += 2; i += 2
        else:
            val = rom[offset+1] | (rom[offset+2]<<8)
            print(f"  $80:{0xF3C1+i:04X}: CMP #{val:04X}")
            offset += 3; i += 3
        continue
    elif byte == 0xE0:  # CPX imm
        if x_flag:
            print(f"  $80:{0xF3C1+i:04X}: CPX #{rom[offset+1]:02X}")
            offset += 2; i += 2
        else:
            val = rom[offset+1] | (rom[offset+2]<<8)
            print(f"  $80:{0xF3C1+i:04X}: CPX #{val:04X}")
            offset += 3; i += 3
        continue
    elif byte == 0x10:  # BPL
        disp = rom[offset+1]
        if disp >= 128: disp -= 256
        target = offset + 2 + disp - a + 0xF3C1
        print(f"  $80:{0xF3C1+i:04X}: BPL ${target:04X}")
        offset += 2; i += 2; continue
    elif byte == 0x30:  # BMI
        disp = rom[offset+1]
        if disp >= 128: disp -= 256
        target = offset + 2 + disp - a + 0xF3C1
        print(f"  $80:{0xF3C1+i:04X}: BMI ${target:04X}")
        offset += 2; i += 2; continue
    elif byte == 0x9B:  # STY abs (actually TXY in 65816)
        # Actually this conflicts with TXY. Let me handle carefully.
        # 9B is TXY in native mode (not in emulation)
        # BUT there might not be any STY abs at 0x9B...
        print(f"  $80:{0xF3C1+i:04X}: TXY")
        offset += 1; i += 1; continue
    elif byte == 0x8C:  # STY abs
        addr = rom[offset+1] | (rom[offset+2]<<8)
        print(f"  $80:{0xF3C1+i:04X}: STY ${addr:04X}")
        offset += 3; i += 3; continue
    elif byte == 0x9C:  # STZ abs (handled above)
        pass
    elif byte == 0x3A:  # DEC A (handled above)
        pass
    elif byte == 0xD8:  # CLD
        print(f"  $80:{0xF3C1+i:04X}: CLD")
        offset += 1; i += 1; continue
    elif byte == 0xDB:  # STP
        print(f"  $80:{0xF3C1+i:04X}: STP")
        break
    else:
        print(f"  $80:{0xF3C1+i:04X}: ?{byte:02X}")
        break

    offset += 1
    i += 1
