"""Package validated score + only required samples as a single offline HTML."""
import argparse,base64,html,json,mimetypes,re
from prepare_piano import embed_piano
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def build(score,out,samples=None):
 d=json.loads(Path(score).read_text());cfg=d['settings'];d.setdefault('sourceImages',[]);d.setdefault('unresolved',[])
 if d['unresolved'] or not d.get('rows'):raise ValueError('Score incomplete')
 for r in d['rows']:
  for v in r['vocal']:
   if v.get('degree') and not all(isinstance(v.get(k),(int,float)) for k in ['pitchBefore','pitchAfter']):raise ValueError('Incomplete melody pitch')
 embed_piano(d,ROOT/'assets/piano-cache')
 samples=Path(samples) if samples else ROOT/'assets/sample-cache'
 required=sorted({n[k] for r in d['rows'] for e in r['events'] for n in e['notes'] for k in ['pitchBefore','pitchAfter']})
 manifest=json.loads((samples/'manifest.json').read_text());tuning={str(x['pitch']):x['playbackRate'] for x in json.loads((samples/'tuning.json').read_text())} if (samples/'tuning.json').exists() else {}
 absent=[n for n in required if not (samples/f'{n}.m4a').is_file()]
 if absent:raise ValueError('Real guitar samples missing for MIDI '+str(absent)+'. Extract these from an authorized guitar soundfont; no synthetic fallback.')
 longest=max([3.2]+[(e.get('sustain',e['duration']))*60/40+.12 for r in d['rows'] for e in r['events'] if not e.get('tie')])
 if manifest['duration']<longest:raise ValueError('Sample sustain too short at minimum BPM; re-extract longer samples')
 d['samples']={str(n):base64.b64encode((samples/f'{n}.m4a').read_bytes()).decode() for n in required};d['sampleTuning']={str(n):tuning.get(str(n),1) for n in required};d['sampleGain']=manifest.get('sampleGain',8)
 d['sampleInfo']={**manifest,'pitches':required,'encodedBytes':sum((samples/f'{n}.m4a').stat().st_size for n in required)}
 for im in d['sourceImages']:
  path=Path(im['path']);path=path if path.is_absolute() else Path(score).parent/path
  im['data']='data:'+ (mimetypes.guess_type(path)[0] or 'image/png')+';base64,'+base64.b64encode(path.read_bytes()).decode()
 title=html.escape(d['title']);artist=html.escape(d.get('artist',''));subtitle=html.escape(f"{cfg['targetFingeringKey']} 指法 · Capo {d['capo']} · 实际 {cfg['targetActualKey']} 调 · {len(d['sourceBars'])} 个原谱小节 / {len(d['rows'])} 个演奏小节")
 documents=[]
 for doc in d.get('sourceDocuments',[]):
  file=Path(doc['path']);file=file if file.is_absolute() else Path(score).parent/file
  documents.append('<p><a download="'+html.escape(file.name,quote=True)+'" href="data:application/pdf;base64,'+base64.b64encode(file.read_bytes()).decode()+'">下载内嵌原始 PDF</a></p>')
 attribution=html.escape(d.get('sourceAttribution',''))+'<p>'+html.escape(json.dumps(manifest.get('font',{}),ensure_ascii=False))+'</p>'
 template='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>__TITLE__ · 完整交互吉他谱</title><style>__CSS__</style></head><body><main class="layout"><div class="screen-only"><div class="eyebrow">GUITAR / __ARTIST__</div><h1>__TITLE__</h1><p class="intro">__SUBTITLE__</p><div class="controls"><div class="control-row"><button id="play" class="primary" aria-pressed="false">▶ 播放</button><button id="restart">从头重播</button><select id="section" aria-label="选择段落"></select><button id="print">打印 / 导出 PDF</button><span id="location"></span></div><div class="settings"><label>速度 <input id="bpm" type="range" min="40" max="140" value="__BPM__"><output id="bpm-value">__BPM__ BPM</output></label><label><input id="melody" type="checkbox">主旋律</label><label><input id="loop" type="checkbox">段落循环</label><label><input id="follow" type="checkbox" checked>跟随谱面</label><select id="mode" aria-label="指法调式"><option value="target">目标指法</option><option value="source">原谱指法</option></select></div><div class="transport"><span id="played">0:00</span><input id="seek" type="range" min="0" step="0.125" value="0" aria-label="播放位置"><span id="duration"></span></div><div id="note-info" aria-live="polite"></div><div id="error" role="alert"></div></div><p class="legend"><span id="mode-label"></span>　品位相对变调夹。点击谱面任意位置即从该处播放；Option / Alt＋点击音符或箭头单独试听。媒体播放／暂停键或空格键可切换播放。和弦图为基础按法，× 不弹、○ 空弦；旋律换指按六线谱，扫弦具体按法查箭头编号。朝一弦为下扫、朝低音弦为上扫；波浪箭头为琶音，⊠ 为已核实的拍弦。默认播放吉他伴奏；勾选“主旋律”可同时播放简谱主旋律（钢琴采样）。谱行随窗口宽度自动分行。</p></div><div id="score"></div><aside class="notes screen-only"><details><summary>八度调整 · <span id="octave-count"></span></summary><p>只在已允许且原声部无法在独立弦位上演奏时调整；对应音符加下划线，逐项记录如下。</p><ol id="octaves"></ol></details><details><summary>原谱与音色来源</summary>__DOCUMENTS__<button id="source-toggle">查看 / 收起内嵌原谱</button><div id="sources" class="sources" hidden></div><p>__ATTRIBUTION__</p></details></aside></main><script id="score-data" type="application/json">__DATA__</script><script>__JS__</script></body></html>'''
 replacements={'DOCUMENTS':''.join(documents),'TITLE':title,'ARTIST':artist,'SUBTITLE':subtitle+('<br>'+html.escape(d['arrangementNotes']) if d.get('arrangementNotes') else ''),'BPM':str(d['bpm']),'ATTRIBUTION':attribution,'CSS':(ROOT/'assets/player.css').read_text(),'JS':(ROOT/'assets/rhythm.js').read_text()+'\n'+(ROOT/'assets/practice.js').read_text()+'\n'+(ROOT/'assets/player.js').read_text(),'DATA':json.dumps(d,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')}
 result=re.sub(r'__(DOCUMENTS|TITLE|ARTIST|SUBTITLE|BPM|ATTRIBUTION|CSS|JS|DATA)__',lambda m:replacements[m[1]],template)
 Path(out).parent.mkdir(parents=True,exist_ok=True);Path(out).write_text(result);print('Built',out,'with',len(required),'sample pitches;',len(result.encode()),'bytes')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('score');a.add_argument('output');a.add_argument('--samples');v=a.parse_args();build(v.score,v.output,v.samples)
