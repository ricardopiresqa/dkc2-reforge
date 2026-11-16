f = open('tools/analysis/_disasm_all.txt')
data = f.read()
f.close()
sections = data.split('============================================================')
for s in sections:
    s = s.strip()
    if s and s[0:3] == '$80':
        lines = s.split('\n')
        name = lines[0].strip()
        body_lines = [l for l in lines[1:] if l.strip()]
        print(f'{name}: {len(body_lines)} lines')
