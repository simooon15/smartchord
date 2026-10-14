from pathlib import Path
root=Path('skills/smartchord')
p=root/'assets/practice.js';s=p.read_text();s+=r'''
// One live output: the actual score mix feeds an audio element for OS media routing.
let mediaOutput=null,mediaAudio=null,mediaReady=false,playbackStarting=false;
function liveDestination(c){
 if(!navigator.mediaSession||!c.createMediaStreamDestination)return c.destination;
 if(!mediaOutput){mediaOutput=c.createMediaStreamDestination();mediaAudio=document.createElement('audio');mediaAudio.id='score-media';mediaAudio.hidden=true;mediaAudio.srcObject=mediaOutput.stream;document.body.append(mediaAudio)}
 return mediaOutput;
}
async function activateMediaOutput(){
 if(!mediaAudio)return;
 try{await mediaAudio.play();mediaReady=true}
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
function installMediaControls(){
 if(navigator.mediaSession){
  if(window.MediaMetadata)navigator.mediaSession.metadata=new MediaMetadata({title:DATA.title,artist:DATA.artist||document.querySelector('.eyebrow').textContent.replace('GUITAR / ',''),album:'SmartChord'});
  for(const [action,handler] of [['play',()=>{if(!playing&&!playbackStarting)start()}],['pause',pause],['stop',pause]])try{navigator.mediaSession.setActionHandler(action,handler)}catch{}
 }
 document.addEventListener('keydown',e=>{
  if(e.repeat||e.defaultPrevented)return;
  if(['MediaPlayPause','MediaPlay','MediaPause'].includes(e.key)){e.preventDefault();if(e.key==='MediaPlay'){if(!playing&&!playbackStarting)start()}else if(e.key==='MediaPause')pause();else togglePlayback();return}
  if(e.code==='Space'&&!e.altKey&&!e.ctrlKey&&!e.metaKey&&!e.shiftKey&&!e.target.closest('input,select,textarea,button,a,[contenteditable="true"],[role="button"]')){e.preventDefault();togglePlayback()}
 });
 syncMediaState();
}
''';p.write_text(s)
for p in [root/'assets/player.js',Path('work/project/app.js')]:
 s=p.read_text();barStart="r.startBeat" if p.name=='player.js' else "(r.i-1)*4"
 # sweepGlyph has no row in scope: recover the exact parent event's bar.
 s=s.replace("g.addEventListener('click',ev=>{ev.stopPropagation();previewEvent(e)})", "g.addEventListener('click',ev=>{ev.stopPropagation();const r=rows[Number(es.getAttribute('data-event').split(':')[0])-1];playAt("+barStart+"+e.beat,ev,()=>previewEvent(e))})")
 s=s.replace("ev.preventDefault();previewEvent(e)", "ev.preventDefault();const r=rows[Number(es.getAttribute('data-event').split(':')[0])-1];playAt("+barStart+"+e.beat,ev,()=>previewEvent(e))")
 s=s.replace("ev.stopPropagation();previewEvent(e)", "ev.stopPropagation();playAt("+barStart+"+e.beat,ev,()=>previewEvent(e))")
 s=s.replace("if(ev.key==='Enter')previewEvent(e)", "if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();playAt("+barStart+"+e.beat,ev,()=>previewEvent(e))}")
 s=s.replace("ev.stopPropagation();preview([n])", "ev.stopPropagation();playAt("+barStart+"+e.beat,ev,()=>preview([n]))")
 s=s.replace("ev.preventDefault();preview([n])", "ev.preventDefault();playAt("+barStart+"+e.beat,ev,()=>preview([n]))")
 # Only the bar click requests autoplay; programmatic seek and paused slider stay positional.
 s=s.replace("g.scoreBeat(local.x))))", "g.scoreBeat(local.x))),true)")
 s=s.replace('bus.connect(ctx.destination)', 'bus.connect(liveDestination(ctx))')
 s=s.replace('await loadSamples(ctx);return ctx;', 'await loadSamples(ctx);await activateMediaOutput();return ctx;')
 s=s.replace('function silence(){generation++;','function silence(){stopMediaOutput();generation++;')
 s=s.replace('const request=++playbackRequest;', 'const request=++playbackRequest;playbackStarting=true;')
 s=s.replace('silence();await audio();const [lo,hi]', 'silence();await audio();if(request!==playbackRequest)return;const [lo,hi]')
 s=s.replace("timer=setInterval(schedule,20);schedule();animate();", "syncMediaState();timer=setInterval(schedule,20);schedule();animate();")
 s=s.replace("}catch(e){$('#error').textContent=e.message;}\n}", "}catch(e){if(request===playbackRequest){pause();$('#error').textContent=e.message}}finally{if(request===playbackRequest)playbackStarting=false}\n}")
 s=s.replace('function pause(){playbackRequest++;','function pause(){playbackRequest++;playbackStarting=false;')
 s=s.replace("$('#play').setAttribute('aria-pressed','false');update()}", "$('#play').setAttribute('aria-pressed','false');syncMediaState();update()}")
 s=s.replace('function seek(at){let was=playing;', 'function seek(at,autoplay=playing){let was=autoplay;')
 s=s.replace("$('#play').onclick=()=>playing?pause():start()", "$('#play').onclick=togglePlayback")
 s=s.replace('src.disconnect();g.disconnect()', 'src.disconnect();g.disconnect();if(!playing&&!voices.size)stopMediaOutput()')
 s=s.replace('pianoCredits();', 'pianoCredits();installMediaControls();')
 s=s.replace('getState:()=>({mode,bpm,position,playing,', 'getState:()=>({mode,bpm,position,playing,playbackStarting,mediaReady,')
 p.write_text(s)
# Same preview cleanup for piano voices.
p=root/'assets/practice.js';s=p.read_text().replace('src.disconnect();gain.disconnect()', 'src.disconnect();gain.disconnect();if(!playing&&!voices.size)stopMediaOutput()');p.write_text(s)
for p in [root/'scripts/build_html.py',Path('work/project/build.py')]:
 s=p.read_text().replace('点击音符或箭头试听，点击谱面定位。', '点击谱面任意位置即从该处播放；Option / Alt＋点击音符或箭头单独试听。媒体播放／暂停键或空格键可切换播放。').replace('点击品位或扫弦箭头试听，点击谱面定位。', '点击谱面任意位置即从该处播放；Option / Alt＋点击品位或箭头单独试听。媒体播放／暂停键或空格键可切换播放。');p.write_text(s)
