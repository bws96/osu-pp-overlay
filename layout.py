"""Resolution-aware positioning. Remember the actual frame edited by the user."""
import math

def resolution(data):
    r=data.get('settings',{}).get('resolution',{})
    full=r.get('fullscreen',False)
    width=r.get('widthFullscreen' if full else 'width')
    height=r.get('heightFullscreen' if full else 'height')
    if any(isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) or x<320 for x in (width,height)):
        return None
    return int(width),int(height)

def fit(item,width,height,live=False):
    previous=item.get('resolutionV5')
    if previous==[width,height]:return
    s=min(width/2560,height/1440)
    fw,fh=(265,100) if live else (720,48)
    if previous and len(previous)==2 and min(previous)>0:
        ow,oh=previous
        old_s=min(ow/2560,oh/1440)
        scale=float(item.get('scale',old_s))*s/old_s
        # Preserve the right edge distance for the gameplay display.
        if live:
            gap=ow-float(item.get('left',0))-fw*float(item.get('scale',old_s))
            left=width-fw*scale-gap*width/ow
        else:left=float(item.get('left',0))*width/ow
        top=float(item.get('top',0))*height/oh
    else:
        scale=s;left=width-fw*s if live else width*675/2560
        top=height*(180 if live else 80)/1440
    scale=max(.1,min(scale,width/fw,height/fh))
    item.update(width=fw,height=fh,scale=scale,left=round(max(0,min(left,width-fw*scale))),
                top=round(max(0,min(top,height-fh*scale))),resolutionV5=[width,height])
