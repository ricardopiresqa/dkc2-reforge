f = open('tools/analysis/_disasm_all.txt')
data = f.read()
f.close()
sections = data.split('============================================================')
for i, s in enumerate(sections):
    s = s.strip()
    if not s:
        continue
    print(f'Section {i}: first 80 chars = {repr(s[:80])}')
    print(f'  Starts with $80: {s[0:3] == "$80"!r}')
