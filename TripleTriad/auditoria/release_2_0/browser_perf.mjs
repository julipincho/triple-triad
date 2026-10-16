import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import {spawn} from 'node:child_process';
const baseline=process.argv.includes('--baseline');
const label=baseline?'baseline':'r1';
const root=path.resolve(baseline?'build/release_2_0/cartones-mazmorras/build/web':'build/release_2_0_web_r1/cartones-mazmorras/build/web');
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
  await cdp('Page.addScriptToEvaluateOnNewDocument',{source:"window.__startupLong=[];new PerformanceObserver(l=>window.__startupLong.push(...l.getEntries().map(e=>e.duration))).observe({type:'longtask',buffered:true});"});
  await cdp('Page.navigate',{url:'http://game.itch.zone:8765/'});
  await delay(12000);
  await cdp('Input.dispatchMouseEvent',{type:'mousePressed',x:640,y:400,button:'left',clickCount:1});
  await cdp('Input.dispatchMouseEvent',{type:'mouseReleased',x:640,y:400,button:'left',clickCount:1});
  await delay(15000);
  const key=async (key,number)=>{const code={27:'Escape',40:'ArrowDown',13:'Enter'}[number];await cdp('Input.dispatchKeyEvent',{type:'keyDown',key,code,windowsVirtualKeyCode:number});await cdp('Input.dispatchKeyEvent',{type:'keyUp',key,code,windowsVirtualKeyCode:number});await delay(1000);};
  await key('Escape',27);
  await key('Escape',27);
  await cdp('Performance.enable');
  await evaluate(`window.__frames=[];window.__last=performance.now();window.__count=true;function measureFrame(t){if(!window.__count)return;window.__frames.push(t-window.__last);window.__last=t;requestAnimationFrame(measureFrame)}requestAnimationFrame(measureFrame);window.__long=[];window.__observer=new PerformanceObserver(list=>window.__long.push(...list.getEntries().map(e=>e.duration)));window.__observer.observe({type:'longtask',buffered:false});`);
  const metricBefore=await cdp('Performance.getMetrics');
  const musicBefore=await evaluate(`window.__ttMusic?({time:window.__ttMusic.currentTime,paused:window.__ttMusic.paused,ready:window.__ttMusic.readyState,error:window.__ttMusicError}):null`);
  await delay(10000);
  const point=await evaluate(`(()=>{let r=document.querySelector('canvas').getBoundingClientRect();return {x:r.x+r.width*450/1280,y:r.y+r.height*303/800}})()`);
  await cdp('Input.dispatchMouseEvent',{type:'mouseMoved',...point});
  await cdp('Input.dispatchMouseEvent',{type:'mousePressed',...point,button:'left',clickCount:1});
  await cdp('Input.dispatchMouseEvent',{type:'mouseReleased',...point,button:'left',clickCount:1});
  await delay(1000);await key('Enter',13);await key('Enter',13);
  await delay(10000);
  const metricAfter=await cdp('Performance.getMetrics');
  const perf=await evaluate(`(()=>{window.__count=false;window.__observer.disconnect();let f=window.__frames.slice().sort((a,b)=>a-b);return {frames:f.length,mean:f.reduce((a,b)=>a+b,0)/f.length,p95:f[Math.floor(f.length*.95)],max:f[f.length-1],longTasks:window.__long,music:window.__ttMusic?({time:window.__ttMusic.currentTime,paused:window.__ttMusic.paused,ready:window.__ttMusic.readyState,error:window.__ttMusicError}):null}})()`);
  const duelShot=await cdp('Page.captureScreenshot',{format:'png'});
  fs.writeFileSync(path.join(out,'duelo_'+label+'.png'),Buffer.from(duelShot.data,'base64'));
  if(!baseline){for(let i=0;i<11;i++)await key('Enter',13);await delay(2000);}
  const finish=await evaluate(`({music:window.__ttMusic?{time:window.__ttMusic.currentTime,paused:window.__ttMusic.paused,ready:window.__ttMusic.readyState,error:window.__ttMusicError}:null,startupLong:window.__startupLong})`);
  const state=await evaluate(`({title:document.title,host:location.host,canvas:!!document.querySelector('canvas'),version:window.python.FS.readFile('/data/data/cartones-mazmorras/assets/version.py',{encoding:'utf8'}).match(/VERSION = "([^"]+)"/)[1],arteNuevo:window.python.FS.analyzePath('/data/data/cartones-mazmorras/assets/assets/lotes_visuales/migracion_20261015/retratos/duelista_gorra.png').exists})`);
  const shot=await cdp('Page.captureScreenshot',{format:'png'});
  fs.writeFileSync(path.join(out,'perf_'+label+'.png'),Buffer.from(shot.data,'base64'));
  fs.writeFileSync(path.join(out,'perf_'+label+'.json'),JSON.stringify({state,messages,perf,musicBefore,metricBefore,metricAfter,finish},null,2));
  console.log(JSON.stringify({state,perf,musicBefore,finish}));
  if(state.version!=='2.0'||!state.arteNuevo)throw Error('El navegador no cargo la version 2.0 con el arte actual');
  await cdp('Browser.close');
} finally {
  if(ws)ws.close();
  chrome.kill();server.close();
}
