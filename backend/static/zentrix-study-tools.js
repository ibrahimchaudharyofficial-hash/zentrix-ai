/* ZENTRIX AI — private study tools: spaced-repetition cards and focus sessions. */
(() => {
  'use strict';
  const $ = (s) => document.querySelector(s);
  const make = (tag, cls, value) => { const el=document.createElement(tag); if(cls)el.className=cls; if(value!==undefined)el.textContent=value; return el; };
  const STORAGE='zentrix_study_tools_v1';
  const deck=[
    ['Algebra','Quadratic formula','For ax² + bx + c = 0, what are the roots?','x = (−b ± √(b² − 4ac)) / 2a','Use the discriminant b² − 4ac to determine the root type.'],
    ['Algebra','Difference of squares','How do you factor a² − b²?','(a − b)(a + b)','A difference of two perfect squares factors into conjugates.'],
    ['Algebra','Slope','What is the slope between (x₁,y₁) and (x₂,y₂)?','m = (y₂ − y₁) / (x₂ − x₁)','Rise divided by run; x₂ must differ from x₁.'],
    ['Algebra','Point-slope form','Write the equation of a line with slope m through (x₁,y₁).','y − y₁ = m(x − x₁)','Substitute the known point and slope.'],
    ['Geometry','Pythagorean theorem','For a right triangle, how are the sides related?','a² + b² = c²','c is the hypotenuse, opposite the right angle.'],
    ['Geometry','Circle area','What is the area of a circle with radius r?','A = πr²','Square the radius, then multiply by π.'],
    ['Geometry','Circle circumference','What is the circumference of a circle?','C = 2πr = πd','d is the diameter and equals 2r.'],
    ['Trigonometry','Sine ratio','In a right triangle, what is sin θ?','opposite / hypotenuse','Remember SOH-CAH-TOA.'],
    ['Trigonometry','Cosine ratio','In a right triangle, what is cos θ?','adjacent / hypotenuse','Remember SOH-CAH-TOA.'],
    ['Trigonometry','Pythagorean identity','What is the fundamental sine-cosine identity?','sin²θ + cos²θ = 1','It holds for every real angle θ.'],
    ['Calculus','Power rule','Differentiate xⁿ with respect to x.','d(xⁿ)/dx = n xⁿ⁻¹','Bring the exponent down, then subtract one.'],
    ['Calculus','Derivative of sine','What is d(sin x)/dx?','cos x','Angles are measured in radians in standard calculus.'],
    ['Calculus','Derivative of cosine','What is d(cos x)/dx?','−sin x','The negative sign is essential.'],
    ['Calculus','Product rule','Differentiate u(x)v(x).','(uv)′ = u′v + uv′','Differentiate one factor at a time and add.'],
    ['Calculus','Chain rule','Differentiate f(g(x)).','f′(g(x)) · g′(x)','Differentiate the outer function, then multiply by the inner derivative.'],
    ['Calculus','Integral power rule','Integrate xⁿ for n ≠ −1.','∫xⁿ dx = xⁿ⁺¹/(n+1) + C','Increase the power by one and divide by the new power.'],
    ['Statistics','Mean','How do you calculate the arithmetic mean?','mean = (sum of values) / (number of values)','The mean uses every observation.'],
    ['Probability','Complement','What is the probability of an event not occurring?','P(Aᶜ) = 1 − P(A)','An event and its complement have probabilities that sum to one.']
  ];
  function read(){try{const v=JSON.parse(localStorage.getItem(STORAGE)||'{}');return {cards:v.cards&&typeof v.cards==='object'?v.cards:{},sessions:Array.isArray(v.sessions)?v.sessions:[]};}catch{return {cards:{},sessions:[]};}}
  function write(v){try{localStorage.setItem(STORAGE,JSON.stringify(v));}catch{}}
  function install(){
    const page=$('#page-learn');if(!page||$('#zentrixStudyTools'))return;
    const root=make('section','panel zentrix-study-tools');root.id='zentrixStudyTools';
    const title=make('div','starter-head');title.append(make('h2','','Study lab'),make('span','subtle','Private · saved on this device'));
    const tabs=make('div','zentrix-study-tabs');
    const flashTab=make('button','softbtn','Formula flashcards');flashTab.type='button';
    const focusTab=make('button','softbtn','Focus timer');focusTab.type='button';
    tabs.append(flashTab,focusTab);
    const flash=make('div','zentrix-study-pane'),focus=make('div','zentrix-study-pane');
    root.append(title,tabs,flash,focus);
    const anchor=$('#zentrixProgressDashboard')||$('#learningProfile')||page.lastElementChild;
    if(anchor&&anchor.parentElement===page)anchor.insertAdjacentElement('afterend',root);else page.append(root);

    let filter='All',index=0,revealed=false;
    const category=make('div','zentrix-study-filters');
    const card=make('article','zentrix-flashcard');
    const cardMeta=make('div','subtle'),question=make('h3',''),answer=make('div','zentrix-flash-answer'),hint=make('p','subtle');
    const reveal=make('button','primary','Reveal answer');reveal.type='button';
    const grades=make('div','zentrix-study-grades');
    const dueLine=make('p','subtle');
    card.append(cardMeta,question,answer,hint,reveal,grades,dueLine);
    const counts=make('div','zentrix-study-counts');
    flash.append(category,counts,card);
    const categories=['All',...new Set(deck.map(x=>x[0]))];
    const filtered=()=>deck.map((x,i)=>({x,i})).filter(o=>filter==='All'||o.x[0]===filter);
    function dueCount(){const now=Date.now(),v=read();return deck.filter((_,i)=>!v.cards[i]||Number(v.cards[i].due||0)<=now).length;}
    function renderCard(){
      const list=filtered();if(index>=list.length)index=0;
      const item=list[index];const v=read(),progress=v.cards[item.i]||{},isDue=!progress.due||progress.due<=Date.now();
      cardMeta.textContent=item.x[0]+' · Card '+(index+1)+' of '+list.length+(isDue?' · Due now':' · Learning');
      question.textContent=item.x[2];answer.replaceChildren();answer.hidden=!revealed;
      answer.append(make('strong','',item.x[3]),make('p','',item.x[4]));
      hint.textContent=progress.reviews?'Reviewed '+progress.reviews+' time(s) · interval '+(progress.interval||0)+' day(s)':'New card · Rate how well you recalled it';
      reveal.hidden=revealed;grades.replaceChildren();
      if(revealed){
        [['Again','again'],['Hard','hard'],['Good','good'],['Easy','easy']].forEach(([label,grade])=>{const b=make('button','softbtn',label);b.type='button';b.addEventListener('click',()=>review(item.i,grade));grades.append(b);});
      }
      dueLine.textContent='Next due: '+(progress.due?new Date(progress.due).toLocaleString():'Not reviewed yet');
      counts.textContent=dueCount()+' cards due · '+deck.length+' cards in the deck';
    }
    function review(cardIndex,grade){
      const v=read(),p=v.cards[cardIndex]||{interval:0,reviews:0};
      let days=grade==='again'?0:grade==='hard'?Math.max(1,Math.round((p.interval||1)*1.2)):grade==='good'?(p.interval===0?1:p.interval===1?3:Math.min(180,p.interval*2)):Math.max(4,Math.round((p.interval||1)*2.5));
      const due=Date.now()+(grade==='again'?10*60*1000:days*86400000);
      v.cards[cardIndex]={interval:days,reviews:(p.reviews||0)+1,due,lastGrade:grade};write(v);
      const list=filtered();index=(index+1)%list.length;revealed=false;renderCard();
    }
    categories.forEach(name=>{const b=make('button',name==='All'?'primary':'softbtn',name);b.type='button';b.addEventListener('click',()=>{filter=name;index=0;revealed=false;Array.from(category.children).forEach(x=>{x.className=x.textContent===name?'primary':'softbtn';});renderCard();});category.append(b);});
    reveal.addEventListener('click',()=>{revealed=true;renderCard();});
    const nav=make('div','zentrix-study-nav');
    const prev=make('button','softbtn','← Previous');prev.type='button';const next=make('button','softbtn','Next →');next.type='button';
    prev.addEventListener('click',()=>{index=(index-1+filtered().length)%filtered().length;revealed=false;renderCard();});
    next.addEventListener('click',()=>{index=(index+1)%filtered().length;revealed=false;renderCard();});
    nav.append(prev,next);flash.append(nav);renderCard();

    // Pomodoro-style focus timer; the countdown is intentionally local and never uploads data.
    const focusTitle=make('h3','','Focus session');
    const timer=make('div','zentrix-focus-time','25:00');
    const focusMode=make('div','zentrix-study-filters');
    const work=make('button','primary','Focus · 25 min');work.type='button';
    const rest=make('button','softbtn','Break · 5 min');rest.type='button';focusMode.append(work,rest);
    const timerActions=make('div','zentrix-study-nav');
    const start=make('button','primary','Start');start.type='button';
    const pause=make('button','softbtn','Pause');pause.type='button';pause.disabled=true;
    const reset=make('button','softbtn','Reset');reset.type='button';
    timerActions.append(start,pause,reset);
    const focusStats=make('p','subtle');
    const focusNote=make('p','subtle','Choose a focus or break session. Keep this tab open while the timer runs.');
    focus.append(focusTitle,focusMode,timer,timerActions,focusStats,focusNote);
    let seconds=1500,mode='focus',interval=null,endAt=0;
    function showTime(){timer.textContent=String(Math.floor(seconds/60)).padStart(2,'0')+':'+String(seconds%60).padStart(2,'0');}
    function setMode(nextMode){stop();mode=nextMode;seconds=mode==='focus'?1500:300;work.className=mode==='focus'?'primary':'softbtn';rest.className=mode==='break'?'primary':'softbtn';showTime();}
    function stop(){if(interval!==null)clearInterval(interval);interval=null;pause.disabled=true;start.disabled=false;}
    function tick(){seconds=Math.max(0,Math.ceil((endAt-Date.now())/1000));showTime();if(seconds<=0){stop();if(mode==='focus'){const v=read();v.sessions.push({date:new Date().toISOString(),minutes:25});v.sessions=v.sessions.slice(-500);write(v);focusNote.textContent='Focus session complete. Take a short break!';}else focusNote.textContent='Break complete. Ready for another focus session?';updateStats();}}
    function updateStats(){const v=read();focusStats.textContent=v.sessions.length+' completed focus sessions · '+v.sessions.reduce((n,s)=>n+(Number(s.minutes)||0),0)+' focus minutes recorded';}
    work.addEventListener('click',()=>setMode('focus'));rest.addEventListener('click',()=>setMode('break'));
    start.addEventListener('click',()=>{if(interval!==null)return;endAt=Date.now()+seconds*1000;interval=setInterval(tick,250);pause.disabled=false;start.disabled=true;focusNote.textContent=mode==='focus'?'Focus time. One task, no distractions.':'Take a proper short break.';});
    pause.addEventListener('click',()=>{if(interval===null)return;tick();stop();focusNote.textContent='Paused. Resume when you are ready.';});
    reset.addEventListener('click',()=>{stop();seconds=mode==='focus'?1500:300;showTime();focusNote.textContent='Timer reset.';});
    showTime();updateStats();
    flashTab.addEventListener('click',()=>{flash.hidden=false;focus.hidden=true;flashTab.className='primary';focusTab.className='softbtn';});
    focusTab.addEventListener('click',()=>{flash.hidden=true;focus.hidden=false;flashTab.className='softbtn';focusTab.className='primary';});
    focus.hidden=true;focusTab.className='softbtn';flashTab.className='primary';
  }
  function styles(){if($('#zentrixStudyStyles'))return;const s=make('style');s.id='zentrixStudyStyles';s.textContent=`
    .zentrix-study-tools{padding:18px;margin-top:18px}.zentrix-study-tabs,.zentrix-study-filters,.zentrix-study-nav,.zentrix-study-grades{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}
    .zentrix-study-filters button,.zentrix-study-grades button,.zentrix-study-nav button{font-size:12px}
    .zentrix-flashcard{border:1px solid var(--line);background:var(--surface2);border-radius:14px;padding:18px;min-height:220px}
    .zentrix-flashcard h3{font-size:18px;line-height:1.5;margin:14px 0}.zentrix-flash-answer{padding:14px;border-radius:10px;background:var(--surface);margin:12px 0;line-height:1.7}
    .zentrix-flash-answer strong{font-size:19px}.zentrix-focus-time{font-size:clamp(42px,8vw,68px);font-weight:750;letter-spacing:2px;text-align:center;padding:20px;font-variant-numeric:tabular-nums}
    .zentrix-study-counts{font-size:12px;color:var(--muted);margin:8px 0}.zentrix-study-pane[hidden],.zentrix-flash-answer[hidden],.zentrix-study-grades:empty{display:none}
    @media(max-width:600px){.zentrix-study-tools{padding:12px}.zentrix-flashcard{padding:13px}}
  `;document.head.append(s);}
  function boot(){styles();install();}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();