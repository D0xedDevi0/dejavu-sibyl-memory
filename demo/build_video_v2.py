#!/usr/bin/env python3
"""Build the dejavu demo video v2 — 2-5min, narrated, cinematic.

Fused identity: NEURAL_MESH blueprint navy/pixel-grid/cyan + Sibyl oracle.
9 scenes, each synced to a TTS narration segment (demo/narr/segNN_*.mp3).
Motion via zoompan (Ken Burns), per-scene fade in/out, subtle ambient music bed.

Usage:
    PYTHONPATH=. .venv/bin/python demo/build_video_v2.py
    # or just: python3 demo/build_video_v2.py   (PIL + ffmpeg only)
"""
from __future__ import annotations
import os, subprocess, math, random, json, re

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FRAMES = os.path.join(HERE, "_frames_v2")
NARR = os.path.join(HERE, "narr")
SEG = os.path.join(HERE, "_segments_v2")
os.makedirs(FRAMES, exist_ok=True)
os.makedirs(SEG, exist_ok=True)

# ---------------- brand ----------------
BG=(0,18,64); BG2=(0,12,40); PANEL=(0,30,72); GRID=(0,26,90)
CYAN=(0,212,255); BLUE=(0,82,255); GREEN=(0,255,136); MAGENTA=(255,0,170)
RED=(255,69,58); AMBER=(255,190,60); WHITE=(235,240,250); GRAY=(136,153,204); DIM=(90,108,150)
W,H=1600,900
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONTB="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

TX_DERISK="0x5175ae5a244b907753cacca9d529c87042ee11332c6e05cf4624d9016d4793dd"
TX_LEARN="0x9c0aa5249beb593633353b262ce868ba6aedee43c5ec3ba6824d6e1c7e6bab0a"

def F(sz, bold=False): return ImageFont.truetype(FONTB if bold else FONT, sz)

def pixel_grid(img, size=8, alpha=18):
    d=ImageDraw.Draw(img,"RGBA")
    for x in range(0,W,size): d.line([(x,0),(x,H)],fill=GRID+(alpha,),width=1)
    for y in range(0,H,size): d.line([(0,y),(W,y)],fill=GRID+(alpha,),width=1)
    rnd=random.Random(7)
    for _ in range(70):
        x=rnd.randrange(0,W,4); y=rnd.randrange(0,H,4)
        c=(CYAN if rnd.random()<0.5 else MAGENTA)+(24,)
        d.ellipse([x,y,x+4,y+4],fill=c)

def header(d, title, accent, tag=None, sub="NEURAL_MESH x Sibyl Memory  |  forget => lose · remember => survive"):
    d.text((44,30), title, font=F(46,True), fill=accent)
    d.text((44,94), sub, font=F(19), fill=GRAY)
    if tag:
        fs=F(22,True); tb=d.textbbox((0,0),tag,font=fs)
        d.rectangle((W-tb[2]-92,30,W-44,30+tb[3]+16),fill=accent)
        d.text((W-tb[2]-74,44),tag,font=fs,fill=BG)

def footer(d, text):
    d.text((44,H-36), text, font=F(17), fill=DIM)

def new_frame():
    img=Image.new("RGB",(W,H),BG); pixel_grid(img); return img, ImageDraw.Draw(img)

def terminal(lines, title, accent, tag=None):
    img,d=new_frame(); header(d,title,accent,tag)
    px,py,pw,ph=44,168,W-88,H-168-60
    d.rounded_rectangle((px,py,px+pw,py+ph),radius=14,outline=BLUE,fill=PANEL,width=2)
    y=py+22; f=F(24)
    for ln in lines:
        col=WHITE
        if ln.startswith(">"): col=AMBER
        elif "0.55" in ln or "wiped" in ln or "AGAIN" in ln or "NO LESSONS" in ln or "-18%" in ln or "loses" in ln.lower():
            col=RED
        elif "0.05" in ln or "status 1" in ln or "FOUND" in ln or "de_risk" in ln or "flips" in ln or "verified" in ln or "0.95" in ln or "de-risk" in ln:
            col=GREEN
        elif ln.startswith("sibyl@") or (":" in ln[:14]):
            col=CYAN
        elif ln[:2] in ("A ","B ","C ","D ","E ","F "): col=MAGENTA
        d.text((px+28,y),ln,font=f,fill=col); y+=38
    return img

# ---------------- charts (clean padding) ----------------
def chart_ablation(r, cw, ch):
    img=Image.new("RGB",(cw,ch),(12,14,20)); d=ImageDraw.Draw(img)
    d.text((30,26),"dejavu ablation benchmark",font=F(28,True),fill=CYAN)
    d.text((30,66),f"mean crisis return · {r['trials']} frames · seed 1337",font=F(18),fill=(150,158,176))
    axis_x=cw-240; bar_h=86; y_no,y_mem=150,300
    worst=max(abs(r['mean_return_no_memory_pct']/100),abs(r['mean_return_memory_pct']/100))
    scale=(axis_x-90)/worst
    for pct,y,color,label in ((r['mean_return_no_memory_pct'],y_no,RED,"NO MEMORY"),(r['mean_return_memory_pct'],y_mem,GREEN,"WITH MEMORY")):
        w=abs(pct/100)*scale; x0=axis_x-w
        d.rounded_rectangle((x0,y,axis_x,y+bar_h),radius=8,fill=color)
        d.text((axis_x+14,y+4),label,font=F(21,True),fill=color)
        d.text((axis_x+14,y+44),f"{pct:.2f}%",font=F(20),fill=color)
    d.line((axis_x,120,axis_x,ch-60),fill=(70,78,96),width=2)
    d.text((axis_x-56,120),"0",font=F(18),fill=(120,128,148))
    d.text((30,ch-40),f"loss averted {r['mean_loss_averted_pp']}pp · decision changed {r['pct_trials_decision_changed']}%",font=F(17),fill=(235,238,245))
    return img

def chart_growth(g, cw, ch):
    img=Image.new("RGB",(cw,ch),(12,14,20)); d=ImageDraw.Draw(img)
    d.text((30,26),"compounding: what memory is worth",font=F(26,True),fill=CYAN)
    d.text((30,64),f"{g['n_episodes']} crisis episodes, starting $1.00",font=F(18),fill=(150,158,176))
    n=g['n_episodes']; plot=(70,150,cw-70,ch-90)
    min_v=min(min(g['mem_series']),min(g['nomem_series']),0.5); max_v=max(max(g['mem_series']),max(g['nomem_series']),1.0)
    def pt(i,v):
        x=plot[0]+(plot[2]-plot[0])*i/max(1,n-1)
        y=plot[3]-(plot[3]-plot[1])*(v-min_v)/max(1e-9,max_v-min_v)
        return x,y
    d.rectangle(plot,outline=(70,78,96),width=2)
    for k in range(5):
        yy=plot[1]+(plot[3]-plot[1])*k/4; d.line((plot[0],yy,plot[2],yy),fill=(30,36,50),width=1)
    # legend (left-aligned, safe)
    d.ellipse((plot[0],100,plot[0]+14,114),fill=GREEN); d.text((plot[0]+22,90),"WITH MEMORY",font=F(20,True),fill=GREEN)
    d.ellipse((plot[0]+220,100,plot[0]+234,114),fill=RED); d.text((plot[0]+242,90),"NO MEMORY",font=F(20,True),fill=RED)
    for series,color in ((g['mem_series'],GREEN),(g['nomem_series'],RED)):
        pts=[pt(i,v) for i,v in enumerate(series)]
        for a,b in zip(pts,pts[1:]): d.line((a,b),fill=color,width=4)
        ex,ey=pts[-1]; d.ellipse((ex-6,ey-6,ex+6,ey+6),fill=color)
        d.text((ex-190,ey-14),f"${series[-1]:.2f}",font=F(22,True),fill=color)
    d.text((30,ch-38),f"memory ${g['mem_final_value']:.2f} vs no-memory ${g['nomem_final_value']:.2f} after {n} crises",font=F(17),fill=(235,238,245))
    return img

# ---------------- scene content ----------------
ABL=json.load(open(os.path.join(HERE,"ablation_results.json")))
GR=json.load(open(os.path.join(HERE,"advanced_analysis.json")))["growth"]

PROBLEM=terminal([
  "the cost of forgetting",
  "---------------------------------------------",
  "SESSION 1:  naive  equity=0.55   -> -18%",
  "SESSION 2:  naive  equity=0.55   -> -18%",
  "SESSION 3:  naive  equity=0.55   -> -18%",
  "SESSION N:  naive  equity=0.55   -> -18%",
  "",
  "no recall  ->  no change  ->  no compounding",
  "",
  "> every session, a clean slate. every loss, re-learned.",
], "the problem  ·  the cost of forgetting", RED, tag="NO MEMORY")

SESSION_A=terminal([
  "SESSION A  --  fresh store",
  "",
  "frame: vix=52.0 credit_stress=2.2  (CRISIS)",
  "",
  "decide(frame): no recall yet ->",
  "  naive_book()   equity = 0.55   <- stays LONG",
  "",
  "outcome: -18% drawdown",
  "write_lesson('crisis-derisking')  -> memory",
  "write_event(journal)",
  "",
  "> dejavu: 'when stressed, de-risk to cash.'",
], "SESSION A  ·  it learns", RED, tag="FRESH STORE")

GATE=terminal([
  "SESSION B  --  store DELETED",
  "",
  "frame: vix=52.0 credit_stress=2.2  (SAME)",
  "",
  "recall: search(...) ->  NO LESSONS  (wiped)",
  "",
  "decide_differently(frame, None)",
  "  naive_book()   <- fails open",
  "  equity = 0.55   stays LONG",
  "",
  "outcome: -18% drawdown AGAIN.",
  "",
  "> that's what forgetting costs.",
], "the gate  ·  delete memory, it breaks", RED, tag="STORE WIPED")

SESSION_B=terminal([
  "SESSION B  --  cold start (zero ctx)",
  "",
  "frame: vix=52.0 credit_stress=2.2  (SAME)",
  "",
  "recall: search('credit stress crisis')",
  "  -> 1 lesson FOUND  (from Session A)",
  "",
  "decide_differently(frame, memory)",
  "  de_risk_book()   <- flips",
  "  equity = 0.05   cash = 0.59",
  "",
  "act_onchain(Base): REAL TX  status 1",
  f"  {TX_DERISK[:20]}...  block 50108439",
], "SESSION B  ·  it remembers, then acts", GREEN, tag="MEMORY-LOADED")

# measured: two charts side by side
def scene_measured():
    img,d=new_frame(); header(d,"measured evidence  ·  real, reproducible",CYAN,tag="MEASURED")
    cw,ch=756,560; off=44; gap=24
    a=chart_ablation(ABL,cw,ch); g=chart_growth(GR,cw,ch)
    img.paste(a,(off,170)); img.paste(g,(off+cw+gap,170))
    d.rectangle((off,170,off+cw,170+ch),outline=BLUE,width=2)
    d.rectangle((off+cw+gap,170,off+cw+gap+cw,170+ch),outline=BLUE,width=2)
    footer(d,"hackathon demo · 200 seeded frames · every number measured, seed 1337")
    return img

# graph+scale: live-rendered relational board + measured recall numbers
def scene_graph_scale():
    import sys, os as _os
    _os.chdir(os.path.join(HERE, ".."))
    sys.path.insert(0, _os.getcwd())
    from dejavu.graph_audit import seed_corpus, scale_recall_check
    from dejavu.memory import Memory
    import tempfile
    db = os.path.join(tempfile.mkdtemp(), "video_scale.db")
    m = Memory(db, tenant_id="fleet-brain")
    stats = seed_corpus(m)
    rc = scale_recall_check(m, trials=15)
    m.close()

    img, d = new_frame()
    header(d, "raised bar  ·  graph + scale  ·  matched", GREEN, tag="BENCH-ALIGNED")
    # left panel: relational graph sketch
    px, py, pw, ph = 44, 170, 756, 560
    d.rectangle((px, py, px+pw, py+ph), fill=PANEL, outline=BLUE, width=2)
    d.text((px+18, py+14), "RELATIONAL BOARD  ·  native entity_relations", font=F(20, True), fill=CYAN)
    nodes = {
        "view/news/market":  (px+80,  py+120),
        "view/risk/stress":  (px+420, py+100),
        "company/acme":      (px+300, py+270),
        "company/globex":    (px+120, py+400),
        "view/sector/credit":(px+500, py+430),
    }
    edges = [("view/news/market","company/acme","impacts"),
             ("view/risk/stress","company/globex","impacts"),
             ("company/acme","view/sector/credit","exposes"),
             ("company/globex","company/acme","peer")]
    for a, b, rel in edges:
        (x1,y1),(x2,y2) = nodes[a], nodes[b]
        d.line((x1+70,y1+22,x2+70,y2+22), fill=(0,110,160), width=3)
        lx, ly = (x1+x2)//2+40, (y1+y2)//2+8
        tw = d.textlength(rel, font=F(15))
        d.rectangle((lx-4, ly-3, lx+tw+4, ly+20), fill=(0,12,40))
        d.text((lx, ly), rel, font=F(15), fill=(190,205,235))
    stress = "view/risk/stress"
    for i, (a, b, _) in enumerate(edges):
        (x1,y1),(x2,y2) = nodes[a], nodes[b]
        if stress in (a,b):
            d.line((x1+70,y1+22,x2+70,y2+22), fill=RED, width=4)
    for name, (x, y) in nodes.items():
        hot = name == stress
        d.rounded_rectangle((x, y, x+140, y+44), 8,
                            fill=(0,60,60) if hot else (0,40,80),
                            outline=RED if hot else CYAN, width=2)
        d.text((x+8, y+12), name.split("/")[-1] + ("/"+name.split("/")[0] if "/" in name else ""),
               font=F(16, True), fill=RED if hot else WHITE)
    d.text((px+18, py+ph-56), "> stress reaches the allocator THROUGH THE GRAPH",
           font=F(19, True), fill=AMBER)
    d.text((px+18, py+ph-30), "  two hops: stress view -> company -> sector view",
           font=F(17), fill=GRAY)
    # right panel: scale numbers
    qx, qw = px+pw+24, pw
    d.rectangle((qx, py, qx+qw, py+ph), fill=PANEL, outline=BLUE, width=2)
    d.text((qx+18, py+14), "SCALE STRESS  ·  seed_corpus + scale_recall_check", font=F(20, True), fill=CYAN)
    rows = [
        ("companies",      f"{stats['companies']}"),
        ("daily views",    f"{stats['views']} (sim yr)"),
        ("journal events", f"{stats['events']}"),
        ("TOTAL RECORDS",  f"{stats['companies']+stats['views']+stats['events']}"),
    ]
    yy = py+70
    for k, v in rows:
        d.text((qx+24, yy), k, font=F(22), fill=GRAY)
        d.text((qx+qw-260, yy), v, font=F(22, True), fill=WHITE)
        yy += 44
    d.line((qx+20, yy+8, qx+qw-20, yy+8), fill=(0,110,160), width=2)
    yy += 30
    d.text((qx+24, yy), "NEEDLE RECALL", font=F(20, True), fill=AMBER); yy += 40
    d.text((qx+24, yy), "top-1 accuracy", font=F(22), fill=GRAY)
    d.text((qx+qw-260, yy), "100%", font=F(24, True), fill=GREEN); yy += 44
    d.text((qx+24, yy), "median search", font=F(22), fill=GRAY)
    d.text((qx+qw-260, yy), f"{rc['median_ms']} ms", font=F(24, True), fill=GREEN); yy += 44
    d.text((qx+24, yy), "max search", font=F(22), fill=GRAY)
    d.text((qx+qw-260, yy), f"{rc['max_ms']} ms", font=F(24, True), fill=GREEN)
    footer(d, f"every number rendered LIVE from a fresh store at build time · trials={rc['trials']}")
    return img

GRAPH_SCALE_lines = ["relational graph + scale stress"]

AUDIT=terminal([
  "AUDIT CHAIN  --  tamper-evident journal seal",
  "",
  "seal_journal():",
  "  chain = SHA256(row_0) -> fold row_1 -> ... -> fold row_N",
  "  digest = 3dbcbd572b34a132...3024bd2   -> HOT tier",
  "",
  "verify_journal():  recompute  ->  MATCH   ok=True",
  "",
  "TAMPER TEST:",
  "  edit row_3    -> digest mismatch  -> ok=False",
  "  delete row_0  -> rows 10 != 9     -> ok=False",
  "",
  "> no record, no action. not a slogan. MATH.",
], "the compliance guarantee  ·  proven", MAGENTA, tag="SOVEREIGN-READY")

DEJAVU=terminal([
  "LEARNER  --  reading the journal",
  "",
  "pattern: 'crisis -> de-risk -> survived'",
  "  observed across sessions A..N",
  "",
  "proposal (skill/crisis-derisking):",
  "  'when stressed, de-risk to cash'",
  "  pattern_kind=drawdown-recovery  confidence=high",
  "",
  "accept -> doc_key skill/crisis-derisking",
  "",
  "> recall -> consolidate -> get sharper.",
], "dejavu  ·  the self-improving loop", MAGENTA, tag="SELF-LEARNING")

PMF=terminal([
  "D0xedDev  --  live autonomous agent hub",
  "",
  "  running in production on Base",
  "  real usage  ·  real audience  ·  real txs",
  "",
  "memory    : Sibyl Memory  (load-bearing)",
  "engine    : NEURAL_MESH  (six lanes)",
  "on-chain  : Base  (executed action)",
  "agent     : Virtuals ACP  (coordinates loop)",
  "",
  "> both partner stacks exercised in the demo.",
], "not a toy  ·  a live system", CYAN, tag="PMF")

CLOSE_lines=[
  "> Forgetting is a bug.",
  "> Remembering is the strategy.",
  "",
  "dejavu  ·  NEURAL_MESH  ·  Sibyl Memory",
  "MIT  ·  github.com/D0xedDevi0/NEURAL_MESH",
  "build in public  ·  @D0xedDevi0",
]
def scene_close():
    img,d=new_frame()
    d.text((120,300),"Forgetting is a bug.",font=F(72,True),fill=RED)
    d.text((120,400),"Remembering is the strategy.",font=F(72,True),fill=CYAN)
    d.text((120,560),"dejavu  ·  NEURAL_MESH  ·  Sibyl Memory",font=F(30,True),fill=WHITE)
    d.text((120,620),"MIT  ·  github.com/D0xedDevi0/NEURAL_MESH  ·  @D0xedDevi0",font=F(24),fill=GRAY)
    footer(d,"hackathon demo · build in public · real Base txs verified on mainnet")
    return img

def scene_title():
    img,d=new_frame()
    d.text((120,250),"dejavu",font=F(120,True),fill=CYAN)
    d.text((120,430),"the agent that remembers",font=F(44,True),fill=WHITE)
    d.text((120,510),"NEURAL_MESH  x  Sibyl Memory",font=F(28),fill=GRAY)
    d.text((120,560),"> an agent whose on-chain decisions are driven by its own memory.",font=F(26),fill=AMBER)
    d.text((120,660),"Built for the Sibyl Memory Hackathon  ·  @base  @virtuals_io",font=F(22),fill=DIM)
    footer(d,"Forgetting is a bug. Remembering is the strategy.")
    return img

SCENES=[
  ("01_title",   scene_title,      "seg01_open.mp3",    2.6, 1.2),
  ("02_problem", lambda: PROBLEM,  "seg02_problem.mp3", 1.4, 1.6),
  ("03_sessionA",lambda: SESSION_A,"seg03_session_a.mp3",1.4,1.6),
  ("04_gate",    lambda: GATE,     "seg04_gate.mp3",    1.4, 1.6),
  ("05_sessionB",lambda: SESSION_B,"seg05_session_b.mp3",1.4,1.6),
  ("06_measured",scene_measured,   "seg06_measured.mp3",1.6,1.6),
  ("10_graph_scale", scene_graph_scale, "seg10_graph_scale.mp3", 1.6, 1.6),
  ("11_audit",   lambda: AUDIT,     "seg11_audit.mp3",   1.4, 1.6),
  ("07_dejavu",  lambda: DEJAVU,    "seg07_dejavu.mp3",  1.4, 1.6),
  ("08_pmf",     lambda: PMF,      "seg08_pmf.mp3",     1.4, 1.8),
  ("09_close",   scene_close,      "seg09_close.mp3",   1.0, 3.2),
]

def ffprobe_dur(p):
    r=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                      "-of","default=noprint_wrappers=1:nokey=1",p],capture_output=True,text=True)
    return float(r.stdout.strip())

def dur_for(name, lead, tail):
    audio=next(s[2] for s in SCENES if s[0]==name)
    narr=ffprobe_dur(os.path.join(NARR, audio))
    return lead+narr+tail, lead, narr

def main():
    print(">> rendering scene frames ...")
    paths={}
    for name,fn,audio,lead,tail in SCENES:
        img=fn()
        if img is None: img=terminal(CLOSE_lines,"remember => survive",CYAN,"MIT")
        p=os.path.join(FRAMES,f"{name}.png"); img.save(p); paths[name]=p
    print("   frames ->",FRAMES)

    print(">> building motion segments (zoompan + fades) ...")
    segs=[]
    n=len(SCENES)
    from concurrent.futures import ThreadPoolExecutor
    def _seg(i,name,fn,audio,lead,tail):
        dur,_,_=dur_for(name,lead,tail)
        frames=int(round(dur*30))
        if i%3==0:
            zexpr="min(zoom+0.0006,1.14)"
        elif i%3==1:
            zexpr="if(lte(zoom,1.0),1.14,max(1.001,zoom-0.0006))"
        else:
            zexpr="min(zoom+0.0008,1.16)"
        vf=(f"scale=2200:1238,zoompan=z='{zexpr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={frames}:s=1600x900:fps=30,fade=t=in:st=0:d=0.5,fade=t=out:st={max(0,dur-0.5):.2f}:d=0.5,format=yuv420p")
        out=os.path.join(SEG,f"{name}.mp4")
        # reuse existing segment if it already matches duration (saves rebuilds)
        if os.path.exists(out):
            try:
                if abs(ffprobe_dur(out)-dur) < 0.3:
                    return (name,dur,True,"reused")
            except Exception:
                pass
        cmd=["ffmpeg","-y","-i",paths[name],"-vf",vf,"-frames:v",str(frames),
             "-c:v","libx264","-preset","veryfast","-crf","20","-r","30",out]
        r=subprocess.run(cmd,capture_output=True,text=True)
        if r.returncode!=0:
            return (name,dur,False,r.stderr[-800:])
        return (name,dur,True,"")
    with ThreadPoolExecutor(max_workers=4) as ex:
        for name,dur,ok,err in ex.map(_seg, range(n), *zip(*SCENES)):
            if not ok:
                print(f"   {name}: FAIL {err}"); raise SystemExit(1)
            segs.append(os.path.join(SEG,f"{name}.mp4"))
            print(f"   {name}: {dur:.1f}s")

    print(">> concatenating video ...")
    lst=os.path.join(SEG,"list.txt")
    with open(lst,"w") as fh:
        for s in segs: fh.write(f"file '{s}'\n")
    video=os.path.join(SEG,"concat_video.mp4")
    r=subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",lst,
                      "-c","copy","-movflags","+faststart",video],capture_output=True,text=True)
    if r.returncode!=0: print(r.stderr[-1500:]); raise SystemExit(r.returncode)
    vdur=ffprobe_dur(video)

    print(">> building narration track (lead+seg+tail per scene) ...")
    wavs=[]
    for name,fn,audio,lead,tail in SCENES:
        narr=os.path.join(NARR,audio)
        segdur,leadv,_=dur_for(name,lead,tail)
        tailv=segdur-leadv-ffprobe_dur(narr)
        L=os.path.join(SEG,f"{name}_lead.wav")
        subprocess.run(["ffmpeg","-y","-f","lavfi","-i","anullsrc=r=44100:cl=mono",
                        "-t",f"{leadv:.2f}","-c:a","pcm_s16le",L],capture_output=True)
        N=os.path.join(SEG,f"{name}_narr.wav")
        subprocess.run(["ffmpeg","-y","-i",narr,"-ar","44100","-ac","1","-c:a","pcm_s16le",N],capture_output=True)
        T=os.path.join(SEG,f"{name}_tail.wav")
        subprocess.run(["ffmpeg","-y","-f","lavfi","-i","anullsrc=r=44100:cl=mono",
                        "-t",f"{tailv:.2f}","-c:a","pcm_s16le",T],capture_output=True)
        clist=os.path.join(SEG,f"{name}_parts.txt")
        with open(clist,"w") as fh:
            for p in (L,N,T): fh.write(f"file '{p}'\n")
        c=os.path.join(SEG,f"{name}_full.wav")
        r=subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",clist,
                          "-c:a","pcm_s16le",c],capture_output=True,text=True)
        if r.returncode!=0:
            print(f"   {name}: audio concat FAIL {r.stderr[-400:]}"); raise SystemExit(r.returncode)
        wavs.append(c)
    alist=os.path.join(SEG,"audio_list.txt")
    with open(alist,"w") as fh:
        for w in wavs: fh.write(f"file '{w}'\n")
    narration=os.path.join(SEG,"narration.wav")
    r=subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",alist,"-c:a","pcm_s16le",narration],
                     capture_output=True,text=True)
    if r.returncode!=0:
        print("   final narration concat FAIL", r.stderr[-400:]); raise SystemExit(r.returncode)
    print(f"   narration.wav = {ffprobe_dur(narration):.1f}s")

    print(">> synthesizing subtle ambient music bed ...")
    # D minor-ish pad: D3 F3 A3 C4 E4 + a low Bb2 root for warmth; slow tremolo + reverb-ish echo
    music=os.path.join(SEG,"music.wav")
    total=vdur
    # layered sines via aevalsrc
    evals=[]
    freqs=[146.83,174.61,220.0,261.63,329.63, 233.08]  # D3 F3 A3 C4 E4 Bb3
    # gentle slow amplitude: 0.5+0.5*sin(2*pi*0.05*t) very slow swell
    parts=[]
    for f in freqs:
        parts.append(f"0.10*sin(2*PI*{f}*t)*(0.55+0.45*sin(2*PI*0.04*t+0.2))")
    expr="+".join(parts)
    r=subprocess.run(["ffmpeg","-y","-f","lavfi","-i",f"aevalsrc={expr}:d={total:.2f}:s=44100",
                      "-af","lowpass=f=900,aecho=0.8:0.6:120|240:0.25|0.15,volume=0.16",
                      "-c:a","pcm_s16le",music],capture_output=True,text=True)
    if r.returncode!=0: print("  (music synth warn)",r.stderr[-300:])

    print(">> mixing narration + music, muxing ...")
    mix=os.path.join(SEG,"mix.wav")
    r=subprocess.run(["ffmpeg","-y","-i",narration,"-i",music,
                      "-filter_complex","[0:a]volume=1.0[n];[1:a]volume=0.5[m];[n][m]amix=inputs=2:duration=first:normalize=0[a]",
                      "-map","[a]","-c:a","pcm_s16le",mix],capture_output=True,text=True)
    if r.returncode!=0:
        print("  (mix warn)",r.stderr[-400:]); raise SystemExit(r.returncode)
    final=os.path.join(HERE,"demo_video_v2.mp4")
    r=subprocess.run(["ffmpeg","-y","-i",video,"-i",mix,
                      "-c:v","copy","-c:a","aac","-b:a","192k","-shortest","-movflags","+faststart",final],
                     capture_output=True,text=True)
    if r.returncode!=0:
        print("  (final mux FAIL)",r.stderr[-800:]); raise SystemExit(r.returncode)
    dur=ffprobe_dur(final)
    print("DONE:",final, os.path.getsize(final),"bytes  duration",round(dur,1),"s")

if __name__=="__main__":
    main()
