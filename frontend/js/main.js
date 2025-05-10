const chatBox = document.getElementById('chat-container');
const input = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const reportBtn = document.getElementById('report-btn');
let canGenerateReport = false;

document.getElementById("report-btn").addEventListener("click", async () => {
  if (!canGenerateReport) return;

  document.getElementById("report-btn").disabled = true;
  document.getElementById("report-btn").style.opacity = 0.5;

  try {
    const response = await fetch("/api/generate_report", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ history: chatHistory })
    });

    if (!response.ok) throw new Error("Failed to generate report");

    const markdown = await response.text();
    const reportHTML = marked.parse(markdown);
    const tempContainer = document.createElement("div");
    tempContainer.innerHTML = reportHTML;

    const opt = {
      margin: 0.5,
      filename: 'case_report.pdf',
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { scale: 2 },
      jsPDF: { unit: 'in', format: 'a4', orientation: 'portrait' }
    };

    const blob = await html2pdf().set(opt).from(tempContainer).outputPdf('blob');
    const blobUrl = URL.createObjectURL(blob);

    const message = `📄 <a href="${blobUrl}" download="case_report.pdf" target="_blank">case_report.pdf</a>`;
    addMessage(message, "system");

  } catch (err) {
    console.error(err);
    addMessage("❌ Failed to generate report.", "system");
  } finally {
    document.getElementById("report-btn").disabled = false;
    document.getElementById("report-btn").style.opacity = 1;
  }
});


let chat = [];
let headerShown = true;

function renderChat() {
  chatBox.innerHTML = '';

  if (headerShown) {
    const header = document.createElement('div');
    header.className = 'chat-header';
    header.innerText = 'Describe your desired procedure';
    chatBox.appendChild(header);
  }

  chat.forEach(([role, content], index) => {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role === 'user' ? 'user-message' : 'system-message'}`;

    if (role === 'system' && index === chat.length - 1) {
      typeWriterEffect(msgDiv, content);
    } else {
      msgDiv.innerText = content;
    }

    chatBox.appendChild(msgDiv);
  });

  chatBox.scrollTop = chatBox.scrollHeight;
}
async function typeWriterEffect(element, text, speed = 5) {
  for (let i = 0; i <= text.length; i++) {
    element.innerText = text.slice(0, i);
    await new Promise(resolve => setTimeout(resolve, speed));
  }
}


async function sendMessage() {
  const prompt = input.value.trim();
  if (!prompt) return;

  input.value = '';
  sendBtn.disabled = true;

  if (headerShown) headerShown = false;

  chat.push(['user', prompt]);
  renderChat();

  try {
    const response = await fetch('http://127.0.0.1:5000/neurocorp', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: chat.map(c => `${c[0]}:${c[1]}`)
      })
    });

    const data = await response.json();

    chat.push(['system', data.reply || '[No response]']);

    if (data.can_generate_report === true) {
      canGenerateReport = true;
      const reportBtn = document.getElementById("report-btn");
      reportBtn.disabled = false;
      reportBtn.style.opacity = 1;
    }

  } catch (err) {
    chat.push(['system', '[Error communicating with backend]']);
  }

  sendBtn.disabled = false;
  renderChat();
}


sendBtn.addEventListener('click', sendMessage);

input.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !sendBtn.disabled) {
    sendMessage();
  }
});

renderChat();