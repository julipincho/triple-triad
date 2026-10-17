import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import {spawn} from 'node:child_process';
const baseline=false;
const label='iframe';
const root=path.resolve('build/v2_1_auditoria/cartones-mazmorras/build/web');
const out=path.resolve('auditoria/rapidos_independientes_20261017/chrome');
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
  const pointerChecks=[];
  for(const [width,height,dpr] of [[1280,900,1],[800,900,1],[1440,1000,1.25],[1280,900,2]]){
    await cdp('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:dpr,mobile:false});
    await delay(800);
    for(const [x,y] of [[40,40],[450,303],[1200,750]]){
      const geometry=await evaluate(`(()=>{let c=document.querySelector('canvas'),r=c.getBoundingClientRect();return {x:r.x+r.width*${x}/1280,y:r.y+r.height*${y}/800,canvas:[c.width,c.height],rect:[r.x,r.y,r.width,r.height]}})()`);
      await cdp('Input.dispatchMouseEvent',{type:'mouseMoved',x:geometry.x,y:geometry.y});
      await delay(700);
      const diag=await evaluate('window.__ttDiag');
      pointerChecks.push({viewport:[width,height,dpr],expected:[x,y],geometry,diag});
    }
  }
  fs.writeFileSync(path.join(out,'puntero_iframe.json'),JSON.stringify(pointerChecks,null,2));
  if(pointerChecks.some(c=>!c.diag||Math.max(...c.expected.map((n,i)=>Math.abs(n-c.diag.puntero[i])))>2))throw Error('Puntero desalineado en iframe');
  console.log('Puntero:',JSON.stringify(pointerChecks.map(c=>({viewport:c.viewport,expected:c.expected,actual:c.diag?.puntero,event:c.diag?.evento,canvas:c.geometry.canvas}))));
  await cdp('Emulation.setDeviceMetricsOverride',{width:1280,height:800,deviceScaleFactor:1,mobile:false});
  await delay(1000);
  await cdp('Performance.enable');
  await evaluate(`window.__frames=[];window.__last=performance.now();window.__count=true;function measureFrame(t){if(!window.__count)return;window.__frames.push(t-window.__last);window.__last=t;requestAnimationFrame(measureFrame)}requestAnimationFrame(measureFrame);window.__long=[];window.__observer=new PerformanceObserver(list=>window.__long.push(...list.getEntries().map(e=>e.duration)));window.__observer.observe({type:'longtask',buffered:false});`);
  const metricBefore=await cdp('Performance.getMetrics');
  const musicBefore=await evaluate(`window.__ttMusic?({time:window.__ttMusic.currentTime,paused:window.__ttMusic.paused,ready:window.__ttMusic.readyState,error:window.__ttMusicError}):null`);
  await delay(10000);
  const menuDiag=await evaluate('window.__ttDiag');
  const click=async(x,y)=>{
    const p=await evaluate(`(()=>{let r=document.querySelector('canvas').getBoundingClientRect();return {x:r.x+r.width*${x}/1280,y:r.y+r.height*${y}/800}})()`);
    await cdp('Input.dispatchMouseEvent',{type:'mouseMoved',...p});
    await cdp('Input.dispatchMouseEvent',{type:'mousePressed',...p,button:'left',buttons:1,clickCount:1});
    await cdp('Input.dispatchMouseEvent',{type:'mouseReleased',...p,button:'left',buttons:0,clickCount:1});
    await delay(1200);
  };
  const fixture=fs.readFileSync(path.resolve('auditoria/rapidos_independientes_20261017/probe.py'),'utf8');
  await evaluate(`python.FS.writeFile('/tmp/rapidos_probe.py',${JSON.stringify(fixture)})`);
  const probe=async()=>{
    await evaluate(`python.PyRun_SimpleString("import sys;sys.path.insert(0,'/tmp');import rapidos_probe;rapidos_probe.inspect()")`);
    return evaluate('window.__ttRapidos');
  };
  const before=await probe();
  if(!before||Object.keys(before.coleccion).length||before.mazo.length||before.campana)throw Error('El perfil inicial no esta vacio');
  await click(450,369);
  const collectionShot=await cdp('Page.captureScreenshot',{format:'png'});
  fs.writeFileSync(path.join(out,'coleccion_iframe.png'),Buffer.from(collectionShot.data,'base64'));
  await key('Escape',27);
  const point=await evaluate(`(()=>{let r=document.querySelector('canvas').getBoundingClientRect();return {x:r.x+r.width*450/1280,y:r.y+r.height*303/800}})()`);
  await cdp('Input.dispatchMouseEvent',{type:'mouseMoved',...point});
  await cdp('Input.dispatchMouseEvent',{type:'mousePressed',...point,button:'left',clickCount:1});
  await cdp('Input.dispatchMouseEvent',{type:'mouseReleased',...point,button:'left',clickCount:1});
  await delay(1000);
  let selector=await cdp('Page.captureScreenshot',{format:'png'});
  fs.writeFileSync(path.join(out,'elegir_mazo.png'),Buffer.from(selector.data,'base64'));
  await key('Enter',13);
  selector=await cdp('Page.captureScreenshot',{format:'png'});
  fs.writeFileSync(path.join(out,'elegir_rival.png'),Buffer.from(selector.data,'base64'));
  await key('Enter',13);
  const started=await probe();
  if(!started?.juego||started.juego.mano_u.length!==5||started.juego.mano_c.length!==5)throw Error('No se repartieron las manos prestadas');
  await delay(10000);
  const duelDiag=await evaluate('window.__ttDiag');
  const geometry=await evaluate(`(()=>{let r=document.querySelector('canvas').getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height}})()`);
  const pointAt=(x,y)=>({x:geometry.x+x*geometry.w/1280,y:geometry.y+y*geometry.h/800});
  await cdp('Input.dispatchMouseEvent',{type:'mouseMoved',...pointAt(400,710)});
  await cdp('Input.dispatchMouseEvent',{type:'mousePressed',...pointAt(400,710),button:'left',buttons:1,clickCount:1});
  for(let i=1;i<=8;i++){await cdp('Input.dispatchMouseEvent',{type:'mouseMoved',...pointAt(400+(524-400)*i/8,710+(222-710)*i/8),button:'left',buttons:1});await delay(60);}
  await cdp('Input.dispatchMouseEvent',{type:'mouseReleased',...pointAt(524,222),button:'left',buttons:0,clickCount:1});
  await delay(3000);
  const dragDiag=await evaluate('window.__ttDiag');
  const dragged=await probe();
  if(!dragged?.juego||dragged.juego.jugadas<1)throw Error('El arrastre no coloco una carta');
  const dragShot=await cdp('Page.captureScreenshot',{format:'png'});
  fs.writeFileSync(path.join(out,'arrastre_iframe.png'),Buffer.from(dragShot.data,'base64'));
  const metricAfter=await cdp('Performance.getMetrics');
  const perf=await evaluate(`(()=>{window.__count=false;window.__observer.disconnect();let f=window.__frames.slice().sort((a,b)=>a-b);return {frames:f.length,mean:f.reduce((a,b)=>a+b,0)/f.length,p95:f[Math.floor(f.length*.95)],max:f[f.length-1],longTasks:window.__long,music:window.__ttMusic?({time:window.__ttMusic.currentTime,paused:window.__ttMusic.paused,ready:window.__ttMusic.readyState,error:window.__ttMusicError}):null}})()`);
  const duelShot=await cdp('Page.captureScreenshot',{format:'png'});
  fs.writeFileSync(path.join(out,'duelo_'+label+'.png'),Buffer.from(duelShot.data,'base64'));
  if(!baseline){
    for(let i=0;i<35;i++){
      const context=await evaluate('window.__ttDiag?.contexto');
      if(context==='menú principal')break;
      await key('Enter',13);
    }
    await delay(1000);
    if(await evaluate('window.__ttDiag?.contexto')!=='menú principal')throw Error('El duelo no regreso al menu');
  }
  const finish=await evaluate(`({music:window.__ttMusic?{time:window.__ttMusic.currentTime,paused:window.__ttMusic.paused,ready:window.__ttMusic.readyState,error:window.__ttMusicError}:null,startupLong:window.__startupLong})`);
  const after=await probe();
  if(!after||JSON.stringify(after.coleccion)!==JSON.stringify(before.coleccion)||JSON.stringify(after.mazo)!==JSON.stringify(before.mazo)||after.campana)throw Error('El rapido altero la coleccion o creo una campana');
  fs.writeFileSync(path.join(out,'aislamiento.json'),JSON.stringify({before,started,dragged,after},null,2));
  const state=await evaluate(`({title:document.title,host:location.host,canvas:!!document.querySelector('canvas'),version:window.python.FS.readFile('/data/data/cartones-mazmorras/assets/version.py',{encoding:'utf8'}).match(/VERSION = "([^"]+)"/)[1],arteNuevo:window.python.FS.analyzePath('/data/data/cartones-mazmorras/assets/assets/lotes_visuales/migracion_20261015/retratos/duelista_gorra.png').exists})`);
  const shot=await cdp('Page.captureScreenshot',{format:'png'});
  fs.writeFileSync(path.join(out,'perf_'+label+'.png'),Buffer.from(shot.data,'base64'));
  fs.writeFileSync(path.join(out,'perf_'+label+'.json'),JSON.stringify({state,messages,perf,musicBefore,metricBefore,metricAfter,finish,menuDiag,duelDiag,dragDiag},null,2));
  console.log(JSON.stringify({state,menuDiag,duelDiag,musicBefore,finish}));
  if(state.version!=='2.0'||!state.arteNuevo)throw Error('El navegador no cargo la version 2.0 con el arte actual');
  if(menuDiag.fps<55||duelDiag.fps<55)throw Error('No se alcanza el objetivo de 60 FPS en iframe');
  await cdp('Browser.close');
} finally {
  if(ws)ws.close();
  chrome.kill();server.close();
}
