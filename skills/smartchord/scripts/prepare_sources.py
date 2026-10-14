"""Non-destructive screenshot/PDF intake; preserves source bytes and page order."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('files',nargs='+');p.add_argument('--out',required=True);a=p.parse_args();out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True);manifest={'originals':[],'sourceImages':[]}
for index,name in enumerate(a.files,1):
 f=Path(name).resolve();dst=out/(f'{index:02d}_'+f.name)
 if dst.exists() and dst.read_bytes()!=f.read_bytes():raise ValueError('Conflicting existing source '+str(dst))
 shutil.copy2(f,dst);manifest['originals'].append({'name':f.name,'path':str(dst),'sha256':hashlib.sha256(dst.read_bytes()).hexdigest()})
 if f.suffix.lower()=='.pdf':
  prefix=out/f'{index:02d}_page';subprocess.run(['pdftoppm','-r','160','-png',str(dst),str(prefix)],check=True)
  pages=sorted(out.glob(prefix.name+'-*.png'),key=lambda x:int(x.stem.rsplit('-',1)[1]))
 else:pages=[dst]
 for page in pages:manifest['sourceImages'].append({'name':page.name,'path':str(page),'sha256':hashlib.sha256(page.read_bytes()).hexdigest()})
(out/'source-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));print('Prepared',len(manifest['sourceImages']),'images; manifest',out/'source-manifest.json')
