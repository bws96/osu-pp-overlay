'use strict';
const fs=require('node:fs');
const {acronyms}=require('./record_calculator.cjs');
const FIELDS={0:['greats','oks','mehs'],3:['perfects','greats','goods','oks','mehs']};
function allocate(template,fields,remaining){
 const sum=fields.reduce((n,f)=>n+(template[f]||0),0);
 if(sum<=0){const result=Object.fromEntries(fields.map(f=>[f,0]));result[fields[0]]=remaining;return result;}
 const items=fields.map((field,index)=>{const exact=(template[field]||0)*remaining/sum;return {field,index,count:Math.floor(exact),fraction:exact%1};});
 let left=remaining-items.reduce((n,item)=>n+item.count,0);
 items.sort((a,b)=>b.fraction-a.fraction||a.index-b.index);
 for(let i=0;i<left;i++)items[i%items.length].count++;
 return Object.fromEntries(items.map(({field,count})=>[field,count]));
}
class Forecast{
 constructor(binding){this.api=require(binding);this.key=null;}
 prepare(input){
  const key=JSON.stringify([input.path,input.checksum,input.mode,input.mods]);
  if(key===this.key)return;
  let map=this.api.PlayBeatmap.parse(fs.readFileSync(input.path,'utf8'));
  if(map.mode!==input.mode){map=map.convert(input.mode);if(!map)throw new Error('Map conversion failed');}
  const mods=acronyms(input.mods).map(acronym=>({acronym,settings:new Map()}));mods.push({acronym:'CL',settings:new Map()});map.applyMods(mods);
  const full=map.createGradualDifficulty();full.skipToEnd();
  this.diff=full.createDifficultyAttrs();this.maxCombo=this.diff.getData().maxCombo;
  this.base=map.createScore(1);this.map=map;this.key=key;
  this.total=FIELDS[input.mode].reduce((n,f)=>n+(this.base[f]||0),0)+(this.base.misses||0);
  this.gradual=map.createGradualDifficulty();this.lastTime=-Infinity;this.lastPassed=0;
 }
 calculate(input){
  if(!FIELDS[input.mode])throw new Error('Unsupported ruleset');
  this.prepare(input);
  const fields=FIELDS[input.mode],hits=input.hits;
  const score={...this.base,isLegacyScore:true,totalScore:input.score||0,maxCombo:input.maxCombo||0,
   greats:hits['300']||0,oks:hits['100']||0,mehs:hits['50']||0,misses:hits['0']||0,
   perfects:input.mode===3?(hits.geki||0):0,goods:input.mode===3?(hits.katu||0):0,
   comboBreaks:hits.sliderBreaks||0,sliderEndHits:hits.sliderEndHits||0,
   largeTickHits:hits.largeTickHits||0,smallTickHits:hits.smallTickHits||0};
  const passed=fields.reduce((n,f)=>n+score[f],score.misses);
  if(passed>this.total)throw new Error('Score/map transition in progress');
  if(input.time<this.lastTime||passed<this.lastPassed)this.gradual=this.map.createGradualDifficulty();
  this.gradual.skipToTime(Math.max(0,input.time));
  const currentDiff=this.gradual.createDifficultyAttrs().getData();
  const accuracy=passed>0?this.gradual.calculateProgressiveAccuracy(score):1;
  const remaining=Math.max(0,this.total-passed);
  const template=this.map.createScore(accuracy);
  const additional=allocate(template,fields,remaining);
  const projected={...score};
  for(const field of fields)projected[field]+=additional[field];
  projected.maxCombo=Math.min(this.maxCombo,Math.max(score.maxCombo,(input.combo||0)+Math.max(0,this.maxCombo-currentDiff.maxCombo)));
  // Remaining slider ends/ticks are hit; past failures, judgement counts and combo breaks remain.
  for(const field of ['sliderEndHits','largeTickHits','smallTickHits'])projected[field]=Math.max(score[field],this.base[field]||0);
  projected.accuracy=this.map.calculateAccuracy(projected);
  const pp=this.map.calculatePerformance(this.diff,projected).pp;
  if(!Number.isFinite(pp)||pp<0)throw new Error('Invalid forecast');
  this.lastTime=input.time;this.lastPassed=passed;
  return {forecast:pp,accuracy,projectedAccuracy:projected.accuracy,remaining,projectedCombo:projected.maxCombo,projectedMisses:projected.misses,projected};
 }
}
if(require.main===module){
 const readline=require('node:readline');let calculator;
 const lines=readline.createInterface({input:process.stdin,crlfDelay:Infinity});
 lines.on('close',()=>process.exit(0));
 lines.on('line',line=>{try{const input=JSON.parse(line);calculator??=new Forecast(input.binding);const result=calculator.calculate(input);delete result.projected;console.log(JSON.stringify({ok:true,...result}));}
 catch(error){console.log(JSON.stringify({ok:false,error:String(error)}));}});
}else module.exports={Forecast,allocate};
