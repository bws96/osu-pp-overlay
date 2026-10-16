(function(root){
  'use strict';
  const accuracies=[95,97,99,100];
  function parse(data){
    const menu=data && data.menu;
    if(!menu || menu.state!==5 || ![0,3].includes(menu.gameMode)) return null;
    const bm=menu.bm, mods=menu.mods;
    if(!bm || !bm.md5 || !bm.path?.file?.endsWith('.osu') || !mods) return null;
    const values=accuracies.map(a=>menu.pp?.[String(a)]);
    if(values.some(v=>typeof v!=='number'||!Number.isFinite(v)||v<0) || values[3]<=0) return null;
    return {key:JSON.stringify([bm.md5,menu.gameMode,mods.num,bm.path.file]),
      checksum:bm.md5,username:data.userProfile?.name||'',recordKey:JSON.stringify([bm.md5,menu.gameMode,data.userProfile?.name||'']),
      values,mods:mods.str || 'NM',mode:menu.gameMode,ranked:[4,5].includes(bm.rankedStatus)};
  }
  class Gate{
    constructor(){this.reset();}
    reset(){this.key=null;this.since=0;this.last=0;}
    update(data,now){
      const result=parse(data);
      this.last=now;
      if(!result){this.key=null;return null;}
      if(result.key!==this.key){this.key=result.key;this.since=now;return null;}
      return now-this.since>=300 ? result : null;
    }
  }
  const api={accuracies,parse,Gate};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  else root.FCEstimates=api;
})(globalThis);

