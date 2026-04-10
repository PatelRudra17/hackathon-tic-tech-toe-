// ═══════════════════════════════════════════════
//  Talent Intelligence — Frontend Application
// ═══════════════════════════════════════════════

const API_BASE = '';
const API_KEY = 'dev-api-key-change-in-production';

// State
let candidates = [];
let matchCount = 0;
let searchTimeout = null;

// ─── Tab Navigation ───
document.querySelectorAll('.nav-tab').forEach(tab => {
  tab.addEventListener('click', () => switchTab(tab.dataset.tab));
});

function switchTab(tabId) {
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));

  const tab = document.querySelector(`.nav-tab[data-tab="${tabId}"]`);
  const content = document.getElementById(`tab-${tabId}`);
  if (tab) tab.classList.add('active');
  if (content) content.classList.add('active');

  // Load data when switching tabs
  if (tabId === 'taxonomy') loadTaxonomy();
  if (tabId === 'candidates') renderCandidates();
}

// ─── File Upload Handling (Multiple Files) ───
const fileInput = document.getElementById('fileInput');
const uploadZone = document.getElementById('uploadZone');

fileInput.addEventListener('change', (e) => {
  if (e.target.files.length > 0) showSelectedFiles(e.target.files);
});

uploadZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  uploadZone.classList.add('drag-over');
});

uploadZone.addEventListener('dragleave', () => {
  uploadZone.classList.remove('drag-over');
});

uploadZone.addEventListener('drop', (e) => {
  e.preventDefault();
  uploadZone.classList.remove('drag-over');
  if (e.dataTransfer.files.length > 0) {
    fileInput.files = e.dataTransfer.files;
    showSelectedFiles(e.dataTransfer.files);
  }
});

function showSelectedFiles(files) {
  document.getElementById('selectedFile').style.display = 'block';

  const count = files.length;
  const fileListEl = document.getElementById('fileList');

  if (count === 1) {
    const f = files[0];
    fileListEl.innerHTML = '';
    document.getElementById('fileName').textContent =
      `${f.name} (${(f.size / 1024).toFixed(1)} KB)`;
    document.getElementById('parseBtn').textContent = 'Parse Resume';
  } else {
    // Show list of files
    let listHtml = `<div style="font-weight:600; margin-bottom:0.4rem;">${count} files selected:</div>`;
    listHtml += '<div style="max-height:150px; overflow-y:auto; font-size:0.85rem;">';
    for (let i = 0; i < files.length; i++) {
      const f = files[i];
      listHtml += `<div style="display:flex; justify-content:space-between; padding:0.2rem 0; border-bottom:1px solid var(--border);">
        <span>${f.name}</span>
        <span style="color:var(--text-muted);">${(f.size / 1024).toFixed(1)} KB</span>
      </div>`;
    }
    listHtml += '</div>';
    fileListEl.innerHTML = listHtml;

    const totalSize = Array.from(files).reduce((a, f) => a + f.size, 0);
    document.getElementById('fileName').textContent =
      `${count} files (${(totalSize / 1024).toFixed(1)} KB total)`;
    document.getElementById('parseBtn').textContent = `Parse ${count} Resumes`;
  }
}

function clearFiles() {
  fileInput.value = '';
  document.getElementById('selectedFile').style.display = 'none';
  document.getElementById('fileList').innerHTML = '';
  document.getElementById('fileName').textContent = '';
}

// ─── Parse Resume(s) ───
async function parseResume() {
  const files = fileInput.files;
  if (!files || files.length === 0) return showToast('Please select file(s) first', 'error');

  if (files.length === 1) {
    // Single file — use /demo/parse
    await parseSingleFile(files[0]);
  } else {
    // Multiple files — use batch endpoint
    await parseBatchFiles(files);
  }
}

async function parseSingleFile(file) {
  const formData = new FormData();
  formData.append('file', file);

  showLoading('Parsing resume with AI agents...');

  try {
    const res = await fetch(`${API_BASE}/demo/parse`, { method: 'POST', body: formData });
    const data = await res.json();
    hideLoading();

    if (data.status === 'success') {
      candidates.push({
        id: data.candidate_id,
        name: data.name,
        email: data.email,
        phone: data.phone,
        skills: data.skills,
        work_experiences: data.work_experiences,
        educations: data.educations,
        certifications: data.certifications,
        publications: data.publications || 0,
        processing_time_ms: data.processing_time_ms
      });
      updateStats();
      displayParseResults(data);
      showToast(`Resume parsed successfully in ${data.processing_time_ms.toFixed(0)}ms`, 'success');
    } else {
      showToast('Parsing failed: ' + (data.message || 'Unknown error'), 'error');
    }
  } catch (err) {
    hideLoading();
    showToast('Error: ' + err.message, 'error');
  }
}

async function parseBatchFiles(files) {
  const count = files.length;
  showLoading(`Uploading ${count} resumes for batch processing...`);

  // Show batch progress panel
  const batchEl = document.getElementById('batchProgress');
  const batchContent = document.getElementById('batchProgressContent');
  batchEl.style.display = 'block';
  document.getElementById('parseEmpty').style.display = 'none';

  batchContent.innerHTML = `
    <div style="text-align:center; padding:1rem;">
      <div class="spinner"></div>
      <p style="margin-top:0.5rem; color:var(--text-secondary);">
        Uploading ${count} resumes...
      </p>
    </div>
  `;

  try {
    // Step 1: Upload all files to batch endpoint
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }

    const uploadRes = await fetch(`${API_BASE}/api/v1/parse/batch`, {
      method: 'POST',
      headers: { 'X-API-Key': API_KEY },
      body: formData,
    });
    const uploadData = await uploadRes.json();

    if (!uploadData.batch_id) {
      hideLoading();
      showToast('Batch upload failed: ' + JSON.stringify(uploadData), 'error');
      return;
    }

    const batchId = uploadData.batch_id;

    batchContent.innerHTML = `
      <div style="padding:0.5rem;">
        <div style="display:flex; justify-content:space-between; margin-bottom:0.5rem;">
          <span style="font-weight:600;">Batch ID:</span>
          <code style="font-size:0.8rem;">${batchId.substring(0, 12)}...</code>
        </div>
        <div style="display:flex; justify-content:space-between; margin-bottom:0.5rem;">
          <span>Total files:</span>
          <span style="font-weight:600;">${count}</span>
        </div>
        <div id="batchStatusLine" style="display:flex; justify-content:space-between; margin-bottom:0.8rem;">
          <span>Status:</span>
          <span style="color:var(--warning); font-weight:600;">Processing...</span>
        </div>
        <div style="background:var(--bg); border-radius:8px; height:8px; overflow:hidden;">
          <div id="batchBar" style="height:100%; background:var(--primary); width:10%; transition:width 0.5s;"></div>
        </div>
        <div id="batchFileResults" style="margin-top:1rem;"></div>
      </div>
    `;

    document.getElementById('loadingText').textContent = 'Batch processing in progress...';

    // Step 2: Poll for completion
    let completed = false;
    let attempts = 0;
    const maxAttempts = 60; // 60 seconds max

    while (!completed && attempts < maxAttempts) {
      await sleep(1000);
      attempts++;

      try {
        const statusRes = await fetch(`${API_BASE}/api/v1/parse/batch/${batchId}`, {
          headers: { 'X-API-Key': API_KEY },
        });
        const statusData = await statusRes.json();

        const processed = statusData.processed_files || 0;
        const failed = statusData.failed_files || 0;
        const total = statusData.total_files || count;
        const done = processed + failed;
        const pct = Math.round((done / total) * 100);

        // Update progress bar
        document.getElementById('batchBar').style.width = pct + '%';

        if (statusData.status === 'completed') {
          completed = true;
          hideLoading();

          // Update status line
          document.getElementById('batchStatusLine').innerHTML = `
            <span>Status:</span>
            <span style="color:var(--success); font-weight:600;">Completed!</span>
          `;
          document.getElementById('batchBar').style.width = '100%';
          document.getElementById('batchBar').style.background = 'var(--success)';

          // Display results
          displayBatchResults(statusData);

          const msg = `Batch complete: ${processed} parsed, ${failed} failed`;
          showToast(msg, failed > 0 ? 'warning' : 'success');
        }
      } catch (pollErr) {
        // Polling error — keep trying
      }
    }

    if (!completed) {
      hideLoading();
      showToast('Batch processing timed out. Check status later.', 'warning');
    }
  } catch (err) {
    hideLoading();
    showToast('Batch upload error: ' + err.message, 'error');
    batchContent.innerHTML = `
      <div style="color:var(--danger); padding:1rem;">
        Error: ${err.message}
      </div>
    `;
  }
}

function displayBatchResults(statusData) {
  const resultsEl = document.getElementById('batchFileResults');
  const results = statusData.results || [];
  const errors = statusData.error_log || [];

  // Add successful candidates to local state
  for (const r of results) {
    if (r.status === 'success') {
      candidates.push({
        id: r.candidate_id,
        name: r.name || 'Unknown',
        email: null,
        phone: null,
        skills: [],
        work_experiences: 0,
        educations: 0,
        certifications: 0,
        publications: 0,
        processing_time_ms: 0,
        fromBatch: true,
      });
    }
  }
  updateStats();

  let html = '';

  // Success results
  if (results.length > 0) {
    html += `<div style="font-weight:600; margin-bottom:0.4rem; color:var(--success);">
      Parsed Successfully (${results.length}):
    </div>`;
    html += '<div style="max-height:250px; overflow-y:auto;">';
    for (const r of results) {
      html += `
        <div style="display:flex; justify-content:space-between; align-items:center;
                    padding:0.5rem; margin-bottom:0.3rem; background:var(--bg);
                    border-radius:6px; border-left:3px solid var(--success);">
          <div>
            <strong>${r.name || 'Unknown'}</strong>
            <span style="color:var(--text-muted); font-size:0.8rem; margin-left:0.5rem;">${r.filename}</span>
          </div>
          <code style="font-size:0.7rem; color:var(--text-muted);">${r.candidate_id.substring(0, 8)}...</code>
        </div>
      `;
    }
    html += '</div>';
  }

  // Error results
  if (errors.length > 0) {
    html += `<div style="font-weight:600; margin-top:0.8rem; margin-bottom:0.4rem; color:var(--danger);">
      Failed (${errors.length}):
    </div>`;
    for (const e of errors) {
      html += `
        <div style="padding:0.5rem; margin-bottom:0.3rem; background:var(--bg);
                    border-radius:6px; border-left:3px solid var(--danger); font-size:0.85rem;">
          ${e.filename || 'Unknown file'}: ${e.error || 'Processing failed'}
        </div>
      `;
    }
  }

  // Summary stats
  html += `
    <div style="margin-top:1rem; padding:0.8rem; background:var(--bg); border-radius:8px;
                display:flex; justify-content:space-around; text-align:center;">
      <div>
        <div style="font-size:1.3rem; font-weight:700; color:var(--success);">${results.length}</div>
        <div style="font-size:0.75rem; color:var(--text-muted);">Parsed</div>
      </div>
      <div>
        <div style="font-size:1.3rem; font-weight:700; color:var(--danger);">${errors.length}</div>
        <div style="font-size:0.75rem; color:var(--text-muted);">Failed</div>
      </div>
      <div>
        <div style="font-size:1.3rem; font-weight:700; color:var(--primary-light);">${statusData.total_files}</div>
        <div style="font-size:0.75rem; color:var(--text-muted);">Total</div>
      </div>
    </div>
  `;

  resultsEl.innerHTML = html;

  // Also show the parse results panel with the last successful candidate
  if (results.length > 0) {
    document.getElementById('parseResults').style.display = 'block';
    document.getElementById('parseResultContent').innerHTML = `
      <div class="result-section">
        <h4>Batch Parse Summary</h4>
        <p style="color:var(--text-secondary);">
          ${results.length} resume(s) parsed successfully from batch.
          Switch to the <strong>Candidates</strong> tab to see all parsed candidates,
          or use the <strong>Job Matching</strong> tab to match them against jobs.
        </p>
        <div style="margin-top:0.8rem; display:flex; gap:0.5rem;">
          <button class="btn btn-primary" onclick="switchTab('candidates')">View Candidates</button>
          <button class="btn btn-secondary" onclick="switchTab('match')">Match Against Job</button>
        </div>
      </div>
    `;
  }
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function parseSample(filename) {
  showLoading('Loading sample resume...');

  try {
    // Fetch sample file
    const fileRes = await fetch(`${API_BASE}/static/samples/${filename}`);
    const blob = await fileRes.blob();
    const file = new File([blob], filename, { type: 'text/plain' });

    const formData = new FormData();
    formData.append('file', file);

    document.getElementById('loadingText').textContent = 'Parsing with AI agents...';

    const res = await fetch(`${API_BASE}/demo/parse`, { method: 'POST', body: formData });
    const data = await res.json();
    hideLoading();

    if (data.status === 'success') {
      candidates.push({
        id: data.candidate_id,
        name: data.name,
        email: data.email,
        phone: data.phone,
        skills: data.skills,
        work_experiences: data.work_experiences,
        educations: data.educations,
        certifications: data.certifications,
        publications: data.publications || 0,
        processing_time_ms: data.processing_time_ms
      });
      updateStats();
      displayParseResults(data);
      showToast(`Parsed "${data.name}" in ${data.processing_time_ms.toFixed(0)}ms`, 'success');
    } else {
      showToast('Parsing failed', 'error');
    }
  } catch (err) {
    hideLoading();
    showToast('Error: ' + err.message, 'error');
  }
}

function displayParseResults(data) {
  document.getElementById('parseEmpty').style.display = 'none';
  document.getElementById('parseResults').style.display = 'block';

  const skillTags = (data.skills || []).map(s => {
    const cat = s.category || 'Other';
    return `<span class="skill-tag default" title="${cat}">${s.name}</span>`;
  }).join('');

  document.getElementById('parseResultContent').innerHTML = `
    <div class="result-section">
      <h4>Personal Information</h4>
      <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.5rem; font-size:0.9rem;">
        <div><strong>Name:</strong> ${data.name || 'N/A'}</div>
        <div><strong>Email:</strong> ${data.email || 'N/A'}</div>
        <div><strong>Phone:</strong> ${data.phone || 'N/A'}</div>
        <div><strong>ID:</strong> <code style="font-size:0.75rem;">${data.candidate_id.substring(0, 8)}...</code></div>
      </div>
    </div>

    <div class="result-section">
      <h4>Skills Extracted (${data.skills ? data.skills.length : 0})</h4>
      <div class="skill-tags">${skillTags || '<span style="color:var(--text-muted)">No skills found</span>'}</div>
    </div>

    <div class="result-section">
      <h4>Summary</h4>
      <div class="grid-3" style="gap:0.5rem;">
        <div class="stat-card">
          <div class="stat-value" style="font-size:1.5rem;">${data.work_experiences || 0}</div>
          <div class="stat-label">Work Experiences</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" style="font-size:1.5rem;">${data.educations || 0}</div>
          <div class="stat-label">Education</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" style="font-size:1.5rem;">${data.certifications || 0}</div>
          <div class="stat-label">Certifications</div>
        </div>
      </div>
    </div>

    <div style="text-align:right; margin-top:1rem; color:var(--text-muted); font-size:0.8rem;">
      Processed in ${data.processing_time_ms.toFixed(1)}ms
    </div>
  `;
}

// ─── Job Matching ───
const JOB_TEMPLATES = {
  swe: {
    title: 'Senior Software Engineer',
    required: 'Python, Docker, PostgreSQL, REST API, Git',
    preferred: 'Kubernetes, AWS, Redis, FastAPI, Terraform'
  },
  ds: {
    title: 'Data Scientist',
    required: 'Python, Machine Learning, SQL, Pandas, Statistics',
    preferred: 'Deep Learning, TensorFlow, Spark, Tableau, A/B Testing'
  },
  fe: {
    title: 'Frontend Developer',
    required: 'JavaScript, React, TypeScript, CSS, HTML',
    preferred: 'Next.js, Redux, GraphQL, Jest, Figma'
  },
  devops: {
    title: 'DevOps Engineer',
    required: 'Docker, Kubernetes, AWS, Linux, Terraform',
    preferred: 'Jenkins, Prometheus, Grafana, Ansible, Python'
  },
  ml: {
    title: 'ML Engineer',
    required: 'Python, Machine Learning, TensorFlow, Docker, SQL',
    preferred: 'PyTorch, Kubernetes, NLP, MLOps, Spark'
  }
};

function loadJobTemplate() {
  const key = document.getElementById('jobTemplate').value;
  if (!key) return;
  const tmpl = JOB_TEMPLATES[key];
  document.getElementById('jobTitle').value = tmpl.title;
  document.getElementById('requiredSkills').value = tmpl.required;
  document.getElementById('preferredSkills').value = tmpl.preferred;
}

async function runMatch() {
  const matchFile = document.getElementById('matchFileInput').files[0];
  if (!matchFile) return showToast('Please upload a resume file for matching', 'error');

  const title = document.getElementById('jobTitle').value;
  const required = document.getElementById('requiredSkills').value;
  const preferred = document.getElementById('preferredSkills').value;

  if (!title) return showToast('Please enter a job title', 'error');
  if (!required) return showToast('Please enter required skills', 'error');

  const formData = new FormData();
  formData.append('file', matchFile);

  const params = new URLSearchParams({
    job_title: title,
    required_skills: required,
    preferred_skills: preferred || ''
  });

  showLoading('Running multi-agent matching pipeline...');

  try {
    const res = await fetch(`${API_BASE}/demo/match?${params}`, { method: 'POST', body: formData });
    const data = await res.json();
    hideLoading();

    if (data.status === 'success') {
      matchCount++;
      updateStats();
      displayMatchResults(data);
      showToast(`Match complete: ${(data.overall_score * 100).toFixed(0)}% score`, 'success');
    } else {
      showToast('Matching failed: ' + (data.message || 'Unknown error'), 'error');
    }
  } catch (err) {
    hideLoading();
    showToast('Error: ' + err.message, 'error');
  }
}

async function matchSample(filename) {
  const title = document.getElementById('jobTitle').value;
  const required = document.getElementById('requiredSkills').value;

  if (!title || !required) {
    // Auto-select SWE template
    document.getElementById('jobTemplate').value = 'swe';
    loadJobTemplate();
  }

  showLoading('Loading sample & matching...');

  try {
    const fileRes = await fetch(`${API_BASE}/static/samples/${filename}`);
    const blob = await fileRes.blob();
    const file = new File([blob], filename, { type: 'text/plain' });

    const formData = new FormData();
    formData.append('file', file);

    const params = new URLSearchParams({
      job_title: document.getElementById('jobTitle').value,
      required_skills: document.getElementById('requiredSkills').value,
      preferred_skills: document.getElementById('preferredSkills').value || ''
    });

    const res = await fetch(`${API_BASE}/demo/match?${params}`, { method: 'POST', body: formData });
    const data = await res.json();
    hideLoading();

    if (data.status === 'success') {
      matchCount++;
      updateStats();
      displayMatchResults(data);
      showToast(`Match score: ${(data.overall_score * 100).toFixed(0)}%`, 'success');
    } else {
      showToast('Matching failed', 'error');
    }
  } catch (err) {
    hideLoading();
    showToast('Error: ' + err.message, 'error');
  }
}

function displayMatchResults(data) {
  document.getElementById('matchEmpty').style.display = 'none';
  document.getElementById('matchResults').style.display = 'block';

  const score = (data.overall_score * 100).toFixed(0);
  const skillScore = (data.skill_match_score * 100).toFixed(0);
  const expScore = (data.experience_score * 100).toFixed(0);

  let recClass = 'weak';
  if (score >= 85) recClass = 'strong';
  else if (score >= 70) recClass = 'good';
  else if (score >= 50) recClass = 'moderate';

  const scoreColor = score >= 85 ? '#10b981' : score >= 70 ? '#0ea5e9' : score >= 50 ? '#f59e0b' : '#ef4444';

  const matchedTags = (data.matched_skills || []).map(s =>
    `<span class="skill-tag matched" title="${s.type} match (${(s.confidence * 100).toFixed(0)}%)">${s.skill}</span>`
  ).join('');

  const missingTags = (data.missing_skills || []).map(s =>
    `<span class="skill-tag missing">${s}</span>`
  ).join('');

  document.getElementById('matchResultContent').innerHTML = `
    <div class="score-container">
      <div class="score-circle" style="--score:${score}; --score-color:${scoreColor};">
        <div class="score-value" style="color:${scoreColor}">${score}%</div>
        <div class="score-label">Overall Match</div>
      </div>
    </div>

    <div class="match-bar-container">
      <div class="match-bar-label">
        <span>Skill Match</span><span style="font-weight:600;">${skillScore}%</span>
      </div>
      <div class="match-bar">
        <div class="match-bar-fill" style="width:${skillScore}%; background:${scoreColor};"></div>
      </div>
    </div>

    <div class="match-bar-container">
      <div class="match-bar-label">
        <span>Experience</span><span style="font-weight:600;">${expScore}%</span>
      </div>
      <div class="match-bar">
        <div class="match-bar-fill" style="width:${expScore}%; background:var(--secondary);"></div>
      </div>
    </div>

    <div class="result-section" style="margin-top:1.5rem;">
      <h4>Matched Skills (${data.matched_skills ? data.matched_skills.length : 0})</h4>
      <div class="skill-tags">${matchedTags || '<span style="color:var(--text-muted)">None</span>'}</div>
    </div>

    <div class="result-section">
      <h4>Missing Skills (${data.missing_skills ? data.missing_skills.length : 0})</h4>
      <div class="skill-tags">${missingTags || '<span style="color:var(--success)">No gaps!</span>'}</div>
    </div>

    <div class="recommendation ${recClass}">
      ${data.recommendation}
    </div>

    <div style="text-align:right; margin-top:1rem; color:var(--text-muted); font-size:0.8rem;">
      Processed in ${data.processing_time_ms.toFixed(1)}ms
    </div>
  `;
}

// ─── Candidates List ───
function renderCandidates() {
  const container = document.getElementById('candidatesList');

  if (candidates.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">&#128101;</div>
        <p>No candidates yet. Parse some resumes first!</p>
      </div>
    `;
    return;
  }

  let rows = candidates.map((c, i) => `
    <tr>
      <td><strong>${c.name || 'N/A'}</strong></td>
      <td>${c.email || 'N/A'}</td>
      <td>${c.skills ? c.skills.length : 0} skills</td>
      <td>${c.work_experiences || 0} positions</td>
      <td><code style="font-size:0.75rem;">${c.id.substring(0, 8)}...</code></td>
      <td>${c.fromBatch ? 'batch' : (c.processing_time_ms || 0).toFixed(0) + 'ms'}</td>
    </tr>
  `).join('');

  container.innerHTML = `
    <p style="color:var(--text-muted); margin-bottom:0.8rem; font-size:0.9rem;">
      ${candidates.length} candidate(s) parsed in this session
    </p>
    <table class="data-table">
      <thead>
        <tr>
          <th>Name</th><th>Email</th><th>Skills</th><th>Experience</th><th>ID</th><th>Parse Time</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

// ─── Skill Taxonomy ───
let taxonomyLoaded = false;

async function loadTaxonomy() {
  if (taxonomyLoaded) return;

  try {
    const res = await fetch(`${API_BASE}/api/v1/skills/taxonomy`, {
      headers: { 'X-API-Key': API_KEY }
    });
    const data = await res.json();

    const container = document.getElementById('taxonomyTree');
    let html = '';

    for (const [topLevel, subcategories] of Object.entries(data.categories)) {
      html += `<div style="margin-bottom:1.5rem;">
        <h3 style="color:var(--primary-light); margin-bottom:0.8rem; font-size:1rem;">${topLevel}</h3>`;

      for (const [category, skills] of Object.entries(subcategories)) {
        const skillTags = skills.map(s =>
          `<span class="skill-tag default">${s}</span>`
        ).join('');

        html += `
          <div class="taxonomy-category">
            <div class="taxonomy-header" onclick="this.nextElementSibling.classList.toggle('open')">
              <span>${category}</span>
              <span style="color:var(--text-muted); font-size:0.8rem;">${skills.length} skills</span>
            </div>
            <div class="taxonomy-skills">
              <div class="skill-tags">${skillTags}</div>
            </div>
          </div>
        `;
      }
      html += '</div>';
    }

    container.innerHTML = html;
    document.getElementById('statSkills').textContent = data.total_skills;
    taxonomyLoaded = true;
  } catch (err) {
    document.getElementById('taxonomyTree').innerHTML =
      `<div class="empty-state"><p>Failed to load taxonomy: ${err.message}</p></div>`;
  }
}

async function searchSkills() {
  const query = document.getElementById('skillSearch').value.trim();
  if (!query) return;

  try {
    const res = await fetch(`${API_BASE}/api/v1/skills/search?q=${encodeURIComponent(query)}`, {
      headers: { 'X-API-Key': API_KEY }
    });
    const data = await res.json();
    const container = document.getElementById('searchResults');

    if (data.results.length === 0) {
      container.innerHTML = '<p style="color:var(--text-muted);">No skills found.</p>';
      return;
    }

    let html = '<div style="display:flex; flex-direction:column; gap:0.5rem;">';
    for (const skill of data.results) {
      const aliases = skill.aliases.length > 0
        ? `<span style="color:var(--text-muted); font-size:0.8rem;"> (also: ${skill.aliases.join(', ')})</span>`
        : '';
      const related = skill.related_skills.length > 0
        ? skill.related_skills.map(r => `<span class="skill-tag default" style="font-size:0.7rem; padding:0.15rem 0.5rem;">${r}</span>`).join('')
        : '';

      html += `
        <div style="padding:0.8rem; background:var(--bg); border-radius:8px;">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <strong>${skill.name}</strong>${aliases}
            <span style="color:var(--text-muted); font-size:0.8rem;">${skill.category} | ${skill.skill_type}</span>
          </div>
          ${related ? `<div style="margin-top:0.5rem; display:flex; gap:4px; flex-wrap:wrap;">${related}</div>` : ''}
        </div>
      `;
    }
    html += '</div>';
    container.innerHTML = html;
  } catch (err) {
    document.getElementById('searchResults').innerHTML = `<p style="color:var(--danger);">Error: ${err.message}</p>`;
  }
}

function debounceSearch() {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(searchSkills, 300);
}

// ─── Utility Functions ───
function showLoading(text) {
  document.getElementById('loadingText').textContent = text || 'Processing...';
  document.getElementById('loadingOverlay').classList.add('active');
}

function hideLoading() {
  document.getElementById('loadingOverlay').classList.remove('active');
}

function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

function updateStats() {
  document.getElementById('statCandidates').textContent = candidates.length;
  document.getElementById('statMatches').textContent = matchCount;
}

// ─── Initialize ───
async function init() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    const data = await res.json();
    document.getElementById('serverStatus').textContent =
      `System Online | ${data.services.skill_taxonomy.total_skills} Skills | ${data.services.orchestrator.engine || 'Custom'} Engine`;
    document.getElementById('statSkills').textContent = data.services.skill_taxonomy.total_skills;
  } catch (err) {
    document.getElementById('serverStatus').textContent = 'System Offline';
    document.querySelector('.status-dot').style.background = '#ef4444';
  }
}

init();
