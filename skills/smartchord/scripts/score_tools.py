"""Source-backed score compiler; standard six-string guitar, quarter-note beat units."""
import argparse,copy,json,itertools,re
from pathlib import Path
OPEN={1:64,2:59,3:55,4:50,5:45,6:40}
PCS={'C':0,'B#':0,'C#':1,'Db':1,'D':2,'D#':3,'Eb':3,'E':4,'Fb':4,'F':5,'E#':5,'F#':6,'Gb':6,'G':7,'G#':8,'Ab':8,'A':9,'A#':10,'Bb':10,'B':11,'Cb':11}
NAMES=['C','C#','D','Eb','E','F','F#','G','G#','A','Bb','B']
def key_pc(key):
 return PCS[re.fullmatch(r'([A-G][b#]?)(?:m|minor|major)?',key).group(1)]
def shift_label(label,shift):
 return re.sub(r'(^|/)([A-G][b#]?)',lambda m:m[1]+NAMES[(PCS[m[2]]+shift)%12],label)
def fingers(shape):
 count=0
 for fret in sorted({f for f in shape.values() if f and f>0}):
  members=sorted(s for s,f in shape.items() if f==fret);count+=1
  for a,b in zip(members,members[1:]):
   if any(shape.get(s,99)<fret for s in range(a+1,b)):count+=1
 return count

def assign(notes,shift,capo,allow_octaves,max_fret=17,preserve=False):
 targets=[n['pitchBefore']+shift-capo for n in notes];best=None
 def search(k,used,chosen,cost):
  nonlocal best
  if best and cost>best[0]:return
  if k==len(targets):
   fs=[f for s,f,o in chosen if f>0];span=max(fs)-min(fs) if fs else 0
   if span>5 or fingers({s:f for s,f,o in chosen})>4:return
   value=(cost,max(fs or [0])*.025+span*.15,chosen)
   if best is None or value<best:best=value
   return
  p=targets[k]
  opts=[]
  for octave in ([0,1,-1,2,-2] if allow_octaves else [0]):
   for string in OPEN:
    fret=p+12*octave-OPEN[string]
    if string not in used and 0<=fret<=max_fret:opts.append((abs(octave),string,fret,octave))
  for penalty,st,fr,octave in sorted(opts):
   q=p+12*octave
   if preserve and any((notes[j]['sourceString']<notes[k]['sourceString'] and ss>=st) or (notes[j]['sourceString']>notes[k]['sourceString'] and ss<=st) or (targets[j]<p and OPEN[ss]+ff>q) or (targets[j]>p and OPEN[ss]+ff<q) for j,(ss,ff,oo) in enumerate(chosen)):continue
   search(k+1,used|{st},chosen+[(st,fr,octave)],cost+penalty)
 search(0,set(),[],0)
 if best is None:raise ValueError('No playable fingering: '+str(targets)+'. Inspect source or explicitly choose octave policy; do not drop notes.')
 return best[2]

def chord_pcs(name):
 m=re.fullmatch(r'([A-G][b#]?)([^/]*)(?:/([A-G][b#]?))?',re.sub(r'\(\d+\)', '', name))
 if not m:raise ValueError('Unsupported chord '+name)
 root,quality,bass=m.groups();types={'':[0,4,7],'m':[0,3,7],'7':[0,4,7,10],'maj7':[0,4,7,11],'m7':[0,3,7,10],'sus4':[0,5,7],'sus2':[0,2,7],'dim':[0,3,6],'dim7':[0,3,6,9],'aug':[0,4,8],'add9':[0,4,7,2],'9':[0,4,7,10,2],'maj9':[0,4,7,11,2],'m9':[0,3,7,10,2],'6':[0,4,7,9],'m6':[0,3,7,9],'m7b5':[0,3,6,10],'add#11':[0,4,7,6],'maj7add13':[0,4,7,11,9],'madd9':[0,3,7,2]}
 if quality not in types:raise ValueError('Supply independently verified shape for '+name)
 bass=PCS[bass or root];return {(PCS[root]+v)%12 for v in types[quality]}|{bass},bass

def foundation(name,override=None):
 expected,bass=chord_pcs(name)
 if override is not None:
  ps=[OPEN[6-i]+f for i,f in enumerate(override) if f is not None]
  if len(override)!=6 or {p%12 for p in ps}!=expected or min(ps)%12!=bass:raise ValueError('Chord diagram mismatch: '+name)
  if fingers({6-i:f for i,f in enumerate(override) if f is not None})>4:raise ValueError('Diagram exceeds four fingers: '+name)
  return override
 best=None
 for limit in [5,9,12]:
  choices=[[None]+[f for f in range(limit+1) if (OPEN[s]+f)%12 in expected] for s in range(6,0,-1)]
  for fs in itertools.product(*choices):
   ps=[OPEN[6-i]+f for i,f in enumerate(fs) if f is not None]
   if not ps or {p%12 for p in ps}!=expected or min(ps)%12!=bass:continue
   positive=[f for f in fs if f];span=max(positive)-min(positive) if positive else 0
   if span>4 or fingers({6-i:f for i,f in enumerate(fs) if f is not None})>4:continue
   score=max(positive or [0])*.8+len(positive)*.5+sum(f is None for f in fs)*.25+span*.3
   if best is None or score<best[0]:best=(score,list(fs))
  if best:return best[1]
 raise ValueError('Provide verified foundation fingering for '+name)

def compile_vocal(v,b,cfg,shift):
 if v.get('degree') in (None,0):return
 if not 1<=v['degree']<=7:raise ValueError('Vocal degree outside 1-7')
 if v.get('pitchBefore') is None:
  tonic=cfg.get('sourceVocalTonicMidi')
  if tonic is None:raise ValueError('Pitched vocal needs verified pitchBefore or sourceVocalTonicMidi')
  if tonic%12!=(key_pc(cfg['sourceFingeringKey'])+cfg.get('sourceCapo',0))%12:raise ValueError('Vocal tonic conflicts with source key / Capo')
  modulation=(key_pc(b['sourceKey'])-key_pc(cfg['sourceFingeringKey']))%12
  if modulation>6:modulation-=12
  v['pitchBefore']=tonic+modulation+[0,2,4,5,7,9,11][v['degree']-1]+v.get('accidental',0)+12*v.get('octave',0)
 v['pitchAfter']=v['pitchBefore']+shift

def compile_score(raw):
 d=copy.deepcopy(raw);cfg=d['settings'];capo=int(cfg['targetCapo']);source_capo=int(cfg.setdefault('sourceCapo',0))
 if not 0<=capo<=12 or not 0<=source_capo<=12:raise ValueError('Capo outside 0–12')
 minor=lambda key:key.endswith('m') or key.endswith('minor')
 if minor(cfg['sourceFingeringKey'])!=minor(cfg['targetFingeringKey']):raise ValueError('Major/minor mode change is arrangement, not pure transposition')
 actual=(key_pc(cfg['targetFingeringKey'])+capo)%12
 if cfg.get('targetActualKey') and (key_pc(cfg['targetActualKey'])!=actual or minor(cfg['targetActualKey'])!=minor(cfg['targetFingeringKey'])):raise ValueError('Target fingering key + capo conflicts with actual key')
 source_actual=(key_pc(cfg['sourceFingeringKey'])+source_capo)%12
 shift=cfg.get('actualSemitones',(actual-source_actual+6)%12-6)
 if (source_actual+shift)%12!=actual:raise ValueError('actualSemitones conflicts with target actual key')
 cfg.update(targetActualKey=shift_label(cfg['targetFingeringKey'],capo),actualSemitones=shift)
 d['capo']=capo;d['bpm']=d.get('bpm',76);d['transposition']={};d['octaveExceptions']=[];cache={}
 if d.get('unresolved'):raise ValueError('Unresolved source interpretation: '+str(d['unresolved']))
 for b in d['sourceBars']:
  b.setdefault('meter',[4,4]);b.setdefault('vocal',[]);b.setdefault('section','全曲');b.setdefault('sourceKey',cfg['sourceFingeringKey']);b['targetKey']=shift_label(b['sourceKey'],shift+source_capo-capo);b['actualKey']=shift_label(b['sourceKey'],shift+source_capo)
  beats=b['meter'][0]*4/b['meter'][1]
  if not b['chordChanges'] or b['chordChanges'][0][0]!=0:raise ValueError('Chord at bar start required')
  for t,c in b['chordChanges']:d['transposition'][c]=shift_label(re.sub(r'\(\d+\)', '', c),shift+source_capo-capo)
  for e in b['events']:
   if not 0<=e['beat']<beats or e['duration']<=0 or e['beat']+e['duration']>beats+1e-6:raise ValueError('Event timing outside bar')
   c=next(c for t,c in reversed(b['chordChanges']) if t<=e['beat']);e['chord']=c;e['targetChord']=d['transposition'][c];e.setdefault('notes',[])
   for n in e['notes']:
    s,f=n['sourceString'],n['sourceFret']
    if n.get('sourceSymbol')=='×' and d['shapes'][c][s-1]!=f:raise ValueError('Cross/diagram mismatch')
    n['pitchBefore']=OPEN[s]+f+source_capo
   sig=(e['technique'],tuple((n['sourceString'],n['sourceFret']) for n in e['notes']))
   if sig not in cache:cache[sig]=assign(e['notes'],shift,capo,cfg.get('allowOctaveAdjustments',False),cfg.get('maxFret',17),e['technique'] in ('strum','arpeggio'))
   chosen=e.get('targetNotes',cache[sig])
   if len(chosen)!=len(e['notes']):raise ValueError('Manual target override loses source voices')
   for n,(s,f,o) in zip(e['notes'],chosen):
    n.update(string=s,fret=f,octaveException=o,pitchAfter=OPEN[s]+f+capo)
    if o:d['octaveExceptions'].append({'bar':b['sourceBarNumber'],'beat':e['beat'],'sourceString':n['sourceString'],'sourceFret':n['sourceFret'],'sourcePitch':n['pitchBefore'],'targetPitchRelativeCapo':OPEN[s]+f,'octaves':o,'reason':'六根独立弦、可按指法与声部次序限制'})
   for n in e['notes']:
    assert n['pitchAfter']==n['pitchBefore']+shift+12*n['octaveException']
  for v in b['vocal']:
   compile_vocal(v,b,cfg,shift)
 d['foundationShapes']={c:foundation(c,d.get('foundationShapes',{}).get(c)) for c in set(d['transposition'].values())}
 bars={b['sourceBarNumber']:b for b in d['sourceBars']};d['rows']=[];counts={}
 for occurrence in d.get('performance',list(bars)):
  n=occurrence if isinstance(occurrence,int) else occurrence['bar'];row=copy.deepcopy(bars[n]);counts[n]=counts.get(n,0)+1;row.update(i=len(d['rows'])+1,**{'pass':counts[n]})
  if isinstance(occurrence,dict):
   if 'vocal' in occurrence:row['vocal']=copy.deepcopy(occurrence['vocal'])
   if 'section' in occurrence:row['section']=occurrence['section']
  for v in row['vocal']:
   compile_vocal(v,row,cfg,shift)
  d['rows'].append(row)
 return d
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('input');a.add_argument('output');args=a.parse_args();d=compile_score(json.loads(Path(args.input).read_text()));Path(args.output).write_text(json.dumps(d,ensure_ascii=False,indent=2));print('Compiled',len(d['sourceBars']),'source bars;',len(d['rows']),'performed bars;',len(d['octaveExceptions']),'explicit octave exceptions')
