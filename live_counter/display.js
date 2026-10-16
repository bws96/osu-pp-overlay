'use strict';
const panel=document.getElementById('live'),currentLabel=document.getElementById('current'),forecastLabel=document.getElementById('forecast');
let active=null,socket,reconnect,busy=false,lastMessage=0,lastForecast=0;
function hide(){panel.dataset.visible='false';active=null;forecastLabel.textContent='—';}
function update(data){
 const next=LiveEstimates.parse(data);
 if(!next){hide();return;}
 if(!active||active.key!==next.key||next.time<active.time-100){forecastLabel.textContent='—';lastForecast=0;}
 active=next;currentLabel.textContent=next.current.toFixed(1);panel.dataset.visible='true';
}
async function poll(){
 if(busy||!active||demo)return;
 busy=true;
 try{
  const response=await fetch('http://127.0.0.1:24051/live',{cache:'no-store',signal:AbortSignal.timeout(1500)});
  const data=await response.json();
  if(LiveEstimates.match(data,active)){forecastLabel.textContent=data.forecast.toFixed(1);lastForecast=performance.now();}
 }catch{}finally{busy=false;}
}
function connect(){
 clearTimeout(reconnect);hide();socket=new WebSocket('ws://127.0.0.1:24050/websocket/v2?l=live-estimates');
 socket.onopen=()=>socket.send('applyFilters:live-estimates:["state","beatmap","play"]');
 socket.onmessage=event=>{try{lastMessage=performance.now();update(JSON.parse(event.data));}catch{hide();}};
 socket.onclose=()=>{hide();reconnect=setTimeout(connect,1000);};socket.onerror=()=>{hide();socket.close();};
}
const demo=new URLSearchParams(location.search).get('demo')==='1';
if(demo){panel.dataset.visible='true';currentLabel.textContent='123.4';forecastLabel.textContent='456.7';}
else{
 connect();setInterval(poll,150);
 setInterval(()=>{const now=performance.now();if(now-lastMessage>1500)hide();else if(now-lastForecast>2000)forecastLabel.textContent='—';},200);
 window.addEventListener('pagehide',()=>{clearTimeout(reconnect);socket?.close();});
}
