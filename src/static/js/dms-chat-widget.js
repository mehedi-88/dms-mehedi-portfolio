
(function () {
  if (window.DMS_CHAT_INIT) return; 
  window.DMS_CHAT_INIT = true;

 const root = document.getElementById('dms-chatbot');
const API = (root.getAttribute('data-api') || '').replace(/\/+$/, '');

  // ---------- DOM refs ----------
  const $       = (s, r=document)=>r.querySelector(s);
  const fab     = root.querySelector(".dms-chat__fab");
  const panel   = root.querySelector(".dms-chat__panel");
  const closeX  = root.querySelector(".dms-chat__close");
  const msgsEl  = $("#dms-msgs", root);
  const input   = $("#dms-input", root);
  const sendBtn = $("#dms-send", root);
  const status  = $("#dms-status", root);
  const quick   = $("#dms-quick", root);

  // ---------- Teaser + badge ----------
  const teaser = document.createElement("button");
  teaser.type="button";
  teaser.className="dms-teaser";
  teaser.innerHTML = '<span class="dot"></span><span class="txt">Chat with us</span><span class="badge" id="dms-badge" hidden>0</span>';
  root.appendChild(teaser);

  const preview = document.createElement("div");
  preview.className = "dms-teaser__preview";
  preview.hidden = true;
  root.appendChild(preview);

  // ---------- Sound ----------
  let ding = document.getElementById("notify-audio");
  if (!ding) {
    ding = document.createElement("audio");
    ding.id = "notify-audio";
    ding.src = "/static/sound/notify.mp3";
    ding.preload = "auto";
    document.body.appendChild(ding);
  }

  // ---------- CID helpers ----------
  function setCID(v){
    try{ localStorage.setItem("dms_cid", v); }catch{}
    try{ document.cookie = `dms_cid=${encodeURIComponent(v)};path=/;max-age=${3600*24*400}`; }catch{}
  }
  function getCID(){
    try{
      const v = localStorage.getItem("dms_cid");
      if (v && v.startsWith("client-")) return v;
    }catch{}
    const fresh = "client-" + (crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).slice(2));
    setCID(fresh);
    return fresh;
  }
  const cid = getCID();

  // ---------- utils ----------
  const bubbleId = (mid) => mid ? `b_${mid}` : "";
  const setSeen  = (mid) => { const el = document.getElementById(bubbleId(mid)); if (el) el.setAttribute("data-status","seen"); };
  function notify(t,b){
    try{ if(ding){ ding.currentTime=0; ding.play().catch(()=>{});} }catch{}
    if ("Notification" in window && Notification.permission==="granted"){
      try{ const n=new Notification(t||"New message",{body:String(b||"").slice(0,80)}); setTimeout(()=>n.close(), 3500);}catch{}
    }
    if (navigator.vibrate) navigator.vibrate(15);
  }
  function scrollEnd(){ requestAnimationFrame(()=>{ msgsEl.scrollTop = msgsEl.scrollHeight; }); }
  function setBadge(on){
    status.textContent = on ? "Admin Online" : "AI Assistant";
    status.classList.toggle("is-admin", on);
    root.classList.toggle("admin-online", on);
  }

  // initial status
  fetch(`/api/status?t=${Date.now()}`)
    .then(r=>r.json()).then(j=>setBadge(!!j.online))
    .catch(()=>setBadge(false));

  // ---------- Typing row (single instance) ----------
  const typingRow = document.createElement("div");
  typingRow.id = "dms-typing-row";
  typingRow.className = "dms-typing"; // CSS: .dms-typing{display:none} .dms-typing.show{display:flex}
  typingRow.innerHTML = '<span class="label">Admin is typing</span><span class="dots"><i class="dot"></i><i class="dot"></i><i class="dot"></i></span>';
  msgsEl.appendChild(typingRow);

  let typingHideTimer = null;
  function showTyping(){
    typingRow.classList.add("show");
    clearTimeout(typingHideTimer);
    typingHideTimer = setTimeout(hideTyping, 3500); // failsafe
    scrollEnd();
  }
  function hideTyping(){
    typingRow.classList.remove("show");
    clearTimeout(typingHideTimer);
    typingHideTimer = null;
  }

  // ---------- SSE (ONLY ONE EventSource) ----------
  let es = null;
  function initSSE(){
    if (es) try{ es.close(); }catch(_){}
    es = new EventSource(`/sse/stream/${encodeURIComponent(cid)}`);

    // agent/bot typing → show/hide dots (রিয়েলটাইম)
    es.addEventListener("typing", e=>{
      try{
        const d = JSON.parse(e.data||"{}"); // {who:'agent'|'bot'|'client', state:true|false}
        if (d.who==="agent" || d.who==="bot"){
          d.state ? showTyping() : hideTyping();
        }
      }catch{}
    });

    // incoming message (agent/bot)
    es.addEventListener("message", e=>{
      try{
        const d = JSON.parse(e.data||"{}");
        const role = (d.role==="user" ? "user" : (d.role||"agent"));
        const text = d.text || "";
        const mid  = d.mid  || "";
        if (!text) return;

        // টাইপিং থামাও—মেসেজ এলেই
        hideTyping();

        // এজেন্ট/বট মেসেজে টাইপরাইটার (ইচ্ছা করলে সরাসরি addBubble করতে পারো)
        if (role === "agent" || role === "bot"){
          addTypewriter("agent", text, mid);
        }else{
          addBubble("user", text, mid);
        }

        if (role!=="user" && panel.hasAttribute("hidden")) {
          incBadge(text);
        }
        if (!panel.hasAttribute("hidden") && mid){
          markSeen([mid], "client");
        }
      }catch{}
    });

    // seen receipts (agent -> user)
    es.addEventListener("seen", e=>{
      try{
        const d = JSON.parse(e.data||"{}");
        if (d.who==="agent"){ (d.mids||[]).forEach(setSeen); }
      }catch{}
    });

    // admin presence badge live
    es.addEventListener("agent_status", e=>{
      try{
        const d = JSON.parse(e.data||"{}");
        setBadge(!!d.online);
      }catch{}
    });

    es.onerror = ()=>{ /* auto-reconnect by browser */ };
  }
  initSSE();

  // ---------- History + Heartbeat ----------
  (async function loadHistory(){
    try{
      const r = await fetch(`/api/chat/history/${encodeURIComponent(cid)}`);
      const list = await r.json();
      msgsEl.innerHTML = "";
      const mids=[];
      (list||[]).forEach(m=>{
        addBubble(m.role==='user'?'user':'agent', m.content, m.mid);
        if(m.role!=='user' && !m.seen_by_client && m.mid) mids.push(m.mid);
      });
      if (mids.length) markSeen(mids,"client");
      scrollEnd();
    }catch{}
  })();

  function heartbeat(){
    fetch("/api/client/heartbeat",{
      method:"POST", headers:{"Content-Type":"application/json"},
      body: JSON.stringify({cid})
    }).catch(()=>{});
  }
  heartbeat();
  setInterval(heartbeat, 20000);
  document.addEventListener("visibilitychange",()=>{ if(!document.hidden) heartbeat(); });

  // ---------- Panel / teaser / badge ----------
  const badgeEl = $("#dms-badge", root);
  let badgeCount=0, previewTimer=0;

  function incBadge(text){
    badgeCount++;
    badgeEl.textContent = String(badgeCount);
    badgeEl.hidden = false;
    preview.textContent = String(text||"").slice(0,60);
    preview.hidden = false;
    clearTimeout(previewTimer);
    previewTimer = setTimeout(()=>{ preview.hidden=true; }, 2600);
    notify("New message", text);
  }

  function resetBadge(){
    badgeCount = 0;
    badgeEl.hidden = true;
    preview.hidden = true;
  }

  const collectAgentMids = ()=>{
    const arr=[];
    msgsEl.querySelectorAll('.dms-chat__bubble:not(.dms-chat__bubble--user)[id^="b_"]').forEach(el=>{
      const id = el.id.slice(2);
      if (id) arr.push(id);
    });
    return arr;
  };

  function openPanel(){
    panel.removeAttribute("hidden");
    fab.setAttribute("aria-expanded","true");
    if (Notification.permission==="default"){
      try{ Notification.requestPermission().catch(()=>{}); }catch{}
    }
    const mids = collectAgentMids();
    if (mids.length) markSeen(mids,"client");
    resetBadge();
    scrollEnd();
  }
  function closePanel(){
    panel.setAttribute("hidden","");
    fab.setAttribute("aria-expanded","false");
  }
  function togglePanel(){ panel.hasAttribute("hidden") ? openPanel() : closePanel(); }

  fab?.addEventListener("click", togglePanel);
  teaser.addEventListener("click", openPanel);
  closeX?.addEventListener("click", closePanel);
  window.addEventListener("keydown", e=>{
    if(e.key==="Escape" && !panel.hasAttribute("hidden")) closePanel();
    if(e.key==="Enter"  &&  panel.hasAttribute("hidden")) openPanel();
  });

  // ---------- Send + Typing (client -> server) ----------
  let lastSendAt=0, typingTimer=null, sentTyping=false;

  async function send(){
    const now = Date.now();
    if (now - lastSendAt < 150) return; // debounce
    lastSendAt = now;

    const text = (input.value||"").trim();
    if (!text) return;

    // temp bubble
    const tempId = Math.random().toString(36).slice(2,10);
    const tmpMid = "tmp_"+tempId;
    const d = document.createElement("div");
    d.className = "dms-chat__bubble dms-chat__bubble--user";
    d.id = "b_"+tmpMid;
    d.dataset.tempid = tempId;
    d.textContent = text;
    msgsEl.appendChild(d);
    scrollEnd();

    try{
      const r = await fetch("/api/client/message",{
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({ cid, text, tempId })
      });
      const j = await r.json();
      const serverMid = j && j.mid ? j.mid : null;
      const el = document.querySelector(`[data-tempid="${tempId}"]`);
      if (el){
        el.id = "b_"+(serverMid||tmpMid);
        el.removeAttribute("data-tempid");
        el.setAttribute("data-status","sent");
      }
    }catch{
      d.setAttribute("data-status","sent");
    }

    // stop typing
    try{
      await fetch("/api/typing",{
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({ cid, who:"client", state:false })
      });
    }catch{}
    sentTyping=false;

    input.value = "";
    autoResize();
    scrollEnd();
  }

  sendBtn?.addEventListener("click", send);
  input?.addEventListener("keydown", e=>{
    if(e.key==="Enter" && !e.shiftKey){ e.preventDefault(); send(); }
  });

  // quick suggestion pills (data-q)
  if (quick){
    quick.addEventListener("click", (e)=>{
      const btn = e.target.closest(".dms-quick__pill");
      if(!btn) return;
      input.value = btn.dataset.q || btn.textContent || "";
      autoResize();
      send();
    });
  }

  // emit typing while user types (client -> admin)
  async function typingPublish(s){
    try{
      await fetch("/api/typing",{
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({ cid, who:"client", state:s })
      });
    }catch{}
  }
  function emitTyping(){
    if (!sentTyping){ typingPublish(true); sentTyping=true; }
    clearTimeout(typingTimer);
    typingTimer = setTimeout(()=>{ typingPublish(false); sentTyping=false; }, 800);
  }
  input?.addEventListener("input", emitTyping);
  input?.addEventListener("keydown", emitTyping);

  // ---------- Render helpers ----------
  function addBubble(who, text, mid){
    const d = document.createElement("div");
    d.className = "dms-chat__bubble " + (who==="user" ? "dms-chat__bubble--user" : "dms-chat__bubble--agent");
    if (mid) d.id = bubbleId(mid);
    d.textContent = text;
    msgsEl.appendChild(d);
    scrollEnd();
    if (who!=="user") notify("New reply", text);
  }

  function addTypewriter(who, text, mid){
    // visual pre-typing dots (immediate feedback)
    const dots = document.createElement("div");
    dots.className = "dms-typing show";
    dots.innerHTML = '<span class="label">Admin is typing</span><span class="dots"><i class="dot"></i><i class="dot"></i><i class="dot"></i></span>';
    msgsEl.appendChild(dots);
    scrollEnd();

    const row = document.createElement("div");
    row.className = "dms-chat__bubble " + (who==="user" ? "dms-chat__bubble--user" : "dms-chat__bubble--agent") + " dms-caret";
    if (mid) row.id = bubbleId(mid);

    let i=0, cps=28;
    function step(){
      if (i===0){ dots.remove(); msgsEl.appendChild(row); }
      row.textContent = text.slice(0,i);
      i++;
      if (i <= text.length) setTimeout(step, 1000/cps);
      else { row.classList.remove("dms-caret"); scrollEnd(); }
    }
    setTimeout(step, 120);

    if (who!=="user") notify("New reply", text);
  }

  async function markSeen(mids, who){
    try{
      await fetch("/api/seen",{
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({ cid, mids, who })
      });
      mids.forEach(setSeen);
    }catch{}
  }

  // ---------- textarea autoresize ----------
  function autoResize(){
    if (!input) return;
    input.style.height = "auto";
    const MAX = 140;
    const h = Math.min(input.scrollHeight, MAX);
    input.style.height = h + "px";
    input.style.overflowY = input.scrollHeight > MAX ? "auto" : "hidden";
  }
  window.addEventListener("load", autoResize);

  // teaser pulse once
  setTimeout(()=>teaser.classList.add("show"), 300);
  setTimeout(()=>teaser.classList.remove("show"), 2600);
})();
// ONE EventSource only (top-level)
const es = new EventSource(`/sse/stream/${encodeURIComponent(cid)}`);

// agent/bot typing → show/hide dots (REALTIME)
es.addEventListener('typing', (e)=>{
  try{
    const d = JSON.parse(e.data||'{}'); // {who, state}
    if (d.who === 'agent' || d.who === 'bot'){
      d.state ? showTyping() : hideTyping();
    }
  }catch(_){}
});

// নতুন মেসেজ এলে ডট লুকাও (already in your code)
es.addEventListener('message', ()=>{
  hideTyping();
});