"""
scrapers/we_work_remotely_enhanced.py — Enhanced WWR with salary extraction
"""

import requests
import xml.etree.ElementTree as ET
import hashlib
import re

def scrape_wwr_enhanced() -> list:
    jobs = []
    headers = {"User-Agent": "HalalJobsBot/1.0"}
    
    # Additional categories not in original WWR
    more_categories = [
        ("All Remote", "https://weworkremotely.com/remote-jobs.rss"),
        ("Programming", "https://weworkremotely.com/categories/remote-programming-jobs.rss"),
        ("Customer Support", "https://weworkremotely.com/categories/remote-customer-support-jobs.rss"),
        ("Sales & Marketing", "https://weworkremotely.com/categories/remote-sales-and-marketing-jobs.rss"),
        ("Writing", "https://weworkremotely.com/categories/remote-writing-jobs.rss"),
    ]
    
    for category, feed_url in more_categories:
        try:
            response = requests.get(feed_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            
            for item in root.findall(".//item"):
                title = item.findtext("title", "")
                link = item.findtext("link", "")
                desc = item.findtext("description", "")
                
                # Extract company and role
                if ": " in title:
                    company, role = title.split(": ", 1)
                else:
                    company, role = "", title
                
                # Extract salary if mentioned
                salary_patterns = [
                    r'\$(\d+(?:,\d{3})*)\s*-\s*\$(\d+(?:,\d{3})*)',
                    r'\$(\d+(?:,\d{3})*)\/?(?:month|year|mo|yr)',
                    r'(\d+(?:,\d{3})*)\s*USD',
                ]
                
                salary = ""
                for pattern in salary_patterns:
                    match = re.search(pattern, desc, re.I)
                    if match:
                        if len(match.groups()) >= 2:
                            salary = f"${match.group(1)}-${match.group(2)} USD"
                        else:
                            salary = f"${match.group(1)}+ USD"
                        break
                
                if not salary:
                    salary = "Check listing"
                
                # Clean description
                desc = re.sub(r'<[^>]+>', ' ', desc)
                desc = re.sub(r'\s+', ' ', desc).strip()[:500]
                
                job_id = hashlib.md5(f"{link}{role}".encode()).hexdigest()
                
                jobs.append({
                    "id": f"wwr_enhanced_{job_id}",
                    "title": role.strip(),
                    "company": company.strip(),
                    "location": "Remote (Worldwide)",
                    "salary": salary,
                    "description": desc,
                    "tags": f"{category}, Remote, Worldwide",
                    "url": link,
                    "source": "WeWorkRemotely+",
                    "suitable_for_nigeria": "Yes",
                })
                
        except Exception as e:
            print(f"     ⚠️ WWR Enhanced {category} failed: {e}")
    
    # Deduplicate
    seen, unique = set(), []
    for job in jobs:
        if job["id"] not in seen:
            seen.add(job["id"])
            unique.append(job)
    
    return unique[:30]  # Limit to 30 most recent
