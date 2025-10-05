import { formatCurrencyShort } from './utils.js';

export class MapController {
  constructor(config) {
    this.containerId = config.containerId;
    this.center = config.center;
    this.zoom = config.zoom;
    this.onProjectClick = config.onProjectClick;
    
    this.map = null;
    this.markers = [];
    this.markerClusterGroup = null;
    
    this.initialize();
  }
  
  initialize() {
    // Create map
    this.map = L.map(this.containerId, {
      zoomControl: false
    }).setView(this.center, this.zoom);
    
    // Add tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 19
    }).addTo(this.map);
    
    // Add zoom control to bottom right
    L.control.zoom({
      position: 'bottomright'
    }).addTo(this.map);
    
    // Initialize marker cluster group
    this.markerClusterGroup = L.markerClusterGroup({
      maxClusterRadius: 50,
      spiderfyOnMaxZoom: true,
      showCoverageOnHover: false,
      zoomToBoundsOnClick: true
    });
    
    this.map.addLayer(this.markerClusterGroup);
    
    // Setup controls
    this.setupControls();
  }
  
  setupControls() {
    const resetBtn = document.getElementById('resetView');
    if (resetBtn) {
      resetBtn.addEventListener('click', () => {
        this.map.setView(this.center, this.zoom);
      });
    }
  }
  
  updateProjects(projects) {
    // Clear existing markers
    this.clearMarkers();
    
    if (!projects || projects.length === 0) {
      return;
    }
    
    // Add new markers
    projects.forEach(project => {
      this.addProjectMarker(project);
    });
    
    // Update stats
    this.updateStats(projects);
  }
  
  addProjectMarker(project) {
    const lat = project.lat || project.latitude;
    const lon = project.lon || project.longitude;
    
    if (!lat || !lon) return;
    
    // Determine marker color based on status
    let markerColor = '#2563eb'; // Default blue
    
    // Create custom icon
    const icon = L.divIcon({
      className: 'custom-marker',
      html: `<div style="background: ${markerColor}; width: 24px; height: 24px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);"></div>`,
      iconSize: [24, 24],
      iconAnchor: [12, 12]
    });
    
    // Create marker
    const marker = L.marker([lat, lon], { icon });
    
    // Create popup content
    const popupContent = this.createPopupContent(project);
    marker.bindPopup(popupContent, {
      maxWidth: 300,
      className: 'custom-popup'
    });
    
    // Add click handler
    marker.on('click', () => {
      if (this.onProjectClick) {
        this.onProjectClick(project);
      }
    });
    
    // Add to cluster group
    this.markerClusterGroup.addLayer(marker);
    this.markers.push(marker);
  }
  
  createPopupContent(project) {
    const description = project.description || project.project_description || 'N/A';
    const contractor = project.contractor || 'N/A';
    const cost = project.contract_cost || project.ContractCost || 0;
    const municipality = project.municipality || project.Municipality || 'N/A';
    const province = project.province || project.Province || 'N/A';
    
    return `
      <div class="popup-content">
        <div class="popup-title">${description}</div>
        <div class="popup-detail">
          <span class="popup-label">Budget</span>
          <span class="popup-value">${formatCurrencyShort(cost)}</span>
        </div>
        <div class="popup-detail">
          <span class="popup-label">Location</span>
          <span class="popup-value">${municipality}, ${province}</span>
        </div>
        <div class="popup-contractor">${contractor}</div>
      </div>
    `;
  }
  
  clearMarkers() {
    this.markerClusterGroup.clearLayers();
    this.markers = [];
  }
  
  fitBounds(bbox, options = {}) {
    if (!bbox || bbox.length !== 2) return;
    
    try {
      // bbox format: [[min_lon, min_lat], [max_lon, max_lat]]
      const bounds = [
        [bbox[0][1], bbox[0][0]], // [min_lat, min_lon]
        [bbox[1][1], bbox[1][0]]  // [max_lat, max_lon]
      ];
      
      // Default options for snappy, smooth animation
      const defaultOptions = {
        padding: [50, 50],
        maxZoom: 12,
        animate: true,
        duration: 0.8,  // Fast, snappy
        easeLinearity: 0.25  // Smooth easing
      };
      
      this.map.fitBounds(bounds, { ...defaultOptions, ...options });
    } catch (error) {
      console.error('Error fitting bounds:', error);
    }
  }
  
  updateStats(projects) {
    const countElement = document.getElementById('projectCount');
    const budgetElement = document.getElementById('totalBudget');
    
    if (countElement) {
      countElement.textContent = projects.length.toLocaleString();
    }
    
    if (budgetElement) {
      const totalBudget = projects.reduce((sum, p) => {
        const cost = p.contract_cost || p.ContractCost || 0;
        return sum + Number(cost);
      }, 0);
      
      budgetElement.textContent = formatCurrencyShort(totalBudget);
    }
  }
}