"""Мінімальний клієнт DevTools Protocol: headless Chrome не дає вікна вужчого
за 500 px, тож справжній телефон емулюється через Emulation.setDeviceMetricsOverride."""
import json,os,socket,base64,struct,subprocess,time,urllib.request,hashlib,os.path,sys
CH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

class WS:
    def __init__(self,url):
        u=url.split('://',1)[1]; hp,path=u.split('/',1); path='/'+path
        host,port=hp.split(':'); self.s=socket.create_connection((host,int(port)))
        k=base64.b64encode(os.urandom(16)).decode()
        self.s.sendall(("GET %s HTTP/1.1\r\nHost: %s\r\nUpgrade: websocket\r\n"
            "Connection: Upgrade\r\nSec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n\r\n"
            %(path,hp,k)).encode())
        buf=b''
        while b'\r\n\r\n' not in buf: buf+=self.s.recv(4096)
        self.buf=buf.split(b'\r\n\r\n',1)[1]; self.id=0
    def send(self,method,params=None,sid=None):
        self.id+=1
        msg={'id':self.id,'method':method,'params':params or {}}
        if sid: msg['sessionId']=sid
        d=json.dumps(msg).encode()
        h=b'\x81'
        n=len(d); mask=os.urandom(4)
        if n<126: h+=bytes([0x80|n])
        elif n<65536: h+=bytes([0x80|126])+struct.pack('>H',n)
        else: h+=bytes([0x80|127])+struct.pack('>Q',n)
        self.s.sendall(h+mask+bytes(b^mask[i%4] for i,b in enumerate(d)))
        return self.id
    def _read(self,n):
        while len(self.buf)<n:
            c=self.s.recv(65536)
            if not c: raise IOError('closed')
            self.buf+=c
        d,self.buf=self.buf[:n],self.buf[n:]; return d
    def recv(self):
        b0,b1=self._read(2); ln=b1&127
        if ln==126: ln=struct.unpack('>H',self._read(2))[0]
        elif ln==127: ln=struct.unpack('>Q',self._read(8))[0]
        return json.loads(self._read(ln))
    def call(self,method,params=None,sid=None,timeout=25):
        i=self.send(method,params,sid); t=time.time()
        while time.time()-t<timeout:
            m=self.recv()
            if m.get('id')==i: return m.get('result',m)
        raise TimeoutError(method)

def freeport():
    s=socket.socket(); s.bind(('127.0.0.1',0)); n=s.getsockname()[1]; s.close(); return n

def launch(port=None):
    port=port or freeport()
    p=subprocess.Popen([CH,'--headless=new','--disable-gpu','--no-first-run','--mute-audio',
        '--remote-debugging-port=%d'%port,'--window-size=1200,900','about:blank'],
        stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    for _ in range(80):
        try:
            j=json.load(urllib.request.urlopen('http://127.0.0.1:%d/json/version'%port))
            return p,j['webSocketDebuggerUrl']
        except Exception: time.sleep(0.25)
    raise RuntimeError('chrome не піднявся')

class Page:
    def __init__(self,port=None):
        self.proc,url=launch(port); self.ws=WS(url)
        t=self.ws.call('Target.createTarget',{'url':'about:blank'})['targetId']
        self.sid=self.ws.call('Target.attachToTarget',{'targetId':t,'flatten':True})['sessionId']
        self.ws.call('Page.enable',{},self.sid); self.ws.call('Runtime.enable',{},self.sid)
    def metrics(self,w,h,dpr=2,mobile=True):
        self.ws.call('Emulation.setDeviceMetricsOverride',
            {'width':w,'height':h,'deviceScaleFactor':dpr,'mobile':mobile},self.sid)
        self.ws.call('Emulation.setTouchEmulationEnabled',{'enabled':mobile,'maxTouchPoints':5},self.sid)
    def goto(self,url,wait=1.4):
        self.ws.call('Page.navigate',{'url':url},self.sid); time.sleep(wait)
    def js(self,expr):
        r=self.ws.call('Runtime.evaluate',
            {'expression':expr,'returnByValue':True,'awaitPromise':True},self.sid)
        return r.get('result',{}).get('value')
    def shot(self,path,full=False):
        r=self.ws.call('Page.captureScreenshot',{'format':'png','captureBeyondViewport':full},self.sid)
        open(path,'wb').write(base64.b64decode(r['data'])); return path
    def close(self):
        try:self.proc.terminate()
        except Exception:pass
