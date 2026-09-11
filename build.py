#!/usr/bin/env python3
"""Build index.html from data/result.json (workflow output) + data/our_cards.json. No em dashes in copy."""
import json, html as H, re, sys
R = json.load(open('data/result.json'))['result']
ours = json.load(open('data/our_cards.json'))

def canon_deck(name, labels):
    """Map an agent's padded deck string to the canonical label (longest label that the string starts with or contains)."""
    n = name.lower()
    best = None
    for lab in labels:
        core = lab.lower().replace(' (mirror)', '')
        if n.startswith(core) or core in n:
            if best is None or len(core) > len(best.lower().replace(' (mirror)', '')): best = lab
    return best

entries = R['entries']; P = R['principles']; decks = {d['label']: d for d in R['decks']}
share = {d['label']: d['share'] for d in R['decks']}
for e in entries:
    lab = canon_deck(e['deck'], list(decks))
    if lab: e['deck_raw'] = e['deck']; e['deck'] = lab
    else: print('UNMAPPED DECK:', e['deck'], file=sys.stderr)
entries.sort(key=lambda e: -share.get(e['deck'], 0))
DASH = 0
def esc(s): return H.escape(str(s), quote=False)
def nd(s):
    global DASH
    s = str(s); n = s.count('—') + s.count('–'); DASH += n
    return re.sub(r'\s*[—–]\s*', ', ', s)
def E(s): return esc(nd(s))
VCOL = {'premium': ('#153a2a', '#6ad48b'), 'good': ('#16243d', '#8fb4ee'), 'situational': ('#3a2e14', '#e0b878'), 'weak': ('#22242a', '#8a90a0')}
def vbadge(v, lab):
    bg, fg = VCOL.get(v, VCOL['weak'])
    return f'<span class="vb" style="background:{bg};color:{fg}">{lab}: {esc(v)}</span>'
def li(items): return ''.join(f'<li>{E(x)}</li>' for x in items)
def targets_tb(ts):
    rows = ''
    for t in sorted(ts, key=lambda t: t.get('priority', 99)):
        rows += f'''<div class="tg"><div class="tg-h"><span class="pr">#{t.get('priority','?')}</span><b>{E(t['card'])}</b></div>
<div class="tg-ab">{E(t['ability'])}</div>
<div class="tg-r"><span class="k">Why</span>{E(t['why'])}</div>
<div class="tg-r"><span class="k">When</span>{E(t['timing_window'])}</div>
<div class="tg-r"><span class="k">After</span>{E(t['after_effect'])}</div>
{f'<div class="tg-r risk"><span class="k">Risk</span>{E(t["risk"])}</div>' if t.get('risk') else ''}</div>'''
    return rows or '<div class="none">No worthwhile targets.</div>'
def targets_w(ts):
    rows = ''
    for t in sorted(ts, key=lambda t: t.get('priority', 99)):
        rows += f'''<div class="tg"><div class="tg-h"><span class="pr">#{t.get('priority','?')}</span><b>{E(t['card'])}</b></div>
<div class="tg-r"><span class="k">Why</span>{E(t['why'])}</div>
<div class="tg-r"><span class="k">When</span>{E(t['timing_window'])}</div>
<div class="tg-r"><span class="k">After</span>{E(t['after_effect'])}</div></div>'''
    return rows or '<div class="none">No worthwhile targets.</div>'
def traps(ts):
    if not ts: return ''
    return '<div class="sub">Traps</div>' + ''.join(f'<div class="trap"><b>{E(t["card"])}:</b> {E(t["wrong_idea"])} <span class="tw">{E(t["why_wrong"])}</span></div>' for t in ts)

secs = ''
for i, e in enumerate(entries):
    tb, w = e['tidebinder'], e['wasp']
    conf = e.get('confidence', '?')
    disputed = e.get('disputed') or []; changes = e.get('changes_made') or []
    meta = f'''<details class="meta"><summary>Review trail: confidence {esc(conf)}, {len(disputed)} disputed, {len(changes)} changes</summary>
{('<div class="sub">Disputed reviewer points (kept as written)</div><ul>' + li(disputed) + '</ul>') if disputed else ''}
{('<div class="sub">Changes after review</div><ul>' + li(changes) + '</ul>') if changes else ''}</details>'''
    secs += f'''<div class="mu{' open' if i == 0 else ''}">
  <div class="mu-head" onclick="this.parentElement.classList.toggle('open')">
    <span class="mu-name">vs. {E(e['deck'])}</span><span class="sh">{share.get(e['deck'], '?')}%</span>
    {vbadge(tb['verdict'], 'TB')}{vbadge(w['verdict'], 'Wasp')}<span class="chev">&#9660;</span>
  </div>
  <div class="mu-body">
    <div class="how">{E(e['how_they_win'])}</div>
    <div class="blk tbk"><div class="blk-h">Tishana's Tidebinder</div><div class="summ">{E(tb['summary'])}</div>
      {targets_tb(tb['targets'])}{traps(tb.get('traps'))}
      {('<div class="sub">Not worth it</div><div class="chips">' + ''.join(f'<span class="chip">{E(x)}</span>' for x in tb.get('dont_bother', [])) + '</div>') if tb.get('dont_bother') else ''}
    </div>
    <div class="blk wbk"><div class="blk-h">The Wondrous Wasp</div><div class="summ">{E(w['summary'])}</div>
      {targets_w(w['targets'])}{traps(w.get('traps'))}
    </div>
    {('<div class="blk"><div class="blk-h">Lines with the rest of the deck</div><ul class="lines">' + li(e['combined_lines']) + '</ul></div>') if e.get('combined_lines') else ''}
    <div class="blk"><div class="blk-h">Hold or fire</div><div class="summ">{E(e['hold_or_fire'])}</div></div>
    <div class="blk"><div class="blk-h">How many to run</div><div class="summ">{E(e['counts_recommendation'])}</div></div>
    {meta}
  </div>
</div>
'''
tb, wa = ours["Tishana's Tidebinder"], ours['The Wondrous Wasp']
top_tb = ''.join(f'<div class="rk"><span class="pr">#{t["rank"]}</span><b>{E(t["card"])}</b> <span class="dk">{E(t["deck"])}</span><div class="tg-ab">{E(t["ability"])}</div><div class="rk-w">{E(t["why"])}</div></div>' for t in sorted(P['top_tidebinder_targets'], key=lambda t: t['rank']))
top_w = ''.join(f'<div class="rk"><span class="pr">#{t["rank"]}</span><b>{E(t["card"])}</b> <span class="dk">{E(t["deck"])}</span><div class="rk-w">{E(t["why"])}</div></div>' for t in sorted(P['top_wasp_targets'], key=lambda t: t['rank']))

page = f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<title>Tidebinder and Wasp Guide</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#080a10;color:#dfe4ee;font-size:14px;line-height:1.5}}
.hero{{display:grid;grid-template-columns:1fr 1fr;height:170px;position:relative;border-bottom:1px solid #1a2233}}
.hero .art{{background-size:cover;background-position:center 25%}}
.hero .ov{{position:absolute;inset:0;background:linear-gradient(to bottom,rgba(8,10,16,.15),rgba(8,10,16,.96));display:flex;flex-direction:column;justify-content:flex-end;padding:0 18px 14px}}
.hero h1{{font-size:24px;font-weight:800;color:#fff;text-shadow:0 2px 12px rgba(0,0,0,.9)}}
.hero .sub{{font-size:12px;color:#9fb3d4;margin-top:3px}}
.banner{{padding:11px 16px;background:#0c1220;border-bottom:1px solid #182236;font-size:11.5px;color:#8fa3c4;line-height:1.6}}
.sect{{padding:16px;border-bottom:1px solid #131a28}}
.sect h2{{font-size:14px;color:#8fb4ee;margin-bottom:9px}}
.card{{background:#0e1320;border:1px solid #1a2438;border-radius:7px;padding:11px 13px;margin-bottom:9px}}
.card .nm{{font-weight:700;color:#e8edf6;font-size:13.5px}} .card .mc{{color:#8fb4ee;font-size:12px;margin-left:6px}}
.card .or{{font-size:12.5px;color:#c5cddb;margin-top:6px;line-height:1.6;white-space:pre-line}}
.rul{{font-size:11.5px;color:#9aa6bb;margin-top:6px;padding-left:10px;border-left:2px solid #1f2d48;line-height:1.55}}
ul.rules{{padding-left:18px}} ul.rules li{{font-size:12.5px;color:#c5cddb;margin-bottom:6px;line-height:1.6}}
ul.traps li{{color:#d9b58c}}
.rk{{background:#0e1320;border:1px solid #1a2438;border-radius:7px;padding:9px 12px;margin-bottom:7px;font-size:12.5px}}
.rk .dk{{color:#7f8ca6;font-size:11px;margin-left:6px}} .rk-w{{color:#b9c2d2;font-size:12px;margin-top:4px;line-height:1.55}}
.pr{{display:inline-block;min-width:26px;font-size:10px;font-weight:800;color:#6ad48b;margin-right:6px}}
.mu{{border-bottom:1px solid #131a28}}
.mu-head{{display:flex;align-items:center;gap:8px;padding:13px 16px;cursor:pointer;user-select:none;-webkit-tap-highlight-color:transparent;flex-wrap:wrap}}
.mu-name{{flex:1;font-size:15px;font-weight:600;color:#e8edf6;min-width:160px}}
.sh{{font-size:10px;font-weight:700;background:#16243d;color:#8fb4ee;border-radius:10px;padding:2px 8px}}
.vb{{font-size:10px;font-weight:700;border-radius:4px;padding:2px 7px;letter-spacing:.3px}}
.chev{{color:#2c3a55;font-size:11px;transition:transform .18s}} .mu.open .chev{{transform:rotate(180deg)}}
.mu-body{{display:none;padding:0 12px 14px}} .mu.open .mu-body{{display:block}}
.how{{font-size:12.5px;color:#aab4c6;font-style:italic;padding:2px 4px 10px;line-height:1.6}}
.blk{{background:#0e1320;border:1px solid #1a2438;border-radius:7px;margin-bottom:9px;padding:10px 12px}}
.blk.tbk{{border-left:3px solid #8fb4ee}} .blk.wbk{{border-left:3px solid #e0c27a}}
.blk-h{{font-size:12px;font-weight:700;color:#e8edf6;margin-bottom:5px;letter-spacing:.3px}}
.summ{{font-size:12.5px;color:#c5cddb;line-height:1.6;margin-bottom:8px}}
.tg{{border-top:1px solid #182236;padding:8px 0 6px}} .tg-h{{font-size:13px;color:#e8edf6}}
.tg-ab{{font-size:11.5px;color:#8fb4ee;font-style:italic;margin:3px 0 5px;line-height:1.5}}
.tg-r{{font-size:12px;color:#c5cddb;line-height:1.55;margin-bottom:3px;padding-left:52px;position:relative}}
.tg-r .k{{position:absolute;left:0;top:1px;font-size:9.5px;font-weight:800;letter-spacing:.6px;text-transform:uppercase;color:#56708f}}
.tg-r.risk{{color:#d9b58c}} .tg-r.risk .k{{color:#a07a50}}
.sub{{font-size:10px;font-weight:800;letter-spacing:.7px;text-transform:uppercase;color:#56708f;margin:10px 0 5px}}
.trap{{font-size:12px;color:#d9b58c;line-height:1.55;margin-bottom:5px}} .trap .tw{{color:#a89478}}
.chips{{display:flex;flex-wrap:wrap;gap:5px}} .chip{{font-size:11px;background:#141a28;color:#8a94aa;border-radius:4px;padding:3px 8px}}
ul.lines{{padding-left:18px}} ul.lines li{{font-size:12.5px;color:#c5cddb;margin-bottom:6px;line-height:1.6}}
details.meta{{margin-top:6px}} details.meta summary{{font-size:11px;color:#56708f;cursor:pointer;list-style:none}} details.meta ul{{padding-left:18px;margin-top:4px}} details.meta li{{font-size:11.5px;color:#9aa6bb;line-height:1.55;margin-bottom:4px}}
.none{{font-size:12px;color:#7f8ca6;font-style:italic}}
.stats{{padding:10px 16px;font-size:11px;color:#56627a}}
@media (max-width:520px){{.hero{{height:140px}}}}
</style></head><body>
<div class="hero">
  <div class="art" style="background-image:url('{tb['art']}')"></div>
  <div class="art" style="background-image:url('{wa['art']}')"></div>
  <div class="ov"><h1>Tidebinder and Wasp</h1><div class="sub">Dimir Midrange interaction guide vs the {len(entries)} most-played Standard decks &middot; Sept 2026 &middot; every rules claim adversarially checked</div></div>
</div>
<div class="banner"><b style="color:#8fb4ee;">How to read this:</b> each deck has a ranked list of abilities to counter with Tidebinder and creatures to tap-and-blank with Wasp, the exact stack moment, what the permanent loses and keeps afterward, and the traps. Each entry was drafted, then attacked by three independent reviewers (rules lawyer, strategy skeptic, oracle-grounding checker), then revised; corrections were accepted only when backed by oracle text or the rules. Decks ordered by metagame share.</div>

<div class="sect"><h2>The two cards</h2>
  <div class="card"><span class="nm">Tishana's Tidebinder</span><span class="mc">{esc(tb['mc'])} &middot; {esc(tb['pt'])} &middot; {esc(tb['type'].replace(' — ',' · '))}</span><div class="or">{E(tb['oracle'])}</div>
    {''.join(f'<div class="rul">{E(t)}</div>' for _, t in tb['rulings'])}</div>
  <div class="card"><span class="nm">The Wondrous Wasp</span><span class="mc">{esc(wa['mc'])} &middot; {esc(wa['pt'])} &middot; {esc(wa['type'].replace(' — ',' · '))}</span><div class="or">{E(wa['oracle'])}</div></div>
</div>
<div class="sect"><h2>Rules you must know</h2><ul class="rules">{li(P['universal_rules'])}</ul>
  <h2 style="margin-top:14px">Universal traps</h2><ul class="rules traps">{li(P['universal_traps'])}</ul></div>
<div class="sect"><h2>Top Tidebinder targets in the format</h2>{top_tb}
  <h2 style="margin-top:14px">Top Wasp targets in the format</h2>{top_w}</div>
<div class="sect"><h2>Hold or fire</h2><ul class="rules">{li(P['hold_fire_heuristics'])}</ul>
  <h2 style="margin-top:14px">Sideboarding the extra Tidebinders</h2><div class="summ">{E(P['sideboard_guidance'])}</div></div>

{secs}
<div class="stats">Built 2026-09-10 from MTGGoldfish featured lists (one per archetype) and Scryfall oracle text. {len(entries)} decks, {sum(len(e['tidebinder']['targets']) for e in entries)} Tidebinder targets, {sum(len(e['wasp']['targets']) for e in entries)} Wasp targets. Art: Tishana's Tidebinder, The Wondrous Wasp (Scryfall).</div>
</body></html>'''
open('index.html', 'w').write(page)
print(f'built {len(page)//1024} KB | {len(entries)} decks | dashes scrubbed: {DASH}')
