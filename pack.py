"""Packs the app code into site/data.txt (compressed + base64) so the Pages link shows no readable code and offers no .py download."""
import base64, json, os, zlib
FILES = ['slip_bridge.py', 'slip_kiosk_app.py']
for f in FILES:
    compile(open(f, encoding='utf-8').read(), f, 'exec')      # stop the deploy if the code has a syntax error
blob = zlib.compress(json.dumps({f: open(f, encoding='utf-8').read() for f in FILES}).encode('utf-8'), 9)
os.makedirs('site', exist_ok=True)
open('site/data.txt', 'w').write(base64.b64encode(blob).decode('ascii'))
open('site/index.html', 'w').write('<!DOCTYPE html><meta charset="utf-8"><title>OK</title>OK')
open('site/.nojekyll', 'w').close()
print('packed', os.path.getsize('site/data.txt'), 'bytes')
