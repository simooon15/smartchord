"""Screenshot-backed transcription. Beat units are quarter notes. No generated accompaniment."""
from pathlib import Path
import json, itertools, copy, hashlib
P=Path(__file__).resolve().parent
ROOT=next(root for root in [P.parent/'SOURCE_SCREENSHOTS',P.parent/'handoff'/'SOURCE_SCREENSHOTS'] if root.is_dir())
OPEN={1:64,2:59,3:55,4:50,5:45,6:40}
SHAPES={'C':[0,1,0,2,3,None],'C/Bb':[0,1,0,2,1,None],'Am':[0,1,2,2,0,None],
'Abmaj7':[3,4,5,5,None,4],'G':[3,0,0,0,2,3],'Cmaj7':[0,0,0,2,3,None],
'Am7':[0,1,0,2,0,None],'Am7/G':[0,1,0,2,0,3],'Fmaj7':[0,1,2,3,0,1],
'F':[1,1,2,3,3,1],'Gsus4':[3,1,0,0,2,3],'G7':[1,0,0,0,2,3],
'Em7/B':[0,3,0,0,2,None],'Gm7':[3,3,3,3,5,3],'C7':[0,1,3,2,3,None],
'C/E':[0,1,0,2,3,0],'Dm7':[1,1,2,0,None,None],'Bb':[1,3,3,3,1,None],
'D':[2,3,2,0,None,None],'F#m7/C#':[2,5,2,2,4,None],'Bm7':[2,3,2,4,2,None],
'D/F#':[2,3,2,0,0,2],'Em7':[0,3,0,2,2,0],'A':[0,2,2,2,0,None],
'A/C#':[0,2,2,2,4,0],'D7':[2,1,2,0,None,None]}
TRAN={'C':'G','C/Bb':'G/F','Am':'Em','Abmaj7':'Ebmaj7','G':'D','Cmaj7':'Gmaj7','Am7':'Em7','Am7/G':'Em7/D','Fmaj7':'Cmaj7','F':'C','Gsus4':'Dsus4','G7':'D7','Em7/B':'Bm7/F#','Gm7':'Dm7','C7':'G7','C/E':'G/B','Dm7':'Am7','Bb':'F','D':'A','F#m7/C#':'C#m7/G#','Bm7':'F#m7','D/F#':'A/C#','Em7':'Bm7','A':'E','A/C#':'E/G#','D7':'A7'}
BARS={}
def bar(n,changes,shot,region):
 b={'sourceBarNumber':n,'sourceScreenshot':'IMG_'+shot+'.PNG','sourceRegion':region,'meter':[4,4],'chordChanges':changes,'events':[],'vocal':[]};BARS[n]=b;return b

def chord(b,t):return next(c for at,c in reversed(b['chordChanges']) if at<=t)
def notes(b,t,d,marks,tech='pluck',tie=False):
 c=chord(b,t);ns=[]
 for s,f in marks:
  sym='×' if f=='x' else str(f); fret=SHAPES[c][s-1] if f=='x' else f
  assert fret is not None,(b['sourceBarNumber'],t,s,c)
  ns.append({'sourceString':s,'sourceFret':fret,'sourceSymbol':sym,'pitchBefore':OPEN[s]+fret})
 b['events'].append({'beat':t,'duration':d,'technique':tech,'chord':c,'notes':ns,'tie':tie})
BASS={'C':5,'C/Bb':5,'Am':5,'Abmaj7':6,'G':6,'Cmaj7':5,'Am7':5,'Am7/G':6,'Fmaj7':6,'F':6,'Gsus4':6,'G7':6,'Em7/B':5,'Gm7':6,'C7':5,'C/E':6,'Dm7':4,'Bb':5,'D':4,'F#m7/C#':5,'Bm7':5,'D/F#':6,'Em7':6,'A':5,'A/C#':5,'D7':4}
def strum(b,t,d,kind='down',tie=False):
 # Source arrows: toward treble = downstroke; short downstroke terminates at string 3.
 c=chord(b,t)
 ss={'rootDown':range(BASS[c],0,-1),'down':range(4,0,-1),'up':range(1,5),'bassDown':range(BASS[c],2,-1)}[kind]
 ns=[(s,'x') for s in ss if SHAPES[c][s-1] is not None]
 notes(b,t,d,ns,'strum',tie);b['events'][-1].update(direction='up' if kind=='up' else 'down',sourceStringRange=list(ss))
def box(b,t,d):b['events'].append({'beat':t,'duration':d,'technique':'slap','sourceSymbol':'boxed ×','sourceString':6,'chord':chord(b,t),'notes':[]})

def melody(b,sequence,lyric=''):
 # degree, octave, duration, lyric; '-' means tied continuation, 0 rest.
 at=0
 for token in sequence.split():
  sym,ds=token.split(':');d=float(ds);octave=sym.count("'") if "'" in sym else -1 if sym.endswith(',') else 0
  deg=int(sym.strip("',")) if sym!='-' else None
  b['vocal'].append({'beat':at,'duration':d,'degree':deg,'octave':octave,'tie':sym=='-','symbol':sym,'lyric':''});at+=d
 assert abs(at-4)<1e-8,(b['sourceBarNumber'],at,sequence)
 chars=lyric.split('/') if '/' in lyric else [lyric] if lyric in ('oh','啊') else list(lyric)
 attacks=[v for v in b['vocal'] if v['degree'] not in (0,None)]
 # Explicit lyrics supplied below with empty entries for ties/slurs.
 assert len(chars)<=len(attacks),(b['sourceBarNumber'],lyric,len(chars),len(attacks))
 for v,c in zip(attacks,chars):v['lyric']=c

# Every repeated guitar figure below was checked against the cited full system.
for n,c,shot,reg in [(1,'C','7041',[0,375,632,950]),(2,'C/Bb','7041',[632,375,1206,950]),(3,'Am','7041',[0,985,418,1510]),(31,'C','7045',[710,1370,1206,1960]),(32,'C/Bb','7046',[0,200,475,700])]:
 b=bar(n,[[0,c]],shot,reg)
 notes(b,0,.5,[(5,'x'),(1,'x')]+([(2,'x')] if n in (1,31) else []))
 for t in [.5,1.5,2.5]:notes(b,t,.5,[(3,'x')])
 for t in [1,2]:notes(b,t,.5,[(1,'x')]+([(2,'x')] if n in (1,31) else []))
 for t,s,f in [(3,1,'x'),(3.25,1,1),(3.5,1,1),(3.75,2,3)]:notes(b,t,.25,[(s,f)])
 melody(b,'0:1 0:1 0:1 0:1')
b=bar(4,[[0,'Abmaj7'],[2,'G']],'7041',[418,985,716,1510])
notes(b,0,.5,[(6,'x'),(3,'x'),(2,'x'),(1,'x')]);notes(b,.5,.5,[(4,'x')]);notes(b,1,1,[(2,6)]);notes(b,2,.5,[(6,'x'),(2,1)]);notes(b,2.5,.5,[(4,'x')]);notes(b,3,1,[(2,3)]);melody(b,'0:1 0:1 0:1 0:1')
mainC=[5,9,13,17];mainMaj=[6,10,14,18];mainAm=[7,11,15,19];mainF=[8,12,16,20]
for n in mainC+mainMaj+mainAm+mainF+[21]:
 shot='7041' if n<=8 else '7042' if n<=14 else '7043' if n<=18 else '7044'
 c='C' if n in mainC else 'Cmaj7' if n in mainMaj else 'Am7' if n in mainAm else 'Gsus4' if n==21 else 'F' if n in (12,20) else 'Fmaj7'
 changes=[[0,c]]+([[2,'Am7/G']] if c=='Am7' else [])
 b=bar(n,changes,shot,[])
 if c=='Am7':
  groups=[[(5,'x')],[(3,'x')],[(1,'x'),(2,'x')],[(3,'x')],[(6,'x')],[(4,'x')],[(2,'x'),(3,'x')],[(4,'x')]]
 elif c=='Gsus4':
  groups=[[(6,'x'),(1,'x'),(2,'x'),(3,'x')],[(4,'x')],[(2,'x'),(3,'x')],[(4,'x')],[(2,'x'),(3,'x')],[(4,'x')],[(2,'x'),(3,'x')],[(4,'x')]]
 else:
  groups=[[(5 if c in ('C','Cmaj7') else 6,'x'),(1,'x'),(2,3 if n==5 else 'x')],[(3,'x')],[(1,'x'),(2,'x')],[(3,'x')],[(1,'x'),(2,'x')],[(3,'x')],[(1,'x'),(2,'x')],[(3,'x')]]
 for j,g in enumerate(groups):notes(b,j/2,.5,g)
b=bar(22,[[0,'G']],'7044',[0,890,508,1460]);strum(b,0,4,'rootDown');b['events'][0]['technique']='arpeggio';melody(b,'0:1 0:1 0:1 0:0.5 5:0.5','多')
# 10 precisely observed strokes per regular chorus bar, not the legacy 9-stroke pattern.
STROKES=[(0,1,'rootDown'),(1,.5,'down'),(1.5,.25,'down'),(1.75,.25,'up'),(2,.25,'bassDown'),(2.25,.25,'up'),(2.5,.5,'bassDown'),(3,.5,'down'),(3.5,.25,'down'),(3.75,.25,'up')]
changes={23:[[0,'C'],[2,'Em7/B']],24:[[0,'Am7'],[2,'Gm7'],[3,'C7']],25:[[0,'F'],[2,'C/E']],26:[[0,'Dm7'],[2,'G']],27:[[0,'C'],[2,'Em7/B']],28:[[0,'Am7'],[2,'Gm7'],[3,'C7']],29:[[0,'F'],[2,'C/E']],30:[[0,'Dm7'],[2,'G']],42:[[0,'G']],43:[[0,'C'],[2,'Em7/B']],44:[[0,'Am7'],[2,'Gm7'],[3,'C7']],45:[[0,'F'],[2,'C/E']],46:[[0,'Dm7'],[2,'G']],47:[[0,'C'],[2,'Em7/B']],48:[[0,'Am7'],[2,'Gm7'],[3,'C7']],49:[[0,'F'],[2,'C/E']],50:[[0,'Dm7'],[2,'G']],51:[[0,'D'],[2,'F#m7/C#']],52:[[0,'Bm7'],[2,'Am7'],[3,'D7']],53:[[0,'G'],[2,'D/F#']],54:[[0,'Em7'],[2,'A']],55:[[0,'Bm7'],[2,'A/C#']],56:[[0,'D'],[2,'Am7'],[3,'D7']],57:[[0,'G'],[2,'D/F#']],58:[[0,'Em7'],[2,'A']],59:[[0,'D']],60:[[0,'C']],61:[[0,'Bm7']],62:[[0,'A']],63:[[0,'D']],64:[[0,'C']],65:[[0,'Bm7']],66:[[0,'A']]}
for n,cs in changes.items():
 shot='7044' if n<=25 else '7045' if n<=30 else '7051' if n<=44 else '7052' if n<=50 else '7053' if n<=56 else '7054' if n<=62 else '7056'
 b=bar(n,cs,shot,[])
 for t,d,k in STROKES:strum(b,t,d,k)
b=bar(33,[[0,'Am'],[3.5,'G7']],'7046',[475,200,883,700])
for t,d,ns in [(0,.5,[(5,'x'),(1,'x'),(2,'x')]),(.5,.5,[(3,'x')]),(1,.5,[(1,'x'),(2,'x')]),(1.5,.5,[(3,'x')]),(2,.5,[(2,'x')]),(2.5,.5,[(2,0)]),(3,.5,[(3,'x')])]:notes(b,t,d,ns)
strum(b,3.5,.5,'rootDown');melody(b,'0:1 0:1 0:1 0:1')
b=bar(34,[[0,'G7'],[2,'F'],[3,'G']],'7046',[883,200,1206,700]);strum(b,0,1,'rootDown',tie=True);strum(b,1,.5);strum(b,1.5,.25);strum(b,1.75,.25,'up');strum(b,2,1,'rootDown');strum(b,3,1,'rootDown');melody(b,'0:1 0:1 0:1 0:1')
# Instrumental variations transcribed independently from 7050/7051.
for n in (35,37,39):
 b=bar(n,[[0,'F'],[1.5,'C']] if n==35 else [[0,'C']],'7050' if n<39 else '7051',[])
 strum(b,0,.75,'rootDown');strum(b,.75,.25,'up');box(b,1,.5);strum(b,1.5,1.5,'rootDown')
 if n in (35,37):
  for t,s,f in [(3,3,'x'),(3.25,3,2),(3.5,2,'x'),(3.75,2,3)]:notes(b,t,.25,[(s,f)])
 else:
  notes(b,3,.25,[(2,'x')]);notes(b,3.25,.25,[(3,2)]);notes(b,3.5,.5,[(3,2)])
 melody(b,'0:1 0:1 0:1 0:1')
for n in (36,38,40):
 b=bar(n,[[0,'Bb']],'7050' if n<40 else '7051',[])
 notes(b,0,.75,[(5,'x'),(2,'x'),(1,0 if n==40 else 'x')]);notes(b,.75,.25,[(2,'x'),(3,'x')] if n==40 else [(1,0)]);box(b,1,.5)
 notes(b,1.5,1.5,[(2,'x'),(3,'x')] if n==40 else [(2,'x')])
 if n==36:notes(b,3,.5,[(4,'x')]);notes(b,3.5,.25,[(3,'x')]);notes(b,3.75,.25,[(4,'x')])
 if n==38:notes(b,3,.5,[(3,'x')]);notes(b,3.5,.25,[(3,5)]);notes(b,3.75,.25,[(3,'x')])
 if n==40:
  for t,s,f in [(3,1,'x'),(3.25,1,0),(3.5,2,'x'),(3.75,2,1)]:notes(b,t,.25,[(s,f)])
 melody(b,'0:1 0:1 0:1 0:1')
b=bar(41,[[0,'Am']],'7051',[0,660,683,1200])
notes(b,0,.25,[(5,'x'),(1,3)])
for t in [.25,.5,.75,1]:notes(b,t,.25,[(1,'x')])
for t in [1.25,1.5,1.75,2]:notes(b,t,.25,[(2,3)])
for t,d,f in [(2.25,.25,'x'),(2.5,.25,0),(2.75,.125,'x'),(2.875,.125,0)]:notes(b,t,d,[(2,f)])
notes(b,3,.25,[(3,'x')]);notes(b,3.25,.25,[(3,0)],'pull-off');notes(b,3.5,.5,[(2,3)]);melody(b,'0:1 0:1 0:1 0:1')
b=bar(67,[[0,'D']],'7056',[850,880,1125,1420]);strum(b,0,4,'rootDown');b['events'][0]['technique']='arpeggio';melody(b,'0:1 0:1 0:1 0:1')
# Vocal numbers: rhythmic alignment comes from original underlines, dots and ties.
M={5:('0:.5 5:.5 5:.25 5:.25 5:.5 -:.5 4:.5 3:.5 4:.25 5:.25','一/颗/葡/萄/有/多/甜/美'),6:('-:2 0:.5 5:.5 6:.5 7:.5','用尽了'),7:("1':1 3':.5 7:.5 -:.5 6:.5 -:.5 5:.5",'所/有/的/图/腾'),8:("5:.5 6:.5 1':.5 1':.5 -:.5 2':.5 -:.5 3':.5",'和/语//言/描/写'),9:("3':.5 5:.5 5:.5 5:.25 5:.25 -:.5 5:.5 6:.5 7:.25 7:.25",'/想/一/个/人/有/多/想/念'),10:('-:.5 5:.5 -:1 0:.5 5:.5 6:.5 7:.5','/那/又/是'),11:("1':.5 3':.5 3':.5 3':.5 -:.5 2':.5 -:.5 1':.5",'文//字/失/效/瞬'),12:("2':.25 1':.25 1':.5 -:2 0:1",'间'),13:('0:.5 5:.5 5:.5 5:.25 5:.25 -:.5 4:.5 3:.5 4:.25 5:.25','结/一/个/纪/念/的/绳/结'),14:('-:2 0:.5 5:.5 6:.5 7:.5','记录你'),15:("1':1 3':.5 7:.5 -:.5 6:.5 -:.5 5:.5",'离/去/后/万/语'),16:("5:.5 6:.5 1':.5 1':.5 -:.5 2':.5 -:.5 3':.5",'和/千//言/瓦/解'),17:("3':.5 5:.5 5:.5 5:.25 5:.25 -:.5 5:.5 6:.5 7:.25 7:.25",'/升/起/了/慌/张/的/狼/烟'),18:('-:.5 5:.5 -:1 0:.5 5:.5 6:.5 7:.5','/我/遗/落'),19:("1':.25 2':.25 1':.5 7:.5 -:.5 1':.5 -:.5 3':1",'在/最/孤/独/史/前'),20:("-:2 0:.5 3':.5 4':.5 3':.5",'的/荒/野'),21:("-:.5 2':.5 -:3",'')}
# Lyrics are aligned explicitly to attacks; tied continuations are not rearticulated.
# Empty lyric entries are intentional melisma.
for n,(s,l) in M.items():melody(BARS[n],s,l)
A="2':.75 3':.25 -:.5 5':.5 2':.75 3':.25 -:.5 5':.5"
B="2':.75 3':.25 -:.5 5':.5 5':.5 3':.5 2':.5 1':.5"
C="2':.75 3':.25 -:.5 5':.5 2':.5 1':.5 1':1"
D="4':.75 3':.25 -:.5 1':.5 6:.5 5:.25 5:.25 -:.5 5:.5"
E="-:1.5 6:.5 1':1 -:1"
F="4':.5 4':.25 4':.25 4':.5 1':.25 6:.25 5:.25 2':.75 1':.25 -:.25 1':.5"
for n,s,l in [(23,A,'遥/远/多/纠/结/多'),(24,B,'想/念/多/无/法/描/写'),(25,C,'疼/痛/和/疯//癫'),(26,D,'你/都/看/不/见//想'),(27,A,'穿/越/想/飞/天/想'),(28,B,'变/成/造/字/的/仓/颉'),(29,E,'写/出'),(30,F,'能/让/你/快/回/来/的/诗//篇'),(42,'0:1 0:1 0:1 0:.5 5:.5','多'),(43,A,'遥/远/多/纠/结/多'),(44,B,'想/念/多/无/法/描/写'),(45,C,'疼/痛/和/疯//癫'),(46,D,'你/都/看/不/见//想'),(47,A,'穿/越/想/飞/天/想'),(48,B,'变/成/造/字/的/仓/颉'),(49,E,'写/出'),(50,"4':.5 4':.25 4':.25 4':.5 1':.25 6:.25 5:.25 2':.75 2':.5 5:.5",'能/让/你/快/回/来/的/诗//需'),(51,A,'要/你/需/要/你/需'),(52,B,'要/你/想/逆/转/时/间'),(53,C,'回/到/最/开//始'),(54,D,'有/你/的/世/界//想'),(55,A,'穿/越/想/飞/天/想'),(56,B,'变/成/造/字/的/仓/颉'),(57,E,'写/出'),(58,F,'让/宇/宙/能/重/来/的/诗//篇'),(59,'-:4',''),(60,'0:1 0:1 0:1 0:1',''),(61,"0:1 6':1 5':1 3':1",'啊'),(62,"5':.75 7':.25 -:3",'啊'),(63,"3':.5 1':.5 5':1 3':1 4':1",'oh'),(64,"4':.5 1':.5 4':.5 5':.5 6':.5 3':.5 4':.5 3':.5",'oh'),(65,"-:.5 1':.5 -:.5 1'':.5 -:.5 5':.5 1'':.5 2'':.5",''),(66,'-:4','')]:melody(BARS[n],s,l)

# Preserve exact pitch first. Revoice only when six simultaneous source voices
# cannot occupy six distinct strings. Each octave displacement is recorded.
def assign(ns,preserve_voices=False):
 pitches=[n['pitchBefore']-5 for n in ns]
 candidates=[]
 def search(k,used,chosen,cost):
  if k==len(pitches):
   frets=[f for s,f,o in chosen if f>0];span=max(frets)-min(frets) if frets else 0
   # Stretch <=5; no arbitrary octave moves just to reduce fret count.
   if span>5:return
   shape={s:f for s,f,o in chosen}
   fingers=0
   for fret in sorted(set(f for f in shape.values() if f>0)):
    members=sorted(s for s,f in shape.items() if f==fret)
    fingers+=1
    for a,b in zip(members,members[1:]):
     if any(shape.get(ss,99)<fret for ss in range(a+1,b)):fingers+=1
   if fingers>4:return
   candidates.append((cost, max(frets or [0])*.025+span*.15, chosen));return
  p=pitches[k]
  opts=[]
  for o in [0,1,2,-1]:
   q=p+12*o
   for s in range(1,7):
    f=q-OPEN[s]
    if s not in used and 0<=f<=17:opts.append((abs(o),s,f,o))
  for penalty,s,f,o in sorted(opts):
   if candidates and cost+penalty>min(c[0] for c in candidates):continue
   if preserve_voices:
    q=p+12*o
    if any((ns[j]['sourceString']<ns[k]['sourceString'] and ss>=s) or (ns[j]['sourceString']>ns[k]['sourceString'] and ss<=s) for j,(ss,ff,oo) in enumerate(chosen)):continue
    if any((pitches[j]<p and OPEN[ss]+ff>q) or (pitches[j]>p and OPEN[ss]+ff<q) for j,(ss,ff,oo) in enumerate(chosen)):continue
   search(k+1,used|{s},chosen+[(s,f,o)],cost+penalty)
 search(0,set(),[],0)
 assert candidates,('unplayable',pitches)
 return min(candidates,key=lambda c:(c[0],c[1],c[2]))[2]
# Solve full chord voicings consistently for each strum; exact subset audio shares it.
CHORD_MAP={}
BARS[33]['events'][-1]['sustain']=1.5
exceptions=[]
for b in BARS.values():
 b['events'].sort(key=lambda e:e['beat'])
 for e in b['events']:
  e['targetChord']=TRAN[e['chord']]
  chosen=assign(e['notes'],preserve_voices=e['technique'] in ('strum','arpeggio')) if e['notes'] else []
  if e['technique'] in ('strum','arpeggio'):
   CHORD_MAP[e['chord']+' / '+','.join(str(n['sourceString']) for n in e['notes'])]={n['sourceString']:v for n,v in zip(e['notes'],chosen)}
  for n,(s,f,o) in zip(e['notes'],chosen):
   n.update(string=s,fret=f,octaveException=o,pitchAfter=OPEN[s]+f+2)
   if o:exceptions.append({'bar':b['sourceBarNumber'],'beat':e['beat'],'sourceString':n['sourceString'],'sourceFret':n['sourceFret'],'sourcePitch':n['pitchBefore'],'targetPitchRelativeCapo':OPEN[s]+f,'octaves':o,'reason':'标准调弦最低音限制' if n['pitchBefore']-5<40 else '保留全部同时声部、原低音转位与声部顺序所需的独立弦位和四指可按指法'})
 # Vocal melody transposes exactly and is kept as an independent guide voice.
 for v in b['vocal']:
  if v['degree'] not in (0,None):
   root=50 if b['sourceBarNumber']>=51 else 48
   v['pitchBefore']=root+[0,2,4,5,7,9,11][v['degree']-1]+12*v['octave'];v['pitchAfter']=v['pitchBefore']-3
assert sorted(BARS)==list(range(1,68))
# Screenshots 7046-7050 explicitly repeat source bars 5-30 with second lyrics.
# Distinct screen occurrence, not accidental overlap duplication.
sequence=list(range(1,35))+list(range(5,31))+list(range(35,68))
secondLyrics={5:'一/只/蝴/蝶/有/多/鲜/艳',6:'能/不/能',7:'飞/越/过/猜/忌',8:'和/冷//漠/世/界',9:'/给/你/的/简/讯/和/留/言',10:'/说/不/清',11:'万//分/之/一/追',12:'悔',13:'当/星/宿/都/沉/没/山/岳',14:'只/盼/你',15:'会/抬/头/看/我',16:'寄/托//的/弯/月',17:'/当/一/个/文/明/即/将/熄',18:'灭/有/什/么',19:'证/明/你/我/存/在',20:'的/岁/月',21:'',29:'创/造',30:'能/让/你/想/起/我/的/字//眼'}
rows=[]
for i,n in enumerate(sequence,1):
 b=copy.deepcopy(BARS[n]);b['i']=i;b['pass']=2 if 35<=i<=60 else 1
 if b['pass']==2:
  shot='7046' if n<=8 else '7047' if n<=14 else '7048' if n<=21 else '7049' if n<=27 else '7050'
  b['sourceScreenshot']='IMG_'+shot+'.PNG'
  if n in secondLyrics:
   for v in b['vocal']:v['lyric']=''
   chars=secondLyrics[n].split('/') if secondLyrics[n] else []
   attacks=[v for v in b['vocal'] if v['degree'] not in (0,None)]
   assert len(chars)<=len(attacks),(n,chars,attacks)
   for v,c in zip(attacks,chars):v['lyric']=c
 b['section']='前奏' if i<=4 else '主歌一' if i<=22 else '副歌一' if i<=30 else '连接' if i<=34 else '主歌二' if i<=52 else '副歌二' if i<=60 else '间奏' if i<=68 else '副歌三' if i<=76 else '升调副歌' if i<=84 else '尾声'
 rows.append(b)
sourceImages=[{'name':f.name,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in sorted(ROOT.glob('IMG_*.PNG'))]
data={'title':'仓颉','bpm':76,'capo':2,'rows':rows,'sourceBars':[BARS[n] for n in sorted(BARS)],'shapes':SHAPES,'transposition':TRAN,'chordMapping':CHORD_MAP,'octaveExceptions':exceptions,'sourceImages':sourceImages,'unresolved':[],'symbolInterpretations':[{'bars':[35,36,37,38,39,40],'symbol':'boxed ×','technique':'slap','pitched':False,'source':'https://www.guitarpro.cc/jiqiao/gp-xcncw.html','reason':'方框叉号为拍弦；普通叉号仍按和弦图的对应弦位正常拨奏'}],'corrections':[{'bar':51,'printed':'Fm7/C#','normalized':'F#m7/C#','reason':'第2品起横按，五弦4品、二弦5品的x42252指法：F# A C# E，按和弦图保留声音'}]}
P.joinpath('score.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
print('Unique bars:',len(BARS),'Performance measures:',len(rows),'Source events:',sum(len(b['events']) for b in BARS.values()),'Octave exceptions:',len(exceptions))
