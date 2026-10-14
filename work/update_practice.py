from pathlib import Path
root=Path('skills/smartchord')
helper=r'''// Shared responsive engraving and independent guide melody; no song-specific data.
function printLayout(){return matchMedia('print').matches}
function staffWidth(){return printLayout()?760:Math.max(240,document.querySelector('#score').clientWidth-(innerWidth<=680?18:50))}
function screenTake(index){
 const width=staffWidth()-30;let used=0,take=0;
 for(const r of rows.slice(index,index+4)){
  const slots=new Set([...r.events,...r.vocal].map(e=>e.beat)).size;
  const needed=Math.max(230,slots*19+40,r.chordChanges.length*76);
  if(take&&used+needed>width)break;used+=needed;take++;
 }
 return Math.max(1,take);
}
function melodyEvents(){
 const result=[];let held=null;
 for(const r of rows)for(const v of r.vocal){
  const beat=(r.startBeat??(r.i-1)*4)+v.beat;
  if(v.degree===0){held=null;continue}
  if(v.degree===null||v.tie){
   if(held&&Math.abs(held.beat+held.e.duration-beat)<1e-6)held.e.duration+=v.duration;
   else if(v.degree!==null)throw new Error('旋律延音缺少相邻起音');
   continue;
  }
  if(!Number.isFinite(v.pitchBefore)||!Number.isFinite(v.pitchAfter))throw new Error('主旋律缺少已核实音高');
  held={beat,bar:r.i,e:{technique:'melody',duration:v.duration,pitchBefore:v.pitchBefore,pitchAfter:v.pitchAfter}};result.push(held);
 }
 return result;
}
function melodySound(c,dest,e,time,tempo,track=true){
 const duration=e.duration*60/tempo,pitch=midi(e),src=c.createOscillator(),gain=c.createGain();
 src.type='sine';src.frequency.value=freq(pitch);
 gain.gain.setValueAtTime(0,time);gain.gain.linearRampToValueAtTime(.13,time+Math.min(.012,duration/4));
 gain.gain.setValueAtTime(.13,time+Math.max(.012,duration-.025));gain.gain.linearRampToValueAtTime(0,time+duration);
 src.connect(gain);gain.connect(dest);src.start(time);src.stop(time+duration+.005);
 if(track){voices.add(src);src.onended=()=>{voices.delete(src);src.disconnect();gain.disconnect()};audioLog.push({generation,track:'melody',pitch,time,duration})}
}
'''
(root/'assets/practice.js').write_text(helper)
for f in [root/'assets/player.js',Path('work/project/app.js')]:
 s=f.read_text().replace("let playbackRequest=0;","let melodyEnabled=false;\nlet playbackRequest=0;")
 s=s.replace('const W=760,H=250','const W=staffWidth(),H=250')
 if f.name=='app.js':
  s=s.replace('const stride=list.length===3?240:365,','const stride=printLayout()?(list.length===3?240:365):(W-30)/list.length,')
 else:
  s=s.replace('const stride=list.length===1&&DATA.settings.denseBarsPerSystem===1?730:list.length===3?240:365,','const stride=printLayout()?(list.length===1&&DATA.settings.denseBarsPerSystem===1?730:list.length===3?240:365):(W-30)/list.length,')
 # Leave printed rhythmic proportions untouched; give short events adequate engraving space on screen.
 s=s.replace('xx=t=>x0+15+t*beatWidth,ys=s=>72+(s-1)*15;', 'xx=t=>x0+15+t*beatWidth,ys=s=>72+(s-1)*15;\n  if(!printLayout()){const points=[...new Set([0,...r.events.map(e=>e.beat),...r.vocal.map(v=>v.beat),...r.chordChanges.map(c=>c[0]),'+('4' if f.name=='app.js' else 'beats(r)')+'])].sort((a,b)=>a-b),weights=points.slice(1).map((p,j)=>12+(p-points[j])*12),sum=weights.reduce((a,b)=>a+b,0),xs=[x0+15];for(const w of weights)xs.push(xs.at(-1)+w/sum*(barWidth-27));xx=t=>{let j=points.findIndex(p=>p>t);if(j<0)return xs.at(-1);if(j===0)return xs[0];return xs[j-1]+(xs[j]-xs[j-1])*(t-points[j-1])/(points[j]-points[j-1])};}')
 s=s.replace("r.section+' · '+key(r)","(printLayout()?r.section+' · '+key(r):r.section)")
 # Cursor and click coordinate mapping must follow elastic spacing.
 s=s.replace("'data-beat-width':beatWidth,", "'data-beat-width':beatWidth,")
 s=s.replace("svg.append(g);", "svg.append(g);g.scoreX=xx;g.scoreBeat=x=>{let lo=0,hi="+('4' if f.name=='app.js' else 'beats(r)')+";for(let j=0;j<24;j++){const mid=(lo+hi)/2;if(xx(mid)<x)lo=mid;else hi=mid}return (lo+hi)/2};")
 s=s.replace('(local.x-x0-15)/beatWidth','g.scoreBeat(local.x)')
 s=s.replace('x=Number(bar.dataset.firstX)+local*Number(bar.dataset.beatWidth)','x=bar.scoreX(local)')
 s=s.replace('systems.push(rows.slice(i,i+take));','if(!printLayout())take=screenTake(i);systems.push(rows.slice(i,i+take));')
 s=s.replace("function dispatch(c,dest,e,t,tempo,track=true){", "function dispatch(c,dest,e,t,tempo,track=true){if(e.technique==='melody'){melodySound(c,dest,e,t,tempo,track);return}")
 s=s.replace("function events(){const [lo,hi]=range();return rows.flatMap", "function events(){const [lo,hi]=range();const guitar=rows.flatMap")
 needle=".filter(x=>x.beat>=lo&&x.beat<hi)}"
 s=s.replace(needle,";return [...guitar,...(melodyEnabled?melodyEvents().map(n=>({...n,beat:Math.max(lo,n.beat),e:{...n.e,duration:n.e.duration-Math.max(0,lo-n.beat)}})).filter(n=>n.e.duration>0):[])].filter(x=>x.beat>=lo&&x.beat<hi).sort((a,b)=>a.beat-b.beat)}")
 s=s.replace('for(const h of held)dispatch', 'if(melodyEnabled)held.push(...melodyEvents().filter(n=>n.beat<at&&n.beat+n.e.duration>at&&n.beat+n.e.duration>range()[0]));\n for(const h of held)dispatch')
 s=s.replace("$('#seek').max=", "$('#melody').onchange=e=>{const was=playing,at=current();pause();melodyEnabled=e.target.checked;position=at;if(was)start(at)};\nlet resizeFrame;const reflow=()=>{cancelAnimationFrame(resizeFrame);resizeFrame=requestAnimationFrame(()=>{render()})};new ResizeObserver(reflow).observe($('.layout'));matchMedia('print').addEventListener('change',()=>render());window.addEventListener('beforeprint',()=>render());window.addEventListener('afterprint',reflow);\n$('#seek').max=")
 s=s.replace('getState:()=>({mode,bpm,position,playing,','getMelodyEvents:melodyEvents,renderMelodyNote:async pitch=>{const C=window.OfflineAudioContext||window.webkitOfflineAudioContext,c=new C(1,44100,44100);melodySound(c,c.destination,{pitchBefore:pitch,pitchAfter:pitch,duration:1},.02,76,false);const b=await c.startRendering();return Array.from(b.getChannelData(0))},getState:()=>({mode,bpm,position,playing,melodyEnabled,')
 # Offline mix uses exactly the same melody synthesis and timing as live playback, including entering sustained notes.
 s=s.replace('let b=await c.startRendering();return Array.from(b.getChannelData(0))},frequency:freq', "if(melodyEnabled){const lo="+('selected[0].startBeat' if f.name!='app.js' else '(startBar-1)*4')+",hi="+('selected.at(-1).startBeat+beats(selected.at(-1))' if f.name!='app.js' else 'endBar*4')+";for(const n of melodyEvents())if(n.beat<hi&&n.beat+n.e.duration>lo){const at=Math.max(lo,n.beat);dispatch(c,g,{...n.e,duration:Math.min(hi,n.beat+n.e.duration)-at},(at-lo)*60/bpm,bpm,false)}}let b=await c.startRendering();return Array.from(b.getChannelData(0))},frequency:freq")
 f.write_text(s)
# Both build entrypoints embed shared module and unchecked melody switch.
for f in [root/'scripts/build_html.py',Path('work/project/build.py')]:
 s=f.read_text();s=s.replace('<label><input id="loop"', '<label><input id="melody" type="checkbox">主旋律</label><label><input id="loop"')
 s=s.replace('播放器演奏吉他声部，简谱是独立人声参考。','默认播放吉他伴奏；勾选“主旋律”可同时播放简谱旋律提示音。谱行随窗口宽度自动分行。')
 s=s.replace('播放器演奏吉他声部。窄屏谱行可横向滑动。','默认播放吉他伴奏；勾选“主旋律”可同时播放简谱旋律提示音。谱行随窗口宽度自动分行。')
 if f.name=='build.py':s=s.replace("(P/'rhythm.js').read_text()+'\\n'+", "(P/'rhythm.js').read_text()+'\\n'+(P.parents[1]/'skills/smartchord/assets/practice.js').read_text()+'\\n'+")
 else:s=s.replace("(ROOT/'assets/rhythm.js').read_text()+'\\n'+", "(ROOT/'assets/rhythm.js').read_text()+'\\n'+(ROOT/'assets/practice.js').read_text()+'\\n'+")
 f.write_text(s)
for f in [root/'assets/player.css',Path('work/project/app.css')]:
 s=f.read_text().replace('.system{overflow-x:auto}.staff{width:760px;max-width:none}', '.system{overflow:visible}.staff{width:100%;max-width:100%}')
 s+='\n@media screen{.staff{width:100%;height:auto}.sheet-heading small{overflow-wrap:anywhere}}\n@media screen and (max-width:680px){.chord{font-size:14px}.fret{font-size:13px}.bar-number{font-size:8px}.section-tag{font-size:9px}.jianpu{font-size:13px}.lyric{font-size:12px}.controls{position:relative}.page-footer{gap:8px;flex-wrap:wrap}}\n'
 f.write_text(s)
