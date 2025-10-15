// a11y.js — theme, motion, font size, colour-blind palettes, caption + TTS
(function () {
  const CB_PALETTES = {
    Viridis:["#440154","#3b528b","#21918c","#5ec962","#fde725"],
    Cividis:["#00204c","#293e70","#576690","#8d90a5","#c7c9a8","#ffea46"],
    Plasma:["#0d0887","#6a00a8","#b12a90","#e16462","#fca636","#eff821"],
    Inferno:["#000004","#1f0c48","#550f6d","#88226a","#b63655","#e65137","#fb9f27","#fcfdbf"],
    Magma:["#000004","#1c1044","#51127c","#b63679","#fb8761","#facd75","#fcfdbf"],
    Turbo:["#30123b","#4145ab","#2ab0d7","#2bdc9f","#86e83f","#fee825","#fd9b35","#fd4c4c"]
  };
  const qs = id => document.getElementById(id);

  function applyTheme(on){ document.body.classList.toggle("theme-dark-high-contrast", !!on); }
  function applyMotion(on){ document.body.classList.toggle("prefers-reduced-motion", !!on); }
  function applyFont(px){ document.body.style.setProperty("font-size", px + "px"); }

  function paletteToGradient(p){
    const g = {}; p.forEach((c,i)=>{ g[(i/(p.length-1)).toFixed(2)] = c; }); return g;
  }

  async function refreshCaption(){
    const el = qs("caption"); if(!el) return;
    try { const r = await fetch("/summary"); const j = await r.json(); el.textContent = j.text || "Summary unavailable."; }
    catch { el.textContent = "Summary unavailable."; }
  }

  function speakCaption(){
    const el = qs("caption"), status = qs("tts-status"); if(!el) return;
    try{
      const u = new SpeechSynthesisUtterance(el.textContent || "No summary available.");
      u.rate = document.body.classList.contains("prefers-reduced-motion") ? 0.9 : 1.0;
      const vs = window.speechSynthesis.getVoices();
      const v = vs.find(x => /en-AU|en-GB/.test(x.lang)) || vs[0]; if(v) u.voice = v;
      window.speechSynthesis.cancel(); window.speechSynthesis.speak(u);
      if(status) status.textContent = "Audio status: speaking…";
    } catch { if(status) status.textContent = "Audio status: not supported."; }
  }

  function initControls(){
    const colour = qs("colour-scale"),
          dark   = qs("dark-contrast"),
          motion = qs("reduced-motion"),
          font   = qs("font-size"),
          speak  = qs("speak-summary");

    // Defaults from page
    applyTheme(dark && dark.checked);
    applyMotion(motion && motion.checked);
    applyFont(parseInt(font?.value || "18", 10));

    if (speak) speak.addEventListener("click", speakCaption);

    if (colour) colour.addEventListener("change", () => {
      const name = colour.value;
      const pal = CB_PALETTES[name] || CB_PALETTES.Viridis;
      if (window.rebuildChartsWithPalette) window.rebuildChartsWithPalette(name, pal);
      if (window.updateHeatGradient) window.updateHeatGradient(paletteToGradient(pal));
    });
    if (dark) dark.addEventListener("change", () => applyTheme(dark.checked));
    if (motion) motion.addEventListener("change", () => {
      applyMotion(motion.checked);
      if (window.applyReducedMotionToMap) window.applyReducedMotionToMap(motion.checked);
      if (window.applyReducedMotionToCharts) window.applyReducedMotionToCharts(motion.checked);
    });
    if (font) font.addEventListener("input", () => applyFont(parseInt(font.value, 10)));

    refreshCaption();
  }

  // Expose tiny API for your existing code to hook into
  window.A11Y = { initControls, CB_PALETTES, paletteToGradient };
})();
