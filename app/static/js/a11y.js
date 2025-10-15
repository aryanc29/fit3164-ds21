// a11y.js — theme, motion, font size, caption + TTS (no colour palette)
(function () {
  const qs = id => document.getElementById(id);

  function applyTheme(on){ document.body.classList.toggle("theme-dark-high-contrast", !!on); }
  function applyMotion(on){ document.body.classList.toggle("prefers-reduced-motion", !!on); }
  function applyFont(px){ document.body.style.setProperty("font-size", px + "px"); }

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
    const dark   = qs("dark-contrast");
    const motion = qs("reduced-motion");
    const font   = qs("font-size");
    const speak  = qs("speak-summary");

    // Apply initial state
    applyTheme(dark && dark.checked);
    applyMotion(motion && motion.checked);
    applyFont(parseInt(font?.value || "18", 10));

    // Listeners
    if (speak) speak.addEventListener("click", speakCaption);
    if (dark) dark.addEventListener("change", () => applyTheme(dark.checked));
    if (motion) motion.addEventListener("change", () => {
      applyMotion(motion.checked);
      if (window.applyReducedMotionToMap) window.applyReducedMotionToMap(motion.checked);
      if (window.applyReducedMotionToCharts) window.applyReducedMotionToCharts(motion.checked);
    });
    if (font) font.addEventListener("input", () => applyFont(parseInt(font.value, 10)));

    refreshCaption();
  }

  // Expose minimal API
  window.A11Y = { initControls };
})();
