<div align="center">

# 🧭 Scout

**Paste a job link → Scoutly parses it → a new row appears in your job tracker.**  
Turn messy job postings into structured data — automatically.

</div>

---

## 🔥 Overview

Scoutly is an AI agent that extracts job details from any career site and syncs them directly into a Google Sheet.  
It removes the most tedious part of job hunting: manually copying fields from Workday / Greenhouse / Lever into a tracker.

---

## ⚙️ How it Works

```
User
↓
LlamaIndex Agent
↓
Tools
├─ fetch_job_page(url)
├─ extract_job_info(text)
└─ log_job_to_sheet(record)
```

The agent orchestrates tool calls based on the goal — not a hardcoded pipeline.

---

## 📌 Data Model

Each job entry is logged using the following schema:

| Field | Description |
|--------|-------------|
| Company | Employer name |
| RoleTitle | Job title shown on posting |
| Level | Intern / New Grad / Junior / etc. |
| Location | City / State / Region |
| RemoteType | Onsite / Hybrid / Remote |
| JobURL | Direct link to job posting |
| JobID | Req ID or Job number if available |
| ATSType | Workday, Greenhouse, Lever, Other |
| PostedDate | If detectable |
| ExperienceRequiredYears | Parsed from qualifications |
| Status | Defaults to `Planned` |
| Tags | Keywords extracted |
| Notes | Optional free text |

The Google Sheet should match this column order.

---

## 🧰 Tech Stack

| Component | Tool |
|----------|------|
| Agent orchestration | LlamaIndex |
| Model | OpenAI (configurable) |
| Data extraction | Structured output program |
| Storage | Google Sheets API |
| Optional | Playwright for JS-rendered pages |

---

## 🚀 Usage

```bash
python main.py "https://careers.company.com/job/12345"
```

Example output:
```
Logged Software Engineer — New Grad at Capital One to your tracker.
```

🗺️ Roadmap
---

- Dashboard for visualizing the job pipeline
- Automatic status updates (OA → interviews → offers)
- Tagging + priority scoring
- Assisted application autofill (with manual confirmation)
- Resume & project matching for written-answer fields

🔒 Notes
---

Scoutly never submits applications automatically.
It only extracts and logs job information so users can stay organized and intentional.

<div align="center"> MIT License • Made for developers on the job hunt </div>
