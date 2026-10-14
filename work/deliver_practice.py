from pathlib import Path
import json,hashlib,shutil,zipfile
root=Path.cwd();deliveries={}
for title,folder,pages in [('仓颉','project',10),('太聪明','new-song',12)]:
 base=root/'work'/folder;report=json.loads((base/'qa-practice/practice-results.json').read_text())
 assert all(r['status']=='PASS' and r['printPages']==pages for r in report.values())
 file=root/'outputs'/f'{title}_完整交互六线谱_G指法_Capo2_FINAL.html';shutil.copyfile(base/'candidate.html',file)
 sha=hashlib.sha256(file.read_bytes()).hexdigest();assert sha==hashlib.sha256((base/'candidate.html').read_bytes()).hexdigest()
 entry=dict(file=str(file),sha256=sha,date='2026-10-14 Asia/Singapore',printPages=pages,chromium='PASS',webkit='PASS',responsiveWidths=[320,390,600,900,1440],melodyDefault=False,melodyNotes=report['chromium']['melodyNotes'],audio='Automatic full source/target mixed audio, melody frequency, toggle and cleanup PASS',visual='Mobile dense/4-chord screenshots; all A4 contact sheets and dense full pages reviewed',source='Existing notation and all guitar events preserved; no fresh full source transcription audit',humanListening='NOT PERFORMED',performanceAcceptance='NOT PERFORMED',physicalPhone='NOT PERFORMED')
 (base/'qa-practice/delivery.json').write_text(json.dumps(entry,ensure_ascii=False,indent=2));deliveries[title]=entry
 if folder=='new-song':(base/'qa-final/delivery.json').write_text(json.dumps(entry,ensure_ascii=False,indent=2))
p=root/'docs/PROJECT_STATE.md';s=p.read_text();s=s.replace('59b22500130a4a2efe7e529a5234ed2ba186a85e415f33ad1e08637b118099df',deliveries['仓颉']['sha256']).replace('4e2e24db22e8e051c7b675eb97164c60826097b32c15c51c725b5dc1f5c9392f',deliveries['太聪明']['sha256']);s+='''
## 两首歌自适应分行与主旋律 · 2026-10-14

- 《仓颉》《太聪明》均按可用窗口宽度与音符/歌词/和弦密度重新分配每行小节数，手机通常一小节，宽窗口容纳更多小节；不再依赖固定桌面谱行横滑。短音用弹性间距，密集双位品号局部收紧字宽。游标与点击定位共用坐标映射，调整窗口保持播放位置与模式。
- 新增默认关闭的“主旋律”开关；开启后原谱简谱旋律用柔和合成提示音与真实吉他伴奏同步播放，关闭恢复伴奏。旋律声部独立于六弦制音，支持两模式、BPM、定位、循环、暂停/后台清音；合并跨小节延音，中途进入恢复剩余时值，休止不发声。
- 《仓颉》沿用原有明确 MIDI；《太聪明》将原谱 E 调无点 1 明确为 E4/MIDI 64，依据八度点和临时变音计算源实际 MIDI，目标统一 +5 半音。408 / 398 个旋律起音，明细在各曲 qa-practice/melody-ledger.json。原有吉他事件、和弦变化、歌词与简谱字段逐项对比未改。
- 通用 skill 更新 player.js/player.css、共享 practice.js、编译/构建/验证与 practice_qa.cjs；《仓颉》保留歌曲专用数据，复用共享旋律与宽度工具。本机 skill 仍链接到项目维护源，outputs/smartchord.zip 已重新打包。
- Chrome/WebKit 在 320/390/600/900/1440 宽度无页面或谱行横溢；实时主旋律开关、旋律频率、两模式整曲混音有限值/RMS/无削波、延音中途播放、循环、重排和清音通过。既有吉他/节奏/滑音回归与混合拍号通用样例通过，零外部请求与页面错误。
- 从手机进入 A4 恢复独立打印布局：《仓颉》10 页、《太聪明》12 页；实际 A4 边界/页数、所有缩略图和密集页复核。证据：work/project/qa-practice 与 work/new-song/qa-practice；交付哈希在 delivery.json。
- 本轮复用已有源转录、抽查简谱并检验结构与音频，没有重新做全曲逐音视觉转录；未完成人耳试听、人类演奏接受或实体手机验收，不将自动 PASS 视为这些验收。
''';p.write_text(s)
p=root/'work/new-song/REVIEW.md';s=p.read_text();s+='''
## 自适应与主旋律更新 · 2026-10-14

屏幕改为按窗口宽度和密度重新分行；A4 仍为独立 12 页。新增默认关闭的主旋律开关，开启后采用柔和合成提示音；源无点 1=E4/MIDI 64，含原简谱八度点与 #5，实际目标 +5 半音。398 个起音，含跨小节延音，声部与吉他制音独立。原吉他事件与已有歌词/简谱逐项与此前正式 HTML 对比相同。

qa-practice 保存五种宽度、Chrome/WebKit、两模式全部 71 小节混音与旋律频率、实时开关/模式/速度、延音进入、定位、循环、重排和清音检查；零外部网络/页面错误，峰值未削波。实际 A4 页数/边界和全页缩略图、密集页已复核。最新哈希见 qa-practice/delivery.json，正式文件已替换。skill、文档和分发 ZIP 同步更新。无本轮全曲重新视觉转录、人耳试听、人类演奏或实体手机接受。
''';p.write_text(s)
p=root/'outputs/smartchord.zip';skill=root/'skills/smartchord'
with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as z:
 for file in sorted(skill.rglob('*')):
  if file.is_file() and '__pycache__' not in file.parts and file.suffix!='.pyc' and file.name!='.DS_Store':z.write(file,'smartchord/'+str(file.relative_to(skill)))
with zipfile.ZipFile(p) as z:
 assert z.testzip() is None
 for file in skill.rglob('*'):
  if file.is_file() and '__pycache__' not in file.parts and file.suffix!='.pyc' and file.name!='.DS_Store':assert z.read('smartchord/'+str(file.relative_to(skill)))==file.read_bytes()
print(json.dumps({t:v['sha256'] for t,v in deliveries.items()},ensure_ascii=False));print('Skill ZIP source/readback PASS')
