from pathlib import Path
import json
P=Path(__file__).resolve().parent
j=json.loads((P/'score.json').read_text());regs={}
def row(shot,nums,xs,y1,y2):
 for n,a,b in zip(nums,xs,xs[1:]):regs[(shot,n)]=[a,y1,b,y2]
row('7041',[1,2],[0,632,1206],375,975);row('7041',[3,4,5],[0,418,716,1206],980,1530);row('7041',[6,7,8],[0,402,805,1206],1540,2160)
row('7042',[9,10],[0,675,1206],185,760);row('7042',[11,12],[0,610,1206],790,1350);row('7042',[13,14],[0,685,1206],1380,2000)
row('7043',[15,16],[0,618,1206],740,1360);row('7043',[17,18],[0,680,1206],1370,1960)
row('7044',[19,20,21],[0,429,818,1206],235,885);row('7044',[22,23],[0,508,1206],885,1470);row('7044',[24,25],[0,616,1206],1470,2080)
row('7045',[26,27],[0,606,1206],185,770);row('7045',[28,29],[0,636,1206],780,1380);row('7045',[30,31],[0,710,1206],1380,2010)
row('7046',[32,33,34],[0,475,872,1206],200,720);row('7046',[5,6],[0,671,1206],740,1310);row('7046',[7,8],[0,607,1206],1320,1960)
row('7047',[9,10],[0,671,1206],150,755);row('7047',[11,12],[0,610,1206],760,1345);row('7047',[13,14],[0,685,1206],1350,2000)
row('7048',[15,16],[0,619,1206],150,765);row('7048',[17,18],[0,682,1206],780,1360);row('7048',[19,20,21],[0,433,817,1206],1370,1970)
row('7049',[22,23],[0,508,1206],150,765);row('7049',[24,25],[0,620,1206],770,1350);row('7049',[26,27],[0,605,1206],1360,1960)
row('7050',[28,29],[0,637,1206],160,770);row('7050',[30,35],[0,723,1206],770,1330);row('7050',[36,37,38],[0,411,804,1206],1340,1880)
row('7051',[39,40],[0,607,1206],150,630);row('7051',[41,42],[0,682,1206],650,1250);row('7051',[43,44],[0,640,1206],1270,1850)
row('7052',[45,46],[0,603,1206],155,775);row('7052',[47,48],[0,642,1206],780,1350);row('7052',[49,50],[0,566,1206],1360,1990)
row('7053',[51,52],[0,672,1206],150,765);row('7053',[53,54],[0,606,1206],780,1370);row('7053',[55,56],[0,653,1206],1370,1960)
row('7054',[57,58],[0,529,1206],150,750);row('7054',[59,60],[0,615,1206],760,1310);row('7054',[61,62],[0,616,1206],1320,1900)
row('7056',[63,64],[0,615,1206],300,925);row('7056',[65,66,67],[0,455,849,1125],930,1530)
for b in j['rows']+j['sourceBars']:
 shot=b['sourceScreenshot'][4:8];b['sourceRegion']=regs[(shot,b['sourceBarNumber'])]
 # Overlaps are recorded for independent comparison, not appended as extra bars.
 b['otherSourceOccurrences']=[{'screenshot':'IMG_'+sh+'.PNG','bounds':rect} for (sh,n),rect in regs.items() if n==b['sourceBarNumber'] and sh!=shot]
source_map=[{'performanceMeasure':r['i'],'sourceBarNumber':r['sourceBarNumber'],'pass':r['pass'],'screenshot':r['sourceScreenshot'],'bounds':r['sourceRegion'],'section':r['section'],'guitarEvents':len(r['events']),'guitarSourceNotes':sum(len(e['notes']) for e in r['events']),'status':'visually_transcribed','notes':'拍弦' if any(e['technique']=='slap' for e in r['events']) else ''} for r in j['rows']]
(P/'score.json').write_text(json.dumps(j,ensure_ascii=False,indent=2));(P/'source-to-score.json').write_text(json.dumps(source_map,ensure_ascii=False,indent=2))
print('Source mapping records:',len(source_map))
