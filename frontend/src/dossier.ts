/** Progressive disclosure keeps research available without turning a bottle into a dashboard. */
export function polishDossier(main:HTMLElement,p:any){
 main.classList.add('dossier-page');
 const names=new Set(p.recipes.flatMap((r:any)=>r.ingredients.map((i:any)=>i.name)));
 const chapter=(section:HTMLElement,title:string,subtitle:string)=>{
  const detail=document.createElement('details');detail.className='dossier-chapter';
  if(section.id){detail.id=section.id;section.removeAttribute('id');}
  const summary=document.createElement('summary');const heading=document.createElement('span');heading.className='chapter-label';heading.textContent=title;const note=document.createElement('span');note.className='chapter-note';note.textContent=subtitle;summary.append(heading,note);detail.append(summary);section.before(detail);detail.append(section);
 };
 const coverage=main.querySelector<HTMLElement>('#record-confidence');if(coverage)chapter(coverage,'Behind the record',`${p.coverage.documented} areas documented · sources & gaps`);
 const story=main.querySelector<HTMLElement>('#heritage');if(story)chapter(story,'The story',p.locality||p.country);
 const packaging=main.querySelector<HTMLElement>('#photo-gallery');if(packaging)chapter(packaging,'Turn the bottle', 'Photographs · front, reverse & details');
 const prices=main.querySelector<HTMLElement>('#price-history');if(prices)chapter(prices,'Price notebook',p.prices?.length?`${p.prices.length} dated observations`:'No price series yet');
 const bottles=main.querySelector<HTMLElement>('#bottlings');if(bottles)chapter(bottles,'Choose a bottling',`${p.variants.length} market references`);
 const critics=main.querySelector<HTMLElement>('#critic-perspectives');if(critics)chapter(critics,'What the critics say',`${p.critic_reviews.length} attributed perspectives`);
 const community=main.querySelector<HTMLElement>('#community');if(community)chapter(community,'The monkey notebook',`${p.rating.count} community notes · add yours`);
 const markov=main.querySelector<HTMLElement>('#markov-panel');if(markov)chapter(markov,'Your private observations','Open your notebook');
 Array.from(main.querySelectorAll<HTMLElement>(':scope > section.panel')).forEach(s=>{
  const title=s.querySelector('h2')?.textContent||'';
  if(title==='Inside the recipe')chapter(s,'Inside the recipe',`${names.size} named inputs · explore the sources`);
  if(title==='Compounds & evidence')chapter(s,'Research library','Studies, exposures & limitations');
 });
 const inspector=main.querySelector<HTMLElement>('#botanical-inspector');if(inspector){inspector.classList.add('scene-inspector');inspector.setAttribute('aria-live','polite');inspector.hidden=true;main.querySelector('.detail-visual')?.append(inspector);}
 const nav=main.querySelector<HTMLElement>('.section-nav');if(nav)nav.innerHTML='<a href="#heritage">Story</a><a href="#photo-gallery">Photographs</a><a href="#critic-perspectives">Opinions</a><a href="#community">Your note</a>';
 const openTarget=(id:string)=>{const target=document.getElementById(id);if(!target||!main.contains(target))return;let n:HTMLElement|null=target;while(n&&n!==main){if(n instanceof HTMLDetailsElement)n.open=true;n=n.parentElement;}target.scrollIntoView({block:'start',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});};
 main.addEventListener('click',e=>{const a=(e.target as Element).closest<HTMLAnchorElement>('a[href^="#"]');if(a){const id=a.getAttribute('href')!.slice(1);if(document.getElementById(id)){e.preventDefault();history.replaceState({},'',location.pathname+location.search+'#'+id);openTarget(id);}}});
 if(location.hash)requestAnimationFrame(()=>openTarget(location.hash.slice(1)));
 const intro=main.querySelector('.detail-intro');if(intro){const line=document.createElement('p');line.className='bottle-one-line';line.textContent=`${p.category} · ${p.country} · ${names.size} named ${names.size===1?'input':'inputs'}`;intro.querySelector('h1')?.after(line);const desc=intro.querySelector<HTMLElement>(':scope > p:not(.bottle-one-line)');if(desc){const d=document.createElement('details');d.className='about-bottle';d.innerHTML='<summary>About this bottle ↗</summary>';desc.before(d);d.append(desc);}}
}

/** Turn the archive into a navigable field journal, rather than ten stacked dashboards. */
export function mountBottleJournal(main:HTMLElement,p:any){
 const definitions=[['story','The story',['heritage']],['inside','Botanical plates',['photo-gallery','bottlings']],['notes','Tasting room',['critic-perspectives','community']],['prices','Price archive',['price-history']],['research','Research',['markov-panel']],['sources','Memento',['record-confidence','source-memento']]] as const;
 const book=document.createElement('section');book.className='atlas-journal';book.id='field-journal';
 const nav=document.createElement('div');nav.className='journal-tabs';nav.setAttribute('role','tablist');nav.setAttribute('aria-label','Bottle field journal');book.append(nav);
 const hero=main.querySelector('.detail-hero');hero?.after(book);
 const panels=new Map<string,HTMLElement>();const buttons=new Map<string,HTMLButtonElement>();
 const select=(key:string)=>{panels.forEach((panel,k)=>{panel.hidden=k!==key;buttons.get(k)!.setAttribute('aria-selected',String(k===key));buttons.get(k)!.tabIndex=k===key?0:-1;});const first=panels.get(key)?.querySelector('details');if(first)first.open=true;};
 definitions.forEach(([key,title,ids],index)=>{
  const panel=document.createElement('div');panel.id='journal-'+key;panel.className='journal-page';panel.dataset.journalPanel=key;panel.setAttribute('role','tabpanel');panel.setAttribute('aria-labelledby','journal-tab-'+key);
  const button=document.createElement('button');button.id='journal-tab-'+key;button.type='button';button.setAttribute('role','tab');button.setAttribute('aria-controls',panel.id);button.innerHTML=`<span>0${index+1}</span>${title}`;button.onclick=()=>select(key);
  button.onkeydown=e=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;e.preventDefault();const offset=e.key==='ArrowLeft'?-1:1;const next=e.key==='Home'?0:e.key==='End'?definitions.length-1:(index+offset+definitions.length)%definitions.length;select(definitions[next][0]);buttons.get(definitions[next][0])?.focus();};
  panels.set(key,panel);buttons.set(key,button);nav.append(button);book.append(panel);
  ids.forEach(id=>{const section=main.querySelector<HTMLElement>('#'+id);if(section)panel.append(section);});
 });
 Array.from(main.querySelectorAll<HTMLElement>(':scope > .dossier-chapter')).forEach(chapter=>{const label=chapter.querySelector('.chapter-label')?.textContent;panels.get(label==='Inside the recipe'?'inside':'research')?.append(chapter);});
 select('story');
 main.addEventListener('click',e=>{const a=(e.target as Element).closest<HTMLAnchorElement>('a[href^="#"]');if(!a)return;const target=document.getElementById(a.hash.slice(1));const panel=target?.closest<HTMLElement>('[data-journal-panel]');if(panel){select(panel.dataset.journalPanel!);requestAnimationFrame(()=>target?.scrollIntoView({block:'start',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'}));}});
 if(location.hash){const target=document.getElementById(location.hash.slice(1));const panel=target?.closest<HTMLElement>('[data-journal-panel]');if(panel)select(panel.dataset.journalPanel!);}
 const sectionNav=main.querySelector<HTMLElement>('.section-nav');if(sectionNav){sectionNav.innerHTML='<a href="#field-journal">Open the field journal ↓</a><a href="#photo-gallery">Turn the bottle ↗</a>';}
 const lead=document.createElement('p');lead.className='bottle-story-lead';lead.textContent=p.history?String(p.history).split(/(?<=[.!?])\s+/).slice(0,1).join(' '):p.description;if(lead.textContent&&lead.textContent.length>200)lead.textContent=lead.textContent.slice(0,197).replace(/\s+\S*$/,'')+'…';main.querySelector('.detail-intro h1')?.after(lead);
 const first=main.querySelector<HTMLButtonElement>('#save');if(first)first.textContent='＋ My notebook';const love=main.querySelector<HTMLButtonElement>('#love');if(love)love.textContent='♥ A favourite';
}
