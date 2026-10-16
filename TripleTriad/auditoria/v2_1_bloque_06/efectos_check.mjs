import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import {spawn} from 'node:child_process';
const baseline=false;
const label='efectos';
const root=path.resolve('build/v2_1_auditoria/cartones-mazmorras/build/web');
const out=path.resolve('auditoria/v2_1_bloque_06');
const server=http.createServer((req,res)=>{
  if(req.url==='/embed-test.html'){
    res.writeHead(200,{'Content-Type':'text/html; charset=utf-8'});
    res.end('<!doctype html><html><body style="margin:0;background:#eee"><iframe id="game" src="/?auditar=1" allow="autoplay;fullscreen" style="display:block;margin:80px 64px;width:min(960px,calc(100vw - 128px));aspect-ratio:8/5;border:0"></iframe></body></html>');
    return;
  }
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
  const request=(method,params={})=>new Promise((resolve,reject)=>{const n=++id;pending.set(n,{resolve,reject});ws.send(JSON.stringify({id:n,method,params}));});
  const cdp=async(method,params={})=>{
    if(method==='Input.dispatchMouseEvent'){
      const offset=(await request('Runtime.evaluate',{expression:"(()=>{let r=document.getElementById('game').getBoundingClientRect();return {x:r.x,y:r.y}})()",returnByValue:true})).result.value;
      params={...params,x:params.x+offset.x,y:params.y+offset.y};
    }
    return request(method,params);
  };
  const evaluate=async expression=>(await cdp('Runtime.evaluate',{expression:`document.getElementById('game').contentWindow.eval(${JSON.stringify(expression)})`,returnByValue:true,awaitPromise:true})).result?.value;
  await cdp('Runtime.enable');await cdp('Page.enable');
  await cdp('Page.addScriptToEvaluateOnNewDocument',{source:"window.__startupLong=[];new PerformanceObserver(l=>window.__startupLong.push(...l.getEntries().map(e=>e.duration))).observe({type:'longtask',buffered:true});"});
  await cdp('Page.navigate',{url:'http://game.itch.zone:8765/embed-test.html'});
  await delay(12000);
  await cdp('Input.dispatchMouseEvent',{type:'mousePressed',x:640,y:400,button:'left',clickCount:1});
  await cdp('Input.dispatchMouseEvent',{type:'mouseReleased',x:640,y:400,button:'left',clickCount:1});
  await delay(15000);
  const key=async (key,number)=>{const code={27:'Escape',40:'ArrowDown',13:'Enter'}[number];await cdp('Input.dispatchKeyEvent',{type:'keyDown',key,code,windowsVirtualKeyCode:number});await cdp('Input.dispatchKeyEvent',{type:'keyUp',key,code,windowsVirtualKeyCode:number});await delay(1000);};
  await key('Escape',27);
  await key('Escape',27);
  await delay(4000);
  const phase=process.argv[2]||'antes';
  const evidence=path.join(out,'chrome',phase);
  fs.mkdirSync(evidence,{recursive:true});
  const fixture=fs.readFileSync(path.join(out,'fixture_web.py'),'utf8');
  await evaluate(`python.FS.writeFile('/tmp/tt_audit_fixture.py',${JSON.stringify(fixture)})`);
  const py=async code=>{await evaluate(`python.PyRun_SimpleString(${JSON.stringify(code)})`);await delay(50);};
  await py("import sys;sys.path.insert(0,'/tmp');import tt_audit_fixture as probe");
  const read=async()=>{await py('probe.inspect()');return evaluate('window.__ttAudit');};
  const tap=async(key,number,code)=>{
    await cdp('Input.dispatchKeyEvent',{type:'keyDown',key,code,windowsVirtualKeyCode:number});
    await cdp('Input.dispatchKeyEvent',{type:'keyUp',key,code,windowsVirtualKeyCode:number});
    await delay(120);
  };
  const click=async(x,y)=>{
    const p=await evaluate(`(()=>{let r=document.querySelector('canvas').getBoundingClientRect();return {x:r.x+r.width*${x}/1280,y:r.y+r.height*${y}/800}})()`);
    await cdp('Input.dispatchMouseEvent',{type:'mouseMoved',...p});
    await cdp('Input.dispatchMouseEvent',{type:'mousePressed',...p,button:'left',buttons:1,clickCount:1});
    await cdp('Input.dispatchMouseEvent',{type:'mouseReleased',...p,button:'left',buttons:0,clickCount:1});
    await delay(80);
  };
  const shot=async name=>{let s=await cdp('Page.captureScreenshot',{format:'png'});fs.writeFileSync(path.join(evidence,name+'.png'),Buffer.from(s.data,'base64'));};
  await click(450,303);await key('Enter',13);await key('Enter',13);await delay(1500);
  const results={phase,casos:{}};
  const prepare=async kind=>{await py(`probe.prepare(${JSON.stringify(kind)})`);return read();};
  const play=async()=>{let s=await read();if(!s?.mano?.length)throw Error('No hay mano para jugar');await click(...s.mano[0]);await click(640,378);};
  await prepare('same');await play();await delay(250);
  results.casos.same=await read();await shot('same');
  if(results.casos.same.efecto!=='SAME'||results.casos.same.capturas!==1)throw Error('Same no se resolvio');
  await tap('Escape',27,'Escape');await delay(2100);
  results.casos.pausa=await read();await shot('pausa');
  await tap('l',76,'KeyL');results.casos.historial_en_pausa=await read();
  for(let i=0;i<3;i++){const s=await read();if(!s.pausa&&!s.historial)break;await tap('Escape',27,'Escape');}
  results.casos.reanudado=await read();await shot('reanudado');
  await prepare('same');await play();await tap('l',76,'KeyL');await delay(2100);
  results.casos.historial=await read();await shot('historial');
  await tap('Escape',27,'Escape');results.casos.historial_cerrado=await read();await shot('historial_cerrado');
  await prepare('quema');await play();await delay(250);
  results.casos.quema=await read();await shot('quema');
  if(results.casos.quema.efecto!=='QUEMA'||results.casos.quema.capturas!==1)throw Error('Quema no se resolvio');
  await prepare('plus');await play();await delay(250);
  results.casos.plus=await read();await shot('plus');
  if(results.casos.plus.efecto!=='PLUS'||results.casos.plus.capturas!==1)throw Error('Plus no se resolvio');
  await prepare('cpu_same');await delay(350);results.casos.cpu_same=await read();await shot('cpu_same');
  if(results.casos.cpu_same.efecto!=='SAME')throw Error('El efecto del rival no aparece');
  await prepare('same');await tap('m',77,'KeyM');await play();await delay(250);
  results.casos.movimiento_reducido=await read();await shot('movimiento_reducido');
  await prepare('final_same');await play();await delay(250);
  results.casos.final_efecto=await read();await shot('final_efecto');
  await delay(2200);results.casos.final_resultado=await read();await shot('final_resultado');
  await delay(4000);
  results.diag=await evaluate('window.__ttDiag');
  results.music=await evaluate('window.__ttMusic?{paused:__ttMusic.paused,ready:__ttMusic.readyState,error:window.__ttMusicError}:null');
  results.runtime={prologoCondensado:await evaluate(`python.FS.readFile('/data/data/cartones-mazmorras/assets/prologo.py',{encoding:'utf8'}).includes('Armá diez cartas')`)};
  results.lectura=[];
  for(const scale of [1.25,1.6]){
    await py(`probe.lectura(${scale})`);
    const geometry=await evaluate('window.__ttLectura');
    if(geometry?.escala!==scale)throw Error('No se verifico la escala de lectura');
    await delay(600);await shot(`resultado_${scale}`);
    await prepare('same');await py(`probe.lectura(${scale})`);
    await tap('Escape',27,'Escape');await shot(`pausa_${scale}`);
    const paused=await read();if(!paused.pausa)throw Error('No se abrio la pausa ampliada');
    await tap('Escape',27,'Escape');
    results.lectura.push(geometry);
    await prepare('final_same');await play();await delay(2500);
  }
  await py('probe.lectura(1)');
  await prepare('cpu_final_same');await delay(350);
  results.casos.cpu_final_efecto=await read();await shot('cpu_final_efecto');
  if(!results.casos.cpu_final_efecto.fin||results.casos.cpu_final_efecto.efecto!=='SAME'||results.casos.cpu_final_efecto.tiempo_fin<=results.casos.cpu_final_efecto.ahora)throw Error('El ultimo Same del rival no precede la derrota');
  await delay(2400);results.casos.cpu_final_resultado=await read();await shot('cpu_final_resultado');
  results.hud=[];
  for(const scale of [1,1.25,1.6]){
    await py(`probe.hud(${scale})`);
    const hud=await evaluate('window.__ttHUD');
    if(hud?.escala!==scale||!hud.comentario_completo){
      fs.writeFileSync(path.join(out,'errores_hud.json'),JSON.stringify(messages,null,2));
      throw Error('Fallo del HUD ampliado');
    }
    await delay(300);await shot(`hud_${scale}`);results.hud.push(hud);
  }
  fs.writeFileSync(path.join(evidence,'resultados_web.json'),JSON.stringify(results,null,2));
  console.log(JSON.stringify(results));
  if(phase==='despues'){
    if(results.diag.fps<55)throw Error('El resultado estatico no alcanza el objetivo de 60 FPS');
    if(results.casos.historial_en_pausa.historial)throw Error('L abre historial durante pausa');
    if(results.casos.reanudado.efecto!=='SAME')throw Error('Se pierde el efecto al reanudar');
    if(results.casos.historial_cerrado.efecto!=='SAME')throw Error('Se pierde el efecto al cerrar historial');
    if(results.casos.final_efecto.tiempo_fin<=results.casos.final_efecto.ahora)throw Error('El resultado pisa el efecto final');
  }
  await cdp('Browser.close');
} finally {
  if(ws)ws.close();
  chrome.kill();server.close();
}
