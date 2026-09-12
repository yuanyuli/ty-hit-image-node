import { app } from "../../../scripts/app.js";
app.registerExtension({name:"civitai.inspiration", nodeCreated(node){
  if(node.comfyClass !== "CivitaiInspirationLoader") return;
  node.addWidget("button", "下载当前图片", null, async ()=>{
    const url=node.properties?.source_url, id=node.properties?.source_id;
    if(!url) return alert("请先执行节点，再下载当前图片");
    const r=await fetch("/civitai-inspiration/download", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({url,id})});
    if(!r.ok) return alert("下载失败");
    node.properties.downloaded_filename=(await r.json()).filename;
  });
  function render(items) {
    if(!items?.length) return;
    const item=items[0];
    node.properties=node.properties||{}; node.properties.source_url=item.url; node.properties.source_id=item.id;
    if(node._civitaiWidget?.element) node._civitaiWidget.element.remove();
    const el=document.createElement("div"); el.style.cssText="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px;width:100%";
    for(const current of items.slice(0,9)) { const card=document.createElement('div'); card.style.cssText='position:relative;min-width:0'; const img=document.createElement('img'); img.src=current.url; img.style.cssText='width:100%;aspect-ratio:1;object-fit:cover;border-radius:3px'; const bar=document.createElement('div'); bar.style.cssText='display:none;position:absolute;bottom:3px;left:3px;gap:3px'; const b=document.createElement('button'); b.textContent='下载'; b.onclick=async()=>{ const r=await fetch('/civitai-inspiration/download',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url:current.url,id:current.id})}); const d=await r.json().catch(()=>({})); if(!r.ok||d.error) return alert('下载失败：'+(d.error||r.status)); node.properties.downloaded_filename=d.filename; alert('已下载到 output/ty-node'); }; bar.appendChild(b); card.onmouseenter=()=>bar.style.display='flex'; card.onmouseleave=()=>bar.style.display='none'; card.append(img,bar); el.appendChild(card); }
    if(node.addDOMWidget) node._civitaiWidget=node.addDOMWidget("civitai_preview","preview",el,{serialize:false});
    node.properties.civitai_gallery=items;
  }
  node.onExecuted = (output) => {
    const items=output?.civitai || output?.output?.civitai || []; if(items.length) render(items);
  };
  const oldDraw=node.onDrawForeground; node.onDrawForeground=function(ctx){ if(oldDraw) oldDraw.apply(this,arguments); if(!node._civitaiWidget && node.properties?.civitai_gallery) render(node.properties.civitai_gallery); };
}});
