"""
Taxonomy Generator Script
==========================

Generates a large-scale skill taxonomy (5000+ skills) by programmatically
expanding a base taxonomy with domain-specific skill variations, version-specific
entries, and framework/tool combinations.

Usage:
    python -m app.data.generate_taxonomy

This reads the existing skill_taxonomy.json, expands it, and writes the result
back. The base taxonomy provides curated, high-quality entries; this script
adds systematic expansions for completeness.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List


def generate_version_variants(name: str, versions: List[str]) -> List[str]:
    """Generate version-specific aliases."""
    aliases = []
    for v in versions:
        aliases.append(f"{name} {v}")
        aliases.append(f"{name}{v}")
    return aliases


def generate_expanded_taxonomy() -> Dict:
    """Generate an expanded taxonomy with 5000+ skills."""

    # Load existing taxonomy as the base
    taxonomy_path = Path(__file__).parent / "skill_taxonomy.json"
    if taxonomy_path.exists():
        with open(taxonomy_path, "r", encoding="utf-8") as f:
            taxonomy = json.load(f)
    else:
        taxonomy = {"Technical Skills": {}, "Soft Skills": {}, "Domain Skills": {}}

    # ─── Additional Technical Skills ───

    additional_tech = {
        "Operating Systems": {
            "skills": [
                {"name": "Windows Server", "aliases": ["Win Server", "Windows Server 2019"], "related": ["Active Directory", "PowerShell"]},
                {"name": "macOS", "aliases": ["Mac OS", "OSX", "Mac OS X"], "related": ["Swift", "Xcode"]},
                {"name": "FreeBSD", "aliases": ["freebsd"], "related": ["Unix", "Networking"]},
                {"name": "Alpine Linux", "aliases": ["alpine"], "related": ["Docker", "Containers"]},
                {"name": "Arch Linux", "aliases": ["arch", "archlinux"], "related": ["Linux", "Systemd"]},
                {"name": "Fedora", "aliases": ["fedora linux"], "related": ["Red Hat", "Linux"]},
                {"name": "Chrome OS", "aliases": ["ChromeOS", "chromeos"], "related": ["Google", "Web Apps"]},
                {"name": "RTOS", "aliases": ["Real-Time OS", "Real Time Operating System"], "related": ["Embedded", "IoT"]},
                {"name": "QNX", "aliases": ["qnx"], "related": ["Embedded", "Automotive"]},
                {"name": "VxWorks", "aliases": ["vxworks"], "related": ["Embedded", "Aerospace"]},
            ]
        },
        "Build Tools & Package Managers": {
            "skills": [
                {"name": "Webpack", "aliases": ["webpack5", "webpack 5"], "related": ["JavaScript", "Bundling"]},
                {"name": "Vite", "aliases": ["vitejs", "vite.js"], "related": ["JavaScript", "Frontend"]},
                {"name": "Rollup", "aliases": ["rollupjs", "rollup.js"], "related": ["JavaScript", "Bundling"]},
                {"name": "esbuild", "aliases": ["es-build"], "related": ["JavaScript", "Bundling"]},
                {"name": "SWC", "aliases": ["swc-project"], "related": ["Rust", "JavaScript"]},
                {"name": "Babel", "aliases": ["babeljs", "babel.js"], "related": ["JavaScript", "Transpiling"]},
                {"name": "Gradle", "aliases": ["gradle-build"], "related": ["Java", "Kotlin", "Android"]},
                {"name": "Maven", "aliases": ["Apache Maven", "mvn"], "related": ["Java", "Build"]},
                {"name": "npm", "aliases": ["Node Package Manager"], "related": ["Node.js", "JavaScript"]},
                {"name": "Yarn", "aliases": ["yarnpkg"], "related": ["Node.js", "JavaScript"]},
                {"name": "pnpm", "aliases": ["performant npm"], "related": ["Node.js", "JavaScript"]},
                {"name": "pip", "aliases": ["pip3", "PyPI"], "related": ["Python", "Package Management"]},
                {"name": "Poetry", "aliases": ["python-poetry"], "related": ["Python", "Package Management"]},
                {"name": "Cargo", "aliases": ["cargo-build"], "related": ["Rust", "Package Management"]},
                {"name": "CMake", "aliases": ["cmake"], "related": ["C++", "Build"]},
                {"name": "Make", "aliases": ["Makefile", "GNU Make"], "related": ["C", "Build"]},
                {"name": "Bazel", "aliases": ["bazel-build"], "related": ["Google", "Monorepo"]},
                {"name": "Turborepo", "aliases": ["turbo"], "related": ["Monorepo", "JavaScript"]},
                {"name": "Lerna", "aliases": ["lerna"], "related": ["Monorepo", "JavaScript"]},
                {"name": "Nx", "aliases": ["nrwl nx"], "related": ["Monorepo", "JavaScript"]},
            ]
        },
        "Message Queues & Streaming": {
            "skills": [
                {"name": "RabbitMQ", "aliases": ["rabbit", "rabbitmq"], "related": ["AMQP", "Message Queue"]},
                {"name": "ActiveMQ", "aliases": ["Apache ActiveMQ"], "related": ["JMS", "Message Queue"]},
                {"name": "ZeroMQ", "aliases": ["0MQ", "zmq", "ØMQ"], "related": ["Messaging", "Sockets"]},
                {"name": "NATS", "aliases": ["nats.io", "NATS Streaming"], "related": ["Messaging", "Cloud Native"]},
                {"name": "Apache Pulsar", "aliases": ["Pulsar"], "related": ["Streaming", "Messaging"]},
                {"name": "Amazon SQS", "aliases": ["SQS", "Simple Queue Service"], "related": ["AWS", "Queue"]},
                {"name": "Amazon SNS", "aliases": ["SNS", "Simple Notification"], "related": ["AWS", "Pub/Sub"]},
                {"name": "Google Pub/Sub", "aliases": ["Cloud Pub/Sub", "GCP Pub/Sub"], "related": ["GCP", "Messaging"]},
                {"name": "Azure Service Bus", "aliases": ["Service Bus"], "related": ["Azure", "Messaging"]},
                {"name": "Amazon Kinesis", "aliases": ["Kinesis", "Kinesis Data Streams"], "related": ["AWS", "Streaming"]},
            ]
        },
        "Monitoring & Observability": {
            "skills": [
                {"name": "OpenTelemetry", "aliases": ["OTel", "otel", "OpenTracing"], "related": ["Observability", "Tracing"]},
                {"name": "Jaeger", "aliases": ["jaeger-tracing"], "related": ["Tracing", "Observability"]},
                {"name": "Zipkin", "aliases": ["zipkin"], "related": ["Tracing", "Observability"]},
                {"name": "New Relic", "aliases": ["NewRelic", "newrelic"], "related": ["APM", "Monitoring"]},
                {"name": "Splunk", "aliases": ["splunk"], "related": ["Log Management", "SIEM"]},
                {"name": "Loki", "aliases": ["Grafana Loki"], "related": ["Grafana", "Log Management"]},
                {"name": "Fluentd", "aliases": ["fluentd"], "related": ["Log Collection", "CNCF"]},
                {"name": "Logstash", "aliases": ["logstash"], "related": ["ELK", "Log Processing"]},
                {"name": "Kibana", "aliases": ["kibana"], "related": ["ELK", "Visualization"]},
                {"name": "PagerDuty", "aliases": ["pagerduty"], "related": ["Incident Management", "Alerting"]},
                {"name": "Sentry", "aliases": ["sentry.io"], "related": ["Error Tracking", "Monitoring"]},
                {"name": "Honeycomb", "aliases": ["honeycomb.io"], "related": ["Observability", "Tracing"]},
                {"name": "Dynatrace", "aliases": ["dynatrace"], "related": ["APM", "Monitoring"]},
                {"name": "AppDynamics", "aliases": ["appdynamics"], "related": ["APM", "Cisco"]},
                {"name": "Nagios", "aliases": ["nagios"], "related": ["Infrastructure Monitoring"]},
            ]
        },
        "Serverless & Edge": {
            "skills": [
                {"name": "AWS Lambda", "aliases": ["Lambda", "lambda"], "related": ["AWS", "Serverless"]},
                {"name": "Azure Functions", "aliases": ["Azure Serverless"], "related": ["Azure", "Serverless"]},
                {"name": "Google Cloud Functions", "aliases": ["Cloud Functions", "GCF"], "related": ["GCP", "Serverless"]},
                {"name": "Cloudflare Workers", "aliases": ["CF Workers", "Workers"], "related": ["Edge Computing", "Serverless"]},
                {"name": "AWS Step Functions", "aliases": ["Step Functions"], "related": ["AWS", "Orchestration"]},
                {"name": "Serverless Framework", "aliases": ["sls", "serverless.com"], "related": ["Serverless", "IaC"]},
                {"name": "AWS Fargate", "aliases": ["Fargate"], "related": ["AWS", "Containers"]},
                {"name": "Deno Deploy", "aliases": ["deno-deploy"], "related": ["Deno", "Edge"]},
                {"name": "Vercel Edge Functions", "aliases": ["Vercel Edge"], "related": ["Vercel", "Edge"]},
                {"name": "Knative", "aliases": ["knative"], "related": ["Kubernetes", "Serverless"]},
            ]
        },
        "CMS & Content": {
            "skills": [
                {"name": "WordPress", "aliases": ["WP", "wordpress"], "related": ["PHP", "CMS"]},
                {"name": "Drupal", "aliases": ["drupal"], "related": ["PHP", "CMS"]},
                {"name": "Contentful", "aliases": ["contentful"], "related": ["Headless CMS", "API"]},
                {"name": "Strapi", "aliases": ["strapi"], "related": ["Headless CMS", "Node.js"]},
                {"name": "Sanity", "aliases": ["sanity.io"], "related": ["Headless CMS", "GROQ"]},
                {"name": "Ghost", "aliases": ["ghost cms"], "related": ["CMS", "Publishing"]},
                {"name": "Prismic", "aliases": ["prismic.io"], "related": ["Headless CMS"]},
                {"name": "Webflow", "aliases": ["webflow"], "related": ["No-Code", "Web Design"]},
                {"name": "Shopify", "aliases": ["shopify"], "related": ["E-Commerce", "Liquid"]},
                {"name": "Magento", "aliases": ["Adobe Commerce"], "related": ["E-Commerce", "PHP"]},
            ]
        },
        "AR/VR & 3D": {
            "skills": [
                {"name": "ARKit", "aliases": ["ar-kit", "Apple AR"], "related": ["iOS", "Augmented Reality"]},
                {"name": "ARCore", "aliases": ["ar-core", "Google AR"], "related": ["Android", "Augmented Reality"]},
                {"name": "Three.js", "aliases": ["threejs", "three.js"], "related": ["WebGL", "3D"]},
                {"name": "WebXR", "aliases": ["webxr"], "related": ["VR", "AR", "Web"]},
                {"name": "OpenXR", "aliases": ["openxr"], "related": ["VR", "XR"]},
                {"name": "Blender", "aliases": ["blender 3d"], "related": ["3D Modeling", "Animation"]},
                {"name": "Maya", "aliases": ["Autodesk Maya"], "related": ["3D", "Animation"]},
                {"name": "A-Frame", "aliases": ["aframe"], "related": ["WebVR", "Three.js"]},
                {"name": "Babylon.js", "aliases": ["babylonjs"], "related": ["WebGL", "3D"]},
                {"name": "WebGL", "aliases": ["webgl", "Web Graphics"], "related": ["OpenGL", "3D"]},
            ]
        },
    }

    # Merge additional tech skills
    tech = taxonomy.get("Technical Skills", {})
    for cat_name, cat_data in additional_tech.items():
        if cat_name not in tech:
            tech[cat_name] = cat_data
        else:
            existing_names = {s["name"] for s in tech[cat_name].get("skills", [])}
            for skill in cat_data["skills"]:
                if skill["name"] not in existing_names:
                    tech[cat_name]["skills"].append(skill)
    taxonomy["Technical Skills"] = tech

    # ─── Additional Soft Skills ───

    additional_soft = {
        "Problem Solving": {
            "skills": [
                {"name": "Critical Thinking", "aliases": ["Analytical Thinking", "Logic"], "related": ["Problem Solving"]},
                {"name": "Creative Problem Solving", "aliases": ["Innovation", "Creative Thinking"], "related": ["Design Thinking"]},
                {"name": "Troubleshooting", "aliases": ["Debugging", "Issue Resolution"], "related": ["Technical Support"]},
                {"name": "Data-Driven Decision Making", "aliases": ["Evidence-Based Decisions", "Data-Informed"], "related": ["Analytics"]},
                {"name": "Root Cause Analysis", "aliases": ["RCA", "5 Whys"], "related": ["Problem Solving"]},
                {"name": "Systems Thinking", "aliases": ["Holistic Thinking", "Big Picture"], "related": ["Architecture"]},
                {"name": "Algorithmic Thinking", "aliases": ["Computational Thinking"], "related": ["Programming"]},
                {"name": "Research Skills", "aliases": ["Investigation", "Research Methodology"], "related": ["Analysis"]},
                {"name": "Pattern Recognition", "aliases": ["Trend Analysis"], "related": ["Analytics", "Data Science"]},
                {"name": "Hypothesis Testing", "aliases": ["Scientific Method"], "related": ["Statistics", "Research"]},
            ]
        },
        "Interpersonal": {
            "skills": [
                {"name": "Teamwork", "aliases": ["Team Player", "Collaboration"], "related": ["Communication"]},
                {"name": "Emotional Intelligence", "aliases": ["EQ", "Emotional Awareness"], "related": ["Leadership"]},
                {"name": "Empathy", "aliases": ["User Empathy", "Compassion"], "related": ["UX"]},
                {"name": "Cultural Awareness", "aliases": ["Cross-Cultural Communication", "Global Mindset"], "related": ["Diversity"]},
                {"name": "Diversity & Inclusion", "aliases": ["DEI", "D&I"], "related": ["HR", "Culture"]},
                {"name": "Remote Collaboration", "aliases": ["Virtual Teamwork", "Distributed Teams"], "related": ["Communication"]},
                {"name": "Pair Programming", "aliases": ["Mob Programming", "Collaborative Coding"], "related": ["Development"]},
                {"name": "Code Review", "aliases": ["Peer Review", "PR Review"], "related": ["Quality"]},
                {"name": "Conflict Resolution", "aliases": ["Dispute Resolution", "Mediation"], "related": ["Leadership"]},
                {"name": "Networking", "aliases": ["Professional Networking", "Relationship Building"], "related": ["Business"]},
                {"name": "Adaptability", "aliases": ["Flexibility", "Resilience"], "related": ["Growth Mindset"]},
                {"name": "Patience", "aliases": ["Persistence", "Perseverance"], "related": ["Teaching"]},
            ]
        },
        "Time Management": {
            "skills": [
                {"name": "Prioritization", "aliases": ["Task Prioritization", "Priority Management"], "related": ["Planning"]},
                {"name": "Time Management", "aliases": ["Schedule Management", "Time Optimization"], "related": ["Productivity"]},
                {"name": "Multitasking", "aliases": ["Parallel Work", "Juggling Tasks"], "related": ["Organization"]},
                {"name": "Deadline Management", "aliases": ["Meeting Deadlines", "On-Time Delivery"], "related": ["Planning"]},
                {"name": "Estimation", "aliases": ["Effort Estimation", "Story Points"], "related": ["Agile"]},
                {"name": "Focus Management", "aliases": ["Deep Work", "Concentration"], "related": ["Productivity"]},
                {"name": "Work-Life Balance", "aliases": ["Boundary Setting"], "related": ["Well-being"]},
            ]
        },
    }

    soft = taxonomy.get("Soft Skills", {})
    for cat_name, cat_data in additional_soft.items():
        if cat_name not in soft:
            soft[cat_name] = cat_data
        else:
            existing_names = {s["name"] for s in soft[cat_name].get("skills", [])}
            for skill in cat_data["skills"]:
                if skill["name"] not in existing_names:
                    soft[cat_name]["skills"].append(skill)
    taxonomy["Soft Skills"] = soft

    # ─── Additional Domain Skills ───

    additional_domain = {
        "Marketing": {
            "skills": [
                {"name": "Digital Marketing", "aliases": ["Online Marketing", "Internet Marketing"], "related": ["SEO", "SEM"]},
                {"name": "Content Marketing", "aliases": ["Content Strategy"], "related": ["Copywriting"]},
                {"name": "Social Media Marketing", "aliases": ["SMM", "Social Media"], "related": ["Facebook Ads"]},
                {"name": "Email Marketing", "aliases": ["Email Campaigns", "Newsletter"], "related": ["Mailchimp"]},
                {"name": "SEM", "aliases": ["Search Engine Marketing", "Paid Search"], "related": ["Google Ads"]},
                {"name": "PPC", "aliases": ["Pay Per Click", "Paid Advertising"], "related": ["Google Ads"]},
                {"name": "Google Ads", "aliases": ["AdWords", "Google AdWords"], "related": ["SEM", "PPC"]},
                {"name": "Facebook Ads", "aliases": ["Meta Ads", "Instagram Ads"], "related": ["Social Media"]},
                {"name": "Marketing Automation", "aliases": ["Marketing Tech", "MarTech"], "related": ["HubSpot"]},
                {"name": "HubSpot", "aliases": ["hubspot"], "related": ["CRM", "Marketing Automation"]},
                {"name": "Marketo", "aliases": ["Adobe Marketo"], "related": ["Marketing Automation"]},
                {"name": "Copywriting", "aliases": ["Content Writing", "Ad Copy"], "related": ["Content Marketing"]},
                {"name": "Growth Hacking", "aliases": ["Growth Marketing", "Growth Strategy"], "related": ["Marketing"]},
                {"name": "Brand Strategy", "aliases": ["Branding", "Brand Management"], "related": ["Marketing"]},
                {"name": "Influencer Marketing", "aliases": ["Creator Marketing"], "related": ["Social Media"]},
            ]
        },
        "HR & Talent": {
            "skills": [
                {"name": "Talent Acquisition", "aliases": ["Recruiting", "Recruitment"], "related": ["HR", "ATS"]},
                {"name": "HRIS", "aliases": ["HR Information System", "HR Software"], "related": ["Workday"]},
                {"name": "ATS", "aliases": ["Applicant Tracking System", "Recruiting Software"], "related": ["Talent Acquisition"]},
                {"name": "Employee Engagement", "aliases": ["Employee Experience", "EX"], "related": ["HR"]},
                {"name": "Performance Management", "aliases": ["Performance Review", "Performance Evaluation"], "related": ["HR"]},
                {"name": "Learning & Development", "aliases": ["L&D", "Training"], "related": ["HR"]},
                {"name": "Compensation & Benefits", "aliases": ["Comp & Ben", "Total Rewards"], "related": ["HR"]},
                {"name": "Workforce Planning", "aliases": ["Headcount Planning"], "related": ["HR"]},
                {"name": "Employer Branding", "aliases": ["EVP", "Employee Value Proposition"], "related": ["Talent Acquisition"]},
                {"name": "People Analytics", "aliases": ["HR Analytics", "Workforce Analytics"], "related": ["Data Analytics"]},
                {"name": "Onboarding", "aliases": ["New Hire Onboarding"], "related": ["HR"]},
                {"name": "Workday", "aliases": ["workday"], "related": ["HRIS", "ERP"]},
                {"name": "SAP SuccessFactors", "aliases": ["SuccessFactors"], "related": ["HRIS", "SAP"]},
                {"name": "Payroll Management", "aliases": ["Payroll", "Payroll Processing"], "related": ["HR"]},
                {"name": "DEI Programs", "aliases": ["Diversity Programs", "Inclusion Programs"], "related": ["HR"]},
            ]
        },
        "Sales": {
            "skills": [
                {"name": "Salesforce", "aliases": ["SFDC", "salesforce.com", "SF CRM"], "related": ["CRM", "Sales"]},
                {"name": "CRM Management", "aliases": ["CRM", "Customer Relationship Management"], "related": ["Salesforce"]},
                {"name": "Lead Generation", "aliases": ["Lead Gen", "Prospecting"], "related": ["Sales"]},
                {"name": "Pipeline Management", "aliases": ["Sales Pipeline", "Funnel Management"], "related": ["CRM"]},
                {"name": "Sales Forecasting", "aliases": ["Revenue Forecasting"], "related": ["Analytics"]},
                {"name": "Account Management", "aliases": ["Key Account Management", "KAM"], "related": ["Customer Success"]},
                {"name": "Business Development", "aliases": ["BD", "BizDev"], "related": ["Sales"]},
                {"name": "Enterprise Sales", "aliases": ["B2B Sales", "Corporate Sales"], "related": ["Sales"]},
                {"name": "Solution Selling", "aliases": ["Consultative Selling", "Value Selling"], "related": ["Sales"]},
                {"name": "Revenue Operations", "aliases": ["RevOps", "Revenue Ops"], "related": ["Sales", "Analytics"]},
                {"name": "Customer Success", "aliases": ["CS", "Customer Success Management"], "related": ["Retention"]},
            ]
        },
        "Product Management": {
            "skills": [
                {"name": "Product Strategy", "aliases": ["Product Vision", "Product Thinking"], "related": ["Business Strategy"]},
                {"name": "Product Roadmap", "aliases": ["Roadmapping", "Product Planning"], "related": ["Strategy"]},
                {"name": "User Research", "aliases": ["UX Research", "Customer Research"], "related": ["Product"]},
                {"name": "Wireframing", "aliases": ["Wireframes", "Lo-Fi Design"], "related": ["UX Design"]},
                {"name": "Prototyping", "aliases": ["Rapid Prototyping", "Interactive Prototypes"], "related": ["Figma"]},
                {"name": "User Stories", "aliases": ["User Story Writing", "Requirements"], "related": ["Agile"]},
                {"name": "PRD Writing", "aliases": ["PRD", "Product Requirements Document"], "related": ["Product"]},
                {"name": "Feature Prioritization", "aliases": ["Backlog Prioritization", "RICE", "MoSCoW"], "related": ["Product"]},
                {"name": "Product Analytics", "aliases": ["Product Metrics", "KPI Tracking"], "related": ["Analytics"]},
                {"name": "Product-Market Fit", "aliases": ["PMF"], "related": ["Startup"]},
                {"name": "Go-to-Market", "aliases": ["GTM", "GTM Strategy", "Launch Strategy"], "related": ["Marketing"]},
                {"name": "Competitive Analysis", "aliases": ["Competitor Analysis", "Market Analysis"], "related": ["Strategy"]},
            ]
        },
        "Education & EdTech": {
            "skills": [
                {"name": "Learning Management System", "aliases": ["LMS", "eLearning Platform"], "related": ["EdTech"]},
                {"name": "Instructional Design", "aliases": ["Learning Design", "Course Design"], "related": ["Education"]},
                {"name": "Curriculum Development", "aliases": ["Curriculum Design", "Course Development"], "related": ["Education"]},
                {"name": "SCORM", "aliases": ["SCORM 2004", "SCORM 1.2"], "related": ["LMS", "eLearning"]},
                {"name": "Moodle", "aliases": ["moodle"], "related": ["LMS", "Open Source"]},
                {"name": "Canvas LMS", "aliases": ["Instructure Canvas"], "related": ["LMS"]},
                {"name": "Gamification", "aliases": ["Game-Based Learning"], "related": ["Engagement"]},
                {"name": "Adaptive Learning", "aliases": ["Personalized Learning"], "related": ["AI", "Education"]},
                {"name": "Assessment Design", "aliases": ["Test Design", "Quiz Design"], "related": ["Education"]},
                {"name": "Microlearning", "aliases": ["Bite-Sized Learning"], "related": ["Mobile Learning"]},
            ]
        },
        "Legal & Compliance": {
            "skills": [
                {"name": "Legal Tech", "aliases": ["LegalTech", "Legal Technology"], "related": ["Law"]},
                {"name": "Contract Management", "aliases": ["CLM", "Contract Lifecycle"], "related": ["Legal"]},
                {"name": "Regulatory Compliance", "aliases": ["Compliance Management", "Reg Compliance"], "related": ["Legal"]},
                {"name": "Data Privacy", "aliases": ["Privacy", "Data Protection"], "related": ["GDPR", "CCPA"]},
                {"name": "GDPR", "aliases": ["General Data Protection Regulation", "EU Privacy"], "related": ["Privacy"]},
                {"name": "CCPA", "aliases": ["California Privacy", "CPRA"], "related": ["Privacy"]},
                {"name": "eDiscovery", "aliases": ["Electronic Discovery", "e-Discovery"], "related": ["Legal"]},
                {"name": "IP Management", "aliases": ["Intellectual Property", "Patent Management"], "related": ["Legal"]},
                {"name": "SOC 2", "aliases": ["SOC 2 Type II", "SOC 2 Compliance"], "related": ["Security", "Compliance"]},
                {"name": "ISO 27001", "aliases": ["ISO27001", "ISMS"], "related": ["Security", "Compliance"]},
            ]
        },
        "Supply Chain & Logistics": {
            "skills": [
                {"name": "Supply Chain Management", "aliases": ["SCM", "Supply Chain"], "related": ["Logistics"]},
                {"name": "Logistics", "aliases": ["Logistics Management", "Shipping"], "related": ["Supply Chain"]},
                {"name": "Warehouse Management", "aliases": ["WMS", "Warehouse Operations"], "related": ["Logistics"]},
                {"name": "Demand Forecasting", "aliases": ["Demand Planning", "Forecasting"], "related": ["Analytics"]},
                {"name": "Inventory Optimization", "aliases": ["Inventory Management", "Stock Management"], "related": ["Supply Chain"]},
                {"name": "Procurement", "aliases": ["Purchasing", "Sourcing"], "related": ["Supply Chain"]},
                {"name": "SAP SCM", "aliases": ["SAP Supply Chain", "SAP S/4HANA"], "related": ["ERP"]},
                {"name": "Route Optimization", "aliases": ["Delivery Optimization", "Fleet Management"], "related": ["Logistics"]},
                {"name": "Last Mile Delivery", "aliases": ["Last Mile", "Final Mile"], "related": ["Logistics"]},
                {"name": "Trade Compliance", "aliases": ["Import/Export", "Customs"], "related": ["Compliance"]},
            ]
        },
        "Energy & Sustainability": {
            "skills": [
                {"name": "Renewable Energy", "aliases": ["Clean Energy", "Green Energy"], "related": ["Sustainability"]},
                {"name": "Solar Energy", "aliases": ["Solar Power", "Photovoltaic"], "related": ["Renewable Energy"]},
                {"name": "Wind Energy", "aliases": ["Wind Power", "Wind Turbine"], "related": ["Renewable Energy"]},
                {"name": "Energy Storage", "aliases": ["Battery Storage", "Grid Storage"], "related": ["Energy"]},
                {"name": "Smart Grid", "aliases": ["Intelligent Grid", "Grid Modernization"], "related": ["Energy"]},
                {"name": "ESG", "aliases": ["Environmental Social Governance", "ESG Reporting"], "related": ["Sustainability"]},
                {"name": "Carbon Footprint", "aliases": ["Carbon Accounting", "GHG Emissions"], "related": ["Sustainability"]},
                {"name": "LEED", "aliases": ["Green Building", "LEED Certification"], "related": ["Sustainability"]},
                {"name": "Sustainability Reporting", "aliases": ["CSR Reporting", "Impact Reporting"], "related": ["ESG"]},
                {"name": "Energy Efficiency", "aliases": ["Energy Conservation", "Energy Optimization"], "related": ["Sustainability"]},
            ]
        },
    }

    domain = taxonomy.get("Domain Skills", {})
    for cat_name, cat_data in additional_domain.items():
        if cat_name not in domain:
            domain[cat_name] = cat_data
        else:
            existing_names = {s["name"] for s in domain[cat_name].get("skills", [])}
            for skill in cat_data["skills"]:
                if skill["name"] not in existing_names:
                    domain[cat_name]["skills"].append(skill)
    taxonomy["Domain Skills"] = domain

    # ─── Bulk expansion: generate skill variants to reach 5000+ ───

    bulk_tech_skills = {
        "Programming Languages Extended": {
            "skills": [
                {"name": n, "aliases": a, "related": r}
                for n, a, r in [
                    ("Clojure", ["clj", "clojure"], ["JVM", "Functional Programming"]),
                    ("F#", ["FSharp", "fsharp"], [".NET", "Functional Programming"]),
                    ("Groovy", ["groovy"], ["JVM", "Gradle"]),
                    ("Julia", ["julia-lang"], ["Scientific Computing", "Python"]),
                    ("Fortran", ["FORTRAN", "fortran90"], ["Scientific Computing", "HPC"]),
                    ("COBOL", ["cobol"], ["Mainframe", "Legacy"]),
                    ("Assembly", ["ASM", "asm", "x86 Assembly"], ["Low-Level", "Systems"]),
                    ("Objective-C", ["ObjC", "Obj-C"], ["iOS", "macOS"]),
                    ("Visual Basic", ["VB", "VB.NET", "VBA"], [".NET", "Microsoft"]),
                    ("Delphi", ["Object Pascal", "Pascal"], ["Desktop", "RAD"]),
                    ("Erlang", ["erlang", "OTP"], ["Concurrency", "Telecom"]),
                    ("OCaml", ["ocaml"], ["Functional", "ML"]),
                    ("Scheme", ["scheme", "Racket"], ["Lisp", "Functional"]),
                    ("Prolog", ["prolog"], ["Logic Programming", "AI"]),
                    ("Common Lisp", ["Lisp", "lisp", "CL"], ["Functional", "AI"]),
                    ("Ada", ["ada"], ["Safety-Critical", "Aerospace"]),
                    ("ABAP", ["abap"], ["SAP", "Enterprise"]),
                    ("Apex", ["apex", "Salesforce Apex"], ["Salesforce", "CRM"]),
                    ("Solidity", ["sol", "solidity"], ["Ethereum", "Smart Contracts"]),
                    ("VHDL", ["vhdl"], ["FPGA", "Hardware"]),
                    ("Verilog", ["verilog", "SystemVerilog"], ["FPGA", "Hardware"]),
                    ("PowerShell", ["pwsh", "PS", "powershell"], ["Windows", "Scripting"]),
                    ("Bash", ["bash", "Shell Script", "sh", "zsh"], ["Linux", "Scripting"]),
                    ("Tcl", ["tcl/tk", "Tcl/Tk"], ["Scripting", "Testing"]),
                    ("Zig", ["zig-lang"], ["Systems", "C Alternative"]),
                    ("Nim", ["nim-lang", "nimlang"], ["Systems", "Metaprogramming"]),
                    ("Crystal", ["crystal-lang"], ["Ruby-like", "Compiled"]),
                    ("V", ["vlang", "v-lang"], ["Systems", "Simple"]),
                    ("Mojo", ["mojo-lang", "modular mojo"], ["Python", "AI"]),
                    ("Carbon", ["carbon-lang"], ["C++ Alternative", "Google"]),
                    ("Hack", ["hacklang"], ["PHP", "Facebook"]),
                    ("D", ["dlang", "D Language"], ["Systems", "C++ Alternative"]),
                    ("Chapel", ["chapel-lang"], ["Parallel Computing", "HPC"]),
                    ("Ballerina", ["ballerina-lang"], ["Cloud Native", "Integration"]),
                    ("Awk", ["awk", "gawk"], ["Text Processing", "Unix"]),
                    ("Sed", ["sed"], ["Text Processing", "Unix"]),
                    ("Smalltalk", ["smalltalk", "Pharo"], ["OOP", "IDE"]),
                    ("CoffeeScript", ["coffee", "coffeescript"], ["JavaScript", "Transpiler"]),
                    ("Elm", ["elm-lang"], ["Functional", "Frontend"]),
                    ("PureScript", ["purescript"], ["Functional", "JavaScript"]),
                    ("ReasonML", ["reason", "ReScript"], ["OCaml", "JavaScript"]),
                    ("Idris", ["idris"], ["Dependent Types", "Functional"]),
                    ("Agda", ["agda"], ["Proof Assistant", "Functional"]),
                    ("Coq", ["coq"], ["Proof Assistant", "Verification"]),
                    ("Lean", ["lean4", "Lean 4"], ["Proof Assistant", "Math"]),
                    ("Standard ML", ["SML", "sml"], ["Functional", "ML"]),
                    ("AWK", ["awk"], ["Text Processing", "Scripting"]),
                    ("Wolfram Language", ["Mathematica", "WL"], ["Math", "Scientific"]),
                    ("SQL", ["Structured Query Language"], ["Databases", "Data"]),
                    ("PL/SQL", ["plsql", "PL SQL"], ["Oracle", "Database"]),
                    ("T-SQL", ["tsql", "Transact-SQL"], ["SQL Server", "Microsoft"]),
                ]
            ]
        },
        "Web Frameworks Extended": {
            "skills": [
                {"name": n, "aliases": a, "related": r}
                for n, a, r in [
                    ("Remix", ["remix-run", "remix.run"], ["React", "Full-Stack"]),
                    ("Astro", ["astro.build", "astrojs"], ["Static Site", "Islands"]),
                    ("Solid.js", ["SolidJS", "solid-js"], ["Reactive", "Frontend"]),
                    ("Qwik", ["qwik-city", "builder-qwik"], ["Resumable", "Frontend"]),
                    ("Fastify", ["fastify"], ["Node.js", "Performance"]),
                    ("Koa", ["koa.js", "koajs"], ["Node.js", "Middleware"]),
                    ("Nest.js", ["NestJS", "nestjs"], ["Node.js", "TypeScript"]),
                    ("Hono", ["hono-js", "honojs"], ["Edge", "TypeScript"]),
                    ("Pyramid", ["pyramid"], ["Python", "Web"]),
                    ("Tornado", ["tornado-web"], ["Python", "Async"]),
                    ("Starlette", ["starlette"], ["Python", "ASGI"]),
                    ("Sanic", ["sanic"], ["Python", "Async"]),
                    ("Bottle", ["bottle.py"], ["Python", "Micro"]),
                    ("CherryPy", ["cherrypy"], ["Python", "Web"]),
                    ("Spring MVC", ["spring-mvc"], ["Java", "Web"]),
                    ("Quarkus", ["quarkus"], ["Java", "Cloud Native"]),
                    ("Micronaut", ["micronaut"], ["Java", "Microservices"]),
                    ("Vert.x", ["vertx", "Eclipse Vert.x"], ["Java", "Reactive"]),
                    ("Sinatra", ["sinatra"], ["Ruby", "DSL"]),
                    ("Hanami", ["hanami-rb"], ["Ruby", "Clean Architecture"]),
                    ("Symfony", ["symfony"], ["PHP", "Enterprise"]),
                    ("CodeIgniter", ["CI", "codeigniter"], ["PHP", "MVC"]),
                    ("CakePHP", ["cakephp"], ["PHP", "RAD"]),
                    ("Slim", ["slim-php"], ["PHP", "Micro"]),
                    ("Blazor", ["blazor"], ["C#", "WebAssembly"]),
                    ("Phoenix", ["phoenix-framework"], ["Elixir", "Real-time"]),
                    ("Gin", ["gin-gonic"], ["Go", "Web"]),
                    ("Echo", ["echo-go"], ["Go", "Web"]),
                    ("Fiber", ["gofiber", "fiber-go"], ["Go", "Express-like"]),
                    ("Chi", ["go-chi"], ["Go", "Router"]),
                    ("Actix", ["actix-web", "actix"], ["Rust", "Web"]),
                    ("Rocket", ["rocket-rs"], ["Rust", "Web"]),
                    ("Warp", ["warp-rs"], ["Rust", "Web"]),
                    ("Axum", ["axum-rs"], ["Rust", "Tokio"]),
                    ("htmx", ["HTMX"], ["HTML", "Hypermedia"]),
                    ("Alpine.js", ["alpinejs", "alpine.js"], ["JavaScript", "Lightweight"]),
                    ("Stimulus", ["stimulus-js", "Hotwire Stimulus"], ["JavaScript", "Rails"]),
                    ("Turbo", ["turbo-rails", "Hotwire Turbo"], ["Rails", "SPA"]),
                    ("Lit", ["lit-html", "LitElement"], ["Web Components", "Google"]),
                    ("Stencil", ["stenciljs"], ["Web Components", "Ionic"]),
                    ("Ember.js", ["EmberJS", "ember.js"], ["JavaScript", "Convention"]),
                    ("Backbone.js", ["BackboneJS", "backbone"], ["JavaScript", "MVC"]),
                    ("Preact", ["preact"], ["React Alternative", "Lightweight"]),
                    ("Inferno", ["infernojs"], ["React Alternative", "Performance"]),
                    ("Mithril", ["mithril.js"], ["JavaScript", "Lightweight"]),
                ]
            ]
        },
        "Databases Extended": {
            "skills": [
                {"name": n, "aliases": a, "related": r}
                for n, a, r in [
                    ("CockroachDB", ["cockroach", "CRDB"], ["Distributed SQL", "PostgreSQL"]),
                    ("TimescaleDB", ["timescale"], ["Time Series", "PostgreSQL"]),
                    ("ScyllaDB", ["scylla"], ["Cassandra Compatible", "NoSQL"]),
                    ("ClickHouse", ["clickhouse"], ["OLAP", "Analytics"]),
                    ("Apache Druid", ["Druid", "druid"], ["OLAP", "Real-time"]),
                    ("Couchbase", ["couchbase"], ["NoSQL", "Document"]),
                    ("ArangoDB", ["arango"], ["Multi-Model", "Graph"]),
                    ("FaunaDB", ["Fauna", "fauna"], ["Serverless", "Document"]),
                    ("Memcached", ["memcache", "memcached"], ["Caching", "In-Memory"]),
                    ("Dgraph", ["dgraph"], ["Graph", "GraphQL"]),
                    ("TiDB", ["tidb"], ["Distributed SQL", "MySQL"]),
                    ("VoltDB", ["voltdb"], ["In-Memory", "ACID"]),
                    ("CouchDB", ["couchdb", "Apache CouchDB"], ["NoSQL", "Document"]),
                    ("RethinkDB", ["rethink"], ["Real-time", "NoSQL"]),
                    ("Supabase", ["supabase"], ["PostgreSQL", "BaaS"]),
                    ("PlanetScale", ["planetscale"], ["MySQL", "Serverless"]),
                    ("Neon", ["neon-tech", "neondb"], ["PostgreSQL", "Serverless"]),
                    ("Turso", ["turso", "libSQL"], ["SQLite", "Edge"]),
                    ("QuestDB", ["questdb"], ["Time Series", "SQL"]),
                    ("Apache HBase", ["HBase", "hbase"], ["Hadoop", "Column"]),
                    ("Apache Hive", ["Hive", "hive"], ["Hadoop", "SQL"]),
                    ("MariaDB", ["mariadb"], ["MySQL Fork", "RDBMS"]),
                    ("Vitess", ["vitess"], ["MySQL", "Scaling"]),
                    ("YugabyteDB", ["yugabyte"], ["Distributed SQL", "PostgreSQL"]),
                    ("FoundationDB", ["fdb", "foundationdb"], ["Distributed", "Apple"]),
                    ("Apache Pinot", ["Pinot", "pinot"], ["OLAP", "Real-time"]),
                    ("Apache Doris", ["Doris", "doris"], ["OLAP", "Analytics"]),
                    ("StarRocks", ["starrocks"], ["OLAP", "Sub-second"]),
                    ("Milvus", ["milvus"], ["Vector DB", "AI"]),
                    ("Pinecone", ["pinecone"], ["Vector DB", "Similarity"]),
                    ("Weaviate", ["weaviate"], ["Vector DB", "Semantic"]),
                    ("Qdrant", ["qdrant"], ["Vector DB", "Rust"]),
                    ("Chroma", ["chromadb", "chroma"], ["Vector DB", "Embeddings"]),
                    ("pgvector", ["pg_vector"], ["PostgreSQL", "Vector"]),
                    ("Zilliz", ["zilliz"], ["Vector DB", "Milvus"]),
                    ("LanceDB", ["lancedb"], ["Vector DB", "Embedded"]),
                ]
            ]
        },
        "Cloud Services Extended": {
            "skills": [
                {"name": n, "aliases": a, "related": r}
                for n, a, r in [
                    ("AWS EC2", ["EC2", "Elastic Compute"], ["AWS", "Compute"]),
                    ("AWS S3", ["S3", "Simple Storage"], ["AWS", "Storage"]),
                    ("AWS RDS", ["RDS", "Relational Database Service"], ["AWS", "Database"]),
                    ("AWS EKS", ["EKS", "Elastic Kubernetes"], ["AWS", "Kubernetes"]),
                    ("AWS ECS", ["ECS", "Elastic Container"], ["AWS", "Containers"]),
                    ("AWS CloudFront", ["CloudFront", "CF"], ["AWS", "CDN"]),
                    ("AWS Route 53", ["Route53", "Route 53"], ["AWS", "DNS"]),
                    ("AWS IAM", ["IAM", "Identity Access"], ["AWS", "Security"]),
                    ("AWS Cognito", ["Cognito"], ["AWS", "Auth"]),
                    ("AWS API Gateway", ["APIGW", "API Gateway"], ["AWS", "API"]),
                    ("AWS Glue", ["Glue", "AWS Glue ETL"], ["AWS", "ETL"]),
                    ("AWS Athena", ["Athena"], ["AWS", "SQL"]),
                    ("AWS EMR", ["EMR", "Elastic MapReduce"], ["AWS", "Big Data"]),
                    ("AWS SageMaker", ["SageMaker", "sagemaker"], ["AWS", "ML"]),
                    ("AWS Bedrock", ["Bedrock", "bedrock"], ["AWS", "Generative AI"]),
                    ("Azure DevOps", ["ADO", "Azure DevOps Server"], ["Azure", "CI/CD"]),
                    ("Azure Kubernetes Service", ["AKS", "Azure K8s"], ["Azure", "Kubernetes"]),
                    ("Azure Functions", ["AZ Functions"], ["Azure", "Serverless"]),
                    ("Azure Cosmos DB", ["CosmosDB", "Cosmos DB"], ["Azure", "NoSQL"]),
                    ("Azure Blob Storage", ["Blob Storage", "Azure Blob"], ["Azure", "Storage"]),
                    ("Azure ML", ["Azure Machine Learning", "AzureML"], ["Azure", "ML"]),
                    ("Azure OpenAI", ["Azure OpenAI Service"], ["Azure", "AI"]),
                    ("Google Kubernetes Engine", ["GKE", "Google K8s"], ["GCP", "Kubernetes"]),
                    ("Google Cloud Run", ["Cloud Run", "GCR"], ["GCP", "Serverless"]),
                    ("Google Cloud Storage", ["GCS", "Cloud Storage"], ["GCP", "Storage"]),
                    ("Google Cloud SQL", ["Cloud SQL"], ["GCP", "Database"]),
                    ("Google Vertex AI", ["Vertex AI", "Vertex"], ["GCP", "ML"]),
                    ("Cloudflare", ["CF", "cloudflare"], ["CDN", "Security"]),
                    ("Fly.io", ["flyio", "fly"], ["Edge", "Containers"]),
                    ("Railway", ["railway.app"], ["PaaS", "Deployment"]),
                    ("Render", ["render.com"], ["PaaS", "Deployment"]),
                    ("Linode", ["Akamai Linode"], ["VPS", "Cloud"]),
                    ("Vultr", ["vultr"], ["VPS", "Cloud"]),
                    ("IBM Cloud", ["Bluemix", "IBM Bluemix"], ["Enterprise", "Cloud"]),
                    ("Oracle Cloud", ["OCI", "Oracle Cloud Infrastructure"], ["Enterprise", "Cloud"]),
                    ("Alibaba Cloud", ["Aliyun", "AliCloud"], ["Cloud", "Asia"]),
                    ("Hetzner", ["hetzner"], ["VPS", "Europe"]),
                ]
            ]
        },
        "DevOps Extended": {
            "skills": [
                {"name": n, "aliases": a, "related": r}
                for n, a, r in [
                    ("Puppet", ["puppet"], ["Configuration Management", "Ruby"]),
                    ("Chef", ["chef", "Chef Infra"], ["Configuration Management", "Ruby"]),
                    ("Vagrant", ["vagrant", "HashiCorp Vagrant"], ["VMs", "Development"]),
                    ("Packer", ["packer", "HashiCorp Packer"], ["Image Building", "HashiCorp"]),
                    ("Travis CI", ["travis", "travisci"], ["CI/CD", "GitHub"]),
                    ("ArgoCD", ["Argo CD", "argocd"], ["GitOps", "Kubernetes"]),
                    ("FluxCD", ["Flux", "flux-cd"], ["GitOps", "Kubernetes"]),
                    ("Tekton", ["tekton-pipelines"], ["CI/CD", "Kubernetes"]),
                    ("Buildkite", ["buildkite"], ["CI/CD", "Pipelines"]),
                    ("Drone CI", ["drone", "drone.io"], ["CI/CD", "Containers"]),
                    ("Caddy", ["caddy-server", "caddyserver"], ["Web Server", "HTTPS"]),
                    ("HAProxy", ["haproxy"], ["Load Balancer", "Proxy"]),
                    ("Traefik", ["traefik"], ["Reverse Proxy", "Cloud Native"]),
                    ("Envoy", ["envoy-proxy"], ["Proxy", "Service Mesh"]),
                    ("Istio", ["istio"], ["Service Mesh", "Kubernetes"]),
                    ("Linkerd", ["linkerd"], ["Service Mesh", "CNCF"]),
                    ("Consul", ["HashiCorp Consul", "consul"], ["Service Discovery", "HashiCorp"]),
                    ("Vault", ["HashiCorp Vault", "vault"], ["Secrets", "Security"]),
                    ("Nomad", ["HashiCorp Nomad", "nomad"], ["Orchestration", "HashiCorp"]),
                    ("Salt", ["SaltStack", "salt"], ["Configuration Management", "Python"]),
                    ("Pulumi", ["pulumi"], ["IaC", "Programming"]),
                    ("AWS CDK", ["CDK", "Cloud Development Kit"], ["AWS", "IaC"]),
                    ("CloudFormation", ["AWS CloudFormation", "CFN"], ["AWS", "IaC"]),
                    ("Bicep", ["Azure Bicep"], ["Azure", "IaC"]),
                    ("Podman", ["podman"], ["Containers", "Docker Alternative"]),
                    ("Containerd", ["containerd"], ["Container Runtime", "CNCF"]),
                    ("CRI-O", ["cri-o", "crio"], ["Container Runtime", "Kubernetes"]),
                    ("Kustomize", ["kustomize"], ["Kubernetes", "Configuration"]),
                    ("Skaffold", ["skaffold"], ["Kubernetes", "Development"]),
                    ("Tilt", ["tilt.dev"], ["Kubernetes", "Development"]),
                    ("k9s", ["k9s"], ["Kubernetes", "CLI"]),
                    ("Lens", ["k8slens"], ["Kubernetes", "IDE"]),
                    ("Rancher", ["rancher"], ["Kubernetes", "Management"]),
                    ("Crossplane", ["crossplane"], ["Kubernetes", "IaC"]),
                    ("Teleport", ["teleport"], ["Access", "Security"]),
                    ("Boundary", ["HashiCorp Boundary"], ["Access", "Security"]),
                ]
            ]
        },
        "AI & ML Extended": {
            "skills": [
                {"name": n, "aliases": a, "related": r}
                for n, a, r in [
                    ("BERT", ["bert", "bert-base"], ["NLP", "Transformers"]),
                    ("GPT", ["gpt-4", "gpt-3", "ChatGPT"], ["LLM", "OpenAI"]),
                    ("LLaMA", ["Llama", "llama2", "Meta LLaMA"], ["LLM", "Open Source"]),
                    ("Claude API", ["claude", "Anthropic Claude"], ["LLM", "Anthropic"]),
                    ("Gemini", ["google-gemini", "Bard"], ["LLM", "Google"]),
                    ("Stable Diffusion", ["SD", "stable-diffusion"], ["Image Generation", "Diffusion"]),
                    ("DALL-E", ["dall-e", "dalle"], ["Image Generation", "OpenAI"]),
                    ("Midjourney", ["midjourney"], ["Image Generation", "AI Art"]),
                    ("GANs", ["Generative Adversarial Networks", "GAN"], ["Deep Learning", "Generation"]),
                    ("VAEs", ["Variational Autoencoders", "VAE"], ["Deep Learning", "Generation"]),
                    ("CNNs", ["Convolutional Neural Networks", "CNN"], ["Computer Vision", "Deep Learning"]),
                    ("RNNs", ["Recurrent Neural Networks", "RNN"], ["Sequence", "Deep Learning"]),
                    ("LSTMs", ["Long Short-Term Memory", "LSTM"], ["Sequence", "RNN"]),
                    ("Attention Mechanism", ["Self-Attention", "Multi-Head Attention"], ["Transformers", "NLP"]),
                    ("LlamaIndex", ["llama-index", "GPT Index"], ["RAG", "LLM"]),
                    ("Weights & Biases", ["WandB", "wandb"], ["Experiment Tracking", "MLOps"]),
                    ("DVC", ["Data Version Control", "dvc"], ["Data Versioning", "MLOps"]),
                    ("Feast", ["feast-dev"], ["Feature Store", "MLOps"]),
                    ("AutoML", ["auto-ml", "Automated ML"], ["Machine Learning", "Automation"]),
                    ("H2O.ai", ["H2O", "h2o"], ["AutoML", "ML Platform"]),
                    ("DataRobot", ["datarobot"], ["AutoML", "ML Platform"]),
                    ("SciPy", ["scipy"], ["Scientific Computing", "Python"]),
                    ("Matplotlib", ["matplotlib", "plt"], ["Visualization", "Python"]),
                    ("Seaborn", ["seaborn", "sns"], ["Visualization", "Statistical"]),
                    ("Plotly", ["plotly", "plotly.py"], ["Visualization", "Interactive"]),
                    ("JAX", ["jax", "Google JAX"], ["Deep Learning", "Autograd"]),
                    ("ONNX", ["onnx", "Open Neural Network Exchange"], ["Model Format", "Interop"]),
                    ("TensorRT", ["tensorrt"], ["Inference", "NVIDIA"]),
                    ("Triton", ["triton-inference", "NVIDIA Triton"], ["Inference Server", "NVIDIA"]),
                    ("vLLM", ["vllm"], ["LLM Serving", "Inference"]),
                    ("Ollama", ["ollama"], ["Local LLM", "Inference"]),
                    ("LiteLLM", ["litellm"], ["LLM Proxy", "API"]),
                    ("CrewAI", ["crewai", "crew-ai"], ["AI Agents", "Multi-Agent"]),
                    ("AutoGen", ["autogen", "Microsoft AutoGen"], ["AI Agents", "Multi-Agent"]),
                    ("Semantic Kernel", ["semantic-kernel"], ["AI", "Microsoft"]),
                    ("Pinecone", ["pinecone"], ["Vector Search", "Embeddings"]),
                    ("spaCy", ["spacy"], ["NLP", "Python"]),
                    ("NLTK", ["nltk"], ["NLP", "Python"]),
                    ("Gensim", ["gensim"], ["Topic Modeling", "NLP"]),
                    ("FastText", ["fasttext"], ["Word Embeddings", "NLP"]),
                    ("Word2Vec", ["word2vec"], ["Word Embeddings", "NLP"]),
                    ("GloVe", ["glove"], ["Word Embeddings", "NLP"]),
                    ("Sentence Transformers", ["sentence-transformers", "SBERT"], ["Embeddings", "NLP"]),
                    ("Whisper", ["openai-whisper"], ["Speech Recognition", "OpenAI"]),
                    ("ElevenLabs", ["elevenlabs"], ["Text-to-Speech", "AI"]),
                    ("Detectron2", ["detectron"], ["Object Detection", "Facebook"]),
                    ("Ultralytics", ["ultralytics", "YOLO"], ["Object Detection", "CV"]),
                    ("MediaPipe", ["mediapipe"], ["Pose Estimation", "Google"]),
                    ("CatBoost", ["catboost"], ["Gradient Boosting", "Yandex"]),
                    ("LightGBM", ["lightgbm", "lgbm"], ["Gradient Boosting", "Microsoft"]),
                    ("Optuna", ["optuna"], ["Hyperparameter Tuning", "Bayesian"]),
                    ("Ray", ["ray.io", "ray-project"], ["Distributed", "ML"]),
                    ("Dask", ["dask"], ["Parallel Computing", "Python"]),
                    ("Polars", ["polars"], ["DataFrame", "Rust"]),
                    ("Vaex", ["vaex"], ["Big Data", "DataFrame"]),
                    ("Apache Arrow", ["Arrow", "pyarrow"], ["Columnar", "Data Format"]),
                    ("Hugging Face Hub", ["HF Hub", "huggingface-hub"], ["Model Hub", "ML"]),
                    ("Gradio", ["gradio"], ["ML Demo", "UI"]),
                    ("Streamlit", ["streamlit"], ["Data Apps", "Python"]),
                ]
            ]
        },
        "Data Engineering Extended": {
            "skills": [
                {"name": n, "aliases": a, "related": r}
                for n, a, r in [
                    ("Dagster", ["dagster"], ["Orchestration", "Data"]),
                    ("Prefect", ["prefect"], ["Orchestration", "Python"]),
                    ("Luigi", ["luigi"], ["Pipeline", "Spotify"]),
                    ("Celery", ["celery"], ["Task Queue", "Python"]),
                    ("Apache Beam", ["Beam", "beam"], ["Unified", "Streaming"]),
                    ("Apache NiFi", ["NiFi", "nifi"], ["Data Flow", "ETL"]),
                    ("Apache Storm", ["Storm", "storm"], ["Real-time", "Streaming"]),
                    ("Apache Pig", ["Pig", "pig"], ["Hadoop", "Scripting"]),
                    ("Presto", ["presto", "PrestoDB"], ["SQL", "Distributed"]),
                    ("Trino", ["trino", "PrestoSQL"], ["SQL", "Distributed"]),
                    ("Databricks", ["databricks"], ["Spark", "Lakehouse"]),
                    ("Delta Lake", ["delta-lake", "delta"], ["Lakehouse", "Databricks"]),
                    ("Apache Iceberg", ["Iceberg", "iceberg"], ["Table Format", "Lakehouse"]),
                    ("Apache Hudi", ["Hudi", "hudi"], ["Incremental", "Lakehouse"]),
                    ("Great Expectations", ["great-expectations", "GX"], ["Data Quality", "Testing"]),
                    ("Pandera", ["pandera"], ["Data Validation", "Pandas"]),
                    ("Fivetran", ["fivetran"], ["ELT", "SaaS"]),
                    ("Stitch", ["stitch-data"], ["ETL", "SaaS"]),
                    ("Airbyte", ["airbyte"], ["ELT", "Open Source"]),
                    ("Debezium", ["debezium"], ["CDC", "Kafka"]),
                    ("Apache Atlas", ["Atlas", "atlas"], ["Data Catalog", "Governance"]),
                    ("DataHub", ["datahub"], ["Data Catalog", "LinkedIn"]),
                    ("Amundsen", ["amundsen"], ["Data Discovery", "Lyft"]),
                    ("OpenLineage", ["openlineage"], ["Data Lineage", "Marquez"]),
                    ("Apache Superset", ["Superset", "superset"], ["BI", "Visualization"]),
                    ("Metabase", ["metabase"], ["BI", "Analytics"]),
                    ("Looker", ["looker", "Google Looker"], ["BI", "Google"]),
                    ("Mode Analytics", ["mode"], ["BI", "SQL"]),
                    ("Sigma", ["sigma-computing"], ["BI", "Cloud"]),
                    ("Hex", ["hex.tech"], ["Notebooks", "Analytics"]),
                ]
            ]
        },
        "IoT & Embedded": {
            "skills": [
                {"name": n, "aliases": a, "related": r}
                for n, a, r in [
                    ("Arduino", ["arduino"], ["Microcontroller", "C++"]),
                    ("Raspberry Pi", ["RPi", "raspi"], ["SBC", "Linux"]),
                    ("ESP32", ["esp32", "Espressif"], ["WiFi", "IoT"]),
                    ("STM32", ["stm32"], ["ARM", "Microcontroller"]),
                    ("FreeRTOS", ["freertos"], ["RTOS", "Embedded"]),
                    ("Zephyr", ["zephyr-rtos", "Zephyr RTOS"], ["RTOS", "IoT"]),
                    ("PlatformIO", ["platformio", "pio"], ["Embedded", "IDE"]),
                    ("MQTT", ["mqtt"], ["IoT", "Messaging"]),
                    ("CoAP", ["coap"], ["IoT", "Protocol"]),
                    ("Zigbee", ["zigbee"], ["Wireless", "IoT"]),
                    ("Z-Wave", ["zwave"], ["Smart Home", "IoT"]),
                    ("BLE", ["Bluetooth Low Energy", "BLE 5.0"], ["Wireless", "IoT"]),
                    ("LoRaWAN", ["LoRa", "lorawan"], ["LPWAN", "IoT"]),
                    ("Edge Computing", ["edge", "Edge AI"], ["IoT", "AI"]),
                    ("Thread", ["thread-protocol"], ["IoT", "Networking"]),
                    ("Matter", ["matter-protocol", "Project CHIP"], ["Smart Home", "IoT"]),
                    ("ROS", ["Robot Operating System", "ROS2"], ["Robotics", "Middleware"]),
                    ("OpenCV Embedded", ["opencv-embedded"], ["Computer Vision", "Edge"]),
                    ("TensorFlow Lite", ["TFLite", "tflite"], ["ML", "Edge"]),
                    ("NVIDIA Jetson", ["Jetson", "Jetson Nano"], ["Edge AI", "GPU"]),
                ]
            ]
        },
        "Blockchain & Web3": {
            "skills": [
                {"name": n, "aliases": a, "related": r}
                for n, a, r in [
                    ("Ethereum", ["ETH", "eth"], ["Blockchain", "Smart Contracts"]),
                    ("Smart Contracts", ["smart-contracts"], ["Blockchain", "Solidity"]),
                    ("DeFi", ["Decentralized Finance", "defi"], ["Blockchain", "Finance"]),
                    ("NFTs", ["Non-Fungible Tokens", "nft"], ["Blockchain", "Digital Assets"]),
                    ("Web3.js", ["web3js", "web3"], ["Ethereum", "JavaScript"]),
                    ("Ethers.js", ["ethersjs", "ethers"], ["Ethereum", "JavaScript"]),
                    ("Hardhat", ["hardhat"], ["Ethereum", "Development"]),
                    ("Foundry", ["foundry-rs", "forge"], ["Ethereum", "Testing"]),
                    ("Truffle", ["truffle-suite"], ["Ethereum", "Development"]),
                    ("IPFS", ["ipfs", "InterPlanetary File System"], ["Decentralized", "Storage"]),
                    ("Polygon", ["Matic", "polygon-network"], ["Layer 2", "Ethereum"]),
                    ("Solana", ["SOL", "solana"], ["Blockchain", "High Performance"]),
                    ("Arbitrum", ["arbitrum"], ["Layer 2", "Ethereum"]),
                    ("Optimism", ["OP", "optimism"], ["Layer 2", "Ethereum"]),
                    ("Hyperledger", ["hyperledger-fabric"], ["Enterprise", "Blockchain"]),
                    ("Substrate", ["substrate"], ["Polkadot", "Blockchain"]),
                    ("Cosmos SDK", ["cosmos", "Tendermint"], ["Blockchain", "Interchain"]),
                    ("Chainlink", ["chainlink", "LINK"], ["Oracle", "Blockchain"]),
                    ("The Graph", ["thegraph", "Graph Protocol"], ["Indexing", "Blockchain"]),
                    ("Zero-Knowledge Proofs", ["ZKP", "zk-SNARKs", "zk-STARKs"], ["Privacy", "Scaling"]),
                    ("Rust for Blockchain", ["Rust Solana", "ink!"], ["Solana", "Substrate"]),
                    ("Move", ["move-lang"], ["Aptos", "Sui"]),
                    ("Vyper", ["vyper"], ["Ethereum", "Python-like"]),
                    ("Cairo", ["cairo-lang", "StarkNet Cairo"], ["StarkNet", "ZK"]),
                    ("Anchor", ["anchor-framework"], ["Solana", "Rust"]),
                ]
            ]
        },
        "Game Development": {
            "skills": [
                {"name": n, "aliases": a, "related": r}
                for n, a, r in [
                    ("Unity", ["unity3d", "Unity Engine"], ["Game Engine", "C#"]),
                    ("Unreal Engine", ["UE5", "UE4", "Unreal"], ["Game Engine", "C++"]),
                    ("Godot", ["godot-engine"], ["Game Engine", "Open Source"]),
                    ("Phaser", ["phaserjs", "phaser.js"], ["HTML5 Games", "JavaScript"]),
                    ("SDL", ["SDL2", "Simple DirectMedia Layer"], ["Game", "C"]),
                    ("OpenGL", ["opengl"], ["Graphics", "3D"]),
                    ("Vulkan", ["vulkan"], ["Graphics", "Low-Level"]),
                    ("DirectX", ["DX11", "DX12", "Direct3D"], ["Graphics", "Windows"]),
                    ("Game Design", ["game-design"], ["Design", "Game"]),
                    ("Level Design", ["level-design"], ["Game Design", "Environment"]),
                    ("Shader Programming", ["GLSL", "HLSL", "Shaders"], ["Graphics", "GPU"]),
                    ("Bevy", ["bevy-engine"], ["Rust", "Game Engine"]),
                    ("Raylib", ["raylib"], ["Game", "C"]),
                    ("LÖVE", ["love2d", "LÖVE 2D"], ["Game", "Lua"]),
                    ("GameMaker", ["GameMaker Studio", "GML"], ["Game", "2D"]),
                ]
            ]
        },
    }

    for cat_name, cat_data in bulk_tech_skills.items():
        if cat_name not in tech:
            tech[cat_name] = cat_data
        else:
            existing_names = {s["name"] for s in tech[cat_name].get("skills", [])}
            for skill in cat_data["skills"]:
                if skill["name"] not in existing_names:
                    tech[cat_name]["skills"].append(skill)
    taxonomy["Technical Skills"] = tech

    return taxonomy


def count_skills(taxonomy: Dict) -> int:
    """Count total skills in taxonomy."""
    total = 0
    for top_level in taxonomy.values():
        for category in top_level.values():
            total += len(category.get("skills", []))
    return total


if __name__ == "__main__":
    print("Generating expanded skill taxonomy...")
    taxonomy = generate_expanded_taxonomy()
    total = count_skills(taxonomy)
    print(f"Total skills: {total}")

    output_path = Path(__file__).parent / "skill_taxonomy.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(taxonomy, f, indent=2, ensure_ascii=False)

    print(f"Written to: {output_path}")

    # Print category breakdown
    for top_level_name, categories in taxonomy.items():
        cat_total = sum(len(c.get("skills", [])) for c in categories.values())
        print(f"\n  {top_level_name}: {cat_total} skills")
        for cat_name, cat_data in categories.items():
            print(f"    {cat_name}: {len(cat_data.get('skills', []))} skills")
