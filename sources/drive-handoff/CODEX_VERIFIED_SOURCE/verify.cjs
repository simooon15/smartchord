const {chromium,webkit}=require('playwright');
const fs=require('fs'),path=require('path'),assert=require('assert');
const root=__dirname,qa=path.join(root,'qa');fs.mkdirSync(qa,{recursive:true});
const url='file://'+path.join(root,'candidate.html');
(async()=>{
 const b=await chromium.launch({headless:true,channel:'chrome'}),p=await b.newPage({viewport:{width:1100,height:1000}}),errors=[],requests=[];
 p.on('pageerror',e=>errors.push(e.message));p.on('request',r=>{if(!r.url().startsWith('file:')&&!r.url().startsWith('data:'))requests.push(r.url())});await p.goto(url);await p.waitForFunction(()=>window.cangjie);
 assert.equal(await p.locator('[data-bar]').count(),93);assert.equal(await p.locator('.chord-foundation').count(),await p.evaluate(()=>cangjie.data.rows.reduce((n,r)=>n+r.chordChanges.length,0)));assert.equal(await p.locator('.sheet').count(),10);assert.equal(await p.locator('.sweep').count(),await p.evaluate(()=>cangjie.data.rows.reduce((n,r)=>n+r.events.filter(e=>['strum','arpeggio'].includes(e.technique)).length,0)));assert.equal(await p.locator('.event:has(.sweep) .fret').count(),0);
 await p.screenshot({path:path.join(qa,'desktop.png'),fullPage:false});
 const rhythmCheck=await p.evaluate(()=>{let first=document.querySelector('[data-bar="1"]'),dense=document.querySelector('[data-bar="67"]');return {first:[...first.querySelectorAll('.rhythm-beam')].map(b=>[Number(b.dataset.level),Number(b.dataset.from),Number(b.dataset.to),b.dataset.hook]),third:[...dense.querySelectorAll('.rhythm-beam[data-level="3"]')].map(b=>[Number(b.dataset.from),Number(b.dataset.to)]),old:document.querySelectorAll('.event .beam').length}});assert.deepEqual(rhythmCheck.first,[[1,0,.5,'false'],[1,1,1.5,'false'],[1,2,2.5,'false'],[1,3,3.75,'false'],[2,3,3.75,'false']]);assert.deepEqual(rhythmCheck.third,[[2.75,2.875]]);assert.equal(rhythmCheck.old,0);
 const data=await p.evaluate(()=>cangjie.data);assert.equal(data.sourceBars.length,67);assert.deepEqual(data.rows.map(r=>r.sourceBarNumber),[...Array.from({length:34},(_,i)=>i+1),...Array.from({length:26},(_,i)=>i+5),...Array.from({length:33},(_,i)=>i+35)]);
 for(const r of data.sourceBars){
  assert.equal(r.events[0].beat,0);assert(r.vocal.length);
  let last=0;for(const e of r.events){assert(e.beat>=0&&e.beat<4);assert(e.duration>0&&e.beat+e.duration<=4+1e-8);assert(e.beat>=last);last=e.beat;
   const used=new Set();for(const n of e.notes){assert(n.fret>=0&&n.fret<=17);assert(!used.has(n.string));used.add(n.string);assert.equal(n.pitchAfter,n.pitchBefore-3+12*n.octaveException);assert.equal(n.pitchAfter,[0,64,59,55,50,45,40][n.string]+n.fret+2);if(n.sourceSymbol==='×')assert.equal(n.sourceFret,data.shapes[e.chord][n.sourceString-1]);}
  }
  for(const v of r.vocal)if(v.degree)assert.equal(v.pitchAfter,v.pitchBefore-3);
 }
 // Independent, screenshot-read anchor notes, not derived from renderer.
 for(const [bar,t,s,f] of [[1,3.25,1,1],[1,3.75,2,3],[4,1,2,6],[4,2,2,1],[5,0,2,3],[7,2,6,3],[8,0,6,1],[33,2.5,2,0],[35,3.75,2,3],[38,3.5,3,5],[41,3.25,3,0],[51,2.25,2,5]]){
  const e=data.sourceBars[bar-1].events.find(e=>e.beat===t);assert(e.notes.some(n=>n.sourceString===s&&n.sourceFret===f),`anchor ${bar}:${t}:${s}:${f}`);
 }
 for(const n of [23,24,43,51,66])assert.equal(data.sourceBars[n-1].events.length,10);
 assert.equal(data.sourceBars[50].chordChanges[1][1],'F#m7/C#');
 await p.locator('#play').click();await p.waitForTimeout(350);assert((await p.evaluate(()=>cangjie.getState())).playing);assert((await p.evaluate(()=>cangjie.audioLog.length))>0);assert.equal(await p.evaluate(()=>cangjie.sampleErrors.length),0);assert((await p.evaluate(()=>cangjie.getDecodedSampleCount()))>=34);
 await p.locator('#play').click();const paused=await p.evaluate(()=>cangjie.getState());assert(!paused.playing);assert.equal(paused.voices,0);await p.waitForTimeout(250);assert.equal((await p.evaluate(()=>cangjie.getState())).position,paused.position);
 await p.locator('.fret').first().click();await p.waitForTimeout(50);assert((await p.evaluate(()=>cangjie.getState())).voices>0);await p.evaluate(()=>cangjie.pause());
 await p.locator('#bpm').fill('88');await p.locator('#bpm').dispatchEvent('input');assert.equal((await p.evaluate(()=>cangjie.getState())).bpm,88);
 await p.locator('#section').selectOption('77');assert.equal((await p.evaluate(()=>cangjie.getState())).position,304);
 await p.locator('#play').click();await p.waitForTimeout(100);await p.locator('#mode').selectOption('source');assert.equal((await p.evaluate(()=>cangjie.getState())).mode,'source');await p.evaluate(()=>cangjie.pause());
 await p.locator('#mode').selectOption('target');await p.locator('#section').selectOption('1');await p.locator('#loop').check();await p.evaluate(()=>cangjie.seek(15.85));await p.locator('#play').click();await p.waitForFunction(()=>cangjie.getState().playing);const loopGeneration=await p.evaluate(()=>cangjie.getState().generation);await p.waitForFunction(old=>{let s=cangjie.getState();return s.playing&&s.generation>=old+2&&s.position<16},loopGeneration,{timeout:5000});const loopState=await p.evaluate(()=>cangjie.getState());assert(loopState.playing);assert(loopState.position<16);await p.evaluate(()=>cangjie.pause());
 // Full performance offline audio through the actual synthesis path.
 await p.locator('#section').selectOption('all');await p.locator('#bpm').fill('76');await p.locator('#bpm').dispatchEvent('input');
 const samples=await p.evaluate(()=>cangjie.renderAudio(1,4));let buf=Buffer.alloc(samples.length*2+44);buf.write('RIFF',0);buf.writeUInt32LE(buf.length-8,4);buf.write('WAVEfmt ',8);buf.writeUInt32LE(16,16);buf.writeUInt16LE(1,20);buf.writeUInt16LE(1,22);buf.writeUInt32LE(44100,24);buf.writeUInt32LE(88200,28);buf.writeUInt16LE(2,32);buf.writeUInt16LE(16,34);buf.write('data',36);buf.writeUInt32LE(buf.length-44,40);samples.forEach((v,i)=>buf.writeInt16LE(Math.max(-32768,Math.min(32767,Math.round(v*32767))),44+2*i));fs.writeFileSync(path.join(qa,'intro.wav'),buf);
 assert(Math.max(...samples.slice(0,100000).map(Math.abs))>0.01);assert(samples.every(Number.isFinite));
 let printed=false;await p.evaluate(()=>window.print=()=>{window.printInvoked=true});await p.locator('#print').click();assert(await p.evaluate(()=>window.printInvoked));
 await p.emulateMedia({media:'print'});await p.pdf({path:path.join(qa,'proof.pdf'),preferCSSPageSize:true,printBackground:true});
 await p.emulateMedia({media:'screen'});await p.setViewportSize({width:390,height:844});await p.screenshot({path:path.join(qa,'mobile.png')});assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 const overflow=await p.evaluate(()=>[...document.querySelectorAll('.system')].every(e=>e.scrollWidth>e.clientWidth));assert(overflow);
 assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);await b.close();
 let webkitReport='';try{const w=await webkit.launch({headless:true}),q=await w.newPage({viewport:{width:390,height:844}}),we=[];q.on('pageerror',e=>we.push(e.message));await q.goto(url);await q.waitForFunction(()=>window.cangjie);await q.locator('#play').click();await q.waitForTimeout(600);assert((await q.evaluate(()=>cangjie.getState())).playing);await q.locator('#play').click();assert.equal((await q.evaluate(()=>cangjie.getState())).voices,0);assert.equal(await q.locator('[data-bar]').count(),93);assert.equal(await q.evaluate(()=>cangjie.sampleErrors.length),0);assert.deepEqual(we,[]);await q.screenshot({path:path.join(qa,'webkit.png')});await w.close();webkitReport='PASS';}catch(e){webkitReport=e.message;}
 fs.writeFileSync(path.join(qa,'results.json'),JSON.stringify({chromium:'PASS',webkit:webkitReport,printPages:10,sampleClips:data.sampleInfo.pitches.length,strumNotation:'cross-string arrows; zero picking digits in sweep events',measures:93,uniqueBars:67,octaveExceptions:data.octaveExceptions.length,unresolved:data.unresolved,networkRequests:requests,consoleErrors:errors},null,2));console.log('Chromium PASS; WebKit:',webkitReport);
})().catch(e=>{console.error(e);process.exit(1)});
