import React, { useEffect, useMemo, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import cytoscape from 'cytoscape';
import dagre from 'cytoscape-dagre';
import { AlertTriangle, Network, Search, ArrowUpRight, ArrowRight, Layers, FlaskConical, ShieldCheck, ChevronDown, Maximize2, Plus, Minus, ExternalLink, Info, Check, CircleDot, BarChart3 } from 'lucide-react';
import './style.css';

const pct = n => `${(100*n).toFixed(2)}%`;
const names = {path_only:'Path scoring',popularity_only:'Popularity',random:'Random reference',embedding_only:'DistMult embedding',combined:'Tuned combined'};
const colors = {drug:'#d97742','gene/protein':'#3f8174',pathway:'#8271a6',disease:'#b66572'};
const LABEL_MAX = 28;
const clip = name => name.length > LABEL_MAX ? `${name.slice(0, LABEL_MAX - 1).trimEnd()}…` : name;
const relationText = e => e.context ? 'pathway member' : e.relations.includes('protein_protein') ? 'interacts with' : 'associated with';
cytoscape.use(dagre);

function Graph({ detail, context, pathIndex, pathLimit, onSelect }) {
  const container = useRef(null), instance = useRef(null);
  const [hovered, setHovered] = useState(null);
  useEffect(() => {
    if (!detail || !container.current) return;
    // Only the paths currently in view contribute edges; context branches hang off them.
    const shownPaths = pathIndex>=0 && detail.paths[pathIndex] ? [detail.paths[pathIndex]] : detail.paths.slice(0, pathLimit);
    const ids = new Set(shownPaths.flatMap(p=>p.nodes.map(n=>n.id)));
    let edges = detail.graph.edges.filter(e=>(context||!e.context) &&
      (e.context ? ids.has(e.source)||ids.has(e.target) : ids.has(e.source)&&ids.has(e.target)));
    const shown = new Set([...ids, ...edges.flatMap(e=>[e.source,e.target])]);
    const nodes = detail.graph.nodes.filter(n=>shown.has(n.id));
    const elements=nodes.map(n=>({data:{...n,id:String(n.id),label:clip(n.name),full:n.name,color:colors[n.type]??'#73817e',
      tier:{drug:0,'gene/protein':1,pathway:2,disease:3}[n.type]??1}}));
    // The graph is undirected, so orient each edge from the lower tier upward. This is
    // purely so the layered layout ranks drug < protein < disease/pathway and stops
    // long edges doubling back across the canvas; it asserts no biological direction.
    const tierOf=Object.fromEntries(elements.map(el=>[el.data.id,el.data.tier]));
    edges.forEach(e=>{
      let [source,target]=[String(e.source),String(e.target)];
      if((tierOf[target]??9)<(tierOf[source]??9)) [source,target]=[target,source];
      elements.push({data:{...e,id:`e-${e.id}`,source,target,label:relationText(e)}});
    });
    const cy=cytoscape({container:container.current,elements,minZoom:.3,maxZoom:3,wheelSensitivity:.18,
      layout:{name:'dagre',rankDir:'LR',nodeSep:58,rankSep:165,edgeSep:26,ranker:'network-simplex',fit:true,padding:60},
      style:[
        // Labels carry a halo (text-outline) and sit above every edge, so lines never cut through text.
        {selector:'node',style:{'background-color':'data(color)','label':'data(label)','color':'#243830','font-size':12,'font-family':'Arial','text-wrap':'wrap','text-max-width':150,'text-valign':'bottom','text-margin-y':9,width:21,height:21,'border-width':5,'border-color':'#f4f7f4','text-outline-color':'#fbfcf8','text-outline-width':3,'z-index':10}},
        {selector:'node[type="drug"]',style:{width:31,height:31,'border-color':'#f5e9dc','border-width':8,'font-weight':700}},
        {selector:'node[type="disease"]',style:{width:34,height:34,'border-color':'#f3e4e6','border-width':8,'font-weight':700}},
        {selector:'node[type="pathway"]',style:{shape:'round-rectangle',width:20,height:20,'font-size':10}},
        // No edge text by default: line style encodes the relation, the legend explains it.
        {selector:'edge',style:{width:1.5,'line-color':'#b4c4ba','curve-style':'bezier','control-point-step-size':55,'text-rotation':'autorotate','font-size':9,'color':'#5f7268','text-background-color':'#fbfcf8','text-background-opacity':1,'text-background-padding':3,'z-index':1}},
        {selector:'edge[?context]',style:{'line-style':'dashed','line-color':'#c4bdd2'}},
        {selector:'.show-label',style:{'label':'data(label)','z-index':20}},
        {selector:'.dim',style:{opacity:.16,'z-index':0}},
        {selector:'.lit',style:{'line-color':'#5c7a5f',width:2.4,'z-index':15}},
        {selector:'node:selected',style:{'border-color':'#263e35','border-width':4}}
      ]});
    instance.current=cy;
    const focus = node => {
      const connected = node.connectedEdges();
      cy.elements().addClass('dim');
      connected.removeClass('dim').addClass('lit show-label');
      connected.connectedNodes().removeClass('dim');
      node.removeClass('dim');
    };
    const clear = () => cy.elements().removeClass('dim lit show-label');
    cy.on('tap','node',e=>{onSelect(e.target.data());focus(e.target);});
    cy.on('mouseover','node',e=>{setHovered(e.target.data().full);focus(e.target);});
    cy.on('mouseout','node',()=>{setHovered(null);clear();});
    cy.on('mouseover','edge',e=>{e.target.addClass('show-label');setHovered(`${e.target.data().label} · direction unknown`);});
    cy.on('mouseout','edge',e=>{e.target.removeClass('show-label');setHovered(null);});
    cy.on('tap',e=>{if(e.target===cy){clear();onSelect(null);}});
    const observer=new ResizeObserver(()=>{cy.resize();cy.fit(undefined,60)});observer.observe(container.current);
    return ()=>{observer.disconnect();cy.destroy();instance.current=null;};
  },[detail,context,pathIndex,pathLimit]);
  return <div className="graph-shell"><div ref={container} className="graph-canvas" role="img" aria-label="Interactive biological association graph; use the accessible node list below for details"/>
    {hovered&&<div className="graph-hover">{hovered}</div>}
    <div className="graph-tools"><button aria-label="Zoom in" onClick={()=>instance.current?.zoom(instance.current.zoom()*1.2)}><Plus size={15}/></button><button aria-label="Zoom out" onClick={()=>instance.current?.zoom(instance.current.zoom()/1.2)}><Minus size={15}/></button><button aria-label="Fit graph" onClick={()=>instance.current?.fit(undefined,60)}><Maximize2 size={15}/></button></div><div className="graph-watermark">PRIMEKG <span>/ ASSOCIATION NETWORK</span></div></div>;
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

function Claim({claim}){
  return <li className={claim.verified?'claim':'claim unverified'}>
    <p>{claim.text}</p>
    {claim.verified
      ? <blockquote>“{claim.quote}”<a href={`https://pubmed.ncbi.nlm.nih.gov/${claim.pmid}/`} target="_blank" rel="noopener noreferrer">PMID {claim.pmid} <ExternalLink size={11}/></a></blockquote>
      : <span className="unverified-flag"><AlertTriangle size={12}/> Unverified — {claim.failure}. Not shown as supported.</span>}
    {claim.evidence_type&&<span className="type-tag">{claim.evidence_type}</span>}
  </li>;
}

function AgentSection({title,body,claims}){
  if(!body&&!(claims||[]).length) return null;
  return <div className="agent-section"><h4>{title}</h4>{body&&<p>{body}</p>}
    <ul className="claims">{(claims||[]).map((c,i)=><Claim key={i} claim={c}/>)}</ul></div>;
}

function LiteratureBody({data,onRunLive}){
  const counts=data.claim_counts;
  return <div className="literature">
    <div className="hypothesis-banner"><AlertTriangle size={15}/><span><strong>Research hypothesis, not medical advice.</strong> {(data.disclaimer||'').replace(/^Research hypothesis, not medical advice\.\s*/,'')}</span></div>
    <div className="literature-meta">
      <span className={`badge ${data.freshness==='live'?'green':'neutral'}`}>{data.freshness==='live'?'Live query':'Cached'}</span>
      <span className="badge neutral">{data.model}</span>
      <span className="badge neutral">Direction: {data.direction}</span>
      {(data.evidence_types||[]).map(t=><span key={t} className="type-tag">{t}</span>)}
      <span className="claim-count">{counts.verified}/{counts.total} claims verified{counts.failed?`, ${counts.failed} flagged`:''}</span>
      {onRunLive&&<button className="toggle-all" onClick={onRunLive}>Re-run live</button>}
    </div>
    {data.live_error&&<p className="fine-print">Live query unavailable, showing cached review: {data.live_error}</p>}
    <AgentSection title="Synthesis" body={data.synthesis.summary} claims={data.synthesis.claims}/>
    {!!(data.synthesis.open_questions||[]).length&&<div className="agent-section"><h4>Open questions</h4><ul className="questions">{data.synthesis.open_questions.map((q,i)=><li key={i}>{q}</li>)}</ul></div>}
    <AgentSection title="Mechanism analyst" body={data.mechanism.summary} claims={data.mechanism.claims}/>
    <AgentSection title="Safety analyst" body={data.safety.summary} claims={data.safety.claims}/>
    <AgentSection title="Skeptic" body={data.skeptic.counter_evidence} claims={data.skeptic.claims}/>
    <details className="retrieval-detail"><summary>Retrieved records ({data.retrieval.retrieved_count}) and query</summary>
      <p className="mono">{data.retrieval.query}</p>
      <ul>{Object.values(data.records).map(r=><li key={r.pmid}><a href={r.url} target="_blank" rel="noopener noreferrer">PMID {r.pmid}</a> · {r.journal} {r.year} — {r.title}</li>)}</ul>
      <p className="fine-print">{data.verification.method}. A claim citing a PMID outside this set, or quoting text that is not in it, is flagged and never shown as supported. {data.scope}</p>
    </details>
  </div>;
}

function LiteraturePanel({family,evidence}){
  const [data,setData]=useState(null),[state,setState]=useState('idle'),[error,setError]=useState('');
  const cached=evidence.cached_family_ids.includes(family.id);
  useEffect(()=>{setData(null);setState('idle');setError('');if(!cached)return;
    setState('loading');
    fetch(`/api/evidence/${encodeURIComponent(family.id)}`).then(r=>r.ok?r.json():Promise.reject(new Error('No cached review')))
      .then(d=>{setData(d);setState('ready')}).catch(e=>{setError(e.message);setState('error')});},[family.id,cached]);
  const runLive=()=>{setState('loading');
    fetch(`/api/evidence/${encodeURIComponent(family.id)}?live=1&session=${SESSION}`).then(r=>r.ok?r.json():Promise.reject(new Error('Live query failed')))
      .then(d=>{setData(d);setState('ready')}).catch(e=>{setError(e.message);setState('error')});};
  if(!cached&&state==='idle') return <div className="literature-pending"><FlaskConical size={25}/><div><h3>No cached review for this family</h3>
    <p>Agent review is cached for the top {evidence.cached_family_ids.length} ranked families. Nothing is generated on the fly for the rest, so no unverified text is shown here.</p>
    <span className="badge neutral">Not reviewed</span></div></div>;
  if(state==='loading') return <div className="graph-loading"><span className="spinner"/> Loading the cached literature review…</div>;
  if(state==='error') return <div className="empty error"><p>{error}</p></div>;
  if(!data) return null;
  return <LiteratureBody data={data} onRunLive={evidence.live_available?runLive:null}/>;
}

function EvidencePanel({detail,node,family,evidence,tabRequest}){
  const [tab,setTab]=useState('graph');
  useEffect(()=>{if(tabRequest?.tab) setTab(tabRequest.tab==='literature'?'literature':'graph');},[tabRequest]);
  return <section className="evidence panel"><div className="section-title"><h2>Evidence & provenance</h2><span className="badge neutral">Graph evidence available</span></div>
    <div className="small-tabs" role="tablist" aria-label="Evidence views">{[['graph','Graph sources'],['trials','Trial records'],['literature','Literature review']].map(([id,label])=><button key={id} role="tab" aria-selected={tab===id} onClick={()=>setTab(id)}>{label}{id==='trials'&&<span>{detail?.trials.length??0}</span>}</button>)}</div>
    {tab==='graph'&&<div className="evidence-grid"><div><div className="source-mark">01 <span>STRUCTURED EVIDENCE</span></div><h3>{node?.label??'Trace every connection'}</h3><p>{node?`${node.type} · ${node.source} identifier: ${node.source_id}`:'Select a node to inspect its source identifier. Every solid edge shown belongs to a scored path in the sanitized PrimeKG graph.'}</p>
      {node&&(node.url?<a className="entity-link" href={node.url} target="_blank" rel="noopener noreferrer">Open in {node.source} <ExternalLink size={13}/></a>:<span className="no-link">No reliable external page for this identifier</span>)}
      <a className="dataset-link" href="https://doi.org/10.7910/DVN/IXA7BM" target="_blank" rel="noopener noreferrer">PrimeKG source dataset <ExternalLink size={12}/></a></div><div className="evidence-note"><ShieldCheck size={20}/><strong>What the graph can tell us</strong><p>Association and pathway membership. Activation, inhibition and treatment benefit remain unverified.</p><span>Direction unknown on all displayed edges</span></div></div>}
    {tab==='trials'&&<div className="trial-list">{detail?.trials.length?detail.trials.map((t,i)=><a key={`${t.nct_id}-${i}`} href={t.url} target="_blank" rel="noopener noreferrer"><span className="mono">{t.nct_id}</span><strong>{t.title}</strong><span>{t.status.toLowerCase()} · {t.enrollment} enrolled <ExternalLink size={13}/></span></a>):<p className="muted">No eligible exact-matched trial record in this cached snapshot. This does not establish that no trial exists.</p>}<p className="fine-print">Trial registrations document testing, not efficacy. They are excluded from graph scoring.</p></div>}
    {tab==='literature'&&<LiteraturePanel family={family} evidence={evidence}/>}
  </section>;
}

function Explorer({data,focus}){
  const [selected,setSelected]=useState(data.families[0].id),[drug,setDrug]=useState(data.families[0].representative_id),[detail,setDetail]=useState(null),[error,setError]=useState(''),[context,setContext]=useState(false),[pathIndex,setPathIndex]=useState(-1),[allPaths,setAllPaths]=useState(false),[node,setNode]=useState(null);
  const DEFAULT_PATHS=3, pathLimit=allPaths?Infinity:DEFAULT_PATHS;
  const choosePath=i=>{setPathIndex(i);setContext(i>=0);};
  const [tabRequest,setTabRequest]=useState(null);
  useEffect(()=>{if(!focus)return;
    if(data.families.some(f=>f.id===focus.familyId)) setSelected(focus.familyId);
    setTabRequest({tab:focus.tab,at:focus.at});},[focus]);
  const family=data.families.find(f=>f.id===selected),variant=family.members.find(m=>m.drug_id===drug)??family.members[0];
  useEffect(()=>{setDrug(family.representative_id);setPathIndex(-1);setContext(false);setNode(null)},[selected]);
  useEffect(()=>{const controller=new AbortController();setDetail(null);setError('');setNode(null);setPathIndex(-1);setContext(false);setAllPaths(false);fetch(`/api/drugs/${drug}`,{signal:controller.signal}).then(r=>{if(!r.ok)throw new Error('Could not load cached graph');return r.json()}).then(setDetail).catch(e=>{if(e.name!=='AbortError')setError(e.message)});return()=>controller.abort()},[drug]);
  return <><div className="page-heading"><div><span className="eyebrow">ALZHEIMER’S RESEARCH WORKBENCH</span><h1>Follow the evidence.</h1><p>Explore biological connections. Inspect the uncertainty.</p></div><div className="snapshot"><span className="status-dot"/> Cached research snapshot <small>PrimeKG · 3-hop disease neighborhood</small></div></div>
    <div className="overview-strip"><div><Network size={18}/><strong>{data.validation.candidate_count.toLocaleString()}</strong><span>eligible drugs</span></div><div><Layers size={18}/><strong>{data.validation.family_count.toLocaleString()}</strong><span>distinct families</span></div><div><ShieldCheck size={18}/><strong>Path-only</strong><span>fixed, explainable scoring</span></div><div><span className="tiny-pill">RESEARCH USE</span><span>Hypotheses, not treatment advice</span></div></div>
    <div className="workbench"><CandidateList families={data.families} selected={selected} onSelect={setSelected}/><div className="detail-column">
      <section className="graph-panel panel"><div className="detail-heading"><div><span className="eyebrow">FAMILY {String(family.rank).padStart(2,'0')} / {family.members.length>1?'GROUPED VARIANTS':'SINGLE COMPOUND'}</span><h2>{family.name}</h2></div><span className="badge green"><Check size={12}/> Sourced graph paths</span></div>
      <div className="variant-bar"><label>Viewing <select aria-label="Drug variant" value={drug} onChange={e=>setDrug(Number(e.target.value))}>{family.members.map(m=><option key={m.drug_id} value={m.drug_id}>{m.name}</option>)}</select></label><div><span>Path score</span><strong>{variant.path_score.toFixed(4)}</strong><i/> <span>{variant.path_count} paths</span></div></div>
      <div className="graph-toolbar"><div className="legend">{[['drug','Drug'],['gene/protein','Protein'],['pathway','Pathway'],['disease','Disease']].map(([id,label])=><span key={id}><i style={{background:colors[id]}}/>{label}</span>)}<span className="legend-line"><i className="line solid"/>Association</span><span className="legend-line"><i className="line dashed"/>Pathway member</span></div><label className="check"><input type="checkbox" checked={context} onChange={e=>setContext(e.target.checked)}/>Pathway context</label></div>
      {error?<div className="empty error">{error}</div>:detail?<Graph detail={detail} context={context} pathIndex={pathIndex} pathLimit={pathLimit} onSelect={setNode}/>:<div className="graph-loading"><span className="spinner"/> Loading sourced connections…</div>}
      <div className="path-selector"><span>Scored paths</span><button className={pathIndex===-1?'active':''} onClick={()=>choosePath(-1)}>{allPaths?'All':`Top ${Math.min(DEFAULT_PATHS,detail?.paths.length??0)}`}</button>{detail?.paths.map((p,i)=><button key={i} className={pathIndex===i?'active':''} onClick={()=>choosePath(i)}>Path {i+1}</button>)}{detail&&!detail.paths.length&&<span className="muted">No scored path in this subgraph</span>}
        {detail&&detail.paths.length>DEFAULT_PATHS&&<button className="toggle-all" onClick={()=>{setAllPaths(!allPaths);setPathIndex(-1);setContext(false);}}>{allPaths?`Show top ${DEFAULT_PATHS} paths`:`Show all ${detail.paths.length} paths`}</button>}</div>
      <div className="graph-caption"><Info size={14}/><span>Hover a node to highlight its connections and read relation labels. Connections show associations, not causality. Dashed pathway branches are context only.</span></div>
      {detail&&<details className="node-list"><summary>Accessible node and connection list</summary><div>{detail.graph.nodes.map(n=><button key={n.id} onClick={()=>setNode({...n,label:n.name})}>{n.name}<small>{n.type}</small></button>)}</div><ul>{detail.graph.edges.map(e=><li key={e.id}>{detail.graph.nodes.find(n=>n.id===e.source)?.name} ↔ {detail.graph.nodes.find(n=>n.id===e.target)?.name}: {e.relations.join(', ')}; direction unknown{e.context?' (context)':''}</li>)}</ul></details>}
      </section><EvidencePanel detail={detail} node={node} family={family} evidence={data.evidence} tabRequest={tabRequest}/>
    </div></div></>;
}

function RecallCell({result,k}){const key=`recall_at_${k}`,ci=result.exact_95_ci?.[key];return <td><strong>{pct(result.metrics[key])}</strong><small>{ci?`${pct(ci[0])}–${pct(ci[1])}`:'Exact random reference'}</small></td>}
function Validation({data}){
  const v=data.validation,path=v.methods.path_only,fp=v.family_permutation.results;
  return <><div className="page-heading"><div><span className="eyebrow">VALIDATION / ALL 44 DISCOVERY LABELS</span><h1>A small signal, with limits.</h1><p>Lift over baselines. Every denominator and assumption visible.</p></div><span className="badge green"><ShieldCheck size={14}/> Untuned path scoring</span></div>
    <div className="validation-stats"><article><span>RECALL @ 20</span><strong>{pct(path.metrics.recall_at_20)}</strong><p>4 of 44 trial-tested drugs</p><small>95% exact CI {pct(path.exact_95_ci.recall_at_20[0])}–{pct(path.exact_95_ci.recall_at_20[1])}</small></article><article><span>LIFT OVER RANDOM @ 20</span><strong>{path.metrics.enrichment_at_20.toFixed(2)}<em>×</em></strong><p>vs. exact random expectation</p><small>+{path.lift['20'].vs_popularity_percentage_points.toFixed(2)} percentage points over popularity</small></article><article><span>DISTINCT FAMILIES @ 20 DRUGS</span><strong>{path.distinct_families_at_k['20']}<em> / {v.positive_family_count}</em></strong><p>{path.recovered_families_at_k['20'].join(' + ')||'None recovered'}</p><small>Family-card permutation p = {fp['20'].p_value_one_sided.toFixed(3)}</small></article></div>
    <div className="caution"><Info size={21}/><div><strong>Small sample. Related compounds.</strong><p>{v.small_sample_note} {v.efficacy_note}</p></div></div>
    <div className="caution scope"><ShieldCheck size={21}/><div><strong>These numbers cover the graph ranking only.</strong><p>Literature agents read the ranked candidates; nothing they produce feeds back into the ranking or into any figure on this page. No agent output was used to fit, tune or select anything.</p></div></div>
    <section className="panel validation-table"><div className="section-title"><div><span className="eyebrow">PRIMARY VALIDATION</span><h2>Per-drug recall & baseline lift</h2></div><span className="muted">{v.candidate_count.toLocaleString()} candidates · 44 labels</span></div><div className="table-scroll"><table><thead><tr><th>Ranking method</th><th>Recall@10 <small>95% Clopper–Pearson CI</small></th><th>Recall@20 <small>95% Clopper–Pearson CI</small></th><th>Recall@50 <small>secondary</small></th><th>Recall@100 <small>secondary</small></th><th>Enrichment@20</th></tr></thead><tbody>{['path_only','popularity_only','random'].map(m=><tr className={m==='path_only'?'highlight':''} key={m}><th>{names[m]}{m==='path_only'&&<span className="badge green">Primary</span>}</th>{[10,20,50,100].map(k=><RecallCell key={k} result={v.methods[m]} k={k}/>)}<td>{v.methods[m].metrics.enrichment_at_20.toFixed(2)}×</td></tr>)}</tbody></table></div><p className="table-note">Exact intervals use integer drug recoveries. Correlated variants weaken the independence assumption. Random recall k/N is an analytical reference, so no fitted-proportion CI applies.</p></section>
    <div className="validation-grid"><section className="panel"><div className="section-title"><div><span className="eyebrow">COUNT BIOLOGICAL DIVERSITY</span><h2>Family-level recovery</h2></div><Layers size={20}/></div><div className="table-scroll"><table><thead><tr><th>Cutoff</th><th>Path: families in top-k drugs</th><th>Popularity</th><th>Random expectation</th></tr></thead><tbody>{[10,20,50].map(k=><tr key={k}><th>Top {k} drugs</th><td>{path.distinct_families_at_k[k]}</td><td>{v.methods.popularity_only.distinct_families_at_k[k]}</td><td>{v.methods.random.distinct_families_at_k[k].toFixed(2)}</td></tr>)}</tbody></table></div><div className="family-null"><h3>Family-aware permutation test</h3><p>Shuffle {v.family_count.toLocaleString()} collapsed families, keeping each family together. Count labeled families among the first k cards.</p><div>{[10,20,50].map(k=><span key={k}>Top {k} cards <strong>{fp[k].observed} families</strong><small>p = {fp[k].p_value_one_sided.toFixed(3)}</small></span>)}</div><small>10,000 permutations. k=20 primary; k=10/50 exploratory, unadjusted. Grouping was defined after earlier results.</small></div></section>
    <section className="panel methods-panel"><span className="eyebrow">METHOD NOTES</span><h2>Fixed rules. No fitted weights.</h2><p>Path length penalty, degree normalization and top-10 path aggregation were fixed before the first evaluation. No hyperparameter was fitted to trial labels.</p><div className="method-item"><Check size={16}/><p>Known Alzheimer’s controls excluded from discovery counts.</p></div><div className="method-item"><Check size={16}/><p>All target–drug edges removed in both directions before graph selection and scoring.</p></div><div className="method-item"><Check size={16}/><p>All 44 discovery labels evaluated; full-set results remain retrospective after method selection.</p></div><h3>What didn’t work</h3><p>{v.embedding_note.replace(/^What didn't work:\s*/,'')}</p><div className="mrr"><span>Single-query MRR <strong>{path.metrics.mrr.toFixed(4)}</strong></span><span>Mean reciprocal rank, all 44 <strong>{path.metrics.mean_reciprocal_heldout_rank.toFixed(5)}</strong></span></div></section></div>
    <details className="panel split-panel"><summary><div><span className="eyebrow">DOCUMENTED EXPERIMENT</span><h2>Earlier 22 / 22 tuning split</h2></div><ChevronDown size={20}/></summary><p>Preserved model-selection experiment, separate from the all-44 primary evaluation. Mixture tuning chose zero embedding weight.</p><div className="table-scroll"><table><thead><tr><th>Method</th><th>Recall@10 [exact CI]</th><th>Recall@20 [exact CI]</th><th>Single-query MRR</th><th>Mean reciprocal rank, all 22</th></tr></thead><tbody>{['path_only','popularity_only','random','embedding_only','combined'].map(m=><tr key={m}><th>{names[m]}</th><RecallCell result={data.split.methods[m]} k={10}/><RecallCell result={data.split.methods[m]} k={20}/><td>{data.split.methods[m].metrics.mrr.toFixed(4)}</td><td>{data.split.methods[m].metrics.mean_reciprocal_heldout_rank.toFixed(5)}</td></tr>)}</tbody></table></div></details>
    <details className="panel controls-panel"><summary>Known controls excluded from the candidate pool <span>{data.controls.filter(c=>c.in_original_pool).length}</span></summary><p>Source-graph indication or sourced treatment registry. Graph indication alone does not verify current regulatory approval.</p><div>{data.controls.filter(c=>c.in_original_pool).map(c=><span className="badge neutral" key={c.drug_id}>{c.name}</span>)}</div></details>
  </>;
}

const GROUPS=[
  ['evidence retrieved, no trial record found','Evidence retrieved, no trial record found','Verified literature claims exist, and this dataset holds no matched Alzheimer’s trial record. That is a gap in the dataset, not a statement that the drug is untested.'],
  ['already in trials','Already in trials','A matched ClinicalTrials.gov record exists for a family member in this snapshot. Registration documents testing, not efficacy.'],
  ['contested or possible wrong direction','Contested or possible wrong direction','The retrieved records disagree, or report the drug acting against the hypothesis. Read the skeptic before anything else.'],
  ['no evidence retrieved','No evidence retrieved','No verified claim survived checking for this query. That is absence in the retrieved set, not proof that no evidence exists.'],
];
const TIER_ORDER=['human trial','animal','in vitro','review','other'];
const VERDICT_TONE={'supported by human evidence':'green','animal or in vitro only':'neutral','mixed or contested':'amber','possible wrong direction':'amber','none in the retrieved set':'neutral'};

function GapCard({card,onOpen}){
  const tiers=card.evidence_tier_counts||{};
  const ordered=TIER_ORDER.filter(t=>tiers[t]);
  const q=card.supporting_quote;
  return <article className="gap-card">
    <header><span className="rank">{String(card.rank).padStart(2,'0')}</span><h3>{card.family_name}</h3><span className={`badge ${VERDICT_TONE[card.verdict]??'neutral'}`}>{card.verdict}</span></header>
    {q&&<blockquote className="verdict-quote">“{q.quote}”<a href={`https://pubmed.ncbi.nlm.nih.gov/${q.pmid}/`} target="_blank" rel="noopener noreferrer">PMID {q.pmid} <ExternalLink size={11}/></a></blockquote>}
    <div className="gap-strength"><span>Path strength</span><div className="score-track"><i style={{width:`${Math.max(3,card.path_strength*100)}%`}}/></div><strong>{card.path_score.toFixed(3)}</strong></div>
    {!!ordered.length&&<div className="tier-breakdown"><span>Verified claims by evidence type</span><div>{ordered.map(t=><span key={t} className={`tier tier-${t.replace(/ /g,'-')}`}>{t}<strong>{tiers[t]}</strong></span>)}</div></div>}
    {card.disease_relevance&&<div className={`relevance relevance-${card.disease_relevance.key}`} title={card.disease_relevance.note}>{card.disease_relevance.label}{card.disease_relevance.human_claims?<em>{card.disease_relevance.human_claims_in_alzheimer}/{card.disease_relevance.human_claims} human claims name an Alzheimer's context</em>:null}</div>}
    <dl className="gap-facts">
      <div><dt>Verified claims</dt><dd>{card.verified_claims}</dd></div>
      <div><dt>Records retrieved</dt><dd>{card.retrieved_count}</dd></div>
      <div><dt>Trial records in dataset</dt><dd>{card.trial_count||'none found'}</dd></div>
    </dl>
    <p className="gap-direction">Direction: {card.direction}</p>
    {card.members.length>1&&<p className="gap-members">{card.members.length} variants: {card.members.join(', ')}</p>}
    <footer><span className="badge neutral">{card.freshness}</span>
      <button onClick={()=>onOpen(card,'graph')}>Graph paths <ArrowUpRight size={13}/></button>
      <button onClick={()=>onOpen(card,'literature')}>Evidence <ArrowUpRight size={13}/></button></footer>
  </article>;
}

function GapMap({onOpen}){
  const [data,setData]=useState(null),[error,setError]=useState('');
  useEffect(()=>{fetch('/api/gap-map').then(r=>r.ok?r.json():Promise.reject(new Error('Run build-gap-map first'))).then(setData).catch(e=>setError(e.message))},[]);
  if(error) return <div className="empty error"><h1>Gap map unavailable</h1><p>{error}</p></div>;
  if(!data) return <div className="page-loading"><span className="spinner"/>Loading the evidence gap map…</div>;
  return <><div className="page-heading"><div><span className="eyebrow">EVIDENCE GAP MAP / TOP {data.families.length} FAMILIES</span><h1>Where the evidence isn’t.</h1><p>Graph strength, verified literature and trial status, side by side.</p></div><span className="badge green"><ShieldCheck size={14}/> Display only</span></div>
    <div className="hypothesis-banner wide"><AlertTriangle size={15}/><span><strong>Research hypothesis, not medical advice.</strong> {data.scope}</span></div>
    <div className="gap-columns">{GROUPS.map(([id,title,blurb])=>{
      const cards=data.families.filter(f=>f.group===id);
      return <section key={id} className={`gap-column ${id.replace(/ /g,'-')}`}>
        <div className="gap-column-head"><h2>{title}<span>{cards.length}</span></h2><p>{blurb}</p></div>
        {cards.map(c=><GapCard key={c.family_id} card={c} onOpen={onOpen}/>)}
        {!cards.length&&<p className="muted empty-column">No families in this group.</p>}
      </section>;})}</div>
    {data.verification&&<section className="panel verification-strip"><div className="section-title"><div><span className="eyebrow">CITATION VERIFICATION, WHOLE CACHE</span><h2>What survived checking</h2></div><ShieldCheck size={20}/></div>
      <div className="verification-stats">
        <div><span>Families reviewed</span><strong>{data.verification.families_reviewed}</strong></div>
        <div><span>With ≥1 verified claim</span><strong>{data.verification.families_with_a_verified_claim}</strong></div>
        <div><span>Claims generated</span><strong>{data.verification.claims_generated}</strong></div>
        <div><span>Verified</span><strong>{data.verification.claims_verified}</strong></div>
        <div><span>Dropped or flagged</span><strong>{data.verification.claims_dropped_or_flagged}</strong></div>
        <div><span>Failure fraction</span><strong>{(data.verification.failure_fraction*100).toFixed(2)}%</strong></div>
      </div>
      <p className="table-note">{data.verification.method}{Object.keys(data.verification.failure_reasons||{}).length?` Reasons: ${Object.entries(data.verification.failure_reasons).map(([r,n])=>`${r} (${n})`).join(', ')}.`:''}</p></section>}
    <p className="table-note">Verdicts are <strong>rule-based heuristics</strong> over the agents’ structured output: fixed keyword vocabularies over the reported direction plus the evidence-type tags, not a clinical judgement. Read the quote on each card before trusting its label. {data.absence_note} Verdicts derive deterministically from verified claims and their evidence-type tags; unverified claims are excluded. These are triage categories for researchers, not a ranking of which drugs work.</p></>;
}

const SESSION = Math.random().toString(36).slice(2, 12);

function CheckIdea(){
  const [drug,setDrug]=useState(''),[result,setResult]=useState(null),[state,setState]=useState('idle'),[error,setError]=useState('');
  const [context,setContext]=useState(false),[pathIndex,setPathIndex]=useState(-1),[node,setNode]=useState(null);
  const run=(live)=>{
    if(!drug.trim()) return;
    setState('loading');setError('');setNode(null);setPathIndex(-1);
    const url=`/api/check?drug=${encodeURIComponent(drug.slice(0,100))}&disease=${encodeURIComponent("Alzheimer's disease")}&live=${live?1:0}&session=${SESSION}`;
    fetch(url).then(r=>r.ok?r.json():Promise.reject(new Error('Check failed')))
      .then(d=>{setResult(d);setState('ready')}).catch(e=>{setError(e.message);setState('error')});
  };
  const detail=result&&result.status==='ok'?{drug_id:result.drug.drug_id,paths:result.paths,graph:result.graph,trials:result.trials}:null;
  return <><div className="page-heading"><div><span className="eyebrow">CHECK MY IDEA</span><h1>Have a hunch?</h1><p>Look a drug up against the same graph, the same agents and the same checker.</p></div><span className="badge neutral">Alzheimer’s disease only</span></div>
    <div className="hypothesis-banner wide"><AlertTriangle size={15}/><span><strong>Research hypothesis, not medical advice.</strong> This reports what the graph and the retrieved literature say. It is not a treatment recommendation, and nothing here changes the ranking or the validation numbers.</span></div>
    <form className="check-form panel" onSubmit={e=>{e.preventDefault();run(false)}}>
      <label>Drug<input value={drug} maxLength={100} onChange={e=>setDrug(e.target.value)} placeholder="e.g. metformin, rapamycin, insulin detemir" aria-label="Drug name"/></label>
      <label>Disease<input value="Alzheimer's disease" disabled aria-label="Disease"/><small>The only disease built in this workbench.</small></label>
      <div className="check-actions"><button type="submit" className="primary">Check</button>
        {result?.live_available&&<button type="button" onClick={()=>run(true)}>Run agents live</button>}</div>
    </form>
    {state==='loading'&&<div className="page-loading"><span className="spinner"/>Resolving against the graph…</div>}
    {state==='error'&&<div className="empty error"><p>{error}</p></div>}
    {state==='ready'&&result&&<section className="check-result">
      {result.status!=='ok'
        ? <div className={`panel check-message ${result.status}`}>
            <h2>{result.known_control?'Known control · excluded from discovery':result.status==='not_in_graph'?'Not in this graph':result.status==='no_path'?(result.in_discovery_pool?'No scored path in this snapshot':'Outside the discovery pool'):result.status==='unsupported_disease'?'Only Alzheimer’s is built':result.status==='ambiguous'?'That synonym matches several drugs':'Enter a drug'}</h2>
            <p>{result.message}</p>
            {!!(result.candidates||[]).length&&<div className="suggestions"><span>Choose one</span>{result.candidates.map(c=><button key={c.drug_id} onClick={()=>{setDrug(c.name);}}>{c.name}<small>{c.source_id}</small></button>)}</div>}
            {!!(result.suggestions||[]).length&&<div className="suggestions"><span>Did you mean</span>{result.suggestions.map(s=><button key={s} onClick={()=>{setDrug(s);}}>{s}</button>)}</div>}
            {result.drug&&<p className="fine-print">{result.drug.match_note?result.drug.match_note+'. ':''}Resolved to the graph node “{result.drug.name}”{result.drug.source_id?` (${result.drug.source_id})`:''}.</p>}
          </div>
        : <>
          <div className="check-summary panel">
            <div><span className="eyebrow">RESOLVED</span><h2>{result.drug.name}</h2>{result.drug.match_note&&<p className="match-note"><Check size={12}/> {result.drug.match_note}</p>}<p className="fine-print">{result.drug.source_id} · family {result.family?.name??'ungrouped'}{result.family?` · rank ${result.family.rank}`:''}</p></div>
            <div className="check-stats">
              <div><span>Path score</span><strong>{result.path_score?.toFixed(4)??'—'}</strong></div>
              <div><span>Scored paths</span><strong>{result.path_count}</strong></div>
              <div><span>Matched trials</span><strong>{result.trials?.length||'none'}</strong></div>
              <div><span>Verdict</span><strong className="verdict">{result.verdict??'none in the retrieved set'}</strong>{result.disease_relevance&&<small className="relevance-inline">{result.disease_relevance.label}</small>}</div>
            </div>
            <div className="check-flags"><span className={`badge ${result.freshness==='live'?'green':'neutral'}`}>{result.freshness==='none'?'no review':result.freshness}</span>
              {!result.live_available&&<span className="badge neutral">live queries unavailable — offline mode or no API key</span>}
              {result.rate_limit&&<span className="badge neutral">{result.rate_limit.remaining} live checks left this session</span>}</div>
            {result.live_error&&<p className="fine-print">{result.live_error}</p>}
          </div>
          <section className="graph-panel panel">
            <div className="graph-toolbar"><div className="legend">{[['drug','Drug'],['gene/protein','Protein'],['pathway','Pathway'],['disease','Disease']].map(([id,label])=><span key={id}><i style={{background:colors[id]}}/>{label}</span>)}<span className="legend-line"><i className="line solid"/>Association</span><span className="legend-line"><i className="line dashed"/>Pathway member</span></div><label className="check"><input type="checkbox" checked={context} onChange={e=>setContext(e.target.checked)}/>Pathway context</label></div>
            <Graph detail={detail} context={context} pathIndex={pathIndex} pathLimit={3} onSelect={setNode}/>
            <div className="path-selector"><span>Scored paths</span><button className={pathIndex===-1?'active':''} onClick={()=>{setPathIndex(-1);setContext(false)}}>Top 3</button>{result.paths.map((p,i)=><button key={i} className={pathIndex===i?'active':''} onClick={()=>{setPathIndex(i);setContext(true)}}>Path {i+1}</button>)}</div>
            <div className="graph-caption"><Info size={14}/><span>Connections show associations, not causality. Direction unknown on every edge.</span></div>
          </section>
          {result.evidence
            ? <section className="evidence panel"><div className="section-title"><h2>Evidence &amp; provenance</h2><span className={`badge ${result.freshness==='live'?'green':'neutral'}`}>{result.freshness}</span></div>
                <LiteratureBody data={{...result.evidence,freshness:result.freshness,live_error:result.live_error}}/></section>
            : <div className="panel literature-pending"><FlaskConical size={25}/><div><h3>No review for this drug</h3><p>{result.evidence_message}</p><span className="badge neutral">Not reviewed</span></div></div>}
        </>}
    </section>}</>;
}

function App(){
  const [page,setPage]=useState('explore'),[data,setData]=useState(null),[error,setError]=useState('');
  const [focus,setFocus]=useState(null);
  useEffect(()=>{fetch('/api/overview').then(r=>{if(!r.ok)throw new Error('Cached data is unavailable. Run validate-primary and prepare-ui.');return r.json()}).then(setData).catch(e=>setError(e.message))},[]);
  const openFamily=(card,tab)=>{setFocus({familyId:card.family_id,tab,at:Date.now()});setPage('explore');};
  const nav=[['explore','Explore',Network],['gaps','Gap map',Layers],['check','Check my idea',FlaskConical],['validation','Validation',BarChart3]];
  return <><header className="topbar"><a className="brand" href="#" onClick={e=>{e.preventDefault();setPage('explore')}}><span className="brand-symbol"><Network size={22}/></span>intersect<span className="brand-sub">/ biology</span></a><nav aria-label="Main navigation">{nav.map(([id,label,Icon])=><button key={id} className={page===id?'active':''} onClick={()=>setPage(id)}><Icon size={16}/>{label}</button>)}</nav><div className="header-label"><span className="status-dot"/>LOCAL RESEARCH DEMO</div></header>
    <main>{error?<div className="empty error"><h1>Could not load the workbench</h1><p>{error}</p></div>:!data?<div className="page-loading"><span className="spinner"/>Opening the cached research workbench…</div>:page==='gaps'?<GapMap onOpen={openFamily}/>:page==='check'?<CheckIdea/>:page==='validation'?<Validation data={data}/>:<Explorer data={data} focus={focus}/>}</main>
    <footer><span><FlaskConical size={14}/> Research hypotheses only</span><p>Trial participation does not establish efficacy. Not medical advice.</p><span>PrimeKG × trial evidence</span></footer></>;
}
createRoot(document.getElementById('root')).render(<App/>);
