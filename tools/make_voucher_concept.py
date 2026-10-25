"""Generate a personalised gift-voucher concept from the demo.

Usage: python tools/make_voucher_concept.py config.json
Output: v/<slug>/index.html  (served at https://p3trilo.github.io/hotel-concepts/v/<slug>/)

config keys: slug, name, tagline, eyebrow, headline, intro, gifts [[title, desc, price, detail]] x3,
amount_desc, message, accent, cta, on_cta, hero_bg, hero_eyebrow, prefix, guest ("client"), biz ("salon"),
seed [[title, to, value, used]] x2
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL = os.path.join(ROOT, 'demo', 'gift-vouchers', 'index.html')


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def js(s):
    return s.replace('\\', '\\\\').replace("'", "\\'")


def money(p):
    return f'{p:.2f}' if isinstance(p, float) and not float(p).is_integer() else f'{int(p)}'


def build(c):
    h = open(TPL, encoding='utf-8').read()
    name, P = c['name'], c['prefix']
    rep = [
        ('<title>Gift Vouchers Demo</title>', f'<title>{esc(name)} Gift Vouchers</title>'),
        ('Demo with a fictional inn by Petr Ivan. No payment is taken and no email is sent.',
         f'Concept prepared for {esc(name)} by Petr Ivan. Nothing here is live: no payment is taken and no email is sent.'),
        ('<b>The Glen Ardour Inn</b><span>A fictional Highland inn</span>', f'<b>{esc(name)}</b><span>{esc(c["tagline"])}</span>'),
        ('<span class="eyebrow">Gift vouchers</span>\n    <h1>Give a night in the Highlands</h1>',
         f'<span class="eyebrow">{esc(c["eyebrow"])}</span>\n    <h1>{esc(c["headline"])}</h1>'),
        ('<p>Choose an amount or an experience, add a personal message, and we email the voucher on the day you pick, ready for Christmas morning.</p>',
         f'<p>{esc(c["intro"])}</p>'),
        ('What the guest sees', f'What the {c["guest"]} sees'),
        ('What the hotel sees', f'What the {c["biz"]} sees'),
        ("See the hotel's view", f"See the {c['biz']}'s view"),
        ('<span class="eyebrow">For the hotel</span>', f'<span class="eyebrow">For the {c["biz"]}</span>'),
        ('When a guest comes to use one', f'When a {c["guest"]} comes to use one'),
        ("the hotel also gets an email for every sale, and the money goes straight to the hotel's own Stripe account",
         f"the {c['biz']} also gets an email for every sale, and the money goes straight to your own Stripe account"),
        ('<div class="vh"><b>The Glen Ardour Inn</b><span>Gift voucher</span></div>', f'<div class="vh"><b>{esc(name)}</b><span>Gift voucher</span></div>'),
        ("Happy Christmas! Let's finally have that weekend away.", esc(c['message'])),
        ('<span>Spend on rooms, food or drink</span><span class="price">£25 to £500</span>', f'<span>{esc(c["amount_desc"])}</span><span class="price">£25 to £500</span>'),
        ("amount: { title: '', detail: 'To spend on rooms, food or drink', price: 0 }", f"amount: {{ title: '', detail: '{js(c['amount_desc'])}', price: 0 }}"),
        ('<p>The Glen Ardour Inn is a fictional business, made up for this demo.</p>',
         f'<p>Concept prepared for {esc(name)} by Petr Ivan. Not the official website of {esc(name)}.</p>'),
        ("var KEY = 'glenArdourVouchers';", f"var KEY = 'vouchers_{c['slug']}';"),
        ('GA-', P + '-'),
    ]
    for a, b in rep:
        if a not in h:
            raise SystemExit(f'template text not found: {a[:60]}')
        h = h.replace(a, b)
    # gift options (3) + JS objects
    keys = ['night', 'dinner', 'tea']
    opts = re.findall(r'<div class="opt"><input type="radio" name="gift" id="g-(night|dinner|tea)"[^\n]*\n', h)
    lines = h.split('\n')
    out = []
    for ln in lines:
        m = re.search(r'id="g-(night|dinner|tea)"', ln)
        if m and 'name="gift"' in ln:
            i = keys.index(m.group(1)); t, d, p, _ = c['gifts'][i]
            ln = re.sub(r'<b>[^<]*</b><span>[^<]*</span><span class="price">[^<]*</span>',
                        f'<b>{esc(t)}</b><span>{esc(d)}</span><span class="price">£{money(p)}</span>', ln)
        out.append(ln)
    h = '\n'.join(out)
    for i, k in enumerate(keys):
        t, d, p, det = c['gifts'][i]
        h = re.sub(rf"    {k}: \{{ title: '[^']*', detail: '[^']*', price: \d+ \}}",
                   f"    {k}: {{ title: '{js(t)}', detail: '{js(det)}', price: {p} }}", h)
    h = h.replace('<div class="vtitle" id="v-title">A night for two</div>', f'<div class="vtitle" id="v-title">{esc(c["gifts"][0][0])}</div>')
    h = h.replace('<b id="total">£220.00</b>', f'<b id="total">£{float(c["gifts"][0][2]):.2f}</b>')
    seed = ',\n    '.join(f"{{ num: '{P}-{n}', title: '{js(t)}', to: '{js(to)}', value: {v}, used: {str(u).lower()} }}"
                           for n, (t, to, v, u) in zip(['418203', '552917'], c['seed']))
    h = re.sub(r"var memory = \[\n.*?\n  \];", "var memory = [\n    " + seed + "\n  ];", h, flags=re.S)
    # colours
    h = re.sub(r'--accent: #[0-9A-Fa-f]{6}; --cta: #[0-9A-Fa-f]{6}; --on-cta: #[0-9A-Fa-f]{6}; --hero-bg: #[0-9A-Fa-f]{6};',
               f'--accent: {c["accent"]}; --cta: {c["cta"]}; --on-cta: {c["on_cta"]}; --hero-bg: {c["hero_bg"]};', h)
    h = h.replace('.intro .eyebrow { color: #E3BD7A; }', f'.intro .eyebrow {{ color: {c["hero_eyebrow"]}; }}')
    h = h.replace('--brass: #B07A2E;', f'--brass: {c["cta"]};')
    h = h.replace('.demo-bar { background: #7A2E2E;', '.demo-bar { background: #2A2A2A;')
    # optional "Visit us" block: address, hours, free Google Maps and reviews links (no API key)
    v = c.get('visit')
    if v:
        from urllib.parse import quote_plus
        q = quote_plus(v['maps_query'])
        block = (
            '<section class="block" id="visit"><div class="wrap two">'
            '<div><div class="head"><span class="eyebrow">Visit us</span>'
            f'<h2>{esc(name)}</h2><p>{esc(v["address"])}</p></div>'
            f'<p class="note" style="margin-top:0">{esc(v["hours"])}</p></div>'
            '<div class="contact"><h2>Find us</h2>'
            f'<a class="btn btn-book" href="https://www.google.com/maps/search/?api=1&amp;query={q}" target="_blank" rel="noopener">Open in Google Maps</a>'
            f'<a class="btn btn-line" href="https://www.google.com/maps/search/?api=1&amp;query={q}" target="_blank" rel="noopener">Read our Google reviews</a>'
            '</div></div></section>\n')
        h = h.replace('</main>', block + '</main>', 1)
    return h


def main():
    c = json.load(open(sys.argv[1], encoding='utf-8'))
    d = os.path.join(ROOT, 'v', c['slug']); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(build(c))
    print('built', f'v/{c["slug"]}/index.html')


if __name__ == '__main__':
    main()
