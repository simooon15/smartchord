from pathlib import Path
import json
p=Path('skills/smartchord/scripts/score_tools.py');s=p.read_text();pos=s.index('def compile_score(raw):')
s=s[:pos]+'''def compile_vocal(v,b,cfg,shift):
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

'''+s[pos:]
s=s.replace("if v.get('pitchBefore') is not None:v['pitchAfter']=v['pitchBefore']+shift", "compile_vocal(v,b,cfg,shift)",1)
s=s.replace("if v.get('pitchBefore') is not None:v['pitchAfter']=v['pitchBefore']+shift", "compile_vocal(v,row,cfg,shift)",1);p.write_text(s)
p=Path('work/new-song/source.json');d=json.loads(p.read_text());d['settings']['sourceVocalTonicMidi']=64;p.write_text(json.dumps(d,ensure_ascii=False,indent=2))
p=Path('work/new-song/transcribe.py');s=p.read_text().replace('maxFret=17,','sourceVocalTonicMidi=64,maxFret=17,');p.write_text(s)
# Fail at build time, not on first toggle, for incomplete melody data.
for p in [Path('skills/smartchord/scripts/build_html.py'),Path('work/project/build.py')]:
 s=p.read_text();needle=" samples=Path(samples)" if p.name=='build_html.py' else "sample_manifest="
 validation=(" for r in d['rows']:\n  for v in r['vocal']:\n   if v.get('degree') and not all(isinstance(v.get(k),(int,float)) for k in ['pitchBefore','pitchAfter']):raise ValueError('Incomplete melody pitch')\n" if p.name=='build_html.py' else "for r in DATA['rows']:\n for v in r['vocal']:\n  if v.get('degree') and not all(isinstance(v.get(k),(int,float)) for k in ['pitchBefore','pitchAfter']):raise ValueError('Incomplete melody pitch')\n")
 s=s.replace(needle,validation+needle,1);p.write_text(s)
