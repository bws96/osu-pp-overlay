"""Read-only parser for osu!stable scores.db and embedded replay headers."""
import struct
from pathlib import Path

class Reader:
    def __init__(self,data):self.data=data;self.pos=0
    def take(self,n):
        if n<0 or self.pos+n>len(self.data):raise ValueError('Truncated scores.db')
        value=self.data[self.pos:self.pos+n];self.pos+=n;return value
    def number(self,fmt):return struct.unpack('<'+fmt,self.take(struct.calcsize('<'+fmt)))[0]
    def string(self):
        tag=self.number('B')
        if tag==0:return ''
        if tag!=11:raise ValueError('Invalid osu string')
        length=0
        for shift in range(0,35,7):
            b=self.number('B');length|=(b&127)<<shift
            if b<128:break
        else:raise ValueError('Invalid string length')
        return self.take(length).decode('utf-8')

def parse_scores(data):
    r=Reader(data);version=r.number('i');maps=r.number('i')
    if not 0<=maps<=2_000_000:raise ValueError('Invalid map count')
    result={};total=0
    for _ in range(maps):
        checksum=r.string();count=r.number('i')
        if not 0<=count<=1_000_000:raise ValueError('Invalid score count')
        rows=[]
        for _ in range(count):
            mode=r.number('B');build=r.number('i');beatmap=r.string();name=r.string();replay=r.string()
            great,ok,meh,geki,katu,miss=struct.unpack('<6H',r.take(12))
            score=r.number('i');combo=r.number('H');perfect=r.number('B');mods=r.number('i')
            r.string();ticks=r.number('q');length=r.number('i')
            if length>0:r.take(length)
            score_id=r.number('q') if build>=20140721 else r.number('i')
            if mods & (1<<23):r.number('d')
            rows.append(dict(mode=mode,name=name,checksum=beatmap or checksum,great=great,ok=ok,meh=meh,
                perfects=geki,goods=katu,miss=miss,score=score,combo=combo,mods=mods,score_id=score_id,ticks=ticks))
            total+=1
        result[checksum]=rows
    if r.pos!=len(data):raise ValueError(f'Unexpected trailing bytes: {len(data)-r.pos}')
    return result

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description='Read an osu!stable scores.db without changing it')
    parser.add_argument('scores_db',type=Path)
    args=parser.parse_args()
    index=parse_scores(args.scores_db.read_bytes())
    print('maps',len(index),'scores',sum(map(len,index.values())))
