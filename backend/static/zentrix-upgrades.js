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
    const preset=make('select','field'); preset.id='zentrix3dPreset'; preset.setAttribute('aria-label','Choose a surface example');
    [['Custom expression',''],['Paraboloid: x² + y²','x^2+y^2'],['Saddle: x² − y²','x^2-y^2'],['Ripple: sin(x) cos(y)','sin(x)*cos(y)'],['Gaussian hill','exp(-(x^2+y^2)/4)'],['Sinc surface','sin(sqrt(x^2+y^2))/sqrt(x^2+y^2)']].forEach(([label,value])=>{const o=make('option','',label);o.value=value;preset.append(o);});
    preset.addEventListener('change',()=>{if(preset.value)expr.value=preset.value;});
    const bounds=make('div','graph-controls');
    const boundInput=(id,label,value)=>{const wrap=make('label','subtle',label);const input=make('input','field');input.type='number';input.step='any';input.value=String(value);input.id=id;input.setAttribute('aria-label',label);wrap.append(input);bounds.append(wrap);return input;};
    const xmin=boundInput('zentrix3dXmin','X minimum',-5),xmax=boundInput('zentrix3dXmax','X maximum',5),ymin=boundInput('zentrix3dYmin','Y minimum',-5),ymax=boundInput('zentrix3dYmax','Y maximum',5);
    const plot=make('button','primary','Plot 3D surface ↗'); plot.type='button';
    const actions=make('div','graph-controls');
    const reset=make('button','softbtn','Reset view');reset.type='button';
    const png=make('button','softbtn','Download PNG');png.type='button';png.disabled=true;
    const csv=make('button','softbtn','Download CSV data');csv.type='button';csv.disabled=true;
    actions.append(reset,png,csv);
    controls.append(expr,preset,plot);
    const canvasWrap=make('div','graph-wrap'); canvasWrap.style.height='390px';
    const canvas=make('canvas',''); canvas.id='zentrix3dCanvas'; canvas.setAttribute('role','img'); canvas.setAttribute('aria-label','Interactive three dimensional mathematical surface'); canvas.style.width='100%';canvas.style.height='100%';canvas.style.touchAction='none';
    canvasWrap.append(canvas);
    const note=make('p','subtle','Plots are sampled locally by ZENTRIX. Drag the surface to rotate it. Undefined points and extreme values are clipped.');
    note.style.margin='10px 0 0';
    panel.append(heading,controls,bounds,actions,canvasWrap,note); page.append(panel);
    let surface=null, yaw=-0.65, pitch=0.85, dragging=false, lastX=0,lastY=0, request=0;
    const download=(blob,name)=>{const url=URL.createObjectURL(blob);const a=make('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);};
    reset.addEventListener('click',()=>{yaw=-0.65;pitch=0.85;draw();});
    png.addEventListener('click',()=>{if(!surface)return;canvas.toBlob(blob=>{if(blob)download(blob,'zentrix-3d-surface.png');});});
    csv.addEventListener('click',()=>{if(!surface)return;const rows=['x,y,z'];for(let i=0;i<surface.y.length;i++)for(let j=0;j<surface.x.length;j++){const z=surface.z[i][j];rows.push([surface.x[j],surface.y[i],z===null?'':z].join(','));}download(new Blob([rows.join('\n')],{type:'text/csv;charset=utf-8'}),'zentrix-3d-surface.csv');});
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
        const r=await fetch('/api/plot3d',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({expr:expr.value,xmin:Number(xmin.value),xmax:Number(xmax.value),ymin:Number(ymin.value),ymax:Number(ymax.value)})});
        const j=await r.json();if(!r.ok)throw new Error(j.detail||'Could not plot this surface.');
        if(id!==request)return;surface=j;draw();png.disabled=false;csv.disabled=false;notifyUser('3D surface generated.');
      }catch(e){notifyUser(e.message);}
      finally{plot.disabled=false;plot.textContent='Plot 3D surface ↗';}
    });
    canvas.addEventListener('pointerdown',e=>{dragging=true;lastX=e.clientX;lastY=e.clientY;canvas.setPointerCapture(e.pointerId);});
    canvas.addEventListener('pointermove',e=>{if(!dragging)return;yaw+=(e.clientX-lastX)*0.009;pitch=Math.max(-1.35,Math.min(1.35,pitch+(e.clientY-lastY)*0.009));lastX=e.clientX;lastY=e.clientY;draw();});
    canvas.addEventListener('pointerup',()=>dragging=false);canvas.addEventListener('pointercancel',()=>dragging=false);
    window.addEventListener('resize',draw);
    new MutationObserver(()=>{if(page.classList.contains('active')){if(!surface&&!plot.disabled)plot.click();else requestAnimationFrame(draw);}}).observe(page,{attributes:true,attributeFilter:['class']});
  }


  // Upgrade the existing 2D plot with an adjustable vertical window and exports.
  function install2DGraphTools() {
    const page=$('#page-graph'), canvas=$('#graphCanvas'), panel=canvas?.closest('.graph-panel');
    if(!page||!canvas||!panel||$('#zentrix2dTools')) return;
    const tools=make('div','graph-controls'); tools.id='zentrix2dTools'; tools.style.marginTop='12px';
    const autoWrap=make('label','subtle','Auto-fit Y'); autoWrap.style.display='flex';autoWrap.style.alignItems='center';autoWrap.style.gap='7px';
    const auto=make('input');auto.type='checkbox';auto.checked=true;auto.id='zentrix2dAuto';autoWrap.append(auto);
    const yMin=make('input','field');yMin.type='number';yMin.step='any';yMin.value='-5';yMin.id='zentrix2dYmin';yMin.setAttribute('aria-label','Y minimum');yMin.disabled=true;
    const yMax=make('input','field');yMax.type='number';yMax.step='any';yMax.value='5';yMax.id='zentrix2dYmax';yMax.setAttribute('aria-label','Y maximum');yMax.disabled=true;
    const png=make('button','softbtn','Download 2D PNG');png.type='button';png.disabled=true;
    const csv=make('button','softbtn','Download 2D CSV');csv.type='button';csv.disabled=true;
    const status=make('span','subtle','Auto-fit shows the useful vertical range.');status.id='zentrix2dStatus';
    tools.append(autoWrap,yMin,yMax,png,csv,status);panel.append(tools);
    let data=null, request=0;
    const download=(blob,name)=>{const url=URL.createObjectURL(blob),a=make('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);};
    function rangeFor(values){
      const finite=values.filter(v=>Number.isFinite(v)).sort((a,b)=>a-b);
      if(!finite.length) return null;
      const lo=finite[Math.floor((finite.length-1)*0.02)],hi=finite[Math.ceil((finite.length-1)*0.98)];
      const pad=Math.max((hi-lo)*0.08,Math.abs(hi||lo||1)*0.04,0.1);
      return [lo-pad,hi+pad];
    }
    function draw(){
      if(!data)return;
      const rect=canvas.getBoundingClientRect(),dpr=Math.min(window.devicePixelRatio||1,2);
      if(rect.width<10||rect.height<10)return;
      const w=Math.max(320,Math.floor(rect.width)),h=Math.max(180,Math.floor(rect.height));
      canvas.width=Math.round(w*dpr);canvas.height=Math.round(h*dpr);
      const g=canvas.getContext('2d');g.setTransform(dpr,0,0,dpr,0,0);
      const css=getComputedStyle(document.documentElement),grid=css.getPropertyValue('--line').trim(),fg=css.getPropertyValue('--muted').trim(),accent=css.getPropertyValue('--accent').trim(),bg=css.getPropertyValue('--surface2').trim();
      g.fillStyle=bg;g.fillRect(0,0,w,h);
      let yr=auto.checked?rangeFor(data.y):[Number(yMin.value),Number(yMax.value)];
      if(!yr||!yr.every(Number.isFinite)||yr[0]>=yr[1]){status.textContent='Enter a valid increasing Y range.';return;}
      const xmin=data.x[0],xmax=data.x[data.x.length-1],X=x=>(x-xmin)/(xmax-xmin)*w,Y=y=>h-(y-yr[0])/(yr[1]-yr[0])*h;
      g.strokeStyle=grid;g.lineWidth=1;g.font='10px sans-serif';g.fillStyle=fg;
      for(let i=0;i<=10;i++){const xx=i*w/10,yy=i*h/10;g.beginPath();g.moveTo(xx,0);g.lineTo(xx,h);g.stroke();g.beginPath();g.moveTo(0,yy);g.lineTo(w,yy);g.stroke();if(i%2===0){g.fillText((xmin+(xmax-xmin)*i/10).toPrecision(3),Math.max(2,xx-12),h-5);g.fillText((yr[1]-(yr[1]-yr[0])*i/10).toPrecision(3),4,Math.max(10,yy-3));}}
      g.strokeStyle=fg;g.lineWidth=1.3;
      if(xmin<=0&&xmax>=0){g.beginPath();g.moveTo(X(0),0);g.lineTo(X(0),h);g.stroke();}
      if(yr[0]<=0&&yr[1]>=0){g.beginPath();g.moveTo(0,Y(0));g.lineTo(w,Y(0));g.stroke();}
      g.strokeStyle=accent;g.lineWidth=2.5;g.beginPath();let pen=false;
      data.x.forEach((x,i)=>{const y=data.y[i];if(y===null||!Number.isFinite(y)||y<yr[0]||y>yr[1]){pen=false;return;}if(pen)g.lineTo(X(x),Y(y));else{g.moveTo(X(x),Y(y));pen=true;}});
      g.stroke();status.textContent='Y range: '+yr[0].toPrecision(4)+' to '+yr[1].toPrecision(4)+' · '+data.x.length+' samples';
    }
    async function plot(){
      const id=++request,expr=$('#fx').value.trim(),xmin=Number($('#xmin').value),xmax=Number($('#xmax').value);
      if(!expr){status.textContent='Enter a function of x.';return;}
      if(!Number.isFinite(xmin)||!Number.isFinite(xmax)||xmin>=xmax||xmax-xmin>100000){status.textContent='Choose a valid increasing X interval.';return;}
      status.textContent='Sampling function…';
      try{
        const response=await fetch('/api/plot',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({expr,xmin,xmax})});
        const result=await response.json();if(!response.ok)throw new Error(result.detail||'Unable to plot this function.');
        if(id!==request)return;data=result;draw();png.disabled=false;csv.disabled=false;
      }catch(error){status.textContent=error.message;}
    }
    auto.addEventListener('change',()=>{yMin.disabled=auto.checked;yMax.disabled=auto.checked;draw();});
    [yMin,yMax].forEach(input=>input.addEventListener('change',draw));
    png.addEventListener('click',()=>{if(data)canvas.toBlob(blob=>{if(blob)download(blob,'zentrix-2d-graph.png');});});
    csv.addEventListener('click',()=>{if(!data)return;const rows=['x,y'];data.x.forEach((x,i)=>rows.push([x,data.y[i]===null?'':data.y[i]].join(',')));download(new Blob([rows.join('\n')],{type:'text/csv;charset=utf-8'}),'zentrix-2d-graph.csv');});
    const oldButton=panel.querySelector('button[onclick*="plotFunction"]');
    if(oldButton){const button=oldButton.cloneNode(true);button.removeAttribute('onclick');button.addEventListener('click',plot);oldButton.replaceWith(button);}
    window.plotFunction=plot;
    window.setGraph=(expression)=>{$('#fx').value=expression;plot();};
    $('#fx').addEventListener('keydown',e=>{if(e.key==='Enter')plot();});
    window.addEventListener('resize',()=>{if(page.classList.contains('active'))draw();},{passive:true});
    new MutationObserver(()=>{if(page.classList.contains('active')){if(!data)plot();else requestAnimationFrame(draw);}}).observe(page,{attributes:true,attributeFilter:['class']});
  }


  // Scanned PDF OCR: render selected pages locally and reuse the app's Tesseract worker.
  function installScannedPdfOcr() {
    const host=$('#zentrixPdfImport');
    if(!host||$('#zentrixPdfOcrButton'))return;
    const input=host.querySelector('input[type="file"]');
    if(!input)return;
    const button=make('button','softbtn','OCR scanned PDF pages');
    button.type='button';button.id='zentrixPdfOcrButton';
    const status=host.querySelector('span');
    host.append(button);
    button.addEventListener('click',async()=>{
      const file=input.files&&input.files[0];
      if(!file){if(status)status.textContent='Choose a PDF file first.';return;}
      if(file.size>15*1024*1024){if(status)status.textContent='PDF is too large. Maximum size is 15 MB.';return;}
      button.disabled=true;
      try{
        if(!window.pdfjsLib){
          if(status)status.textContent='Loading PDF reader…';
          await new Promise((resolve,reject)=>{
            const script=document.createElement('script');
            script.src='https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js';
            script.onload=resolve;script.onerror=()=>reject(new Error('PDF reader could not load. Check your internet connection.'));
            document.head.append(script);
          });
        }
        const pdfjs=window.pdfjsLib;
        if(!pdfjs)throw new Error('PDF reader is unavailable.');
        pdfjs.GlobalWorkerOptions.workerSrc='https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
        if(typeof getOcrWorker!=='function')throw new Error('The OCR engine is not available in this build.');
        const pdf=await pdfjs.getDocument({data:await file.arrayBuffer()}).promise;
        const limit=Math.min(pdf.numPages,8),worker=await getOcrWorker(),pages=[];
        for(let n=1;n<=limit;n++){
          if(status)status.textContent='Rendering and recognising scanned page '+n+' of '+limit+'…';
          const page=await pdf.getPage(n),base=page.getViewport({scale:1});
          const scale=Math.min(1.8,1500/base.width,Math.sqrt(2200000/(base.width*base.height)));
          const viewport=page.getViewport({scale:Math.max(.7,scale)});
          const canvas=document.createElement('canvas');
          canvas.width=Math.max(1,Math.floor(viewport.width));canvas.height=Math.max(1,Math.floor(viewport.height));
          const ctx=canvas.getContext('2d',{willReadFrequently:true});
          if(!ctx)throw new Error('This browser cannot render PDF pages for OCR.');
          await page.render({canvasContext:ctx,viewport}).promise;
          await worker.setParameters({tessedit_pageseg_mode:'6',preserve_interword_spaces:'1',user_defined_dpi:'240'});
          const result=await worker.recognize(canvas);
          const raw=(result.data.text||'').replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g,'').trim();
          if(raw)pages.push('Page '+n+': '+raw);
          canvas.width=1;canvas.height=1;
        }
        const extracted=pages.join('\n\n').replace(/[‐‑‒–—]/g,'-').replace(/[×✕]/g,'*').replace(/[÷]/g,'/');
        const area=$('#ocrText');
        if(area){area.value=extracted;area.dispatchEvent(new Event('input',{bubbles:true}));}
        const use=$('#useOcrBtn');if(use)use.disabled=!extracted;
        if(status)status.textContent=extracted?'OCR finished on this device for '+pages.length+' of '+limit+' page(s). Review symbols and fractions before solving.':'No readable text found in the scanned pages.';
        notifyUser(extracted?'Scanned PDF recognised locally. Review the text before solving.':'No readable text found in this PDF.');
      }catch(error){if(status)status.textContent=error.message||'Scanned PDF OCR failed.';}
      finally{button.disabled=false;}
    });
  }

  // A lightweight equation toolbar inserts safe, editable math syntax into the solver.
  function installEquationEditor() {
    const composer=$('#composer'),field=$('#question');
    if(!composer||!field||$('#zentrixEquationEditor'))return;
    const panel=make('div','zentrix-equation-editor');panel.id='zentrixEquationEditor';
    const head=make('div','zentrix-equation-head');
    head.append(make('strong','','Equation editor'),make('span','subtle','Insert a symbol or template'));
    const toolbar=make('div','zentrix-equation-tools');
    const items=[
      ['Fraction','()/()'],['Power','^()'],['Square root','sqrt()'],['π','pi'],['∞','oo'],
      ['×','*'],['÷','/'],['≤','<='],['≥','>='],['≠','!='],['±','+/-'],
      ['sin','sin()'],['cos','cos()'],['tan','tan()'],['log','log()'],['eˣ','exp()'],
      ['Absolute','abs()'],['Parentheses','()']
    ];
    items.forEach(([label,value])=>{
      const b=make('button','softbtn',label);b.type='button';b.title='Insert '+label;b.addEventListener('click',()=>{
        const start=field.selectionStart??field.value.length,end=field.selectionEnd??start;
        const insert=value,open=insert.indexOf('()'),cursor=open>=0?start+open+1:start+insert.length;
        field.setRangeText(insert,start,end,'end');field.focus();field.setSelectionRange(cursor,cursor);
        field.dispatchEvent(new Event('input',{bubbles:true}));
      });toolbar.append(b);
    });
    const preview=make('div','zentrix-equation-preview');preview.id='zentrixEquationPreview';preview.setAttribute('aria-live','polite');
    panel.append(head,toolbar,preview);
    field.parentElement.insertBefore(panel,field);
    const render=()=>{
      const value=field.value.trim();
      preview.replaceChildren();
      if(!value){preview.textContent='Live preview appears here as you type.';return;}
      if(window.katex){
        try{window.katex.render(value.replace(/\^\(([^()]*)\)/g,'^{($1)}').replace(/\bpi\b/g,'\\pi').replace(/\boo\b/g,'\\infty').replace(/\*/g,'\\cdot '),preview,{throwOnError:false,displayMode:true});}
        catch{preview.textContent=value;}
      }else preview.textContent=value;
    };
    field.addEventListener('input',render);render();
  }

  // Local progress dashboard: no account, analytics service, or external storage required.
  function installProgressDashboard() {
    const page=$('#page-learn'),profile=$('#learningProfile');
    if(!page||!profile||$('#zentrixProgressDashboard'))return;
    const card=make('section','panel zentrix-progress');card.id='zentrixProgressDashboard';
    const heading=make('div','starter-head');heading.append(make('h2','','Your progress dashboard'),make('span','subtle','Private · saved on this device'));
    const stats=make('div','zentrix-progress-stats');
    const weekly=make('div','zentrix-weekly');
    const topics=make('div','zentrix-topic-progress');
    const actions=make('div','photo-controls');
    const exportBtn=make('button','softbtn','Export progress CSV');exportBtn.type='button';
    const clearBtn=make('button','softbtn','Reset progress');clearBtn.type='button';
    const note=make('p','subtle','Tracks practice answers and completed exams on this device. Existing solver history is counted separately.');
    actions.append(exportBtn,clearBtn);card.append(heading,stats,weekly,topics,actions,note);
    profile.parentElement.insertBefore(card,profile.nextSibling);
    const key='zentrix_progress_v1';
    const read=()=>{try{const v=JSON.parse(localStorage.getItem(key)||'{}');return {practice:Array.isArray(v.practice)?v.practice:[],exams:Array.isArray(v.exams)?v.exams:[]};}catch{return {practice:[],exams:[]};}};
    const write=v=>{try{localStorage.setItem(key,JSON.stringify(v));}catch{}};
    const recordPractice=entry=>{const v=read();v.practice.push(entry);v.practice=v.practice.slice(-1000);write(v);render();};
    const recordExam=entry=>{const v=read();v.exams.push(entry);v.exams=v.exams.slice(-200);write(v);render();};
    const fmt=n=>Number(n||0).toLocaleString();
    function render(){
      const v=read(),correct=v.practice.filter(x=>x.correct).length,total=v.practice.length,accuracy=total?Math.round(correct*100/total):0;
      let examBest=0;v.exams.forEach(x=>examBest=Math.max(examBest,Number(x.score)||0));
      let historyCount=0;try{const h=JSON.parse(localStorage.getItem('zentrix_history')||'[]');historyCount=Array.isArray(h)?h.length:0;}catch{}
      stats.replaceChildren();
      [[fmt(total),'Practice attempts'],[accuracy+'%','Practice accuracy'],[fmt(v.exams.length),'Exams completed'],[examBest+'%','Best exam'],[fmt(historyCount),'Saved calculations']].forEach(([value,label])=>{const tile=make('div','zentrix-progress-stat');tile.append(make('strong','',value),make('span','',label));stats.append(tile);});
      weekly.replaceChildren(make('h3','','Last 7 days'));
      const today=new Date();const days=[];
      for(let back=6;back>=0;back--){const d=new Date(today);d.setHours(0,0,0,0);d.setDate(d.getDate()-back);const iso=d.toISOString().slice(0,10);const rows=v.practice.filter(x=>(x.date||'').slice(0,10)===iso);days.push({label:d.toLocaleDateString(undefined,{weekday:'short'}),count:rows.length,correct:rows.filter(x=>x.correct).length});}
      const max=Math.max(1,...days.map(x=>x.count));
      const bars=make('div','zentrix-week-bars');
      days.forEach(d=>{const col=make('div','zentrix-week-day');const bar=make('div','zentrix-week-bar');bar.style.height=Math.max(4,d.count/max*76)+'px';bar.title=d.count+' attempts · '+d.correct+' correct';const count=make('small','',String(d.count));const label=make('span','',d.label);col.append(count,bar,label);bars.append(col);});
      weekly.append(bars);
      topics.replaceChildren(make('h3','','Topic breakdown'));
      const grouped={};v.practice.forEach(x=>{const k=x.topic||'Mixed';grouped[k]??={total:0,correct:0};grouped[k].total++;if(x.correct)grouped[k].correct++;});
      const entries=Object.entries(grouped).sort((a,b)=>b[1].total-a[1].total);
      if(!entries.length)topics.append(make('p','subtle','Complete a practice question to start building your topic profile.'));
      entries.forEach(([name,data])=>{const row=make('div','zentrix-topic-row');const label=make('span','',name);const pct=Math.round(data.correct/data.total*100);const value=make('b','',pct+'% · '+data.total+' attempts');const track=make('div','zentrix-topic-track');const fill=make('span','');fill.style.width=pct+'%';track.append(fill);row.append(label,value,track);topics.append(row);});
    }
    exportBtn.addEventListener('click',()=>{
      const v=read(),rows=['type,date,topic,correct,score,difficulty'];
      v.practice.forEach(x=>rows.push(['practice',x.date,x.topic,x.correct,'',x.difficulty].map(csvCell).join(',')));
      v.exams.forEach(x=>rows.push(['exam',x.date,x.subject,'',x.score,''].map(csvCell).join(',')));
      const blob=new Blob([rows.join('\n')],{type:'text/csv;charset=utf-8'}),url=URL.createObjectURL(blob),a=make('a');
      a.href=url;a.download='zentrix-learning-progress.csv';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
    });
    clearBtn.addEventListener('click',()=>{if(!confirm('Reset saved practice and exam progress on this device? This does not delete solver history.'))return;localStorage.removeItem(key);render();notifyUser('Learning progress reset.');});
    function csvCell(value){const s=String(value??'');return '"'+s.replace(/"/g,'""')+'"';}
    let lastPracticeQuestion='';
    const originalNewPractice=window.newPractice;
    if(typeof originalNewPractice==='function')window.newPractice=async function(){lastPracticeQuestion='';return originalNewPractice.apply(this,arguments);};
    const originalCheckPractice=window.checkPractice;
    if(typeof originalCheckPractice==='function')window.checkPractice=async function(){
      await originalCheckPractice.apply(this,arguments);
      const feedback=$('#practiceFeedback')?.textContent||'',question=$('#practiceQuestion')?.textContent||'';
      if((feedback.startsWith('✓')||feedback.startsWith('✕'))&&question&&question!==lastPracticeQuestion){
        lastPracticeQuestion=question;
        recordPractice({date:new Date().toISOString(),topic:$('#practiceTopic')?.value||'Mixed',difficulty:$('#practiceDifficulty')?.value||'medium',correct:feedback.startsWith('✓'),question});
      }
    };
    const originalNextExam=window.nextExamQuestion;
    if(typeof originalNextExam==='function')window.nextExamQuestion=function(){
      const before=Number(examStats()?.tests)||0;
      const result=originalNextExam.apply(this,arguments);
      const after=Number(examStats()?.tests)||0;
      if(after>before){
        const scoreText=$('#examResult .exam-result-score')?.textContent||'0%';
        recordExam({date:new Date().toISOString(),subject:$('#examSubject')?.value||'Mixed',score:Number.parseInt(scoreText,10)||0});
      }
      return result;
    };
    window.zentrixProgressRefresh=render;
    render();
  }

  function installUpgradeStyles(){
    if($('#zentrixUpgradeStyles'))return;
    const style=make('style');style.id='zentrixUpgradeStyles';
    style.textContent=`
      .zentrix-equation-editor{border:1px solid var(--line);background:var(--surface2);border-radius:12px;padding:10px;margin:8px 0 10px}
      .zentrix-equation-head{display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:8px}
      .zentrix-equation-tools{display:flex;gap:6px;flex-wrap:wrap}
      .zentrix-equation-tools button{padding:5px 9px;font-size:12px}
      .zentrix-equation-preview{min-height:34px;margin-top:9px;padding:7px 10px;border-radius:8px;background:var(--surface);color:var(--text);overflow-x:auto}
      .zentrix-progress{padding:18px;margin-top:18px}
      .zentrix-progress-stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(115px,1fr));gap:9px;margin:12px 0}
      .zentrix-progress-stat{padding:12px;border:1px solid var(--line);border-radius:10px;background:var(--surface2);display:flex;flex-direction:column;gap:3px}
      .zentrix-progress-stat strong{font-size:22px;color:var(--text)}.zentrix-progress-stat span,.zentrix-week-day span{font-size:11px;color:var(--muted)}
      .zentrix-weekly,.zentrix-topic-progress{margin-top:16px}.zentrix-weekly h3,.zentrix-topic-progress h3{font-size:13px;margin:0 0 10px}
      .zentrix-week-bars{display:grid;grid-template-columns:repeat(7,1fr);gap:8px;align-items:end;min-height:110px;padding:8px;background:var(--surface2);border-radius:10px}
      .zentrix-week-day{display:flex;flex-direction:column;align-items:center;justify-content:end;gap:5px;min-width:0}
      .zentrix-week-day small{font-size:10px;color:var(--muted)}.zentrix-week-day span{font-size:10px}
      .zentrix-week-bar{width:min(26px,70%);min-height:4px;border-radius:5px 5px 2px 2px;background:var(--accent);opacity:.8}
      .zentrix-topic-row{display:grid;grid-template-columns:minmax(70px,1fr) auto;gap:5px 12px;align-items:center;padding:8px 0;border-bottom:1px solid var(--line);font-size:12px}
      .zentrix-topic-row b{font-size:11px;color:var(--muted)}.zentrix-topic-track{grid-column:1/-1;height:6px;border-radius:8px;background:var(--surface3);overflow:hidden}
      .zentrix-topic-track span{display:block;height:100%;background:var(--mint);border-radius:8px}
      @media(max-width:600px){.zentrix-equation-head{align-items:flex-start;flex-direction:column}.zentrix-progress{padding:12px}}
    `;
    document.head.append(style);
  }

  function registerOfflineShell(){
    if(!('serviceWorker' in navigator) || !/^https?:$/.test(location.protocol))return;
    window.addEventListener('load',()=>navigator.serviceWorker.register('/sw.js').catch(()=>{}),{once:true});
  }
  function boot(){installUpgradeStyles();installPdfImporter();installScannedPdfOcr();installEquationEditor();installProgressDashboard();install2DGraphTools();install3DGraph();registerOfflineShell();}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();