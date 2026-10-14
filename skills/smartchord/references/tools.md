# 工具与运行方式

`<skill>` 指当前 SKILL.md 所在目录；安装路径和工作路径均由实际会话决定。不要使用《仓颉》的旧目录或小节编号作为新曲参数。

## 环境

- Python 3：编译、校验、打包只用标准库；打印缩略图需要 Pillow，音色校准需要 NumPy。
- Poppler：pdftoppm、pdftotext、pdfinfo 用于 PDF 渲染和验证。
- Node + Playwright：Chrome/Chromium 和 WebKit 已安装浏览器。优先查已有工作区/桌面 bundled runtime，不重复装依赖。`browser_qa.cjs` 默认使用系统 Chrome；没有 Chrome 时可把 launch 的 channel 去掉使用 Playwright Chromium。
- 需要新音高时：spessasynth_core、用户授权的钢弦吉他 SF2，Mac afconvert 或其他平台 ffmpeg。生成后的 HTML 无上述依赖。

所有脚本支持传入实际输入、输出目录，不修改原谱。

```sh
python3 <skill>/scripts/prepare_sources.py /path/截图.png /path/原谱.pdf --out work/sources
# 阅读所有图片并创建 source.json，然后：
python3 <skill>/scripts/score_tools.py work/source.json work/score.json
python3 <skill>/scripts/validate_score.py work/score.json --raw work/source.json
node <skill>/scripts/rhythm_qa.cjs
python3 <skill>/scripts/build_html.py work/score.json work/candidate.html
# 按现有环境配置 Node 的 module 搜索路径后：
node <skill>/scripts/browser_qa.cjs work/candidate.html work/qa
python3 <skill>/scripts/print_qa.py work/qa/proof.pdf --expected <browser-results中的plannedPages> --out work/qa/print
```

`print_qa.py` 输出各页 PNG 和 6 页一张的 contact sheet。实际 PDF 页数必须等于 DOM 计划页数；字体 bbox 在页内只证明未出页，不能证明字之间无碰撞。必须实际看图。使用 PDF 技能时遵循该技能的 authoring marker 约定；不要假定其它运行环境无需该约定。

转调脚本按事件求解、对相同源音组合稳定复用；它不证明整首演奏的换把流畅、不识别图片，也不能自动判读图例。特殊输入需有据扩展，重新测试后才交付。

<a id="audio"></a>
## 音色生成与校准

assets/sample-cache 是 34 个已经验证的钢弦 MIDI 音高缓存，约 1 MB。构建只抽取曲目原谱与目标模式用到的集合。缓存不是整套音色，不保证新歌曲的所有音高都在其中。manifest.json 保留音色与署名；tuning.json 保留同一采样的频率校准。

必要时找用户已有的已授权音色和 spessasynth_core，不要把已有仓库作为可随意修改的素材目录。本次参考过 chord-inspiration 的钢弦方案（ https://github.com/simooon15/chord-inspiration ）；它是可选音色来源示例，不是运行必需依赖。不要自动下载巨大 SF2 或假定 program 0 在任何音色里都是吉他。核实音色库 preset/program（传入零起始编号）。原缓存使用 Guitar Expressive、program 0；一般 GM 钢弦吉他通常在不同编号，应以具体库为准。

```sh
node <skill>/scripts/extract_samples.mjs --core /path/spessasynth_core/dist/index.js --font /path/authorized-guitar.sf2 --program 0 --preset "Guitar Expressive" --score work/score.json --out work/samples
python3 <skill>/scripts/tune_samples.py work/samples
python3 <skill>/scripts/build_html.py work/score.json work/candidate.html --samples work/samples
```

提取器只离线渲染两种模式需要的音高；22050 Hz mono、velocity 88、AAC 64kbps，每个音按曲目最长时值选择持续长度（最低 BPM 40）。同一音色保持全局增益，以保留不同采样的相对强弱，不逐音强制同响度。构建器检查持续长度，不够就重新提取。

tune_samples 用稳态 Hann 窗 FFT 测原频率并生成播放速率校准；browser_qa 使用 HTML 的真实 OfflineAudioContext 路径比较目标频率与相邻半音，并检查 RMS/峰值。音色有弱基频或较多谐波时，频率探测失败要核实音色，不盲目放宽门槛。去噪、换音色或主观听感的迭代需重新输出音频证据。

采样只解决音色。扫弦上下方向、范围、逐弦延迟、同弦重新拨奏释放、和弦切换、延音与暂停清理依赖谱数据和播放器；不能把一段预录整曲音频绑在谱面上冒充逐音交互。

## 节奏绘制共享模块

assets/rhythm.js 是符梁层数、附点、节拍分组的唯一来源，由 build_html.py 内联在播放器前。八分/十六分/三十二分分别一/二/三层；分组符梁统一绘制，事件上不能同时画短横线再叠加分组横线。第二、三层只连接连续具有对应时值的音符，混合时值用局部短符梁；独立音符用曲线符尾。人声简谱减时线使用同一时值解析，三十二分也显示第三条线。

事件 writtenDuration 用于三连音等“实际拍长不同于书写时值”的情况，仍需额外绘制原谱的连音数标记；默认模板不能仅有正确播放时长却漏掉连音数字。小节 beamGroups 可显式提供 [0,1,2,3,4] 一类分组边界，beamBreak=true 表示该事件前断开；优先遵照原谱。默认复拍子 6/8、9/8、12/8 按附点四分分组，常规拍号按四分分组。

改动共享模块后运行 rhythm_qa.cjs 并重建 HTML：测试八分对、四个十六分、八个三十二分、混合时值、附点、孤立符尾、休止/时间间隔及复拍子；放大检查实际谱面，不仅检查数据里的 duration。

## 自适应谱面与主旋律

`assets/practice.js` 是播放器共享模块；构建器与《仓颉》build.py 均内嵌它。主旋律以原谱明确的 pitchBefore / sourceVocalTonicMidi 建立，钢琴采样完全离线，独立于吉他采样与六弦制音。

```sh
node <skill>/scripts/practice_qa.cjs work/candidate.html work/qa-practice
```

该验证覆盖两浏览器、五种宽度、主旋律频率、两模式整曲混音、实时开关与暂停清音、定位/循环/窗口变化，以及窄屏切入 A4 打印；打印仍须使用 print_qa.py 并进行视觉复核。

## 主旋律钢琴采样

默认使用 **Salamander Grand Piano V3**，Alexander Holm 原始录音，CC BY 3.0：https://github.com/sfzinstruments/SalamanderGrandPiano 。从该仓库的固定 commit 按需下载 velocity-8 原始 FLAC；不下载整套多层库。缓存扩充保留既有音高映射与固定 commit，避免制作新曲时覆盖当前曲目的可用音域。主旋律采用独立采样缓存 assets/piano-cache，不复用吉他采样。13 个原始根音覆盖当前两曲 29 个实际音高（49–83，稀疏集合）；新曲缺映射必须扩充并验证，不退回振荡器。

```sh
python3 <skill>/scripts/prepare_piano.py work/score.json --out <skill>/assets/piano-cache --source work/piano-source
```

准备脚本使用 numpy、curl、macOS afconvert；非 macOS 环境可适配为 ffmpeg 后运行同等校验。生成 mono 44.1 kHz AAC 96kbps，测量根音频率并校准；保留原始文件和导出文件 SHA-256、commit、署名与完整许可。钢琴原库每隔小三度录音，采用显式根音映射，距离不超过一个半音；这是采样库的正常键区映射，不是吉他缺音采样的静默兜底。保留原采样起音与自然衰减，按记谱时值加 180ms 松键尾音；中途进入持续音从采样相应偏移恢复，避免重新敲键。没有模拟完整 SFZ 的踏板共鸣与键噪。

构建器只内嵌本曲两模式旋律使用的根音，并附来源、处理方式与 CC BY 3.0 许可全文。钢琴不替代钢弦吉他采样。运行 practice_qa 与 piano_qa，检查实际采样解码、全部旋律频率、起音/自然衰减/松键、延音进入、两模式整曲混音与峰值。

## 点击播放与系统媒体控制

```sh
node <skill>/scripts/transport_qa.cjs work/candidate.html work/qa-transport
```

实现参考浏览器官方 [Media Session 文档](https://developer.chrome.com/blog/media-session) 与 [规范](https://w3c.github.io/mediasession/)。页面普通点击启动连续播放，Option/Alt 保留试听；真实混音经过 HTML audio 的 MediaStream 输出以接入媒体会话，离线合成验证仍直接用 OfflineAudioContext。不要以媒体回调或 DOM 模拟键冒充实际 OS 媒体键结果。
