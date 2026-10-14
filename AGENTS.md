# SmartChord 项目工作约定

本对话的工程与产品决定均属于本项目。首先阅读 README.md 和 docs/PROJECT_STATE.md；涉及历史决定时读取 docs/conversation/conversation.md 或对应原始日志。

- 当前歌曲工程：work/project。可复用 skill：skills/smartchord，安装目录只是项目内文件的链接。
- 交接要求与原谱在 sources/drive-handoff；archive/initial-development 是历史版本，不能当最新实现。
- 中间文件留 work，用户成果留 outputs。更改通用播放器/节奏时同步检查当前《仓颉》实现与 skill，但不要用硬编码歌曲数据污染通用工具。
- 逐音准确性、结构自动验证、人耳试听与演奏接受分开记录；不以工程 PASS 替代视觉/音乐核查。
- 每次交付前核对 A4 实际渲染。一次只交付一个完整歌曲 HTML，用户另行要求的 skill 打包照常交付。
- Google Drive 本地快照不证明云端同步，参考仓库 chord-inspiration 不属于本工程的可随意修改文件。
