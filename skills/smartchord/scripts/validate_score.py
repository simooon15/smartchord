"""Meaningful structural invariants. This cannot certify screenshot transcription."""
import argparse,json
from pathlib import Path
from score_tools import OPEN,foundation
p=argparse.ArgumentParser();p.add_argument('score');p.add_argument('--raw');a=p.parse_args();d=json.loads(Path(a.score).read_text());cfg=d['settings'];assert not d.get('unresolved');assert d['rows']
seen=set()
for b in d['sourceBars']:
 assert b['sourceBarNumber'] not in seen;seen.add(b['sourceBarNumber']);limit=b['meter'][0]*4/b['meter'][1];last=-1
 for e in b['events']:
  assert last<=e['beat']<limit and e['duration']>0 and e['beat']+e['duration']<=limit+1e-6;last=e['beat'];used=set()
  for n in e['notes']:
   assert n['string'] not in used;used.add(n['string']);assert 0<=n['fret']<=cfg.get('maxFret',17);assert n['pitchBefore']==OPEN[n['sourceString']]+n['sourceFret']+cfg['sourceCapo'];assert n['pitchAfter']==OPEN[n['string']]+n['fret']+d['capo'];assert n['pitchAfter']==n['pitchBefore']+cfg['actualSemitones']+12*n['octaveException']
for i,r in enumerate(d['rows'],1):assert r['i']==i and r['sourceBarNumber'] in seen
held_end=None;cursor=0
for r in d['rows']:
 limit=r['meter'][0]*4/r['meter'][1];last=-1
 for v in r.get('vocal',[]):
  assert last<=v['beat']<limit and v['duration']>0 and v['beat']+v['duration']<=limit+1e-6;last=v['beat'];at=cursor+v['beat']
  if v['degree']==0:held_end=None
  elif v['degree'] is None or v.get('tie'):
   assert held_end is not None and abs(held_end-at)<1e-6,('Orphan melody sustain',r['i'],v)
   held_end=at+v['duration']
  else:
   assert 1<=v['degree']<=7 and isinstance(v.get('pitchBefore'),(int,float)) and v['pitchAfter']==v['pitchBefore']+cfg['actualSemitones']
   held_end=at+v['duration']
 cursor+=limit
for c,shape in d['foundationShapes'].items():foundation(c,shape)
if a.raw:
 raw=json.loads(Path(a.raw).read_text());assert len(raw['sourceBars'])==len(d['sourceBars'])
 for source,target in zip(raw['sourceBars'],d['sourceBars']):
  assert source['sourceBarNumber']==target['sourceBarNumber'];assert len(source['events'])==len(target['events'])
  assert len(source.get('vocal',[]))==len(target.get('vocal',[]))
  for x,y in zip(source.get('vocal',[]),target.get('vocal',[])):
   for k in ['beat','duration','degree','octave','accidental','lyric','tie']:assert x.get(k)==y.get(k),('Melody notation changed',source['sourceBarNumber'],k)
  for x,y in zip(source['events'],target['events']):assert (x['beat'],x['duration'],x['technique'])==(y['beat'],y['duration'],y['technique']) and [(n['sourceString'],n['sourceFret']) for n in x.get('notes',[])]==[(n['sourceString'],n['sourceFret']) for n in y['notes']]
print('Pitch/capo, independent strings, timing, chord tones/bass and source-event conservation PASS')
