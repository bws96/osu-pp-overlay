(function(root){
 'use strict';
 function parse(data){
  const play=data?.play,checksum=data?.beatmap?.checksum;
  if(data?.state?.number!==2||!play||play.failed||![0,3].includes(play.mode?.number)||!checksum)return null;
  const current=play.pp?.current;
  if(typeof current!=='number'||!Number.isFinite(current)||current<0)return null;
  const mode=play.mode.number,mods=play.mods?.number||0,time=data.beatmap.time?.live||0;
  return {key:JSON.stringify([checksum,mode,mods]),checksum,mode,mods,time,current};
 }
 function match(data,active){
  return Boolean(active&&data?.status==='ok'&&JSON.stringify([data.checksum,data.mode,data.mods])===active.key&&
   Number.isFinite(data.forecast)&&data.forecast>=0&&Number.isFinite(data.time)&&data.time<=active.time+300&&active.time-data.time<1500);
 }
 const api={parse,match};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.LiveEstimates=api;
})(globalThis);
