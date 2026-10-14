from pathlib import Path
p=Path(__file__).parent/'app.js';s=p.read_text()
s=s.replace('const W=760,H=315','const W=760,H=250')
s=s.replace('let r=list[k],x0=30+k*365,xx=t=>x0+22+t*82,ys=s=>72+(s-1)*15;',"const stride=list.length===3?240:365,barWidth=stride-10,beatWidth=(barWidth-27)/4;let r=list[k],x0=30+k*stride,xx=t=>x0+15+t*beatWidth,ys=s=>72+(s-1)*15;")
s=s.replace("transform:'translate(0,85)'","transform:'translate(0,23)'")
s=s.replace('x:x0,y:-57,width:359,height:281','x:x0,y:-8,width:barWidth,height:229')
s=s.replace('txt(g,x0,-69,','txt(g,x0,-11,').replace('txt(g,x0+350,-69,','txt(g,x0+barWidth-5,-11,')
s=s.replace("const center=Math.min(xx(t)+20,x0+317);txt(g,center,-41,label(c),'chord',{'text-anchor':'middle'});g.append(foundationDiagram(c,center-34.5,-36));","const center=Math.min(xx(t)+14,x0+barWidth-25);txt(g,center,9,label(c),'chord',{'text-anchor':'middle'});let chart=foundationDiagram(c,0,0);chart.setAttribute('transform',`translate(${center-24.15},14) scale(.7)`);g.append(chart);")
s=s.replace('x0+355','x0+barWidth').replace('x0+351','x0+barWidth-4')
s=s.replace('(local.x-x0-22)/82','(local.x-x0-15)/beatWidth')
start=s.index('function render(){');end=s.index('const sampleLoads=',start)
s=s[:start]+s[start:end].replace("const root=$('#score');root.replaceChildren();prepareVoicings();const pageCount=Math.ceil(rows.length/6)+Math.ceil(voicingList.length/20);", "const root=$('#score');root.replaceChildren();prepareVoicings();const systems=[];for(let i=0;i<rows.length;){let take=rows.slice(i,i+3).some(r=>r.events.some(e=>e.duration<.25))?2:3;systems.push(rows.slice(i,i+take));i+=take}const scorePages=Math.ceil(systems.length/4),pageCount=scorePages+Math.ceil(voicingList.length/20);") .replace('for(let page=0;page<Math.ceil(rows.length/6);page++)','for(let page=0;page<scorePages;page++)').replace("let sheet=document.createElement('section');sheet.className='sheet';let rr=rows.slice(page*6,page*6+6);","let sheet=document.createElement('section');sheet.className='sheet';let ss=systems.slice(page*4,page*4+4),rr=ss.flat();sheet.dataset.firstBar=rr[0].i;").replace("for(let i=0;i<rr.length;i+=2){let wrap=document.createElement('div');wrap.className='system';wrap.append(renderSystem(rr.slice(i,i+2)));sheet.append(wrap)}","for(const systemRows of ss){let wrap=document.createElement('div');wrap.className='system';wrap.append(renderSystem(systemRows));sheet.append(wrap)}").replace('Math.ceil(rows.length/6)+page+1','scorePages+page+1')+s[end:]
s=s.replace('key(rows[i*6])',"key(rows[Number(el.closest('.sheet').dataset.firstBar)-1])")
p.write_text(s)
p=Path(__file__).parent/'app.css';s=p.read_text();s+='''\n/* Compact engraving keeps type sizes while fitting three bars across A4. */
.chord{font-size:16px}.section-tag{font-size:9px}.bar-number{font-size:9px}
@media print{.sheet-heading{height:10mm;margin-bottom:2mm;padding-bottom:1mm}.system{margin:.5mm 0 1mm}.page-footer{margin-top:1mm;padding-top:1mm}.chord-foundation .foundation-open,.chord-foundation .foundation-fret{font-size:10px}}
''';p.write_text(s)
p=Path(__file__).parent/'verify.cjs';s=p.read_text().replace('count(),18)','count(),10)').replace('printPages:18','printPages:10');p.write_text(s)
