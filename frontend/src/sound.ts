/** Original procedural sonification. Artistic timbres, never a chemical or health measurement. */
let context:AudioContext|null=null,master:GainNode|null=null,nodes:AudioScheduledSourceNode[]=[],timer:number|undefined;
let active=false,signature={slug:'gallery',ingredients:[] as string[]};
const hash=(s:string)=>Array.from(s).reduce((n,c)=>(Math.imul(n,31)+c.charCodeAt(0))>>>0,47);
function stop(){clearInterval(timer);nodes.forEach(n=>{try{n.stop();}catch{}});nodes=[];context?.close();context=null;master=null;}
function play(){
 stop();context=new AudioContext();master=context.createGain();master.gain.value=.12;master.connect(context.destination);
 const seed=hash(signature.slug),names=signature.ingredients.join(' ').toLowerCase();
 const floral=/flower|rose|lavender|chamomile|jasmine/.test(names),spice=/nutmeg|pepper|coriander|cinnamon|cardamom/.test(names),citrus=/lemon|orange|yuzu|citrus/.test(names);
 const pentatonic=[0,3,5,7,10],base=110*Math.pow(2,(seed%9)/12);let step=0;
 const phrase=()=>{if(!context||!master||document.hidden)return;const now=context.currentTime;const note=pentatonic[(seed+step*3)%5];
  const o=context.createOscillator(),g=context.createGain(),pan=context.createStereoPanner();o.type=spice?'triangle':'sine';o.frequency.value=base*Math.pow(2,note/12)*(floral?2:1);pan.pan.value=Math.sin(step*.7)*.65;g.gain.setValueAtTime(0,now);g.gain.linearRampToValueAtTime(.17,now+.8);g.gain.exponentialRampToValueAtTime(.0001,now+5);o.connect(g).connect(pan).connect(master);o.start();o.stop(now+5.1);nodes.push(o);o.onended=()=>{nodes=nodes.filter(n=>n!==o);o.disconnect();g.disconnect();pan.disconnect();};step++;
  if(citrus){const b=context.createOscillator(),bg=context.createGain();b.type='sine';b.frequency.value=base*6;bg.gain.setValueAtTime(.035,now);bg.gain.exponentialRampToValueAtTime(.0001,now+1.8);b.connect(bg).connect(master);b.start();b.stop(now+2);nodes.push(b);b.onended=()=>{nodes=nodes.filter(n=>n!==b);b.disconnect();bg.disconnect();};}
 };phrase();timer=window.setInterval(phrase,2400);
}
export function setSoundSignature(slug:string,ingredients:string[]=[]){if(signature.slug===slug)return;signature={slug,ingredients};if(active)play();}
export function bindSound(button:HTMLButtonElement){button.textContent=active?'◉ Sound on':'◌ Sound off';button.setAttribute('aria-pressed',String(active));button.onclick=()=>{active=!active;if(active)play();else stop();bindSound(button);};}
document.addEventListener('visibilitychange',()=>{if(document.hidden)context?.suspend();else if(active)context?.resume();});
