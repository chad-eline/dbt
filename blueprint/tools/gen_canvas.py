"""Generate the laned canvas companion for the blueprint note, validate it, and write a box preview."""
import json, re, sys, pathlib, html
note_path = pathlib.Path(sys.argv[1]); wfdir = pathlib.Path(sys.argv[2]); out = pathlib.Path(sys.argv[3]); preview = pathlib.Path(sys.argv[4])
D = 'blueprint/'
NOTE = D + 'AWS_Batch_Pipeline_Blueprint.md'
WF = D + 'wireframes/AWS_Batch_Blueprint_wf_{}.svg'
CW, PITCH = 440, 480
c = lambda i: i * PITCH
TOTAL_W = 6 * PITCH + CW
nodes, edges = [], []
def group(id, x, y, w, h, label, color=None):
    n = {'id': id, 'type': 'group', 'x': x, 'y': y, 'width': w, 'height': h, 'label': label}
    if color: n['color'] = color
    nodes.append(n)
def text(id, x, y, w, h, t, color=None):
    n = {'id': id, 'type': 'text', 'x': x, 'y': y, 'width': w, 'height': h, 'text': t}
    if color: n['color'] = color
    nodes.append(n)
def sect(id, x, y, w, h, heading):
    nodes.append({'id': id, 'type': 'file', 'file': NOTE, 'subpath': '#' + heading, 'x': x, 'y': y, 'width': w, 'height': h})
def image(id, x, y, w, h, name):
    nodes.append({'id': id, 'type': 'file', 'file': WF.format(name), 'x': x, 'y': y, 'width': w, 'height': h})
def edge(id, a, aside, b, bside, label=None):
    e = {'id': id, 'fromNode': a, 'fromSide': aside, 'toNode': b, 'toSide': bside}
    if label: e['label'] = label
    edges.append(e)

# lanes (groups first so they sit behind the cards)
UI_Y, UI_H = 0, 420
TB_Y, TB_H = 510, 540
PL_Y, PL_H = 1140, 340
group('lane_ui', -40, UI_Y, TOTAL_W + 80, UI_H, 'UI', '6')
group('lane_tables', -40, TB_Y, TOTAL_W + 80, TB_H, 'Tables', '5')
group('lane_pipeline', -40, PL_Y, TOTAL_W + 80, PL_H, 'Pipeline', '2')
group('grp_raw_positions', c(2) - 16, TB_Y + 44, PITCH + CW + 32, 472, 'raw_positions (bronze)')

# header cards
text('title', 0, -190, 920, 130, '# AWS Batch Pipeline Blueprint\nBoard view of [[AWS_Batch_Pipeline_Blueprint]]. Pipeline does the work, Tables hold the results, UI shows them.')
text('legend', 960, -190, 1400, 130, '**How to read**\n- Step to table: writes. Table to step or screen: reads.\n- Table and pipeline cards are live views of sections in the note. Edit the note, not the card.\n- Wireframe callout numbers match the Elements table in each screen section.')

# UI lane: link card over wireframe image
for key, col, heading, wf in (('run_monitor', 0, 'Run monitor', 'run_monitor'), ('holdings_grid', 5, 'Holdings grid', 'holdings_grid'), ('break_report', 6, 'Break report', 'break_report')):
    text(f'ui_{key}_link', c(col), UI_Y + 30, CW, 64, f'**{heading}**\nSpec and element bindings: [[AWS_Batch_Pipeline_Blueprint#{heading}]]')
    image(f'ui_{key}', c(col), UI_Y + 110, CW, 280, wf)

# Tables lane
TY, TH = TB_Y + 60, 440
for key, col in (('ops_pipeline_runs', 0), ('raw_custodian_positions', 2), ('raw_abor_positions', 3), ('stg_positions', 4), ('fct_holdings', 5), ('fct_position_breaks', 6)):
    sect(f't_{key}', c(col), TY, CW, TH, key)

# Pipeline lane
PY, PH = PL_Y + 30, 280
sect('p_orchestrate', c(0), PY, CW, PH, 'Orchestrate')
sect('p_sources', c(1), PY, CW, PH, 'Sources')
sect('p_ingest', c(2), PY, PITCH + CW, PH, 'Ingest and validate')
sect('p_stage', c(4), PY, CW, PH, 'Stage positions')
sect('p_build', c(5), PY, PITCH + CW, PH, 'Build marts')

# edges
edge('e_orch_ops', 'p_orchestrate', 'top', 't_ops_pipeline_runs', 'bottom', 'writes')
edge('e_ops_ui', 't_ops_pipeline_runs', 'top', 'ui_run_monitor', 'bottom', 'reads')
edge('e_src_ing', 'p_sources', 'right', 'p_ingest', 'left')
edge('e_ing_raw', 'p_ingest', 'top', 'grp_raw_positions', 'bottom', 'writes')
edge('e_raw_stage', 'grp_raw_positions', 'bottom', 'p_stage', 'top', 'reads')
edge('e_stage_stg', 'p_stage', 'top', 't_stg_positions', 'bottom', 'writes')
edge('e_stg_build', 't_stg_positions', 'bottom', 'p_build', 'top', 'reads')
edge('e_build_hold', 'p_build', 'top', 't_fct_holdings', 'bottom', 'writes')
edge('e_build_brk', 'p_build', 'top', 't_fct_position_breaks', 'bottom', 'writes')
edge('e_hold_ui', 't_fct_holdings', 'top', 'ui_holdings_grid', 'bottom', 'reads')
edge('e_brk_ui', 't_fct_position_breaks', 'top', 'ui_break_report', 'bottom', 'reads')

# ---- validation
errs = []
note = note_path.read_text(encoding='utf-8')
heads = set(re.findall(r'^#{1,6} (.+)$', re.sub(r'```.*?```', '', note, flags=re.S), flags=re.M))
ids = [n['id'] for n in nodes] + [e['id'] for e in edges]
if len(ids) != len(set(ids)): errs.append('duplicate ids')
byid = {n['id']: n for n in nodes}
for e in edges:
    for k in ('fromNode', 'toNode'):
        if e[k] not in byid: errs.append(f'edge {e["id"]} references missing node {e[k]}')
for n in nodes:
    if n['type'] == 'file':
        if n['file'] == NOTE:
            if n['subpath'][1:] not in heads: errs.append(f'{n["id"]}: heading {n["subpath"]} not in note')
        elif not (wfdir / pathlib.Path(n['file']).name).exists():
            errs.append(f'{n["id"]}: file missing {n["file"]}')
    for k in ('x', 'y', 'width', 'height'):
        if not isinstance(n[k], int): errs.append(f'{n["id"]}: {k} not an integer')
def rect(n): return (n['x'], n['y'], n['x'] + n['width'], n['y'] + n['height'])
def overlap(a, b): return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]
def inside(a, b): return a[0] >= b[0] and a[1] >= b[1] and a[2] <= b[2] and a[3] <= b[3]
cards = [n for n in nodes if n['type'] != 'group']
for i, a in enumerate(cards):
    for b in cards[i + 1:]:
        if overlap(rect(a), rect(b)): errs.append(f'cards overlap: {a["id"]} and {b["id"]}')
lane_of = {'ui_': 'lane_ui', 't_': 'lane_tables', 'p_': 'lane_pipeline'}
for n in cards:
    for pre, lane in lane_of.items():
        if n['id'].startswith(pre) and not inside(rect(n), rect(byid[lane])): errs.append(f'{n["id"]} not inside {lane}')
    for lane in lane_of.values():
        if not any(n['id'].startswith(p) for p, l in lane_of.items() if l == lane) and overlap(rect(n), rect(byid[lane])): errs.append(f'{n["id"]} intrudes on {lane}')
if not inside(rect(byid['grp_raw_positions']), rect(byid['lane_tables'])): errs.append('raw group not inside tables lane')
for k in ('t_raw_custodian_positions', 't_raw_abor_positions'):
    if not inside(rect(byid[k]), rect(byid['grp_raw_positions'])): errs.append(f'{k} not inside raw group')
blob = json.dumps({'nodes': nodes, 'edges': edges}, ensure_ascii=False)
if re.search('[—–]', blob) or re.search(r'[^\x00-\x7F]', blob): errs.append('non-ASCII or dash in canvas text')
print('nodes', len(nodes), 'edges', len(edges))
print('ERRORS' if errs else 'CANVAS OK', *errs, sep='\n')
if errs: sys.exit(1)

# ---- write in Obsidian's layout: one node per line, tab indented
def dump(items): return ',\n'.join('\t\t' + json.dumps(i, ensure_ascii=False, separators=(',', ':')) for i in items)
out.write_text('{\n\t"nodes":[\n' + dump(nodes) + '\n\t],\n\t"edges":[\n' + dump(edges) + '\n\t]\n}', encoding='utf-8')
json.loads(out.read_text())

# ---- box preview (straight edges, labels only) for a geometry eyeball
minx = min(n['x'] for n in nodes) - 40; miny = min(n['y'] for n in nodes) - 60
maxx = max(n['x'] + n['width'] for n in nodes) + 40; maxy = max(n['y'] + n['height'] for n in nodes) + 40
col = {'6': '#f3e8ff', '5': '#e6fbf7', '2': '#fff1e0'}
o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{minx} {miny} {maxx-minx} {maxy-miny}" width="1700" font-family="Segoe UI, Arial, sans-serif">', f'<rect x="{minx}" y="{miny}" width="{maxx-minx}" height="{maxy-miny}" fill="#fff"/>']
def anchor(n, side):
    x, y, w, h = n['x'], n['y'], n['width'], n['height']
    return {'top': (x + w / 2, y), 'bottom': (x + w / 2, y + h), 'left': (x, y + h / 2), 'right': (x + w, y + h / 2)}[side]
for n in nodes:
    if n['type'] == 'group':
        o.append(f'<rect x="{n["x"]}" y="{n["y"]}" width="{n["width"]}" height="{n["height"]}" fill="{col.get(n.get("color"), "none")}" stroke="#888" stroke-width="3" rx="12"/>')
        o.append(f'<text x="{n["x"]+6}" y="{n["y"]-12}" font-size="34" font-weight="700" fill="#444">{html.escape(n["label"])}</text>')
for n in nodes:
    if n['type'] == 'group': continue
    lab = n.get('subpath', '') or pathlib.Path(n.get('file', '')).name or n.get('text', '').split('\n')[0]
    fill = '#ffffff' if n['type'] == 'file' else '#f1f1f1'
    o.append(f'<rect x="{n["x"]}" y="{n["y"]}" width="{n["width"]}" height="{n["height"]}" fill="{fill}" stroke="#333" stroke-width="3" rx="8"/>')
    o.append(f'<text x="{n["x"]+14}" y="{n["y"]+44}" font-size="28" fill="#222">{html.escape(lab[:30])}</text>')
for e in edges:
    (x1, y1), (x2, y2) = anchor(byid[e['fromNode']], e['fromSide']), anchor(byid[e['toNode']], e['toSide'])
    o.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#c2410c" stroke-width="4"/>')
    o.append(f'<circle cx="{x2}" cy="{y2}" r="9" fill="#c2410c"/>')
    o.append(f'<text x="{(x1+x2)/2+10}" y="{(y1+y2)/2+8}" font-size="24" fill="#c2410c">{e.get("label","")}</text>')
o.append('</svg>')
preview.write_text('\n'.join(o))
