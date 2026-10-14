from pathlib import Path
p=Path('skills/smartchord/assets/player.js');s=p.read_text()
s=s.replace("state.notes.set(lane,{source:src,gain:g})","state.notes.set(lane,{source:src,gain:g,basePitch:pitch,pitch,volume})")
s=s.replace("const scorePages=Math.ceil(systems.length/4)","const scorePages=Math.ceil(systems.length/4)")
s=s.replace("let take=rows.slice(i,i+3).some(r=>r.events.some(e=>e.duration<.25))?2:3;","let take=DATA.settings.barsPerSystem|| (rows.slice(i,i+3).some(r=>r.events.some(e=>e.duration<.25))?2:3);")
# Retain the normal synthesis path unless a source explicitly marks legato.
s=s.replace("ns.forEach((n,j)=>sound(c,dest,midi(n),t+j*spread,length,(ns.length>3?.25:.34)*(e.technique==='strum'&&e.direction==='up'?.72:1),track,viewNote(n).s));", """ns.forEach((n,j)=>{
 const lane=viewNote(n).s,prior=state.notes.get(lane),pitch=midi(n);
 if(e.transition&&prior){
  const param=prior.source.playbackRate,base=DATA.sampleTuning?.[prior.basePitch]||1;
  param.cancelScheduledValues(t);param.setValueAtTime(base*2**((prior.pitch-prior.basePitch)/12),t);
  param.linearRampToValueAtTime(base*2**((pitch-prior.basePitch)/12),t+(e.transition==='slide'?.045:.008));
  prior.gain.gain.cancelScheduledValues(t);prior.gain.gain.setValueAtTime(prior.volume,t);prior.gain.gain.setValueAtTime(prior.volume,t+length-.025);prior.gain.gain.linearRampToValueAtTime(0,t+length);prior.source.stop(t+length+.015);prior.pitch=pitch;
  if(track)audioLog.push({generation,pitch,time:t,duration:length,transition:e.transition});
 }else sound(c,dest,pitch,t+j*spread,length,(ns.length>3?.25:.34)*(e.technique==='strum'&&e.direction==='up'?.72:1),track,lane);
 });""")
s=s.replace("let t=v.degree===null?'—':String(v.degree);", "let t=v.degree===null?'—':(v.accidental===1?'♯':v.accidental===-1?'♭':'')+String(v.degree);")
needle="  renderRhythm(g,r,xx);"
s=s.replace(needle,"""  if(DATA.engravingVersion>=2){
   for(let j=1;j<r.events.length;j++){
    const e=r.events[j],prev=r.events[j-1];if(!e.tie&&!e.transition)continue;
    for(const n of e.notes){const old=prev.notes.find(q=>q.sourceString===n.sourceString);if(!old)continue;
     const a=viewNote(old),b=viewNote(n),x1=xx(prev.beat)+5,x2=xx(e.beat)-5;
     if(e.transition==='slide')g.append(el('path',{d:`M ${x1} ${ys(a.s)-3} L ${x2} ${ys(b.s)-8}`,class:'legato-line','data-transition':e.transition}));
     else {const y=Math.min(ys(a.s),ys(b.s))-9;g.append(el('path',{d:`M ${x1} ${y} Q ${(x1+x2)/2} ${y-15} ${x2} ${y}`,class:'legato-line','data-transition':e.transition||'tie'}));if(e.transition)txt(g,(x1+x2)/2,y-6,e.transition==='hammer-on'?'H':'P','legato-label',{'text-anchor':'middle'});}
    }
   }
  }
"""+needle)
s=s.replace("if(e.tie)txt(es,x,160,'⌒'", "if(e.tie&&!(DATA.engravingVersion>=2))txt(es,x,160,'⌒'")
p.write_text(s)
p=Path('skills/smartchord/assets/player.css');s=p.read_text();s+='\n.legato-line{fill:none;stroke:#555;stroke-width:1;pointer-events:none}.legato-label{font:8px Arial,sans-serif;fill:#555;paint-order:stroke;stroke:var(--paper);stroke-width:3px}\n';p.write_text(s)
p=Path('skills/smartchord/scripts/build_html.py');s=p.read_text();s=s.replace("attribution=html.escape(json.dumps(manifest.get('font',{}),ensure_ascii=False))","attribution=html.escape(d.get('sourceAttribution',''))+'<p>'+html.escape(json.dumps(manifest.get('font',{}),ensure_ascii=False))+'</p>'")
s=s.replace("title=html.escape(d['title']);artist=", "title=html.escape(d['title']);artist=")
s=s.replace("'<p><a download=", "'<p><a download=")
s=s.replace("'SUBTITLE':subtitle,", "'SUBTITLE':subtitle+('<br>'+html.escape(d['arrangementNotes']) if d.get('arrangementNotes') else ''),")
p.write_text(s)
p=Path('work/new-song/transcribe.py');s=p.read_text().replace("maxFret=17)","maxFret=17,barsPerSystem=2)").replace("raw=dict(title=", "raw=dict(engravingVersion=2,title=")
p.write_text(s)
