import { formatDate } from './utils.js';

export class NewsManager {
  constructor(config) {
    this.containerId = config.containerId;
    this.itemsContainer = document.getElementById('newsItems');
  }
  
  render(articles) {
    if (!articles || articles.length === 0) {
      this.showEmpty();
      return;
    }
    
    const html = articles.map(article => this.createNewsCard(article)).join('');
    this.itemsContainer.innerHTML = html;
    
    // Add click handlers
    this.itemsContainer.querySelectorAll('.news-card').forEach((card) => {
      card.addEventListener('click', () => {
        const url = card.dataset.url;
        if (url && url !== '#') {
          window.open(url, '_blank', 'noopener,noreferrer');
        }
      });
    });
  }
  
  createNewsCard(article) {
    const title = article.title || 'Untitled Article';
    const snippet = article.snippet || 'No description available';
    const source = article.source || 'Unknown';
    const publishedDate = article.published_date || article.published || '';
    const url = article.url || '#';
    
    return `
      <div class="news-card" data-url="${url}">
        <div class="news-header">
          <span class="news-source">${source}</span>
          <span class="news-date">${formatDate(publishedDate)}</span>
        </div>
        <h4 class="news-title">${title}</h4>
        <p class="news-snippet">${snippet}</p>
      </div>
    `;
  }
  
  async fetchForProject(project) {
    this.showLoading();
    
    try {
      // Build search query from project details
      const description = project.description || project.project_description || '';
      const contractor = project.contractor || '';
      const municipality = project.municipality || project.Municipality || '';
      const province = project.province || project.Province || '';
      const location = `${municipality} ${province}`.trim();
      
      // Create URL with all parameters
      const params = new URLSearchParams();
      if (description) params.append('query', description);
      if (contractor && contractor !== 'N/A') params.append('contractor', contractor);
      if (location) params.append('location', location);
      
      const response = await fetch(`/api/news?${params.toString()}`);
      const data = await response.json();
      
      if (data.articles && data.articles.length > 0) {
        this.render(data.articles);
      } else {
        this.showEmpty();
      }
    } catch (error) {
      console.error('Error fetching news:', error);
      this.showError();
    }
  }
  
  async fetchForContractor(contractor) {
    this.showLoading();
    
    try {
      const params = new URLSearchParams();
      params.append('contractor', contractor);
      params.append('query', 'flood control infrastructure');
      
      const response = await fetch(`/api/news?${params.toString()}`);
      const data = await response.json();
      
      if (data.articles && data.articles.length > 0) {
        this.render(data.articles);
      } else {
        this.showEmpty();
      }
    } catch (error) {
      console.error('Error fetching news:', error);
      this.showError();
    }
  }
  
  showEmpty() {
    this.itemsContainer.innerHTML = `
      <p class="empty-state-small">No news articles found</p>
    `;
  }
  
  showError() {
    this.itemsContainer.innerHTML = `
      <p class="empty-state-small">Error loading news articles</p>
    `;
  }
  
  showLoading() {
    this.itemsContainer.innerHTML = `
      <div class="skeleton skeleton-title"></div>
      <div class="skeleton skeleton-text"></div>
      <div class="skeleton skeleton-text"></div>
    `;
  }
}