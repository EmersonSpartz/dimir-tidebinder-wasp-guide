#!/usr/bin/env python3
"""Hallucination gate: every card an entry names must exist in that deck's 75 (or be one of ours). Exit 2 on violations."""
import json, unicodedata, re, sys
R = json.load(open('data/result.json'))['result']
decks = {d['label']: d for d in R['decks']}
ours = {"tishana's tidebinder", "the wondrous wasp"}
stock = json.load(open('/Users/emersonspartz/dimir-midrange-guide-library/data/dm_decks.json'))[0]
ourlist = {k.lower() for k in list(stock['main']) + list(stock['side'])} | ours

def canon_deck(name, labels):
    """Map an agent's padded deck string to the canonical label (longest label that the string starts with or contains)."""
    n = name.lower()
    best = None
    for lab in labels:
        core = lab.lower().replace(' (mirror)', '')
        if n.startswith(core) or core in n:
            if best is None or len(core) > len(best.lower().replace(' (mirror)', '')): best = lab
    return best

GENERIC = ('any ', 'their ', 'our ', 'own ', 'opponent', 'token', 'each ', 'every ', 'all ', 'attacker', 'blocker', 'holding a blank')
def norm(s): return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower().strip()
bad = 0; total = 0
for e in R['entries']:
    lab = canon_deck(e['deck'], list(decks))
    d = decks.get(lab)
    if not d: print(f'!! entry deck not in list: {e["deck"]}'); bad += 1; continue
    f = json.load(open(f"data/decks/{d['slug']}.json"))
    pool = {norm(k) for k in list(f['main']) + list(f['side'])}
    for k in f['cards']:
        for face in k.split(' // '): pool.add(norm(face))
    pool = {p for p in pool if len(p) > 3}
    DERIVED = ('earthbended', 'earthbend', 'token', 'emblem', 'treasure', 'copy', 'animated', 'manland', 'creature land', 'ours', 'our ')
    master = json.load(open('data/opponents.json'))['cards']
    for k in master:
        if any(norm(k.split(' // ')[0]) == p or norm(k.split(' // ')[0]) in pool for p in [norm(k.split(' // ')[0])]):
            for face in k.split(' // '): pool.add(norm(face))
    STOP = {'with','cast','once','mana','after','before','while','their','attacker','holding','blank','creature','returned','trigger','granted','body','plays','third','bucket','rare','bonuses','demon','summon',
            'sacrifice','ordinary','legendary','equipped','declared','already','attacking','ninjutsu','returning','copy','back','face','only','survive','main','side'}
    vocab = {w for p in pool | {norm(o) for o in ourlist} for w in re.findall(r"[a-z']{4,}", p)} - STOP
    def ok(name):
        n = norm(name)
        if any(p in n for p in pool): return True                 # grounded in a real card of this deck
        # short-name reference (Thorin, Inti, Hydra / Chocobo): EVERY capitalized word must be in this deck's card vocabulary
        base = re.sub(r'\([^)]*\)', ' ', name)
        caps = [norm(w) for w in re.findall(r"\b[A-Z][A-Za-z'\u00C0-\u024F]{3,}", base)]
        caps = [w for w in caps if w not in STOP]
        if caps and all(w in vocab for w in caps): return True
        if any(o in n for o in ourlist if len(o) > 5): return True # one of our cards
        if any(w in n for w in GENERIC) or any(w in n for w in DERIVED): return True
        return False
    named = [t['card'] for t in e['tidebinder']['targets']] + [t['card'] for t in e['wasp']['targets']] \
          + [t['card'] for t in e['tidebinder'].get('traps', [])] + [t['card'] for t in e['wasp'].get('traps', [])]
    for c in named:
        total += 1
        if not ok(c): print(f'!! {e["deck"]}: "{c}" not in this deck\'s 75'); bad += 1
    for key in ('tidebinder', 'wasp'):
        pr = sorted(t['priority'] for t in e[key]['targets'])
        if pr and pr != list(range(1, len(pr) + 1)): print(f'-- {e["deck"]} {key}: priorities not 1..n: {pr}')
print(f'\n{len(R["entries"])} entries, {total} card references checked, {bad} violations')
conf = {}
for e in R['entries']: conf[e.get('confidence')] = conf.get(e.get('confidence'), 0) + 1
print('confidence:', conf, '| disputed total:', sum(len(e.get('disputed') or []) for e in R['entries']))
sys.exit(2 if bad else 0)
