import React, { useEffect, useMemo, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import cytoscape from 'cytoscape';
import { Network, Search, ArrowUpRight, ArrowRight, Layers, FlaskConical, ShieldCheck, ChevronDown, Maximize2, Plus, Minus, ExternalLink, Info, Check, CircleDot, BarChart3 } from 'lucide-react';
import './style.css';

const pct = n => `${(100*n).toFixed(2)}%`;
const names = {path_only:'Path scoring',popularity_only:'Popularity',random:'Random reference',embedding_only:'DistMult embedding',combined:'Tuned combined'};
const colors = {drug:'#d97742','gene/protein':'#3f8174',pathway:'#8271a6',disease:'#b66572'};

function Graph({ detail, context, pathIndex, onSelect }) {
  const container = useRef(null), instance = useRef(null);
  useEffect(() => {
    if (!detail || !container.current) return;
    let nodes = detail.graph.nodes, edges = detail.graph.edges.filter(e=>context || !e.context);
    if(pathIndex>=0 && detail.paths[pathIndex]){
      const path = detail.paths[pathIndex], ids = new Set(path.nodes.map(n=>n.id));
      edges = edges.filter(e=>(ids.has(e.source)&&ids.has(e.target)) || (context&&e.context&&ids.has(e.source)));
      const shown=new Set([...ids,...edges.flatMap(e=>[e.source,e.target])]);
      nodes=nodes.filter(n=>shown.has(n.id));
    } else if(!context){ const ids=new Set([detail.drug_id,...edges.flatMap(e=>[e.source,e.target])]);nodes=nodes.filter(n=>ids.has(n.id)); }
    const buckets={drug:[], 'gene/protein':[],pathway:[],disease:[]};nodes.forEach(n=>(buckets[n.type]??=[]).push(n));
    const elements=nodes.map(n=>{
      const bucket=buckets[n.type],i=bucket.indexOf(n), count=bucket.length;
      const x={drug:60,'gene/protein':330,pathway:570,disease:810}[n.type]??400;
      return {data:{...n,id:String(n.id),label:n.name,color:colors[n.type]??'#73817e'},position:{x:x+(n.type==='gene/protein'?(i%2)*90:0),y:70+(i+1)*370/(count+1)}};
    });
    edges.forEach(e=>elements.push({data:{...e,id:`e-${e.id}`,source:String(e.source),target:String(e.target),label:e.context?'pathway member':e.relations.includes('protein_protein')?'interacts':e.relations.includes('drug_protein')?'associated':'associated'}}));
    const cy=cytoscape({container:container.current,elements,layout:{name:'preset',fit:true,padding:45},minZoom:.3,maxZoom:3,wheelSensitivity:.18,
      style:[
        {selector:'node',style:{'background-color':'data(color)','label':'data(label)','color':'#293d38','font-size':12,'font-family':'Arial','text-wrap':'wrap','text-max-width':128,'text-valign':'bottom','text-margin-y':10,width:21,height:21,'border-width':5,'border-color':'#f4f7f4'}},
        {selector:'node[type="drug"]',style:{width:31,height:31,'border-color':'#f5e9dc','border-width':8,'font-weight':700}},
        {selector:'node[type="disease"]',style:{width:34,height:34,'border-color':'#f3e4e6','border-width':8,'font-weight':700}},
        {selector:'node[type="pathway"]',style:{shape:'round-rectangle',width:20,height:20,'font-size':10,'text-max-width':145}},
        {selector:'edge',style:{width:1.5,'line-color':'#bbc9c0','curve-style':'bezier','label':'data(label)','font-size':9,'color':'#72827a','text-background-color':'#fbfcf8','text-background-opacity':.9,'text-background-padding':3,'text-rotation':'autorotate'}},
        {selector:'edge[?context]',style:{'line-style':'dashed','line-color':'#c4bdd2','font-size':8}},
        {selector:':selected',style:{'border-color':'#263e35','border-width':4,'line-color':'#263e35',width:28,height:28}}
      ]});
    instance.current=cy;cy.on('tap','node',e=>onSelect(e.target.data()));
    const observer=new ResizeObserver(()=>{cy.resize();cy.fit(undefined,45)});observer.observe(container.current);
    return ()=>{observer.disconnect();cy.destroy();instance.current=null;};
  },[detail,context,pathIndex]);
  return <div className="graph-shell"><div ref={container} className="graph-canvas" role="img" aria-label="Interactive biological association graph; use the accessible node list below for details"/><div className="graph-tools"><button aria-label="Zoom in" onClick={()=>instance.current?.zoom(instance.current.zoom()*1.2)}><Plus size={15}/></button><button aria-label="Zoom out" onClick={()=>instance.current?.zoom(instance.current.zoom()/1.2)}><Minus size={15}/></button><button aria-label="Fit graph" onClick={()=>instance.current?.fit(undefined,45)}><Maximize2 size={15}/></button></div><div className="graph-watermark">PRIMEKG <span>/ ASSOCIATION NETWORK</span></div></div>;
}

function CandidateList({families,selected,onSelect}){
  const [query,setQuery]=useState(''),[limit,setLimit]=useState(40);
  const filtered=useMemo(()=>families.filter(f=>`${f.name} ${f.members.map(m=>m.name).join(' ')}`.toLowerCase().includes(query.toLowerCase())),[families,query]);
  return <aside className="candidate-panel"><div className="panel-heading"><div><span className="eyebrow">DISCOVERY RANKING</span><h2>Candidate families <span>{families.length.toLocaleString()}</span></h2></div><Layers size={19}/></div>
    <label className="search"><Search size={16}/><input value={query} onChange={e=>{setQuery(e.target.value);setLimit(40)}} placeholder="Search a drug or family…" aria-label="Search candidate families"/><kbd>⌕</kbd></label>
    <div className="ranking-caption"><span>Ordered by best variant’s path score</span><Info size={13}/></div>
    <div className="candidate-scroll">{filtered.slice(0,limit).map(f=><button key={f.id} className={`candidate ${selected===f.id?'selected':''}`} onClick={()=>onSelect(f.id)} aria-pressed={selected===f.id}>
      <span className="rank">{String(f.rank).padStart(2,'0')}</span><div className="candidate-main"><div className="candidate-title">{f.name}<ArrowUpRight size={16}/></div><div className="candidate-meta">{f.members.length>1?`${f.members.length} variants grouped`:'Single compound'} <span>·</span> {f.members[0].path_count} paths</div><div className="score-track"><i style={{width:`${Math.max(2,f.score/families[0].score*100)}%`}}/></div></div><span className="score">{f.score.toFixed(3)}</span></button>)}
      {!filtered.length&&<div className="empty"><Search size={25}/><h3>No matching families</h3><p>Try a generic drug name or “insulin”.</p></div>}
      {filtered.length>limit&&<button className="load-more" onClick={()=>setLimit(limit+40)}>Show 40 more families <ChevronDown size={15}/></button>}
    </div><div className="panel-foot"><ShieldCheck size={14}/> Known Alzheimer’s controls excluded</div></aside>;
}

function EvidencePanel({detail,node}){
  const [tab,setTab]=useState('graph');
  return <section className="evidence panel"><div className="section-title"><h2>Evidence & provenance</h2><span className="badge neutral">Graph evidence available</span></div>
    <div className="small-tabs" role="tablist" aria-label="Evidence views">{[['graph','Graph sources'],['trials','Trial records'],['literature','Literature review']].map(([id,label])=><button key={id} role="tab" aria-selected={tab===id} onClick={()=>setTab(id)}>{label}{id==='trials'&&<span>{detail?.trials.length??0}</span>}</button>)}</div>
    {tab==='graph'&&<div className="evidence-grid"><div><div className="source-mark">01 <span>STRUCTURED EVIDENCE</span></div><h3>{node?.label??'Trace every connection'}</h3><p>{node?`${node.type} · ${node.source} identifier: ${node.source_id}`:'Select a node to inspect its source identifier. Every solid edge shown belongs to a scored path in the sanitized PrimeKG graph.'}</p>
      {node&&(node.url?<a className="entity-link" href={node.url} target="_blank" rel="noopener noreferrer">Open in {node.source} <ExternalLink size={13}/></a>:<span className="no-link">No reliable external page for this identifier</span>)}
      <a className="dataset-link" href="https://doi.org/10.7910/DVN/IXA7BM" target="_blank" rel="noopener noreferrer">PrimeKG source dataset <ExternalLink size={12}/></a></div><div className="evidence-note"><ShieldCheck size={20}/><strong>What the graph can tell us</strong><p>Association and pathway membership. Activation, inhibition and treatment benefit remain unverified.</p><span>Direction unknown on all displayed edges</span></div></div>}
    {tab==='trials'&&<div className="trial-list">{detail?.trials.length?detail.trials.map((t,i)=><a key={`${t.nct_id}-${i}`} href={t.url} target="_blank" rel="noopener noreferrer"><span className="mono">{t.nct_id}</span><strong>{t.title}</strong><span>{t.status.toLowerCase()} · {t.enrollment} enrolled <ExternalLink size={13}/></span></a>):<p className="muted">No eligible exact-matched trial record in this cached snapshot. This does not establish that no trial exists.</p>}<p className="fine-print">Trial registrations document testing, not efficacy. They are excluded from graph scoring.</p></div>}
    {tab==='literature'&&<div className="literature-pending"><FlaskConical size={25}/><div><h3>Literature analysis is next</h3><p>Mechanism, safety and skeptical review will appear here after stage 4. No generated claims or unverified citations are shown.</p><span className="badge neutral">Not yet reviewed</span></div></div>}
  </section>;
}

function Explorer({data}){
  const [selected,setSelected]=useState(data.families[0].id),[drug,setDrug]=useState(data.families[0].representative_id),[detail,setDetail]=useState(null),[error,setError]=useState(''),[context,setContext]=useState(true),[pathIndex,setPathIndex]=useState(-1),[node,setNode]=useState(null);
  const family=data.families.find(f=>f.id===selected),variant=family.members.find(m=>m.drug_id===drug)??family.members[0];
  useEffect(()=>{setDrug(family.representative_id);setPathIndex(-1);setNode(null)},[selected]);
  useEffect(()=>{const controller=new AbortController();setDetail(null);setError('');setNode(null);setPathIndex(-1);fetch(`/api/drugs/${drug}`,{signal:controller.signal}).then(r=>{if(!r.ok)throw new Error('Could not load cached graph');return r.json()}).then(setDetail).catch(e=>{if(e.name!=='AbortError')setError(e.message)});return()=>controller.abort()},[drug]);
  return <><div className="page-heading"><div><span className="eyebrow">ALZHEIMER’S RESEARCH WORKBENCH</span><h1>Follow the evidence.</h1><p>Explore biological connections. Inspect the uncertainty.</p></div><div className="snapshot"><span className="status-dot"/> Cached research snapshot <small>PrimeKG · 3-hop disease neighborhood</small></div></div>
    <div className="overview-strip"><div><Network size={18}/><strong>{data.validation.candidate_count.toLocaleString()}</strong><span>eligible drugs</span></div><div><Layers size={18}/><strong>{data.validation.family_count.toLocaleString()}</strong><span>distinct families</span></div><div><ShieldCheck size={18}/><strong>Path-only</strong><span>fixed, explainable scoring</span></div><div><span className="tiny-pill">RESEARCH USE</span><span>Hypotheses, not treatment advice</span></div></div>
    <div className="workbench"><CandidateList families={data.families} selected={selected} onSelect={setSelected}/><div className="detail-column">
      <section className="graph-panel panel"><div className="detail-heading"><div><span className="eyebrow">FAMILY {String(family.rank).padStart(2,'0')} / {family.members.length>1?'GROUPED VARIANTS':'SINGLE COMPOUND'}</span><h2>{family.name}</h2></div><span className="badge green"><Check size={12}/> Sourced graph paths</span></div>
      <div className="variant-bar"><label>Viewing <select aria-label="Drug variant" value={drug} onChange={e=>setDrug(Number(e.target.value))}>{family.members.map(m=><option key={m.drug_id} value={m.drug_id}>{m.name}</option>)}</select></label><div><span>Path score</span><strong>{variant.path_score.toFixed(4)}</strong><i/> <span>{variant.path_count} paths</span></div></div>
      <div className="graph-toolbar"><div className="legend">{[['drug','Drug'],['gene/protein','Protein'],['pathway','Pathway'],['disease','Disease']].map(([id,label])=><span key={id}><i style={{background:colors[id]}}/>{label}</span>)}</div><label className="check"><input type="checkbox" checked={context} onChange={e=>setContext(e.target.checked)}/>Pathway context</label></div>
      {error?<div className="empty error">{error}</div>:detail?<Graph detail={detail} context={context} pathIndex={pathIndex} onSelect={setNode}/>:<div className="graph-loading"><span className="spinner"/> Loading sourced connections…</div>}
      <div className="path-selector"><span>Scored paths</span><button className={pathIndex===-1?'active':''} onClick={()=>setPathIndex(-1)}>All</button>{detail?.paths.map((p,i)=><button key={i} className={pathIndex===i?'active':''} onClick={()=>setPathIndex(i)}>Path {i+1}</button>)}{detail&&!detail.paths.length&&<span className="muted">No scored path in this subgraph</span>}</div>
      <div className="graph-caption"><Info size={14}/><span>Connections show associations, not causality. Dashed pathway branches are context only.</span></div>
      {detail&&<details className="node-list"><summary>Accessible node and connection list</summary><div>{detail.graph.nodes.map(n=><button key={n.id} onClick={()=>setNode({...n,label:n.name})}>{n.name}<small>{n.type}</small></button>)}</div><ul>{detail.graph.edges.map(e=><li key={e.id}>{detail.graph.nodes.find(n=>n.id===e.source)?.name} ↔ {detail.graph.nodes.find(n=>n.id===e.target)?.name}: {e.relations.join(', ')}; direction unknown{e.context?' (context)':''}</li>)}</ul></details>}
      </section><EvidencePanel detail={detail} node={node}/>
    </div></div></>;
}

function RecallCell({result,k}){const key=`recall_at_${k}`,ci=result.exact_95_ci?.[key];return <td><strong>{pct(result.metrics[key])}</strong><small>{ci?`${pct(ci[0])}–${pct(ci[1])}`:'Exact random reference'}</small></td>}
function Validation({data}){
  const v=data.validation,path=v.methods.path_only,fp=v.family_permutation.results;
  return <><div className="page-heading"><div><span className="eyebrow">VALIDATION / ALL 44 DISCOVERY LABELS</span><h1>A small signal, with limits.</h1><p>Lift over baselines. Every denominator and assumption visible.</p></div><span className="badge green"><ShieldCheck size={14}/> Untuned path scoring</span></div>
    <div className="validation-stats"><article><span>RECALL @ 20</span><strong>{pct(path.metrics.recall_at_20)}</strong><p>4 of 44 trial-tested drugs</p><small>95% exact CI {pct(path.exact_95_ci.recall_at_20[0])}–{pct(path.exact_95_ci.recall_at_20[1])}</small></article><article><span>LIFT OVER RANDOM @ 20</span><strong>{path.metrics.enrichment_at_20.toFixed(2)}<em>×</em></strong><p>vs. exact random expectation</p><small>+{path.lift['20'].vs_popularity_percentage_points.toFixed(2)} percentage points over popularity</small></article><article><span>DISTINCT FAMILIES @ 20 DRUGS</span><strong>{path.distinct_families_at_k['20']}<em> / {v.positive_family_count}</em></strong><p>{path.recovered_families_at_k['20'].join(' + ')||'None recovered'}</p><small>Family-card permutation p = {fp['20'].p_value_one_sided.toFixed(3)}</small></article></div>
    <div className="caution"><Info size={21}/><div><strong>Small sample. Related compounds.</strong><p>{v.small_sample_note} {v.efficacy_note}</p></div></div>
    <section className="panel validation-table"><div className="section-title"><div><span className="eyebrow">PRIMARY VALIDATION</span><h2>Per-drug recall & baseline lift</h2></div><span className="muted">{v.candidate_count.toLocaleString()} candidates · 44 labels</span></div><div className="table-scroll"><table><thead><tr><th>Ranking method</th><th>Recall@10 <small>95% Clopper–Pearson CI</small></th><th>Recall@20 <small>95% Clopper–Pearson CI</small></th><th>Recall@50 <small>secondary</small></th><th>Recall@100 <small>secondary</small></th><th>Enrichment@20</th></tr></thead><tbody>{['path_only','popularity_only','random'].map(m=><tr className={m==='path_only'?'highlight':''} key={m}><th>{names[m]}{m==='path_only'&&<span className="badge green">Primary</span>}</th>{[10,20,50,100].map(k=><RecallCell key={k} result={v.methods[m]} k={k}/>)}<td>{v.methods[m].metrics.enrichment_at_20.toFixed(2)}×</td></tr>)}</tbody></table></div><p className="table-note">Exact intervals use integer drug recoveries. Correlated variants weaken the independence assumption. Random recall k/N is an analytical reference, so no fitted-proportion CI applies.</p></section>
    <div className="validation-grid"><section className="panel"><div className="section-title"><div><span className="eyebrow">COUNT BIOLOGICAL DIVERSITY</span><h2>Family-level recovery</h2></div><Layers size={20}/></div><div className="table-scroll"><table><thead><tr><th>Cutoff</th><th>Path: families in top-k drugs</th><th>Popularity</th><th>Random expectation</th></tr></thead><tbody>{[10,20,50].map(k=><tr key={k}><th>Top {k} drugs</th><td>{path.distinct_families_at_k[k]}</td><td>{v.methods.popularity_only.distinct_families_at_k[k]}</td><td>{v.methods.random.distinct_families_at_k[k].toFixed(2)}</td></tr>)}</tbody></table></div><div className="family-null"><h3>Family-aware permutation test</h3><p>Shuffle {v.family_count.toLocaleString()} collapsed families, keeping each family together. Count labeled families among the first k cards.</p><div>{[10,20,50].map(k=><span key={k}>Top {k} cards <strong>{fp[k].observed} families</strong><small>p = {fp[k].p_value_one_sided.toFixed(3)}</small></span>)}</div><small>10,000 permutations. k=20 primary; k=10/50 exploratory, unadjusted. Grouping was defined after earlier results.</small></div></section>
    <section className="panel methods-panel"><span className="eyebrow">METHOD NOTES</span><h2>Fixed rules. No fitted weights.</h2><p>Path length penalty, degree normalization and top-10 path aggregation were fixed before the first evaluation. No hyperparameter was fitted to trial labels.</p><div className="method-item"><Check size={16}/><p>Known Alzheimer’s controls excluded from discovery counts.</p></div><div className="method-item"><Check size={16}/><p>All target–drug edges removed in both directions before graph selection and scoring.</p></div><div className="method-item"><Check size={16}/><p>All 44 discovery labels evaluated; full-set results remain retrospective after method selection.</p></div><h3>What didn’t work</h3><p>{v.embedding_note.replace(/^What didn't work:\s*/,'')}</p><div className="mrr"><span>Single-query MRR <strong>{path.metrics.mrr.toFixed(4)}</strong></span><span>Mean reciprocal rank, all 44 <strong>{path.metrics.mean_reciprocal_heldout_rank.toFixed(5)}</strong></span></div></section></div>
    <details className="panel split-panel"><summary><div><span className="eyebrow">DOCUMENTED EXPERIMENT</span><h2>Earlier 22 / 22 tuning split</h2></div><ChevronDown size={20}/></summary><p>Preserved model-selection experiment, separate from the all-44 primary evaluation. Mixture tuning chose zero embedding weight.</p><div className="table-scroll"><table><thead><tr><th>Method</th><th>Recall@10 [exact CI]</th><th>Recall@20 [exact CI]</th><th>Single-query MRR</th><th>Mean reciprocal rank, all 22</th></tr></thead><tbody>{['path_only','popularity_only','random','embedding_only','combined'].map(m=><tr key={m}><th>{names[m]}</th><RecallCell result={data.split.methods[m]} k={10}/><RecallCell result={data.split.methods[m]} k={20}/><td>{data.split.methods[m].metrics.mrr.toFixed(4)}</td><td>{data.split.methods[m].metrics.mean_reciprocal_heldout_rank.toFixed(5)}</td></tr>)}</tbody></table></div></details>
    <details className="panel controls-panel"><summary>Known controls excluded from the candidate pool <span>{data.controls.filter(c=>c.in_original_pool).length}</span></summary><p>Source-graph indication or sourced treatment registry. Graph indication alone does not verify current regulatory approval.</p><div>{data.controls.filter(c=>c.in_original_pool).map(c=><span className="badge neutral" key={c.drug_id}>{c.name}</span>)}</div></details>
  </>;
}

function App(){
  const [page,setPage]=useState('explore'),[data,setData]=useState(null),[error,setError]=useState('');
  useEffect(()=>{fetch('/api/overview').then(r=>{if(!r.ok)throw new Error('Cached data is unavailable. Run validate-primary and prepare-ui.');return r.json()}).then(setData).catch(e=>setError(e.message))},[]);
  return <><header className="topbar"><a className="brand" href="#" onClick={e=>{e.preventDefault();setPage('explore')}}><span className="brand-symbol"><Network size={22}/></span>intersect<span className="brand-sub">/ biology</span></a><nav aria-label="Main navigation"><button className={page==='explore'?'active':''} onClick={()=>setPage('explore')}><Network size={16}/>Explore</button><button className={page==='validation'?'active':''} onClick={()=>setPage('validation')}><BarChart3 size={16}/>Validation</button></nav><div className="header-label"><span className="status-dot"/>LOCAL RESEARCH DEMO</div></header>
    <main>{error?<div className="empty error"><h1>Could not load the workbench</h1><p>{error}</p></div>:!data?<div className="page-loading"><span className="spinner"/>Opening the cached research workbench…</div>:page==='explore'?<Explorer data={data}/>:<Validation data={data}/>}</main>
    <footer><span><FlaskConical size={14}/> Research hypotheses only</span><p>Trial participation does not establish efficacy. Not medical advice.</p><span>PrimeKG × trial evidence</span></footer></>;
}
createRoot(document.getElementById('root')).render(<App/>);
