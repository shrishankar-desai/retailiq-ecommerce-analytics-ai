// Commerce Studio presents the packaged dataset and model outputs without simulated metrics.
'use strict';
const API='/api';
const C={coral:'#f17d73',lavender:'#a483db',plum:'#57264e',ink:'#4b3043',muted:'#8d7687',grid:'#f0e8ef'};
const methods={popularity:'Popularity',similarity:'Item similarity',category:'Category blend'};
const methodKeys=['similarity','category','popularity'];
const methodColors={similarity:C.coral,category:C.plum,popularity:C.lavender};
const fmt=n=>Number(n||0).toLocaleString('en-US');
const compact=n=>new Intl.NumberFormat('en-US',{notation:'compact',maximumFractionDigits:2}).format(Number(n||0));
const pct=n=>n==null?'N/A':(100*Number(n)).toFixed(3)+'%';
const $=id=>document.getElementById(id);
const escapeHTML=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const icon=name=>`<svg aria-hidden="true"><use href="#i-${name}"/></svg>`;
const kpi=(label,value,sub,name)=>`<div class="kpi"><div class="kpi-icon">${icon(name)}</div><div><div class="kpi-label">${escapeHTML(label)}</div><div class="kpi-value">${escapeHTML(value)}</div><div class="kpi-sub">${escapeHTML(sub)}</div></div></div>`;
const cache=new Map();
async function fetchJSON(path){
  if(!cache.has(path)) cache.set(path,(async()=>{const r=await fetch(API+path);if(!r.ok)throw new Error('The data service did not respond.');return r.json();})().catch(e=>{cache.delete(path);throw e;}));
  return cache.get(path);
}
function plot(id,traces,layout={}){
  const el=$(id);if(!el)return Promise.resolve();
  if(typeof Plotly==='undefined')throw new Error('The chart library could not load.');
  return Plotly.react(el,traces,{paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(0,0,0,0)',font:{family:'DM Sans, system-ui, sans-serif',color:C.muted,size:11},margin:{t:12,r:20,b:36,l:48},showlegend:false,xaxis:{gridcolor:C.grid,zeroline:false,linecolor:C.grid},yaxis:{gridcolor:C.grid,zeroline:false},...layout},{displayModeBar:false,responsive:true});
}
const loaded={},pending={};
const loaders={overview:loadOverview,products:loadProducts,customers:loadCustomers,recommend:loadRecommender,model:loadModel,about:loadAbout};
function showError(page){
  loaded[page]=false;
  const target=$('page-'+page);if(!target)return;
  target.querySelector('.error')?.remove();
  const box=document.createElement('div');box.className='error';box.setAttribute('role','alert');
  const text=document.createElement('span');text.textContent='This view could not load. Please try again.';
  const retry=document.createElement('button');retry.textContent='Try again';retry.addEventListener('click',()=>loadPage(page));
  box.append(text,retry);target.prepend(box);
}
async function loadPage(page){
  if(loaded[page])return;if(pending[page])return pending[page];
  $('page-'+page).querySelector('.error')?.remove();
  pending[page]=(async()=>{try{await loaders[page]();loaded[page]=true;}catch(e){showError(page);}finally{delete pending[page];}})();
  return pending[page];
}
function navigate(page){
  if(!loaders[page])page='overview';
  document.querySelectorAll('.page').forEach(el=>el.classList.toggle('active',el.id==='page-'+page));
  document.querySelectorAll('.nav').forEach(el=>{const active=el.dataset.page===page;el.classList.toggle('active',active);if(active)el.setAttribute('aria-current','page');else el.removeAttribute('aria-current');});
  history.replaceState(null,'','#'+page);
  window.scrollTo({top:0,behavior:'instant'});
  loadPage(page);
  requestAnimationFrame(()=>document.querySelectorAll('.page.active .js-plotly-plot').forEach(el=>Plotly.Plots.resize(el)));
}
let summaryData=null,trendData=null;
const visibleSeries={view:true,addtocart:true,transaction:true};
async function getSummary(){
  const s=await fetchJSON('/summary');summaryData=s;
  const first=new Date(s.first_date+'T00:00:00Z'),last=new Date(s.last_date+'T00:00:00Z');
  const month=d=>d.toLocaleDateString('en-GB',{month:'short',timeZone:'UTC'});
  const dates=`${month(first)}–${month(last)} ${last.getUTCFullYear()}`;
  document.querySelectorAll('.data-period').forEach(el=>{el.textContent=dates;el.title=`${s.first_date} to ${s.last_date} · full dataset`});
  return s;
}
function productRows(items,links=false){return items.map(x=>`<tr><td>${links?`<button class="item-link" data-item="${Number(x.itemid)}">#${Number(x.itemid)}</button>`:'#'+Number(x.itemid)}</td><td>${fmt(x.views)}</td><td>${fmt(x.carts)}</td><td>${fmt(x.purchases)}</td></tr>`).join('');}
async function loadOverview(){
  const [s,t,products,m]=await Promise.all([getSummary(),fetchJSON('/trends'),fetchJSON('/products?sort=views&limit=3'),fetchJSON('/model')]);
  $('summary-kpis').innerHTML=[kpi('Visitors',compact(s.visitors),'Distinct anonymous IDs','users'),kpi('Shopping events',compact(s.events),'All recorded actions','event'),kpi('Cart additions',fmt(s.addtocarts),'Item-level cart events','cart'),kpi('Purchased-item events',fmt(s.transaction_events),fmt(s.orders)+' distinct order IDs','bag')].join('');
  trendData=t.data;await renderActivity();
  $('overview-products').innerHTML=productRows(products.products,true);
  $('overview-methods').innerHTML=methodKeys.map(key=>`<tr><td><i class="dot method-dot" style="background:${methodColors[key]}"></i>${methods[key]}</td><td>${pct(m.test[key].precision_at_5)}</td><td>${pct(m.test[key].recall_at_5)}</td><td>${pct(m.test[key].hit_rate_at_5)}</td></tr>`).join('');
  $('overview-evaluation-note').textContent=`${fmt(m.test.similarity.users)} eligible test visitors · offline relevance, not sales uplift.`;
  await plot('overview-model-chart',[{type:'bar',orientation:'h',y:['Popularity','Category blend','Item similarity'],x:['popularity','category','similarity'].map(k=>100*m.test[k].hit_rate_at_5),marker:{color:[C.lavender,C.plum,C.coral]},text:['popularity','category','similarity'].map(k=>pct(m.test[k].hit_rate_at_5)),textposition:'outside',cliponaxis:false,hovertemplate:'%{y}: %{x:.3f}%<extra></extra>'}],{margin:{t:7,b:20,l:93,r:56},bargap:.45,xaxis:{gridcolor:C.grid,ticksuffix:'%',nticks:3,range:[0,Math.max(...methodKeys.map(k=>100*m.test[k].hit_rate_at_5))*1.45]},yaxis:{showgrid:false,fixedrange:true},font:{family:'DM Sans, sans-serif',size:10,color:C.muted}});
}
async function renderActivity(){
  if(!trendData)return;const d=trendData;
  const series=[['view','Views',C.coral,'y'],['addtocart','Cart additions',C.lavender,'y2'],['transaction','Purchased-item events',C.plum,'y2']];
  await plot('activity-chart',series.map(([key,name,color,axis])=>({x:d.map(a=>a.date),y:d.map(a=>a[key]),name,type:'scatter',mode:'lines',yaxis:axis,visible:visibleSeries[key],line:{color,width:2},fill:key==='view'?'tozeroy':undefined,fillcolor:'rgba(241,125,115,.09)',hovertemplate:`${name}: %{y:,}<extra></extra>`})),{margin:{t:9,r:43,b:33,l:47},hovermode:'x unified',xaxis:{showgrid:false,tickformat:'%b %d',nticks:5,zeroline:false},yaxis:{gridcolor:C.grid,tickformat:'~s',title:{text:'Views',font:{size:10}},rangemode:'tozero'},yaxis2:{overlaying:'y',side:'right',showgrid:false,tickformat:'~s',rangemode:'tozero',title:{text:'Cart / purchase events',font:{size:10}}}});
}
let productOptionsLoaded=false,productRequest=0;
async function loadProducts(){
  const [cats,stats]=await Promise.all([fetchJSON('/categories'),fetchJSON('/category-stats')]);
  if(!productOptionsLoaded){$('category-filter').insertAdjacentHTML('beforeend',cats.map(x=>`<option value="${Number(x.categoryid)}">Category ${Number(x.categoryid)}</option>`).join(''));productOptionsLoaded=true;}
  const rows=stats.slice(0,9).sort((a,b)=>a.view-b.view);
  await plot('category-chart',[{type:'bar',orientation:'h',y:rows.map(c=>'Category '+c.root_category),x:rows.map(c=>c.view),marker:{color:C.lavender},hovertemplate:'%{y}: %{x:,} views<extra></extra>'}],{margin:{l:104,t:8,r:18,b:36},xaxis:{gridcolor:C.grid,tickformat:'~s'},yaxis:{showgrid:false,automargin:true},bargap:.35});
  await loadProductTable();
}
async function loadProductTable(){
  const request=++productRequest;
  const params=new URLSearchParams({sort:$('sort-products').value,limit:'30'});
  if($('category-filter').value)params.set('category',$('category-filter').value);
  if($('product-search').value.trim())params.set('search',$('product-search').value.trim());
  const r=await fetchJSON('/products?'+params);if(request!==productRequest)return;
  $('product-table').innerHTML=r.products.length?productRows(r.products):'<tr><td colspan="4">No matching items. Try a different ID or reset the filters.</td></tr>';
  $('product-count').textContent=`${fmt(r.shown)} items shown · top-10,000 leaderboard`;
  $('app-status').textContent=`${r.shown} matching products shown.`;
}
async function loadCustomers(){
  const [seg,s]=await Promise.all([fetchJSON('/segments'),getSummary()]);
  const map=Object.fromEntries(seg.map(x=>[x.segment,x.visitors]));
  const names=['Browser','Cart engager','Purchaser'];
  const desc=['No cart or purchase event','Cart activity, no recorded purchase','At least one purchased-item event'];
  $('segment-kpis').innerHTML=names.map((n,i)=>kpi(n+'s',compact(map[n]),desc[i],['users','cart','bag'][i])).join('');
  await plot('segment-chart',[{type:'pie',hole:.72,labels:names,values:names.map(n=>map[n]||0),marker:{colors:[C.coral,C.lavender,C.plum],line:{color:'#fff',width:4}},textinfo:'none',hovertemplate:'%{label}: %{value:,} (%{percent})<extra></extra>',sort:false}],{margin:{t:15,b:50,l:15,r:15},showlegend:true,legend:{orientation:'h',x:.5,xanchor:'center',y:-.09,font:{size:11}},annotations:[{text:compact(s.visitors)+'<br><span style="font-size:12px;color:#94778d">visitors</span>',showarrow:false,font:{size:29,color:C.plum}}]});
  const f=s.funnel_visitors,mx=Math.max(f.view,f.addtocart,f.transaction,1);
  $('funnel-bars').innerHTML=[['Product viewers',f.view,''],['Added to cart',f.addtocart,'cart'],['Purchased',f.transaction,'buy']].map(([label,n,cls])=>`<div class="funnel-row"><div class="funnel-text"><span>${label}</span><b>${fmt(n)}</b></div><div class="track"><div class="fill ${cls}" style="width:${100*n/mx}%"></div></div></div>`).join('');
}
let recRequest=0;
async function loadRecommender(){
  const visitors=await fetchJSON('/visitors');
  if(!$('visitor-select').options.length)$('visitor-select').innerHTML=visitors.map(x=>`<option value="${Number(x.visitorid)}">Visitor #${Number(x.visitorid)} · ${Number(x.interactions)} items</option>`).join('');
  await generateRecommendations();
}
function recommendationRows(rows){return rows.map((x,i)=>`<div class="rec-item"><span class="rec-rank">${String(i+1).padStart(2,'0')}</span><div class="rec-info"><b>Item #${Number(x.itemid)}</b><p>${escapeHTML(x.reason)}${x.categoryid!=null?' · category '+Number(x.categoryid):''}</p></div><span class="score"><small>RANK SCORE</small>${Number(x.score).toFixed(3)}</span></div>`).join('')||'<p class="footnote">No eligible items for this visitor.</p>';}
async function generateRecommendations(){
  const id=$('visitor-select').value,mode=$('rec-mode').value;if(!id)return;
  const request=++recRequest;const button=$('generate-button');button.disabled=true;button.textContent='Comparing…';
  try{
    const path=`/recommend?visitorid=${encodeURIComponent(id)}&mode=`;
    const [selected,baseline]=await Promise.all([fetchJSON(path+mode),fetchJSON(path+'popularity')]);
    if(request!==recRequest)return;
    $('history-tags').innerHTML=selected.history.map(n=>`<span class="tag">#${Number(n)}</span>`).join('');
    $('history-count').textContent=selected.history.length+' items';
    $('recommendation-heading').textContent=methods[mode];
    $('recommendation-list').innerHTML=recommendationRows(selected.recommendations);
    $('baseline-list').innerHTML=recommendationRows(baseline.recommendations);
    $('page-recommend').querySelector('.error')?.remove();
    $('app-status').textContent=`${methods[mode]} compared with popularity for visitor ${id}.`;
  }finally{if(request===recRequest){button.disabled=false;button.textContent='Compare recommendations';}}
}
async function loadModel(){
  const m=await fetchJSON('/model'),test=m.test,keys=['popularity','similarity','category'];
  const best=keys.reduce((a,b)=>(test[b].hit_rate_at_5||0)>(test[a].hit_rate_at_5||0)?b:a);
  $('model-kpis').innerHTML=[kpi('Eligible test visitors',fmt(test[best].users),'Warm visitors with unseen future items','users'),kpi('Best hit rate@5',pct(test[best].hit_rate_at_5),methods[best],'chart'),kpi('Training catalog',fmt(m.catalog_items),'Candidate items at training time','box')].join('');
  await plot('model-chart',['precision_at_5','recall_at_5','hit_rate_at_5'].map((metric,i)=>({type:'bar',name:['Precision@5','Recall@5','Hit rate@5'][i],x:keys.map(k=>methods[k]),y:keys.map(k=>100*(test[k][metric]||0)),marker:{color:[C.coral,C.lavender,C.plum][i]},hovertemplate:'%{y:.3f}%<extra>%{fullData.name}</extra>'})),{barmode:'group',showlegend:true,legend:{orientation:'h',y:-.2,font:{size:11}},margin:{t:12,r:12,b:67,l:52},yaxis:{gridcolor:C.grid,ticksuffix:'%',rangemode:'tozero'},xaxis:{showgrid:false},bargap:.25});
  document.querySelector('#model-table tbody').innerHTML=keys.map(k=>`<tr><td>${methods[k]}</td><td>${pct(test[k].precision_at_5)}</td><td>${pct(test[k].recall_at_5)}</td><td>${pct(test[k].hit_rate_at_5)}</td></tr>`).join('');
  $('eval-notes').innerHTML=`<b>Training cutoff</b><br>${escapeHTML(m.train_cutoff_utc)}<br><br><b>Validation cutoff</b><br>${escapeHTML(m.validation_cutoff_utc)}<br><br><b>Event split</b><br>${fmt(m.train_events)} train / ${fmt(m.validation_events)} validation / ${fmt(m.test_events)} test<br><br><b>Protocol</b><br>${escapeHTML(m.protocol)}<br><br><b>Limitation</b><br>${escapeHTML(m.limitation)}`;
}
async function loadAbout(){
  const s=await getSummary();$('data-source').textContent=s.source||'Historical shopping events supplied with this demonstration.';
  if(/synthetic/i.test(s.source||'')){$('source-license').textContent='This dataset is independently generated for demonstration. Results are illustrative and do not represent a client’s performance.';}
}
async function exportReport(button){
  const original=button.innerHTML;button.disabled=true;
  try{
    const [s,m]=await Promise.all([getSummary(),fetchJSON('/model')]);
    const rows=[['RetailIQ Commerce Studio','Historical offline report'],['Source',s.source||'Packaged dataset'],['Period',s.first_date+' to '+s.last_date],['Metric','Value'],['Visitors',s.visitors],['Shopping events',s.events],['Product views',s.views],['Cart additions',s.addtocarts],['Purchased-item events',s.transaction_events],['Distinct order IDs',s.orders],[],['Method','Precision@5','Recall@5','Hit rate@5','Eligible users'],...methodKeys.map(k=>[methods[k],m.test[k].precision_at_5,m.test[k].recall_at_5,m.test[k].hit_rate_at_5,m.test[k].users]),[],['Limitations','Historical offline analysis; no revenue or sales-uplift claim.'],['Protocol',m.protocol]];
    const csv=rows.map(row=>row.map(v=>'"'+String(v??'').replace(/"/g,'""')+'"').join(',')).join('\r\n');
    const url=URL.createObjectURL(new Blob(['\uFEFF'+csv],{type:'text/csv;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download='RetailIQ_Commerce_Report.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
    $('app-status').textContent='Commerce report downloaded.';
  }catch(e){showError('overview');}finally{button.disabled=false;button.innerHTML=original;}
}
document.querySelectorAll('.nav').forEach(b=>b.addEventListener('click',()=>navigate(b.dataset.page)));
document.querySelectorAll('[data-open-page]').forEach(b=>b.addEventListener('click',()=>navigate(b.dataset.openPage)));
document.querySelector('.brand').addEventListener('click',e=>{e.preventDefault();navigate('overview')});
document.querySelectorAll('.series-toggle').forEach(b=>b.addEventListener('click',()=>{visibleSeries[b.dataset.series]=!visibleSeries[b.dataset.series];b.classList.toggle('active',visibleSeries[b.dataset.series]);b.setAttribute('aria-pressed',String(visibleSeries[b.dataset.series]));renderActivity().catch(()=>showError('overview'));}));
$('overview-products').addEventListener('click',e=>{const b=e.target.closest('[data-item]');if(!b)return;$('product-search').value=b.dataset.item;$('category-filter').value='';navigate('products');if(loaded.products)loadProductTable().catch(()=>showError('products'));});
['sort-products','category-filter'].forEach(id=>$(id).addEventListener('change',()=>loadProductTable().catch(()=>showError('products'))));
let searchTimer;$('product-search').addEventListener('input',()=>{clearTimeout(searchTimer);searchTimer=setTimeout(()=>loadProductTable().catch(()=>showError('products')),250)});
$('reset-products').addEventListener('click',()=>{$('product-search').value='';$('category-filter').value='';$('sort-products').value='views';loadProductTable().catch(()=>showError('products'));});
$('generate-button').addEventListener('click',()=>generateRecommendations().catch(()=>showError('recommend')));
['visitor-select','rec-mode'].forEach(id=>$(id).addEventListener('change',()=>generateRecommendations().catch(()=>showError('recommend'))));
document.querySelectorAll('.export-report').forEach(b=>b.addEventListener('click',()=>exportReport(b)));
window.addEventListener('hashchange',()=>navigate(location.hash.slice(1)));
getSummary().catch(()=>{});
navigate(location.hash.slice(1)||'overview');

$('header-search').addEventListener('submit',async e=>{e.preventDefault();$('product-search').value=$('header-product-search').value.trim();$('category-filter').value='';navigate('products');await loadPage('products');if(loaded.products)loadProductTable().catch(()=>showError('products'));});
