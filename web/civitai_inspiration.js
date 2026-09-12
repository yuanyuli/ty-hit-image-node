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
}});
