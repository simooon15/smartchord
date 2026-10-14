from pathlib import Path
import json,base64,re,sys
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P.parents[1]/'skills/smartchord/scripts'))
from prepare_piano import embed_piano
SOURCE=P.parents[1]/'sources'/'drive-handoff'/'SOURCE_SCREENSHOTS'
DATA=json.loads((P/'score.json').read_text())
for r in DATA['rows']:
 for v in r['vocal']:
  if v.get('degree') and not all(isinstance(v.get(k),(int,float)) for k in ['pitchBefore','pitchAfter']):raise ValueError('Incomplete melody pitch')
embed_piano(DATA,P.parents[1]/'skills/smartchord/assets/piano-cache')
sample_manifest=json.loads((P/'samples'/'manifest.json').read_text())
DATA['sampleInfo']={k:sample_manifest[k] for k in ['preset','program','velocity','sampleRate','duration','pitches','encodedBytes','sourceBytes','font']}
DATA['sampleTuning']={str(r['pitch']):r['playbackRate'] for r in json.loads((P/'samples'/'tuning.json').read_text())}
DATA['samples']={str(n):base64.b64encode((P/'samples'/f'{n}.m4a').read_bytes()).decode() for n in sample_manifest['pitches']}
for im in DATA['sourceImages']:
 im['data']='data:image/png;base64,'+base64.b64encode((SOURCE/im['name']).read_bytes()).decode()
html='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light"><title>仓颉 · 完整交互六线谱 · G 指法 Capo 2</title><style>CSS</style></head><body><main class="layout"><div class="screen-only"><div class="eyebrow">GUITAR / 五月天</div><h1>仓颉</h1><p class="intro">G 调指法 | Capo 2 | 实际 A 调 | 标准调弦 E A D G B e | 默认 76 BPM<br>后段升至 A 指法（实际 B 调）。原谱 67 小节；按第二轮歌词与重复段展开，共 93 个演奏小节。</p><div class="controls"><div class="control-row"><button id="play" class="primary" aria-pressed="false">▶ 播放</button><button id="restart">从头重播</button><select id="section" aria-label="选择段落"></select><button id="print">打印 / 导出 PDF</button><span id="location"></span></div><div class="settings"><label>速度 <input id="bpm" type="range" min="40" max="140" value="76"><output id="bpm-value">76 BPM</output></label><label><input id="melody" type="checkbox">主旋律</label><label><input id="loop" type="checkbox">段落循环</label><label><input id="follow" type="checkbox" checked>跟随谱面</label><select id="mode" aria-label="指法调式"><option value="target">G → A · Capo 2</option><option value="source">原谱 C → D · 不夹</option></select></div><div class="transport"><span id="played">0:00</span><input id="seek" type="range" min="0" step="0.125" value="0" aria-label="播放位置"><span id="duration"></span></div><div id="note-info" aria-live="polite"></div><div id="error" role="alert"></div></div><p class="legend"><span id="mode-label"></span>　数字相对变调夹；点击谱面任意位置即从该处播放；Option / Alt＋点击品位或箭头单独试听。媒体播放／暂停键或空格键可切换播放。箭头朝一弦为下扫，朝低音弦为上扫；波浪箭头为琶音，⊠ 为拍弦。和弦名下方为易按的基础指法图（× 不弹、○ 空弦，品位相对变调夹）；旋律换指按六线谱，扫弦具体按法按箭头旁编号查谱后指法表。人声简谱与歌词在六线谱下方；默认播放吉他伴奏；勾选“主旋律”可同时播放简谱主旋律（钢琴采样）。谱行随窗口宽度自动分行。</p></div><div id="score"></div><aside class="notes screen-only"><p>仅内嵌本曲所需的真实吉他音符采样，在浏览器内组合演奏，无需网络。原谱中的普通 × 已按当前和弦的对应弦位还原为品位数字。</p><details><summary>八度调整 · <span id="octave-count"></span></summary><p>转调后的最低音或同时声部无法放到六根独立弦上时，使用显式八度调整。对应品位加下划线；点击品位可查看原音与实际发声音高。</p><ol id="octaves"></ol></details><details><summary>谱源与校对说明</summary><p>来源：用户原谱截图 IMG_7041—IMG_7056。演奏顺序为原谱 1—34、5—30（二遍）、35—67。截图中第51小节的 Fm7/C# 标签与指法图不符，本谱按图保留 F#m7/C# 的声音，转为 C#m7/G#。</p><p id="qa-status">逐音转录与转调校对完成；保留全部声部，八度调整逐项列于上方。普通 × 为和弦弦位音，方框 × 按拍弦处理。吉他采样来自 Acoustic Guitars JNv2.4 的 Guitar Expressive（主采样 Keith Smith，预设与修改 JN），仅保留本曲需要的音高；浏览器、音频与打印验收记录保存在交接文件夹。</p><button id="source-toggle">查看 / 收起内嵌原谱截图</button><div id="sources" class="sources" hidden></div></details></aside></main><script id="score-data" type="application/json">DATA</script><script>JS</script></body></html>'''
parts={'CSS':(P/'app.css').read_text(),'DATA':json.dumps(DATA,ensure_ascii=False,separators=(',',':')).replace('</','<\\/'),'JS':(P/'rhythm.js').read_text()+'\n'+(P.parents[1]/'skills/smartchord/assets/practice.js').read_text()+'\n'+(P/'app.js').read_text()}
html=re.sub(r'\b(CSS|DATA|JS)\b',lambda m:parts[m.group()],html)
# This stays in work until every acceptance gate clears.
(P/'candidate.html').write_text(html)
print('Built',P/'candidate.html',len(html.encode()),'bytes')
