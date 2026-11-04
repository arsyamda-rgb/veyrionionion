from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
import numpy as np, math, os, random, glob
import glyphs as GL

S=4; W,H=176,222
P="pack_out"; TX=f"{P}/assets/veyrion/textures/font"
os.makedirs(TX,exist_ok=True)
CAPS="/usr/share/texmf/fonts/opentype/public/lm/lmromancaps10-regular.otf"
ITAL="/usr/share/texmf/fonts/opentype/public/lm/lmroman10-italic.otf"

# --- font asli (opsional): taruh file di folder fonts/ ---
def find_font(*pats):
    for p in pats:
        r=glob.glob(f"fonts/{p}")
        if r: return r[0]
FANTASY_TTF=find_font("FantasyAlphabet*.[to]tf","Fantasy*Alphabet*.[to]tf")
HARMESH_TTF=find_font("HarMesh*.[to]tf","Harmesh*.[to]tf")

SILVER=[(0,(255,255,255)),(.55,(206,208,216)),(1,(132,134,146))]
GOLD  =[(0,(255,240,184)),(.35,(236,196,92)),(.62,(190,138,44)),(.8,(236,200,100)),(1,(132,86,22))]
GOLDC=(226,182,78); SILC=(222,224,232); DIMC=(104,106,114)

def vgrad(w,h,stops,alpha=255):
    ys=np.linspace(0,1,h);out=np.zeros((h,w,4),np.uint8)
    for c in range(3):
        out[:,:,c]=np.interp(ys,[s[0] for s in stops],[s[1][c] for s in stops])[:,None]
    out[:,:,3]=alpha;return Image.fromarray(out,"RGBA")
def canvas(): return Image.new("RGBA",(W*S,H*S),(0,0,0,0))
def over(img,layer): img.alpha_composite(layer)
def blur(m,r): return m.filter(ImageFilter.GaussianBlur(r*S))

def fill_mask(img,mask,pos,stops=None,color=None,shadow=0.8,glow=None,outline=None):
    """tempel mask (L) di pos (px canvas) dengan gradient logam / warna polos, bayangan, glow."""
    full=Image.new("L",img.size,0);full.paste(mask,pos)
    if glow:
        gc,gr,ga=glow;g=Image.new("RGBA",img.size,gc+(0,));g.putalpha(blur(full,gr).point(lambda v:int(v*ga)));over(img,g)
    if shadow:
        sh=Image.new("RGBA",img.size,(0,0,0,0));sm=ImageChops.offset(full,int(0.6*S),int(1.2*S))
        sh.putalpha(blur(sm,0.9).point(lambda v:int(v*shadow)));over(img,sh)
    if outline:
        ol=full.filter(ImageFilter.MaxFilter(3));o=Image.new("RGBA",img.size,outline+(255,));o.putalpha(ol);over(img,o)
    bb=full.getbbox()
    if not bb: return
    if stops:
        f=Image.new("RGBA",img.size,(0,0,0,0));f.paste(vgrad(bb[2]-bb[0],bb[3]-bb[1],stops),(bb[0],bb[1]))
    else:
        f=Image.new("RGBA",img.size,color+(255,))
    f.putalpha(ImageChops.multiply(f.getchannel("A"),full));over(img,f)

def ttf_mask(text,path,size,sp=0.0,stroke=0.0):
    f=ImageFont.truetype(path,int(size*S));ws=[f.getlength(c) for c in text]
    tot=int(sum(ws)+sp*S*(len(text)-1)+4*S);hh=int(size*S*1.6)
    m=Image.new("L",(tot,hh),0);d=ImageDraw.Draw(m);x=2*S
    for c,w in zip(text,ws):
        d.text((x,hh//2),c,font=f,fill=255,anchor="lm",stroke_width=int(stroke*S),stroke_fill=255);x+=w+sp*S
    return m.crop(m.getbbox())
def fit(m,maxw):
    if m.width>maxw*S:
        k=maxw*S/m.width;m=m.resize((int(m.width*k),int(m.height*k)),Image.LANCZOS)
    return m
def put(img,m,cx,cy,**kw):
    fill_mask(img,m,(int(cx*S-m.width/2),int(cy*S-m.height/2)),**kw)

def fantasy(text,xh):
    if FANTASY_TTF:
        f=ImageFont.truetype(FANTASY_TTF,int(xh*1.45*S));m=Image.new("L",(int(len(text)*xh*2*S),int(xh*3*S)),0)
        ImageDraw.Draw(m).text((10,m.height//2),text,font=f,fill=255,anchor="lm");return m.crop(m.getbbox())
    m,_=GL.mask(text,int(xh*S),spacing=0.05);return m.crop(m.getbbox())
def roleplay_mask(size):
    if HARMESH_TTF: return ttf_mask("Roleplay",HARMESH_TTF,size*1.5,0.5)
    return ttf_mask("ROLEPLAY",CAPS,size,sp=4.4,stroke=0.28)   # stand-in sampai HarMesh.ttf tersedia

# ---------------- elemen dekor ----------------
def lozenge(d,cx,cy,r,fill,outline=None):
    d.polygon([(cx,cy-r),(cx+r,cy),(cx,cy+r),(cx-r,cy)],fill=fill,outline=outline)
def fade_line(img,x0,x1,y,color,w=0.6,fade=True):
    L=Image.new("RGBA",img.size,(0,0,0,0));d=ImageDraw.Draw(L)
    n=int((x1-x0)*S)
    for i in range(n):
        t=i/max(1,n-1);a=int(255*(1-abs(2*t-1)**1.6)) if fade else 255
        d.line([(x0*S+i,y*S),(x0*S+i,y*S)],fill=color+(a,),width=max(1,int(w*S)))
    over(img,L)
def divider(img,cx,y,half,col=GOLDC):
    fade_line(img,cx-half,cx-7,y,col,0.6);fade_line(img,cx+7,cx+half,y,col,0.6)
    d=ImageDraw.Draw(img)
    lozenge(d,cx*S,y*S,4.2*S,col+(255,),(255,244,200,255));lozenge(d,cx*S,y*S,1.7*S,(14,14,16,255))
    for s in(-1,1):
        lozenge(d,(cx+s*10)*S,y*S,1.5*S,col+(255,))
        d.arc([(cx+s*14)*S-3*S,(y-3.5)*S,(cx+s*14)*S+3*S,(y+3.5)*S],-90 if s>0 else 90,90 if s>0 else 270,fill=col+(255,),width=max(1,int(.6*S)))
def corner(img,x,y,sx,sy):
    d=ImageDraw.Draw(img);L=11
    d.line([(x*S,(y+sy*L)*S),(x*S,y*S),((x+sx*L)*S,y*S)],fill=SILC+(255,),width=int(1.2*S))
    d.line([((x+sx*2.4)*S,(y+sy*(L-3))*S),((x+sx*2.4)*S,(y+sy*2.4)*S),((x+sx*(L-3))*S,(y+sy*2.4)*S)],fill=GOLDC+(190,),width=int(.7*S))
    lozenge(d,(x+sx*2.4)*S,(y+sy*2.4)*S,2.1*S,GOLDC+(255,),(255,240,190,255))
    d.ellipse([(x+sx*L)*S-S,(y)*S-S,(x+sx*L)*S+S,(y)*S+S],fill=GOLDC+(255,))
    d.ellipse([(x)*S-S,(y+sy*L)*S-S,(x)*S+S,(y+sy*L)*S+S],fill=GOLDC+(255,))

def background(seed=3):
    """Layer panel (704x888) TRANSPARAN. Latar & frame ada di layar penuh (bg_full)."""
    return canvas()

# ---------------- latar FULL LAYAR ----------------
# Ukuran dalam "gui px" (1 px gambar = 1 gui px). 1920x1080 menutup layar 1080p walau GUI scale = 1.
BW,BH=1920,1080
CHEST_X,CHEST_Y=(BW-W)//2,(BH-H)//2      # pojok kiri-atas chest di dalam gambar latar
def bg_full(seed=7):
    yy,xx=np.mgrid[0:BH,0:BW].astype(np.float32)
    cx,cy=BW/2,BH/2
    r=np.sqrt((xx-cx)**2+((yy-cy)*1.15)**2)
    t=np.clip((yy-(cy-190))/700,0,1)
    base=np.zeros((BH,BW,3),np.float32)
    for c,(a,b) in enumerate(zip((34,34,40),(5,5,7))): base[:,:,c]=a+(b-a)*t
    # cahaya lembut di belakang logo + lantai
    glow=np.exp(-(((xx-cx)/260)**2+((yy-(CHEST_Y+34))/120)**2))*38+np.exp(-(((xx-cx)/380)**2+((yy-(cy+170))/110)**2))*14
    base+=glow[:,:,None]*np.array([1.0,1.0,1.1],np.float32)
    # vignette dari tengah: tepi layar makin gelap
    sm=np.clip((r-140)/760,0,1);sm=sm*sm*(3-2*sm)
    base*= (1-0.62*sm)[:,:,None]
    img=Image.fromarray(np.clip(base,0,255).astype(np.uint8),"RGB")
    d=ImageDraw.Draw(img,"RGBA")
    # lattice berlian tipis
    st=16
    for k in range(-BH,BW+BH,st):
        d.line([(k,0),(k+BH,BH)],fill=(255,255,255,5));d.line([(k,BH),(k+BH,0)],fill=(255,255,255,5))
    # cincin ornamen konsentris di sekitar panel (kelihatan di semua GUI scale)
    for rad,a in((150,26),(205,20),(275,16),(360,12),(470,9),(600,7)):
        d.ellipse([cx-rad,cy-rad*1.0,cx+rad,cy+rad*1.0],outline=GOLDC+(a,),width=1)
    for rad in(150,275,470):
        for ang in range(0,360,45):
            x=cx+rad*math.cos(math.radians(ang));y=cy+rad*math.sin(math.radians(ang))
            lozenge(d,x,y,2.4,GOLDC+(70,))
    # garis cahaya horizontal sampai tepi layar (sejajar divider panel)
    for yv,al in((CHEST_Y+68,70),(CHEST_Y+152,40)):
        for side in(-1,1):
            for i in range(0,int(BW/2-96)):
                x=cx+side*(96+i);a=int(al*(1-(i/(BW/2-96)))**1.3)
                if a>0: d.point((x,yv),fill=(236,222,176,a))
    # debu bintang
    rng=random.Random(seed)
    for _ in range(420):
        x=rng.randint(0,BW-1);y=rng.randint(0,BH-1);a=rng.randint(25,120);rr=rng.choice([0,0,0,0,1])
        if rr: d.ellipse([x-rr,y-rr,x+rr,y+rr],fill=(255,255,255,a//2))
        d.point((x,y),fill=(255,255,255,a))
    # grain halus
    n=np.random.default_rng(seed).normal(0,2.6,(BH,BW)).astype(np.int16)
    arr=np.array(img).astype(np.int16);arr=np.clip(arr+n[:,:,None],0,255)
    return Image.fromarray(arr.astype(np.uint8),"RGB")

def chamfer(x0,y0,x1,y1,c=2.6):
    return [((x0+c)*S,y0*S),((x1-c)*S,y0*S),(x1*S,(y0+c)*S),(x1*S,(y1-c)*S),((x1-c)*S,y1*S),((x0+c)*S,y1*S),(x0*S,(y1-c)*S),(x0*S,(y0+c)*S)]
def poly_mask(pts,size):
    m=Image.new("L",size,0);ImageDraw.Draw(m).polygon(pts,fill=255);return m
BLUE=[(0,(190,232,255)),(.45,(96,170,255)),(1,(36,104,238))]
BLUEC=(86,164,255)
RED=[(0,(255,214,206)),(.45,(255,98,84)),(1,(220,34,34))]
REDC=(255,84,72)
def button(img,x0,y0,x1,y1,label,primary=False,size=8.4,blue=False,red=False):
    pts=chamfer(x0,y0,x1,y1);m=poly_mask(pts,img.size)
    body=Image.new("RGBA",img.size,(0,0,0,0))
    g=vgrad(int((x1-x0)*S),int((y1-y0)*S),[(0,(40,96,200)),(1,(14,40,112))] if blue else [(0,(176,36,36)),(1,(76,10,12))] if red else [(0,(58,52,38)),(1,(22,19,12))] if primary else [(0,(44,44,50)),(1,(15,15,18))])
    body.paste(g,(int(x0*S),int(y0*S)));body.putalpha(ImageChops.multiply(body.getchannel("A"),m));over(img,body)
    d=ImageDraw.Draw(img)
    # border gradient
    bd=vgrad(img.width,img.height,BLUE if blue else RED if red else GOLD if primary else SILVER)
    bm=Image.new("L",img.size,0);ImageDraw.Draw(bm).line(pts+[pts[0]],fill=255,width=int(.9*S),joint="curve")
    bd.putalpha(bm);over(img,bd)
    ImageDraw.Draw(img).line([((x0+3.4)*S,(y0+1.5)*S),((x1-3.4)*S,(y0+1.5)*S)],fill=(255,255,255,48),width=int(.5*S))   # highlight kaca
    ImageDraw.Draw(img).line(chamfer(x0+2.2,y0+2.2,x1-2.2,y1-2.2,1.6)+[chamfer(x0+2.2,y0+2.2,x1-2.2,y1-2.2,1.6)[0]],fill=(255,255,255,22),width=int(.4*S))
    for sx in(x0+7.5,x1-7.5): lozenge(ImageDraw.Draw(img),sx*S,(y0+y1)/2*S,2.0*S,(BLUEC if blue else REDC if red else GOLDC if primary else (150,152,160))+(255,))
    lm=fit(ttf_mask(label,CAPS,size,sp=1.7),(x1-x0)-26)
    put(img,lm,(x0+x1)/2,(y0+y1)/2-0.2,stops=[(0,(255,255,255)),(1,(206,232,255))] if blue else [(0,(255,255,255)),(1,(255,214,208))] if red else SILVER if not primary else [(0,(255,255,255)),(1,(236,222,176))],shadow=.9,glow=(BLUEC,2.2,.55) if blue else (REDC,2.2,.55) if red else (GOLDC,2.2,.5) if primary else None)

def header(img,y_top=8):
    vm=fit(fantasy("Veyrion",31),132)
    put(img,vm,W/2,y_top+vm.height/S/2,stops=SILVER,glow=((255,255,255),3.2,.30),shadow=.9)
    rm=roleplay_mask(9.6);ry=y_top+vm.height/S+6.5
    put(img,rm,W/2,ry,stops=GOLD,glow=((236,176,60),2.4,.5),shadow=.9)
    return ry

def footer(img,text):
    fade_line(img,34,142,152,(255,255,255),.5)
    put(img,ttf_mask(text,ITAL,7,sp=.3),W/2,162,color=(120,122,130),shadow=.5)

LOGO_SRC=os.path.join(os.path.dirname(os.path.abspath(__file__)),"LOGO_VEYRION_NO_BG.png")
LOGO_H_VIS=64   # tinggi logo terlihat (gui px)
LOGO_X,LOGO_Y=180,2   # posisi logo terlihat relatif pojok kiri-atas chest (gui px)
LOGO_PAD=6      # ruang glow (gui px) tiap sisi
def make_logo():
    lg=Image.open(LOGO_SRC).convert("RGBA");lg=lg.crop(lg.getchannel("A").getbbox())
    k=LOGO_H_VIS*S/lg.height;lg=lg.resize((int(lg.width*k),int(lg.height*k)),Image.LANCZOS)
    p=LOGO_PAD*S;cv=Image.new("RGBA",(lg.width+2*p,lg.height+2*p),(0,0,0,0))
    g=Image.new("RGBA",cv.size,(190,210,255,0));al=Image.new("L",cv.size,0);al.paste(lg.getchannel("A"),(p,p))
    g.putalpha(blur(al,2.6).point(lambda v:int(v*.55)));cv.alpha_composite(g);cv.alpha_composite(lg,(p,p))
    cv.save(f"{TX}/logo.png",optimize=True);return cv.size
def make_cursor():
    K=8;T=64;cv=Image.new("RGBA",(T*K,T*K),(0,0,0,0));d=ImageDraw.Draw(cv)
    pts=[(0,0),(0,23),(5.6,18.2),(9.6,27.2),(13.4,25.6),(9.4,16.8),(16.6,16.4)]
    PP=lambda dx=0,dy=0:[((32+x+dx)*K,(32+y+dy)*K) for x,y in pts]
    d.polygon([((32+x+.9)*K,(32+y+1.2)*K) for x,y in pts],fill=(0,0,0,90))          # bayangan
    d.polygon(PP(),fill=(10,10,14,255),outline=(10,10,14,255),width=int(1.6*K))        # outline gelap
    ins=Image.new("L",cv.size,0);ImageDraw.Draw(ins).polygon(PP(),fill=255)
    ins=ins.filter(ImageFilter.MinFilter(int(2.0*K)//2*2+1))
    fill=vgrad(cv.width,cv.height,[(0,(255,255,255)),(1,(214,218,230))]);fill.putalpha(ins);cv.alpha_composite(fill)
    cv=cv.resize((T,T),Image.LANCZOS);cv.save(f"{P}/assets/veyrion/textures/item/cursor.png",optimize=True)
    return cv.getchannel("A").getbbox()
def save(img,name): img.save(f"{TX}/{name}.png",optimize=True)

# ---------------- emblem ----------------
def rot(pts,a): c,s=math.cos(a),math.sin(a);return [(x*c-y*s,x*s+y*c) for x,y in pts]
def emblem(img,kind,cx,cy,k,col,glow=None):
    L=Image.new("RGBA",img.size,(0,0,0,0));d=ImageDraw.Draw(L);w=max(1,int(.95*max(1,k/9)*S))
    T=lambda pts:[((cx+x*k)*S,(cy+y*k)*S) for x,y in pts]
    ln=lambda pts,ww=w,c=False:d.line(T(pts)+([T(pts)[0]] if c else []),fill=col+(255,),width=ww,joint="curve")
    if kind==0:
        R=[];Lf=[]
        for i in range(31):
            t=i/30;y=-1+2*t;hw=.52*math.sin(math.pi*t)**.85;R.append((hw,y));Lf.append((-hw,y))
        a=math.radians(22);ln(rot(R+Lf[::-1],a),c=True);ln(rot([(0,.95),(0,-.7)],a),int(w*.8))
        for yy in(.45,.05,-.35):
            for sg in(-1,1): ln(rot([(0,yy),(sg*.3,yy-.22)],a),int(w*.6))
    elif kind==1:
        for off,hh,sh in((-.55,.9,.18),(0,1.0,.2),(.55,.85,.18)):
            d.polygon(T([(off-.13,-hh),(off+.13,-hh),(off+sh+.02,hh)]),fill=col+(255,))
    elif kind==2:
        ln([(0,-1),(.12,-.8),(.12,.3),(-.12,.3),(-.12,-.8)],c=True);ln([(0,-.75),(0,.25)],int(w*.6))
        ln([(-.5,.3),(.5,.3),(.5,.42),(-.5,.42)],c=True);ln([(-.05,.42),(.05,.42),(.05,.8),(-.05,.8)],c=True)
        d.ellipse([(cx-.11*k)*S,(cy+.82*k)*S,(cx+.11*k)*S,(cy+1.04*k)*S],outline=col+(255,),width=w)
    else:
        ln([(-.55,.75),(-.2,-.6),(.9,-.95),(.62,-.3),(.7,.2),(.3,.05),(.18,.62)])
        for e in((.62,-.3),(.3,.05)): ln([(-.2,-.6),e],int(w*.7))
        ln([(-.55,.75),(-.2,-.6)],int(w*1.4))
    if glow:
        g=L.copy();g.putalpha(blur(L.getchannel("A"),glow[0]).point(lambda v:int(v*glow[1])));g=Image.composite(Image.new("RGBA",img.size,col+(255,)),g,g.getchannel("A"));over(img,g)
    over(img,L)

RACES=["ELF","BEAST","HUMAN","DRAGON"];NAMES=["Elf","Beast","Human","Dragon"]
ICON=["KEANGGUNAN DAN PANAHMU","TARING DAN CAKARMU","KEBERANIANMU","SAYAPMU"]

# ---------------- layar ----------------
def main_menu():
    img=background(1);ry=header(img);divider(img,W/2,ry+9.5,52)
    button(img,26,73,150,89,"TENTUKAN RAS",True);button(img,26,91,150,107,"KELUAR",red=True);button(img,26,109,150,125,"DISCORD",blue=True)
    footer(img,"Setiap kisah dimulai dari satu pilihan.");save(img,"main")

def gacha(lit=None,win=False,status="Memutar takdir..."):
    img=background(2)
    tm=fit(fantasy("Tentukan Ras",21),140);put(img,tm,W/2,30,stops=SILVER,glow=((255,255,255),3,.28))
    divider(img,W/2,49,46)
    put(img,ttf_mask("TAKDIR AKAN MEMILIHMU",CAPS,6.6,sp=2.1),W/2,58,color=(142,144,152),shadow=.5)
    for i in range(4):
        x=8+i*41;on=(lit==i);pts=chamfer(x,76,x+36,132,3)
        accent=GOLDC if (on and win) else (236,238,246)
        if on:
            gl=Image.new("RGBA",img.size,accent+(0,));gl.putalpha(blur(poly_mask(pts,img.size),5).point(lambda v:int(v*(.55 if win else .38))));over(img,gl)
        card=Image.new("RGBA",img.size,(0,0,0,0))
        top,bot=((70,58,28),(26,20,9)) if (on and win) else ((60,60,68),(24,24,28)) if on else ((26,26,30),(11,11,13))
        card.paste(vgrad(36*S,56*S,[(0,top),(1,bot)]),(x*S,76*S));card.putalpha(ImageChops.multiply(card.getchannel("A"),poly_mask(pts,img.size)));over(img,card)
        bm=Image.new("L",img.size,0);ImageDraw.Draw(bm).line(pts+[pts[0]],fill=255,width=int((1.3 if on else .6)*S),joint="curve")
        bdr=vgrad(img.width,img.height,GOLD if (on and win) else SILVER if on else [(0,(88,90,98)),(1,(48,49,54))]);bdr.putalpha(bm);over(img,bdr)
        ecol=(244,206,98) if (on and win) else (250,250,255) if on else (112,114,122)
        emblem(img,i,x+18,96,14,ecol,glow=(1.6,.9) if on else None)
        nm=fit(ttf_mask(RACES[i],CAPS,6.8,sp=.7),31);put(img,nm,x+18,121,color=ecol,shadow=.6)
    sm=ttf_mask(status,ITAL,8,sp=.3);put(img,sm,W/2,150,color=GOLDC if win else (150,152,160),shadow=.6,glow=(GOLDC,2,.4) if win else None)
    return img

def result(i):
    img=background(10+i)
    put(img,ttf_mask("SELAMAT KAMU MENJADI RAS",CAPS,7.6,sp=1.5).resize((1,1)) if False else fit(ttf_mask("SELAMAT KAMU MENJADI RAS",CAPS,7.6,sp=1.5),146),W/2,19,color=(150,152,160),shadow=.6)
    nm=fit(fantasy(NAMES[i],24),120);put(img,nm,W/2,41,stops=SILVER,glow=((255,255,255),3,.3))
    # halo emas di belakang emblem
    hl=Image.new("L",img.size,0);ImageDraw.Draw(hl).ellipse([(W/2-20)*S,(76-20)*S,(W/2+20)*S,(76+20)*S],fill=255)
    g=Image.new("RGBA",img.size,GOLDC+(0,));g.putalpha(blur(hl,7).point(lambda v:int(v*.5)));over(img,g)
    d=ImageDraw.Draw(img)
    for r,a in((15,120),(19,70),(23,36)): d.ellipse([(W/2-r)*S,(76-r)*S,(W/2+r)*S,(76+r)*S],outline=GOLDC+(a,),width=int(.5*S))
    emblem(img,i,W/2,76,11,(244,206,98),glow=(2,1.0))
    line="AYO TUNJUKKAN "+ICON[i]
    put(img,fit(ttf_mask(line,CAPS,7.4,sp=1.1),150),W/2,95,stops=GOLD,glow=((236,176,60),2,.35))
    put(img,ttf_mask("DI DUNIA VEYRION",CAPS,7.4,sp=1.6),W/2,103.5,stops=GOLD,glow=((236,176,60),2,.35))
    button(img,62,109,116,125,"MASUK",True,8)
    footer(img,"Veyrion  ·  Roleplay");save(img,f"result_{i}")

if __name__=="__main__":
    bg_full().save(f"{TX}/bg.png",optimize=True);print("logo",make_logo());os.makedirs(f"{P}/assets/veyrion/textures/item",exist_ok=True);print("cursor bbox",make_cursor())
    main_menu();save(gacha(),"gacha_idle")
    for i in range(4):
        save(gacha(i),f"gacha_spin_{i}");save(gacha(i,True,"Takdir telah berbicara."),f"gacha_win_{i}")
        result(i)
    bg=bg_full()
    def screen(n,scale,sw=1920,sh=1080):
        gw,gh=sw//scale,sh//scale
        panel=Image.open(f"{TX}/{n}.png").resize((W,H),Image.LANCZOS)
        full=bg.copy();full.paste(panel,(CHEST_X,CHEST_Y),panel)
        if True:
            lg=Image.open(f"{TX}/logo.png");lg=lg.resize((lg.width//S,lg.height//S),Image.LANCZOS);full.paste(lg,(CHEST_X+LOGO_X-LOGO_PAD,CHEST_Y+LOGO_Y-LOGO_PAD),lg)
        x0=(BW-gw)//2;y0=(BH-gh)//2
        return full.crop((x0,y0,x0+gw,y0+gh)).resize((sw//2,sh//2),Image.NEAREST if scale>=2 else Image.LANCZOS)
    for n in["main","gacha_win_3","result_0"]:
        screen(n,4).save(f"preview_{n}_scale4.png")
    screen("main",2).save("preview_main_scale2.png")
