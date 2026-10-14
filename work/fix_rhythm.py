from pathlib import Path
import re,shutil
skill=Path('/Users/simonluo/.codex/skills/guitar-score-html')
shutil.copy2(skill/'assets/rhythm.js',Path('work/project/rhythm.js'))
render='''function renderRhythm(parent,r,xx){
 const plan=RhythmNotation.plan(r.events,r.meter,r.beamGroups),layer=el('g',{class:'rhythm-layer','pointer-events':'none'});parent.append(layer);
 plan.specs.forEach((spec,i)=>{const e=r.events[i],x=xx(e.beat),g=parent.querySelector(`[data-event="${r.i}:${e.beat}"]`);g.setAttribute('data-beam-levels',spec.levels);g.setAttribute('data-dots',spec.dots);g.setAttribute('data-duration',e.duration);if(e.technique==='rest')return;
  if(spec.stem)line(layer,x,153,x,174,'stem');for(let dot=0;dot<spec.dots;dot++)txt(layer,x+7+dot*5,162,'·','dot');
 });
 for(const beam of plan.beams){let x1=xx(r.events[beam.from].beat),x2=beam.hook?x1+beam.direction*Math.min(7,Math.abs(xx(r.events[beam.neighbor].beat)-x1)*.42):xx(r.events[beam.to].beat),y=174-(beam.level-1)*5;
  layer.append(el('line',{x1,y1:y,x2,y2:y,class:'beam rhythm-beam','data-level':beam.level,'data-from':r.events[beam.from].beat,'data-to':r.events[beam.to].beat,'data-hook':beam.hook}));
 }
 for(const flag of plan.flags){const x=xx(r.events[flag.index].beat);for(let level=1;level<=flag.levels;level++){let y=174-(level-1)*5;layer.append(el('path',{d:`M ${x} ${y} C ${x-9} ${y-2}, ${x-9} ${y-10}, ${x-4} ${y-15}`,class:'rhythm-flag','data-level':level,'data-beat':r.events[flag.index].beat}));}}
}
'''
for p in [Path('work/project/app.js'),skill/'assets/player.js']:
 s=p.read_text();s=s.replace('function renderSystem(list){',render+'\nfunction renderSystem(list){')
 a=s.index('   // A separate stem follows');b=s.index("   if(e.technique==='pull-off')",a);s=s[:a]+s[b:]
 a=s.index('  // Join subdivided attack stems');b=s.index('  for(const v of r.vocal)',a);s=s[:a]+'  renderRhythm(g,r,xx);\n'+s[b:]
 s=s.replace("if(v.duration<1){line(g,x-5,200,x+5,200,'vocal-beam');if(v.duration<=.25)line(g,x-5,203,x+5,203,'vocal-beam')}\n   if(v.duration===.75)txt(g,x+7,195,'·','dot');", "const value=RhythmNotation.value(v);for(let level=0;level<value.levels;level++)line(g,x-5,200+level*3,x+5,200+level*3,'vocal-beam');for(let dot=0;dot<value.dots;dot++)txt(g,x+7+dot*5,195,'·','dot');")
 p.write_text(s)
for p in [Path('work/project/app.css'),skill/'assets/player.css']:
 p.write_text(p.read_text()+"\n.rhythm-beam{stroke-linecap:butt}.rhythm-flag{fill:none;stroke:#555;stroke-width:1.5;stroke-linecap:round}@media print{.rhythm-flag{stroke:#111}}\n")
p=Path('work/project/build.py');s=p.read_text().replace("'JS':(P/'app.js').read_text()","'JS':(P/'rhythm.js').read_text()+'\\n'+(P/'app.js').read_text()");p.write_text(s)
p=skill/'scripts/build_html.py';s=p.read_text().replace("'JS':(ROOT/'assets/player.js').read_text()","'JS':(ROOT/'assets/rhythm.js').read_text()+'\\n'+(ROOT/'assets/player.js').read_text()");p.write_text(s)
