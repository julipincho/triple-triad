import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import {spawn} from 'node:child_process';
const root=path.resolve('build/release_2_0/cartones-mazmorras/build/web');
const out=path.resolve('auditoria/release_2_0');
const server=http.createServer((req,res)=>{
  const p=path.resolve(root,'.'+decodeURIComponent(req.url.split('?')[0]));
  const file=p===root?path.join(root,'index.html'):p;
  if(!file.startsWith(root+path.sep)||!fs.existsSync(file)){res.writeHead(404);res.end();return;}
  const types={'.html':'text/html; charset=utf-8','.js':'text/javascript','.apk':'application/zip','.png':'image/png','.gz':'application/gzip'};
  res.writeHead(200,{'Content-Type':types[path.extname(file)]||'application/octet-stream'});
  fs.createReadStream(file).pipe(res);
});
await new Promise(resolve=>server.listen(8765,'127.0.0.1',resolve));
const profile=fs.mkdtempSync(path.join(os.tmpdir(),'tt_browser_2_0_'));
const chrome=spawn('C:/Program Files/Google/Chrome/Application/chrome.exe',[
  '--headless=new','--no-first-run','--no-default-browser-check','--no-proxy-server',
  '--autoplay-policy=no-user-gesture-required','--remote-debugging-port=9225',
  '--host-resolver-rules=MAP game.itch.zone 127.0.0.1',`--user-data-dir=${profile}`,
  '--window-size=1280,900','about:blank'],{windowsHide:true,stdio:'ignore'});
const delay=ms=>new Promise(r=>setTimeout(r,ms));
let ws;
const messages=[];
try {
  let target;
  for(let i=0;i<50;i++){
    try{target=(await(await fetch('http://127.0.0.1:9225/json')).json()).find(x=>x.type==='page');if(target)break;}catch{}
    await delay(200);
  }
  if(!target)throw Error('Chrome no abrio el puerto de diagnostico');
  ws=new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject;});
  let id=0;
  const pending=new Map();
  ws.onmessage=({data})=>{
    const m=JSON.parse(data);
    if(m.id){const p=pending.get(m.id);if(p){pending.delete(m.id);m.error?p.reject(m.error):p.resolve(m.result);}}
    else if(m.method==='Runtime.consoleAPICalled'||m.method==='Runtime.exceptionThrown')messages.push(m);
  };
  const cdp=(method,params={})=>new Promise((resolve,reject)=>{const n=++id;pending.set(n,{resolve,reject});ws.send(JSON.stringify({id:n,method,params}));});
  const evaluate=async expression=>(await cdp('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true})).result?.value;
  await cdp('Runtime.enable');await cdp('Page.enable');
  await cdp('Page.navigate',{url:'http://game.itch.zone:8765/'});
  await delay(12000);
  await cdp('Input.dispatchMouseEvent',{type:'mousePressed',x:640,y:400,button:'left',clickCount:1});
  await cdp('Input.dispatchMouseEvent',{type:'mouseReleased',x:640,y:400,button:'left',clickCount:1});
  await delay(15000);
  const state=await evaluate(`({title:document.title,host:location.host,canvas:!!document.querySelector('canvas'),version:window.python.FS.readFile('/data/data/cartones-mazmorras/assets/version.py',{encoding:'utf8'}).match(/VERSION = "([^"]+)"/)[1],arteNuevo:window.python.FS.analyzePath('/data/data/cartones-mazmorras/assets/assets/lotes_visuales/migracion_20261015/retratos/duelista_gorra.png').exists})`);
  const shot=await cdp('Page.captureScreenshot',{format:'png'});
  fs.writeFileSync(path.join(out,'navegador.png'),Buffer.from(shot.data,'base64'));
  fs.writeFileSync(path.join(out,'navegador.json'),JSON.stringify({state,messages},null,2));
  console.log(JSON.stringify(state));
  if(state.version!=='2.0'||!state.arteNuevo)throw Error('El navegador no cargo la version 2.0 con el arte actual');
  await cdp('Browser.close');
} finally {
  if(ws)ws.close();
  chrome.kill();server.close();
}
