import { escapeHtml, generateId } from './utils.js';

export class ChatManager {
  constructor(config) {
    this.wsUrl = config.wsUrl;
    this.onMessage = config.onMessage;
    this.ws = null;
    this.sessionId = generateId();
    this.isConnected = false;
    
    this.messagesContainer = document.getElementById('chatMessages');
    this.inputElement = document.getElementById('chatInput');
    this.sendButton = document.getElementById('sendBtn');
    
    this.initializeEventListeners();
    this.connect();
  }
  
  initializeEventListeners() {
    // Send button click
    this.sendButton.addEventListener('click', () => this.sendMessage());
    
    // Enter key to send (Shift+Enter for new line)
    this.inputElement.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });
    
    // Auto-resize textarea
    this.inputElement.addEventListener('input', () => {
      this.inputElement.style.height = 'auto';
      this.inputElement.style.height = this.inputElement.scrollHeight + 'px';
    });
    
    // Welcome message examples
    this.messagesContainer.querySelectorAll('.welcome-message li').forEach(li => {
      li.addEventListener('click', () => {
        this.inputElement.value = li.textContent.replace(/^["']|["']$/g, '');
        this.sendMessage();
      });
    });
  }
  
  connect() {
    try {
      this.ws = new WebSocket(this.wsUrl);
      
      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.isConnected = true;
        this.sendButton.disabled = false;
      };
      
      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        this.handleMessage(data);
      };
      
      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.showError('Connection error. Please refresh the page.');
      };
      
      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.isConnected = false;
        this.sendButton.disabled = true;
        
        // Try to reconnect after 3 seconds
        setTimeout(() => this.connect(), 3000);
      };
    } catch (error) {
      console.error('Failed to connect:', error);
      this.showError('Failed to connect to server.');
    }
  }
  
  sendMessage() {
    const message = this.inputElement.value.trim();
    
    if (!message || !this.isConnected) return;
    
    // Check for API keys
    const anthropicKey = sessionStorage.getItem('floodguard_anthropic_key');
    const openaiKey = sessionStorage.getItem('floodguard_openai_key');

    if (!anthropicKey || !openaiKey) {
      this.addMessage('assistant', '⚠️ Please configure your API keys in Settings (gear icon) to use the chat feature.');
      return;
    }
    
    // Add user message to chat
    this.addMessage('user', message);
    
    // Clear input
    this.inputElement.value = '';
    this.inputElement.style.height = 'auto';
    
    // Disable send button
    this.sendButton.disabled = true;
    
    // Send to server with API keys
    try {
      this.ws.send(JSON.stringify({
        message: message,
        session_id: this.sessionId,
        anthropic_key: anthropicKey,
        openai_key: openaiKey
      }));
      
      // Add typing indicator
      this.addTypingIndicator();
    } catch (error) {
      console.error('Failed to send message:', error);
      this.showError('Failed to send message.');
      this.sendButton.disabled = false;
    }
  }
  
  handleMessage(data) {
    switch (data.type) {
      case 'status':
        this.updateTypingIndicator(data.message);
        break;
        
      case 'message':
        this.removeTypingIndicator();
        this.addMessage('assistant', data.content);
        if (data.done) {
          this.sendButton.disabled = false;
        }
        break;
        
      case 'projects':
      case 'map_bounds':
      case 'news':
        // Forward to app controller
        if (this.onMessage) {
          this.onMessage(data);
        }
        break;
        
      case 'error':
        this.removeTypingIndicator();
        this.showError(data.content);
        this.sendButton.disabled = false;
        break;
    }
  }
  
  addMessage(role, content) {
    // Remove welcome message if present
    const welcomeMsg = this.messagesContainer.querySelector('.welcome-message');
    if (welcomeMsg) {
      welcomeMsg.remove();
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    
    // Parse markdown-style formatting
    const formattedContent = this.parseMarkdown(content);
    bubble.innerHTML = formattedContent;
    
    messageDiv.appendChild(bubble);
    this.messagesContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    this.scrollToBottom();
  }
  
  parseMarkdown(text) {
    // Escape HTML first
    const escaped = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
    
    // Parse markdown patterns (order matters!)
    let result = escaped;
    
    // Bold FIRST: **text** (must be before single *)
    result = result.replace(/\*\*([^\*]+?)\*\*/g, '<strong>$1</strong>');
    
    // Italic: *text* (after bold is processed)
    result = result.replace(/\*([^\*]+?)\*/g, '<em>$1</em>');
    
    // Line breaks
    result = result.replace(/\n/g, '<br>');
    
    return result;
  }
  
  addTypingIndicator() {
    const indicator = document.createElement('div');
    indicator.className = 'message assistant';
    indicator.id = 'typingIndicator';
    
    const status = document.createElement('div');
    status.className = 'message-status typing';
    status.textContent = 'Thinking...';
    
    indicator.appendChild(status);
    this.messagesContainer.appendChild(indicator);
    this.scrollToBottom();
  }
  
  updateTypingIndicator(text) {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
      const status = indicator.querySelector('.message-status');
      if (status) {
        status.textContent = text;
      }
    }
  }
  
  removeTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
      indicator.remove();
    }
  }
  
  showError(message) {
    this.addMessage('assistant', `⚠️ ${message}`);
  }
  
  scrollToBottom() {
    this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
  }
}