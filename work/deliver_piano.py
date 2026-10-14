from pathlib import Path
import json,hashlib,shutil,zipfile
root=Path.cwd();entries={}
for title,folder,pages in [('仓颉','project',10),('太聪明','new-song',12)]:
 base=root/'work'/folder;qa=base/'qa-piano';report=json.loads((qa/'practice-results.json').read_text());piano=json.loads((qa/'piano-results.json').read_text());assert piano['status']=='PASS';assert all(r['status']=='PASS' and r['printPages']==pages for r in report.values())
 final=root/'outputs'/f'{title}_完整交互六线谱_G指法_Capo2_FINAL.html';prior=hashlib.sha256(final.read_bytes()).hexdigest();shutil.copyfile(base/'candidate.html',final);sha=hashlib.sha256(final.read_bytes()).hexdigest()
 entry=dict(file=str(final),sha256=sha,previousSha256=prior,date='2026-10-14 Asia/Singapore',printPages=pages,chromium='PASS',webkit='PASS',piano='Salamander Grand Piano V3 · Alexander Holm · CC BY 3.0',pianoRootSamples=piano['recordedRoots'],pianoSourceCommit=piano['upstreamCommit'],pianoDefault=False,audio='Real sampled-piano source/target melody frequency, all mixed audio, envelope and seek-offset PASS; all accompaniment PCM matches previous version within numeric decode tolerance.',print='All page rasters identical to preceding verified version; A4 bounds/page count PASS',humanListening='NOT PERFORMED',performanceAcceptance='NOT PERFORMED',physicalPhone='NOT PERFORMED')
 (qa/'delivery.json').write_text(json.dumps(entry,ensure_ascii=False,indent=2));entries[title]=entry
 if folder=='new-song':(base/'qa-final/delivery.json').write_text(json.dumps(entry,ensure_ascii=False,indent=2))
p=root/'docs/PROJECT_STATE.md';s=p.read_text()
for entry in entries.values():s=s.replace(entry['previousSha256'],entry['sha256'])
s+='''
## 钢琴主旋律替换 · 2026-10-14

- 用户反馈合成主旋律音色难听，已将两首歌统一替换为 **Salamander Grand Piano V3** 原始钢琴录音，作者 Alexander Holm，CC BY 3.0；来源 https://github.com/sfzinstruments/SalamanderGrandPiano 。固定 commit `3382bf9496bba2486f5ab0de55a264d1dfc38404`，按需下载第 8 力度层 FLAC，未下载整套多层库。
- 通用 piano-cache 共 13 个根音、29 个实际音高映射。每份歌曲只内嵌自身需要的根音 AAC（44.1 kHz mono、96kbps）；显式小三度键区映射，最多偏移一个半音，并校准录音音高。处理方式、来源、署名及完整 CC BY 3.0 许可内嵌，原始/导出 SHA-256 留 manifest。
- 播放器使用独立钢琴 AudioBuffer，保留采样起音与自然衰减，记谱时值后加 180ms 松键尾音；从延音中间进入使用采样偏移，无重新敲键。保持主旋律默认关闭、指法转调、BPM、定位、循环及后台/暂停清音。没有模拟完整 SFZ 的踏板共鸣或键噪。
- 新增 prepare_piano.py、piano_qa.cjs，构建器与《仓颉》入口共用缓存嵌入与声学模块。缓存扩充保留既有映射与固定上游 commit；缺映射或缓存哈希不符阻止构建，不退回振荡器。README、PRD、skill/参考文档及分发 ZIP 同步更新。
- Chrome/WebKit 的全部旋律频率、两模式整曲混音/无削波、开关/循环/定位/清音、自适应分行通过；钢琴原始/导出哈希、起音/自然衰减/松键尾音和延音采样偏移通过。两模式完整伴奏音频与上版逐样本在数值解码容差内一致，吉他数据和采样完全一致。
- A4 仍为《仓颉》10 页、《太聪明》12 页，实际全部页面光栅图与上版逐像素一致，页数/边界和缩略图复核通过。证据与新交付哈希在各曲 qa-piano；此前版本备份仅留 qa-piano/baseline.html。
- 本轮完成工程与自动声音检查，未声称人耳听感或人类演奏接受通过；钢琴许可明确不改变既有吉他采样及谱源的分发边界。
''';p.write_text(s)
p=root/'work/new-song/REVIEW.md';s=p.read_text();s+='''
## 钢琴音色更新 · 2026-10-14

主旋律从合成提示音改为 Salamander Grand Piano V3（Alexander Holm，CC BY 3.0）真实录音，内嵌本曲需要的根音采样、校准/键区映射与完整许可。保留自然起音与衰减、180ms 松键尾音，中途进入持续音恢复采样偏移；默认关闭的开关与其他练习功能保留。qa-piano 保存两浏览器、两模式整曲混音与频率、自然包络、延音定位、缓存哈希及完整伴奏波形对比。伴奏 PCM 在数值解码容差内一致，谱数据/吉他采样完全一致；12 页实际 A4 全页光栅与前版逐像素一致。最新正式文件与 skill ZIP 已替换，哈希见 qa-piano/delivery.json；没有主观人耳试听或演奏接受记录。
''';p.write_text(s)
p=root/'outputs/smartchord.zip';skill=root/'skills/smartchord'
with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as z:
 for file in sorted(skill.rglob('*')):
  if file.is_file() and '__pycache__' not in file.parts and file.suffix!='.pyc' and file.name!='.DS_Store':z.write(file,'smartchord/'+str(file.relative_to(skill)))
with zipfile.ZipFile(p) as z:
 assert z.testzip() is None
 for file in skill.rglob('*'):
  if file.is_file() and '__pycache__' not in file.parts and file.suffix!='.pyc' and file.name!='.DS_Store':assert z.read('smartchord/'+str(file.relative_to(skill)))==file.read_bytes()
print(json.dumps({t:e['sha256'] for t,e in entries.items()},ensure_ascii=False));print('Song hash/readback and bundled piano skill ZIP PASS')
