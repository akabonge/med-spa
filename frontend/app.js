const API = '';
const SESSION_ID = 'session_' + Math.random().toString(36).slice(2, 10);
let messageCount = 0;
let contactCaptured = false;

// ── Chat open/close ───────────────────────────────────
function openChat() {
  const win = document.getElementById('chat-window');
  win.classList.add('open');
  if (messageCount === 0) sendWelcome();
  setTimeout(() => document.getElementById('chat-input').focus(), 250);
}

function toggleChat() {
  const win = document.getElementById('chat-window');
  const isOpen = win.classList.contains('open');
  if (isOpen) {
    win.classList.remove('open');
  } else {
    openChat();
  }
}

function sendWelcome() {
  appendMsg('bot', "Hi, I'm Luna — Luminara's AI wellness consultant. I'm here to help you find the right treatment for your goals and answer any questions about what we offer. What's been on your mind lately?");
}

// ── Message rendering ─────────────────────────────────
function appendMsg(role, text) {
  const container = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = `msg ${role}`;

  const avatar = document.createElement('div');
  avatar.className = 'msg-avatar';
  avatar.textContent = role === 'bot' ? '🌙' : '👤';

  const bubble = document.createElement('div');
  bubble.className = 'msg-bubble';
  bubble.textContent = text;

  div.appendChild(avatar);
  div.appendChild(bubble);
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function showTyping() {
  const container = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = 'msg bot';
  div.id = 'typing-indicator';

  const avatar = document.createElement('div');
  avatar.className = 'msg-avatar';
  avatar.textContent = '🌙';

  const bubble = document.createElement('div');
  bubble.className = 'msg-bubble';
  bubble.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';

  div.appendChild(avatar);
  div.appendChild(bubble);
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function removeTyping() {
  const el = document.getElementById('typing-indicator');
  if (el) el.remove();
}

// ── Contact capture card (appears after 3rd message) ─
function showContactCard() {
  if (contactCaptured) return;
  const container = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = 'msg bot';
  div.id = 'contact-card-msg';

  const avatar = document.createElement('div');
  avatar.className = 'msg-avatar';
  avatar.textContent = '🌙';

  const bubble = document.createElement('div');
  bubble.className = 'msg-bubble';
  bubble.style.maxWidth = '90%';

  bubble.innerHTML = `
    <div class="contact-card">
      <p>To book your free consultation, I just need a few quick details:</p>
      <input type="text" id="cc-name" placeholder="Your name" />
      <input type="email" id="cc-email" placeholder="Email address" />
      <input type="tel" id="cc-phone" placeholder="Phone (optional)" />
      <button onclick="submitContact()">Book My Free Consult →</button>
    </div>
  `;

  div.appendChild(avatar);
  div.appendChild(bubble);
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

async function submitContact() {
  const name = document.getElementById('cc-name').value.trim();
  const email = document.getElementById('cc-email').value.trim();
  const phone = document.getElementById('cc-phone').value.trim();

  if (!name || !email) {
    alert('Please enter your name and email.');
    return;
  }

  try {
    await fetch(`${API}/api/leads/contact`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: SESSION_ID, name, email, phone }),
    });
    contactCaptured = true;
    const card = document.getElementById('contact-card-msg');
    if (card) card.remove();
    appendMsg('bot', `Thank you, ${name}! I've noted your information. One of our team members will reach out within one business day to schedule your consultation. Is there anything else you'd like to know about the treatments we've discussed?`);
  } catch {
    appendMsg('bot', "There was a hiccup saving your info — please call us directly at (540) 899-4200 and we'll get you booked.");
  }
}

// ── Send message ──────────────────────────────────────
async function sendMessage() {
  const input = document.getElementById('chat-input');
  const text = input.value.trim();
  if (!text) return;

  input.value = '';
  input.style.height = 'auto';
  appendMsg('user', text);
  messageCount++;

  showTyping();

  try {
    const res = await fetch(`${API}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, session_id: SESSION_ID }),
    });
    const data = await res.json();
    removeTyping();
    appendMsg('bot', data.response);

    if (messageCount >= 3 && !contactCaptured) {
      setTimeout(showContactCard, 600);
    }
  } catch {
    removeTyping();
    appendMsg('bot', "I'm having a moment — please try again or call us at (540) 899-4200.");
  }
}

// ── Auto-resize textarea ──────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const input = document.getElementById('chat-input');
  if (!input) return;

  input.addEventListener('input', () => {
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 100) + 'px';
  });

  input.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
});
