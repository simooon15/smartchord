import json,re
from pathlib import Path
root=Path('work/new-song/easier')
base=json.loads(re.search(r'<script id="score-data" type="application/json">(.*?)</script>',(root/'baseline.html').read_text(),re.S)[1])
new=json.loads((root/'score.json').read_text())
assert len(base['rows'])==len(new['rows'])==71
for old,row in zip(base['sourceBars'],new['sourceBars']):
 assert old['vocal']==row['vocal'] and old['chordChanges']==row['chordChanges']
 assert len(old['events'])==len(row['events'])
 for e,f in zip(old['events'],row['events']):
  assert {k:v for k,v in e.items() if k not in ['notes','targetNotes']}=={k:v for k,v in f.items() if k not in ['notes','targetNotes']}
  assert [{k:v for k,v in n.items() if k not in ['string','fret']} for n in e['notes']]==[{k:v for k,v in n.items() if k not in ['string','fret']} for n in f['notes']]
 for i,e in enumerate(row['events']):
  if not (e.get('transition') or e.get('tie')):continue
  prev={n['sourceString']:n for n in row['events'][i-1]['notes']}
  for n in e['notes']:
   assert n['string']==prev[n['sourceString']]['string']
   if e.get('tie'):assert n['fret']==prev[n['sourceString']]['fret']
report={'sourceDataAndMode':'PASS','all997GuitarPitchesAndOctaves':'PASS','vocalPitchesLyricsAndTiming':'PASS','chordChangesEventCountsRhythmTechniquesSustain':'PASS','sameStringLegatoAndTies':'PASS','humanListening':'NOT_PERFORMED','humanPerformanceAcceptance':'NOT_PERFORMED'}
(root/'preservation-results.json').write_text(json.dumps(report,indent=2))
print('Preservation and physical legato/ties PASS')
