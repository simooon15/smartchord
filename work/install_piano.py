from pathlib import Path
root=Path('skills/smartchord')
p=root/'assets/practice.js';s=p.read_text();s=s[:s.index('function melodySound')]+r'''const pianoBuffers=new Map(),pianoLoads=new Map();
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
 if(track){voices.add(src);src.onended=()=>{voices.delete(src);src.disconnect();gain.disconnect()};audioLog.push({generation,track:'melody',instrument:'piano',root,pitch,time,duration,sampleOffset:offset})}
}
function pianoCredits(){
 if(!DATA.pianoInfo||document.querySelector('#piano-credits'))return;
 const m=DATA.pianoInfo,details=document.createElement('details');details.id='piano-credits';
 const summary=document.createElement('summary');summary.textContent='钢琴主旋律 · 音色与许可';details.append(summary);
 const credit=document.createElement('p');credit.textContent=m.name+' · '+m.author+' · '+m.license+'。'+m.adaptations;details.append(credit);
 for(const [label,url] of [['采样来源',m.sourceUrl],['许可',m.licenseUrl]]){const a=document.createElement('a');a.textContent=label+' ';a.href=url;details.append(a)}
 const license=document.createElement('pre');license.style.whiteSpace='pre-wrap';license.textContent=DATA.pianoLicenseText;details.append(license);document.querySelector('.notes').append(details);
}
''';p.write_text(s)
for p in [root/'assets/player.js',Path('work/project/app.js')]:
 s=p.read_text().replace('async function loadSamples(c){','async function loadSamples(c){await loadPianoSamples(c);')
 s=s.replace('const b=await c.startRendering();return Array.from(b.getChannelData(0))},getState:', 'const b=await c.startRendering();return Array.from(b.getChannelData(0))},getState:')
 s=s.replace('melodySound(c,c.destination,{pitchBefore:pitch', 'await loadSamples(c);melodySound(c,c.destination,{pitchBefore:pitch')
 s=s.replace("e:{...n.e,duration:n.e.duration-Math.max(0,lo-n.beat)}", "e:{...n.e,sampleOffsetBeats:Math.max(0,lo-n.beat),duration:n.e.duration-Math.max(0,lo-n.beat)}")
 s=s.replace('{...h.e,sustain:undefined,duration:', '{...h.e,sampleOffsetBeats:(h.e.sampleOffsetBeats||0)+at-h.beat,sustain:undefined,duration:')
 s=s.replace('{...n.e,duration:Math.min(hi,n.beat+n.e.duration)-at}', '{...n.e,sampleOffsetBeats:at-n.beat,duration:Math.min(hi,n.beat+n.e.duration)-at}')
 s=s.replace("$('#seek').max=", "pianoCredits();\n$('#seek').max=");p.write_text(s)
p=root/'scripts/build_html.py';s=p.read_text().replace('import argparse,base64,html,json,mimetypes,re','import argparse,base64,html,json,mimetypes,re\nfrom prepare_piano import embed_piano');s=s.replace(" samples=Path(samples)", " embed_piano(d,ROOT/'assets/piano-cache')\n samples=Path(samples)",1);s=s.replace('简谱旋律提示音','简谱主旋律（钢琴采样）');p.write_text(s)
p=Path('work/project/build.py');s=p.read_text().replace('import json,base64,re','import json,base64,re,sys');s=s.replace("SOURCE=P.parents", "sys.path.insert(0,str(P.parents[1]/'skills/smartchord/scripts'))\nfrom prepare_piano import embed_piano\nSOURCE=P.parents");s=s.replace('sample_manifest=', "embed_piano(DATA,P.parents[1]/'skills/smartchord/assets/piano-cache')\nsample_manifest=",1);s=s.replace('简谱旋律提示音','简谱主旋律（钢琴采样）');p.write_text(s)
