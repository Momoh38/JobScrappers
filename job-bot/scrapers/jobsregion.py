"""
jobsregion.py - Scrapes ALL job listings from Jobsregion.com
UPDATED: Scrapes from sitemap and homepage to get every job post
"""

import re
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def scrape_jobsregion():
    """Scrape ALL job listings from Jobsregion.com"""
    jobs = []
    seen_urls = set()
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    
    # Method 1: Try to get sitemap
    sitemap_urls = [
        "https://www.jobsregion.com/sitemap.xml",
        "https://www.jobsregion.com/post-sitemap.xml",
        "https://jobsregion.com/sitemap.xml",
    ]
    
    all_post_urls = []
    
    for sitemap_url in sitemap_urls:
        try:
            response = requests.get(sitemap_url, headers=headers, timeout=30)
            if response.status_code == 200:
                print(f"     📍 Found sitemap: {sitemap_url}")
                # Parse sitemap XML
                soup = BeautifulSoup(response.text, 'xml')
                for loc in soup.find_all('loc'):
                    url = loc.text
                    if 'jobsregion.com' in url and '/job-' not in url and '/vacancy' in url.lower():
                        all_post_urls.append(url)
                break
        except:
            continue
    
    # Method 2: Scrape homepage for job links
    if not all_post_urls:
        try:
            response = requests.get("https://www.jobsregion.com", headers=headers, timeout=30)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                all_links = soup.find_all('a', href=True)
                
                for link in all_links:
                    href = link.get('href', '')
                    text = link.get_text(strip=True)
                    
                    # Look for job post patterns
                    if href and ('/job-' in href or '/vacancy' in href or '/recruitment' in href):
                        if href.startswith('/'):
                            full_url = f"https://www.jobsregion.com{href}"
                        elif href.startswith('http'):
                            full_url = href
                        else:
                            continue
                        
                        if full_url not in seen_urls and len(text) > 5:
                            seen_urls.add(full_url)
                            all_post_urls.append(full_url)
        except Exception as e:
            print(f"     ⚠️ Homepage scrape error: {e}")
    
    # Method 3: Try category pages
    category_urls = [
        "https://www.jobsregion.com/category/jobs/",
        "https://www.jobsregion.com/category/vacancies/",
        "https://www.jobsregion.com/jobs/",
    ]
    
    for cat_url in category_urls:
        try:
            response = requests.get(cat_url, headers=headers, timeout=30)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                for link in soup.find_all('a', href=True):
                    href = link.get('href', '')
                    if href and ('/job-' in href or '/vacancy' in href):
                        if href.startswith('/'):
                            full_url = f"https://www.jobsregion.com{href}"
                        elif href.startswith('http'):
                            full_url = href
                        else:
                            continue
                        
                        if full_url not in seen_urls:
                            seen_urls.add(full_url)
                            all_post_urls.append(full_url)
        except:
            continue
    
    print(f"     📍 Found {len(all_post_urls)} job post URLs")
    
    # Now scrape each job post URL
    for job_url in all_post_urls[:50]:  # Limit to 50 per run
        try:
            response = requests.get(job_url, headers=headers, timeout=30)
            if response.status_code != 200:
                continue
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title_elem = soup.find('h1')
            title = title_elem.get_text(strip=True) if title_elem else "Job Opportunity"
            
            # Extract company - look for common patterns
            company = "Not specified"
            company_patterns = [
                soup.find('a', class_=re.compile(r'company', re.I)),
                soup.find('span', class_=re.compile(r'company', re.I)),
                soup.find('div', class_=re.compile(r'company', re.I)),
                soup.find('strong', string=re.compile(r'Company', re.I)),
            ]
            for pattern in company_patterns:
                if pattern:
                    company = pattern.get_text(strip=True)
                    company = re.sub(r'^Company:?\s*', '', company, flags=re.I)
                    break
            
            # Extract location
            location = "Nigeria"
            location_elem = soup.find('span', class_=re.compile(r'location', re.I))
            if location_elem:
                location = location_elem.get_text(strip=True)
            else:
                loc_match = re.search(r'Location:\s*([^|\n]+)', response.text, re.I)
                if loc_match:
                    location = loc_match.group(1).strip()
            
            # Extract description
            desc_elem = soup.find('div', class_=re.compile(r'description|content|entry', re.I))
            if not desc_elem:
                desc_elem = soup.find('article')
            
            description = ""
            if desc_elem:
                for unwanted in desc_elem.find_all(['script', 'style', 'iframe']):
                    unwanted.decompose()
                description = desc_elem.get_text(strip=True)
                description = re.sub(r'\s+', ' ', description)
                description = description[:800]
            
            # Extract salary if available
            salary = ""
            salary_match = re.search(r'Salary:\s*([^|\n]+)', response.text, re.I)
            if salary_match:
                salary = salary_match.group(1).strip()
            elif '₦' in response.text:
                salary_match = re.search(r'[₦][\d,]+', response.text)
                if salary_match:
                    salary = salary_match.group(0)
            
            # Extract deadline
            deadline = ""
            deadline_match = re.search(r'Deadline:\s*([^|\n]+)', response.text, re.I)
            if deadline_match:
                deadline = deadline_match.group(1).strip()
            
            if job_url and title:
                job = {
                    'title': title[:150],
                    'company': company[:100],
                    'location': location[:100],
                    'description': description if description else "",
                    'salary': salary,
                    'url': job_url,
                    'source': 'Jobsregion',
                    'date_posted': datetime.now().isoformat(),
                    'tags': deadline if deadline else "",
                }
                jobs.append(job)
                
        except Exception as e:
            continue
    
    print(f"     📥 Jobsregion: {len(jobs)} job posts scraped")
    return jobs


if __name__ == "__main__":
    jobs = scrape_jobsregion()
    print(f"\n✅ Total: {len(jobs)} jobs")
    for job in jobs[:3]:
        print(f"\n📋 {job['title']}")
        print(f"   🏢 {job['company']}")
        print(f"   📍 {job['location']}")
        print(f"   🔗 {job['url']}")
