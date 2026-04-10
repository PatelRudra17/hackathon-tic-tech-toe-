Challenge Requirements — Simple Explanation 🎯

Requirement 1: Multi-Format Resume Parsing Agent
Simple meaning: Build an AI that can READ resumes
Resume (PDF / DOCX / Text)
        ↓
AI reads and extracts:
  ✅ Name, Email, Phone
  ✅ Work Experience
  ✅ Education
  ✅ Skills
  ✅ Certifications
  ✅ Projects
Real Example:

Upload any resume → AI automatically fills a structured form with all details


Requirement 2: Skill Taxonomy and Normalization Agent
Simple meaning: Build an AI that understands skill synonyms and categories
Resume says "JS"     → System knows → "JavaScript"
Resume says "K8s"    → System knows → "Kubernetes"
Resume says "ML"     → System knows → "Machine Learning"

Also creates hierarchy:
Python
  └── Programming Languages
        └── Technical Skills
Real Example:

Candidate writes "ReactJS" and job needs "React.js" → AI knows they are the SAME skill ✅


Requirement 3: Semantic Skill-to-Job Matching Agent
Simple meaning: Build an AI that smartly matches candidates to jobs
Candidate Skills:  Python, ML, TensorFlow
Job Requirements:  Python (Required), Deep Learning (Required)
        ↓
AI thinks:
  ✅ Python → Direct match
  ✅ TensorFlow → implies Deep Learning → Smart match
  ❌ Missing: Cloud experience → Gap detected
        ↓
Match Score: 78%
Real Example:

Not just keyword search — AI understands meaning and gives a compatibility score


Requirement 4: Multi-Agent Orchestration Layer
Simple meaning: Build a manager/coordinator that controls all 3 agents above
You upload resume
        ↓
ORCHESTRATOR (Manager Agent)
    ↓           ↓           ↓
Agent 1     Agent 2     Agent 3
(Parse)   (Normalize)  (Match)
    ↓           ↓           ↓
ORCHESTRATOR collects all results
        ↓
Final Output to User
Extra features:

If Agent 1 crashes → other agents still work
Can process 100 resumes at the same time
Tracks how long each agent takes


Requirement 5: API Layer for Third-Party Consumption
Simple meaning: Build REST APIs so other apps can use your system
POST /api/v1/parse          → Upload 1 resume
POST /api/v1/parse/batch    → Upload 100 resumes at once
GET  /api/v1/candidates/    → Get candidate skill profile
POST /api/v1/match          → Match candidate to a job
GET  /api/v1/skills/taxonomy → Browse skill categories
Real Example:

LinkedIn or Naukri can connect to YOUR system using these APIs to parse resumes automatically


Overall Picture 🖼️
RESUME IN
    ↓
[Agent 1] Parse Resume
    ↓
[Agent 2] Normalize Skills
    ↓
[Agent 3] Match to Job
    ↓
[Orchestrator] Manages everything
    ↓
[API] Other apps can use it
    ↓
RESULT OUT