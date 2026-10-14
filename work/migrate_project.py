from pathlib import Path
import shutil,json,hashlib,datetime
ROOT=Path('/Users/simonluo/罗鑫宇/Vibe Coding/smartchord');CURRENT=Path('/Users/simonluo/Documents/ChatGPT/picking谱子调子转换小工具');INITIAL=Path('/Users/simonluo/Documents/Codex/2026-10-14/google-drive-handoff-x20-https-drive');SKILL=Path('/Users/simonluo/.codex/skills/smartchord');DRIVE=Path('/Users/simonluo/Library/CloudStorage/GoogleDrive-simooonluo@gmail.com/我的云端硬盘/仓颉_G指法Capo2_Codex_Handoff_2026-10-14')
records=[]
def inventory(src,dst):
 result=[]
 for f in sorted(src.rglob('*')):
  if f.is_file():result.append({'source':str(f),'destination':str(dst/f.relative_to(src)),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
 return result
# The local work/ contains only this migration script. Move the earlier work/ into it.
for item in CURRENT.iterdir():
 dest=ROOT/item.name
 if dest.exists():
  assert item.name=='work'
  for child in item.iterdir():assert not (dest/child.name).exists()
  for child in list(item.iterdir()):
   if child.is_dir():records+=inventory(child,dest/child.name)
   else:records.append({'source':str(child),'destination':str(dest/child.name),'bytes':child.stat().st_size,'sha256':hashlib.sha256(child.read_bytes()).hexdigest()})
   shutil.move(str(child),str(dest/child.name))
  item.rmdir()
 else:
  if item.is_dir():records+=inventory(item,dest)
  else:records.append({'source':str(item),'destination':str(dest),'bytes':item.stat().st_size,'sha256':hashlib.sha256(item.read_bytes()).hexdigest()})
  shutil.move(str(item),str(dest))
CURRENT.rmdir();CURRENT.symlink_to(ROOT,target_is_directory=True)
archive=ROOT/'archive/initial-development';archive.parent.mkdir(parents=True,exist_ok=True);assert not archive.exists();records+=inventory(INITIAL,archive);shutil.move(str(INITIAL),str(archive));INITIAL.symlink_to(archive,target_is_directory=True)
project_skill=ROOT/'skills/smartchord';project_skill.parent.mkdir(exist_ok=True);assert not project_skill.exists();records+=inventory(SKILL,project_skill);shutil.move(str(SKILL),str(project_skill));SKILL.symlink_to(project_skill,target_is_directory=True)
source=ROOT/'sources/drive-handoff';source.parent.mkdir(exist_ok=True);assert not source.exists();records+=inventory(DRIVE,source);shutil.copytree(DRIVE,source)
for r in records:
 file=Path(r['destination']);assert file.stat().st_size==r['bytes'];assert hashlib.sha256(file.read_bytes()).hexdigest()==r['sha256'],r['destination']
(ROOT/'docs').mkdir(exist_ok=True)
(ROOT/'docs/migration-manifest.json').write_text(json.dumps({'date':'2026-10-14','project':str(ROOT),'verification':'SHA-256 readback PASS before any path adaptation','legacyPathsAreSymlinks':[str(CURRENT),str(INITIAL),str(SKILL)],'driveOriginals':'preserved; complete snapshot copied into project','files':records},ensure_ascii=False,indent=2))
# Keep Codex's live session logs in place; archive snapshots inside the project.
conversation=ROOT/'docs/conversation';conversation.mkdir(exist_ok=True);entries=[]
for log in sorted(Path('/Users/simonluo/.codex/sessions/2026/10/14').glob('*01a13639-b070-7ca3-ac45-12c0e76d1ba0*.jsonl')):
 target=conversation/log.name;shutil.copy2(log,target)
 for line in target.open():
  record=json.loads(line);payload=record.get('payload',{})
  if record.get('type')=='response_item' and payload.get('type')=='message' and payload.get('role') in ['user','assistant'] and payload.get('channel') not in ['analysis','summary']:
   body='\n'.join(c.get('text','') for c in payload.get('content',[]) if c.get('type') in ['input_text','output_text','text'])
   if body:entries.append((record.get('timestamp',''),payload['role'],body))
entries.sort(key=lambda e:e[0]);text=['# 本对话文字记录','\n迁移时的本地日志快照；原始 JSONL 包含工具记录与会话元数据。当前迁移操作之后的新消息仍保存在 Codex 正常会话日志里。\n']
for timestamp,role,body in entries:text+=['\n## '+timestamp+' · '+('用户' if role=='user' else '助手'),'\n'+body+'\n']
(conversation/'conversation.md').write_text('\n'.join(text))
attachment=Path('/var/folders/2f/fjctbb912y775mzwl83b2y_80000gn/T/codex-clipboard-fa442a15-4ec2-49e1-b437-4535e1f93c3a.png')
if attachment.exists():
 (conversation/'attachments').mkdir(exist_ok=True);shutil.copy2(attachment,conversation/'attachments/rhythm-report.png')
print('Migrated and SHA-256 verified',len(records),'files; archived',len(entries),'conversation messages.')
