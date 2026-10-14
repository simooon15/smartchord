from pathlib import Path
import json,shutil,hashlib,zipfile
root=Path.cwd();entries={}
for title,folder,pages in [('仓颉','project',10),('太聪明','new-song',12)]:
 base=root/'work'/folder;report=json.loads((base/'qa-transport/transport-results.json').read_text());reg=json.loads((base/'qa-transport-regression/practice-results.json').read_text());assert all(r['status']=='PASS' and r['printPages']==pages for r in report.values());assert all(r['status']=='PASS' for r in reg.values())
 final=root/'outputs'/f"{'五月天' if title=='仓颉' else '陈绮贞'} - {title}.html";before=hashlib.sha256(final.read_bytes()).hexdigest();shutil.copyfile(final,base/'qa-transport/baseline.html');shutil.copyfile(base/'candidate.html',final);after=hashlib.sha256(final.read_bytes()).hexdigest();assert after==hashlib.sha256((base/'candidate.html').read_bytes()).hexdigest()
 entry=dict(file=str(final),sha256=after,previousSha256=before,date='2026-10-14 Asia/Singapore',printPages=pages,chromium='PASS',webkit='PASS',controls='Click note/sweep/lyric/blank to start; Alt audition; Media Session play/pause/stop; page media-key and Space; last-request-wins; loading cancellation PASS',mediaOutput='One actual audio mix via MediaStreamDestination -> HTML audio where supported; direct Web Audio fallback',regression='Both-mode full automatic audio and responsive layout PASS; all score/sample JSON identical; all printed page rasters identical',physicalMediaKey='NOT TESTED; browser/system session routing requires real-world acceptance',humanListening='NOT PERFORMED',physicalPhone='NOT PERFORMED')
 (base/'qa-transport/delivery.json').write_text(json.dumps(entry,ensure_ascii=False,indent=2));entries[title]=entry
 if folder=='new-song':(base/'qa-final/delivery.json').write_text(json.dumps(entry,ensure_ascii=False,indent=2))
p=root/'docs/PROJECT_STATE.md';s=p.read_text()
for e in entries.values():s=s.replace(e['previousSha256'],e['sha256'])
s+='''
## 点击即播放与电脑媒体键 · 2026-10-14

- 两首歌普通点击音符、扫弦/琶音箭头、歌词与谱面空白，从对应拍点立即连续播放；原谱/目标、暂停/播放状态均支持。音符/箭头/歌词使用精确拍点，空白使用共享弹性坐标映射。点击当前段落外切换为整首；Option/Alt＋点击品位或箭头保留单事件试听。
- 音符与歌词加入透明 SVG 命中区和键盘入口，避免 WebKit 文字命中到后面的琴弦；不改变显示、音高、节奏或打印。进度条在暂停时仍只定位，点击谱面明确要求启动。
- 接入浏览器 Media Session 的 play/pause/stop、歌曲信息与播放状态；真实混音单一输出经 MediaStreamDestination → HTML audio，帮助系统媒体会话路由，不使用占位静音或重复输出；不可用时回退直接 Web Audio。页面媒体键事件和空格切换作补充，空格不拦截输入框/菜单/按钮/链接/可编辑区域。
- 加载、媒体 play 等待、快速连点和变速/切模式时按请求编号保留最后一次意图；暂停取消待启动请求、暂停媒体元素并清除声源。原有主旋律、循环、后台暂停与模式切换继续有效。
- Chrome/WebKit 真实点击（1100/390 宽度）、Alt 试听、范围外跳转、空白定位、媒体会话已注册回调、页面媒体键/空格、单一真实 audio 流、快速跳转及加载中暂停通过。两模式整曲自动音频、自适应/循环回归通过，零页面错误/外部请求；谱数据、吉他与钢琴内嵌采样逐项完全相同。
- 《仓颉》10 页、《太聪明》12 页实际 A4 核对，全部页面光栅图与上版逐像素一致。证据及最新交付哈希：各曲 qa-transport；音频/宽度回归：qa-transport-regression。README、PRD、skill/参考文档与分发 ZIP 同步更新。
- 自动媒体会话回调和 DOM 按键不能代表物理键已验收。首次打开需先点击谱面或播放按钮允许发声；系统键是否交给本页取决于操作系统和浏览器的活动媒体会话。物理系统媒体键、实体手机及人耳/人类演奏接受仍未实测。
''';p.write_text(s)
p=root/'work/new-song/REVIEW.md';s=p.read_text()+'''\n## 点击播放与媒体键更新 · 2026-10-14\n\n默认点击谱面音符/箭头/歌词/空白从对应拍点连续播放，Option/Alt＋点击保留单事件试听；Media Session 接入电脑媒体播放/暂停，页面媒体键与空格作为补充。媒体元素承载实际单一混音，不用占位静音。异步解码/播放等待中保持最后一次请求，暂停取消待启动。qa-transport 验证两浏览器的实际点击、范围外跳转、媒体回调/页面键盘、单一真实 audio 流、连点和加载取消；qa-transport-regression 完成两模式音频/宽度/循环回归。全部谱数据/采样与此前正式版相同，12 页打印光栅逐像素相同。物理系统媒体键、实体手机、人耳试听仍未验收。最新哈希见 qa-transport/delivery.json。\n''';p.write_text(s)
for p in [root/'work/project/qa-transport/delivery.json',root/'work/new-song/qa-transport/delivery.json']:assert p.exists()
zipfile_path=root/'outputs/smartchord.zip';skill=root/'skills/smartchord'
with zipfile.ZipFile(zipfile_path,'w',zipfile.ZIP_DEFLATED) as z:
 for file in sorted(skill.rglob('*')):
  if file.is_file() and '__pycache__' not in file.parts and file.suffix!='.pyc' and file.name!='.DS_Store':z.write(file,'smartchord/'+str(file.relative_to(skill)))
with zipfile.ZipFile(zipfile_path) as z:
 assert z.testzip() is None
 for file in skill.rglob('*'):
  if file.is_file() and '__pycache__' not in file.parts and file.suffix!='.pyc' and file.name!='.DS_Store':assert z.read('smartchord/'+str(file.relative_to(skill)))==file.read_bytes()
print(json.dumps({t:e['sha256'] for t,e in entries.items()},ensure_ascii=False));print('Formal songs / docs / skill ZIP source readback PASS')
