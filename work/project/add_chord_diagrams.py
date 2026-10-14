from pathlib import Path
p=Path(__file__).parent/'app.js';s=p.read_text()
insert='''// Low-position foundation shapes, string 6 → 1. Melody changes remain in the tab.
const easyShapes={
 'G':[3,2,0,0,0,3],'G/F':[1,null,0,0,0,3],'Em':[0,2,2,0,0,0],
 'Ebmaj7':[null,null,1,3,3,3],'D':[null,null,0,2,3,2],
 'Gmaj7':[3,2,0,0,0,2],'Em7':[0,2,0,0,0,0],'Em7/D':[null,null,0,0,0,0],
 'Cmaj7':[null,3,2,0,0,0],'C':[null,3,2,0,1,0],'Dsus4':[null,null,0,2,3,3],
 'D7':[null,null,0,2,1,2],'Bm7/F#':[2,null,0,2,0,2],'Dm7':[null,null,0,2,1,1],
 'G7':[3,2,0,0,0,1],'G/B':[null,2,0,0,0,3],'Am7':[null,0,2,0,1,0],
 'F':[null,null,3,2,1,1],'A':[null,0,2,2,2,0],'C#m7/G#':[4,null,2,4,2,0],
 'F#m7':[2,null,2,2,2,0],'A/C#':[null,4,2,2,2,0],'Bm7':[null,2,0,2,0,2],
 'E':[0,2,2,1,0,0],'E/G#':[4,null,2,1,0,0],'A7':[null,0,2,0,2,0]
};
function foundationShape(c){return mode==='target'?easyShapes[label(c)]:[...DATA.shapes[c]].reverse()}
function foundationDiagram(c,x,y){
 const shape=foundationShape(c),g=el('g',{class:'chord-foundation',transform:`translate(${x},${y})`,'data-chord':label(c),'data-shape':JSON.stringify(shape),role:'img','aria-label':label(c)+' 基础指法，六至一弦 '+shape.map(f=>f===null?'不弹':f+'品').join('、')});
 g.append(el('title',{},'基础按法：旋律变化按六线谱；扫弦具体按法查箭头编号。'));
 const positive=shape.filter(f=>f>0),base=Math.max(...positive,0)<=4?1:Math.min(...positive),span=Math.max(4,Math.max(...positive,0)-base+1),dy=42/span;
 if(base>1)txt(g,0,29,base+'fr','foundation-fret');
 for(let i=0;i<6;i++)line(g,12+i*9,18,12+i*9,60,'diagram-string');
 for(let i=0;i<=span;i++)line(g,12,18+i*dy,57,18+i*dy,i===0&&base===1?'diagram-nut':'diagram-string');
 shape.forEach((f,i)=>{const xx=12+i*9;if(f===null||f===0)txt(g,xx,12,f===0?'○':'×','foundation-open',{'text-anchor':'middle'});else g.append(el('circle',{cx:xx,cy:18+(f-base+.5)*dy,r:3.1,class:'diagram-dot'}));txt(g,xx,71,f===null?'–':f,'foundation-fret',{'text-anchor':'middle'})});
 return g;
}
'''
s=s.replace('let voicingMap=new Map(),voicingList=[];',insert+'\nlet voicingMap=new Map(),voicingList=[];')
s=s.replace('const W=760,H=230','const W=760,H=315')
s=s.replace("let g=el('g',{'data-bar':r.i})","let g=el('g',{'data-bar':r.i,transform:'translate(0,85)'})")
s=s.replace('x:x0,y:28,width:359,height:196','x:x0,y:-57,width:359,height:281')
s=s.replace('txt(g,x0,16,','txt(g,x0,-69,').replace('txt(g,x0+350,16,','txt(g,x0+350,-69,')
s=s.replace("r.chordChanges.forEach(([t,c])=>txt(g,xx(t)-7,44,label(c),'chord'));","r.chordChanges.forEach(([t,c])=>{const center=Math.min(xx(t)+20,x0+317);txt(g,center,-41,label(c),'chord',{'text-anchor':'middle'});g.append(foundationDiagram(c,center-34.5,-36));});")
s=s.replace('Math.ceil(rows.length/8)','Math.ceil(rows.length/6)').replace('rows.slice(page*8,page*8+8)','rows.slice(page*6,page*6+6)').replace('rows[i*8]','rows[i*6]')
s=s.replace('品位相对变调夹 · 下划线品位含八度调整 · 简谱为人声旋律','和弦图为基础按法 · 旋律换指按六线谱 · 扫弦具体按法查编号')
p.write_text(s)
p=Path(__file__).parent/'app.css';s=p.read_text();s+='\n.foundation-open,.foundation-fret{font:9px Arial,sans-serif;fill:#555}.chord-foundation .diagram-nut{stroke-width:2}.chord-foundation .diagram-string{stroke-width:.65}@media print{.foundation-open,.foundation-fret{fill:#111}}\n';p.write_text(s)
p=Path(__file__).parent/'verify.cjs';s=p.read_text().replace("count(),14)","count(),18)").replace('printPages:14','printPages:18');s=s.replace("assert.equal(await p.locator('[data-bar]').count(),93);","assert.equal(await p.locator('[data-bar]').count(),93);assert.equal(await p.locator('.chord-foundation').count(),await p.evaluate(()=>cangjie.data.rows.reduce((n,r)=>n+r.chordChanges.length,0)));",1);p.write_text(s)
