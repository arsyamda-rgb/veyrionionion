"""Ekstrak glyph 'Fantasy Alphabet' dari gambar specimen -> mask huruf yang bisa dipakai menyusun teks apa saja."""
from PIL import Image, ImageFilter, ImageDraw
import numpy as np, string

import os
SRC=os.path.join(os.path.dirname(os.path.abspath(__file__)),"fantasy_alphabet_specimen.jpg")
ROWS=[(542,587,"ABCDEFGHI"),(602,652,"JKLMNOPQR"),(661,712,"STUVWXYZ"),
      (722,772,"abcdefghijklm"),(792,832,"nopqrstuvwxyz"),(844,886,"1234567890")]
THR=185

def _segments(dark,n,split_idx=None):
    prof=dark.sum(axis=0).astype(int)
    runs=[];s=None
    for x,v in enumerate(prof):
        if v>0 and s is None: s=x
        if v==0 and s is not None: runs.append([s,x]);s=None
    if s is not None: runs.append([s,len(prof)])
    # serpihan sempit (ekor swash) digabung ke huruf di kirinya
    merged=[]
    for r in runs:
        if r[1]-r[0]<=10 and merged: merged[-1][1]=r[1]
        elif r[1]-r[0]>2: merged.append(r)
    runs=merged
    if split_idx is not None and len(runs)<n:
        a,b=runs[split_idx];lo,hi=a+(b-a)//4,b-(b-a)//4
        cut=lo+int(np.argmin(prof[lo:hi]));runs[split_idx:split_idx+1]=[[a,cut],[cut,b]]
    while len(runs)<n:
        i=max(range(len(runs)),key=lambda k:runs[k][1]-runs[k][0]); a,b=runs[i]
        lo,hi=a+(b-a)//4,b-(b-a)//4
        cut=lo+int(np.argmin(prof[lo:hi]));runs[i:i+1]=[[a,cut],[cut,b]]
    while len(runs)>n:
        i=min(range(len(runs)),key=lambda k:runs[k][1]-runs[k][0])
        j=i-1 if i>0 else i+1;a=min(runs[i][0],runs[j][0]);b=max(runs[i][1],runs[j][1])
        runs[min(i,j):max(i,j)+1]=[[a,b]]
    return runs

def _clean(cov):
    """Buang serpihan milik huruf tetangga; pertahankan titik i/j dan bagian yang masih menyambung."""
    from scipy import ndimage
    m=cov>0.25
    lab,n=ndimage.label(m,structure=np.ones((3,3)))
    if n<=1: return cov
    areas=ndimage.sum(m,lab,range(1,n+1));big=int(np.argmax(areas))+1
    ys,xs=np.where(lab==big);bx0,bx1=xs.min(),xs.max()
    keep=np.zeros_like(m)
    for i in range(1,n+1):
        yy,xx=np.where(lab==i);cx=xx.mean()
        if i==big or (areas[i-1]>=0.10*areas[big-1] and bx0-2<=cx<=bx1+2) or (bx0<=cx<=bx1 and areas[i-1]>=6):
            keep|=(lab==i)
    keep=ndimage.binary_dilation(keep,iterations=2)
    return cov*keep

def load():
    im=Image.open(SRC).convert("L");a=np.array(im).astype(float)
    G={}
    for y0,y1,chars in ROWS:
        band=a[y0-6:y1+6]
        dark=band<THR
        segs=_segments(dark,len(chars),split_idx=8 if chars.startswith('abc') else None)
        boxes=[]
        for (x0,x1),ch in zip(segs,chars):
            sub=dark[:,x0:x1];ys=np.where(sub.any(axis=1))[0]
            top,bot=ys.min(),ys.max()+1
            boxes.append((ch,x0,x1,top,bot))
        # baseline = median bottom dari huruf yang tidak turun (ambil kuartil bawah-tengah)
        bots=sorted(b[4] for b in boxes);base=bots[len(bots)//2]
        for ch,x0,x1,top,bot in boxes:
            pad=3
            sub=a[max(0,y0-6+top-pad):y0-6+bot+pad, x0:x1]
            cov=np.clip((228-sub)/(228-80),0,1)
            cov=_clean(cov)
            ys=np.where(cov.max(axis=1)>0.15)[0]
            if len(ys)==0: continue
            t2,b2=ys.min(),ys.max()+1
            off=max(0,y0-6+top-pad)-(y0-6)
            G[ch]=dict(a=cov[t2:b2],top=off+t2-base,bot=off+b2-base,w=x1-x0)
    return G

_G=None
def glyphs():
    global _G
    if _G is None: _G=load()
    return _G

def mask(text,xh,spacing=0.06,size=(1,1)):
    """Render teks -> L mask. xh = tinggi huruf besar (px output). Mengembalikan (img, baseline_y_dalam_img)."""
    G=glyphs();capsrc=float(-np.median([G[c]["top"] for c in "EHIT" if c in G]))  # tinggi cap sumber
    k=float(xh/capsrc)
    pieces=[];x=0;miny=0;maxy=0
    for ch in text:
        if ch==" ": x+=int(0.35*xh);continue
        g=G.get(ch)
        if g is None: continue
        im=Image.fromarray((g["a"]*255).astype("uint8"),"L")
        w=max(1,int(im.width*k));h=max(1,int(im.height*k))
        im=im.resize((w,h),Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.6*k/2))
        im=im.point(lambda v:255 if v>150 else (0 if v<70 else int((v-70)/80*255)))
        y=int(g["top"]*k)
        pieces.append((im,x,y));miny=min(miny,y);maxy=max(maxy,y+h);x+=w+int(spacing*xh)
    W=x;H=maxy-miny
    out=Image.new("L",(W,H),0)
    for im,px,py in pieces:
        out.paste(ImageChopsLighter(out.crop((px,py-miny,px+im.width,py-miny+im.height)),im),(px,py-miny))
    return out,-miny
def ImageChopsLighter(a,b):
    from PIL import ImageChops
    return ImageChops.lighter(a,b)

if __name__=="__main__":
    G=glyphs()
    print({c:(g["a"].shape,g["top"],g["bot"]) for c,g in list(G.items())[:6]})
    sheet=Image.new("L",(1400,400),20);y=10
    for t in ["Veyrion","Tentukan Ras","Elf Beast Human Dragon"]:
        m,b=mask(t,90);sheet.paste(255,(10,y),m);y+=m.height+20
    sheet.save("glyph_test.png")
