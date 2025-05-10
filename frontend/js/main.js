  const chatBox = document.getElementById('chat-box');
  const input = document.getElementById('chat-input');
  const sendBtn = document.getElementById('send-btn');
  const reportBtn = document.getElementById('report-btn');

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

    chat.forEach(entry => {
      const msgDiv = document.createElement('div');
      msgDiv.className = `message ${entry.role === 'user' ? 'user-message' : 'model-message'}`;
      msgDiv.innerText = entry.content;
      chatBox.appendChild(msgDiv);
    });

    chatBox.scrollTop = chatBox.scrollHeight;
  }

  async function sendMessage() {
    const prompt = input.value.trim();
    if (!prompt) return;

    input.value = '';
    sendBtn.disabled = true;

    if (headerShown) headerShown = false;

    chat.push({ role: 'user', content: prompt });
    renderChat();

    try {
      const response = await fetch('/api/fake-endpoint', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: chat.map(c => `${c.role}:${c.content}`)
        })
      });

      const data = await response.json();
      chat.push({ role: 'model', content: data.reply || '[No response]' });
    } catch (err) {
      chat.push({ role: 'model', content: '[Error communicating with backend]' });
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
