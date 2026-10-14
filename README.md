# SmartChord · 智能吉他谱

**Turn guitar tabs into interactive sheet music you can play, practice, and print.**  
**把吉他谱截图或 PDF，变成能试听、能练习、能打印的交互六线谱。**

[中文](#中文) · [English](#english) · [体验示例](#先体验成品) · [安装 SmartChord Skill](#安装-smartchord-skill)

---

## 中文

### 让喜欢的吉他谱，更适合自己弹

找到一份谱子，但它用的不是你熟悉的指法？想听清前奏里的每个音，或把一段难弹的扫弦放慢练习？

**SmartChord 是一个用于 Codex 的制谱 Skill。** 你提供完整的吉他六线谱截图或 PDF，告诉它想用的指法调和变调夹位置，它就可以协助核对原谱、转换指法，并制作一份**完整的交互 HTML 乐谱**。

制谱在 Codex 中完成。**拿到成品后，只需浏览器**：打开一个 HTML 文件，就能看谱、试听、分段练习，还能打印成 A4 纸谱。

### 先体验成品

不安装 Skill，也能先体验已经制作好的乐谱。

| 示例歌曲 | 乐谱文件 | 演奏设置 |
| --- | --- | --- |
| 五月天《仓颉》 | [下载交互乐谱](outputs/%E4%BA%94%E6%9C%88%E5%A4%A9%20-%20%E4%BB%93%E9%A2%89.html) | G 指法 · Capo 2；后段升调 |
| 陈绮贞《太聪明》 | [下载交互乐谱](outputs/%E9%99%88%E7%BB%AE%E8%B4%9E%20-%20%E5%A4%AA%E8%81%AA%E6%98%8E.html) | G 指法 · Capo 2 |

**体验方法：** 点击上方链接，在 GitHub 文件页面选择 **Download raw file** 下载 `.html`，然后用 Chrome 或其他现代浏览器打开。点击“播放”即可开始试听。文件保存到本地后可以离线使用。

### 能做什么？

| 转换吉他谱 | 练习整首歌曲 |
| --- | --- |
| **按自己习惯的指法弹。** 转换和弦，也同步处理六线谱中的旋律音、低音和弦位，而不是只替换和弦名。 | **点击就能听。** 支持吉他试听、单音试听、播放位置跟随，并可开启钢琴主旋律提示音。 |
| **保留原谱内容。** 尽量保留 picking、扫弦、歌词、节奏、反复和升调；无法确定的地方需要核对。 | **慢下来反复练。** 可以调节 BPM、选择段落、循环播放、从指定位置继续。 |
| **看清具体按法。** 显示六线谱、和弦图和扫弦方向；需要时可切换原谱与目标指法对照。 | **带走一份纸谱。** 一个 HTML 文件可离线打开，点击“打印 / 导出 PDF”即可按 A4 排版。 |

### 安装 SmartChord Skill

> **只想使用示例乐谱？** 不需要安装。下面的步骤只针对**想把自己的吉他谱做成交互乐谱**的人。

你需要能在本机运行的 **Codex**（CLI、IDE 扩展或支持本地 Skill 的客户端），以及一份自己的吉他谱。处理 PDF、音频和打印时，还可能需要 Python、Node.js、浏览器或其他本地工具；Codex 会按 [环境说明](skills/smartchord/references/tools.md) 检查所需依赖。

**方法一：在 Codex 中安装（推荐先试）**

打开 Codex，使用内置的 `$skill-installer`，告诉它：

```text
$skill-installer
请从 https://github.com/simooon15/smartchord
安装 skills/smartchord 这个 Skill。
安装后检查能否使用 $smartchord。
```

**方法二：手动安装（macOS / Linux）**

在终端运行：

```bash
git clone https://github.com/simooon15/smartchord.git
mkdir -p ~/.agents/skills
cp -R smartchord/skills/smartchord ~/.agents/skills/smartchord
```

安装完成后，目录应包含 `~/.agents/skills/smartchord/SKILL.md`。重新打开 Codex 会话，在输入框中输入 `$smartchord`，或通过 `/skills` 查看。Skill 的本地安装位置参考 [Codex 官方说明](https://developers.openai.com/codex/skills)。

也可以从仓库下载 [SmartChord Skill 压缩包](outputs/smartchord.zip)，将其中**包含 `SKILL.md` 的完整 `smartchord` 文件夹**放到 `~/.agents/skills/` 下；不要只复制 `SKILL.md`，它还需要其他脚本和资源。

### 用 SmartChord 制作自己的谱子

**1. 准备原谱。** 提供完整、清晰的六线谱截图或 PDF。多张截图尽量保持顺序，别漏掉前奏、间奏、反复记号和最后一页。

**2. 告诉它你的弹奏习惯。** 在 Codex 中附上文件，并发送：

```text
$smartchord
请把我上传的完整吉他谱做成一份交互六线谱。
我想使用 G 调指法，变调夹夹第 2 品（实际 A 调）。
请保留原谱的旋律、节奏、分解和弦、扫弦、歌词和升调。
不要只替换和弦名称，也不要用通用伴奏型覆盖原谱。
最后交付一个可离线播放、支持 A4 打印的完整 HTML 文件。
```

**3. 核对关键问题。** 如果原谱记号不清楚、原调与夹位冲突，或某些音无法在新指法下保持原八度，SmartChord 会说明情况，必要时请你选择。它不会把不确定的内容直接当作正确结果。

**4. 打开成品开始练。** 保存最终 `.html`，直接用浏览器打开即可，无需启动 SmartChord 或本地服务器。要打印时点击页面里的 **“打印 / 导出 PDF”**，在浏览器打印窗口选择 A4 或“另存为 PDF”。

### 你需要知道的事

SmartChord **不是上传文件后就能保证完全正确的自动识谱网站**。制谱过程需要 Codex 读取原谱、调用工具，并核对不清楚的音符与记号。目前以**标准六弦调弦**为基础；复杂声部、特殊调弦或特殊奏法可能需要额外处理。

目标指法不一定能保留所有原来的八度；如果必须做八度调整，成品会标明。两首示例做过浏览器、音频和 A4 打印的自动检查，**但不能把这些检查等同于人耳试听或实际弹奏验收**。

示例曲谱及吉他音色的公开再分发权限仍需核实。请尊重原谱和音色的版权。钢琴主旋律使用的 [Salamander Grand Piano V3](https://github.com/sfzinstruments/SalamanderGrandPiano) 按 CC BY 3.0 署名。

### 项目文档

- [SmartChord Skill](skills/smartchord/SKILL.md)：Skill 的实际工作流程。
- [环境与工具说明](skills/smartchord/references/tools.md)：运行与依赖。
- [产品需求文档](docs/PRD.md)：产品目标和功能定义。
- [项目状态](docs/PROJECT_STATE.md)：当前实现、验证情况与已知限制。

**当前版本：v0.1.0** · [GitHub 仓库](https://github.com/simooon15/smartchord)

---

## English

### Your guitar tabs, made playable

SmartChord is a **Codex skill** that helps turn guitar tab screenshots or PDFs into **interactive, offline HTML sheet music**. Supply the original score, choose your preferred chord shapes and capo position, and get a song you can read, listen to, practise section by section, and print.

**Making a score requires Codex and the skill. Playing a finished HTML file only requires a browser.**

### Try it first

| Song | Interactive score | Guitar setup |
| --- | --- | --- |
| Mayday — Cang Jie | [Download HTML](outputs/%E4%BA%94%E6%9C%88%E5%A4%A9%20-%20%E4%BB%93%E9%A2%89.html) | G shapes · Capo 2; later key change |
| Cheer Chen — Too Smart | [Download HTML](outputs/%E9%99%88%E7%BB%AE%E8%B4%9E%20-%20%E5%A4%AA%E8%81%AA%E6%98%8E.html) | G shapes · Capo 2 |

Open a song link, choose **Download raw file** on GitHub, and open the saved HTML in a modern browser. Playback works offline.

### What you can do

- **Play it your way:** transpose chords **and individual tab notes**, including bass notes and melodic lines.
- **See and hear the score:** follow the tab, chord diagrams and strumming directions; click to play or audition a note.
- **Practise at your pace:** adjust tempo, jump to sections, loop tricky passages, or enable a piano melody guide.
- **Take it anywhere:** receive one self-contained offline HTML per song, with an **A4 print / Save as PDF** option.

### Install the Codex skill

If you only want to open an existing example, **skip installation**.

**Option A — use the Codex skill installer:**

```text
$skill-installer
Install the skill at skills/smartchord from
https://github.com/simooon15/smartchord
and confirm that $smartchord is available.
```

**Option B — manual install (macOS / Linux):**

```bash
git clone https://github.com/simooon15/smartchord.git
mkdir -p ~/.agents/skills
cp -R smartchord/skills/smartchord ~/.agents/skills/smartchord
```

Restart Codex if necessary. Check for `~/.agents/skills/smartchord/SKILL.md`. You can also download the [skill ZIP](outputs/smartchord.zip) and put the full `smartchord` skill folder in `~/.agents/skills/`. See the [official skills guide](https://developers.openai.com/codex/skills) and [environment notes](skills/smartchord/references/tools.md) for prerequisites.

### Make your own interactive score

1. **Upload a complete score** as clear screenshots or a PDF.
2. **Tell Codex your preferred shapes and capo position:**

```text
$smartchord
Turn my complete guitar score into an interactive HTML tab.
Use G chord shapes with capo on fret 2 (concert key A).
Preserve the original picking, melody, rhythm, lyrics,
strumming patterns, repeats, and key changes.
Do not replace the original part with a generic pattern.
Deliver one complete offline HTML with A4 print / PDF support.
```

3. **Review any unclear notes or octave conflicts** when asked. A transposed arrangement may need an explicitly documented octave change.
4. **Open your final HTML in a browser.** Play, slow down, loop sections, or print / save as PDF—no server needed.

### Scope and status

**v0.1.0** focuses on standard six-string guitar tuning. SmartChord is **not** a fully automatic, error-free score-recognition website. Transcription requires visual review, and advanced techniques or alternate tunings may need adaptation. Automated browser, audio and print checks on the demos do **not** replace human listening or playing tests.

Rights to redistribute the example scores and guitar samples should be confirmed before further public distribution. The piano melody samples are credited to [Salamander Grand Piano V3](https://github.com/sfzinstruments/SalamanderGrandPiano) (CC BY 3.0).

**Learn more:** [Skill instructions](skills/smartchord/SKILL.md) · [Tooling](skills/smartchord/references/tools.md) · [Product spec](docs/PRD.md) · [Project state](docs/PROJECT_STATE.md)
