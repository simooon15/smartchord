'use strict';
const DATA=JSON.parse(document.querySelector('#score-data').textContent),rows=DATA.rows;
const beats=r=>r.meter[0]*4/r.meter[1];let totalBeats=0;for(const r of rows){r.startBeat=totalBeats;totalBeats+=beats(r)}
const esc=t=>String(t).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const $=s=>document.querySelector(s),NS='http://www.w3.org/2000/svg',O=[0,64,59,55,50,45,40];
let mode='target',bpm=DATA.bpm,position=0,playing=false,loop=false,follow=true,section='all';
let melodyEnabled=false;
let playbackRequest=0;
let ctx=null,bus=null,voices=new Set(),timer=null,frame=null,anchorBeat=0,anchorTime=0,next=0,timeline=[],generation=0,lastBar=-1;
const audioLog=[];let clickTrack=false;
function el(tag,a={},t){let n=document.createElementNS(NS,tag);for(const [k,v] of Object.entries(a))n.setAttribute(k,v);if(t!==undefined)n.textContent=t;return n}
function txt(p,x,y,t,cls,a={}){let n=el('text',{x,y,class:cls,...a},t);p.append(n);return n}
function line(p,x1,y1,x2,y2,cls){p.append(el('line',{x1,y1,x2,y2,class:cls}))}
const freq=m=>440*2**((m-69)/12),fmt=s=>`${Math.floor(s/60)}:${String(Math.floor(s%60)).padStart(2,'0')}`;
const sections=[{id:'all',name:'整首',start:0,end:totalBeats}];
for(const r of rows){let s=sections.at(-1);if(s.id==='all'||s.name!==r.section)sections.push({id:String(r.i),name:r.section,start:r.startBeat,end:r.startBeat+beats(r)});else s.end=r.startBeat+beats(r)}
function range(){let s=sections.find(s=>s.id===section);return[s.start,s.end]}
function midi(n){return mode==='target'?n.pitchAfter:n.pitchBefore}
function viewNote(n){return mode==='target'?{s:n.string,f:n.fret}:{s:n.sourceString,f:n.sourceFret}}
function activeChord(r,t){return [...r.chordChanges].reverse().find(c=>c[0]<=t)[1]}
function label(c){return mode==='target'?DATA.transposition[c]:c}
function key(r){return mode==='target'?r.targetKey+' 指法 · 实际 '+r.actualKey+' 调':r.sourceKey+' 指法 · Capo '+DATA.settings.sourceCapo}
// Low-position foundation shapes, string 6 → 1. Melody changes remain in the tab.
function foundationShape(c){return mode==='target'?DATA.foundationShapes[label(c)]:[...DATA.shapes[c]].reverse()}
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
 let g=el('g',{class:'sweep',role:'button',tabindex:0,'aria-label':label(e.chord)+(up?'上扫':'下扫')+'，指法 '+id,'data-low-string':lo,'data-high-string':hi});g.append(el('rect',{x:x-10,y:top-8,width:20,height:bottom-top+16,fill:'transparent'}));g.append(el('path',{d:path+' '+head,class:'sweep-line'}));g.append(el('title',{},'指法 '+id+' · '+label(e.chord)+' · '+ns.sort((a,b)=>b.s-a.s).map(n=>n.s+'弦'+n.f+'品').join(' / ')));txt(g,x+9,tip+(up?-2:1),String(id),'voicing-ref');g.addEventListener('click',ev=>{ev.stopPropagation();const r=rows[Number(es.getAttribute('data-event').split(':')[0])-1];playAt(r.startBeat+e.beat,ev,()=>previewEvent(e))});g.addEventListener('keydown',ev=>{if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();const r=rows[Number(es.getAttribute('data-event').split(':')[0])-1];playAt(r.startBeat+e.beat,ev,()=>previewEvent(e))}});es.append(g);
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
 const W=staffWidth(),H=250,svg=el('svg',{viewBox:`0 0 ${W} ${H}`,class:'staff',role:'group','aria-label':`演奏第${list[0].i}至${list.at(-1).i}小节`});
 for(let k=0;k<list.length;k++){
  const stride=printLayout()?(list.length===1&&DATA.settings.denseBarsPerSystem===1?730:list.length===3?240:365):(W-30)/list.length,barWidth=stride-10,r=list[k],beatWidth=(barWidth-27)/beats(r);let x0=30+k*stride,xx=t=>x0+15+t*beatWidth,ys=s=>72+(s-1)*15;
  if(!printLayout()){const points=[...new Set([0,...r.events.map(e=>e.beat),...r.vocal.map(v=>v.beat),...r.chordChanges.map(c=>c[0]),beats(r)])].sort((a,b)=>a-b),weights=points.slice(1).map((p,j)=>12+(p-points[j])*12),sum=weights.reduce((a,b)=>a+b,0),xs=[x0+15];for(const w of weights)xs.push(xs.at(-1)+w/sum*(barWidth-27));xx=t=>{let j=points.findIndex(p=>p>t);if(j<0)return xs.at(-1);if(j===0)return xs[0];return xs[j-1]+(xs[j]-xs[j-1])*(t-points[j-1])/(points[j]-points[j-1])};}
  let g=el('g',{'data-bar':r.i,'data-first-x':xx(0),'data-beat-width':beatWidth,transform:'translate(0,23)'});svg.append(g);g.scoreX=xx;g.scoreBeat=x=>{let lo=0,hi=beats(r);for(let j=0;j<24;j++){const mid=(lo+hi)/2;if(xx(mid)<x)lo=mid;else hi=mid}return (lo+hi)/2};
  g.append(el('rect',{x:x0,y:-8,width:barWidth,height:229,class:'bar-shade'}));
  txt(g,x0,-11,`${r.i} · 原谱 ${r.sourceBarNumber}${r.pass===2?' / 二遍':''}`,'bar-number');
  if(r.i===1||rows[r.i-2]?.section!==r.section)txt(g,x0+barWidth-5,-11,(printLayout()?r.section+' · '+key(r):r.section),'section-tag',{'text-anchor':'end'});
  r.chordChanges.forEach(([t,c])=>{const center=Math.min(xx(t)+14,x0+barWidth-25);txt(g,center,9,label(c),'chord',{'text-anchor':'middle'});let chart=foundationDiagram(c,0,0);chart.setAttribute('transform',`translate(${center-24.15},10) scale(.7)`);g.append(chart);});
  if(k===0)for(let s=1;s<=6;s++)txt(g,x0-14,ys(s)+4,['','e','B','G','D','A','E'][s],'string-label',{'text-anchor':'middle'});
  for(let s=1;s<=6;s++)line(g,x0,ys(s),x0+barWidth,ys(s),'string-line');
  line(g,x0,72,x0,147,'barline');line(g,x0+barWidth,72,x0+barWidth,147,'barline');
  if(r.i===rows.length)line(g,x0+barWidth-4,72,x0+barWidth-4,147,'final-barline');
  for(const e of r.events){
   const x=xx(e.beat),es=el('g',{'data-event':`${r.i}:${e.beat}`,class:'event','data-beat':e.beat});g.append(es);
   if(e.technique==='rest')txt(es,x,110,'休','rest-mark',{'text-anchor':'middle'});
   if(e.technique==='slap'){let mark=txt(es,x,147,'⊠','slap-mark',{'text-anchor':'middle',role:'button',tabindex:0,'aria-label':'拍弦试听'});mark.append(el('title',{},'拍弦：右手拍击琴弦，短促打击声，无确定音高'));mark.addEventListener('click',ev=>{ev.stopPropagation();playAt(r.startBeat+e.beat,ev,()=>previewEvent(e))});mark.addEventListener('keydown',ev=>{if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();playAt(r.startBeat+e.beat,ev,()=>previewEvent(e))}});}
   for(const n of (['strum','arpeggio'].includes(e.technique)?[]:e.notes)){
    const {s,f}=viewNote(n);let nt=txt(es,x,ys(s),String(f),'fret'+(mode==='target'&&n.octaveException?' octave':''),{'text-anchor':'middle','dominant-baseline':'central',role:'button',tabindex:0,'aria-label':`${s}弦${f}品，${Math.round(freq(midi(n)))}赫兹`});
    if(!printLayout()&&W<400&&f>=10){const neighbors=r.events.filter(q=>q!==e&&q.notes.some(a=>viewNote(a).s===s)).map(q=>Math.abs(xx(q.beat)-x)),space=Math.min(14,...neighbors.map(gap=>gap-3));nt.setAttribute('textLength',Math.max(9,space));nt.setAttribute('lengthAdjust','spacingAndGlyphs');nt.style.strokeWidth='3px'}
    const title=el('title',{},`原谱 ${n.sourceString}弦${n.sourceFret}品 (${n.pitchBefore}) → ${s}弦${f}品，实际 MIDI ${midi(n)}${n.octaveException?'；八度调整 '+(n.octaveException>0?'+':'')+n.octaveException:''}`);nt.append(title);
    nt.addEventListener('click',ev=>{ev.stopPropagation();playAt(r.startBeat+e.beat,ev,()=>preview([n]))});nt.addEventListener('keydown',ev=>{if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();playAt(r.startBeat+e.beat,ev,()=>preview([n]))}});
    noteTarget(nt,r,e,n);
   }
   if(e.technique==='strum'||e.technique==='arpeggio')sweepGlyph(es,e,x);
   if(e.tie&&!(DATA.engravingVersion>=2))txt(es,x,160,'⌒','tie',{'text-anchor':'middle'});
   if(e.technique==='pull-off')txt(es,x,160,'P','technique');
  }
  if(DATA.engravingVersion>=2){
   for(let j=1;j<r.events.length;j++){
    const e=r.events[j],prev=r.events[j-1];if(!e.tie&&!e.transition)continue;
    for(const n of e.notes){const old=prev.notes.find(q=>q.sourceString===n.sourceString);if(!old)continue;
     const a=viewNote(old),b=viewNote(n),x1=xx(prev.beat)+5,x2=xx(e.beat)-5;
     if(e.transition==='slide')g.append(el('path',{d:`M ${x1} ${ys(a.s)-3} L ${x2} ${ys(b.s)-8}`,class:'legato-line','data-transition':e.transition}));
     else {const y=Math.min(ys(a.s),ys(b.s))-9;g.append(el('path',{d:`M ${x1} ${y} Q ${(x1+x2)/2} ${y-15} ${x2} ${y}`,class:'legato-line','data-transition':e.transition||'tie'}));if(e.transition)txt(g,(x1+x2)/2,y-6,e.transition==='hammer-on'?'H':'P','legato-label',{'text-anchor':'middle'});}
    }
   }
  }
  renderRhythm(g,r,xx);
  for(const v of r.vocal){const value=RhythmNotation.value(v);let x=xx(v.beat);let t=v.degree===null?'—':(v.accidental===1?'♯':v.accidental===-1?'♭':'')+String(v.degree);txt(g,x,195,t,'jianpu',{'text-anchor':'middle'});
   if(v.degree){for(let j=0;j<Math.abs(v.octave);j++)txt(g,x,v.octave>0?185-j*4:207+Math.max(0,value.levels-1)*3+j*4,'·','vocal-dot',{'text-anchor':'middle'});}
   for(let level=0;level<value.levels;level++)line(g,x-5,200+level*3,x+5,200+level*3,'vocal-beam');for(let dot=0;dot<value.dots;dot++)txt(g,x+7+dot*5,195,'·','dot');
   if(v.lyric)positionTarget(txt(g,x,222,v.lyric,'lyric',{'text-anchor':'middle'}),r.startBeat+v.beat);
  }
  let cursor=el('line',{x1:xx(0),x2:xx(0),y1:50,y2:177,class:'cursor','data-cursor':r.i});g.append(cursor);
  g.addEventListener('click',ev=>{if(ev.target.closest('.fret')||ev.target.classList.contains('arrow'))return;const p=svg.createSVGPoint();p.x=ev.clientX;p.y=ev.clientY;const local=p.matrixTransform(svg.getScreenCTM().inverse());seek(r.startBeat+Math.max(0,Math.min(beats(r)-.001,g.scoreBeat(local.x))),true)});
 }
 return svg;
}
function render(){
 const root=$('#score');root.replaceChildren();prepareVoicings();const systems=[];for(let i=0;i<rows.length;){let take=DATA.settings.barsPerSystem|| (rows.slice(i,i+3).some(r=>r.events.some(e=>e.duration<.25))?2:3);if(DATA.settings.denseBarsPerSystem===1){const dense=r=>r?.events.some(e=>e.duration<.25);if(dense(rows[i])||(take>1&&dense(rows[i+1])))take=1;}if(!printLayout())take=screenTake(i);systems.push(rows.slice(i,i+take));i+=take}const scorePages=Math.ceil(systems.length/4),pageCount=scorePages+Math.ceil(voicingList.length/20);
 for(let page=0;page<scorePages;page++){
  let sheet=document.createElement('section');sheet.className='sheet';let ss=systems.slice(page*4,page*4+4),rr=ss.flat();sheet.dataset.firstBar=rr[0].i;
  let header=document.createElement('header');header.className='sheet-heading';header.innerHTML=`<span>${esc(DATA.title)} <small>${esc(DATA.artist||'')}</small></span><small>${key(rr[0])} · Capo ${mode==='target'?DATA.capo:DATA.settings.sourceCapo} · ${rr[0].meter.join('/')} · ♩ = ${bpm}</small>`;sheet.append(header);
  for(const systemRows of ss){let wrap=document.createElement('div');wrap.className='system';wrap.append(renderSystem(systemRows));sheet.append(wrap)}
  let footer=document.createElement('footer');footer.className='page-footer';footer.innerHTML=`<span>和弦图为基础按法 · 旋律换指按六线谱 · 扫弦具体按法查编号</span><span>${page+1} / ${pageCount}</span>`;sheet.append(footer);root.append(sheet);
 }
 for(let page=0;page<Math.ceil(voicingList.length/20);page++){let sheet=document.createElement('section');sheet.className='sheet voicing-page';if(page===0)sheet.id='strum-fingerings';let h=document.createElement('header');h.className='sheet-heading';h.innerHTML='<span>扫弦指法对照</span><small>'+ ('品位相对 Capo '+(mode==='target'?DATA.capo:DATA.settings.sourceCapo))+'</small>';sheet.append(h);let desc=document.createElement('p');desc.className='diagram-description';desc.textContent='谱面箭头旁的小编号对应下列指法。× 为不发声弦，跨弦扫过时轻触制音；○ 为空弦。格左为起始品位，图下为逐弦品位。';sheet.append(desc);let grid=document.createElement('div');grid.className='voicing-grid';for(const v of voicingList.slice(page*20,page*20+20)){let item=document.createElement('div');item.className='voicing-item';item.append(voicingDiagram(v));grid.append(item)}sheet.append(grid);let footer=document.createElement('footer');footer.className='page-footer';footer.innerHTML='<span>同一和弦可能因原声部或八度安排使用不同指法；按箭头编号对应弹奏</span><span>'+(scorePages+page+1)+' / '+pageCount+'</span>';sheet.append(footer);root.append(sheet);}
 $('#mode-label').textContent=key(rows[0])+' · Capo '+(mode==='target'?DATA.capo:DATA.settings.sourceCapo);update();
}
const sampleLoads=new Map(),sampleErrors=[];
async function loadSamples(c){await loadPianoSamples(c);const sr=c.sampleRate;if(sampleLoads.has(sr))return sampleLoads.get(sr);let p=Promise.all(Object.entries(DATA.samples||{}).map(async([pitch,str])=>{try{let binary=atob(str),bytes=new Uint8Array(binary.length);for(let i=0;i<bytes.length;i++)bytes[i]=binary.charCodeAt(i);let decoded=await c.decodeAudioData(bytes.buffer);for(let channel=0;channel<decoded.numberOfChannels;channel++){let d=decoded.getChannelData(channel);for(let i=0;i<d.length;i++)d[i]*=DATA.sampleGain}buffers.set(sr+':'+pitch,decoded)}catch(e){sampleErrors.push({pitch,error:e.message});throw e}}));sampleLoads.set(sr,p);return p}
async function audio(request){
 if(!ctx){const C=window.AudioContext||window.webkitAudioContext;if(!C)throw new Error('浏览器不支持 Web Audio');ctx=new C();}
 if(ctx.state==='suspended')await ctx.resume();
 if(!bus){bus=ctx.createGain();bus.gain.value=.7;bus.connect(liveDestination(ctx))}
 await loadSamples(ctx);if(request!==undefined&&request!==playbackRequest)return ctx;await activateMediaOutput(request);return ctx;
}
const buffers=new Map();
function makeBuffer(c,pitch){
 const cacheKey=c.sampleRate+':'+pitch;if(buffers.has(cacheKey))return buffers.get(cacheKey);
 throw new Error('缺少实际音高 '+pitch+' 的离线采样');
}
const voiceLanes=new WeakMap();
function sound(c,dest,pitch,time,duration,volume=.2,track=true,lane){
 let src=c.createBufferSource(),g=c.createGain();if(lane){let state=voiceLanes.get(c);if(!state){state={chord:null,notes:new Map()};voiceLanes.set(c,state)}let prior=state.notes.get(lane);if(prior){prior.gain.gain.cancelScheduledValues(Math.max(0,time-.004));prior.gain.gain.setTargetAtTime(.0001,Math.max(0,time-.004),.001);prior.source.stop(time)}state.notes.set(lane,{source:src,gain:g,basePitch:pitch,pitch,volume})}src.buffer=makeBuffer(c,pitch);src.playbackRate.value=DATA.sampleTuning?.[pitch]||1;g.gain.setValueAtTime(volume,time);g.gain.setValueAtTime(volume,time+Math.max(.02,duration-.025));g.gain.linearRampToValueAtTime(0,time+duration);src.connect(g);g.connect(dest);src.start(time);src.stop(time+duration+.015);
 if(track){voices.add(src);src.onended=()=>{voices.delete(src);src.disconnect();g.disconnect();if(!playing&&!playbackStarting&&!voices.size)stopMediaOutput()};audioLog.push({generation,pitch,time,duration})}return src;
}
function ordered(e){let ns=[...e.notes];if(e.technique==='strum'||e.technique==='arpeggio')ns.sort((a,b)=>e.direction==='up'?viewNote(a).s-viewNote(b).s:viewNote(b).s-viewNote(a).s);return ns}
function slap(c,dest,time,track=true){let buf=c.createBuffer(1,Math.ceil(c.sampleRate*.12),c.sampleRate),d=buf.getChannelData(0),seed=73;for(let j=0;j<d.length;j++){seed=(seed*1664525+1013904223)>>>0;let t=j/c.sampleRate;d[j]=((seed/4294967296-.5)*.6+Math.sin(2*Math.PI*105*t)*.3)*Math.exp(-55*t)*Math.min(1,t/.001);}let src=c.createBufferSource(),g=c.createGain();src.buffer=buf;g.gain.value=.45;src.connect(g);g.connect(dest);src.start(time);src.stop(time+.13);if(track){voices.add(src);src.onended=()=>{voices.delete(src);src.disconnect();g.disconnect();if(!playing&&!playbackStarting&&!voices.size)stopMediaOutput()};audioLog.push({generation,technique:'slap',time,duration:.12})}}
function dispatch(c,dest,e,t,tempo,track=true){if(e.technique==='melody'){melodySound(c,dest,e,t,tempo,track);return}if(e.technique==='slap'){slap(c,dest,t,track);return}if(e.tie)return;let state=voiceLanes.get(c);if(state&&state.chord!==e.chord){for(const v of state.notes.values()){v.gain.gain.cancelScheduledValues(Math.max(0,t-.004));v.gain.gain.setTargetAtTime(.0001,Math.max(0,t-.004),.001);v.source.stop(t)}state.notes.clear()}if(!state){state={chord:e.chord,notes:new Map()};voiceLanes.set(c,state)}state.chord=e.chord;let ns=ordered(e),spread=e.technique==='strum'?(e.direction==='up'?.008:.012):e.technique==='arpeggio'?.025:0;let length=Math.max(3.2,(e.sustain||e.duration)*60/tempo);ns.forEach((n,j)=>{
 const lane=viewNote(n).s,prior=state.notes.get(lane),pitch=midi(n);
 if(e.transition&&prior){
  const param=prior.source.playbackRate,base=DATA.sampleTuning?.[prior.basePitch]||1;
  param.cancelScheduledValues(t);param.setValueAtTime(base*2**((prior.pitch-prior.basePitch)/12),t);
  param.linearRampToValueAtTime(base*2**((pitch-prior.basePitch)/12),t+(e.transition==='slide'?.045:.008));
  prior.gain.gain.cancelScheduledValues(t);prior.gain.gain.setValueAtTime(prior.volume,t);prior.gain.gain.setValueAtTime(prior.volume,t+length-.025);prior.gain.gain.linearRampToValueAtTime(0,t+length);prior.source.stop(t+length+.015);prior.pitch=pitch;
  if(track)audioLog.push({generation,pitch,time:t,duration:length,transition:e.transition});
 }else sound(c,dest,pitch,t+j*spread,length,(ns.length>3?.25:.34)*(e.technique==='strum'&&e.direction==='up'?.72:1),track,lane);
 });}
function silence(){stopMediaOutput();generation++;if(ctx)voiceLanes.delete(ctx);for(const v of voices){try{v.stop()}catch{}}voices.clear();if(bus){bus.gain.cancelScheduledValues(ctx.currentTime);bus.gain.setValueAtTime(0,ctx.currentTime);bus.disconnect();bus=null}}
function current(){return playing?Math.max(anchorBeat,anchorBeat+(ctx.currentTime-anchorTime)*bpm/60):position}
function events(){const [lo,hi]=range();const guitar=rows.flatMap(r=>r.events.map(e=>({beat:r.startBeat+e.beat,e,bar:r.i})));return [...guitar,...(melodyEnabled?melodyEvents().map(n=>({...n,beat:Math.max(lo,n.beat),e:{...n.e,sampleOffsetBeats:Math.max(0,lo-n.beat),duration:n.e.duration-Math.max(0,lo-n.beat)}})).filter(n=>n.e.duration>0):[])].filter(x=>x.beat>=lo&&x.beat<hi).sort((a,b)=>a.beat-b.beat)}
async function start(at=position){
 const request=++playbackRequest;playbackStarting=true;
 try{await audio(request);if(request!==playbackRequest)return;clearInterval(timer);cancelAnimationFrame(frame);silence();await audio(request);if(request!==playbackRequest)return;const [lo,hi]=range();if(at<lo||at>=hi)at=lo;
 position=at;anchorBeat=at;anchorTime=ctx.currentTime+.05;timeline=events();next=timeline.findIndex(e=>e.beat>=at-1e-6);if(next<0)next=timeline.length;
 const held=rows.flatMap(r=>r.events.map(e=>({beat:r.startBeat+e.beat,e}))).filter(v=>v.beat<at&&v.beat+(v.e.sustain||v.e.duration)>at&&!v.e.tie&&v.e.notes.length);
 if(melodyEnabled)held.push(...timeline.filter(n=>n.e.technique==='melody'&&n.beat<at&&n.beat+n.e.duration>at));
 for(const h of held)dispatch(ctx,bus,{...h.e,sampleOffsetBeats:(h.e.sampleOffsetBeats||0)+at-h.beat,sustain:undefined,duration:h.beat+(h.e.sustain||h.e.duration)-at},anchorTime,bpm);
 playing=true;$('#play').textContent='Ⅱ 暂停';$('#play').setAttribute('aria-pressed','true');$('#error').textContent='';
 syncMediaState();timer=setInterval(schedule,20);schedule();animate();
 }catch(e){if(request===playbackRequest){pause();$('#error').textContent=e.message}}finally{if(request===playbackRequest)playbackStarting=false}
}
function pause(){playbackRequest++;playbackStarting=false;if(playing)position=Math.min(range()[1],current());playing=false;clearInterval(timer);cancelAnimationFrame(frame);silence();$('#play').textContent='▶ 播放';$('#play').setAttribute('aria-pressed','false');syncMediaState();update()}
function schedule(){if(!playing)return;while(next<timeline.length){let n=timeline[next],t=anchorTime+(n.beat-anchorBeat)*60/bpm;if(t>ctx.currentTime+.1)break;next++;if(t<ctx.currentTime-.025)continue;dispatch(ctx,bus,n.e,t,bpm)}const now=current();if(now>=range()[1]){let lo=range()[0];pause();position=range()[1];update();if(loop)start(lo)}}
function animate(){if(!playing)return;position=current();update();frame=requestAnimationFrame(animate)}
function update(){
 position=Math.max(0,Math.min(totalBeats,position));let r=[...rows].reverse().find(r=>r.startBeat<=position)||rows[0],bi=r.i-1,local=Math.min(beats(r),position-r.startBeat);
 $('#seek').value=position;$('#played').textContent=fmt(position*60/bpm);$('#duration').textContent=fmt(totalBeats*60/bpm);$('#location').textContent=`${r.i} / ${rows.length} · 原谱 ${r.sourceBarNumber}${r.pass===2?'（二遍）':''}`;
 document.querySelectorAll('.current').forEach(e=>e.classList.remove('current'));document.querySelectorAll('.event.active').forEach(e=>e.classList.remove('active'));
 let bar=document.querySelector(`[data-bar="${r.i}"]`);if(bar){bar.classList.add('current');let cur=bar.querySelector('.cursor'),x=bar.scoreX(local);cur.setAttribute('x1',x);cur.setAttribute('x2',x);
 let ee=r.events.filter(e=>e.beat<=local+1e-6).at(-1);if(ee&&local<ee.beat+ee.duration)bar.querySelector(`[data-event="${r.i}:${ee.beat}"]`)?.classList.add('active');
 if(follow&&playing&&lastBar!==bi){let bounds=bar.getBoundingClientRect();if(bounds.top<120||bounds.bottom>innerHeight-25)bar.closest('.system').scrollIntoView({block:'center',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'})}lastBar=bi;}
}
function seek(at,autoplay=playing||playbackStarting){let was=autoplay;pause();position=Math.max(0,Math.min(totalBeats-.0001,Number(at)));const [lo,hi]=range();if(position<lo||position>=hi){section='all';$('#section').value='all'}update();if(was)start(position)}
async function preview(ns){try{if(playing||playbackStarting)pause();await audio();silence();await audio();ns.forEach(n=>sound(ctx,bus,midi(n),ctx.currentTime+.02,.8,.5));$('#note-info').textContent=ns.map(n=>{let a=viewNote(n);return`${a.s}弦 ${a.f}品 · ${freq(midi(n)).toFixed(1)} Hz`}).join(' / ')}catch(e){$('#error').textContent=e.message}}
async function previewEvent(e){if(playing||playbackStarting)pause();await audio();silence();await audio();dispatch(ctx,bus,e,ctx.currentTime+.02,bpm);$('#note-info').textContent=(e.technique==='slap'?'拍弦':'指法 '+voicingMap.get(voicingKey(e)).id)+' · '+label(e.chord)+' · '+e.notes.map(viewNote).sort((a,b)=>b.s-a.s).map(n=>n.s+'弦'+n.f+'品').join(' / ')}
$('#play').onclick=togglePlayback;$('#restart').onclick=()=>{pause();position=range()[0];start()};
$('#bpm').oninput=e=>{let was=playing||playbackStarting,at=current();pause();bpm=Number(e.target.value);position=at;$('#bpm-value').textContent=bpm+' BPM';update();document.querySelectorAll('.sheet:not(.voicing-page) .sheet-heading > small').forEach((el,i)=>el.textContent=`${key(rows[Number(el.closest('.sheet').dataset.firstBar)-1])} · Capo ${mode==='target'?DATA.capo:DATA.settings.sourceCapo} · ${rows[Number(el.closest('.sheet').dataset.firstBar)-1].meter.join('/')} · ♩ = ${bpm}`);if(was)start(at)};
$('#seek').oninput=e=>seek(e.target.value);$('#loop').onchange=e=>loop=e.target.checked;$('#follow').onchange=e=>follow=e.target.checked;
$('#section').onchange=e=>{let was=playing;pause();section=e.target.value;position=range()[0];update();document.querySelector(`[data-bar="${(rows.find(r=>r.startBeat===position)||rows[0]).i}"]`)?.closest('.system').scrollIntoView({block:'center'});if(was)start()};
$('#mode').onchange=e=>{let was=playing||playbackStarting,at=current();pause();mode=e.target.value;position=at;render();if(was)start(at)};
$('#print').onclick=()=>{pause();window.print()};document.addEventListener('visibilitychange',()=>{if(document.hidden&&playing)pause()});window.addEventListener('pagehide',pause);
$('#source-toggle').onclick=()=>{$('#sources').hidden=!$('#sources').hidden;if(!$('#sources').dataset.loaded){for(const im of DATA.sourceImages){let fig=document.createElement('figure'),img=document.createElement('img');img.src=im.data;img.alt=im.name;img.loading='lazy';let cap=document.createElement('figcaption');cap.textContent=im.name;fig.append(img,cap);$('#sources').append(fig)}$('#sources').dataset.loaded='yes'}};
for(const s of sections){let op=document.createElement('option');op.value=s.id;op.textContent=s.name;$('#section').append(op)}
const oct=$('#octaves');for(const ex of DATA.octaveExceptions){let li=document.createElement('li');li.textContent=`原谱 ${ex.bar} 小节，第 ${ex.beat+1} 拍：${ex.sourceString}弦${ex.sourceFret}品 → 相对夹 MIDI ${ex.targetPitchRelativeCapo}（${ex.octaves>0?'+':''}${ex.octaves} 八度）。${ex.reason}。`;oct.append(li)}
$('#octave-count').textContent=DATA.octaveExceptions.length+' 个原谱音事件含八度调整';
$('#melody').onchange=e=>{const was=playing||playbackStarting,at=current();pause();melodyEnabled=e.target.checked;position=at;if(was)start(at)};
let resizeFrame;const reflow=()=>{cancelAnimationFrame(resizeFrame);resizeFrame=requestAnimationFrame(()=>{render()})};new ResizeObserver(reflow).observe($('.layout'));matchMedia('print').addEventListener('change',()=>render());window.addEventListener('beforeprint',()=>render());window.addEventListener('afterprint',reflow);
pianoCredits();installMediaControls();
$('#seek').max=totalBeats;render();
// Inspectable QA API; same synthesis and same data as live playback.
window.guitarScore={data:DATA,sampleErrors,getDecodedSampleCount:()=>buffers.size,sections,getMelodyEvents:melodyEvents,renderMelodyNote:async pitch=>{const C=window.OfflineAudioContext||window.webkitOfflineAudioContext,c=new C(1,44100,44100);await loadSamples(c);melodySound(c,c.destination,{pitchBefore:pitch,pitchAfter:pitch,duration:1},.02,76,false);const b=await c.startRendering();return Array.from(b.getChannelData(0))},getMediaActions:()=>mediaActionHandlers,getState:()=>({mode,bpm,position,playing,playbackStarting,mediaReady,melodyEnabled,voices:voices.size,generation,contextState:ctx?.state}),audioLog,pause,seek,start,renderNote:async pitch=>{const C=window.OfflineAudioContext||window.webkitOfflineAudioContext,c=new C(1,44100,44100);await loadSamples(c);sound(c,c.destination,pitch,.02,.8,.5,false);let b=await c.startRendering();return Array.from(b.getChannelData(0))},
 renderAudio:async(startBar=1,endBar=rows.length)=>{let selected=rows.filter(r=>r.i>=startBar&&r.i<=endBar);let len=selected.reduce((sum,r)=>sum+beats(r),0)*60/bpm+8;const C=window.OfflineAudioContext||window.webkitOfflineAudioContext,c=new C(1,Math.ceil(len*44100),44100),g=c.createGain();g.gain.value=.7;g.connect(c.destination);await loadSamples(c);for(const r of selected)for(const e of r.events)dispatch(c,g,e,(r.startBeat-selected[0].startBeat+e.beat)*60/bpm,bpm,false);if(melodyEnabled){const lo=selected[0].startBeat,hi=selected.at(-1).startBeat+beats(selected.at(-1));for(const n of melodyEvents())if(n.beat<hi&&n.beat+n.e.duration>lo){const at=Math.max(lo,n.beat);dispatch(c,g,{...n.e,sampleOffsetBeats:at-n.beat,duration:Math.min(hi,n.beat+n.e.duration)-at},(at-lo)*60/bpm,bpm,false)}}let b=await c.startRendering();return Array.from(b.getChannelData(0))},frequency:freq,getVoicings:()=>voicingList};
