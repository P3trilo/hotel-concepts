"""Generate a personalised garage booking concept from the demo (their name, photo, services, prices, colours).

Usage: python tools/make_garage_concept.py config.json
Output: v/<slug>/index.html  (served at https://p3trilo.github.io/hotel-concepts/v/<slug>/)

config keys: slug, name, tagline, eyebrow, headline, intro, trust [4 short verified facts], phone ("01234 567890"),
services [[svc_key, title, desc, price_text, minutes]] (1-6; price_text like "£54.85" or "Quote"; never invent prices),
accent, cta, on_cta, hero_bg
optional: photo (local path to a photo from their own site -> intro background), visit {address, hours, maps_query},
footer_note (replaces the MOT/pre-MOT note)
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL = os.path.join(ROOT, 'demo', 'garage-booking', 'index.html')


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def build(c):
    h = open(TPL, encoding='utf-8').read()
    name = c['name']
    tel = '+44' + re.sub(r'\D', '', c['phone'])[1:]
    trust = ''.join(f'<li>{esc(t)}</li>' for t in c['trust'])
    svcs = c['services']
    svc_html = '\n'.join(
        f'          <button type="button" class="svc" data-svc="{esc(k)}" data-price="{esc(p)}" data-mins="{m}" aria-pressed="{str(i == 0).lower()}">'
        f'<b>{esc(t)}</b><span>{esc(d)}</span><em>{esc(p)}</em></button>' for i, (k, t, d, p, m) in enumerate(svcs))
    rep = [
        ('<title>Garage Booking Demo</title>', f'<title>{esc(name)} Online Booking</title>'),
        ('Demo with a fictional garage by Petr Ivan. No booking is made and no message is sent.',
         f'Concept prepared for {esc(name)} by Petr Ivan. Nothing here is live: no booking is made and no message is sent.'),
        ('<b>Glenbrae Garage</b><span>A fictional independent garage</span>', f'<b>{esc(name)}</b><span>{esc(c["tagline"])}</span>'),
        ('<span class="eyebrow">MOT · Servicing · Repairs</span>\n    <h1>Book your MOT in two minutes</h1>',
         f'<span class="eyebrow">{esc(c["eyebrow"])}</span>\n    <h1>{esc(c["headline"])}</h1>'),
        ('<p>Pick a service, enter your registration, choose a time that suits you. We confirm by text, usually within the hour.</p>',
         f'<p>{esc(c["intro"])}</p>'),
        ('<li>Family run since 1987</li><li>Approved MOT test centre</li><li>4.9 from 312 Google reviews</li><li>All makes and models</li>', trust),
        ('href="tel:+440000000000"', f'href="tel:{tel}"'),
        ("var KEY = 'glenbraeRequests';", f"var KEY = 'garage_{c['slug']}';"),
        ("chosen = { svc: 'MOT', price: '£54.85' }", f"chosen = {{ svc: '{svcs[0][0]}', price: '{svcs[0][3]}' }}"),
        ('<p>Glenbrae Garage is a fictional business, made up for this demo. Prices are examples; the MOT fee shown is the official maximum for a car.</p>',
         f'<p>Concept prepared for {esc(name)} by Petr Ivan. Not the official website of {esc(name)}. Services are taken from your own website.</p>'),
        ('.demo-bar { background: #7A2E2E;', '.demo-bar { background: #2A2A2A;'),
    ]
    for a, b in rep:
        if a not in h:
            raise SystemExit(f'template text not found: {a[:60]}')
        h = h.replace(a, b)
    h = re.sub(r'(<div class="services" id="services">\n).*?(\n        </div>)', lambda m: m.group(1) + svc_html + m.group(2), h, count=1, flags=re.S)
    if c.get('footer_note'):
        h = re.sub(r'<p>The list of services is set up for each garage\..*?</p>', f'<p>{esc(c["footer_note"])}</p>', h, count=1, flags=re.S)
    # seed requests use the first two services
    h = h.replace("svc: 'MOT', when: 'Tomorrow 08:30'", f"svc: '{svcs[0][0]}', when: 'Tomorrow 08:30'")
    h = h.replace("svc: 'Full service', when: 'Tomorrow 09:00'", f"svc: '{svcs[min(1, len(svcs) - 1)][0]}', when: 'Tomorrow 09:00'")
    h = h.replace("name: 'Morag'", "name: 'Sarah'").replace("name: 'Alasdair'", "name: 'James'")
    h = h.replace("reg: 'SN19 ABC'", "reg: 'YD19 ABC'").replace("reg: 'SY66 DEF'", "reg: 'KX66 DEF'")
    h = re.sub(r'--accent: #[0-9A-Fa-f]{6}; --cta: #[0-9A-Fa-f]{6}; --on-cta: #[0-9A-Fa-f]{6}; --hero-bg: #[0-9A-Fa-f]{6};',
               f'--accent: {c["accent"]}; --cta: {c["cta"]}; --on-cta: {c["on_cta"]}; --hero-bg: {c["hero_bg"]};', h)
    if c.get('photo'):
        h = h.replace('.intro { background: var(--hero-bg); color: #fff; }',
                      '.intro { background: linear-gradient(180deg, rgba(0,0,0,.55), rgba(0,0,0,.78)), url(photo.jpg) center/cover no-repeat, var(--hero-bg); color: #fff; }\n'
                      '.intro p { color: #EEE !important; }\n'
                      '.intro .eyebrow { color: #FFFFFF !important; text-shadow: 0 1px 3px rgba(0,0,0,.6); }')
    v = c.get('visit')
    if v:
        from urllib.parse import quote_plus
        q = quote_plus(v['maps_query'])
        block = (
            '<section id="visit" style="background:var(--paper);color:var(--ink);padding:40px 0;border-top:1px solid var(--line)"><div class="wrap">'
            f'<span class="eyebrow" style="color:var(--accent)">Find us</span><h2>{esc(name)}</h2>'
            f'<p>{esc(v["address"])}</p><p>{esc(v["hours"])}</p>'
            f'<div class="actions" style="display:flex;flex-wrap:wrap;gap:10px"><a class="btn btn-line" href="https://www.google.com/maps/search/?api=1&amp;query={q}" target="_blank" rel="noopener">Open in Google Maps</a>'
            f'<a class="btn btn-line" href="tel:{tel}">{esc(c["phone"])}</a></div>'
            '</div></section>\n')
        h = h.replace('</main>', block + '</main>', 1)
    return h


def main():
    c = json.load(open(sys.argv[1], encoding='utf-8'))
    d = os.path.join(ROOT, 'v', c['slug']); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(build(c))
    if c.get('photo'):
        from PIL import Image
        im = Image.open(c['photo']).convert('RGB'); im.thumbnail((1400, 1400))
        im.save(os.path.join(d, 'photo.jpg'), quality=78, optimize=True)
    print('built', f'v/{c["slug"]}/index.html')


if __name__ == '__main__':
    main()
