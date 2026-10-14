/* Single source of truth for rhythmic values and beam geometry. Beat unit: quarter. */
const RhythmNotation=(()=>{
 const near=(a,b)=>Math.abs(a-b)<1e-7;
 function value(e){
  const duration=e.writtenDuration??e.duration;
  for(let dots=0;dots<=2;dots++){const factor=2-2**(-dots);for(let power=-4;power<=2;power++){const base=2**power;if(near(duration,base*factor))return{levels:Math.max(0,-power),dots,base,stem:base<4}}}
  throw Error('Rhythm '+duration+' requires explicit writtenDuration (e.g. tuplets); cannot infer note value');
 }
 function plan(events,meter=[4,4],breaks){
  const units=meter[0]*4/meter[1],pulse=meter[1]===8&&meter[0]>=6&&meter[0]%3===0?1.5:1;
  const edges=breaks||Array.from({length:Math.ceil(units/pulse)+1},(_,i)=>Math.min(units,i*pulse));
  const groupAt=t=>{for(let i=0;i<edges.length-1;i++)if(t>=edges[i]-1e-8&&t<edges[i+1]-1e-8)return i;return edges.length-2};
  const specs=events.map(value),groups=[];let current=[];
  function flush(){if(current.length)groups.push(current);current=[]}
  for(let i=0;i<events.length;i++){
   const e=events[i],prior=events[current.at(-1)];
   if(!specs[i].levels||e.technique==='rest'){flush();continue}
   if(prior&&(e.beamBreak||groupAt(prior.beat)!==groupAt(e.beat)||!near(prior.beat+prior.duration,e.beat)))flush();current.push(i);
  }flush();
  const beams=[],flags=[];
  for(const group of groups){
   if(group.length===1){flags.push({index:group[0],levels:specs[group[0]].levels});continue}
   const max=Math.max(...group.map(i=>specs[i].levels));
   for(let level=1;level<=max;level++){
    let run=[];const finish=()=>{if(run.length>1)beams.push({level,from:run[0],to:run.at(-1),hook:false});else if(run.length){const index=run[0],offset=group.indexOf(index),previous=group[offset-1],next=group[offset+1];let direction=offset===0?1:offset===group.length-1?-1:near(events[index].beat%(2**(1-level)),0)?1:-1;const neighbor=direction===1?next:previous;beams.push({level,from:index,to:index,hook:true,direction,neighbor});}run=[]};
    for(const i of group){if(specs[i].levels>=level)run.push(i);else finish()}finish();
   }
  }
  return{specs,groups,beams,flags};
 }
 return{value,plan};
})();
if(typeof module!=='undefined')module.exports=RhythmNotation;
