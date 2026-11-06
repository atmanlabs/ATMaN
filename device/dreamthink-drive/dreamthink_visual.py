"""DreamThink Brainstorm: a visual metaphor driven by actual practice telemetry."""
import json,math,time,tkinter as tk
from PIL import Image, ImageTk, ImageDraw, ImageFilter, ImageChops
from pathlib import Path
ROOT=Path(__file__).resolve().parent/'runtime'/'dream-cloud'
BG='#070b16'
def read(path,default):
    try:return json.loads(path.read_text(encoding='utf-8-sig')) if path.stat().st_size<4194304 else default
    except (OSError,ValueError):return default
def blend(a,b,t):
    av=[int(a[i:i+2],16) for i in (1,3,5)];bv=[int(b[i:i+2],16) for i in (1,3,5)]
    return '#'+''.join(f'{int(x+(y-x)*t):02x}' for x,y in zip(av,bv))
class Brainstorm:
    def __init__(self,window):
        self.window=window;window.title('DreamThink — Brainstorm');window.geometry('1220x840');window.minsize(1000,720)
        window.configure(bg=BG);self.zero=time.monotonic();self.record={};self.rest={};self.state={};self.phase=0
        self.art=Image.open(Path(__file__).resolve().parent/'dreamthink-storm-original.png').convert('RGB')
        self.art_size=None;self.art_tk=None
        top=tk.Frame(window,bg=BG);top.pack(fill='x',padx=30,pady=(24,5))
        tk.Label(top,text='D R E A M T H I N K',font=('Segoe UI',24,'bold'),fg='#edf4ff',bg=BG).pack(side='left')
        self.badge=tk.Label(top,text='B R A I N S T O R M',font=('Segoe UI',11,'bold'),fg='#86e9db',bg=BG);self.badge.pack(side='right')
        self.subtitle=tk.Label(window,text='',bg=BG,fg='#8fa8c8',font=('Segoe UI',11));self.subtitle.pack()
        self.canvas=tk.Canvas(window,bg=BG,height=470,highlightthickness=0);self.canvas.pack(fill='both',expand=True,padx=12)
        self.stats=tk.Label(window,bg=BG,fg='#a3cbdc',font=('Segoe UI',11));self.stats.pack(pady=(1,10))
        panel=tk.Frame(window,bg='#111d30',height=140,highlightthickness=1,highlightbackground='#25405a');panel.pack(fill='x',padx=30,pady=(0,14));panel.pack_propagate(False)
        self.state_label=tk.Label(panel,bg='#111d30',fg='#74e5c2',font=('Segoe UI',10,'bold'),anchor='w');self.state_label.pack(fill='x',padx=20,pady=(12,4))
        self.lesson=tk.Text(panel,bg='#111d30',fg='#f0f4ff',font=('Segoe UI',12),wrap='word',height=4,relief='flat')
        self.lesson.pack(fill='both',expand=True,padx=20,pady=(0,15))
        tk.Label(window,text='Recorded cycle activity replay · Regions represent software functions, not anatomy · Lightning is artistic, not a measure of intelligence.',
                 bg=BG,fg='#637e9e',font=('Segoe UI',9)).pack(pady=(0,12))
        self.refresh();self.animate()
    def set_lesson(self,text):
        if getattr(self,'lesson_text',None)==text:return
        self.lesson_text=text
        self.lesson.configure(state='normal');self.lesson.delete('1.0','end');self.lesson.insert('1.0',text);self.lesson.configure(state='disabled')

    def refresh(self):
        self.record=read(ROOT/'dreamthink-practice'/'latest.json',{})
        self.rest=read(ROOT.parent/'timed-sleep.json',{})
        self.state=read(ROOT/'dreamthink-practice'/'state.json',{})
        self.phase=min(3,int(max(0,time.time()-self.rest.get('started_at',time.time()))//3600))
        remaining=max(0,int(self.rest.get('wake_at',0)-time.time())) if self.rest.get('state')=='sleeping' else 0
        phase=self.record.get('phase_name','Waiting for a live cycle')
        self.subtitle.config(text=f'{phase}    /    HOUR {self.phase+1} OF 4    /    {remaining//3600:02}:{remaining//60%60:02}:{remaining%60:02} remaining')
        status=self.record.get('status','waiting')
        self.badge.config(text='D R E A M I N G' if remaining else 'A W A K E',fg='#86e9db' if remaining else '#8fa8c8')
        review=self.record.get('reconciler',[])
        rc='passed' if review and review[0].get('approved') else 'holding'
        judge=self.record.get('judge',{})
        jd='approved' if judge.get('approved') else 'not submitted' if not judge else 'rejected'
        self.stats.config(text=f"{self.state.get('cycles',0)} cycles    ·    {sum(self.state.get('phase_imprints',{}).values())} lessons retained    ·    Reconciler {rc}    ·    Judge {jd}    ·    0 model calls")
        color='#74e5c2' if status=='imprinted' else '#d5a3ed' if 'duplicate' in status else '#f6be90' if 'reject' in status else '#95b9dd'
        self.state_label.config(text=status.replace('-',' ').upper(),fg=color)
        self.set_lesson(self.record.get('gist') or self.record.get('rejection_reason') or 'The next idea has not converged yet.')
        self.window.after(1000,self.refresh)
    def animate(self):
        self.storm()
        self.window.after(100,self.animate)

    def storm(self):
        c=self.canvas;c.delete('all');w=max(c.winfo_width(),900);h=max(c.winfo_height(),380)
        # Fit the supplied artwork intact; resize only when the viewport changes.
        scale=min(w/self.art.width,h/self.art.height)
        size=(int(self.art.width*scale),int(self.art.height*scale))
        if size!=self.art_size:
            self.art_base=self.art.resize(size,Image.Resampling.LANCZOS);self.art_size=size
            self.glow_masks=[]
            for nx,ny in ((.28,.40),(.51,.20),(.68,.35),(.52,.60),(.78,.55),(.65,.78)):
                mask=Image.new('L',size);draw=ImageDraw.Draw(mask)
                x,y=nx*size[0],ny*size[1];rx,ry=size[0]*.13,size[1]*.105
                draw.ellipse((x-rx,y-ry,x+rx,y+ry),fill=220)
                self.glow_masks.append(mask.filter(ImageFilter.GaussianBlur(max(6,size[0]*.035))))
        x0=(w-size[0])/2;y0=(h-size[1])/2
        rec=self.record; sandbox=rec.get('sandbox',{})
        regions=[('FRAGMENTS',.28,.40,'#79e8ff',bool(rec.get('scenario'))),
                 ('CONNECTIONS',.51,.20,'#bca1ff',bool(rec.get('funnel',{}).get('thoughts'))),
                 ('DREAM WORLD',.68,.35,'#ffbf77',bool(sandbox.get('trace'))),
                 ('RECONCILER',.52,.60,'#73ffd4',bool(rec.get('reconciler'))),
                 ('JUDGE',.78,.55,'#ff92df',bool(rec.get('judge'))),
                 ('RETAINED LESSON',.65,.78,'#fff0a0',bool(rec.get('gists_imprinted')))]
        elapsed=time.monotonic()-self.zero
        fresh=time.time()-rec.get('timestamp',0)<100 and self.rest.get('state')=='sleeping'
        selected=int(elapsed/2)%len(regions)
        # Render light across the cloud texture, not just around an indicator.
        frame=self.art_base
        if fresh and regions[selected][4]:
            pulse=.28+.65*(.5+.5*math.sin(elapsed*3.1))
            mask=self.glow_masks[selected].point([int(v*pulse) for v in range(256)])
            light=Image.new('RGB',size,regions[selected][3])
            luminous=ImageChops.screen(self.art_base,light)
            frame=Image.composite(luminous,self.art_base,mask)
        self.art_tk=ImageTk.PhotoImage(frame)
        c.create_image(w/2,h/2,image=self.art_tk)
        for i,(name,nx,ny,color,present) in enumerate(regions):
            x=x0+nx*size[0];y=y0+ny*size[1]
            active=present and fresh and i==selected
            radius=20+5*math.sin(elapsed*2) if active else 12
            if active:
                for k in range(3):
                    rr=radius+k*7
                    c.create_oval(x-rr,y-rr,x+rr,y+rr,outline=color,width=2 if k==0 else 1)
                pts=[]
                for j in range(9):
                    pts.extend((x+(j-4)*9,y+math.sin(j*2.6+int(elapsed*6))*12))
                c.create_line(*pts,fill=color,width=3)
                c.create_line(*pts,fill='white',width=1)
            c.create_oval(x-5,y-5,x+5,y+5,fill=color if present else '#455166',outline='')
            lx=22 if i<3 else w-215;ly=38+(i%3)*63
            c.create_line(x,y,lx+90,ly+12,fill=color if active else '#455166',dash=() if active else (2,5))
            c.create_rectangle(lx-8,ly-10,lx+192,ly+34,fill=BG,outline=color if active else '#24344b')
            c.create_text(lx,ly,text=name,anchor='w',fill=color,font=('Segoe UI',10,'bold'))
            c.create_text(lx,ly+19,text='RECORDED ACTIVITY' if present else 'NOT IN THIS CYCLE',anchor='w',fill='#91a4bc',font=('Segoe UI',8))
        c.create_text(w/2,h-17,text='CYCLE REPLAY  •  '+rec.get('status','waiting').replace('-',' ').upper(),fill='#dcf5ff',font=('Segoe UI',10,'bold'))
        if sandbox:
            self.state_label.config(text='DREAM WORLD: '+sandbox.get('kind','').upper()+' · '+sandbox.get('status','').upper())
            self.set_lesson(' → '.join(e['action']+' ['+e.get('status',e.get('outcome','recorded'))+']' for e in sandbox.get('trace',[])))

    def legacy_graph(self):
        c=self.canvas;c.delete('all');w=max(c.winfo_width(),900);h=max(c.winfo_height(),380)
        t=time.monotonic()-self.zero;cx=w*.50;cy=h*.48
        # Slow ambient nebula; no semantic claims are encoded by the animation.
        for i in range(30):
            a=i*2.399;tone='#243b72' if i%3 else '#493474'
            x=cx+math.cos(a)*w*.23+math.sin(t*.12+i)*18
            y=cy+math.sin(a)*h*.24+math.cos(t*.13+i)*13
            radius=48+(i%7)*7
            c.create_oval(x-radius*1.6,y-radius,x+radius*1.6,y+radius,fill=blend(BG,tone,.22+(i%3)*.04),outline='')
        # Star field is decorative, deliberately slower and quieter than actual graph signals.
        for i in range(65):
            x=(i*173.73)%w;y=(i*91.17)%h
            glow=.18+.15*(1+math.sin(t*.45+i))/2
            color=blend(BG,'#a8d8f2',glow);r=1 if i%7 else 1.6
            c.create_oval(x-r,y-r,x+r,y+r,fill=color,outline='')
        sc=self.record.get('scenario',{})
        edges=[r for row in sc.get('rows',[]) for r in row.get('relations',[])]
        names=list(dict.fromkeys(s for r in edges for s in (r['subject'],r['object'])))[:12]
        positions={}
        for i,name in enumerate(names):
            a=2*math.pi*i/max(1,len(names))-.8
            positions[name]=(cx+math.cos(a)*w*.25+math.sin(t*.2+i)*13,cy+math.sin(a)*h*.27+math.cos(t*.18+i)*12)
        # Existing relationships glow quietly. No edges are fabricated.
        for i,r in enumerate(edges):
            if r['subject'] not in positions or r['object'] not in positions:continue
            p=positions[r['subject']];q=positions[r['object']]
            color='#e58ba0' if r.get('negative') else '#3b7298'
            c.create_line(*p,*q,fill=blend(BG,color,.38),width=7,smooth=True)
            c.create_line(*p,*q,fill=color,width=1,dash=(5,5) if r.get('negative') else ())
        # Flash only derived links recorded by the actual funnel, never imaginary inferences.
        for i,thought in enumerate(self.record.get('funnel',{}).get('thoughts',[])):
            r=thought['relationship']
            if r['subject'] not in positions or r['object'] not in positions:continue
            p=positions[r['subject']];q=positions[r['object']]
            pulse=.4+.5*(1+math.sin(t*1.8+i))/2
            for width,brightness in ((11,.12),(6,.25),(2,.9)):
                c.create_line(*p,*q,fill=blend(BG,'#78ffe1',brightness*pulse),width=width)
            # Traveling points illustrate the recorded relationship, not new events.
            fraction=(t*.17+i*.21)%1;x=p[0]+(q[0]-p[0])*fraction;y=p[1]+(q[1]-p[1])*fraction
            c.create_oval(x-3,y-3,x+3,y+3,fill='#b7fff0',outline='')
        for i,(name,(x,y)) in enumerate(positions.items()):
            core='#7bdcd8' if i<3 else '#7c94da'
            for k in range(6,0,-1):
                radius=18+k*6
                c.create_oval(x-radius,y-radius,x+radius,y+radius,fill=blend(BG,core,.02+(7-k)*.014),outline='')
            c.create_oval(x-6,y-6,x+6,y+6,fill=core,outline='#d9ffff')
            c.create_text(x,y+35,text=name,fill='#d7e9f7',width=190,font=('Segoe UI',10,'bold'))
        # Central storm ring reflects result class through color, without inventing a thought.
        held='reject' in self.record.get('status','')
        color='#f2aa90' if held else '#92f4df'
        radius=25+math.sin(t*.8)*3
        c.create_oval(cx-radius,cy-radius,cx+radius,cy+radius,outline=blend(BG,color,.5),width=1)
        c.create_text(cx,cy,text='HELD' if held else 'DREAM',fill=color,font=('Segoe UI',9,'bold'))
        c.create_text(cx,28,text=sc.get('prompt','Waiting for real DreamThink telemetry…'),fill='#aabfd6',width=w-110,font=('Segoe UI',11))
        sandbox=self.record.get('sandbox',{})
        if sandbox:
            events=sandbox.get('trace',[])
            text='DREAM WORLD: '+sandbox.get('kind','')+' | '+sandbox.get('status','')+'\n'
            text+=' → '.join(e['action']+' ['+e['status']+']' for e in events)
            c.create_text(cx,h-75,text=text,fill='#a9f5da',width=w-70,font=('Segoe UI',10,'bold'))
        # Four-hour journey indicator.
        labels=['CONVERSATION → ACTION','FILES & MEMORY','RECOVERY & PROOF','PLANNING & IMPROVEMENT']
        for i,label in enumerate(labels):
            x=w*(.14+i*.24);active=i==self.phase
            c.create_line(x-70,h-27,x+70,h-27,fill='#78dec9' if active else '#23344e',width=3 if active else 1)
            c.create_text(x,h-12,text=label,fill='#b1eada' if active else '#647a96',font=('Segoe UI',8,'bold'))
        self.window.after(80,self.animate)
if __name__=='__main__':
    window=tk.Tk();Brainstorm(window);window.mainloop()
