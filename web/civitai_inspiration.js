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
  node.addWidget("button", "加载到新节点", null, ()=>{
    const filename=node.properties?.downloaded_filename;
    if(!filename) return alert("请先下载图片");
    const n=LiteGraph.createNode("CivitaiImageLoader"); n.pos=[node.pos[0]+node.size[0]+30,node.pos[1]];
    const w=n.widgets?.find(x=>x.name==="filename"); if(w) w.value=filename; app.graph.add(n);
  });
  node.onExecuted = (output) => {
    const items=output?.civitai || output?.output?.civitai || []; if(!items.length) return;
    const item=items[0];
    node.properties=node.properties||{}; node.properties.source_url=item.url; node.properties.source_id=item.id;
    const el=document.createElement("div"); el.style.cssText="display:grid;grid-template-columns:repeat(3,1fr);gap:4px;max-width:300px";
    for(const current of items) { const card=document.createElement('div'); card.style.cssText='position:relative'; const img=document.createElement('img'); img.src=current.url; img.style.cssText='width:96px;height:96px;object-fit:cover'; const bar=document.createElement('div'); bar.style.cssText='display:none;position:absolute;bottom:2px;left:2px;gap:2px'; for(const label of ['下载','加载']) { const b=document.createElement('button'); b.textContent=label; b.onclick=()=>{node.properties.source_url=current.url; node.properties.source_id=current.id; if(label==='下载') node.widgets.find(w=>w.name==='下载当前图片')?.callback(); else node.widgets.find(w=>w.name==='加载到新节点')?.callback();}; bar.appendChild(b);} card.onmouseenter=()=>bar.style.display='flex'; card.onmouseleave=()=>bar.style.display='none'; card.append(img,bar); el.appendChild(card); }
    if(node.addDOMWidget) node.addDOMWidget("civitai_preview","preview",el,{serialize:false});
  };
}});
