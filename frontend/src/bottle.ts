export type Bottle={name:string;brand:string;color:string;shape:string;slug?:string;category?:string;image?:string;recipes?:any[];compounds?:any[];ethanol_mechanisms?:any[]};
export function bottleSVG(p:Bottle,large=false):string{
 const name=p.name.replace(/[<>&"']/g,'').slice(0,24),brand=p.brand.replace(/[<>&"']/g,'');
 return `<svg viewBox="0 0 180 260" class="bottle-svg ${large?'large':''}" role="img" aria-label="Illustrative ${brand} bottle"><defs><linearGradient id="g-${name.replace(/\W/g,'')}" x1="0" x2="1"><stop stop-color="${p.color}"/><stop offset=".4" stop-color="${p.color}" stop-opacity=".5"/><stop offset="1" stop-color="#22251b"/></linearGradient></defs><ellipse cx="90" cy="238" rx="47" ry="7" fill="#000" opacity=".15"/><path d="M51 103Q51 75 75 67L77 32H103L105 67Q129 75 129 103V216Q129 232 113 232H67Q51 232 51 216Z" fill="url(#g-${name.replace(/\W/g,'')})"/><rect x="74" y="20" width="32" height="23" rx="3" fill="#252a25"/><path d="M62 111V211" stroke="#fff" stroke-opacity=".14" stroke-width="5"/><rect x="58" y="121" width="64" height="73" rx="2" fill="#eee8d7"/><rect x="62" y="125" width="56" height="65" fill="none" stroke="#a99a70" stroke-width=".6"/><text x="90" y="145" text-anchor="middle" fill="#334239" font-size="7">${brand}</text><text x="90" y="165" text-anchor="middle" fill="#334239" font-size="5.5">${name}</text><text x="90" y="184" text-anchor="middle" fill="#647164" font-size="4.5">ILLUSTRATIVE EDITION</text></svg>`;
}
export type SceneMode='bottle'|'exploded'|'neuro';
export async function mount3D(el:HTMLElement,p:Bottle,mode:SceneMode='bottle',select?:(name:string)=>void):Promise<()=>void>{
 const THREE=await import('three');
 const {OrbitControls}=await import('three/addons/controls/OrbitControls.js');
 const {RoomEnvironment}=await import('three/addons/environments/RoomEnvironment.js');
 const {RoundedBoxGeometry}=await import('three/addons/geometries/RoundedBoxGeometry.js');
 let renderer:InstanceType<typeof THREE.WebGLRenderer>;
 try{renderer=new THREE.WebGLRenderer({antialias:true,alpha:true,powerPreference:'high-performance'});}catch{el.innerHTML='<p>WebGL is unavailable. Use the photograph and ingredient list.</p>';return()=>{};}
 renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.setClearColor(mode==='exploded'?0xe7dbc1:0x101510,1);renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.25;renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;
 el.replaceChildren(renderer.domElement);renderer.domElement.tabIndex=0;renderer.domElement.setAttribute('aria-label',mode==='neuro'?'Illustrative receptor network. Drag to rotate; arrow keys rotate. Positions are artistic, not anatomical.':'Interactive bottle sculpture. Drag or use left/right arrow keys to rotate. Use plus/minus buttons or keys to zoom.');renderer.domElement.setAttribute('role','img');
 const scene=new THREE.Scene();scene.fog=new THREE.FogExp2(mode==='exploded'?0xe7dbc1:0x101510,.028);const camera=new THREE.PerspectiveCamera(34,1,.1,80);camera.position.set(mode==='bottle'?3:0,mode==='neuro'?1:1.1,mode==='bottle'?6.7:9.3);
 const pmrem=new THREE.PMREMGenerator(renderer);const environment=new RoomEnvironment();const env=pmrem.fromScene(environment,.04);scene.environment=env.texture;
 scene.add(new THREE.HemisphereLight(0xffeccb,0x243724,2));
 for(const [color,power,x,y,z] of [[0xffd0a0,55,-3,5,4],[0xc0e1cf,45,4,3,-2],[0xffffff,30,0,6,-4]]){const light=new THREE.PointLight(color,power,20);light.position.set(x,y,z);scene.add(light);}
 const group=new THREE.Group();scene.add(group);const rotating=new THREE.Group();group.add(rotating);
 const pickables:any[]=[];const animated:any[]=[];const textures:any[]=[];const botanicalNodes:any[]=[];let spread=1,page=0;const pageSize=8;
 function material(color:any,extra:any={}){return new THREE.MeshStandardMaterial({color,roughness:.55,...extra});}
 function addMesh(geometry:any,mat:any,parent:any=rotating,pos:number[]=[0,0,0]){const mesh=new THREE.Mesh(geometry,mat);mesh.position.set(pos[0],pos[1],pos[2]);mesh.castShadow=true;mesh.receiveShadow=true;parent.add(mesh);return mesh;}
 function textSprite(text:string,color='#e7d3ac',scale=1){const c=document.createElement('canvas');c.width=512;c.height=128;const x=c.getContext('2d')!;x.clearRect(0,0,512,128);x.fillStyle=color;x.textAlign='center';x.font='500 31px Arial';x.fillText(text,256,73,490);const tex=new THREE.CanvasTexture(c);tex.colorSpace=THREE.SRGBColorSpace;textures.push(tex);const sp=new THREE.Sprite(new THREE.SpriteMaterial({map:tex,transparent:true,depthTest:false}));sp.scale.set(1.65*scale,.41*scale,1);return sp;}
 const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
 if(mode!=='neuro'){
  const bottle=new THREE.Group();rotating.add(bottle);bottle.position.y=-1.45;
  const isDark=p.slug?.includes('monkey')||p.slug?.includes('hendricks');const squat=p.slug?.includes('disaronno');const glassColor=isDark?0x432612:p.shape==='hex'?0xd6e1cf:p.slug?.includes('bombay')?0x4d9daf:p.slug?.includes('tanqueray')||p.slug?.includes('jameson')?0x387c35:0xd6dfcb;
  const glass=new THREE.MeshPhysicalMaterial({color:glassColor,roughness:.1,transmission:isDark?.15:.88,thickness:.14,ior:1.48,clearcoat:1,envMapIntensity:1.3,transparent:true,opacity:isDark?1:.92});
  const radius=squat?.77:.58;const neckHeight=p.slug?.includes('bacardi')||p.slug?.includes('havana')||p.slug?.includes('jameson')?.85:.53;
  const bodyHeight=squat?1.55:1.95;const bottleTop=bodyHeight+neckHeight+.2;
  const points=[[0,.03],[radius*.8,.03],[radius*.95,.07],[radius,.16],[radius,.3],[radius,bodyHeight-.17],[radius*.94,bodyHeight-.04],[.28,bodyHeight+.15],[.23,bodyHeight+.25],[.225,bottleTop],[0,bottleTop]].map(([x,y])=>new THREE.Vector2(x,y));
  if(p.shape==='square'){
   addMesh(new RoundedBoxGeometry(radius*1.9,bodyHeight,.94,4,.09),glass,bottle,[0,bodyHeight/2,0]);
   const shoulder=addMesh(new THREE.CylinderGeometry(.24,.62,.33,4),glass,bottle,[0,bodyHeight+.1,0]);shoulder.rotation.y=Math.PI/4;
   addMesh(new THREE.CylinderGeometry(.225,.24,neckHeight,48),glass,bottle,[0,bodyHeight+.18+neckHeight/2,0]);
  }else addMesh(new THREE.LatheGeometry(points,p.shape==='hex'?6:96),glass,bottle);
  // Separate liquid volume and thick glass base; artistically reconstructed from a reference silhouette.
  const amber=['Rum','Whisky','Amaretto','Liqueur'].includes(p.category||'');const liquid=new THREE.MeshPhysicalMaterial({color:p.category==='Aperitif'?0xd83813:amber?0xae4d10:0xe4e7cb,roughness:.05,transmission:.88,thickness:.8,ior:1.36,transparent:true,opacity:.82});
  if(p.shape==='square')addMesh(new RoundedBoxGeometry(radius*1.7,bodyHeight*.78,.78,4,.07),liquid,bottle,[0,bodyHeight*.45,0]);
  else addMesh(new THREE.CylinderGeometry(radius*.9,radius*.9,bodyHeight*.8,p.shape==='hex'?6:64),liquid,bottle,[0,bodyHeight*.46,0]);
  addMesh(new THREE.TorusGeometry(radius*.91,.04,10,80),glass,bottle,[0,.11,0]).rotation.x=Math.PI/2;
  const capGroup=new THREE.Group();bottle.add(capGroup);capGroup.position.y=bottleTop+.06+(mode==='exploded'?.65:0);
  const cap=addMesh(new THREE.CylinderGeometry(.255,.255,.28,64),material(isDark?0x231d16:0xa3997a,{metalness:.35,roughness:.45}),capGroup);
  for(let i=0;i<9;i++)addMesh(new THREE.TorusGeometry(.254,.006,4,64),material(0x665c45,{metalness:.6}),capGroup,[0,-.11+i*.025,0]).rotation.x=Math.PI/2;
  if(mode==='exploded')animated.push({obj:capGroup,base:capGroup.position.clone(),phase:0});
  let labelMat:any;
  if(p.image){const t=await new THREE.TextureLoader().loadAsync(p.image);t.colorSpace=THREE.SRGBColorSpace;const crop=p.slug?.includes('monkey')?[.35,.34,.325,.22]:p.slug?.includes('bombay')?[.28,.56,.27,.1]:p.slug?.includes('roku')?[.35,.24,.34,.42]:[.49,.3,.25,.2];t.repeat.set(crop[0],crop[1]);t.offset.set(crop[2],crop[3]);textures.push(t);labelMat=material(0xffffff,{map:t,roughness:.9});}
  else{const c=document.createElement('canvas');c.width=512;c.height=512;const x=c.getContext('2d')!;x.fillStyle='#e8dfc7';x.fillRect(0,0,512,512);x.strokeStyle='#796744';x.strokeRect(18,18,476,476);x.fillStyle='#25351f';x.font='38px Georgia';x.textAlign='center';x.fillText(p.brand,256,170,450);x.font='27px Georgia';x.fillText(p.name,256,270,450);x.font='15px Arial';x.fillText('ILLUSTRATIVE RECONSTRUCTION',256,410);const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;textures.push(t);labelMat=material(0xffffff,{map:t});}
  const labelGeometry=p.shape==='round'?new THREE.CylinderGeometry(radius+.009,radius+.009,.93,64,1,true,-.9,1.8):new THREE.PlaneGeometry(squat?1.1:.92,.96);
  const label=addMesh(labelGeometry,labelMat,bottle,[0,bodyHeight*.55,p.shape==='round'?0:p.shape==='square'?.477:.51]);
  if(mode==='exploded'){label.position.z+=.65;const sp=textSprite('LABEL / RECIPE', '#786140',.6);sp.position.set(0,bodyHeight*.55-.67,.8);bottle.add(sp);}
  if(mode==='bottle'){
   const pedestal=addMesh(new THREE.CylinderGeometry(1.25,1.3,.12,96),material(0x263121,{metalness:.3,roughness:.3}),group,[0,-1.48,0]);pedestal.receiveShadow=true;
  }
  if(mode==='exploded'){
   bottle.scale.setScalar(.75);bottle.position.y=-1.1;
   const ingredients=[...new Map((p.recipes||[]).flatMap(r=>r.ingredients).map(i=>[i.name,i])).values()].slice(0,32);
   // Illustrations are sampled from an attributed art atlas, never treated as specimen photographs.
   const plates:Record<string,number>={'juniper':0,'coriander':1,'angelica root':2,'orris root':3,'lemon peel':4,'orange peel':5,'sweet orange peel':5,'lavender':6,'rose':7,'chamomile':8,'yuzu peel':9,'rosemary':10,'sage':11,'cardamom':12,'green cardamom':12,'cinnamon':13,'ginger':14,'sencha tea':15,'gyokuro tea':15};
   let atlas:InstanceType<typeof THREE.Texture>|null=null;
   try{atlas=await new THREE.TextureLoader().loadAsync('/art/botanical-atlas-v1.png');atlas.colorSpace=THREE.SRGBColorSpace;textures.push(atlas);}catch{/* The indexed ingredient remains available if an illustration cannot load. */}
   ingredients.forEach((i,index)=>{
    const angle=(index%pageSize)/Math.min(pageSize,ingredients.length)*Math.PI*2+Math.PI/8;const x=Math.cos(angle)*2.15,z=-.35+Math.sin(angle)*.35,y=Math.sin(angle)*1.65;
    const node=new THREE.Group();node.position.set(x,y,z);rotating.add(node);node.userData.ingredient=i.name;
    const plate=plates[i.name.toLowerCase()];
    if(plate!==undefined&&atlas){
     const tex=atlas.clone();tex.repeat.set(.25,.25);tex.offset.set((plate%4)*.25,(3-Math.floor(plate/4))*.25);tex.needsUpdate=true;textures.push(tex);
     const art=new THREE.Sprite(new THREE.SpriteMaterial({map:tex,transparent:true,alphaTest:.035,depthWrite:false}));art.scale.set(1.1,1.1,1);art.userData.ingredient=i.name;node.add(art);pickables.push(art);
    }else{const plateNote=textSprite('PLATE TO BE DRAWN','#746144',.43);plateNote.position.y=.12;node.add(plateNote);}
    node.traverse(o=>{if(o instanceof THREE.Mesh){o.userData.ingredient=i.name;pickables.push(o);}});
    node.scale.setScalar(1.2);const sprite=textSprite(i.name,'#4a3d28',.72);sprite.position.y=-.54;node.add(sprite);pickables.push(sprite);sprite.userData.ingredient=i.name;
    const line=new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(x*.78,y*.8,z*.78),new THREE.Vector3(x,y,z)]),new THREE.LineBasicMaterial({color:0x879765,transparent:true,opacity:.27}));rotating.add(line);botanicalNodes.push({node,line,name:i.name});
    animated.push({obj:node,base:node.position.clone(),phase:index*.7});
   });
   if(!ingredients.length){const label=textSprite('Recipe not disclosed. No plants invented.','#c1ad8b',1.2);label.position.y=1.8;group.add(label);}
  }
 }else{
  // Abstract neural sculpture. Spatial positions and pulses are artistic, not an anatomical atlas.
  const brain=new THREE.Group();rotating.add(brain);
  for(let side of [-1,1]){
   const geometry=new THREE.SphereGeometry(1,48,32);const pos=geometry.attributes.position;
   for(let i=0;i<pos.count;i++){const x=pos.getX(i),y=pos.getY(i),z=pos.getZ(i);const fold=1+.055*Math.sin(y*22+z*11)*Math.sin(x*18);pos.setXYZ(i,x*fold*.78,y*fold,z*fold*.82);}geometry.computeVertexNormals();
   const hemi=new THREE.Mesh(geometry,new THREE.MeshPhysicalMaterial({color:0xd1ae87,roughness:.4,transmission:.2,transparent:true,opacity:.28,wireframe:true}));hemi.position.x=side*.57;hemi.rotation.z=side*-.1;brain.add(hemi);
  }
  const links:any[]=[{name:'Ethanol',target:'NMDA receptor',known:true},...(p.compounds||[]).flatMap(c=>(c.mechanisms||[]).map((m:any)=>({name:c.name,target:m.target,known:false})))];
  const limited=links.slice(0,8);
  limited.forEach((n,index)=>{
   const a=index/limited.length*Math.PI*2;const start=new THREE.Vector3(Math.cos(a)*2.8,Math.sin(a)*1.8,.5),end=new THREE.Vector3(Math.cos(a)*.7,Math.sin(a)*.7,.2);
   const dot=addMesh(new THREE.IcosahedronGeometry(.13,3),material(n.known?0xf5b478:0x8ead7d,{emissive:n.known?0x7d3c12:0x274a22,emissiveIntensity:1.3}),rotating,[start.x,start.y,start.z]);pickables.push(dot);dot.userData.ingredient=n.name;
   const curve=new THREE.QuadraticBezierCurve3(start,new THREE.Vector3(start.x*.6,start.y*.4,1.4),end);const tube=new THREE.Mesh(new THREE.TubeGeometry(curve,40,.009,5,false),new THREE.MeshBasicMaterial({color:n.known?0xeab17b:0x83a36c,transparent:true,opacity:n.known?.8:.35}));rotating.add(tube);
   const title=textSprite(n.name,n.known?'#f6c48f':'#b4c89e',.75);title.position.copy(start).add(new THREE.Vector3(0,.32,0));rotating.add(title);
   const target=textSprite(n.target,'#a99579',.48);target.position.copy(end).add(new THREE.Vector3(0,-.22,0));rotating.add(target);
   const pulse=addMesh(new THREE.SphereGeometry(.035,10,8),new THREE.MeshBasicMaterial({color:0xffdfb4}),rotating);animated.push({obj:pulse,curve,phase:index*.2});
  });
  const caption=textSprite('MECHANISMS, NOT A PREDICTION','#9baf88',1);caption.position.y=-2.05;group.add(caption);
 }
 const dustPositions=new Float32Array(240*3);for(let i=0;i<240;i++){dustPositions[i*3]=Math.sin(i*12.9898)*8;dustPositions[i*3+1]=Math.cos(i*8.233)*4;dustPositions[i*3+2]=Math.sin(i*4.193)*7-2;}const dustGeo=new THREE.BufferGeometry();dustGeo.setAttribute('position',new THREE.BufferAttribute(dustPositions,3));scene.add(new THREE.Points(dustGeo,new THREE.PointsMaterial({color:0xc7b488,size:.015,transparent:true,opacity:.4})));
 const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.enablePan=true;controls.minDistance=3.5;controls.maxDistance=13;controls.autoRotate=!reduced&&mode==='bottle';controls.autoRotateSpeed=.3;controls.zoomSpeed=.55;controls.rotateSpeed=.65;controls.enableZoom=false;controls.target.set(0,0,0);controls.update();
 const tools=document.createElement('div');tools.className='scene-tools';
 tools.innerHTML=`<button data-scene="zoom-out" aria-label="Zoom out 3D">−</button><button data-scene="zoom-in" aria-label="Zoom in 3D">＋</button><button data-scene="rotate" aria-pressed="${controls.autoRotate}">${controls.autoRotate?'Pause orbit':'Start orbit'}</button><button data-scene="reset" aria-label="Reset camera">Reset view</button><button data-scene="full" aria-label="Toggle immersive full screen">⛶ Full screen</button>${mode==='exploded'?'<button data-scene="previous" aria-label="Previous botanical group">← Plants</button><button data-scene="next" aria-label="Next botanical group">Plants →</button><label>Unfold<input type="range" min="40" max="125" value="100" aria-label="Botanical spread"></label>':''}`;
 el.append(tools);const hint=document.createElement('span');hint.className='scene-instructions';hint.textContent='DRAG TO ORBIT · SHIFT + DRAG TO MOVE · ＋ / − TO ZOOM · ARROWS TO TURN';el.append(hint);
 tools.querySelector<HTMLButtonElement>('[data-scene=reset]')!.onclick=()=>{controls.reset();rotating.rotation.set(0,0,0);};
 tools.querySelector<HTMLButtonElement>('[data-scene=full]')!.onclick=()=>{const stage=(el.closest('.detail-visual')||el) as HTMLElement;if(document.fullscreenElement)document.exitFullscreen();else stage?.requestFullscreen?.().catch(()=>{});};
 const zoom=(factor:number)=>{const offset=camera.position.clone().sub(controls.target);offset.setLength(Math.max(controls.minDistance,Math.min(controls.maxDistance,offset.length()*factor)));camera.position.copy(controls.target).add(offset);controls.update();};
 tools.querySelector<HTMLButtonElement>('[data-scene=zoom-in]')!.onclick=()=>zoom(.85);tools.querySelector<HTMLButtonElement>('[data-scene=zoom-out]')!.onclick=()=>zoom(1.18);tools.querySelector<HTMLButtonElement>('[data-scene=rotate]')!.onclick=e=>{controls.autoRotate=!controls.autoRotate;const b=e.currentTarget as HTMLButtonElement;b.textContent=controls.autoRotate?'Pause orbit':'Start orbit';b.setAttribute('aria-pressed',String(controls.autoRotate));};
 const index=document.createElement('div');index.className='scene-plant-index';index.setAttribute('aria-label','Select an ingredient');
 botanicalNodes.forEach(b=>{const button=document.createElement('button');button.textContent=b.name;button.type='button';button.onclick=()=>select?.(b.name);index.append(button);});
 if(mode==='exploded')el.append(index);
 const showPage=()=>{botanicalNodes.forEach((b,i)=>{const visible=Math.floor(i/pageSize)===page;b.node.visible=b.line.visible=visible;if(index.children[i]) (index.children[i] as HTMLElement).hidden=!visible;});};showPage();
 tools.querySelector<HTMLButtonElement>('[data-scene=next]')?.addEventListener('click',()=>{page=(page+1)%Math.max(1,Math.ceil(botanicalNodes.length/pageSize));showPage();});
 tools.querySelector<HTMLButtonElement>('[data-scene=previous]')?.addEventListener('click',()=>{page=(page-1+Math.ceil(botanicalNodes.length/pageSize))%Math.max(1,Math.ceil(botanicalNodes.length/pageSize));showPage();});
 tools.querySelector<HTMLInputElement>('input')?.addEventListener('input',e=>{spread=Number((e.target as HTMLInputElement).value)/100;});
 const resize=()=>{const w=el.clientWidth,h=el.clientHeight||465;renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix();};const observer=new ResizeObserver(resize);observer.observe(el);resize();
 const ray=new THREE.Raycaster(),pointer=new THREE.Vector2();let down={x:0,y:0};const pointerDown=(e:PointerEvent)=>{down={x:e.clientX,y:e.clientY};};renderer.domElement.addEventListener('pointerdown',pointerDown);const click=(event:PointerEvent)=>{if(Math.hypot(event.clientX-down.x,event.clientY-down.y)>5)return;const r=renderer.domElement.getBoundingClientRect();pointer.set((event.clientX-r.left)/r.width*2-1,-(event.clientY-r.top)/r.height*2+1);ray.setFromCamera(pointer,camera);const hit=ray.intersectObjects(pickables.filter(o=>{let n:typeof o|null=o;while(n){if(!n.visible)return false;n=n.parent;}return true;}))[0];if(hit){let node:typeof hit.object|null=hit.object;while(node&&node.visible)node=node.parent;if(!node)select?.(hit.object.userData.ingredient);}};renderer.domElement.addEventListener('pointerup',click);
 const keyboard=(event:KeyboardEvent)=>{if(event.key==='+'||event.key==='='||event.key==='-'){zoom(event.key==='-'?1.18:.85);event.preventDefault();}if(event.key==='ArrowLeft'||event.key==='ArrowRight'){rotating.rotation.y+=event.key==='ArrowLeft'?-.15:.15;controls.autoRotate=false;const orbit=tools.querySelector<HTMLButtonElement>('[data-scene=rotate]')!;orbit.textContent='Start orbit';orbit.setAttribute('aria-pressed','false');event.preventDefault();}};renderer.domElement.addEventListener('keydown',keyboard);
 let frame=0,disposed=false,start=performance.now();function tick(){if(disposed)return;const t=(performance.now()-start)/1000;animated.forEach(a=>{if(a.curve&&!reduced)a.obj.position.copy(a.curve.getPoint((t*.12+a.phase)%1));else if(a.base){a.obj.position.x=a.base.x*spread;a.obj.position.y=a.base.y*spread+(!reduced?Math.sin(t*.65+a.phase)*.055:0);}});controls.update();renderer.render(scene,camera);frame=requestAnimationFrame(tick);}tick();
 return()=>{disposed=true;cancelAnimationFrame(frame);observer.disconnect();controls.dispose();renderer.domElement.removeEventListener('pointerdown',pointerDown);renderer.domElement.removeEventListener('pointerup',click);renderer.domElement.removeEventListener('keydown',keyboard);scene.traverse(o=>{if(o instanceof THREE.Mesh||o instanceof THREE.Line||o instanceof THREE.Points){o.geometry.dispose();const mats=Array.isArray(o.material)?o.material:[o.material];mats.forEach(m=>m.dispose());}else if(o instanceof THREE.Sprite)o.material.dispose();});textures.forEach(t=>t.dispose());env.dispose();environment.dispose();pmrem.dispose();renderer.dispose();renderer.domElement.remove();tools.remove();hint.remove();index.remove();};
}
