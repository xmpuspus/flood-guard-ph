import { ChatManager } from './chat.js';
import { MapController } from './map.js';
import { ProjectRenderer } from './project.js';
import { NewsManager } from './news.js';
import { APIKeyManager } from './api-keys.js';

class FloodGuardApp {
  constructor() {
    this.currentProjects = [];
    
    // Initialize API key manager
    this.apiKeyManager = new APIKeyManager();
    
    // Determine WebSocket URL
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/api/chat`;
    
    // Initialize managers
    this.chat = new ChatManager({
      wsUrl: wsUrl,
      onMessage: this.handleChatMessage.bind(this)
    });
    
    this.map = new MapController({
      containerId: 'map',
      center: [12.8797, 121.7740], // Philippines center
      zoom: 6,
      onProjectClick: this.handleProjectClick.bind(this)
    });
    
    this.projectRenderer = new ProjectRenderer({
      containerId: 'projectCard'
    });
    
    this.news = new NewsManager({
      containerId: 'newsFeed'
    });
    
    // Load initial projects
    this.loadInitialProjects();
    
    // Hide loading overlay
    this.hideLoading();
  }
  
  async loadInitialProjects() {
    try {
      // Load all projects to show on map (marker clustering handles performance)
      const response = await fetch('/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filters: {},
          limit: 10000  // Load all projects - clustering handles performance
        })
      });
      
      const data = await response.json();
      
      if (data.projects && data.projects.length > 0) {
        this.currentProjects = data.projects;
        this.map.updateProjects(this.currentProjects);
        
        // Update stats with actual database totals
        const countElement = document.getElementById('projectCount');
        const budgetElement = document.getElementById('totalBudget');
        
        if (countElement) {
          // Show actual total from database, not just rendered count
          const totalCount = data.total || data.projects.length;
          countElement.textContent = totalCount.toLocaleString();
        }
        
        if (budgetElement && data.stats) {
          const totalBudget = data.stats.total_budget;
          budgetElement.textContent = this.formatBudgetShort(totalBudget);
        }
        
        console.log(`Loaded ${data.projects.length} projects on map. Total in database: ${data.total || data.projects.length}`);
      }
    } catch (error) {
      console.error('Error loading initial projects:', error);
    }
  }
  
  formatBudgetShort(amount) {
    if (!amount) return '₱0';
    const num = Number(amount);
    if (num >= 1000000000) {
      return '₱' + (num / 1000000000).toFixed(1) + 'B';
    } else if (num >= 1000000) {
      return '₱' + (num / 1000000).toFixed(1) + 'M';
    }
    return '₱' + num.toLocaleString('en-PH');
  }
  
  handleChatMessage(message) {
    switch (message.type) {
      case 'projects':
        // Clear previous query results first for fresh view
        this.currentProjects = message.data || [];
        
        // Update map with new projects (replaces old markers)
        this.map.clearMarkers();
        this.map.updateProjects(this.currentProjects);
        
        // Auto-pan to new results immediately
        if (this.currentProjects.length > 0) {
          // Calculate bounds from projects
          const bounds = this.calculateBounds(this.currentProjects);
          this.map.fitBounds(bounds, { 
            padding: [50, 50],
            maxZoom: 12,
            animate: true,
            duration: 0.8  // Fast, snappy animation
          });
          
          // Show first project
          this.projectRenderer.render(this.currentProjects[0]);
        }
        break;
        
      case 'map_bounds':
        // Explicit bounds from backend (fallback)
        if (message.bbox) {
          this.map.fitBounds(message.bbox, {
            padding: [50, 50],
            maxZoom: 12,
            animate: true,
            duration: 0.8
          });
        }
        break;
        
      case 'news':
        if (message.data) {
          this.news.render(message.data);
        }
        break;
    }
  }
  
  calculateBounds(projects) {
    if (!projects || projects.length === 0) {
      return [[121.0, 12.0], [122.0, 13.0]]; // Default Philippines
    }
    
    const lats = projects.map(p => p.lat || p.latitude).filter(Boolean);
    const lons = projects.map(p => p.lon || p.longitude).filter(Boolean);
    
    if (lats.length === 0 || lons.length === 0) {
      return [[121.0, 12.0], [122.0, 13.0]];
    }
    
    const padding = 0.1;
    return [
      [Math.min(...lons) - padding, Math.min(...lats) - padding],
      [Math.max(...lons) + padding, Math.max(...lats) + padding]
    ];
  }
  
  handleProjectClick(project) {
    // Render project details
    this.projectRenderer.render(project);
    
    // Fetch related news using full project details for web search
    this.news.showLoading();
    this.news.fetchForProject(project);
    
    // Highlight on mobile
    if (window.innerWidth <= 1024) {
      const detailsPanel = document.querySelector('.details-panel');
      if (detailsPanel) {
        detailsPanel.classList.add('active');
        
        // Add close button if not exists
        if (!detailsPanel.querySelector('.close-btn')) {
          const closeBtn = document.createElement('button');
          closeBtn.className = 'control-btn close-btn';
          closeBtn.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          `;
          closeBtn.style.position = 'absolute';
          closeBtn.style.top = '16px';
          closeBtn.style.right = '16px';
          closeBtn.style.zIndex = '1000';
          
          closeBtn.addEventListener('click', () => {
            detailsPanel.classList.remove('active');
          });
          
          detailsPanel.appendChild(closeBtn);
        }
      }
    }
  }
  
  hideLoading() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) {
      setTimeout(() => {
        loadingOverlay.classList.add('hidden');
      }, 500);
    }
  }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.app = new FloodGuardApp();
  console.log('FloodGuard PH initialized');
});