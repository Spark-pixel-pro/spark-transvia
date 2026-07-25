const EDGE_FUNCTION_URL = "https://kmxmgxiobhcovrvvcdqh.supabase.co/functions/v1/bright-api";
const SUPABASE_ANON_KEY = "sb_publishable_FiS3WrWInHeqakBWl8mr6A_aVC4IJ32";
let historiaRozmowy = [];

document.addEventListener('DOMContentLoaded', function() {
  const widgetHTML = `
    <button id="sparkBubble">💬</button>
    <div id="sparkPanel">
      <div class="spark-panel-header">
        <div><div class="h-title">Spark — TransVia</div><div class="h-sub">Asystent AI, dostępny 24/7</div></div>
        <button class="spark-close" id="sparkCloseBtn">✕</button>
      </div>
      <div class="spark-mode-toggle">
        <button class="spark-mode-btn active" id="btnTrybTekst">💬 Tekst</button>
        <button class="spark-mode-btn" id="btnTrybGlos">🎤 Głos</button>
      </div>
      <div class="spark-body">
        <div class="spark-chat-log" id="sparkChatLog"></div>
        <div class="spark-input-row" id="sparkInputRow">
          <input type="text" id="sparkInput" placeholder="Napisz wiadomość...">
          <button id="sparkSendBtn">Wyślij</button>
        </div>
        <div class="spark-voice-view" id="sparkVoiceView">
          <button class="spark-mic-btn" id="sparkMicBtn">🎤</button>
          <div class="spark-voice-status" id="sparkVoiceStatus">Kliknij mikrofon i powiedz coś</div>
        </div>
      </div>
    </div>
  `;
  document.body.insertAdjacentHTML('beforeend', widgetHTML);

  document.getElementById('sparkBubble').addEventListener('click', sparkOtworz);
  document.getElementById('sparkCloseBtn').addEventListener('click', sparkZamknij);
  document.getElementById('btnTrybTekst').addEventListener('click', () => ustawTrybWidgetu('tekst'));
  document.getElementById('btnTrybGlos').addEventListener('click', () => ustawTrybWidgetu('glos'));
  document.getElementById('sparkSendBtn').addEventListener('click', sparkWyslijTekst);
  document.getElementById('sparkInput').addEventListener('keydown', (e) => { if (e.key === 'Enter') sparkWyslijTekst(); });

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('in'); });
  }, { threshold: 0.15 });
  document.querySelectorAll('.reveal').forEach(el => observer.observe(el));

  inicjujGlos();
});

function sparkOtworz() { document.getElementById('sparkPanel').classList.add('open'); }
function sparkZamknij() { document.getElementById('sparkPanel').classList.remove('open'); }

function ustawTrybWidgetu(tryb) {
  document.getElementById('btnTrybTekst').classList.toggle('active', tryb === 'tekst');
  document.getElementById('btnTrybGlos').classList.toggle('active', tryb === 'glos');
  document.getElementById('sparkInputRow').style.display = tryb === 'tekst' ? 'flex' : 'none';
  document.getElementById('sparkVoiceView').classList.toggle('active', tryb === 'glos');
}

function dodajBanke(text, who) {
  const log = document.getElementById('sparkChatLog');
  const div = document.createElement('div');
  div.className = 'spark-bubble ' + who;
  div.textContent = text;
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
}

async function wyslijDoSparka(wiadomosc) {
  try {
    const response = await fetch(EDGE_FUNCTION_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": "Bearer " + SUPABASE_ANON_KEY, "apikey": SUPABASE_ANON_KEY },
      body: JSON.stringify({ wiadomosc: wiadomosc, tryb: "klient", historia: historiaRozmowy })
    });
    const data = await response.json();
    const odpowiedz = data.odpowiedz || "Przepraszam, coś poszło nie tak.";
    historiaRozmowy.push({ role: "user", content: wiadomosc });
    historiaRozmowy.push({ role: "assistant", content: odpowiedz });
    return odpowiedz;
  } catch (err) { return "Nie udało się połączyć. Spróbuj ponownie."; }
}

async function sparkWyslijTekst() {
  const input = document.getElementById('sparkInput');
  const tekst = input.value.trim();
  if (!tekst) return;
  dodajBanke(tekst, 'user');
  input.value = '';
  const odp = await wyslijDoSparka(tekst);
  dodajBanke(odp, 'bot');
}

function inicjujGlos() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const micBtn = document.getElementById('sparkMicBtn');
  const voiceStatus = document.getElementById('sparkVoiceStatus');
  if (!SpeechRecognition) {
    voiceStatus.textContent = "Twoja przeglądarka nie obsługuje głosu.";
    micBtn.disabled = true;
    return;
  }
  const recognition = new SpeechRecognition();
  recognition.lang = 'pl-PL'; recognition.continuous = false; recognition.interimResults = true;
  let listening = false, przetworzone = false, ostatniTekst = '', timerCiszy = null;

  micBtn.addEventListener('click', () => {
    if (listening) return;
    if (window.speechSynthesis) window.speechSynthesis.speak(new SpeechSynthesisUtterance(' '));
    przetworzone = false; ostatniTekst = '';
    try { recognition.start(); } catch (e) {}
  });
  recognition.onstart = () => { listening = true; micBtn.classList.add('listening'); voiceStatus.textContent = "Słucham..."; };
  recognition.onend = () => {
    listening = false; micBtn.classList.remove('listening');
    if (timerCiszy) clearTimeout(timerCiszy);
    if (!przetworzone && ostatniTekst.trim()) { przetworzone = true; obsluzGlos(ostatniTekst.trim()); }
  };
  recognition.onresult = (event) => {
    let finalText = '', interim = '';
    for (let i = event.resultIndex; i < event.results.length; i++) {
      if (event.results[i].isFinal) finalText += event.results[i][0].transcript;
      else interim += event.results[i][0].transcript;
    }
    if (finalText || interim) ostatniTekst = finalText || interim;
    if (timerCiszy) clearTimeout(timerCiszy);
    timerCiszy = setTimeout(() => { if (!przetworzone) recognition.stop(); }, 1500);
    if (finalText && !przetworzone) { przetworzone = true; recognition.stop(); obsluzGlos(finalText); }
  };
  async function obsluzGlos(tekst) {
    voiceStatus.textContent = "Spark myśli...";
    const odp = await wyslijDoSparka(tekst);
    voiceStatus.textContent = "Kliknij mikrofon i powiedz coś";
    const utter = new SpeechSynthesisUtterance(odp);
    utter.lang = 'pl-PL';
    window.speechSynthesis.speak(utter);
  }
}
