import './price-index.css';
type Point={period:string;value:string|number};
type MarketIndex={id:string;title:string;currency:string;territory:string;statistic:string;unit_scope:string;method:string;notes:string;method_source_url:string;source:{title:string;url:string;publisher:string};points:Point[]};
const monthNames=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const monthLabel=(period:string)=>`${monthNames[Number(period.slice(5))-1]} ${period.slice(0,4)}`;
const ordinal=(period:string)=>Number(period.slice(0,4))*12+Number(period.slice(5))-1;

/** A contextual survey series is never mixed with dated individual bottle offers. */
export function marketIndexesHTML(indexes:MarketIndex[]|undefined,esc:(value:unknown)=>string):string{
 return (indexes||[]).map(index=>{
  const points=index.points.filter(p=>/^[12]\d{3}-(0[1-9]|1[0-2])$/.test(p.period)&&Number(p.value)>0&&Number.isFinite(Number(p.value))).sort((a,b)=>a.period.localeCompare(b.period));
  if(!points.length)return '';
  const first=points[0],last=points[points.length-1],values=points.map(p=>Number(p.value));
  const min=Math.min(...values),max=Math.max(...values),padding=Math.max((max-min)*.15,max*.025,1),lower=Math.max(0,min-padding),upper=max+padding;
  const start=ordinal(first.period),span=Math.max(1,ordinal(last.period)-start);
  const x=(p:Point)=>64+(ordinal(p.period)-start)/span*880,y=(p:Point)=>230-(Number(p.value)-lower)/(upper-lower)*180;
  const format=(value:number)=>new Intl.NumberFormat('en',{maximumFractionDigits:2}).format(value);
  const path=points.map((p,i)=>`${i&&ordinal(p.period)-ordinal(points[i-1].period)===1?'L':'M'}${x(p).toFixed(2)},${y(p).toFixed(2)}`).join(' ');
  const ticks=[0,.5,1].map(f=>{const value=lower+(upper-lower)*f,py=230-f*180;return `<line x1="64" x2="944" y1="${py}" y2="${py}"/><text x="52" y="${py+4}" text-anchor="end">${esc(format(value))}</text>`;}).join('');
  const middle=points[Math.floor((points.length-1)/2)],axis=[first,middle,last].filter((p,i,a)=>a.findIndex(v=>v.period===p.period)===i).map((p,i,a)=>`<text x="${x(p)}" y="264" text-anchor="${i===0?'start':i===a.length-1?'end':'middle'}">${esc(monthLabel(p.period))}</text>`).join('');
  return `<section class="market-index" aria-label="${esc(index.title)}"><div class="market-index-heading"><div><span class="eyebrow">A LONGER VIEW / ${esc(index.territory)}</span><h3>${esc(index.title)}</h3><p>${esc(index.statistic)} · ${esc(index.currency)}</p></div><div class="market-index-latest"><strong>${esc(format(Number(last.value)))}</strong><span>${esc(index.currency)} · ${esc(monthLabel(last.period))}</span></div></div><figure><svg viewBox="0 0 980 284" role="img" aria-label="${esc(index.title)}: ${points.length} monthly observations, ${esc(monthLabel(first.period))} to ${esc(monthLabel(last.period))}. Values range from ${esc(format(min))} to ${esc(format(max))} ${esc(index.currency)}."><g class="market-index-grid">${ticks}${axis}</g><path class="market-index-line" d="${path}"/>${points.map(p=>`<circle class="market-index-point" cx="${x(p).toFixed(2)}" cy="${y(p).toFixed(2)}" r="5"><title>${esc(monthLabel(p.period))}: ${esc(format(Number(p.value)))} ${esc(index.currency)}</title></circle>`).join('')}</svg><figcaption>${points.length} recorded months · ${esc(index.unit_scope)}.</figcaption></figure><div class="market-index-links"><a href="${esc(index.source.url)}" target="_blank" rel="noopener noreferrer">${esc(index.source.publisher)} source ↗</a><details><summary>How to read this series</summary><p>${esc(index.method)}</p><p>${esc(index.notes)}</p>${index.method_source_url?`<a href="${esc(index.method_source_url)}" target="_blank" rel="noopener noreferrer">Original survey reference ↗</a>`:''}</details></div><details class="market-index-records"><summary>Explore every month <span>${points.length} records</span></summary><div class="market-index-table" tabindex="0" aria-label="Monthly survey records"><table><thead><tr><th scope="col">Month</th><th scope="col">${esc(index.currency)}</th></tr></thead><tbody>${points.map(p=>`<tr><th scope="row">${esc(monthLabel(p.period))}</th><td>${esc(format(Number(p.value)))}</td></tr>`).join('')}</tbody></table></div></details></section>`;
 }).join('');
}
