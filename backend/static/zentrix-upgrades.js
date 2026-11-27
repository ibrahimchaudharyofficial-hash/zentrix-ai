/* ZENTRIX AI — next-release enhancements: 3D graphing, PDF text import, install/offline support. */
(() => {
  'use strict';
  const $ = (s) => document.querySelector(s);
  const make = (tag, cls, text) => { const n=document.createElement(tag); if(cls)n.className=cls; if(text!==undefined)n.textContent=text; return n; };
  const notifyUser = (message) => {
    if (typeof window.notify === 'function') window.notify(message);
    else { const el=$('#photoStatus'); if(el) el.textContent=message; }
  };

  // PDF text extraction is performed locally in the browser. The file is never uploaded.
  function installPdfImporter() {
    const host=$('#photoReader');
    if(!host || $('#zentrixPdfImport')) return;
    const panel=make('div','photo-controls');
    panel.id='zentrixPdfImport';
    const input=make('input','field'); input.type='file'; input.accept='application/pdf,.pdf'; input.setAttribute('aria-label','Choose a PDF worksheet');
    const button=make('button','softbtn','Extract text from PDF'); button.type='button';
    const status=make('span','subtle','PDF pages are processed on this device.');
    panel.append(input,button,status);
    host.append(panel);
    button.addEventListener('click', async () => {
      const file=input.files && input.files[0];
      if(!file){status.textContent='Choose a PDF file first.';return;}
      if(file.size>15*1024*1024){status.textContent='PDF is too large. Maximum size is 15 MB.';return;}
      button.disabled=true; status.textContent='Loading PDF reader…';
      try {
        if(!window.pdfjsLib){
          await new Promise((resolve,reject)=>{
            const script=document.createElement('script');
            script.src='https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js';
            script.onload=resolve; script.onerror=()=>reject(new Error('PDF reader could not load. Check your internet connection.'));
            document.head.append(script);
          });
        }
        const pdfjs=window.pdfjsLib;
        if(!pdfjs) throw new Error('PDF reader is unavailable.');
        pdfjs.GlobalWorkerOptions.workerSrc='https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
        const bytes=await file.arrayBuffer();
        const pdf=await pdfjs.getDocument({data:bytes}).promise;
        const limit=Math.min(pdf.numPages,20), pages=[];
        for(let pageNo=1;pageNo<=limit;pageNo++){
          status.textContent='Extracting page '+pageNo+' of '+limit+'…';
          const page=await pdf.getPage(pageNo);
          const content=await page.getTextContent();
          const line=content.items.map(item=>item.str||'').join(' ').replace(/\s+/g,' ').trim();
          if(line) pages.push('Page '+pageNo+': '+line);
        }
        const extracted=pages.join('\n\n');
        if(!extracted) throw new Error('No selectable text found. This may be a scanned PDF; use the photo reader on individual page images.');
        const area=$('#ocrText');
        if(area){area.value=extracted;area.dispatchEvent(new Event('input',{bubbles:true}));}
        status.textContent='Extracted text from '+pages.length+' page(s). Review it below before solving.';
        notifyUser('PDF text extracted locally. Review it before solving.');
      } catch(error) { status.textContent=error.message||'Could not read this PDF.'; }
      finally {button.disabled=false;}
    });
  }

  // Server-side sampling uses the same safe mathematical parser as the solver.
  function install3DGraph() {
    const page=$('#page-graph');
    if(!page || $('#zentrix3dPanel')) return;
    const panel=make('div','panel graph-panel'); panel.id='zentrix3dPanel'; panel.style.marginTop='14px'; panel.style.padding='16px';
    const heading=make('div','starter-head'); heading.append(make('h2','','3D surface explorer'),make('span','subtle','Drag to rotate'));
    const controls=make('div','graph-controls');
    const expr=make('input','field'); expr.id='zentrix3dExpr'; expr.value='sin(sqrt(x^2+y^2))/sqrt(x^2+y^2)'; expr.placeholder='f(x,y)'; expr.setAttribute('aria-label','Function of x and y');
    const plot=make('button','primary','Plot 3D surface ↗'); plot.type='button';
    controls.append(expr,plot);
    const canvasWrap=make('div','graph-wrap'); canvasWrap.style.height='390px';
    const canvas=make('canvas',''); canvas.id='zentrix3dCanvas'; canvas.setAttribute('role','img'); canvas.setAttribute('aria-label','Interactive three dimensional mathematical surface'); canvas.style.width='100%';canvas.style.height='100%';canvas.style.touchAction='none';
    canvasWrap.append(canvas);
    const note=make('p','subtle','Plots are sampled locally by ZENTRIX. Drag the surface to rotate it. Undefined points and extreme values are clipped.');
    note.style.margin='10px 0 0';
    panel.append(heading,controls,canvasWrap,note); page.append(panel);
    let surface=null, yaw=-0.65, pitch=0.85, dragging=false, lastX=0,lastY=0, request=0;
    const draw=()=>{
      if(!surface)return;
      const rect=canvas.getBoundingClientRect(),dpr=Math.min(window.devicePixelRatio||1,2);
      if(rect.width<10||rect.height<10)return;
      canvas.width=Math.round(rect.width*dpr);canvas.height=Math.round(rect.height*dpr);
      const ctx=canvas.getContext('2d');ctx.scale(dpr,dpr);
      const w=rect.width,h=rect.height;
      const css=getComputedStyle(document.documentElement),line=css.getPropertyValue('--line').trim(),accent=css.getPropertyValue('--accent').trim(),fg=css.getPropertyValue('--muted').trim(),bg=css.getPropertyValue('--surface2').trim();
      ctx.fillStyle=bg;ctx.fillRect(0,0,w,h);
      const xs=surface.x,ys=surface.y,zs=surface.z,rows=zs.length,cols=xs.length;
      const valid=zs.flat().filter(v=>v!==null&&Number.isFinite(v));
      if(!valid.length){ctx.fillStyle=fg;ctx.fillText('No finite surface values in this interval.',14,24);return;}
      const min=Math.min(...valid),max=Math.max(...valid),range=Math.max(1e-9,max-min);
      const project=(x,y,z)=>{
        const nx=(x-(xs[0]+xs.at(-1))/2)/Math.max(1e-9,xs.at(-1)-xs[0])*2;
        const ny=(y-(ys[0]+ys.at(-1))/2)/Math.max(1e-9,ys.at(-1)-ys[0])*2;
        const nz=((z-(min+max)/2)/range)*1.55;
        const cy=Math.cos(yaw),sy=Math.sin(yaw),cp=Math.cos(pitch),sp=Math.sin(pitch);
        const rx=nx*cy-ny*sy, ry=nx*sy+ny*cy;
        const rz=ry*sp+nz*cp, depth=ry*cp-nz*sp;
        const scale=Math.min(w,h)*0.36/(1+depth*0.12);
        return {x:w/2+rx*scale,y:h*0.53-rz*scale,depth};
      };
      // Draw mesh from back to front for a stable wireframe perspective.
      ctx.lineWidth=0.8;ctx.strokeStyle=line;
      for(let i=0;i<rows;i+=2){ctx.beginPath();let pen=false;for(let j=0;j<cols;j++){const z=zs[i][j];if(z===null){pen=false;continue;}const p=project(xs[j],ys[i],z);if(pen)ctx.lineTo(p.x,p.y);else{ctx.moveTo(p.x,p.y);pen=true;}}ctx.stroke();}
      for(let j=0;j<cols;j+=2){ctx.beginPath();let pen=false;for(let i=0;i<rows;i++){const z=zs[i][j];if(z===null){pen=false;continue;}const p=project(xs[j],ys[i],z);if(pen)ctx.lineTo(p.x,p.y);else{ctx.moveTo(p.x,p.y);pen=true;}}ctx.stroke();}
      ctx.fillStyle=accent;ctx.font='12px sans-serif';ctx.fillText('z range: '+min.toPrecision(4)+' to '+max.toPrecision(4),12,18);
      ctx.fillStyle=fg;ctx.fillText('x: '+xs[0]+' to '+xs.at(-1)+'  ·  y: '+ys[0]+' to '+ys.at(-1),12,h-12);
    };
    plot.addEventListener('click',async()=>{
      const id=++request;plot.disabled=true;plot.textContent='Sampling surface…';
      try{
        const r=await fetch('/api/plot3d',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({expr:expr.value,xmin:-5,xmax:5,ymin:-5,ymax:5})});
        const j=await r.json();if(!r.ok)throw new Error(j.detail||'Could not plot this surface.');
        if(id!==request)return;surface=j;draw();notifyUser('3D surface generated.');
      }catch(e){notifyUser(e.message);}
      finally{plot.disabled=false;plot.textContent='Plot 3D surface ↗';}
    });
    canvas.addEventListener('pointerdown',e=>{dragging=true;lastX=e.clientX;lastY=e.clientY;canvas.setPointerCapture(e.pointerId);});
    canvas.addEventListener('pointermove',e=>{if(!dragging)return;yaw+=(e.clientX-lastX)*0.009;pitch=Math.max(-1.35,Math.min(1.35,pitch+(e.clientY-lastY)*0.009));lastX=e.clientX;lastY=e.clientY;draw();});
    canvas.addEventListener('pointerup',()=>dragging=false);canvas.addEventListener('pointercancel',()=>dragging=false);
    window.addEventListener('resize',draw);
    new MutationObserver(()=>{if(page.classList.contains('active'))requestAnimationFrame(draw);}).observe(page,{attributes:true,attributeFilter:['class']});
    plot.click();
  }

  function registerOfflineShell(){
    if(!('serviceWorker' in navigator) || !/^https?:$/.test(location.protocol))return;
    window.addEventListener('load',()=>navigator.serviceWorker.register('/sw.js').catch(()=>{}),{once:true});
  }
  function boot(){installPdfImporter();install3DGraph();registerOfflineShell();}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();