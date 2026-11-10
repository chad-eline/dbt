"""Generate lo-fi SVG wireframes for the AWS batch pipeline blueprint prototype."""
import html, sys, pathlib

W, H = 960, 600
INK, MUTED, LINE = '#2b2b2b', '#6b6b6b', '#9a9a9a'
PANEL, BAR, HEAD, ROWLINE = '#f4f4f4', '#e3e3e3', '#ebebeb', '#d4d4d4'
ACC = '#c2410c'
FONT = 'Segoe UI, Helvetica Neue, Arial, sans-serif'


class Svg:
    def __init__(self, title):
        self.o = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="{FONT}">',
            f'<title>{html.escape(title)}</title>',
            f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" fill="#ffffff" stroke="#bdbdbd"/>',
        ]
        self.calls = []

    def R(self, x, y, w, h, fill='none', stroke=LINE, rx=4, sw=1):
        self.o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def T(self, x, y, t, size=12, weight=400, fill=INK, anchor='start'):
        self.o.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{html.escape(str(t))}</text>')

    def L(self, x1, y1, x2, y2, stroke=LINE, sw=1):
        self.o.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}"/>')

    def callout(self, n, x, y):
        self.calls.append((n, x, y))

    def chrome(self, active):
        self.R(0.5, 0.5, W - 1, 44, fill='#ededed', stroke='#bdbdbd', rx=0)
        self.T(20, 28, 'Positions', 14, 700)
        x = 150
        for name, w in (('Holdings', 54), ('Breaks', 42), ('Runs', 30)):
            on = name == active
            self.T(x, 28, name, 12, 700 if on else 400, INK if on else MUTED)
            if on:
                self.L(x, 36, x + w, 36, INK, 2)
            x += w + 30
        self.o.append(f'<circle cx="928" cy="22" r="11" fill="{BAR}" stroke="{LINE}"/>')

    def title(self, text):
        self.T(24, 78, text, 20, 700)

    def select(self, x, y, w, label, value, placeholder=False, chev=True):
        self.T(x, y - 6, label, 10, 400, MUTED)
        self.R(x, y, w, 28, fill='#ffffff')
        self.T(x + 10, y + 18, value, 12, 400, MUTED if placeholder else INK)
        if chev:
            self.o.append(f'<polyline points="{x+w-19},{y+11} {x+w-14},{y+17} {x+w-9},{y+11}" fill="none" stroke="{MUTED}" stroke-width="1.5"/>')

    def tile(self, x, y, w, label, value):
        self.R(x, y, w, 60, fill=PANEL)
        self.T(x + 12, y + 22, label, 10, 400, MUTED)
        self.T(x + 12, y + 46, value, 18, 700)

    def chip(self, x, y, text, dark=False):
        w = round(len(text) * 6.3 + 16)
        self.R(x, y, w, 18, fill=INK if dark else '#ffffff', stroke=INK if dark else LINE, rx=9)
        self.T(x + w / 2, y + 13, text, 10, 700, '#ffffff' if dark else INK, 'middle')

    def table(self, x, y, cols, rows, rh=30, hh=28, size=12, selected=None, placeholders=0):
        w = sum(c[1] for c in cols)
        n = len(rows) + placeholders
        self.R(x, y, w, hh + rh * n, fill='#ffffff')
        self.R(x, y, w, hh, fill=HEAD)
        cx = x
        for title, cw, al in cols:
            self.T(cx + cw - 10 if al == 'r' else cx + 10, y + 18, title, 11, 700, INK, 'end' if al == 'r' else 'start')
            cx += cw
        for i, row in enumerate(rows):
            ry = y + hh + i * rh
            if selected == i:
                self.R(x + 1, ry + 1, w - 2, rh - 1, fill='#dedede', stroke='none', rx=0)
                self.R(x + 1, ry + 1, 3, rh - 1, fill=INK, stroke='none', rx=0)
            self.L(x, ry, x + w, ry, ROWLINE)
            cx = x
            for (title, cw, al), cell in zip(cols, row):
                if isinstance(cell, tuple):
                    self.chip(cx + 8, ry + (rh - 18) / 2, cell[1], cell[2])
                elif cell != '':
                    self.T(cx + cw - 10 if al == 'r' else cx + 10, ry + rh / 2 + 4, cell, size, 400, INK, 'end' if al == 'r' else 'start')
                cx += cw
        for j in range(placeholders):
            ry = y + hh + (len(rows) + j) * rh
            self.L(x, ry, x + w, ry, ROWLINE)
            cx = x
            for k, (title, cw, al) in enumerate(cols):
                bw = round(cw * (0.5 + 0.12 * ((j + k) % 3)))
                bw = min(bw, cw - 20)
                bx = cx + cw - 10 - bw if al == 'r' else cx + 10
                self.R(bx, ry + rh / 2 - 4, bw, 8, fill=BAR, stroke='none', rx=3)
                cx += cw
        return y + hh + rh * n

    def caption(self, screen):
        self.T(24, 590, f'Wireframe (lo-fi): {screen}. Callout numbers match the Elements table in AWS_Batch_Pipeline_Blueprint.', 10, 400, MUTED)

    def out(self):
        for n, x, y in self.calls:
            self.o.append(f'<circle cx="{x}" cy="{y}" r="11" fill="{ACC}" stroke="#ffffff" stroke-width="2"/>')
            self.o.append(f'<text x="{x}" y="{y+4}" font-size="12" font-weight="700" fill="#ffffff" text-anchor="middle">{n}</text>')
        return '\n'.join(self.o + ['</svg>']) + '\n'


def holdings_grid():
    s = Svg('Wireframe: Holdings grid')
    s.chrome('Holdings')
    s.title('Holdings')
    s.R(662, 58, 274, 28, fill=PANEL, rx=14)
    s.T(799, 76, 'Loaded 2026-11-10 06:12, load 20261109-01', 11, 400, INK, 'middle')
    s.callout(1, 662, 60)
    s.select(24, 110, 150, 'As-of date', '2026-11-09'); s.callout(2, 174, 110)
    s.select(190, 110, 200, 'Account', 'All accounts (37)'); s.callout(3, 390, 110)
    s.select(406, 110, 170, 'Asset class', 'All'); s.callout(4, 576, 110)
    s.select(592, 110, 344, 'Search', 'Security name or id', placeholder=True, chev=False)
    s.tile(24, 156, 296, 'Market value (USD)', '1,842,330,118'); s.callout(5, 24, 156)
    s.tile(332, 156, 296, 'Positions', '12,408')
    s.tile(640, 156, 296, 'Accounts', '37')
    cols = [('Account', 100, 'l'), ('Security id', 110, 'l'), ('Security name', 250, 'l'), ('Asset class', 120, 'l'),
            ('Quantity', 110, 'r'), ('Price', 90, 'r'), ('Market value (USD)', 132, 'r')]
    rows = [
        ['ACC-0012', 'SEC-000184', 'Corp bond A 4.25% 2031', 'Fixed income', '2,500,000', '98.412', '2,460,300'],
        ['ACC-0012', 'SEC-000912', 'Treasury note 3.875% 2029', 'Fixed income', '10,000,000', '99.870', '9,987,000'],
        ['ACC-0012', 'SEC-004410', 'Large cap equity B', 'Equity', '15,200', '228.410', '3,471,832'],
        ['ACC-0031', 'SEC-000184', 'Corp bond A 4.25% 2031', 'Fixed income', '750,000', '98.412', '738,090'],
        ['ACC-0031', 'SEC-007702', 'Agency MBS pool C', 'Structured', '4,000,000', '101.125', '4,045,000'],
        ['ACC-0044', 'SEC-004410', 'Large cap equity B', 'Equity', '3,900', '228.410', '890,799'],
    ]
    s.table(24, 232, cols, rows, placeholders=3); s.callout(6, 24, 232)
    s.T(24, 562, 'Rows 1 to 50 of 12,408', 11, 400, MUTED)
    x = 380
    for lab, w in (('Prev', 44), ('1', 26), ('2', 26), ('3', 26), ('Next', 44)):
        s.R(x, 544, w, 26, fill=HEAD if lab == '1' else '#ffffff')
        s.T(x + w / 2, 561, lab, 11, 700 if lab == '1' else 400, INK, 'middle')
        x += w + 6
    s.R(826, 544, 110, 26, fill=INK, stroke=INK)
    s.T(881, 561, 'Export CSV', 11, 700, '#ffffff', 'middle'); s.callout(7, 826, 544)
    s.caption('Holdings grid')
    return s.out()


def break_report():
    s = Svg('Wireframe: Break report')
    s.chrome('Breaks')
    s.title('Position breaks')
    s.select(24, 110, 150, 'As-of date', '2026-11-09'); s.callout(1, 174, 110)
    s.select(190, 110, 200, 'Break type', 'All types'); s.callout(2, 390, 110)
    s.select(406, 110, 120, 'Min age (days)', '0', chev=False)
    for i, (lab, val) in enumerate((('Open breaks', '23'), ('Quantity mismatch', '14'), ('Missing at custodian', '6'), ('Missing in ABOR', '3'))):
        s.tile(24 + i * 231, 156, 219, lab, val)
    s.callout(3, 24, 156)
    cols = [('Account', 80, 'l'), ('Security id', 88, 'l'), ('ABOR qty', 88, 'r'), ('Custodian qty', 100, 'r'),
            ('Diff', 84, 'r'), ('Type', 136, 'l'), ('Age', 44, 'r')]
    rows = [
        ['ACC-0012', 'SEC-000184', '2,500,000', '2,450,000', '50,000', 'Quantity mismatch', '4'],
        ['ACC-0031', 'SEC-007702', '4,000,000', '', '4,000,000', 'Missing at custodian', '1'],
        ['ACC-0044', 'SEC-004410', '3,900', '4,100', '-200', 'Quantity mismatch', '2'],
        ['ACC-0058', 'SEC-001377', '', '125,000', '-125,000', 'Missing in ABOR', '7'],
    ]
    s.table(24, 232, cols, rows, size=11, selected=0, placeholders=5); s.callout(4, 24, 232)
    # detail panel
    px, py, pw, ph = 660, 232, 276, 298
    s.R(px, py, pw, ph, fill=PANEL); s.callout(5, px, py)
    s.T(px + 16, py + 26, 'Break detail', 13, 700)
    s.T(px + 16, py + 50, 'ACC-0012 / SEC-000184', 12, 700)
    s.T(px + 16, py + 67, 'Corp bond A 4.25% 2031', 11, 400, MUTED)
    for i, (lab, val) in enumerate((('ABOR', '2,500,000'), ('Custodian', '2,450,000'))):
        bx = px + 16 + i * 126
        s.R(bx, py + 80, 118, 56, fill='#ffffff')
        s.T(bx + 10, py + 98, lab, 10, 400, MUTED)
        s.T(bx + 10, py + 122, val, 15, 700)
    s.T(px + 16, py + 160, 'Difference 50,000', 12, 700)
    s.T(px + 16, py + 178, 'Type: quantity mismatch', 11)
    s.T(px + 16, py + 195, 'First seen 2026-11-05, age 4 days', 11)
    s.L(px + 16, py + 210, px + pw - 16, py + 210, ROWLINE)
    s.T(px + 30, py + 230, 'Lineage', 10, 700, MUTED); s.callout(6, px + 16, py + 226)
    s.T(px + 16, py + 250, 'ABOR load 20261109-01', 11)
    s.T(px + 16, py + 267, 'Custodian load 20261109-01', 11)
    s.T(px + 16, py + 284, 'File cust_a_positions_20261109.csv', 11)
    s.T(24, 562, 'Rows 1 to 23 of 23', 11, 400, MUTED)
    s.caption('Break report')
    return s.out()


def run_monitor():
    s = Svg('Wireframe: Run monitor')
    s.chrome('Runs')
    s.title('Pipeline runs')
    s.R(24, 96, 912, 54, fill=PANEL); s.callout(1, 24, 96)
    s.R(40, 110, 100, 26, fill=INK, stroke=INK, rx=13)
    s.T(90, 127, 'SUCCEEDED', 11, 700, '#ffffff', 'middle')
    s.T(156, 119, 'Run 20261109-01 for business date 2026-11-09', 13, 700)
    s.T(156, 138, 'Started 2026-11-10 05:40, ended 06:12, 32 min', 11, 400, MUTED)
    steps = (('Ingest and validate', 'Succeeded, 6 min', 'Rows out 24,811'),
             ('Stage positions', 'Succeeded, 9 min', 'Rows out 24,811'),
             ('Build marts', 'Succeeded, 17 min', 'Rows out 12,431'))
    for i, (name, st, rows_out) in enumerate(steps):
        x = 24 + i * 316
        s.R(x, 168, 280, 64, fill='#ffffff')
        s.o.append(f'<circle cx="{x+24}" cy="{200}" r="6" fill="{INK}"/>')
        s.T(x + 42, 192, name, 12, 700)
        s.T(x + 42, 209, st, 11, 400, MUTED)
        s.T(x + 42, 224, rows_out, 11, 400, MUTED)
        if i < 2:
            s.L(x + 280, 200, x + 310, 200, INK, 1.5)
            s.o.append(f'<polyline points="{x+304},{195} {x+311},{200} {x+304},{205}" fill="none" stroke="{INK}" stroke-width="1.5"/>')
    s.callout(2, 24, 168)
    s.select(24, 262, 220, 'Date range', '2026-11-03 to 2026-11-09'); s.callout(3, 244, 262)
    s.select(260, 262, 160, 'Status', 'All')
    cols = [('Run id', 104, 'l'), ('Business date', 100, 'l'), ('Step', 140, 'l'), ('Status', 96, 'l'), ('Rows in', 76, 'r'),
            ('Rows out', 76, 'r'), ('Started', 70, 'l'), ('Duration', 70, 'r'), ('Error', 180, 'l')]
    ok, bad = ('chip', 'Succeeded', False), ('chip', 'Failed', True)
    rows = [
        ['20261109-01', '2026-11-09', 'Build marts', ok, '24,811', '12,431', '05:55', '17 min', ''],
        ['20261109-01', '2026-11-09', 'Stage positions', ok, '24,811', '24,811', '05:46', '9 min', ''],
        ['20261109-01', '2026-11-09', 'Ingest and validate', ok, '24,811', '24,811', '05:40', '6 min', ''],
        ['20261106-02', '2026-11-06', 'Ingest and validate', ok, '24,790', '24,790', '07:15', '6 min', ''],
        ['20261106-01', '2026-11-06', 'Ingest and validate', bad, '12,390', '0', '05:40', '1 min', 'Contract: unknown column'],
    ]
    s.table(24, 306, cols, rows, rh=28, size=11, placeholders=2); s.callout(4, 24, 306)
    s.T(24, 556, 'Rows 1 to 7 of 41', 11, 400, MUTED)
    s.caption('Run monitor')
    return s.out()


if __name__ == '__main__':
    out = pathlib.Path(sys.argv[1])
    for name, fn in (('holdings_grid', holdings_grid), ('break_report', break_report), ('run_monitor', run_monitor)):
        p = out / f'AWS_Batch_Blueprint_wf_{name}.svg'
        p.write_text(fn(), encoding='ascii')
        print(p.name, p.stat().st_size)
