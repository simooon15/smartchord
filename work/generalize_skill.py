from pathlib import Path
import shutil,re
base=Path('/Users/simonluo/.codex/skills/guitar-score-html');dest=base/'assets';src=Path('work/project')
s=(src/'app.js').read_text()
s=s.replace("const $=s=>", "const beats=r=>r.meter[0]*4/r.meter[1];let totalBeats=0;for(const r of rows){r.startBeat=totalBeats;totalBeats+=beats(r)}\nconst esc=t=>String(t).replace(/[&<>\"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',\"'\":'&#39;'}[c]));\nconst $=s=>")
s=s.replace('bpm=76','bpm=DATA.bpm').replace('rows.length*4','totalBeats').replace('(r.i-1)*4','r.startBeat').replace('r.i*4','r.startBeat+beats(r)')
s=re.sub(r'function key\(r\)\{.*?\}\n',"function key(r){return mode==='target'?r.targetKey+' 指法 · 实际 '+r.actualKey+' 调':r.sourceKey+' 指法 · Capo '+DATA.settings.sourceCapo}\n",s)
start=s.index('const easyShapes=');end=s.index('function foundationDiagram',start)
s=s[:start]+"function foundationShape(c){return mode==='target'?DATA.foundationShapes[label(c)]:[...DATA.shapes[c]].reverse()}\n"+s[end:]
s=s.replace('const stride=list.length===3?240:365','const stride=list.length===3?240:365').replace('beatWidth=(barWidth-27)/4;let r=list[k]','r=list[k],beatWidth=(barWidth-27)/beats(r);let unused=list[k]')
s=s.replace("r.section+(r.sourceBarNumber===51?(mode==='target'?' · 1=A / 实际 B':' · 1=D / 不夹'):'')","r.section+' · '+key(r)")
s=s.replace('r.i===93','r.i===rows.length').replace('for(let q=0;q<4;q++)','for(let q=0;q<Math.ceil(beats(r));q++)').replace('Math.min(3.999,','Math.min(beats(r)-.001,')
s=s.replace('<span>仓颉 <small>五月天</small></span>','<span>${esc(DATA.title)} <small>${esc(DATA.artist||\'\')}</small></span>').replace("${mode==='target'?'2':'0'}","${mode==='target'?DATA.capo:DATA.settings.sourceCapo}").replace('· 4/4 ·','· ${rr[0].meter.join(\'/\')} ·').replace("(mode==='target'?'品位相对 Capo 2':'原谱指法 · 不夹')","('品位相对 Capo '+(mode==='target'?DATA.capo:DATA.settings.sourceCapo))")
s=s.replace("$('#mode-label').textContent=mode==='target'?'G → A 指法 · Capo 2':'C → D 指法 · 不夹'","$('#mode-label').textContent=key(rows[0])+' · Capo '+(mode==='target'?DATA.capo:DATA.settings.sourceCapo)")
s=s.replace('let bi=Math.min(rows.length-1,Math.floor(position/4)),r=rows[bi],local=position%4','let r=[...rows].reverse().find(r=>r.startBeat<=position)||rows[0],bi=r.i-1,local=Math.min(beats(r),position-r.startBeat)')
s=s.replace('`${key(rows[Number(el.closest(\'.sheet\').dataset.firstBar)-1])} · Capo ${mode===\'target\'?DATA.capo:DATA.settings.sourceCapo} · 4/4 · ♩ = ${bpm}`','`${key(rows[Number(el.closest(\'.sheet\').dataset.firstBar)-1])} · Capo ${mode===\'target\'?DATA.capo:DATA.settings.sourceCapo} · ♩ = ${bpm}`')
# The tempo callback uses row-local metadata instead of the render loop variable.
s=s.replace("${rr[0].meter.join('/')} · ♩ = ${bpm}`);if(was)","${rows[Number(el.closest('.sheet').dataset.firstBar)-1].meter.join('/')} · ♩ = ${bpm}`);if(was)")
s=s.replace('Math.floor(position/4)+1',"(rows.find(r=>r.startBeat===position)||rows[0]).i")
s=s.replace('window.cangjie=','window.guitarScore=').replace('endBar=93','endBar=rows.length').replace('let len=selected.length*4*60/bpm+2','let len=selected.reduce((sum,r)=>sum+beats(r),0)*60/bpm+8').replace('((r.i-startBar)*4+e.beat)','(r.startBeat-selected[0].startBeat+e.beat)')
s=s.replace("'指法 '+voicingMap.get(voicingKey(e)).id", "(e.technique==='slap'?'拍弦':'指法 '+voicingMap.get(voicingKey(e)).id)")
s=s.replace("let length=Math.max(3.2,(e.sustain||e.duration)*60/tempo)","let length=Math.max(3.2,(e.sustain||e.duration)*60/tempo)")
# Fallback must not quietly replace missing real samples.
a=s.index(' const length=8,sr=c.sampleRate,buf=',s.index('function makeBuffer'));b=s.index('\n}',a)
s=s[:a]+" throw new Error('缺少实际音高 '+pitch+' 的离线采样');"+s[b:]
(dest/'player.js').write_text(s);shutil.copy2(src/'app.css',dest/'player.css')
# The cache is small; final HTML embeds only pitches used by the new song.
shutil.copytree(src/'samples',dest/'sample-cache',ignore=shutil.ignore_patterns('*.wav'),dirs_exist_ok=True)
