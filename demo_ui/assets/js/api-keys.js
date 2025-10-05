/**
 * API Key Manager
 * Handles secure storage and retrieval of API keys in session storage only
 */

export class APIKeyManager {
  constructor() {
    this.ANTHROPIC_KEY = 'floodguard_anthropic_key';
    this.OPENAI_KEY = 'floodguard_openai_key';
    this.initModal();
    this.checkKeys();
  }

  initModal() {
    const modal = document.getElementById('settingsModal');
    const settingsBtn = document.getElementById('settingsBtn');
    const closeBtn = document.getElementById('closeSettings');
    const saveBtn = document.getElementById('saveKeys');
    const clearBtn = document.getElementById('clearKeys');

    // Open modal
    settingsBtn.addEventListener('click', () => {
      this.openModal();
    });

    // Close modal
    closeBtn.addEventListener('click', () => {
      this.closeModal();
    });

    // Close on overlay click
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        this.closeModal();
      }
    });

    // Save keys
    saveBtn.addEventListener('click', () => {
      this.saveKeys();
    });

    // Clear keys
    clearBtn.addEventListener('click', () => {
      this.clearKeys();
    });

    // Close on Escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && modal.classList.contains('active')) {
        this.closeModal();
      }
    });
  }

  openModal() {
    const modal = document.getElementById('settingsModal');
    const anthropicInput = document.getElementById('anthropicKey');
    const openaiInput = document.getElementById('openaiKey');

    // Load existing keys (masked)
    const anthropicKey = this.getAnthropicKey();
    const openaiKey = this.getOpenAIKey();

    if (anthropicKey) {
      anthropicInput.value = this.maskKey(anthropicKey);
    }
    if (openaiKey) {
      openaiInput.value = this.maskKey(openaiKey);
    }

    modal.classList.add('active');
  }

  closeModal() {
    const modal = document.getElementById('settingsModal');
    modal.classList.remove('active');
    this.clearStatus();
  }

  saveKeys() {
    const anthropicInput = document.getElementById('anthropicKey');
    const openaiInput = document.getElementById('openaiKey');
    const statusDiv = document.getElementById('apiStatus');

    const anthropicKey = anthropicInput.value.trim();
    const openaiKey = openaiInput.value.trim();

    // Validate keys
    if (!anthropicKey && !openaiKey) {
      this.showStatus('Please enter at least one API key', 'error');
      return;
    }

    // Save to session storage (not localStorage - only for current session)
    if (anthropicKey && !anthropicKey.includes('•')) {
      sessionStorage.setItem(this.ANTHROPIC_KEY, anthropicKey);
    }
    if (openaiKey && !openaiKey.includes('•')) {
      sessionStorage.setItem(this.OPENAI_KEY, openaiKey);
    }

    this.showStatus('✓ API keys saved successfully! (Session only)', 'success');

    setTimeout(() => {
      this.closeModal();
      // Reload the page to reinitialize with new keys
      window.location.reload();
    }, 1500);
  }

  clearKeys() {
    if (confirm('Are you sure you want to clear all API keys? You will need to re-enter them.')) {
      sessionStorage.removeItem(this.ANTHROPIC_KEY);
      sessionStorage.removeItem(this.OPENAI_KEY);
      
      document.getElementById('anthropicKey').value = '';
      document.getElementById('openaiKey').value = '';
      
      this.showStatus('API keys cleared', 'warning');
      
      setTimeout(() => {
        window.location.reload();
      }, 1000);
    }
  }

  checkKeys() {
    const anthropicKey = this.getAnthropicKey();
    const openaiKey = this.getOpenAIKey();

    if (!anthropicKey || !openaiKey) {
      // Show modal on first load if keys are missing
      setTimeout(() => {
        this.openModal();
        this.showStatus('Please enter your API keys to use FloodGuard PH', 'warning');
      }, 1000);
    }
  }

  getAnthropicKey() {
    return sessionStorage.getItem(this.ANTHROPIC_KEY);
  }

  getOpenAIKey() {
    return sessionStorage.getItem(this.OPENAI_KEY);
  }

  hasKeys() {
    return !!(this.getAnthropicKey() && this.getOpenAIKey());
  }

  maskKey(key) {
    if (!key || key.length < 8) return key;
    return key.substring(0, 7) + '•'.repeat(20) + key.substring(key.length - 4);
  }

  showStatus(message, type) {
    const statusDiv = document.getElementById('apiStatus');
    statusDiv.textContent = message;
    statusDiv.className = `api-status ${type}`;
  }

  clearStatus() {
    const statusDiv = document.getElementById('apiStatus');
    statusDiv.textContent = '';
    statusDiv.className = 'api-status';
  }
}