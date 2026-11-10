"""Lint the blueprint note: map vs sections, edges stated at both ends, bindings vs columns, links, callouts."""
import re, sys, pathlib, collections
note = pathlib.Path(sys.argv[1]); vault = pathlib.Path(sys.argv[2]); wfdir = pathlib.Path(sys.argv[3])
s = note.read_text(encoding='utf-8'); lines = s.splitlines()
errs = []
# headings and sections
heads = []  # (level, text, line_index)
infence = False
for i, l in enumerate(lines):
    if l.startswith('```'): infence = not infence
    if not infence:
        m = re.match(r'^(#{1,6}) (.+)$', l)
        if m: heads.append((len(m.group(1)), m.group(2).strip(), i))
names = [h[1] for h in heads]
dups = [n for n, c in collections.Counter(names).items() if c > 1]
if dups: errs.append(f'duplicate headings: {dups}')
def section(name):
    idx = next(k for k, h in enumerate(heads) if h[1] == name)
    lvl, _, start = heads[idx]
    end = len(lines)
    for h in heads[idx + 1:]:
        if h[0] <= lvl: end = h[2]; break
    return lines[start:end]
def parent_h2(name):
    idx = next(k for k, h in enumerate(heads) if h[1] == name)
    for h in reversed(heads[:idx]):
        if h[0] == 2: return h[1]
# mermaid map
blocks = re.findall(r'```mermaid\n(.*?)```', s, flags=re.S)
mm = blocks[0]
lane = None; nodes = {}; lanes = {}
for l in mm.splitlines():
    t = l.strip()
    m = re.match(r'subgraph (\w+) \[(.+)\]', t)
    if m: lane = m.group(2); lanes[lane] = []; continue
    if t == 'end': lane = None; continue
    m = re.match(r'(\w+)\[\(?"?#?([^\]\)"]+)"?\)?\]$', t)
    if m and lane: nodes[m.group(1)] = (m.group(2), lane); lanes[lane].append(m.group(1))
edges = re.findall(r'^\s*(\w+) --> (\w+)\s*$', mm, flags=re.M)
print('lanes:', {k: len(v) for k, v in lanes.items()}, 'edges:', len(edges))
for nid, (label, ln) in nodes.items():
    if label not in names: errs.append(f'node {nid} label "{label}" has no heading'); continue
    if parent_h2(label) != ln: errs.append(f'node "{label}" is in lane {ln} but under H2 {parent_h2(label)}')
for h in heads:
    if h[0] == 3 and parent_h2(h[1]) in lanes and h[1] not in [v[0] for v in nodes.values()]:
        errs.append(f'section "{h[1]}" is not on the map')
def field(name, key):
    for l in section(name):
        if l.startswith(f'- **{key}**'): return l
    return ''
for a, b in edges:
    if a not in nodes or b not in nodes: errs.append(f'edge {a}->{b} uses unknown node'); continue
    (la, lna), (lb, lnb) = nodes[a], nodes[b]
    if lna == 'Pipeline' and lnb == 'Tables':
        if f'[[#{lb}]]' not in field(la, 'Writes'): errs.append(f'"{la}" Writes does not name "{lb}"')
        if f'[[#{la}]]' not in field(lb, 'Written by'): errs.append(f'"{lb}" Written by does not name "{la}"')
    else:
        key = 'Order' if False else 'Reads'
        if f'[[#{la}]]' not in field(lb, 'Reads'): errs.append(f'"{lb}" Reads does not name "{la}"')
        if f'[[#{lb}]]' not in field(la, 'Read by'): errs.append(f'"{la}" Read by does not name "{lb}"')
# columns per table section
def columns(name):
    cols = []
    for l in section(name):
        m = re.match(r'^\| `(\w+)` \|', l)
        if m: cols.append(m.group(1))
    return cols
callouts = {}
for nid in lanes['UI']:
    scr = nodes[nid][0]
    reads = re.findall(r'\[\[#([^\]]+)\]\]', field(scr, 'Reads'))
    assert len(reads) == 1, (scr, reads)
    cols = set(columns(reads[0]))
    nums = []
    for l in section(scr):
        m = re.match(r'^\| (\d+) \| ([^|]+) \| ([^|]+) \| ([^|]*) \|', l)
        if m:
            nums.append(int(m.group(1)))
            for c in re.findall(r'`(\w+)`', m.group(4)):
                if c not in cols: errs.append(f'{scr} element {m.group(1)}: column `{c}` not in {reads[0]}')
    emb = re.findall(r'!\[\[([^\]]+\.svg)\]\]', '\n'.join(section(scr)))
    if len(emb) != 1: errs.append(f'{scr}: expected one wireframe embed, got {emb}'); continue
    f = wfdir / emb[0]
    if not f.exists(): errs.append(f'{scr}: wireframe file missing {emb[0]}'); continue
    svg = f.read_text()
    cn = sorted(int(x) for x in re.findall(r'fill="#c2410c"[^>]*/>\n<text [^>]*>(\d+)</text>', svg))
    if cn != sorted(nums): errs.append(f'{scr}: callouts {cn} vs element rows {sorted(nums)}')
    print(f'{scr}: reads {reads[0]} ({len(cols)} cols), elements {nums}, callouts {cn}')
# links
for tgt in set(re.findall(r'!?\[\[([^\]]+)\]\]', s)):
    t = tgt.split('|')[0]
    if t.startswith('#'):
        if t[1:] not in names: errs.append(f'heading link not found: {t}')
        continue
    base = t.split('#')[0]
    fn = base if re.search(r'\.(canvas|svg|md)$', base) else base + '.md'
    planned = {'AWS_Batch_Pipeline_Blueprint.canvas'} | {p.name for p in wfdir.glob('*.svg')}
    if fn in planned: continue
    hits = [p for p in vault.rglob(fn) if '.obsidian' not in p.parts]
    if len(hits) != 1: errs.append(f'link [[{t}]] resolves to {len(hits)} files')
# characters and bullets
for i, l in enumerate(lines, 1):
    if re.search('[—–]', l): errs.append(f'line {i}: em or en dash')
    if re.search(r'[^\x00-\x7F]', l): errs.append(f'line {i}: non-ASCII character')
    if re.match(r'^ +- ', l): errs.append(f'line {i}: nested bullet uses spaces')
    if l != l.rstrip(): errs.append(f'line {i}: trailing whitespace')
print('ERRORS' if errs else 'LINT OK', *errs, sep='\n')
sys.exit(1 if errs else 0)
