# Scoutly

**Paste a job link → Scoutly parses it → a new row appears in your job tracker.**

Scoutly is an AI agent that reads job postings from any career site (Workday, Greenhouse, Lever, etc.) and logs structured job details directly into a Google Sheet. It automates the most painful part of job searching: manually copying fields into a tracker.

---

## What Scoutly Does

- Accepts a job posting URL
- Fetches and reads the page
- Extracts structured job info (company, role, location, level, remote type, ATS type, job ID, etc.)
- Appends a row to a Google Sheet with the correct column order
- Leaves missing fields blank rather than fabricating values

---

## Architecture

User
↓
LlamaIndex Agent
↓
Tool Calls
├─ fetch_job_page(url)
├─ extract_job_info(text)
└─ log_job_to_sheet(record)

yaml
Copy code

The agent — not hardcoded pipeline logic — determines which tool to call and when.

---

## Schema

Scoutly writes each job entry using the following structure (column order should match your sheet):

Company
RoleTitle
Level
Location
RemoteType
JobURL
JobID
ATSType
PostedDate
ExperienceRequiredYears
Status
Tags
Notes

yaml
Copy code

---

## Tech Stack

- LlamaIndex (agent + structured extraction)
- OpenAI (configurable)
- Google Sheets API
- Optional: Playwright for JavaScript-rendered career sites

---

## Usage

```bash
python main.py "https://careers.company.com/job/12345"
```

Example output:

pgsql
Copy code
Logged Software Engineer — New Grad at Capital One to your tracker.
Roadmap
Dashboard for visualizing the job pipeline

Status updater (tracks OA / interviews / offers)

Tagging + priority scoring

Assisted application autofill (manual approval only)

Resume/project matching for tailored written answers

Notes
Scoutly does not submit job applications on behalf of the user.
It only extracts and logs job information to support organized and intentional job searching.

License
MIT

yaml
Copy code

---
- A GitHub description + tagline
- A logo + Figma color palette

Just say which one you want next.
