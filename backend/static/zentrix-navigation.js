/* ZENTRIX AI — navigation refinement, compact sidebar and keyboard-first controls. */
(() => {
  'use strict';
  const root=document.documentElement,sidebar=document.getElementById('sidebar');
  if(!sidebar||document.getElementById('zentrixSidebarToggle'))return;
  const desktop=()=>window.matchMedia('(min-width:721px)').matches;
  const saved=()=>{try{return localStorage.getItem('zentrix_sidebar')==='collapsed'}catch{return false}};
  function setCollapsed(value){
    const collapsed=!!value&&desktop();
    root.dataset.sidebar=collapsed?'collapsed':'expanded';
    root.style.setProperty('--sidebar',collapsed?'76px':'208px');
    const btn=document.getElementById('zentrixSidebarToggle');
    if(btn){btn.setAttribute('aria-expanded',String(!collapsed));btn.setAttribute('aria-label',collapsed?'Expand sidebar':'Collapse sidebar');btn.title=collapsed?'Expand sidebar':'Collapse sidebar';btn.textContent=collapsed?'»':'«';}
    sidebar.querySelectorAll('.nav button').forEach(b=>{if(!b.dataset.fullLabel)b.dataset.fullLabel=b.textContent.trim();b.title=b.dataset.fullLabel;});
    try{localStorage.setItem('zentrix_sidebar',collapsed?'collapsed':'expanded')}catch{}
  }
  const brand=sidebar.querySelector('.brand');
  if(brand){const btn=document.createElement('button');btn.type='button';btn.id='zentrixSidebarToggle';btn.className='zentrix-sidebar-toggle';btn.addEventListener('click',()=>setCollapsed(root.dataset.sidebar!=='collapsed'));brand.append(btn);}
  const style=document.createElement('style');
  style.textContent=`
    @media(min-width:721px){
      .sidebar{transition:width .22s ease,padding .22s ease}.main{transition:margin-left .22s ease}
      [data-sidebar=collapsed] .sidebar{width:76px;padding:14px 9px}
      [data-sidebar=collapsed] .brand{justify-content:center;padding:2px 0 17px}
      [data-sidebar=collapsed] .brand>div:not(.brandmark),[data-sidebar=collapsed] .navlabel,[data-sidebar=collapsed] .local-card,[data-sidebar=collapsed] .sidebottom>span{display:none}
      [data-sidebar=collapsed] .brandmark{width:42px;height:42px}
      [data-sidebar=collapsed] .newbtn{font-size:0;min-height:42px;padding:8px}
      [data-sidebar=collapsed] .newbtn::before{content:"＋";font-size:19px}
      [data-sidebar=collapsed] .nav button{justify-content:center;gap:0;padding:10px 4px;font-size:0;min-height:43px}
      [data-sidebar=collapsed] .navicon{width:auto;font-size:18px}
      [data-sidebar=collapsed] .sidebottom{justify-content:center}
      .zentrix-sidebar-toggle{margin-left:auto;width:27px;height:27px;flex:0 0 27px;border:1px solid var(--line);border-radius:8px;background:var(--surface2);color:var(--muted);font-size:17px;line-height:1}
      [data-sidebar=collapsed] .zentrix-sidebar-toggle{position:absolute;right:8px;top:57px}
    }
    @media(max-width:720px){.zentrix-sidebar-toggle{display:none}}
    @media(max-width:560px){.topbar .engine-pill{display:none}.top-actions{gap:5px}.top-actions #accountButton{font-size:0;min-width:38px}.top-actions #accountButton::before{content:"⇧";font-size:16px}}
    @media(prefers-reduced-motion:reduce){.sidebar,.main{transition:none!important}}
  `;
  document.head.append(style);setCollapsed(saved());
  window.addEventListener('resize',()=>{if(!desktop()&&root.dataset.sidebar==='collapsed'){root.dataset.sidebar='expanded';root.style.setProperty('--sidebar','252px')}else if(desktop())setCollapsed(saved())},{passive:true});
  document.addEventListener('keydown',event=>{
    if(event.altKey&&!event.ctrlKey&&!event.metaKey&&/^[1-9]$/.test(event.key)){
      const pages=['home','matrix','graph','definitions','exam','learn','arcade','auditor','coach'],page=pages[Number(event.key)-1];
      if(page&&typeof window.goPage==='function'){event.preventDefault();window.goPage(page);}
    }
    if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==='b'&&!event.shiftKey&&desktop()){event.preventDefault();setCollapsed(root.dataset.sidebar!=='collapsed');}
    if((event.ctrlKey||event.metaKey)&&event.key==='Enter'){
      const question=document.getElementById('question');
      if(question&&document.activeElement===question&&typeof window.solveQuestion==='function'){event.preventDefault();window.solveQuestion();}
    }
  });
  const crumb=document.getElementById('crumbTitle');
  if(crumb){const update=()=>{const active=document.querySelector('.nav button.active');if(active)crumb.textContent=active.dataset.fullLabel||active.textContent.trim();};
    sidebar.addEventListener('click',event=>{if(event.target.closest('.nav button'))setTimeout(update,0)});
    document.querySelectorAll('.starter[onclick*="goPage"]').forEach(b=>b.addEventListener('click',()=>setTimeout(update,0)));
  }
})();
