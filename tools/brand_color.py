"""Guess a business's brand colours from its website.

Usage: python tools/brand_color.py https://example.co.uk
Prints theme-color (if any) and the most used saturated colours from the page and its CSS,
weighted towards buttons, links and headers. Always check the result by eye.
"""
import collections, colorsys, re, sys
from urllib.parse import urljoin
import requests

requests.packages.urllib3.disable_warnings()
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124'}


def norm(hx):
    hx = hx.lstrip('#')
    if len(hx) == 3: hx = ''.join(ch * 2 for ch in hx)
    return '#' + hx[:6].upper()


def sat_ok(hx):
    r, g, b = (int(hx[i:i + 2], 16) / 255 for i in (1, 3, 5))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return s > 0.25 and 0.12 < l < 0.85


def main(url):
    html = requests.get(url, headers=UA, timeout=20, verify=False).text
    theme = re.search(r'<meta[^>]+name=["\']theme-color["\'][^>]+content=["\']([^"\']+)', html, re.I)
    css = [html]
    for href in re.findall(r'<link[^>]+rel=["\']stylesheet["\'][^>]+href=["\']([^"\']+)', html, re.I)[:8]:
        if 'fonts.googleapis' in href: continue
        try: css.append(requests.get(urljoin(url, href), headers=UA, timeout=15, verify=False).text[:400000])
        except Exception: pass
    text = '\n'.join(css)
    cnt = collections.Counter()
    for m in re.finditer(r'#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b', text):
        hx = norm(m.group(0))
        if not sat_ok(hx): continue
        ctx = text[max(0, m.start() - 160):m.start()].lower()
        w = 3 if re.search(r'(btn|button|cta|primary|accent|brand|header|nav|a:hover|\ba\s*\{|link)', ctx) else 1
        cnt[hx] += w
    for m in re.finditer(r'rgba?\((\d+),\s*(\d+),\s*(\d+)', text):
        hx = '#%02X%02X%02X' % tuple(int(x) for x in m.groups())
        if sat_ok(hx): cnt[hx] += 1
    print('theme-color:', theme.group(1) if theme else '-')
    for hx, n in cnt.most_common(8):
        print(hx, n)


if __name__ == '__main__':
    main(sys.argv[1])
