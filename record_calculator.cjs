'use strict';
// Runs as a short-lived, read-only calculation worker. No game process is modified.
const fs=require('node:fs');
const readline=require('node:readline');
const MODS=[[1,'NF'],[2,'EZ'],[4,'TD'],[8,'HD'],[16,'HR'],[32,'SD'],[64,'DT'],[128,'RX'],[256,'HT'],[512,'NC'],[1024,'FL'],[2048,'AT'],[4096,'SO'],[8192,'AP'],[16384,'PF'],[32768,'4K'],[65536,'5K'],[131072,'6K'],[262144,'7K'],[524288,'8K'],[1048576,'FI'],[2097152,'RD'],[4194304,'CN'],[8388608,'TP'],[16777216,'9K'],[33554432,'CO'],[67108864,'1K'],[134217728,'3K'],[268435456,'2K'],[536870912,'SV2'],[1073741824,'MR']];
function acronyms(bits){
 const mods=MODS.filter(([flag])=>(bits&flag)!==0).map(([,name])=>name);
 return mods.filter(m=>!(m==='DT'&&mods.includes('NC'))&&!(m==='SD'&&mods.includes('PF')));
}
function calculate(input){
 const {PlayBeatmap}=require(input.binding);
 const content=fs.readFileSync(input.path,'utf8');
 let best=null;
 const maps=new Map();
 for(const r of input.scores){
  // These automation/practice mods cannot award account pp.
  if(r.mods&(128|2048|8192|4194304|8388608))continue;
  let cached=maps.get(r.mods);
  if(!cached){
   let map=PlayBeatmap.parse(content);
   if(map.mode!==input.mode){map=map.convert(input.mode);if(!map)continue;}
   const mods=acronyms(r.mods).map(acronym=>({acronym,settings:new Map()}));
   mods.push({acronym:'CL',settings:new Map()});map.applyMods(mods);
   const gradual=map.createGradualDifficulty();gradual.skipToEnd();
   const diff=gradual.createDifficultyAttrs();const base=map.createScore(1);
   const total=input.mode===3?base.perfects+base.greats+base.goods+base.oks+base.mehs+base.misses:base.greats+base.oks+base.mehs+base.misses;
   cached={map,diff,base,total};maps.set(r.mods,cached);
  }
  const {map,diff,base,total}=cached;
  const hits=r.great+r.ok+r.meh+r.miss+(input.mode===3?r.perfects+r.goods:0);
  if(hits!==total)continue; // Do not present failed/incomplete plays as a completed record.
  const score={...base,totalScore:r.score,isLegacyScore:true,maxCombo:r.combo,
   greats:r.great,oks:r.ok,mehs:r.meh,misses:r.miss,
   perfects:input.mode===3?r.perfects:0,goods:input.mode===3?r.goods:0};
  score.accuracy=map.calculateAccuracy(score);
  const result=map.calculatePerformance(diff,score);
  if(!Number.isFinite(result.pp)||result.pp<0)continue;
  if(!best||result.pp>best.pp)best={pp:result.pp,mods:acronyms(r.mods).join('')||'NM',accuracy:score.accuracy,score_id:r.score_id};
 }
 return best;
}
if(require.main===module){
 let text='';process.stdin.setEncoding('utf8');
 process.stdin.on('data',part=>text+=part);
 process.stdin.on('end',()=>{try{process.stdout.write(JSON.stringify({ok:true,record:calculate(JSON.parse(text))}));}
 catch(error){process.stdout.write(JSON.stringify({ok:false,error:String(error)}));process.exitCode=1;}});
}else module.exports={acronyms,calculate};
