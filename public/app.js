const urlInput = document.getElementById('url');
const goBtn = document.getElementById('go');
const iframe = document.getElementById('viewer');
const backBtn = document.getElementById('back');
const forwardBtn = document.getElementById('forward');
const reloadBtn = document.getElementById('reload');
const spinner = document.getElementById('spinner');
const status = document.getElementById('status');

let historyStack = [];
let historyIndex = -1;

function setStatus(text){
  status.textContent = text;
}

function updateNavButtons(){
  backBtn.disabled = historyIndex <= 0;
  forwardBtn.disabled = historyIndex >= historyStack.length - 1 || historyIndex === -1;
}

function navigateTo(rawUrl, push=true){
  const v = rawUrl.trim();
  if (!v) return;
  const encoded = encodeURIComponent(v);
  iframe.src = '/proxy?url=' + encoded;
  setStatus('Loading ' + v + ' ...');
  spinner.classList.remove('hidden');

  if (push) {
    // trim forward history
    if (historyIndex < historyStack.length -1) historyStack = historyStack.slice(0, historyIndex+1);
    historyStack.push(v);
    historyIndex = historyStack.length -1;
  }
  urlInput.value = v;
  updateNavButtons();
}

goBtn.addEventListener('click', () => navigateTo(urlInput.value, true));
urlInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') goBtn.click(); });

backBtn.addEventListener('click', () => {
  if (historyIndex > 0) {
    historyIndex -= 1;
    navigateTo(historyStack[historyIndex], false);
    updateNavButtons();
  }
});

forwardBtn.addEventListener('click', () => {
  if (historyIndex < historyStack.length -1) {
    historyIndex += 1;
    navigateTo(historyStack[historyIndex], false);
    updateNavButtons();
  }
});

reloadBtn.addEventListener('click', () => {
  if (historyIndex >= 0) {
    navigateTo(historyStack[historyIndex], false);
  } else if (urlInput.value) {
    navigateTo(urlInput.value, false);
  }
});

// iframe load handlers
iframe.addEventListener('load', () => {
  spinner.classList.add('hidden');
  setStatus('Loaded');
});

iframe.addEventListener('error', () => {
  spinner.classList.add('hidden');
  setStatus('Failed to load');
});

// Initialize focus
urlInput.focus();

