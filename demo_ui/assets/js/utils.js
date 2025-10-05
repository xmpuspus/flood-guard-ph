// Utility functions

export function formatCurrency(amount) {
  if (!amount) return '₱0';
  return '₱' + Number(amount).toLocaleString('en-PH', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
}

export function formatCurrencyShort(amount) {
  if (!amount) return '₱0';
  
  const num = Number(amount);
  if (num >= 1000000) {
    return '₱' + (num / 1000000).toFixed(1) + 'M';
  } else if (num >= 1000) {
    return '₱' + (num / 1000).toFixed(1) + 'K';
  }
  return '₱' + num.toLocaleString('en-PH');
}

export function formatDate(dateString) {
  if (!dateString) return 'N/A';
  
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-PH', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  } catch (e) {
    return dateString;
  }
}

export function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

export function generateId() {
  return Math.random().toString(36).substring(2, 15);
}

export function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}