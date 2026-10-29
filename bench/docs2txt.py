import re, sys
from html.parser import HTMLParser
from pathlib import Path
class P(HTMLParser):
    def __init__(s): super().__init__(); s.out=[]; s.skip=0
    def handle_starttag(s,t,a):
        if t in('script','style','nav'): s.skip+=1
        if t in('p','div','br','li','dt','dd','h1','h2','h3','h4','pre','tr'): s.out.append('\n')
    def handle_endtag(s,t):
        if t in('script','style','nav'): s.skip-=1
    def handle_data(s,d):
        if not s.skip: s.out.append(d)
for h in Path(sys.argv[1]).glob('*.html'):
    p=P(); p.feed(h.read_text(errors='replace'))
    h.with_suffix('.txt').write_text(re.sub(r'\n\s*\n+','\n\n',''.join(p.out)))
