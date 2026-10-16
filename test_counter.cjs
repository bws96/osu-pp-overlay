'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const {Gate,parse}=require('./counter/logic.js');
const sample={userProfile:{name:'Player'},menu:{state:5,gameMode:0,mods:{num:64,str:'DT'},bm:{md5:'a',path:{file:'test.osu'},rankedStatus:4},pp:{95:442.42,97:473.71,99:527.81,100:565.68}}};
const copy=()=>structuredClone(sample);
let g=new Gate();assert.equal(g.update(sample,0),null);assert.equal(g.update(sample,299),null);
assert.deepEqual(g.update(sample,301).values,[442.42,473.71,527.81,565.68]);
let changed=copy();changed.menu.mods.num=0;assert.equal(g.update(changed,400),null);assert.ok(g.update(changed,701));
changed.menu.state=2;assert.equal(g.update(changed,800),null);
changed=copy();changed.menu.gameMode=3;assert.equal(parse(changed).mode,3);
changed.menu.gameMode=1;assert.equal(parse(changed),null);
for(const bad of [NaN,Infinity,-1,null,undefined,true,'400']){changed=copy();changed.menu.pp[99]=bad;assert.equal(parse(changed),null);}
function browser(){
 const nodes=new Map();
 for(const id of ['row','mods','unranked','pp95','pp97','pp99','pp100','personal','personal-pp','personal-mods'])nodes.set(id,{dataset:{},style:{},textContent:'',title:'',hidden:true,scrollWidth:600});
 let ws,now=0;const timers=[];
 let payload={checksum:'a',mode:0,username:'Player',status:'ok',record:{pp:536.35154,mods:'DT'}};
 class Socket{constructor(){ws=this;}close(){this.onclose?.();}}
 const context={FCEstimates:{Gate,parse,accuracies:[95,97,99,100]},document:{getElementById:id=>nodes.get(id)},window:{innerWidth:670,addEventListener(){}},
  location:{search:''},URLSearchParams,AbortSignal,WebSocket:Socket,performance:{now:()=>now},
  setTimeout:()=>1,clearTimeout(){},setInterval:fn=>timers.push(fn),
  fetch:async()=>({ok:true,json:async()=>payload})};
 vm.runInNewContext(fs.readFileSync('counter/display.js','utf8'),context);
 return {nodes,timers,send(data,time){now=time;ws.onmessage({data:JSON.stringify(data)});},setPayload(value){payload=value;},close(){ws.onclose();}};
}
(async()=>{
 const b=browser();b.send(sample,0);b.send(sample,301);await new Promise(setImmediate);
 assert.equal(b.nodes.get('row').dataset.visible,'true');assert.equal(b.nodes.get('pp100').textContent,'565.7');
 assert.equal(b.nodes.get('personal').hidden,false);assert.equal(b.nodes.get('personal-pp').textContent,'536.4');
 assert.equal(b.nodes.get('personal-mods').textContent,'DT');
 b.setPayload({checksum:'another-map',mode:0,username:'Player',status:'ok',record:{pp:999,mods:'HD'}});
 await b.timers[1]();assert.equal(b.nodes.get('personal').hidden,true);
 b.setPayload({checksum:'a',mode:0,username:'Somebody Else',status:'ok',record:{pp:999,mods:'HD'}});
 await b.timers[1]();assert.equal(b.nodes.get('personal').hidden,true);
 b.setPayload({checksum:'a',mode:0,username:'Player',status:'none',record:null});await b.timers[1]();assert.equal(b.nodes.get('personal').hidden,true);
 b.close();assert.equal(b.nodes.get('row').dataset.visible,'false');assert.equal(b.nodes.get('personal').hidden,true);
 console.log('PASS: FC rows, selection changes, personal pp, wrong map/user rejection, no-record and disconnect hiding');
})().catch(e=>{console.error(e);process.exitCode=1;});
