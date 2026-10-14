// Shared responsive engraving and independent guide melody; no song-specific data.
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
const pianoBuffers=new Map(),pianoLoads=new Map();
async function loadPianoSamples(c){
 if(pianoLoads.has(c.sampleRate))return pianoLoads.get(c.sampleRate);
 const task=Promise.all(Object.entries(DATA.pianoSamples||{}).map(async([root,b64])=>{
  const bytes=Uint8Array.from(atob(b64),ch=>ch.charCodeAt(0));
  try{pianoBuffers.set(c.sampleRate+':'+root,await c.decodeAudioData(bytes.buffer))}
  catch(e){sampleErrors.push({instrument:'piano',pitch:root,error:e.message});throw e}
 }));pianoLoads.set(c.sampleRate,task);return task;
}
function melodySound(c,dest,e,time,tempo,track=true){
 const duration=e.duration*60/tempo,pitch=midi(e),root=DATA.pianoInfo?.mappings[String(pitch)],buffer=pianoBuffers.get(c.sampleRate+':'+root);
 if(!buffer)throw new Error('缺少主旋律钢琴采样 MIDI '+pitch);
 const src=c.createBufferSource(),gain=c.createGain(),sample=DATA.pianoInfo.samples[String(root)],rate=sample.playbackRate*2**((pitch-root)/12),volume=DATA.pianoInfo.gain;
 src.buffer=buffer;src.playbackRate.value=rate;
 const release=.18,offset=(e.sampleOffsetBeats||0)*60/tempo*rate;
 if(offset>=buffer.duration)return; // A naturally decayed piano is not re-attacked when seeking.
 gain.gain.setValueAtTime(volume,time);gain.gain.setValueAtTime(volume,time+duration);
 gain.gain.linearRampToValueAtTime(0,time+duration+release);
 src.connect(gain);gain.connect(dest);src.start(time,offset);src.stop(time+duration+release+.005);
 if(track){voices.add(src);src.onended=()=>{voices.delete(src);src.disconnect();gain.disconnect();if(!playing&&!playbackStarting&&!voices.size)stopMediaOutput()};audioLog.push({generation,track:'melody',instrument:'piano',root,pitch,time,duration,sampleOffset:offset})}
}
function pianoCredits(){
 if(!DATA.pianoInfo||document.querySelector('#piano-credits'))return;
 const m=DATA.pianoInfo,details=document.createElement('details');details.id='piano-credits';
 const summary=document.createElement('summary');summary.textContent='钢琴主旋律 · 音色与许可';details.append(summary);
 const credit=document.createElement('p');credit.textContent=m.name+' · '+m.author+' · '+m.license+'。'+m.adaptations;details.append(credit);
 for(const [label,url] of [['采样来源',m.sourceUrl],['许可',m.licenseUrl]]){const a=document.createElement('a');a.textContent=label+' ';a.href=url;details.append(a)}
 const license=document.createElement('pre');license.style.whiteSpace='pre-wrap';license.textContent=DATA.pianoLicenseText;details.append(license);document.querySelector('.notes').append(details);
}

// One live output: the actual score mix feeds an audio element for OS media routing.
let mediaOutput=null,mediaAudio=null,mediaReady=false,playbackStarting=false;
function liveDestination(c){
 if(!navigator.mediaSession||!c.createMediaStreamDestination)return c.destination;
 if(!mediaOutput){mediaOutput=c.createMediaStreamDestination();mediaAudio=document.createElement('audio');mediaAudio.id='score-media';mediaAudio.hidden=true;mediaAudio.srcObject=mediaOutput.stream;document.body.append(mediaAudio)}
 return mediaOutput;
}
async function activateMediaOutput(request){
 if(!mediaAudio)return;
 try{await mediaAudio.play();mediaReady=true;if(request!==undefined&&request!==playbackRequest&&!playing&&!playbackStarting)mediaAudio.pause()}
 catch(e){if(e.name==='AbortError')throw e;mediaReady=false;if(bus){bus.disconnect();bus.connect(ctx.destination)}}
}
function stopMediaOutput(){mediaAudio?.pause()}
function syncMediaState(){
 if(!navigator.mediaSession)return;
 try{navigator.mediaSession.playbackState=playing?'playing':'paused';const duration=rows.reduce((n,r)=>n+r.meter[0]*4/r.meter[1],0)*60/bpm;navigator.mediaSession.setPositionState?.({duration,playbackRate:1,position:Math.max(0,Math.min(duration,current()*60/bpm))})}catch{}
}
function togglePlayback(){if(playing||playbackStarting)pause();else start()}
function playAt(beat,event,audition){
 if(event?.altKey&&audition){audition();return}
 seek(beat,true);
}
const mediaActionHandlers={};
function installMediaControls(){
 if(navigator.mediaSession){
  if(window.MediaMetadata)navigator.mediaSession.metadata=new MediaMetadata({title:DATA.title,artist:DATA.artist||document.querySelector('.eyebrow').textContent.replace('GUITAR / ',''),album:'SmartChord'});
  for(const [action,handler] of [['play',()=>{if(!playing&&!playbackStarting)start()}],['pause',pause],['stop',pause]])try{navigator.mediaSession.setActionHandler(action,handler);mediaActionHandlers[action]=handler}catch{}
 }
 document.addEventListener('keydown',e=>{
  if(e.repeat||e.defaultPrevented)return;
  if(['MediaPlayPause','MediaPlay','MediaPause'].includes(e.key)){e.preventDefault();if(e.key==='MediaPlay'){if(!playing&&!playbackStarting)start()}else if(e.key==='MediaPause')pause();else togglePlayback();return}
  if(e.code==='Space'&&!e.altKey&&!e.ctrlKey&&!e.metaKey&&!e.shiftKey&&!e.target.closest('input,select,textarea,button,a,[contenteditable="true"],[role="button"]')){e.preventDefault();togglePlayback()}
 });
 syncMediaState();
}
// Give SVG notes a real hit area; WebKit text glyph hit-testing can miss the glyph.
function noteTarget(nt,r,e,n){
 const x=Number(nt.getAttribute('x')),y=Number(nt.getAttribute('y')),group=el('g',{class:'note-button',role:'button',tabindex:0,'aria-label':nt.getAttribute('aria-label')});
 nt.replaceWith(group);group.append(el('rect',{x:x-7,y:y-10,width:14,height:20,fill:'transparent','pointer-events':'all'}),nt);nt.style.pointerEvents='none';nt.removeAttribute('role');nt.removeAttribute('tabindex');
 const beat=(r.startBeat??(r.i-1)*4)+e.beat;group.addEventListener('click',ev=>{ev.stopPropagation();playAt(beat,ev,()=>preview([n]))});group.addEventListener('keydown',ev=>{if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();playAt(beat,ev,()=>preview([n]))}});
}
function positionTarget(nt,beat){
 const x=Number(nt.getAttribute('x')),y=Number(nt.getAttribute('y')),group=el('g',{class:'lyric-button',role:'button',tabindex:0,'aria-label':nt.textContent+'，从此处播放'});
 nt.replaceWith(group);group.append(el('rect',{x:x-8,y:y-14,width:16,height:18,fill:'transparent','pointer-events':'all'}),nt);nt.style.pointerEvents='none';group.addEventListener('click',ev=>{ev.stopPropagation();playAt(beat,ev)});group.addEventListener('keydown',ev=>{if(!ev.repeat&&(ev.key==='Enter'||ev.key===' ')){ev.preventDefault();playAt(beat,ev)}});
}
