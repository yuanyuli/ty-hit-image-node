import { app } from "../../../scripts/app.js";

const NODE_TYPES = new Set(["CivitaiInspirationLoader", "TyHitImageNode", "ty-hit-image-node"]);
const DOWNLOAD_ENDPOINT = "/civitai-inspiration/download";

const style = document.createElement("style");
style.textContent = `
.ty-hit-gallery{display:flex;flex-direction:column;gap:8px;width:100%;box-sizing:border-box;font-family:system-ui,sans-serif;color:var(--fg-color,#ddd)}
.ty-hit-toolbar{display:flex;align-items:center;gap:6px;flex-wrap:wrap;padding:2px 0}
.ty-hit-toolbar button,.ty-hit-card button,.ty-hit-dialog button{border:1px solid rgba(255,255,255,.18);border-radius:4px;background:rgba(255,255,255,.08);color:inherit;padding:4px 8px;cursor:pointer;font-size:11px;line-height:1.2}
.ty-hit-toolbar button:hover,.ty-hit-card button:hover,.ty-hit-dialog button:hover{background:rgba(255,255,255,.18)}
.ty-hit-toolbar button:disabled,.ty-hit-card button:disabled{opacity:.55;cursor:wait}
.ty-hit-status{font-size:11px;color:var(--descrip-text,#aaa);min-height:16px;flex:1}
.ty-hit-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px;width:100%;max-height:min(62vh,760px);overflow:auto;padding:1px;box-sizing:border-box}
.ty-hit-card{position:relative;min-width:0;aspect-ratio:1;background:rgba(0,0,0,.18);border-radius:5px;overflow:hidden;box-shadow:0 0 0 1px rgba(255,255,255,.08)}
.ty-hit-card img{display:block;width:100%;height:100%;object-fit:cover;cursor:zoom-in;transition:filter .15s}.ty-hit-card:hover img{filter:brightness(.78)}
.ty-hit-card .ty-hit-badge{position:absolute;left:4px;top:4px;border:0;border-radius:4px;padding:3px 5px;background:rgba(23,126,76,.9);color:#fff;font-size:10px;cursor:pointer;max-width:calc(100% - 8px);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.ty-hit-card .ty-hit-badge.empty{background:rgba(90,90,90,.88)}
.ty-hit-card .ty-hit-actions{position:absolute;right:4px;bottom:4px;display:flex;gap:4px;opacity:0;transition:opacity .15s}.ty-hit-card:hover .ty-hit-actions,.ty-hit-card:focus-within .ty-hit-actions{opacity:1}.ty-hit-card .ty-hit-actions button{background:rgba(15,15,15,.8);padding:4px 6px}
.ty-hit-empty{padding:12px 6px;text-align:center;font-size:12px;color:var(--descrip-text,#aaa);border:1px dashed rgba(255,255,255,.18);border-radius:5px}
.ty-hit-dialog-backdrop{position:fixed;inset:0;z-index:10000;background:rgba(0,0,0,.72);display:flex;align-items:center;justify-content:center;padding:24px;box-sizing:border-box}.ty-hit-dialog{width:min(900px,96vw);max-height:92vh;display:flex;flex-direction:column;gap:10px;background:var(--comfy-menu-bg,#242424);color:var(--fg-color,#eee);border:1px solid rgba(255,255,255,.2);border-radius:8px;padding:12px;box-sizing:border-box;box-shadow:0 18px 60px rgba(0,0,0,.55)}
.ty-hit-dialog img{display:block;max-width:100%;max-height:52vh;object-fit:contain;background:#111;border-radius:5px;align-self:center}.ty-hit-dialog .ty-hit-dialog-title{display:flex;justify-content:space-between;gap:8px;align-items:center;font-size:13px;font-weight:600}.ty-hit-dialog textarea{width:100%;min-height:80px;max-height:180px;resize:vertical;box-sizing:border-box;background:rgba(0,0,0,.28);color:inherit;border:1px solid rgba(255,255,255,.16);border-radius:4px;padding:7px;font:12px/1.4 ui-monospace,SFMono-Regular,Consolas,monospace}.ty-hit-dialog .ty-hit-dialog-actions{display:flex;gap:6px;flex-wrap:wrap}
.ty-hit-resources{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.ty-hit-resource-group{min-width:0;padding:7px 8px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.12);border-radius:4px}.ty-hit-resource-title{font-size:11px;font-weight:600;color:var(--descrip-text,#aaa);margin-bottom:4px}.ty-hit-resource-list{font-size:12px;line-height:1.4;white-space:pre-line;overflow-wrap:anywhere}.ty-hit-resource-empty{color:var(--descrip-text,#888)}
`;
document.head.appendChild(style);

function notify(message, kind = "info") {
  const color = kind === "error" ? "#e66" : kind === "ok" ? "#6dca91" : "#eee";
  const toast = document.createElement("div"); toast.textContent = message; toast.style.cssText = `position:fixed;right:18px;bottom:18px;z-index:11000;padding:8px 12px;border-radius:5px;background:rgba(25,25,25,.94);color:${color};font:12px system-ui,sans-serif;box-shadow:0 4px 16px rgba(0,0,0,.35)`; document.body.appendChild(toast); setTimeout(() => toast.remove(), 2600);
}

async function copyText(value, label) {
  if (!value) return notify("当前图片没有可复制的内容", "error");
  try { await navigator.clipboard.writeText(value); } catch (_) { const area = document.createElement("textarea"); area.value = value; area.style.cssText = "position:fixed;opacity:0"; document.body.appendChild(area); area.select(); const ok = document.execCommand("copy"); area.remove(); if (!ok) return notify("复制失败，请手动选择文本", "error"); }
  notify(`${label || "内容"}已复制`, "ok");
}

async function downloadItem(item, button) {
  if (isLocalItem(item)) return notify("本地图片已在 ComfyUI/output/ty-node/ 中", "info");
  if (!item?.url) return notify("当前图片没有可下载地址", "error");
  const oldLabel = button?.textContent; if (button) { button.disabled = true; button.textContent = "下载中…"; }
  try { const response = await fetch(DOWNLOAD_ENDPOINT, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({url: item.url, id: item.id})}); const data = await response.json().catch(() => ({})); if (!response.ok || data.error) throw new Error(data.error || `HTTP ${response.status}`); notify(`已下载：${data.filename || "output/ty-node"}`, "ok"); return data; }
  catch (error) { notify(`下载失败：${error.message || error}`, "error"); return null; }
  finally { if (button) { button.disabled = false; button.textContent = oldLabel || "下载"; } }
}

function metadataText(item) { const metadata = item?.metadata ?? item?.meta; return metadata && typeof metadata === "object" ? JSON.stringify(metadata, null, 2) : ""; }

function resourceLabel(resource) {
  if (typeof resource === "string") return resource.trim();
  if (!resource || typeof resource !== "object") return "";
  const name = resource.name || resource.modelName || resource.model || "未命名资源";
  const hash = resource.hash || resource.modelHash;
  return hash ? `${name} · ${hash}` : String(name);
}

function resourceValues(item, kind) {
  const direct = Array.isArray(item?.[kind]) ? item[kind] : [];
  if (direct.length) return direct;
  const metadata = item?.metadata ?? item?.meta;
  if (!metadata || typeof metadata !== "object") return [];
  if (Array.isArray(metadata[kind])) return metadata[kind];
  if (!Array.isArray(metadata.resources)) return [];
  return metadata.resources.filter((resource) => {
    const type = String(resource?.type || resource?.resourceType || "").toLowerCase();
    return kind === "loras" ? type.includes("lora") || type.includes("lycoris") : type.includes("model") || ["checkpoint", "ckpt", "vae", "embedding"].includes(type);
  });
}

function isLocalItem(item) {
  const url = item?.url;
  return item?.local === true || item?.source === "local" || (typeof url === "string" && url.startsWith("/view?") && /(?:^|&)type=output(?:&|$)/.test(url));
}

function cycleEnumWidget(widget) {
  const values = widget?.options?.values;
  if (!Array.isArray(values) || values.length < 2) return false;
  const currentIndex = values.indexOf(widget.value);
  const nextIndex = (currentIndex < 0 ? 0 : currentIndex + 1) % values.length;
  widget.value = values[nextIndex];
  if (typeof widget.callback === "function") widget.callback(widget.value);
  return true;
}

function openDialog(item) {
  const backdrop = document.createElement("div"); backdrop.className = "ty-hit-dialog-backdrop"; const dialog = document.createElement("div"); dialog.className = "ty-hit-dialog";
  const title = document.createElement("div"); title.className = "ty-hit-dialog-title"; title.append(document.createTextNode(item?.has_prompt ? "提示词详情" : "图片详情")); const close = document.createElement("button"); close.textContent = "关闭"; close.onclick = () => backdrop.remove(); title.appendChild(close);
  const image = document.createElement("img"); image.src = item?.url || ""; image.alt = `Civitai ${item?.id || "image"}`; const prompt = document.createElement("textarea"); prompt.readOnly = true; prompt.placeholder = "没有检测到正向提示词"; prompt.value = item?.prompt || ""; const negative = document.createElement("textarea"); negative.readOnly = true; negative.placeholder = "没有检测到负面提示词"; negative.value = item?.negative_prompt || "";
  const resources = document.createElement("div"); resources.className = "ty-hit-resources"; const addResourceGroup = (label, kind) => { const group = document.createElement("div"); group.className = "ty-hit-resource-group"; const heading = document.createElement("div"); heading.className = "ty-hit-resource-title"; heading.textContent = label; const list = document.createElement("div"); list.className = "ty-hit-resource-list"; const values = resourceValues(item, kind).map(resourceLabel).filter(Boolean); list.textContent = values.length ? values.join("\n") : "未检测到"; if (!values.length) list.classList.add("ty-hit-resource-empty"); group.append(heading, list); resources.appendChild(group); }; addResourceGroup("模型", "models"); addResourceGroup("LoRA", "loras");
  const actions = document.createElement("div"); actions.className = "ty-hit-dialog-actions"; const cpPrompt = document.createElement("button"); cpPrompt.textContent = "复制正向提示词"; cpPrompt.onclick = () => copyText(prompt.value, "正向提示词"); const cpNegative = document.createElement("button"); cpNegative.textContent = "复制负面提示词"; cpNegative.onclick = () => copyText(negative.value, "负面提示词"); const all = document.createElement("button"); all.textContent = "复制全部 metadata"; all.onclick = () => copyText([prompt.value && `Prompt: ${prompt.value}`, negative.value && `Negative prompt: ${negative.value}`, metadataText(item)].filter(Boolean).join("\n"), "Metadata"); const local = isLocalItem(item); const dialogDownload = document.createElement("button"); dialogDownload.textContent = "下载图片"; dialogDownload.onclick = () => downloadItem(item, dialogDownload); const source = item?.source_url || item?.post_url; const openSource = document.createElement("button"); openSource.textContent = local ? "本地文件" : "打开 Civitai 原帖"; openSource.onclick = () => { if (source) window.open(source, "_blank", "noopener,noreferrer"); }; openSource.disabled = local || !source; if (!local) actions.append(dialogDownload); actions.append(cpPrompt, cpNegative, all, openSource);
  dialog.append(title, image, document.createTextNode("正向提示词"), prompt, document.createTextNode("负面提示词"), negative, resources, actions); backdrop.appendChild(dialog); backdrop.onclick = (event) => { if (event.target === backdrop) backdrop.remove(); }; document.body.appendChild(backdrop); close.focus();
}

app.registerExtension({name: "ty.hit.image.node", nodeCreated(node) {
  if (!NODE_TYPES.has(node.comfyClass)) return; node.properties = node.properties || {}; const findWidget = (name) => node.widgets?.find((widget) => widget.name === name); const setHidden = (name) => { const widget = findWidget(name); if (!widget) return; widget.hidden = true; widget.computeSize = () => [0, -4]; if (widget.element) widget.element.style.display = "none"; }; setHidden("page"); setHidden("refresh");
  const enumWidgets = (node.widgets || []).filter((widget) => !widget.hidden && Array.isArray(widget?.options?.values) && widget.options.values.length > 1); const previousMouseDown = node.onMouseDown; node.onMouseDown = function(event, pos, canvas) { if (event?.button === 2) { const y = Number(pos?.[1]); const target = enumWidgets.find((widget) => { const top = Number(widget.last_y); const height = Number(widget.computeSize?.(node.size?.[0])?.[1] || 30); return Number.isFinite(y) && Number.isFinite(top) && y >= top && y <= top + height; }); if (target && cycleEnumWidget(target)) { event.preventDefault?.(); event.stopPropagation?.(); node.setDirtyCanvas?.(true, true); return true; } } return previousMouseDown?.apply(this, arguments); };
  const resetOnChange = new Set(["site", "prompt_query", "period", "count", "sfw", "sort", "only_with_prompt", "source"]); const originalWidgetCallbacks = new WeakMap(); (node.widgets || []).forEach((widget) => { if (!resetOnChange.has(widget.name) || typeof widget.callback !== "function") return; const original = widget.callback; originalWidgetCallbacks.set(widget, original); widget.callback = function(value) { const page = findWidget("page"); if (page) page.value = 0; return original.apply(this, arguments); }; });
  const previousWidgetChanged = node.onWidgetChanged; node.onWidgetChanged = function(name, value, oldValue) { if (previousWidgetChanged) previousWidgetChanged.apply(this, arguments); if (resetOnChange.has(name)) { const page = findWidget("page"); if (page) page.value = 0; } };
  const root = document.createElement("div"); root.className = "ty-hit-gallery"; const toolbar = document.createElement("div"); toolbar.className = "ty-hit-toolbar"; const loadButton = document.createElement("button"); loadButton.textContent = "加载灵感图"; const refreshButton = document.createElement("button"); refreshButton.textContent = "刷新结果"; const nextButton = document.createElement("button"); nextButton.textContent = "下一页"; const allDownloadButton = document.createElement("button"); allDownloadButton.textContent = "下载当前页"; const status = document.createElement("span"); status.className = "ty-hit-status"; status.textContent = "尚未加载"; toolbar.append(loadButton, refreshButton, nextButton, allDownloadButton, status); const grid = document.createElement("div"); grid.className = "ty-hit-grid"; root.append(toolbar, grid); node._tyHitRoot = root; node._tyHitGrid = grid; node._tyHitStatus = status;
  const setStatus = (message, kind = "") => { status.textContent = message; status.style.color = kind === "error" ? "#e66" : kind === "ok" ? "#6dca91" : ""; }; const setBusy = (busy) => { loadButton.disabled = refreshButton.disabled = nextButton.disabled = allDownloadButton.disabled = busy; }; const queue = (mode) => { const page = findWidget("page"); const refresh = findWidget("refresh"); if ((mode === "next" || mode === "load" || mode === "refresh") && page) page.value = mode === "next" ? (Number(page.value) || 0) + 1 : 0; if (refresh && (mode === "load" || mode === "refresh")) refresh.value = mode === "refresh"; setStatus(mode === "next" ? "正在加载下一页…" : mode === "refresh" ? "正在刷新第一页…" : "正在加载第一页…"); setBusy(true); if (app.queuePrompt) app.queuePrompt(); };
  loadButton.onclick = () => queue("load"); refreshButton.onclick = () => queue("refresh"); nextButton.onclick = () => queue("next"); allDownloadButton.onclick = async () => { const items = node._tyHitItems || []; if (!items.length) return notify("当前页没有图片", "error"); setBusy(true); setStatus(`正在下载 ${items.length} 张…`); let success = 0; for (const item of items) if (await downloadItem(item)) success += 1; setBusy(false); setStatus(`已下载 ${success}/${items.length} 张`, success === items.length ? "ok" : "error"); };
  function render(items, info = {}) { grid.style.maxHeight = Math.max(120, (node.size?.[1] || 420) - 105) + "px"; const safeItems = Array.isArray(items) ? items.filter((item) => item && item.url) : []; const localMode = info.source === "local" || safeItems.some(isLocalItem); allDownloadButton.style.display = localMode ? "none" : ""; node._tyHitItems = safeItems; node.properties.ty_hit_gallery = safeItems.map((item) => ({...item})); grid.replaceChildren(); if (!safeItems.length) { const empty = document.createElement("div"); empty.className = "ty-hit-empty"; empty.textContent = info.error || "没有符合条件的图片"; grid.appendChild(empty); setStatus(info.error ? "加载失败" : "暂无结果", info.error ? "error" : ""); } else { safeItems.forEach((item) => { const card = document.createElement("div"); card.className = "ty-hit-card"; card.tabIndex = 0; const img = document.createElement("img"); img.src = item.url; img.alt = `${localMode ? "本地" : "Civitai"} ${item.id || "image"}`; img.onerror = () => { img.style.opacity = ".35"; }; img.onclick = () => openDialog(item); const badge = document.createElement("button"); badge.className = `ty-hit-badge${item.has_prompt ? "" : " empty"}`; badge.textContent = item.has_prompt ? "提示词 ✓" : "无提示词"; badge.title = "打开详情"; badge.onclick = (event) => { event.stopPropagation(); openDialog(item); }; const actions = document.createElement("div"); actions.className = "ty-hit-actions"; const download = document.createElement("button"); download.textContent = "下载"; download.onclick = (event) => { event.stopPropagation(); downloadItem(item, download); }; const details = document.createElement("button"); details.textContent = "详情"; details.onclick = (event) => { event.stopPropagation(); openDialog(item); }; if (!isLocalItem(item)) actions.append(download); actions.append(details); card.append(img, badge, actions); grid.appendChild(card); }); const page = Number(findWidget("page")?.value || 0) + 1; const sourceLabel = localMode ? "本地历史 · " : info.stale ? "缓存 · " : ""; setStatus(`${sourceLabel}第 ${page} 页 · ${safeItems.length} 张`, "ok"); } setBusy(false); if (node.setDirtyCanvas) node.setDirtyCanvas(true, true); }
  const saved = node.properties.ty_hit_gallery; if (Array.isArray(saved) && saved.length) render(saved, {stale: true}); if (node.addDOMWidget) node._tyHitWidget = node.addDOMWidget("ty_hit_preview", "preview", root, {serialize: false}); const previousExecuted = node.onExecuted; node.onExecuted = (output) => { if (previousExecuted) previousExecuted.call(node, output); const raw = output?.civitai || output?.output?.civitai || output?.output?.ui?.civitai || []; let info = output?.civitai_info || output?.output?.civitai_info || {}; if (typeof info === "string") { try { info = JSON.parse(info); } catch (_) {} } const payload = Array.isArray(raw) ? raw : (raw?.items || []); render(payload, info); }; const previousError = node.onExecutionError; node.onExecutionError = (error) => { if (previousError) previousError.call(node, error); render([], {error: error?.message || "节点执行失败"}); };
  const previousResize = node.onResize; node.onResize = function(size) { if (previousResize) previousResize.apply(this, arguments); if (node._tyHitGrid) node._tyHitGrid.style.maxHeight = Math.max(120, (node.size?.[1] || 420) - 105) + "px"; };
}});



