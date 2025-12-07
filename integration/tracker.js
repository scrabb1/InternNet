// --- Application Tracker Logic ---

// 1. Define Status Configuration
const STATUS_CONFIG = {
  "Planning to Apply": { class: "status-planning" },
  "Applied": { class: "status-applied" },
  "Interviewing": { class: "status-interviewing" },
  "Offer Received": { class: "status-offer" },
  "Not Selected": { class: "status-rejected" }
};

// 2. Placeholder Data (This will eventually come from your DB)
let myApplications = [
  { id: 1, internshipName: "Frontend Intern", organization: "Tech Corp", deadline: "2024-05-01", status: "Planning to Apply" },
  { id: 2, internshipName: "Data Analyst", organization: "Finance Inc", deadline: "2024-04-15", status: "Applied" }
];

// 3. Render Function
function renderTracker() {
  const tbody = document.getElementById('tracker-body');
  const emptyState = document.getElementById('tracker-empty-state');
  
  // Clear existing content
  tbody.innerHTML = '';

  if (myApplications.length === 0) {
    emptyState.style.display = 'block';
    return;
  }
  
  emptyState.style.display = 'none';

  myApplications.forEach(app => {
    const row = document.createElement('tr');
    
    // Create Select Element for Status
    const select = document.createElement('select');
    select.className = `status-select ${STATUS_CONFIG[app.status].class}`;
    
    // Populate Options
    Object.keys(STATUS_CONFIG).forEach(statusKey => {
      const option = document.createElement('option');
      option.value = statusKey;
      option.textContent = statusKey;
      if (app.status === statusKey) option.selected = true;
      select.appendChild(option);
    });

    // Handle Change Event
    select.addEventListener('change', (e) => {
      const newStatus = e.target.value;
      
      // Update Local State
      app.status = newStatus;
      
      // Update Visual Class immediately
      select.className = `status-select ${STATUS_CONFIG[newStatus].class}`;
      
      // TODO: Send update to backend
      console.log(`Updated App ID ${app.id} to status: ${newStatus}`);
      // updateApplicationStatusInDB(app.id, newStatus); 
    });

    // Build Row HTML
    row.innerHTML = `
      <td class="font-medium">${app.internshipName}</td>
      <td>${app.organization}</td>
      <td>${new Date(app.deadline).toLocaleDateString()}</td>
      <td></td> 
    `;
    
    // Append the select element to the last cell
    row.cells[3].appendChild(select);
    tbody.appendChild(row);
  });
}

// 4. Initialize (Call this when the user logs in)
// document.addEventListener('DOMContentLoaded', renderTracker); // Uncomment if you want to test immediately without login