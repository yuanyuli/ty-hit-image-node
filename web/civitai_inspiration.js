import { app } from "../../../scripts/app.js";
app.registerExtension({name:"civitai.inspiration", nodeCreated(node){
  if(node.comfyClass !== "CivitaiInspirationLoader") return;
  node.addWidget("button", "下载当前图片", null, async ()=>{
    const current=node._civitaiItems?.[0], url=current?.url, id=current?.id;
    if(!url) return alert("请先执行节点，再下载当前图片");
    const r=await fetch("/civitai-inspiration/download", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({url,id})});
    if(!r.ok) return alert("下载失败");
    node.properties.downloaded_filename=(await r.json()).filename;
  });
  node.addWidget("button", "下一页（执行）", null, ()=>{ const w=node.widgets?.find(x=>x.name==='page'); if(w) w.value=(Number(w.value)||0)+1; const r=node.widgets?.find(x=>x.name==='refresh'); if(r) r.value=!r.value; app.queuePrompt(); });
  function render(items) {
    node._civitaiItems=items || [];
    const el=node._civitaiElement || document.createElement("div");
    node._civitaiElement=el; el.innerHTML=""; el.style.cssText="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px;width:100%;max-height:calc(100vh - 180px);overflow-y:auto;overflow-x:hidden";
    for(const current of items.slice(0,9)) { const card=document.createElement('div'); card.style.cssText='position:relative;min-width:0'; const img=document.createElement('img'); img.src=current.url; img.style.cssText='width:100%;aspect-ratio:1;object-fit:cover;border-radius:3px'; const badge=document.createElement('span'); badge.textContent=current.has_prompt?'提示词 ✓':'无提示词'; badge.title='点击复制提示词'; badge.onclick=()=>{ if(current.prompt) navigator.clipboard.writeText(current.prompt).then(()=>alert('提示词已复制')); }; badge.style.cursor='pointer'; badge.style.cssText='position:absolute;top:3px;left:3px;padding:2px 4px;border-radius:3px;background:'+(current.has_prompt?'#16834b':'#777')+';color:white;font-size:10px;cursor:pointer'; const bar=document.createElement('div'); bar.style.cssText='display:none;position:absolute;bottom:3px;left:3px;gap:3px'; const b=document.createElement('button'); b.textContent='下载'; b.onclick=async()=>{ const r=await fetch('/civitai-inspiration/download',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url:current.url,id:current.id})}); const d=await r.json().catch(()=>({})); if(!r.ok||d.error) return alert('下载失败：'+(d.error||r.status)); node.properties.downloaded_filename=d.filename; alert('已下载到 output/ty-node'); }; bar.appendChild(b); card.onmouseenter=()=>bar.style.display='flex'; card.onmouseleave=()=>bar.style.display='none'; card.append(img,badge,bar); el.appendChild(card); }
    if(node.addDOMWidget && !node._civitaiWidget) { node._civitaiWidget=node.addDOMWidget("civitai_preview","preview",el,{serialize:false}); }
    if(!items?.length) { el.textContent='没有符合条件的图片'; return; }
  }
  const previousExecuted=node.onExecuted;
  node.onExecuted = (output) => {
    if(previousExecuted) previousExecuted.call(node, output);
    const items=output?.civitai || output?.output?.civitai || []; if(items.length) render(items);
  };
  const oldDraw=node.onDrawForeground; node.onDrawForeground=function(ctx){ if(oldDraw) oldDraw.apply(this,arguments); };
}});



