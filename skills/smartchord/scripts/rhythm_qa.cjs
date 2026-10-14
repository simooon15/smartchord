const assert=require('assert'),rhythm=require('../assets/rhythm.js');
const make=ds=>{let beat=0;return ds.map(duration=>{let e={beat,duration,technique:'pluck'};beat+=duration;return e})};
let p=rhythm.plan(make([.5,.5]));assert.equal(p.beams.length,1);assert.deepEqual(p.beams.map(b=>[b.level,b.from,b.to,b.hook]),[[1,0,1,false]]);assert.equal(p.flags.length,0);
p=rhythm.plan(make([.25,.25,.25,.25]));assert.deepEqual(p.beams.map(b=>[b.level,b.from,b.to]),[[1,0,3],[2,0,3]]);
p=rhythm.plan(make(Array(8).fill(.125)));assert.deepEqual(p.beams.map(b=>[b.level,b.from,b.to]),[[1,0,7],[2,0,7],[3,0,7]]);
p=rhythm.plan(make([.5,.25,.25]));assert.deepEqual(p.beams.map(b=>[b.level,b.from,b.to]),[[1,0,2],[2,1,2]]);
p=rhythm.plan(make([.25,.5,.25]));assert.equal(p.beams.filter(b=>b.level===2&&b.hook).length,2);assert.equal(p.beams.filter(b=>b.level===2&&!b.hook).length,0);
p=rhythm.plan(make([.75,.25]));assert.equal(p.specs[0].levels,1);assert.equal(p.specs[0].dots,1);assert(p.beams.some(b=>b.level===2&&b.hook&&b.direction===-1));
p=rhythm.plan(make([.375,.125,.5]));assert.equal(p.specs[0].levels,2);assert.equal(p.specs[0].dots,1);assert(p.beams.some(b=>b.level===3&&b.hook));assert.equal(rhythm.value({duration:1.5}).dots,1);
p=rhythm.plan([{beat:0,duration:.125,technique:'pluck'}]);assert.equal(p.flags[0].levels,3);assert.equal(p.beams.length,0);
p=rhythm.plan(make(Array(6).fill(.5)),[6,8]);assert.deepEqual(p.beams.map(b=>[b.from,b.to]),[[0,2],[3,5]]);
p=rhythm.plan([{beat:0,duration:.25,technique:'pluck'},{beat:.5,duration:.25,technique:'pluck'}]);assert.equal(p.flags.length,2);assert.equal(p.beams.length,0);assert.throws(()=>rhythm.value({duration:1/3}));assert.equal(rhythm.value({duration:1/3,writtenDuration:.5}).levels,1);
// Every stem must receive exactly its own rhythmic level(s), never overbeamed.
for(const ds of [[.25,.25,.5],[.5,.125,.125,.25],[.375,.125,.5],[.125,.375,.25,.25]]){
 const es=make(ds),plan=rhythm.plan(es);const coverage=es.map(()=>new Set());for(const b of plan.beams){for(let i=b.from;i<=b.to;i++){assert(plan.specs[i].levels>=b.level);coverage[i].add(b.level)}}for(const f of plan.flags)for(let l=1;l<=f.levels;l++)coverage[f.index].add(l);coverage.forEach((levels,i)=>assert.equal(levels.size,plan.specs[i].levels));}
console.log('Rhythm PASS: eighth/sixteenth/thirty-second, mixed values, dotted notes, beamlets, isolated flags, compound meter and gaps');
