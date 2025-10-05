import { formatCurrency, formatDate } from './utils.js';

export class ProjectRenderer {
  constructor(config) {
    this.containerId = config.containerId;
    this.container = document.getElementById(this.containerId);
  }
  
  render(project) {
    if (!project) {
      this.showEmpty();
      return;
    }
    
    const html = this.createProjectCard(project);
    this.container.innerHTML = html;
    
    // Animate in
    this.container.classList.add('fade-in');
  }
  
  createProjectCard(project) {
    const description = project.project_description || project.description || 'N/A';
    const contractor = project.contractor || 'N/A';
    const contractCost = project.contract_cost || project.ContractCost || 0;
    const abc = project.abc || project.ABC || 0;
    const municipality = project.municipality || project.Municipality || 'N/A';
    const province = project.province || project.Province || 'N/A';
    const region = project.region || project.Region || 'N/A';
    const typeOfWork = project.type_of_work || project.TypeofWork || 'N/A';
    const infraYear = project.infra_year || project.InfraYear || 'N/A';
    const startDate = project.start_date || project.StartDate;
    const completionDate = project.completion_date_actual || project.CompletionDateActual;
    
    // Determine status
    let status = 'ongoing';
    let statusText = 'Ongoing';
    
    if (completionDate) {
      const compDate = new Date(completionDate);
      const now = new Date();
      if (compDate < now) {
        status = 'completed';
        statusText = 'Completed';
      }
    }
    
    return `
      <div class="project-header">
        <h2 class="project-title">${description}</h2>
        <div class="project-badges">
          <span class="badge contractor">${contractor}</span>
          <span class="badge status ${status}">${statusText}</span>
        </div>
      </div>
      
      <div class="project-details">
        <div class="detail-row">
          <span class="detail-label">Contract Cost</span>
          <span class="detail-value budget">${formatCurrency(contractCost)}</span>
        </div>
        
        <div class="detail-row">
          <span class="detail-label">ABC</span>
          <span class="detail-value">${formatCurrency(abc)}</span>
        </div>
        
        <div class="detail-row">
          <span class="detail-label">Location</span>
          <span class="detail-value location">${municipality}<br>${province}<br>${region}</span>
        </div>
        
        <div class="detail-row">
          <span class="detail-label">Type of Work</span>
          <span class="detail-value">${typeOfWork}</span>
        </div>
        
        <div class="detail-row">
          <span class="detail-label">Year</span>
          <span class="detail-value">${infraYear}</span>
        </div>
      </div>
      
      ${startDate || completionDate ? `
        <div class="project-timeline">
          <div class="timeline-title">Timeline</div>
          <div class="timeline-dates">
            <div class="timeline-date">
              <span class="timeline-date-label">Start</span>
              <span class="timeline-date-value">${formatDate(startDate)}</span>
            </div>
            <span class="timeline-arrow">→</span>
            <div class="timeline-date">
              <span class="timeline-date-label">Completion</span>
              <span class="timeline-date-value">${formatDate(completionDate)}</span>
            </div>
          </div>
        </div>
      ` : ''}
    `;
  }
  
  showEmpty() {
    this.container.innerHTML = `
      <p class="empty-state">
        Click a project on the map or ask a question to see details
      </p>
    `;
  }
  
  showLoading() {
    this.container.innerHTML = `
      <div class="skeleton skeleton-title"></div>
      <div class="skeleton skeleton-text"></div>
      <div class="skeleton skeleton-text"></div>
      <div class="skeleton skeleton-text"></div>
    `;
  }
}