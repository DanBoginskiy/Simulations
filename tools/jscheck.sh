#!/bin/sh
# Синтаксис ВЛАСНОГО скрипта файлу: останній <script> без id (KaTeX має id).
JSC=/System/Library/Frameworks/JavaScriptCore.framework/Versions/A/Helpers/jsc
bad=0
for f in "$@"; do
  python3 - "$f" <<'PY' > /tmp/own.js
import sys,re
s=open(sys.argv[1],encoding='utf-8').read()
m=[x for x in re.finditer(r'<script(?P<a>[^>]*)>(?P<b>.*?)</script>',s,re.S) if 'id=' not in x.group('a')]
print(m[-1].group('b') if m else '')
PY
  r=$("$JSC" -e "try{new Function(readFile('/tmp/own.js'));print('OK')}catch(e){print('ERR '+e)}")
  [ "$r" = OK ] || { echo "$(basename $f): $r"; bad=1; }
done
[ $bad = 0 ] && echo "синтаксис: усі $# OK"
