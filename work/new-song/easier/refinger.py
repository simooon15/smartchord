"""Song-scoped refingering: every pitch/event retained; beam search across sustained voices."""
import sys,json,itertools,copy,collections
from pathlib import Path
sys.path.insert(0,str(Path('skills/smartchord/scripts').resolve()))
from score_tools import OPEN,fingers,compile_score
OUT=Path('work/new-song/easier')
raw=json.loads(Path('work/new-song/source.json').read_text())
base=json.loads(Path('work/new-song/score.json').read_text())
for im in raw['sourceImages']:im['path']=str((Path('work/new-song')/im['path']).resolve())
flat=[(b,e) for b in raw['sourceBars'] for e in b['events']]
def options(e):
 ps=[OPEN[n['sourceString']]+n['sourceFret']+3 for n in e['notes']]
 opts=[[(s,p-OPEN[s],0) for s in OPEN if 0<=p-OPEN[s]<=10] for p in ps]
 found=[]
 for ch in itertools.product(*opts):
  if len({s for s,f,o in ch})!=len(ch):continue
  fs=[f for s,f,o in ch if f];shape={s:f for s,f,o in ch}
  if fs and max(fs)-min(fs)>5:continue
  if fingers(shape)>4:continue
  if e['technique']=='arpeggio' and any((e['notes'][i]['sourceString']<e['notes'][j]['sourceString'])!=(ch[i][0]<ch[j][0]) for i in range(len(ch)) for j in range(i)):continue
  found.append(ch)
 if not found:raise ValueError(('no options',e))
 return found
# State: cost, held explicit sustain map(source-string -> [target-string,fret,end]), prior source mapping, path.
states=[(0,{}, {}, [])];ledger=[]
for k,(b,e) in enumerate(flat):
 at=(b['sourceBarNumber']-1)*4+e['beat'];poss=options(e);nxt=[]
 for cost,held,prev,path in states:
  held={s:v for s,v in held.items() if v[2]>at+1e-7}
  for ch in poss:
   cur={n['sourceString']:(st,fr) for n,(st,fr,o) in zip(e['notes'],ch)}
   if e.get('tie') and any(prev.get(s)!=v for s,v in cur.items()):continue
   if e.get('transition') and any(s not in prev or prev[s][0]!=v[0] for s,v in cur.items()):continue
   if any(st==hs and fr!=hf for st,fr in cur.values() for hs,hf,end in held.values()):continue
   shape={hs:hf for hs,hf,end in held.values()};shape.update({st:fr for st,fr in cur.values()});fs=[f for f in shape.values() if f]
   if fs and max(fs)-min(fs)>5:continue
   if fingers(shape)>4:continue
   local=sum(fr*.22+(1.8 if fr>5 else 0)+(3 if fr>7 else 0) for st,fr in cur.values())
   local+=max(fs or [0])*.6+(max(fs)-min(fs) if fs else 0)*.35
   for s,(st,fr) in cur.items():
    if s in prev:local+=abs(fr-prev[s][1])*.18+(st!=prev[s][0])*.45
   held2=dict(held)
   if e.get('sustain'):
    for s,(st,fr) in cur.items():held2[s]=(st,fr,at+e['sustain'])
   nxt.append((cost+local,held2,cur,path+[ch]))
 if not nxt:raise ValueError(('no sequence',b['sourceBarNumber'],e['beat']))
 # Deduplicate histories with the same future constraints; retain beam.
 nxt.sort(key=lambda v:v[0]);states=[];seen=set()
 for st in nxt:
  sig=(tuple(sorted(st[1].items())),tuple(sorted(st[2].items())))
  if sig in seen:continue
  seen.add(sig);states.append(st)
  if len(states)==128:break
chosen=states[0][3]
for (b,e),ch in zip(flat,chosen):
 old=e['targetNotes'];e['targetNotes']=[list(n) for n in ch]
 ledger.append({'bar':b['sourceBarNumber'],'beat':e['beat'],'before':old,'after':e['targetNotes'],'transition':e.get('transition'),'tie':e.get('tie',False)})
raw['arrangementNotes']='易按指法版：G 指法 · Capo 2 · 实际 A。全部旋律、伴奏音高、八度、节奏与歌词保留；优先空弦和低把位，保留同弦滑音及击勾弦。少数高音仍需 7–10 品，第 50 小节保留原八度时仍有一次 3 品＋8 品双音跨度；完整六弦琶音仍需横按。和弦图为基础按法，具体换指以六线谱为准。可先降到 50 BPM 分段练习。'
score=compile_score(raw)
old=[n['fret'] for b in base['sourceBars'] for e in b['events'] for n in e['notes']]
new=[n['fret'] for b in score['sourceBars'] for e in b['events'] for n in e['notes']]
report={'preservedNotes':len(new),'changedPositions':sum(v['before']!=v['after'] for v in ledger),'before':{'maxFret':max(old),'openNotes':old.count(0),'above5':sum(f>5 for f in old),'frets':dict(collections.Counter(old))},'after':{'maxFret':max(new),'openNotes':new.count(0),'above5':sum(f>5 for f in new),'frets':dict(collections.Counter(new))},'events':ledger}
for name,data in [('source.json',raw),('score.json',score),('refingering-report.json',report)]: (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='events'},ensure_ascii=False))
