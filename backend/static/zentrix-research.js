/* ZENTRIX Research Workbench — local symbolic multivariable mathematics. */
(() => {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const make = (tag, cls, value) => {
    const node = document.createElement(tag);
    if (cls) node.className = cls;
    if (value !== undefined) node.textContent = value;
    return node;
  };
  const field = (label, id, value, placeholder) => {
    const wrap = make('label', 'zentrix-research-field');
    wrap.append(make('span', 'subtle', label));
    const input = make('input', 'field');
    input.id = id; input.value = value;
    if (placeholder) input.placeholder = placeholder;
    wrap.append(input); return wrap;
  };
  const showResult = (host, data) => {
    host.replaceChildren();
    const grid = make('div', 'starter-grid');
    const entries = Object.entries(data).filter(([key, value]) =>
      !['notes','point','variables','hessian_at_point','jacobian_at_point'].includes(key) &&
      (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean' || Array.isArray(value)));
    entries.forEach(([key, value]) => {
      const card = make('div', 'trust');
      card.append(make('b', '', key.replaceAll('_',' ')));
      card.append(make('span', '', Array.isArray(value) ? JSON.stringify(value) : String(value)));
      grid.append(card);
    });
    host.append(grid);
    (data.notes || []).forEach(note => host.append(make('p', 'subtle', note)));
  };
  function boot() {
    const nav = document.querySelector('nav[aria-label="Math tools"]');
    if (!nav || $('page-research')) return;
    const button = make('button', '');
    button.dataset.page = 'research';
    button.title = 'Explore multivariable calculus and vector fields';
    button.append(make('span', 'navicon', '∇'), document.createTextNode(' Research Lab'));
    button.addEventListener('click', () => window.goPage('research'));
    nav.append(button);

    const page = make('section', 'page');
    page.id = 'page-research';
    const title = make('div', 'page-title');
    title.append(make('h1', '', 'Research mathematics lab'),
      make('p', '', 'Multivariable calculus, local critical-point analysis and vector-field operators. Exact symbolic derivatives; numerical diagnostics. Runs locally with no AI key.'));
    const tabs = make('div', 'panel settings-card zentrix-research-tabs');
    const scalarBtn = make('button', 'primary', 'Scalar field');
    const vectorBtn = make('button', 'softbtn', 'Vector field');
    scalarBtn.type = vectorBtn.type = 'button';
    tabs.append(scalarBtn, vectorBtn);
    const scalar = make('div', 'panel settings-card zentrix-research-card');
    scalar.id = 'zentrixScalarForm';
    scalar.append(make('h2', '', 'Gradient and Hessian analysis'),
      make('p', 'subtle', 'Study a real-valued function f(x, y, …) at a chosen point.'));
    scalar.append(field('FUNCTION f(x, y)', 'zResearchExpression', 'x^2 + x*y + y^2', 'e.g. x^2 + x*y + y^2'));
    scalar.append(field('VARIABLES · comma separated', 'zResearchVariables', 'x,y', 'x,y,z'));
    scalar.append(field('POINT · comma separated in the same order', 'zResearchPoint', '0,0', '0,0'));
    scalar.append(field('PRECISION · 15–80 digits', 'zResearchPrecision', '30'));
    const scalarRun = make('button', 'primary', 'Analyse scalar field ↗');
    scalarRun.type = 'button';
    const scalarOut = make('div', 'result hidden'); scalarOut.id = 'zResearchScalarOutput';
    scalar.append(scalarRun, scalarOut);

    const vector = make('div', 'panel settings-card zentrix-research-card hidden');
    vector.id = 'zentrixVectorForm';
    vector.append(make('h2', '', 'Vector-field analysis'),
      make('p', 'subtle', 'Calculate the Jacobian, divergence and three-dimensional curl.'));
    vector.append(field('COMPONENTS · comma separated', 'zResearchComponents', 'x^2*y, x*y^2', 'P, Q or P, Q, R'));
    vector.append(field('VARIABLES · comma separated', 'zResearchVectorVariables', 'x,y', 'x,y,z'));
    vector.append(field('POINT · comma separated in the same order', 'zResearchVectorPoint', '1,2', '1,2 or 1,2,3'));
    vector.append(field('PRECISION · 15–80 digits', 'zResearchVectorPrecision', '30'));
    const vectorRun = make('button', 'primary', 'Analyse vector field ↗');
    vectorRun.type = 'button';
    const vectorOut = make('div', 'result hidden'); vectorOut.id = 'zResearchVectorOutput';
    vector.append(vectorRun, vectorOut);

    scalarBtn.addEventListener('click', () => { scalar.classList.remove('hidden'); vector.classList.add('hidden'); scalarBtn.className='primary'; vectorBtn.className='softbtn'; });
    vectorBtn.addEventListener('click', () => { vector.classList.remove('hidden'); scalar.classList.add('hidden'); vectorBtn.className='primary'; scalarBtn.className='softbtn'; });
    const parseList = (value) => value.split(',').map(item => item.trim()).filter(Boolean);
    const parsePoint = (variables, values) => {
      const numbers = values.split(',').map(item => Number(item.trim()));
      if (numbers.length !== variables.length || numbers.some(value => !Number.isFinite(value))) throw Error('Enter exactly one finite point coordinate per variable.');
      return Object.fromEntries(variables.map((name, index) => [name, numbers[index]]));
    };
    scalarRun.addEventListener('click', async () => {
      scalarRun.disabled = true; scalarRun.textContent = 'Computing…'; scalarOut.classList.remove('hidden');
      try {
        const variables = parseList($('zResearchVariables').value);
        const payload = {expression:$('zResearchExpression').value, variables, point:parsePoint(variables,$('zResearchPoint').value), precision:Number($('zResearchPrecision').value)};
        const response = await fetch('/api/research/multivariable',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
        const data = await response.json(); if (!response.ok) throw Error(data.detail || 'Analysis failed.');
        showResult(scalarOut,data);
      } catch(error) { scalarOut.replaceChildren(make('div','note warning',error.message)); }
      finally { scalarRun.disabled=false; scalarRun.textContent='Analyse scalar field ↗'; }
    });
    vectorRun.addEventListener('click', async () => {
      vectorRun.disabled = true; vectorRun.textContent = 'Computing…'; vectorOut.classList.remove('hidden');
      try {
        const variables = parseList($('zResearchVectorVariables').value);
        const payload = {components:parseList($('zResearchComponents').value), variables, point:parsePoint(variables,$('zResearchVectorPoint').value), precision:Number($('zResearchVectorPrecision').value)};
        const response = await fetch('/api/research/vector-field',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
        const data = await response.json(); if (!response.ok) throw Error(data.detail || 'Analysis failed.');
        showResult(vectorOut,data);
      } catch(error) { vectorOut.replaceChildren(make('div','note warning',error.message)); }
      finally { vectorRun.disabled=false; vectorRun.textContent='Analyse vector field ↗'; }
    });
    const style = make('style','');
    style.textContent = '.zentrix-research-tabs{display:flex;gap:8px;margin:12px 0}.zentrix-research-card{padding:18px;margin:12px 0}.zentrix-research-card h2{font-size:17px;margin:0 0 6px}.zentrix-research-field{display:grid;gap:6px;margin:12px 0}.zentrix-research-field .field{width:100%;max-width:700px}.zentrix-research-card>.primary{margin-top:6px}.zentrix-research-card .result{margin-top:15px}.zentrix-research-card .starter-grid{grid-template-columns:repeat(auto-fit,minmax(210px,1fr))}';
    document.head.append(style);
    page.append(title,tabs,scalar,vector);
    const main = document.querySelector('main') || document.querySelector('.content') || document.body;
    main.append(page);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, {once:true});
  else boot();
})();
