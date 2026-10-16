'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const {parse,match}=require('./live_counter/logic.js');
const data={state:{number:2},beatmap:{checksum:'a',time:{live:2000}},play:{mode:{number:0},mods:{number:64},pp:{current:123.45},failed:false}};
const active=parse(data);assert.equal(active.current,123.45);
const result={status:'ok',checksum:'a',mode:0,mods:64,time:1900,forecast:456.78};assert.ok(match(result,active));
assert.ok(!match({...result,mods:0},active));assert.ok(!match({...result,time:4000},active));
assert.ok(!match({...result,time:0},active));assert.ok(!match({...result,forecast:NaN},active));
assert.equal(parse({...data,state:{number:5}}),null);assert.equal(parse({...data,play:{...data.play,failed:true}}),null);
let ws,now=0;const timers=[];
const nodes=new Map(['live','current','forecast'].map(id=>[id,{dataset:{},textContent:''}]));
const context={document:{getElementById:id=>nodes.get(id)},LiveEstimates:{parse,match},
 WebSocket:class{constructor(){ws=this;}send(){}close(){this.onclose?.();}},performance:{now:()=>now},
 setTimeout:()=>1,clearTimeout(){},setInterval:fn=>timers.push(fn),window:{addEventListener(){}},URLSearchParams,location:{search:''},AbortSignal,
 fetch:async()=>({json:async()=>result})};
vm.runInNewContext(fs.readFileSync('live_counter/display.js','utf8'),context);
(async()=>{
 ws.onmessage({data:JSON.stringify(data)});assert.equal(nodes.get('live').dataset.visible,'true');assert.equal(nodes.get('current').textContent,'123.5');
 await timers[0]();assert.equal(nodes.get('forecast').textContent,'456.8');
 ws.onmessage({data:JSON.stringify({...data,beatmap:{...data.beatmap,time:{live:0}}})});assert.equal(nodes.get('forecast').textContent,'—');
 ws.onmessage({data:JSON.stringify({...data,state:{number:5}})});assert.equal(nodes.get('live').dataset.visible,'false');
 ws.onmessage({data:JSON.stringify(data)});now=2000;timers[1]();assert.equal(nodes.get('live').dataset.visible,'false');
 console.log('PASS: live numbers, forecast matching, retry, failed/menu hiding and stale data');
})().catch(e=>{console.error(e);process.exitCode=1;});
