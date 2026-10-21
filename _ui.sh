su -c 'uiautomator dump /data/local/tmp/u.xml >/dev/null 2>&1; dumpsys window 2>/dev/null | grep -m1 mCurrentFocus; cat /data/local/tmp/u.xml; rm -f /data/local/tmp/u.xml' </dev/null | python3 -c "
import sys,re
d=sys.stdin.read(); print(d.splitlines()[0][:120])
for m in re.finditer(r'<node [^>]*>',d):
  n=m.group(0); t=re.search(r' text=\"([^\"]*)\"',n).group(1); c=re.search(r'content-desc=\"([^\"]*)\"',n).group(1); b=re.search(r'bounds=\"([^\"]*)\"',n).group(1); k='C' if 'clickable=\"true\"' in n else ' '
  if t or c: print(k,b,(t or c)[:50])
"
