"""Check A4 pages and text bounds, rasterize every page, build review contact sheets."""
import argparse,subprocess,re,xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
p=argparse.ArgumentParser();p.add_argument('pdf');p.add_argument('--expected',type=int,required=True);p.add_argument('--out',required=True);a=p.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
info=subprocess.check_output(['pdfinfo',a.pdf],text=True);actual=int(re.search(r'Pages:\s+(\d+)',info)[1]);assert actual==a.expected,(actual,a.expected)
subprocess.run(['pdftotext','-bbox',a.pdf,str(out/'bbox.html')],check=True);pages=[p for p in ET.parse(out/'bbox.html').getroot().iter() if p.tag.endswith('page')]
for i,page in enumerate(pages,1):
 w,h=float(page.attrib['width']),float(page.attrib['height']);assert abs(w-595)<2 and abs(h-842)<2
 for word in page:
  if word.tag.endswith('word'):assert 0<=float(word.attrib['xMin'])<=float(word.attrib['xMax'])<=w and 0<=float(word.attrib['yMin'])<=float(word.attrib['yMax'])<=h,(i,word.text)
subprocess.run(['pdftoppm','-scale-to','1400','-png',a.pdf,str(out/'page')],check=True)
images=sorted(out.glob('page-*.png'),key=lambda x:int(x.stem.rsplit('-',1)[1]))
for start in range(0,len(images),6):
 canvas=Image.new('RGB',(900,1320),'#dddddd');draw=ImageDraw.Draw(canvas)
 for j,file in enumerate(images[start:start+6]):
  im=Image.open(file).convert('RGB');im.thumbnail((290,620));x=(j%3)*300+(300-im.width)//2;y=(j//3)*660+24;canvas.paste(im,(x,y));draw.text((x,y-18),'Page '+str(start+j+1),fill='black')
 canvas.save(out/f'contact-{start//6+1}.png')
print(actual,'A4 pages, text bounds PASS; review contact sheets and full-size dense pages before claiming visual acceptance')
