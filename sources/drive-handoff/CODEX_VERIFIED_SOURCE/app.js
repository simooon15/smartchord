'use strict';
const DATA=JSON.parse(document.querySelector('#score-data').textContent),rows=DATA.rows;
const $=s=>document.querySelector(s),NS='http://www.w3.org/2000/svg',O=[0,64,59,55,50,45,40];
let mode='target',bpm=76,position=0,playing=false,loop=false,follow=true,section='all';
let playbackRequest=0;
let ctx=null,bus=null,voices=new Set(),timer=null,frame=null,anchorBeat=0,anchorTime=0,next=0,timeline=[],generation=0,lastBar=-1;
const audioLog=[];let clickTrack=false;
function el(tag,a={},t){let n=document.createElementNS(NS,tag);for(const [k,v] of Object.entries(a))n.setAttribute(k,v);if(t!==undefined)n.textContent=t;return n}
function txt(p,x,y,t,cls,a={}){let n=el('text',{x,y,class:cls,...a},t);p.append(n);return n}
function line(p,x1,y1,x2,y2,cls){p.append(el('line',{x1,y1,x2,y2,class:cls}))}
const freq=m=>440*2**((m-69)/12),fmt=s=>`${Math.floor(s/60)}:${String(Math.floor(s%60)).padStart(2,'0')}`;
const sections=[{id:'all',name:'整首',start:0,end:rows.length*4}];
for(const r of rows){let s=sections.at(-1);if(s.id==='all'||s.name!==r.section)sections.push({id:String(r.i),name:r.section,start:(r.i-1)*4,end:r.i*4});else s.end=r.i*4}
function range(){let s=sections.find(s=>s.id===section);return[s.start,s.end]}
function midi(n){return mode==='target'?n.pitchAfter:n.pitchBefore}
function viewNote(n){return mode==='target'?{s:n.string,f:n.fret}:{s:n.sourceString,f:n.sourceFret}}
function activeChord(r,t){return [...r.chordChanges].reverse().find(c=>c[0]<=t)[1]}
function label(c){return mode==='target'?DATA.transposition[c]:c}
function key(r){return mode==='target'?(r.sourceBarNumber>=51?'A 指法 · 实际 B 调':'G 指法 · 实际 A 调'):(r.sourceBarNumber>=51?'D 调 · 不夹':'C 调 · 不夹')}
// Low-position foundation shapes, string 6 → 1. Melody changes remain in the tab.
const easyShapes={
 'G':[3,2,0,0,0,3],'G/F':[1,null,0,0,0,3],'Em':[0,2,2,0,0,0],
 'Ebmaj7':[null,null,1,3,3,3],'D':[null,null,0,2,3,2],
 'Gmaj7':[3,2,0,0,0,2],'Em7':[0,2,0,0,0,0],'Em7/D':[null,null,0,0,0,0],
 'Cmaj7':[null,3,2,0,0,0],'C':[null,3,2,0,1,0],'Dsus4':[null,null,0,2,3,3],
 'D7':[null,null,0,2,1,2],'Bm7/F#':[2,null,0,2,0,2],'Dm7':[null,null,0,2,1,1],
 'G7':[3,2,0,0,0,1],'G/B':[null,2,0,0,0,3],'Am7':[null,0,2,0,1,0],
 'F':[null,null,3,2,1,1],'A':[null,0,2,2,2,0],'C#m7/G#':[4,null,2,4,2,0],
 'F#m7':[2,null,2,2,2,0],'A/C#':[null,4,2,2,2,0],'Bm7':[null,2,0,2,0,2],
 'E':[0,2,2,1,0,0],'E/G#':[4,null,2,1,0,0],'A7':[null,0,2,0,2,0]
};
function foundationShape(c){return mode==='target'?easyShapes[label(c)]:[...DATA.shapes[c]].reverse()}
function foundationDiagram(c,x,y){
 const shape=foundationShape(c),g=el('g',{class:'chord-foundation',transform:`translate(${x},${y})`,'data-chord':label(c),'data-shape':JSON.stringify(shape),role:'img','aria-label':label(c)+' 基础指法，六至一弦 '+shape.map(f=>f===null?'不弹':f+'品').join('、')});
 g.append(el('title',{},'基础按法：旋律变化按六线谱；扫弦具体按法查箭头编号。'));
 const positive=shape.filter(f=>f>0),base=Math.max(...positive,0)<=4?1:Math.min(...positive),span=Math.max(4,Math.max(...positive,0)-base+1),dy=42/span;
 if(base>1)txt(g,0,29,base+'fr','foundation-fret');
 for(let i=0;i<6;i++)line(g,12+i*9,18,12+i*9,60,'diagram-string');
 for(let i=0;i<=span;i++)line(g,12,18+i*dy,57,18+i*dy,i===0&&base===1?'diagram-nut':'diagram-string');
 shape.forEach((f,i)=>{const xx=12+i*9;if(f===null||f===0)txt(g,xx,12,f===0?'○':'×','foundation-open',{'text-anchor':'middle'});else g.append(el('circle',{cx:xx,cy:18+(f-base+.5)*dy,r:3.1,class:'diagram-dot'}))});
 return g;
}

let voicingMap=new Map(),voicingList=[];
function voicingKey(e){return label(e.chord)+':'+e.notes.map(n=>viewNote(n)).sort((a,b)=>a.s-b.s).map(n=>n.s+'='+n.f).join(',')}
function prepareVoicings(){voicingMap=new Map();voicingList=[];for(const r of rows)for(const e of r.events)if(['strum','arpeggio'].includes(e.technique)){let k=voicingKey(e);if(!voicingMap.has(k)){let item={id:voicingList.length+1,chord:label(e.chord),notes:e.notes.map(viewNote),oct:mode==='target'&&e.notes.some(n=>n.octaveException)};voicingMap.set(k,item);voicingList.push(item)}}}
function voicingDiagram(v){let svg=el('svg',{viewBox:'0 0 150 142',class:'voicing-diagram',role:'img','aria-label':v.chord+' 指法 '+v.id});txt(svg,75,14,String(v.id).padStart(2,'0')+' · '+v.chord,'diagram-title',{'text-anchor':'middle'});const sh=new Map(v.notes.map(n=>[n.s,n.f])),frets=v.notes.filter(n=>n.f>0).map(n=>n.f);let min=Math.min(...frets,99);const base=Math.max(...frets,0)<=4?1:min;txt(svg,11,55,String(base),'diagram-fret');for(let i=0;i<6;i++)line(svg,30+i*18,40,30+i*18,120,'diagram-string');for(let f=0;f<=4;f++)line(svg,30,40+f*20,120,40+f*20,f===0&&base===1?'diagram-nut':'diagram-string');for(let st=6;st>=1;st--){let x=30+(6-st)*18,f=sh.get(st);if(f===undefined||f===0)txt(svg,x,33,f===0?'○':'×','diagram-open',{'text-anchor':'middle'});else svg.append(el('circle',{cx:x,cy:40+(f-base+.5)*20,r:5,class:'diagram-dot'}));txt(svg,x,137,f===undefined?'–':String(f),'diagram-fret',{'text-anchor':'middle'})}return svg}
function sweepGlyph(es,e,x){let ns=e.notes.map(viewNote),lo=Math.max(...ns.map(n=>n.s)),hi=Math.min(...ns.map(n=>n.s)),top=72+(hi-1)*15-6,bottom=72+(lo-1)*15+3,up=e.direction==='up',tip=up?bottom:top,base=up?top:bottom,id=voicingMap.get(voicingKey(e)).id;
 let path='M '+x+' '+base+' L '+x+' '+tip;
 if(e.technique==='arpeggio'){path='M '+x+' '+base;let direction=tip>base?1:-1;for(let y=base+direction*5;direction>0?y<tip:y>tip;y+=direction*5)path+=' L '+(x+(Math.round(Math.abs(y-base)/5)%2?3:-3))+' '+y;path+=' L '+x+' '+tip;}
 let head=up?`M ${x-5} ${tip-9} L ${x} ${tip} L ${x+5} ${tip-9}`:`M ${x-5} ${tip+9} L ${x} ${tip} L ${x+5} ${tip+9}`;
 let g=el('g',{class:'sweep',role:'button',tabindex:0,'aria-label':label(e.chord)+(up?'上扫':'下扫')+'，指法 '+id,'data-low-string':lo,'data-high-string':hi});g.append(el('rect',{x:x-10,y:top-8,width:20,height:bottom-top+16,fill:'transparent'}));g.append(el('path',{d:path+' '+head,class:'sweep-line'}));g.append(el('title',{},'指法 '+id+' · '+label(e.chord)+' · '+ns.sort((a,b)=>b.s-a.s).map(n=>n.s+'弦'+n.f+'品').join(' / ')));txt(g,x+9,tip+(up?-2:1),String(id),'voicing-ref');g.addEventListener('click',ev=>{ev.stopPropagation();previewEvent(e)});g.addEventListener('keydown',ev=>{if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();previewEvent(e)}});es.append(g);
}
function renderRhythm(parent,r,xx){
 const plan=RhythmNotation.plan(r.events,r.meter,r.beamGroups),layer=el('g',{class:'rhythm-layer','pointer-events':'none'});parent.append(layer);
 plan.specs.forEach((spec,i)=>{const e=r.events[i],x=xx(e.beat),g=parent.querySelector(`[data-event="${r.i}:${e.beat}"]`);g.setAttribute('data-beam-levels',spec.levels);g.setAttribute('data-dots',spec.dots);g.setAttribute('data-duration',e.duration);if(e.technique==='rest')return;
  if(spec.stem)line(layer,x,153,x,174,'stem');for(let dot=0;dot<spec.dots;dot++)txt(layer,x+7+dot*5,162,'·','dot');
 });
 for(const beam of plan.beams){let x1=xx(r.events[beam.from].beat),x2=beam.hook?x1+beam.direction*Math.min(7,Math.abs(xx(r.events[beam.neighbor].beat)-x1)*.42):xx(r.events[beam.to].beat),y=174-(beam.level-1)*5;
  layer.append(el('line',{x1,y1:y,x2,y2:y,class:'beam rhythm-beam','data-level':beam.level,'data-from':r.events[beam.from].beat,'data-to':r.events[beam.to].beat,'data-hook':beam.hook}));
 }
 for(const flag of plan.flags){const x=xx(r.events[flag.index].beat);for(let level=1;level<=flag.levels;level++){let y=174-(level-1)*5;layer.append(el('path',{d:`M ${x} ${y} C ${x-9} ${y-2}, ${x-9} ${y-10}, ${x-4} ${y-15}`,class:'rhythm-flag','data-level':level,'data-beat':r.events[flag.index].beat}));}}
}

function renderSystem(list){
 const W=760,H=250,svg=el('svg',{viewBox:`0 0 ${W} ${H}`,class:'staff',role:'group','aria-label':`演奏第${list[0].i}至${list.at(-1).i}小节`});
 for(let k=0;k<list.length;k++){
  const stride=list.length===3?240:365,barWidth=stride-10,beatWidth=(barWidth-27)/4;let r=list[k],x0=30+k*stride,xx=t=>x0+15+t*beatWidth,ys=s=>72+(s-1)*15;
  let g=el('g',{'data-bar':r.i,'data-first-x':xx(0),'data-beat-width':beatWidth,transform:'translate(0,23)'});svg.append(g);
  g.append(el('rect',{x:x0,y:-8,width:barWidth,height:229,class:'bar-shade'}));
  txt(g,x0,-11,`${r.i} · 原谱 ${r.sourceBarNumber}${r.pass===2?' / 二遍':''}`,'bar-number');
  if(r.i===1||rows[r.i-2]?.section!==r.section)txt(g,x0+barWidth-5,-11,r.section+(r.sourceBarNumber===51?(mode==='target'?' · 1=A / 实际 B':' · 1=D / 不夹'):''),'section-tag',{'text-anchor':'end'});
  r.chordChanges.forEach(([t,c])=>{const center=Math.min(xx(t)+14,x0+barWidth-25);txt(g,center,9,label(c),'chord',{'text-anchor':'middle'});let chart=foundationDiagram(c,0,0);chart.setAttribute('transform',`translate(${center-24.15},10) scale(.7)`);g.append(chart);});
  if(k===0)for(let s=1;s<=6;s++)txt(g,x0-14,ys(s)+4,['','e','B','G','D','A','E'][s],'string-label',{'text-anchor':'middle'});
  for(let s=1;s<=6;s++)line(g,x0,ys(s),x0+barWidth,ys(s),'string-line');
  line(g,x0,72,x0,147,'barline');line(g,x0+barWidth,72,x0+barWidth,147,'barline');
  if(r.i===93)line(g,x0+barWidth-4,72,x0+barWidth-4,147,'final-barline');
  for(const e of r.events){
   const x=xx(e.beat),es=el('g',{'data-event':`${r.i}:${e.beat}`,class:'event','data-beat':e.beat});g.append(es);
   if(e.technique==='slap'){let mark=txt(es,x,147,'⊠','slap-mark',{'text-anchor':'middle',role:'button',tabindex:0,'aria-label':'拍弦试听'});mark.append(el('title',{},'拍弦：右手拍击琴弦，短促打击声，无确定音高'));mark.addEventListener('click',ev=>{ev.stopPropagation();previewEvent(e)});mark.addEventListener('keydown',ev=>{if(ev.key==='Enter')previewEvent(e)});}
   for(const n of (['strum','arpeggio'].includes(e.technique)?[]:e.notes)){
    const {s,f}=viewNote(n);let nt=txt(es,x,ys(s),String(f),'fret'+(mode==='target'&&n.octaveException?' octave':''),{'text-anchor':'middle','dominant-baseline':'central',role:'button',tabindex:0,'aria-label':`${s}弦${f}品，${Math.round(freq(midi(n)))}赫兹`});
    const title=el('title',{},`原谱 ${n.sourceString}弦${n.sourceFret}品 (${n.pitchBefore}) → ${s}弦${f}品，实际 MIDI ${midi(n)}${n.octaveException?'；八度调整 '+(n.octaveException>0?'+':'')+n.octaveException:''}`);nt.append(title);
    nt.addEventListener('click',ev=>{ev.stopPropagation();preview([n])});nt.addEventListener('keydown',ev=>{if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();preview([n])}});
   }
   if(e.technique==='strum'||e.technique==='arpeggio')sweepGlyph(es,e,x);
   if(e.tie)txt(es,x,160,'⌒','tie',{'text-anchor':'middle'});
   if(e.technique==='pull-off')txt(es,x,160,'P','technique');
  }
  renderRhythm(g,r,xx);
  for(const v of r.vocal){let x=xx(v.beat);let t=v.degree===null?'—':String(v.degree);txt(g,x,195,t,'jianpu',{'text-anchor':'middle'});
   if(v.degree){for(let j=0;j<Math.abs(v.octave);j++)txt(g,x,v.octave>0?185-j*4:200+j*4,'·','vocal-dot',{'text-anchor':'middle'});}
   const value=RhythmNotation.value(v);for(let level=0;level<value.levels;level++)line(g,x-5,200+level*3,x+5,200+level*3,'vocal-beam');for(let dot=0;dot<value.dots;dot++)txt(g,x+7+dot*5,195,'·','dot');
   if(v.lyric)txt(g,x,222,v.lyric,'lyric',{'text-anchor':'middle'});
  }
  let cursor=el('line',{x1:xx(0),x2:xx(0),y1:50,y2:177,class:'cursor','data-cursor':r.i});g.append(cursor);
  g.addEventListener('click',ev=>{if(ev.target.closest('.fret')||ev.target.classList.contains('arrow'))return;const p=svg.createSVGPoint();p.x=ev.clientX;p.y=ev.clientY;const local=p.matrixTransform(svg.getScreenCTM().inverse());seek((r.i-1)*4+Math.max(0,Math.min(3.999,(local.x-x0-15)/beatWidth)))});
 }
 return svg;
}
function render(){
 const root=$('#score');root.replaceChildren();prepareVoicings();const systems=[];for(let i=0;i<rows.length;){let take=rows.slice(i,i+3).some(r=>r.events.some(e=>e.duration<.25))?2:3;systems.push(rows.slice(i,i+take));i+=take}const scorePages=Math.ceil(systems.length/4),pageCount=scorePages+Math.ceil(voicingList.length/20);
 for(let page=0;page<scorePages;page++){
  let sheet=document.createElement('section');sheet.className='sheet';let ss=systems.slice(page*4,page*4+4),rr=ss.flat();sheet.dataset.firstBar=rr[0].i;
  let header=document.createElement('header');header.className='sheet-heading';header.innerHTML=`<span>仓颉 <small>五月天</small></span><small>${key(rr[0])} · Capo ${mode==='target'?'2':'0'} · 4/4 · ♩ = ${bpm}</small>`;sheet.append(header);
  for(const systemRows of ss){let wrap=document.createElement('div');wrap.className='system';wrap.append(renderSystem(systemRows));sheet.append(wrap)}
  let footer=document.createElement('footer');footer.className='page-footer';footer.innerHTML=`<span>和弦图为基础按法 · 旋律换指按六线谱 · 扫弦具体按法查编号</span><span>${page+1} / ${pageCount}</span>`;sheet.append(footer);root.append(sheet);
 }
 for(let page=0;page<Math.ceil(voicingList.length/20);page++){let sheet=document.createElement('section');sheet.className='sheet voicing-page';if(page===0)sheet.id='strum-fingerings';let h=document.createElement('header');h.className='sheet-heading';h.innerHTML='<span>扫弦指法对照</span><small>'+ (mode==='target'?'品位相对 Capo 2':'原谱指法 · 不夹')+'</small>';sheet.append(h);let desc=document.createElement('p');desc.className='diagram-description';desc.textContent='谱面箭头旁的小编号对应下列指法。× 为不发声弦，跨弦扫过时轻触制音；○ 为空弦。格左为起始品位，图下为逐弦品位。';sheet.append(desc);let grid=document.createElement('div');grid.className='voicing-grid';for(const v of voicingList.slice(page*20,page*20+20)){let item=document.createElement('div');item.className='voicing-item';item.append(voicingDiagram(v));grid.append(item)}sheet.append(grid);let footer=document.createElement('footer');footer.className='page-footer';footer.innerHTML='<span>同一和弦可能因原声部或八度安排使用不同指法；按箭头编号对应弹奏</span><span>'+(scorePages+page+1)+' / '+pageCount+'</span>';sheet.append(footer);root.append(sheet);}
 $('#mode-label').textContent=mode==='target'?'G → A 指法 · Capo 2':'C → D 指法 · 不夹';update();
}
const sampleLoads=new Map(),sampleErrors=[];
async function loadSamples(c){const sr=c.sampleRate;if(sampleLoads.has(sr))return sampleLoads.get(sr);let p=Promise.all(Object.entries(DATA.samples||{}).map(async([pitch,str])=>{try{let binary=atob(str),bytes=new Uint8Array(binary.length);for(let i=0;i<bytes.length;i++)bytes[i]=binary.charCodeAt(i);let decoded=await c.decodeAudioData(bytes.buffer);for(let channel=0;channel<decoded.numberOfChannels;channel++){let d=decoded.getChannelData(channel);for(let i=0;i<d.length;i++)d[i]*=8}buffers.set(sr+':'+pitch,decoded)}catch(e){sampleErrors.push({pitch,error:e.message});throw e}}));sampleLoads.set(sr,p);return p}
async function audio(){
 if(!ctx){const C=window.AudioContext||window.webkitAudioContext;if(!C)throw new Error('浏览器不支持 Web Audio');ctx=new C();}
 if(ctx.state==='suspended')await ctx.resume();
 if(!bus){bus=ctx.createGain();bus.gain.value=.7;bus.connect(ctx.destination)}
 await loadSamples(ctx);return ctx;
}
const buffers=new Map();
function makeBuffer(c,pitch){
 const cacheKey=c.sampleRate+':'+pitch;if(buffers.has(cacheKey))return buffers.get(cacheKey);
 const length=8,sr=c.sampleRate,buf=c.createBuffer(1,sr*length,sr),d=buf.getChannelData(0),f=freq(pitch);
 for(let j=0;j<d.length;j++){let t=j/sr,a=2*Math.PI*f*t;d[j]=Math.min(1,t/.003)*(.62*Math.sin(a)*Math.exp(-2.6*t)+.23*Math.sin(2*a)*Math.exp(-4.7*t)+.1*Math.sin(3*a)*Math.exp(-7*t)+.05*Math.sin(4*a)*Math.exp(-10*t));}
 buffers.set(cacheKey,buf);return buf;
}
const voiceLanes=new WeakMap();
function sound(c,dest,pitch,time,duration,volume=.2,track=true,lane){
 let src=c.createBufferSource(),g=c.createGain();if(lane){let state=voiceLanes.get(c);if(!state){state={chord:null,notes:new Map()};voiceLanes.set(c,state)}let prior=state.notes.get(lane);if(prior){prior.gain.gain.cancelScheduledValues(Math.max(0,time-.004));prior.gain.gain.setTargetAtTime(.0001,Math.max(0,time-.004),.001);prior.source.stop(time)}state.notes.set(lane,{source:src,gain:g})}src.buffer=makeBuffer(c,pitch);src.playbackRate.value=DATA.sampleTuning?.[pitch]||1;g.gain.setValueAtTime(volume,time);g.gain.setValueAtTime(volume,time+Math.max(.02,duration-.025));g.gain.linearRampToValueAtTime(0,time+duration);src.connect(g);g.connect(dest);src.start(time);src.stop(time+duration+.015);
 if(track){voices.add(src);src.onended=()=>{voices.delete(src);src.disconnect();g.disconnect()};audioLog.push({generation,pitch,time,duration})}return src;
}
function ordered(e){let ns=[...e.notes];if(e.technique==='strum'||e.technique==='arpeggio')ns.sort((a,b)=>e.direction==='up'?viewNote(a).s-viewNote(b).s:viewNote(b).s-viewNote(a).s);return ns}
function slap(c,dest,time,track=true){let buf=c.createBuffer(1,Math.ceil(c.sampleRate*.12),c.sampleRate),d=buf.getChannelData(0),seed=73;for(let j=0;j<d.length;j++){seed=(seed*1664525+1013904223)>>>0;let t=j/c.sampleRate;d[j]=((seed/4294967296-.5)*.6+Math.sin(2*Math.PI*105*t)*.3)*Math.exp(-55*t)*Math.min(1,t/.001);}let src=c.createBufferSource(),g=c.createGain();src.buffer=buf;g.gain.value=.45;src.connect(g);g.connect(dest);src.start(time);src.stop(time+.13);if(track){voices.add(src);src.onended=()=>{voices.delete(src);src.disconnect();g.disconnect()};audioLog.push({generation,technique:'slap',time,duration:.12})}}
function dispatch(c,dest,e,t,tempo,track=true){if(e.technique==='slap'){slap(c,dest,t,track);return}if(e.tie)return;let state=voiceLanes.get(c);if(state&&state.chord!==e.chord){for(const v of state.notes.values()){v.gain.gain.cancelScheduledValues(Math.max(0,t-.004));v.gain.gain.setTargetAtTime(.0001,Math.max(0,t-.004),.001);v.source.stop(t)}state.notes.clear()}if(!state){state={chord:e.chord,notes:new Map()};voiceLanes.set(c,state)}state.chord=e.chord;let ns=ordered(e),spread=e.technique==='strum'?(e.direction==='up'?.008:.012):e.technique==='arpeggio'?.025:0;let length=Math.max(3.2,(e.sustain||e.duration)*60/tempo);ns.forEach((n,j)=>sound(c,dest,midi(n),t+j*spread,length,(ns.length>3?.25:.34)*(e.technique==='strum'&&e.direction==='up'?.72:1),track,viewNote(n).s));}
function silence(){generation++;if(ctx)voiceLanes.delete(ctx);for(const v of voices){try{v.stop()}catch{}}voices.clear();if(bus){bus.gain.cancelScheduledValues(ctx.currentTime);bus.gain.setValueAtTime(0,ctx.currentTime);bus.disconnect();bus=null}}
function current(){return playing?Math.max(anchorBeat,anchorBeat+(ctx.currentTime-anchorTime)*bpm/60):position}
function events(){const [lo,hi]=range();return rows.flatMap(r=>r.events.map(e=>({beat:(r.i-1)*4+e.beat,e,bar:r.i}))).filter(x=>x.beat>=lo&&x.beat<hi)}
async function start(at=position){
 const request=++playbackRequest;
 try{await audio();if(request!==playbackRequest)return;clearInterval(timer);cancelAnimationFrame(frame);silence();await audio();const [lo,hi]=range();if(at<lo||at>=hi)at=lo;
 position=at;anchorBeat=at;anchorTime=ctx.currentTime+.05;timeline=events();next=timeline.findIndex(e=>e.beat>=at-1e-6);if(next<0)next=timeline.length;
 const held=rows.flatMap(r=>r.events.map(e=>({beat:(r.i-1)*4+e.beat,e}))).filter(v=>v.beat<at&&v.beat+(v.e.sustain||v.e.duration)>at&&!v.e.tie&&v.e.notes.length);
 for(const h of held)dispatch(ctx,bus,{...h.e,sustain:undefined,duration:h.beat+(h.e.sustain||h.e.duration)-at},anchorTime,bpm);
 playing=true;$('#play').textContent='Ⅱ 暂停';$('#play').setAttribute('aria-pressed','true');$('#error').textContent='';
 timer=setInterval(schedule,20);schedule();animate();
 }catch(e){$('#error').textContent=e.message;}
}
function pause(){playbackRequest++;if(playing)position=Math.min(range()[1],current());playing=false;clearInterval(timer);cancelAnimationFrame(frame);silence();$('#play').textContent='▶ 播放';$('#play').setAttribute('aria-pressed','false');update()}
function schedule(){if(!playing)return;while(next<timeline.length){let n=timeline[next],t=anchorTime+(n.beat-anchorBeat)*60/bpm;if(t>ctx.currentTime+.1)break;next++;if(t<ctx.currentTime-.025)continue;dispatch(ctx,bus,n.e,t,bpm)}const now=current();if(now>=range()[1]){let lo=range()[0];pause();position=range()[1];update();if(loop)start(lo)}}
function animate(){if(!playing)return;position=current();update();frame=requestAnimationFrame(animate)}
function update(){
 position=Math.max(0,Math.min(rows.length*4,position));let bi=Math.min(rows.length-1,Math.floor(position/4)),r=rows[bi],local=position%4;
 $('#seek').value=position;$('#played').textContent=fmt(position*60/bpm);$('#duration').textContent=fmt(rows.length*4*60/bpm);$('#location').textContent=`${r.i} / ${rows.length} · 原谱 ${r.sourceBarNumber}${r.pass===2?'（二遍）':''}`;
 document.querySelectorAll('.current').forEach(e=>e.classList.remove('current'));document.querySelectorAll('.event.active').forEach(e=>e.classList.remove('active'));
 let bar=document.querySelector(`[data-bar="${r.i}"]`);if(bar){bar.classList.add('current');let cur=bar.querySelector('.cursor'),x=Number(bar.dataset.firstX)+local*Number(bar.dataset.beatWidth);cur.setAttribute('x1',x);cur.setAttribute('x2',x);
 let ee=r.events.filter(e=>e.beat<=local+1e-6).at(-1);if(ee&&local<ee.beat+ee.duration)bar.querySelector(`[data-event="${r.i}:${ee.beat}"]`)?.classList.add('active');
 if(follow&&playing&&lastBar!==bi){let bounds=bar.getBoundingClientRect();if(bounds.top<120||bounds.bottom>innerHeight-25)bar.closest('.system').scrollIntoView({block:'center',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'})}lastBar=bi;}
}
function seek(at){let was=playing;pause();position=Math.max(0,Math.min(rows.length*4-.0001,Number(at)));const [lo,hi]=range();if(position<lo||position>=hi){section='all';$('#section').value='all'}update();if(was)start(position)}
async function preview(ns){try{if(playing)pause();await audio();silence();await audio();ns.forEach(n=>sound(ctx,bus,midi(n),ctx.currentTime+.02,.8,.5));$('#note-info').textContent=ns.map(n=>{let a=viewNote(n);return`${a.s}弦 ${a.f}品 · ${freq(midi(n)).toFixed(1)} Hz`}).join(' / ')}catch(e){$('#error').textContent=e.message}}
async function previewEvent(e){if(playing)pause();await audio();silence();await audio();dispatch(ctx,bus,e,ctx.currentTime+.02,bpm);$('#note-info').textContent='指法 '+voicingMap.get(voicingKey(e)).id+' · '+label(e.chord)+' · '+e.notes.map(viewNote).sort((a,b)=>b.s-a.s).map(n=>n.s+'弦'+n.f+'品').join(' / ')}
$('#play').onclick=()=>playing?pause():start();$('#restart').onclick=()=>{pause();position=range()[0];start()};
$('#bpm').oninput=e=>{let was=playing,at=current();pause();bpm=Number(e.target.value);position=at;$('#bpm-value').textContent=bpm+' BPM';update();document.querySelectorAll('.sheet:not(.voicing-page) .sheet-heading > small').forEach((el,i)=>el.textContent=`${key(rows[Number(el.closest('.sheet').dataset.firstBar)-1])} · Capo ${mode==='target'?'2':'0'} · 4/4 · ♩ = ${bpm}`);if(was)start(at)};
$('#seek').oninput=e=>seek(e.target.value);$('#loop').onchange=e=>loop=e.target.checked;$('#follow').onchange=e=>follow=e.target.checked;
$('#section').onchange=e=>{let was=playing;pause();section=e.target.value;position=range()[0];update();document.querySelector(`[data-bar="${Math.floor(position/4)+1}"]`)?.closest('.system').scrollIntoView({block:'center'});if(was)start()};
$('#mode').onchange=e=>{let was=playing,at=current();pause();mode=e.target.value;position=at;render();if(was)start(at)};
$('#print').onclick=()=>{pause();window.print()};document.addEventListener('visibilitychange',()=>{if(document.hidden&&playing)pause()});window.addEventListener('pagehide',pause);
$('#source-toggle').onclick=()=>{$('#sources').hidden=!$('#sources').hidden;if(!$('#sources').dataset.loaded){for(const im of DATA.sourceImages){let fig=document.createElement('figure'),img=document.createElement('img');img.src=im.data;img.alt=im.name;img.loading='lazy';let cap=document.createElement('figcaption');cap.textContent=im.name;fig.append(img,cap);$('#sources').append(fig)}$('#sources').dataset.loaded='yes'}};
for(const s of sections){let op=document.createElement('option');op.value=s.id;op.textContent=s.name;$('#section').append(op)}
const oct=$('#octaves');for(const ex of DATA.octaveExceptions){let li=document.createElement('li');li.textContent=`原谱 ${ex.bar} 小节，第 ${ex.beat+1} 拍：${ex.sourceString}弦${ex.sourceFret}品 → 相对夹 MIDI ${ex.targetPitchRelativeCapo}（${ex.octaves>0?'+':''}${ex.octaves} 八度）。${ex.reason}。`;oct.append(li)}
$('#octave-count').textContent=DATA.octaveExceptions.length+' 个原谱音事件含八度调整';
$('#seek').max=rows.length*4;render();
// Inspectable QA API; same synthesis and same data as live playback.
window.cangjie={data:DATA,sampleErrors,getDecodedSampleCount:()=>buffers.size,sections,getState:()=>({mode,bpm,position,playing,voices:voices.size,generation,contextState:ctx?.state}),audioLog,pause,seek,start,renderNote:async pitch=>{const C=window.OfflineAudioContext||window.webkitOfflineAudioContext,c=new C(1,44100,44100);await loadSamples(c);sound(c,c.destination,pitch,.02,.8,.5,false);let b=await c.startRendering();return Array.from(b.getChannelData(0))},
 renderAudio:async(startBar=1,endBar=93)=>{let selected=rows.filter(r=>r.i>=startBar&&r.i<=endBar);let len=selected.length*4*60/bpm+2;const C=window.OfflineAudioContext||window.webkitOfflineAudioContext,c=new C(1,Math.ceil(len*44100),44100),g=c.createGain();g.gain.value=.7;g.connect(c.destination);await loadSamples(c);for(const r of selected)for(const e of r.events)dispatch(c,g,e,((r.i-startBar)*4+e.beat)*60/bpm,bpm,false);let b=await c.startRendering();return Array.from(b.getChannelData(0))},frequency:freq,getVoicings:()=>voicingList};
