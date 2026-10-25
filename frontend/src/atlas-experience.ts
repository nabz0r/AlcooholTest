import {startSound,toggleSound,soundIsPlaying,soundVolume,setSoundVolume,openSound} from './sound';
let immersive=true;try{immersive=sessionStorage.getItem('atlas-mode')!=='off';}catch{}
function enter(){immersive=true;try{sessionStorage.setItem('atlas-mode','on');}catch{}apply();}
function leave(){immersive=false;try{sessionStorage.setItem('atlas-mode','off');}catch{}apply();}
function apply(){document.body.classList.toggle('atlas-immersive',immersive);document.querySelector<HTMLButtonElement>('#atlas-leave')?.setAttribute('aria-pressed',String(immersive));}
export function mountAtlasExperience(){
 document.querySelector('#atlas-controls')?.remove();document.querySelector('#atlas-gateway')?.remove();
 const bar=document.createElement('nav');bar.id='atlas-controls';bar.setAttribute('aria-label','Atlas experience controls');
 bar.innerHTML=`<a href="/" class="atlas-home" aria-label="Atlas opening">✦</a><a href="/catalogue/">Cabinet</a><a href="/stories/">Journal</a><a href="/research/">Research</a><button data-atlas-sound aria-pressed="${soundIsPlaying()}">${soundIsPlaying()?'Ⅱ Pause sound':'▶ Play sound'}</button><label class="atlas-volume">Volume<input data-atlas-volume aria-label="Atmosphere volume" type="range" min="0" max="100" value="${Math.round(soundVolume()*100)}"></label><button id="atlas-mixer" aria-label="Open atmosphere mixer">Mix</button><button id="atlas-leave" aria-label="Leave immersive atlas">↙ Exit</button>`;
 document.body.append(bar);bar.querySelector<HTMLButtonElement>('[data-atlas-sound]')!.onclick=()=>void toggleSound();bar.querySelector<HTMLInputElement>('input')!.oninput=e=>setSoundVolume(Number((e.target as HTMLInputElement).value)/100);bar.querySelector<HTMLButtonElement>('#atlas-mixer')!.onclick=openSound;bar.querySelector<HTMLButtonElement>('#atlas-leave')!.onclick=leave;
 let started=false;try{started=sessionStorage.getItem('atlas-started')==='yes';}catch{}
 if(immersive&&!started&&!['/setup/','/account/','/studio/'].includes(location.pathname)){
  const gate=document.createElement('dialog');gate.id='atlas-gateway';gate.setAttribute('aria-labelledby','atlas-gateway-title');gate.innerHTML='<div class="disc-label">ALCOOLTEST / DISC ONE</div><div class="pixel-compass" aria-hidden="true">✦</div><p class="disc-label">AN INDEPENDENT SPIRITS ATLAS</p><h1 id="atlas-gateway-title">Places. Plants.<br>Good spirits.</h1><p class="disc-subtitle">A field atlas, made to be explored.</p><button class="disc-start" id="disc-start">▶ PRESS START · SOUND ON</button><button class="disc-quiet" id="disc-quiet">Enter quietly</button><small>Original audio · headphones welcome</small>';
  document.body.append(gate);gate.showModal();
  const begin=(sound:boolean)=>{try{sessionStorage.setItem('atlas-started','yes');}catch{}gate.close();gate.remove();enter();if(sound)void startSound();};
  gate.querySelector<HTMLButtonElement>('#disc-start')!.onclick=()=>begin(true);gate.querySelector<HTMLButtonElement>('#disc-quiet')!.onclick=()=>begin(false);gate.addEventListener('cancel',()=>{try{sessionStorage.setItem('atlas-started','yes');}catch{}gate.remove();});
 }
 const intro=document.querySelector('.experience-copy .action-row,.detail-intro .action-row');
 if(intro){const button=document.createElement('button');button.className='button atlas-enter';button.id='enter-atlas';button.textContent='✦ Enter the atlas · sound on';button.onclick=()=>{enter();void startSound();};intro.prepend(button);const silent=document.createElement('button');silent.className='button subtle atlas-enter-silent';silent.textContent='Enter quietly ↗';silent.onclick=enter;intro.append(silent);}
 apply();
}
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!document.querySelector('dialog[open]'))leave();});
