#!/usr/bin/env python3
"""Build the THE SPINE demo video — deep/confident narrated, cinematic.

Fused identity: NEURAL_MESH blueprint navy/pixel-grid/cyan + Sibyl oracle.
12 scenes, each synced to a narration segment (spine_narr/spine_*.mp3).
Motion via zoompan (Ken Burns), per-scene fade in/out, subtle ambient music bed.
Voice: edge-tts en-US-BrianNeural (deep/confident) — see _gen_narr.py.

Usage:
    PYTHONPATH=. /opt/data/dxlive/.venv/bin/python demo/build_video_spine.py
"""
from __future__ import annotations
import os, subprocess, random, json
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FRAMES = os.path.join(HERE, "_frames_spine")
NARR = os.path.join(HERE, "spine_narr")
SEG = os.path.join(HERE, "_segments_spine")
os.makedirs(FRAMES, exist_ok=True)
os.makedirs(SEG, exist_ok=True)

# ---------------- brand ----------------
BG=(0,18,64); BG2=(0,12,40); PANEL=(0,30,72); GRID=(0,26,90)
CYAN=(0,212,255); BLUE=(0,82,255); GREEN=(0,255,136); MAGENTA=(255,0,170)
RED=(255,69,58); AMBER=(255,190,60); WHITE=(235,240,250); GRAY=(136,153,204); DIM=(90,108,150)
W,H=1600,900
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONTB="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# verified onchain facts (2026-08-29)
TX_DERISK="0xc58019b54af66f7e58d206fa5d5582323f890de1042e1d77b1184fd28ca294b7"
TX_LEARN="0x9c0aa5249beb593633353b262ce868ba6aedee43c5ec3ba6824d6e1c7e6bab0a"
ROOT="0x34dbf2324b27777fbfe5a47d222de9700acfdbd2847e60293d9260a1da223ddb"
X402_BLOCK=50608909
GATE_MP4 = os.path.join(HERE, "continuous_gate.mp4")  # real unedited capture scene


def _gate_dur():
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
                        GATE_MP4], capture_output=True, text=True)
    return float(r.stdout.strip())

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

def header(d, title, accent, tag=None, sub="THE SPINE  ·  memory owns itself, earns from itself, writes itself"):
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
        elif "0.49" in ln or "wiped" in ln or "AGAIN" in ln or "NO LESSONS" in ln or "-18%" in ln or "loses" in ln.lower() or "orphan" in ln.lower():
            col=RED
        elif "0.05" in ln or "status 1" in ln or "FOUND" in ln or "de_risk" in ln or "flips" in ln or "verified" in ln or "0.82" in ln or "de-risk" in ln or "1.67" in ln or "0.8176" in ln:
            col=GREEN
        elif "200" in ln or "402" in ln or "USDC" in ln or "settle" in ln.lower():
            col=CYAN
        elif ln.startswith("sibyl@") or (":" in ln[:14]):
            col=CYAN
        elif ln[:2] in ("A ","B ","C ","D ","E ","F ","L "): col=MAGENTA
        d.text((px+28,y),ln,font=f,fill=col); y+=38
    return img

# ---------------- charts ----------------
def chart_gate(r, cw, ch):
    img=Image.new("RGB",(cw,ch),(12,14,20)); d=ImageDraw.Draw(img)
    d.text((30,26),"economic deletion gate · 12 crises · seed 1337",font=F(24,True),fill=CYAN)
    # capital bar
    axis_x=cw-250; bar_h=90
    worst=max(r['capital_with_memory'], r['capital_without_memory'])
    scale=(axis_x-90)/worst
    for val,y,color,label in ((r['capital_without_memory'],150,RED,"WIPED"),(r['capital_with_memory'],300,GREEN,"WITH MEMORY")):
        w=val*scale
        d.rounded_rectangle((axis_x-w,y,axis_x,y+bar_h),radius=8,fill=color)
        d.text((axis_x+16,y+8),label,font=F(22,True),fill=color)
        d.text((axis_x+16,y+48),f"{val:.2f}",font=F(24,True),fill=color)
    d.line((axis_x,110,axis_x,ch-50),fill=(70,78,96),width=2)
    d.text((axis_x-30,105),"0",font=F(18),fill=(120,128,148))
    d.text((30,ch-36),f"capital preserved {r['capital_preserved_multiple']}x · mean return -{abs(r['mean_return_no_memory_pct']):.2f}% wiped vs -{abs(r['mean_return_memory_pct']):.2f}% with memory",font=F(17),fill=(235,238,245))
    return img

# ---------------- scene content ----------------
SPINE=json.load(open(os.path.join(HERE,"spine_ablation.json")))

def scene_open():
    img,d=new_frame()
    d.text((120,250),"THE SPINE",font=F(120,True),fill=CYAN)
    d.text((120,430),"memory that owns itself",font=F(44,True),fill=WHITE)
    d.text((120,510),"NEURAL_MESH  x  Sibyl Memory",font=F(28),fill=GRAY)
    d.text((120,560),"> sovereign · identity · self-authored · shared · regret · temporal · loop · conflict",font=F(25),fill=AMBER)
    d.text((120,660),"Built for the Sibyl Memory Hackathon  ·  @base  @virtuals_io",font=F(22),fill=DIM)
    footer(d,"Forgetting is a bug. Remembering is the strategy.")
    return img

def scene_problem():
    return terminal([
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

def scene_sovereign():
    return terminal([
      "SOVEREIGN MEMORY  --  content-addressed",
      "",
      "root = sha256(concat(content))",
      f"  {ROOT[:38]}...",
      "",
      "anchor:  ACT_ONCHAIN(Base)",
      f"  tx {TX_DERISK[:20]}...  status 1",
      f"  block {X402_BLOCK}",
      "",
      "wipe the store  ->  root orphans  ->  asset gone",
      "",
      "> the memory is an asset it owns.",
    ], "L1  ·  sovereign  ·  the memory is an asset", GREEN, tag="ANCHORED")

def scene_gate():
    return terminal([
      "SESSION B  --  store DELETED",
      "",
      "frame: vix=52.0 credit_stress=2.2  (SAME)",
      "",
      "recall: search(...) ->  NO LESSONS  (wiped)",
      "",
      "decide_differently(frame, None)",
      "  naive_book()   <- fails open",
      "  equity = 0.49   stays LONG",
      "",
      "outcome: -18% drawdown AGAIN.",
      "",
      "> that's what forgetting a soul costs.",
    ], "the gate  ·  wipe it, it breaks", RED, tag="STORE WIPED")

def scene_sessionB():
    return terminal([
      "SESSION B  --  memory loaded",
      "",
      "frame: vix=52.0 credit_stress=2.2  (SAME)",
      "",
      "recall: search('credit stress crisis')",
      "  -> 1 lesson FOUND  (remembered)",
      "",
      "decide_differently(frame, memory)",
      "  de_risk_book()   <- flips",
      "  equity = 0.05   cash = 0.59",
      "",
      "act_onchain(Base): REAL TX  status 1",
      f"  {TX_DERISK[:20]}...",
    ], "L1  ·  remembers, then acts", GREEN, tag="MEMORY-LOADED")

def scene_identity():
    return terminal([
      "IDENTITY  --  memory defines the being",
      "",
      "identity = hash(root, contents)",
      "",
      "same box + same store  ->  SAME BEING",
      "same box + wiped store  ->  identity CHANGES",
      "",
      "measured (12 crises, seed 1337):",
      "  identity stable WITH memory",
      "  identity churns WITHOUT memory",
      "",
      "> wipe changes who it is.",
    ], "L2  ·  identity  ·  memory defines the being", MAGENTA, tag="SAME BEING")

def scene_dream():
    return terminal([
      "DREAM / LEARNER  --  writes its own skills",
      "",
      "pattern: 'crisis -> de-risk -> survived'",
      "  observed across sessions A..N",
      "",
      "proposal (skill/crisis-derisking):",
      "  'when stressed, de-risk to cash'",
      "  confidence=high",
      "",
      "accept -> doc_key skill/crisis-derisking",
      "",
      "> recall -> consolidate -> get sharper.",
    ], "L3  ·  self-authorship  ·  memory writes itself", MAGENTA, tag="SELF-LEARNING")

def scene_commons():
    return terminal([
      "SHARED MEMORY  --  the fleet commons",
      "",
      "agent news  ->  writes 'view/news/market'",
      "agent risk  ->  writes 'view/risk/stress'",
      "allocator   ->  reads the whole board",
      "",
      "no agent talks to another.",
      "the memory is the only thing they share.",
      "",
      "> one store, many agents, one brain.",
    ], "L4  ·  commons  ·  a fleet, one memory", CYAN, tag="SHARED")

def scene_regret():
    return terminal([
      "REGRET / COUNTERFACTUAL  --  the road not taken",
      "",
      "if it had stayed LONG in that crisis:",
      "  would have lost 18%",
      "  regret_urgency = high",
      "",
      "the memory records the mistake",
      "  it NEVER made.",
      "",
      "> memory, even of what did not happen.",
    ], "L5  ·  regret  ·  remembers the road not taken", MAGENTA, tag="COUNTERFACTUAL")

def scene_temporal():
    return terminal([
      "TEMPORAL  --  a time-bound, dynamic layer",
      "",
      "belief formed  : day 41  (credit stress)",
      "reinforced     : day 52,  day 78",
      "",
      "stale memory  ->  score low  ->  ARCHIVE",
      "fresh memory   ->  retained  ->  live",
      "",
      "strategic forgetting, not amnesia.",
      "archive is recoverable.",
      "",
      "> it knows WHEN it believes.",
    ], "L6  ·  temporal  ·  dynamic, not static", CYAN, tag="TIME-BOUND")

def scene_earns():
    img,d=new_frame(); header(d,"it earns  ·  paid reads, settled on-chain",GREEN,tag="PMF · LIVE")
    px,py,pw,ph=44,168,W-88,H-168-60
    d.rounded_rectangle((px,py,px+pw,py+ph),radius=14,outline=BLUE,fill=PANEL,width=2)
    lines=[
      "memory-query endpoint  (x402 paid read · $0.01 USDC)",
      "",
      "GET  -> HTTP 402   (pay 10000 micro-USDC = $0.01)",
      "sign -> EIP-3009 TransferWithAuthorization",
      "retry-> HTTP 200   (memory data returned)",
      "",
      "EXTERNAL payer 0x4a15fc61...  settled 2x on Base",
      "  tx 0x7f3e577b...   status 1   block 50,609,928",
      "  tx 0x57f15297...   status 1   block 50,609,934",
      "agent production wallet 0x23129c04...  ->  459 txs",
      "",
      "> someone outside us paid to read the memory.",
    ]
    y=py+20; f=F(23)
    for ln in lines:
        col=WHITE
        if ln.startswith(">"): col=AMBER
        elif "200" in ln or "1.0" in ln or "settled" in ln.lower() or "status 1" in ln or "459" in ln: col=GREEN
        elif "402" in ln or "10000" in ln or "USDC" in ln: col=CYAN
        elif "EXTERNAL" in ln or "0x4a15fc61" in ln or "0x7f3e577b" in ln or "0x57f15297" in ln: col=MAGENTA
        elif "sign" in ln.lower(): col=GRAY
        d.text((px+28,y),ln,font=f,fill=col); y+=36
    footer(d,"docs/pmf.md  ·  verified settlements 2026-08-29  ·  all receipts on basescan")
    return img

def scene_loop():
    img,d=new_frame(); header(d,"the sovereign loop  ·  it remembers",GREEN,tag="SELF-REFERENTIAL")
    px,py,pw,ph=44,168,W-88,H-168-60
    d.rounded_rectangle((px,py,px+pw,py+ph),radius=14,outline=BLUE,fill=PANEL,width=2)
    lines=[
      "mint the root on-chain  ->  tx committed on Base",
      "",
      "anchor_self(memory, mint)",
      "  writes the receipt BACK INTO the store",
      "  (REFERENCE tier, folded into the root)",
      "",
      "fresh box, same store:",
      "  identity provably references committed root",
      "  is_self_anchored -> True",
      "",
      "wipe the store:",
      "  anchor lost, asset orphaned, identity churns",
      "",
      "> the memory doesn't get anchored. it remembers.",
    ]
    y=py+20; f=F(23)
    for ln in lines:
        col=WHITE
        if ln.startswith(">"): col=AMBER
        elif "True" in ln or "committed" in ln or "self_anchored" in ln or "back INTO" in ln: col=GREEN
        elif "wipe" in ln.lower() or "orphaned" in ln.lower() or "churns" in ln: col=RED
        elif "fresh" in ln.lower() or "identity" in ln.lower(): col=CYAN
        d.text((px+28,y),ln,font=f,fill=col); y+=36
    footer(d,"src/dejavu/sovereign.py::anchor_self  ·  tests/test_sovereign_loop.py")
    return img

def scene_conflict():
    img,d=new_frame(); header(d,"write-time conflict resolution",MAGENTA,tag="L8 · CONFLICT")
    px,py,pw,ph=44,168,W-88,H-168-60
    d.rounded_rectangle((px,py,px+pw,py+ph),radius=14,outline=BLUE,fill=PANEL,width=2)
    lines=[
      "view/risk/stress  { credit_stress: 0.3 }   (day 1)",
      "view/risk/stress  { credit_stress: 1.4 }   (day 2)",
      "view/risk/stress  { credit_stress: 2.2 }   (day 3)",
      "",
      "supersede_entity(old, new):",
      "  winner  -> live WARM entity",
      "  loser   -> ARCH tier  (recoverable)",
      "  event   -> SUPERSEDES  (journaled)",
      "",
      "supersession_chain(key):",
      "  reconstructs old -> new revision trail",
      "",
      "> contradictions are resolved, never erased.",
    ]
    y=py+20; f=F(23)
    for ln in lines:
        col=WHITE
        if ln.startswith(">"): col=AMBER
        elif "winner" in ln or "WARM" in ln or "reconstruct" in ln.lower() or "trail" in ln: col=GREEN
        elif "loser" in ln or "ARCH" in ln or "recoverable" in ln: col=CYAN
        elif "SUPERSEDES" in ln or "resolved" in ln: col=MAGENTA
        d.text((px+28,y),ln,font=f,fill=col); y+=36
    footer(d,"src/dejavu/supersede.py  ·  Mem0-equivalent  ·  tests/test_sovereign_loop.py")
    return img

def scene_close():
    img,d=new_frame()
    d.text((120,220),"Forgetting is a bug.",font=F(68,True),fill=RED)
    d.text((120,320),"Remembering is the strategy.",font=F(68,True),fill=CYAN)
    d.text((120,470),"THE SPINE",font=F(56,True),fill=WHITE)
    d.text((120,560),"sovereign · identity · self-authored · shared · regret · temporal",font=F(24),fill=GRAY)
    d.text((120,604),"sovereign loop · conflict resolution · earned (PMF live)",font=F(24),fill=GRAY)
    d.text((120,690),"MIT  ·  github.com/D0xedDevi0/dejavu-sibyl-memory  ·  @D0xedDevi0",font=F(22),fill=DIM)
    footer(d,"THE SPINE  ·  memory owns itself, earns from itself, writes itself")
    return img

SCENES=[
  ("01_open",    scene_open,      "spine_01_open.mp3",    2.2, 1.2),
  ("02_problem", scene_problem,   "spine_02_problem.mp3", 1.2, 1.4),
  ("03_sovereign",scene_sovereign,"spine_03_sovereign.mp3",1.2,1.4),
  ("04_gate",    scene_gate,      "spine_04_gate.mp3", 0.4, 0.2),
  ("05_sessionB",scene_sessionB,  "spine_05_sessionB.mp3",1.2,1.4),
  ("06_identity",scene_identity,  "spine_06_identity.mp3",1.2,1.4),
  ("07_dream",   scene_dream,     "spine_07_dream.mp3",   1.2, 1.4),
  ("08_commons", scene_commons,   "spine_08_commons.mp3", 1.2, 1.4),
  ("09_regret",  scene_regret,    "spine_09_regret.mp3",  1.2, 1.4),
  ("10_temporal",scene_temporal,  "spine_10_temporal.mp3",1.2,1.4),
  ("11_loop",    scene_loop,      "spine_11_loop.mp3",    1.2, 1.4),
  ("12_conflict",scene_conflict,  "spine_12_conflict.mp3",1.2,1.4),
  ("13_earns",   scene_earns,     "spine_13_earns.mp3",   1.2, 1.4),
  ("14_close",   scene_close,     "spine_14_close.mp3",   1.0, 2.6),
]

def ffprobe_dur(p):
    r=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                      "-of","default=noprint_wrappers=1:nokey=1",p],capture_output=True,text=True)
    return float(r.stdout.strip())

def dur_for(name, lead, tail):
    if name == "04_gate":
        gd = _gate_dur()
        narr = ffprobe_dur(os.path.join(NARR, "spine_04_gate.mp3"))
        return gd, 0.4, narr
    audio=next(s[2] for s in SCENES if s[0]==name)
    narr=ffprobe_dur(os.path.join(NARR, audio))
    return lead+narr+tail, lead, narr

def main():
    print(">> rendering scene frames ...")
    paths={}
    for name,fn,audio,lead,tail in SCENES:
        img=fn()
        p=os.path.join(FRAMES,f"{name}.png"); img.save(p); paths[name]=p
    print("   frames ->",FRAMES)

    print(">> building motion segments (zoompan + fades) ...")
    segs=[]; n=len(SCENES)
    from concurrent.futures import ThreadPoolExecutor
    def _seg(i,name,fn,audio,lead,tail):
        dur,_,_=dur_for(name,lead,tail)
        out=os.path.join(SEG,f"{name}.mp4")
        if name=="04_gate":
            # real, unedited terminal capture: no zoompan, no synthetic frame.
            # just fade in/out and re-encode to match the other segments.
            vf=(f"fade=t=in:st=0:d=0.5,fade=t=out:st={max(0,dur-0.5):.2f}:d=0.5,format=yuv420p")
            cmd=["ffmpeg","-y","-i",GATE_MP4,"-vf",vf,
                 "-c:v","libx264","-preset","veryfast","-crf","20","-r","30",out]
            r=subprocess.run(cmd,capture_output=True,text=True)
            if r.returncode!=0: return (name,dur,False,r.stderr[-800:])
            return (name,dur,True,"")
        frames=int(round(dur*30))
        if i%3==0: zexpr="min(zoom+0.00035,1.06)"
        elif i%3==1: zexpr="if(lte(zoom,1.0),1.06,max(1.001,zoom-0.00035))"
        else: zexpr="min(zoom+0.0004,1.07)"
        # scale up slightly less and keep zoom modest so edges of the frame (incl. text)
        # stay inside the visible window — no edge clipping of content.
        vf=(f"scale=1850:1041,zoompan=z='{zexpr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={frames}:s=1600x900:fps=30,fade=t=in:st=0:d=0.5,fade=t=out:st={max(0,dur-0.5):.2f}:d=0.5,format=yuv420p")
        cmd=["ffmpeg","-y","-i",paths[name],"-vf",vf,"-frames:v",str(frames),
             "-c:v","libx264","-preset","veryfast","-crf","20","-r","30",out]
        r=subprocess.run(cmd,capture_output=True,text=True)
        if r.returncode!=0: return (name,dur,False,r.stderr[-800:])
        return (name,dur,True,"")
    with ThreadPoolExecutor(max_workers=4) as ex:
        for name,dur,ok,err in ex.map(_seg, range(n), *zip(*SCENES)):
            if not ok: print(f"   {name}: FAIL {err}"); raise SystemExit(1)
            segs.append(os.path.join(SEG,f"{name}.mp4")); print(f"   {name}: {dur:.1f}s")

    print(">> concatenating video ...")
    lst=os.path.join(SEG,"list.txt")
    with open(lst,"w") as fh:
        for s in segs: fh.write(f"file '{s}'\n")
    video=os.path.join(SEG,"concat_video.mp4")
    r=subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",lst,
                      "-c","copy","-movflags","+faststart",video],capture_output=True,text=True)
    if r.returncode!=0: print(r.stderr[-1500:]); raise SystemExit(r.returncode)
    vdur=ffprobe_dur(video)

    print(">> building narration track ...")
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
        if r.returncode!=0: print(f"   {name}: audio concat FAIL"); raise SystemExit(r.returncode)
        wavs.append(c)
    alist=os.path.join(SEG,"audio_list.txt")
    with open(alist,"w") as fh:
        for w in wavs: fh.write(f"file '{w}'\n")
    narration=os.path.join(SEG,"narration.wav")
    r=subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",alist,"-c:a","pcm_s16le",narration],
                     capture_output=True,text=True)
    if r.returncode!=0: print("   narration concat FAIL"); raise SystemExit(r.returncode)
    print(f"   narration.wav = {ffprobe_dur(narration):.1f}s")

    print(">> synthesizing ambient music bed ...")
    music=os.path.join(SEG,"music.wav"); total=vdur
    freqs=[146.83,174.61,220.0,261.63,329.63,233.08]
    parts=[f"0.10*sin(2*PI*{f}*t)*(0.55+0.45*sin(2*PI*0.04*t+0.2))" for f in freqs]
    expr="+".join(parts)
    r=subprocess.run(["ffmpeg","-y","-f","lavfi","-i",f"aevalsrc={expr}:d={total:.2f}:s=44100",
                      "-af","lowpass=f=900,aecho=0.8:0.6:120|240:0.25|0.15,volume=0.16",
                      "-c:a","pcm_s16le",music],capture_output=True,text=True)

    print(">> mixing narration + music, muxing ...")
    mix=os.path.join(SEG,"mix.wav")
    r=subprocess.run(["ffmpeg","-y","-i",narration,"-i",music,
                      "-filter_complex","[0:a]volume=1.0[n];[1:a]volume=0.5[m];[n][m]amix=inputs=2:duration=first:normalize=0[a]",
                      "-map","[a]","-c:a","pcm_s16le",mix],capture_output=True,text=True)
    final=os.path.join(HERE,"demo_the_spine.mp4")
    r=subprocess.run(["ffmpeg","-y","-i",video,"-i",mix,
                      "-c:v","copy","-c:a","aac","-b:a","192k","-shortest","-movflags","+faststart",final],
                     capture_output=True,text=True)
    if r.returncode!=0: print(r.stderr[-800:]); raise SystemExit(r.returncode)
    dur=ffprobe_dur(final)
    print("DONE:",final, os.path.getsize(final),"bytes  duration",round(dur,1),"s")

if __name__=="__main__":
    main()
