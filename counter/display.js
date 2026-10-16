'use strict';
const row=document.getElementById('row');
const personal=document.getElementById('personal');
const gate=new FCEstimates.Gate();
let socket,reconnect,lastMessage=0,current=null,recordKey='',busy=false;
function fit(){
  const width=row.scrollWidth;
  if(width>0)row.style.transform=`scaleX(${Math.min(1,(window.innerWidth-2)/width)})`;
}
function hide(){row.dataset.visible='false';current=null;recordKey='';personal.hidden=true;}
function show(result){
  if(!result){hide();return;}
  current=result;
  if(recordKey!==result.recordKey){recordKey=result.recordKey;personal.hidden=true;pollPersonal();}
  FCEstimates.accuracies.forEach((a,i)=>document.getElementById('pp'+a).textContent=result.values[i].toFixed(1));
  document.getElementById('mods').textContent=result.mods==='NM'?'':result.mods;
  document.getElementById('unranked').textContent=result.ranked?'':'비랭크';
  row.title=result.mode===3?'mania: 판정 분포에 따른 예상 FC pp':'최대 콤보, 0 miss 예상 pp';
  row.dataset.visible='true';fit();
}
async function pollPersonal(){
  if(busy||!current||preview)return;
  const expected=recordKey;
  busy=true;
  try{
    const response=await fetch('http://127.0.0.1:24051/personal',{cache:'no-store',signal:AbortSignal.timeout(2000)});
    if(!response.ok)throw new Error('record service unavailable');
    const data=await response.json();
    if(!current||recordKey!==expected)return;
    const actual=JSON.stringify([data.checksum,data.mode,data.username]);
    if(actual!==expected||data.status!=='ok'||typeof data.record?.pp!=='number'||!Number.isFinite(data.record.pp)||data.record.pp<0){personal.hidden=true;fit();return;}
    document.getElementById('personal-pp').textContent=data.record.pp.toFixed(1);
    document.getElementById('personal-mods').textContent=data.record.mods==='NM'?'NM':data.record.mods;
    personal.title='이 PC에 저장된 본인 완주 기록 중 최고 pp (현재 선택 모드와 다를 수 있음)';
    personal.hidden=false;fit();
  }catch{
    if(current&&recordKey===expected){personal.hidden=true;fit();}
  }finally{busy=false;}
}
function connect(){
  clearTimeout(reconnect);hide();gate.reset();
  socket=new WebSocket('ws://127.0.0.1:24050/ws');
  socket.onmessage=event=>{
    try{lastMessage=performance.now();show(gate.update(JSON.parse(event.data),lastMessage));}
    catch{hide();}
  };
  socket.onclose=()=>{hide();reconnect=setTimeout(connect,1000);};
  socket.onerror=()=>{hide();socket.close();};
}
setInterval(()=>{if(performance.now()-lastMessage>1500)hide();},250);
setInterval(pollPersonal,1000);
window.addEventListener('resize',fit);
window.addEventListener('pagehide',()=>{clearTimeout(reconnect);if(socket)socket.close();});
const preview=new URLSearchParams(location.search).get('demo')==='1';
if(preview){
  show({values:[442.42,473.71,527.81,565.68],mods:'DT',mode:0,ranked:true,recordKey:'demo'});
  document.getElementById('personal-pp').textContent='536.4';
  document.getElementById('personal-mods').textContent='DT';personal.hidden=false;
  row.insertAdjacentText('beforeend',' DEMO');fit();
}else connect();
