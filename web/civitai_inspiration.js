import { app } from "../../../scripts/app.js";
app.registerExtension({name:"civitai.inspiration", async setup(){
  app.registerExtension({name:"civitai.inspiration.actions", nodeCreated(node){
    if(node.comfyClass !== "CivitaiInspirationLoader") return;
    node.addWidget("button", "下载/加载图片", null, ()=>alert("请从批次预览中选择图片操作"));
  }}});
}});
