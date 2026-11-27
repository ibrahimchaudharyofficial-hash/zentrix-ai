/* ZENTRIX AI — keyboard-first command palette. */
(() => {
  'use strict';
  const backdrop=document.getElementById('paletteBackdrop');
  const search=document.getElementById('paletteSearch');
  const list=document.getElementById('paletteList');
  if(!backdrop||!search||!list||typeof examples==='undefined')return;

  let activeIndex=0;
  let visible=[];
  const extra=[
    {label:'Focus solver',description:'Jump home and focus the question box',action:'focus-solver',keywords:'question input calculate'},
    {label:'Solve current question',description:'Run the current maths question',action:'solve',keywords:'calculate enter submit'},
    {label:'Clear question',description:'Empty the question box',action:'clear',keywords:'reset delete'},
    {label:'Toggle compact sidebar',description:'Collapse or expand the desktop navigation',action:'sidebar',keywords:'navigation width'},
    {label:'Toggle spacing',description:'Switch between compact and comfortable layout',action:'density',keywords:'layout density'},
    {label:'Toggle fullscreen',description:'Enter or exit fullscreen mode',action:'fullscreen',keywords:'screen expand'},
  ];

  function execute(item){
    closePalette();
    if(item.action==='focus-solver'||item.action==='solve'||item.action==='clear'){
      if(typeof goPage==='function')goPage('home');
      const field=document.getElementById('question');
      if(item.action==='clear'){if(field){field.value='';field.focus();}return;}
      if(item.action==='focus-solver'){if(field)field.focus();return;}
      if(field&&field.value.trim()&&typeof solveQuestion==='function')solveQuestion();
      else if(field){field.focus();if(typeof notify==='function')notify('Enter a question, then run Solve current question.');}
      return;
    }
    if(item.action==='sidebar'){document.getElementById('zentrixSidebarToggle')?.click();return;}
    if(item.action==='density'){document.getElementById('zentrixDensity')?.click();return;}
    if(item.action==='fullscreen'){if(typeof toggleFullscreen==='function')toggleFullscreen();return;}
    if(item.target==='new'){if(typeof newCalculation==='function')newCalculation();return;}
    if(item.target==='theme'){if(typeof toggleTheme==='function')toggleTheme();return;}
    if(item.target&&typeof goPage==='function')goPage(item.target);
  }

  window.filterPalette=function(){
    const q=search.value.trim().toLowerCase();
    const base=examples.map(([label,description,target])=>({label,description,target,keywords:''}));
    const all=base.concat(extra);
    visible=all.filter(item=>(item.label+' '+item.description+' '+item.keywords).toLowerCase().includes(q));
    activeIndex=0;
    list.replaceChildren();
    list.setAttribute('role','listbox');
    search.setAttribute('role','combobox');
    search.setAttribute('aria-autocomplete','list');
    search.setAttribute('aria-controls','paletteList');
    search.setAttribute('aria-expanded',String(visible.length>0));
    if(!visible.length){
      const empty=document.createElement('div');empty.className='palette-empty';empty.textContent='No matching commands. Try another search.';list.append(empty);search.removeAttribute('aria-activedescendant');return;
    }
    visible.forEach((item,index)=>{
      const button=document.createElement('button');
      button.type='button';button.id='zentrix-command-'+index;button.setAttribute('role','option');
      button.setAttribute('aria-selected',String(index===activeIndex));
      button.innerHTML='';
      const title=document.createElement('span');title.className='zentrix-command-title';title.textContent=item.label;
      const description=document.createElement('small');description.className='zentrix-command-description';description.textContent=item.description;
      button.append(title,description);
      button.addEventListener('mouseenter',()=>setActive(index));
      button.addEventListener('click',()=>execute(item));
      list.append(button);
    });
    syncActive();
  };

  function syncActive(){
    [...list.querySelectorAll('button[role="option"]')].forEach((button,index)=>{
      button.setAttribute('aria-selected',String(index===activeIndex));
    });
    const current=list.querySelector('#zentrix-command-'+activeIndex);
    if(current){search.setAttribute('aria-activedescendant',current.id);current.scrollIntoView({block:'nearest'});}
  }
  function setActive(index){if(!visible.length)return;activeIndex=Math.max(0,Math.min(index,visible.length-1));syncActive();}

  document.addEventListener('keydown',event=>{
    if(!backdrop.classList.contains('open'))return;
    if(event.key==='ArrowDown'){event.preventDefault();setActive((activeIndex+1)%visible.length);}
    else if(event.key==='ArrowUp'){event.preventDefault();setActive((activeIndex-1+visible.length)%visible.length);}
    else if(event.key==='Home'&&document.activeElement===search){event.preventDefault();setActive(0);}
    else if(event.key==='End'&&document.activeElement===search){event.preventDefault();setActive(visible.length-1);}
    else if(event.key==='Enter'&&document.activeElement===search&&visible[activeIndex]){event.preventDefault();execute(visible[activeIndex]);}
  });

  const style=document.createElement('style');
  style.textContent=`
    .palette-list button{display:grid;gap:2px;width:100%;border:1px solid transparent}
    .palette-list button[aria-selected="true"]{background:var(--accent-soft);border-color:color-mix(in srgb,var(--accent) 32%,var(--line));color:var(--accent)}
    .zentrix-command-title{font-size:12px;font-weight:700}
    .zentrix-command-description{font-size:10px;color:var(--muted);font-weight:400}
    .palette-empty{padding:18px 10px;text-align:center;color:var(--muted);font-size:11px}
    @media(prefers-reduced-motion:reduce){.palette-list button{transition:none!important}}
  `;
  document.head.append(style);
})();
