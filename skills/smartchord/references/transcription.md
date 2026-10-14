# 原谱转录与数据契约

## 输入处理

`prepare_sources.py FILE... --out work/sources` 保留输入与 SHA-256，PDF 用 Poppler 160 DPI 渲染。先确认用户文件排列顺序；文件名排序不等于歌曲顺序。获取源图尺寸，分系统/小节放大查看，记录 [x0,y0,x1,y1] 原图区域。对已提供的原谱图例、调号、Capo、拍号和反复优先采信，但和弦标签与图冲突必须明确记录并核查。

`source.json` 是人工/视觉核实后的输入，不是 OCR 自动生成的可靠谱。脚本不包含自动音乐识别模型。未知音符保存在 `unresolved`，构建器会阻止其被当完整谱交付。

## JSON 约定

拍点与时值单位都是**四分音符**，因此 6/8 一小节是 3，3/4 是 3；三十二分音符是 .125。弦编号 1 = 高音 e，6 = 低音 E。原和弦 shapes 数组是**一弦至六弦**；目标 foundationShapes 数组是**六弦至一弦**（指法图左至右）。不弹弦是 null，空弦是 0。

最小完整输入：

```json
{
  "title": "歌名",
  "artist": "作者",
  "bpm": 76,
  "settings": {
    "sourceFingeringKey": "C", "sourceCapo": 0,
    "targetFingeringKey": "G", "targetCapo": 2,
    "targetActualKey": "A", "allowOctaveAdjustments": false
  },
  "shapes": {"C": [0,1,0,2,3,null]},
  "sourceImages": [{"name":"page-1.png", "path":"sources/page-1.png"}],
  "sourceDocuments": [],
  "sourceBars": [{
    "sourceBarNumber": 1, "sourceScreenshot": "page-1.png",
    "sourceRegion": [30,100,600,400], "meter": [4,4],
    "sourceKey": "C", "section": "前奏",
    "chordChanges": [[0,"C"]],
    "events": [{
      "beat":0,"duration":1,"technique":"pluck","tie":false,
      "notes":[{"sourceString":5,"sourceFret":3,"sourceSymbol":"3"}]
    }],
    "vocal": []
  }],
  "performance": [1],
  "unresolved": []
}
```

- sourceDocuments 可放原始 PDF 的 name/path，由构建器作为原文件内嵌下载。
- sourceKey 在原调改变的第一个小节更新，后续小节也填该段调；不要根据小节编号写死。
- events 按 beat 排列，可含 pluck、strum、arpeggio、slap、pull-off、rest 等。休止 notes 为 []；明确留白/休止与漏转录的差别。默认播放器真实实现拨弦、扫弦、琶音和拍弦；其他装饰奏法须依声学需求扩展，不能用改标签声称已实现。
- strum/arpeggio notes 列出该次箭头实际发声的全部弦和品位，并填 direction: down/up、sourceStringRange。不是整个和弦每次都六弦齐响。
- tie=true 表示承接上一音、不重新拨弦。上一发声音的 sustain 要覆盖延音的完整拍数（可跨小节）。审核连线含义，不能把所有弧线当延音。
- sourceSymbol=× 只有确认其为和弦弦位音后使用；sourceFret 要等于对应原谱 shapes。实际静音叉号用制音技术，不能转成音高。
- vocal 项含 beat、duration、degree (1–7，0 休止，null 延音)、octave、lyric，可含已核实实际 pitchBefore。有音高的旋律项必须提供已核实的 `pitchBefore`，或明确设置已核实的 `settings.sourceVocalTonicMidi`（原谱实际调中无八度点的 1 对应 MIDI，包含原 Capo）。编译器按每段 sourceKey、degree、accidental 和 octave 计算实际音高，再按 actualSemitones 得到 pitchAfter；绝不默猜基准八度。第二遍覆盖的 vocal 也要编译。degree=null 表示延续前音，degree=0 表示休止；`tie=true` 的有音高项延续相邻前音。不要凭空加人声 MIDI。简谱和歌词保留原位置，默认只弹吉他，主旋律开关开启时加入钢琴采样。
- performance 中数字是原谱小节编号。第二遍歌词可用 {"bar":1,"section":"主歌二","vocal":[...]} 覆盖；保持对应吉他事件，不能混淆源编号和演奏编号。
- targetNotes 可手工指定该事件每个源音的 [目标弦,相对目标夹品位,八度调整整数]。数量/顺序需对应 source notes，必须重新运行验证与真实指法检查。
- actualSemitones 可覆盖自动选择的最近半音位移（默认 -6 到 +5）；必须与目标实际调一致。有歌唱音域要求时确认具体上/下行转调，不能只根据同名调忽略八度。

## 逐音与指法复核

建立 source-to-score.json 或等价工作台账：每条事件的原页、区域、原弦品/拍点、目标弦品、实际 MIDI、异常与修正。每页独立抽取至少一个非重复音、低音转位、密集节奏或装饰奏法锚点；关键易误处逐条核对。全部小节仍需视觉对照，不以抽样取代完整转录检查。

基础指法图允许与旋律变化使用不同弦位，前提是图上声部完整匹配该和弦及 slash 低音，且界面清楚说明。自动图形搜索优先低把位，不能证明按法对每位演奏者都简单。检查横按、空弦、禁弹弦、低音和换把。旋律形状若跳把严重，使用人工目标弦位约束重新求解并记录，不改音高偷换容易按的伴奏。

## 已核实的滑音与击勾弦

`engravingVersion: 2` 启用逐弦的连奏线；事件的 `transition` 可为 `slide`、`hammer-on`、`pull-off`。事件前一项必须包含相同的原弦，目标弦也必须一致；上下行连奏不允许自动换弦。播放器延续该弦正在发声的采样，滑音使用连续音高斜坡，击勾弦使用短音高过渡，不添加新的拨弦起音。独立点击品位仍用于试听最终音高。新曲应以真实渲染音频验证过渡后的音高。

源和弦括号数字仅保留源指法版本，目标名称去掉括号数字，防止误解为转调后的品位。已支持 add#11、maj7add13、madd9 的完整和弦组成音；原图 `add11+` 需先核实后统一为 `add#11`。

密集谱可在 settings 指定 `barsPerSystem: 2, denseBarsPerSystem: 1`，含三十二分的系统改为一小节并用整行宽度。此选项只对明确设置的新曲生效，须重新检查实际 A4 渲染。

屏幕分行不使用 barsPerSystem 的纸谱限制；该设置仅用于 A4 打印。共享 assets/practice.js 处理窗口宽度、独立主旋律事件和钢琴采样，不能加入特定歌曲小节号。
