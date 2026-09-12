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
    const item=output?.civitai?.[0]; if(!item) return;
    node.properties=node.properties||{}; node.properties.source_url=item.url; node.properties.source_id=item.id;
    const el=document.createElement("div"); el.className="civitai-hover-preview";
    const img=document.createElement("img"); img.src=item.url; img.style.cssText="max-width:180px;max-height:120px;display:block";
    const bar=document.createElement("div"); bar.style.cssText="display:none;gap:4px;position:absolute;bottom:2px;left:2px";
    for(const [label,fn] of [["下载",node.widgets.find(w=>w.name==='下载当前图片')?.callback],["加载",node.widgets.find(w=>w.name==='加载到新节点')?.callback]]) { const b=document.createElement('button'); b.textContent=label; b.onclick=fn||(()=>{}); bar.appendChild(b); }
    el.onmouseenter=()=>bar.style.display='flex'; el.onmouseleave=()=>bar.style.display='none'; el.append(img,bar);
    if(node.addDOMWidget) node.addDOMWidget("civitai_preview","preview",el,{serialize:false});
  };
}});
