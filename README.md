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

User → LlamaIndex Agent → Tool Calls
├ fetch_job_page(url)
├ extract_job_info(text)
└ log_job_to_sheet(record)

yaml
Copy code

The agent—not hardcoded logic—decides which tool to call and when.

---

## Schema

Scoutly writes jobs to the sheet using the following structure:

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

The Google Sheet should use this column order for best results.

---

## Tech Stack

- LlamaIndex (agent + structured extraction)
- OpenAI (configurable)
- Google Sheets API
- Optional: Playwright for JS-rendered sites

---

## Usage

```bash
python main.py "https://careers.company.com/job/12345"
Example response:

pgsql
Copy code
Logged Software Engineer — New Grad at Capital One to your tracker.
Roadmap
Dashboard for visualizing the job pipeline

Status updater (tracks OA / interviews / offers)

Tagging + priority scoring

Assisted application autofill (manual approval only)

Resume/project matching for custom written answers

Notes
Scoutly does not submit applications on your behalf.
It only extracts and logs job data so you can make intentional decisions during recruiting.

License
MIT

yaml
Copy code

---

If you want, I can now generate:
- A matching `.env.example` file
- Folder structure template
- Badges for the top of the README
- A GitHub description + tagline
- A logo + Figma color palette

Just say which one you want next.
