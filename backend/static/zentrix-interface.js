/* ZENTRIX AI — cohesive colour themes and accessible, friendlier controls. */
(() => {
  'use strict';
  const $=(s)=>document.querySelector(s);
  const palettes={
    lavender:{light:['#f7f6ff','#ffffff','#efedff','#e5e2fb','#dedaf8','#4c4770','#77718f','#9b95ad','#7568c9','#eeeaff','#a9c9f2','#9bd8c5'],dark:['#111321','#191c2d','#22263b','#2b3048','#343a55','#f0efff','#a9adc7','#858aa8','#b6a8ff','#302b50','#83baf0','#80d5bd']},
    ocean:{light:['#f2f9ff','#ffffff','#e8f4ff','#dceeff','#d0e6fa','#243d55','#617b91','#8ba1b4','#347fb5','#e3f2ff','#8bc6ed','#8bd5c2'],dark:['#101923','#172432','#1e3041','#263c50','#304a61','#eef7ff','#a6bfd2','#7f9cb2','#75b9ec','#203b52','#72bce9','#75d1ba']},
    sage:{light:['#f5faf6','#ffffff','#eaf4ec','#deeee1','#d2e6d6','#354b3b','#6e8373','#96a79a','#4c8b65','#e5f3e9','#a6cdb4','#8bd2bd'],dark:['#111b16','#19271e','#22342a','#2b4134','#354e3f','#eff8f0','#adbfaf','#829a87','#85c99a','#263e30','#8bc7a2','#75d3bd']},
    rose:{light:['#fff7fa','#ffffff','#fff0f5','#f8e4ed','#f0d7e3','#503846','#806c79','#a38e9b','#b46e91','#f9e9f1','#b8c7f1','#9bd7c8'],dark:['#1c141c','#291d29','#352638','#423044','#513a50','#fff0f8','#c3aebe','#9b8798','#e3a0c2','#452b40','#9eafe9','#85d2bf']}
  };
  const keys=['bg','surface','surface2','surface3','line','text','muted','muted2','accent','accentSoft','blue','mint'];
  const root=document.documentElement;
  function applyPalette(name){
    const p=palettes[name]||palettes.lavender;
    root.dataset.palette=name in palettes?name:'lavender';
    const dark=root.dataset.theme==='dark';
    const values=dark?p.dark:p.light;
    keys.forEach((key,i)=>root.style.setProperty('--'+key,values[i]));
    const meta=$('meta[name="theme-color"]');if(meta)meta.content=values[0];
    try{localStorage.setItem('zentrix_palette',root.dataset.palette)}catch{}
    const picker=$('#zentrixPalette');if(picker)picker.value=root.dataset.palette;
  }
  function applyDensity(compact){
    root.dataset.density=compact?'compact':'comfortable';
    try{localStorage.setItem('zentrix_density',compact?'compact':'comfortable')}catch{}
    const b=$('#zentrixDensity');if(b){b.setAttribute('aria-pressed',String(compact));b.textContent=compact?'Compact spacing':'Comfortable spacing';}
  }
  function mount(){
    const actions=$('.top-actions');if(!actions||$('#zentrixAppearance'))return;
    const wrap=document.createElement('div');wrap.id='zentrixAppearance';wrap.className='zentrix-appearance';
    const label=document.createElement('label');label.htmlFor='zentrixPalette';label.textContent='Colour theme';
    const select=document.createElement('select');select.id='zentrixPalette';select.className='field';select.setAttribute('aria-label','Choose colour theme');
    [['lavender','Soft lavender'],['ocean','Ocean blue'],['sage','Sage green'],['rose','Rose pink']].forEach(([v,t])=>{const o=document.createElement('option');o.value=v;o.textContent=t;select.append(o)});
    select.addEventListener('change',()=>applyPalette(select.value));
    const density=document.createElement('button');density.type='button';density.id='zentrixDensity';density.className='softbtn';density.addEventListener('click',()=>applyDensity(root.dataset.density!=='compact'));
    wrap.append(label,select,density);
    const themeButton=actions.querySelector('button[onclick="toggleTheme()"]');
    if(themeButton)themeButton.insertAdjacentElement('beforebegin',wrap);else actions.append(wrap);
    applyPalette(root.dataset.palette||'lavender');
    applyDensity(root.dataset.density==='compact');
  }
  function styles(){
    if($('#zentrixInterfaceStyles'))return;
    const s=document.createElement('style');s.id='zentrixInterfaceStyles';
    s.textContent=`
      :root{--radius-control:12px;--control-height:42px;--focus-ring:color-mix(in srgb,var(--accent) 48%,transparent)}
      body{background:radial-gradient(ellipse at 82% -12%,color-mix(in srgb,var(--accent) 11%,transparent),transparent 42%),var(--bg);transition:background-color .2s,color .2s}
      .panel,.composer,.usage-card,.starter,.settings-card,.local-card,.result-card{border-color:var(--line)}
      button,.field,input,select,textarea{accent-color:var(--accent)}
      button{min-height:38px}
      .primary{min-height:42px;padding:10px 18px;background:linear-gradient(115deg,color-mix(in srgb,var(--accent) 90%,#fff),color-mix(in srgb,var(--accent) 72%,var(--blue)));box-shadow:0 5px 14px color-mix(in srgb,var(--accent) 18%,transparent)}
      .softbtn,.chip,.actionbtn,.iconbtn{min-height:40px;border-radius:var(--radius-control);transition:background .16s,border-color .16s,color .16s,transform .16s}
      .softbtn,.chip,.actionbtn{padding:9px 13px;color:var(--text);background:var(--surface2);border-color:var(--line)}
      .softbtn:hover,.chip:hover,.actionbtn:hover{background:var(--accent-soft);border-color:var(--accent);color:var(--accent);transform:translateY(-1px)}
      .primary:focus-visible,.softbtn:focus-visible,.iconbtn:focus-visible,.nav button:focus-visible,.field:focus-visible,input:focus-visible,select:focus-visible,textarea:focus-visible{outline:3px solid var(--focus-ring);outline-offset:2px}
      .field,input:not([type=checkbox]):not([type=radio]),select,textarea{border:1px solid var(--line);border-radius:11px;background:var(--surface);color:var(--text);min-height:42px;padding:9px 12px}
      textarea{min-height:92px}
      .nav button{min-height:43px;border-radius:12px}
      .nav button.active{background:var(--accent-soft);color:var(--accent);border-color:color-mix(in srgb,var(--accent) 28%,var(--line))}
      .iconbtn{width:40px;height:40px;display:inline-grid;place-items:center}
      .panel,.settings-card,.starter,.usage-card{border-radius:16px}
      .zentrix-appearance{display:flex;align-items:center;gap:7px}
      .zentrix-appearance label{font-size:10px;color:var(--muted);font-weight:700;white-space:nowrap}
      #zentrixPalette{width:auto;min-width:126px;max-width:155px;padding:7px 25px 7px 9px;font-size:11px;min-height:38px}
      #zentrixDensity{font-size:10px;white-space:nowrap;min-height:38px;padding:7px 10px}
      [data-density=compact] .panel,[data-density=compact] .settings-card{padding-top:13px;padding-bottom:13px}
      [data-density=compact] .nav button{min-height:37px;padding-top:7px;padding-bottom:7px}
      [data-density=compact] .softbtn,[data-density=compact] .actionbtn{min-height:34px;padding:6px 10px}
      [data-density=compact] .topbar{margin-bottom:23px}
      @media(max-width:900px){.zentrix-appearance label{display:none}#zentrixPalette{min-width:105px;max-width:120px}}
      @media(max-width:720px){.top-actions{gap:6px}.zentrix-appearance{gap:4px}#zentrixPalette{min-width:92px;max-width:105px;font-size:10px}.zentrix-appearance #zentrixDensity{display:none}}
      @media(max-width:480px){#zentrixPalette{min-width:88px;max-width:92px}.top-actions .softbtn#accountButton{font-size:10px;padding:6px 8px}.main{padding-left:14px;padding-right:14px}}
      @media(prefers-reduced-motion:reduce){*,*::before,*::after{scroll-behavior:auto!important;animation-duration:.01ms!important;animation-iteration-count:1!important;transition-duration:.01ms!important}}
    `;
    document.head.append(s);
  }
  function boot(){
    styles();
    const savedTheme=(()=>{try{return localStorage.getItem('zentrix_palette')||'lavender'}catch{return 'lavender'}})();
    const savedDensity=(()=>{try{return localStorage.getItem('zentrix_density')||'comfortable'}catch{return 'comfortable'}})();
    root.dataset.palette=savedTheme;
    // Replace the original theme toggle so the selected palette updates in both modes.
    window.toggleTheme=function(){
      root.dataset.theme=root.dataset.theme==='dark'?'light':'dark';
      try{localStorage.setItem('zentrix_theme',root.dataset.theme)}catch{}
      applyPalette(root.dataset.palette||'lavender');
      if($('#page-graph')?.classList.contains('active')&&typeof window.plotFunction==='function')window.plotFunction();
    };
    mount();applyPalette(savedTheme);applyDensity(savedDensity==='compact');
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();