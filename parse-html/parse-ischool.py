import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime
import json

## NOTES:
# - The I School course catalog structure is somewhat different from other UC Berkeley departments.
# need to fix for https://www.ischool.berkeley.edu/courses/info/247

# --- Configuration ---
BASE_URL = "https://www.ischool.berkeley.edu"
COURSE_CATALOGS = [
    "/courses/info",
    # Based on search results, uncomment these if you want to crawl other departments
    # "/courses/datasci",
    # "/courses/cyber",
]
SEMESTERS = ["fall", "spring"] # maybe add "summer" if needed
START_YEAR = datetime.now().year - 2 
END_YEAR = datetime.now().year + 1 

# Set headers to mimic a real browser to avoid potential blocking
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def generate_semester_urls(base_path):
    """
    Generates URLs for historical and future semester course schedules.
    Format: BASE_URL/courses/info/YEAR/SEMESTER
    """
    urls = []

    for year in range(START_YEAR, END_YEAR + 1):
        for semester in SEMESTERS:
            # Construct the path for a specific semester
            path = f"{base_path}/{year}/{semester}"
            url = f"{BASE_URL}{path}"
            urls.append(url)
    
    return urls

def fetch_html(url):
    """Fetches the HTML content for a given URL."""
    try:
        # print(f"Fetching: {url}")
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)c
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

DAY_MAP = {
    "Mo": "Monday",
    "Tu": "Tuesday",
    "We": "Wednesday",
    "Th": "Thursday",
    "Fr": "Friday"
}

def parse_days(day_string):
    """
    Converts a day string like 'MoWe' or 'TuTh' into a list of full weekday names.
    """
    if not day_string:
        return []
    
    days = []
    i = 0
    while i < len(day_string):
        # check 2-character abbreviation
        abbrev = day_string[i:i+2]
        if abbrev in DAY_MAP:
            days.append(DAY_MAP[abbrev])
            i += 2
        else:
            i += 1
    return days

def parse_lab_section_info(lab_string):
    """
    Parses lab/discussion section information from a given string.
    Expected format: "Discussion 1 Mo 2:00 pm - 3:00 pm — Location Instructor(s): Name"
    """
    pattern = re.compile(
        r'(?P<section_type>Discussion\s*\d*|Laboratory\s*\d*)\s*'
        r'(?P<days>[A-Za-z]+)\s+'
        r'(?P<start>\d{1,2}:\d{2}\s*(?:am|pm))\s*-\s*'
        r'(?P<end>\d{1,2}:\d{2}\s*(?:am|pm))\s*—\s*'
        r'(?P<location>.*?)\s*Instructor\(s\):\s*(?P<instructor>[A-Za-z .-]+)',
        flags=re.IGNORECASE
    )
    
    match = pattern.search(lab_string)
    if match:
        days_list = parse_days(match.group('days'))
        return {
            "section_type": match.group('section_type').strip(),
            "days": days_list,
            "start_time": match.group('start').strip(),
            "end_time": match.group('end').strip(),
            "location": match.group('location').strip(),
            "instructor": match.group('instructor').strip()
        }
    return None

def parse_course_page(html_content):
    if not html_content:
        return []

    soup = BeautifulSoup(html_content, 'html.parser')

    output = {
        "prerequisites": {
            "text": "",
            "courses": []
        },
        "requirements-satisfied": []
    }

    course_elements = soup.find_all(lambda tag: (
        (tag.name == "div"
        and tag.get("class") is not None
        and "pane-node-field-course-prerequisites" in tag.get('class')
        and tag.find("h2", string="Prerequisites"))
        or 
        (tag.name == "div"
         and tag.get("class") is not None
         and "pane-node-field-course-req-satisfied" in tag.get('class')
        and tag.find("h2", string="Requirements Satisfied"))
    ))

    if not course_elements:
        return output

    for element in course_elements:
        if "pane-node-field-course-prerequisites" in element.get('class'):
            prereq_text = element.get_text(strip=True, separator=' ').replace("Prerequisites", "").strip()
            output["prerequisites"]["text"] = prereq_text

            # Extract course codes from the prerequisite text
            course_codes = re.findall(r'[A-Z]+\s*C?[0-9]{1,3}[A-Z]*', prereq_text, flags=re.IGNORECASE)
            output["prerequisites"]["courses"] = list(set(course_codes))  # unique course codes
        elif "pane-node-field-course-req-satisfied" in element.get('class'):
            req_soup = BeautifulSoup(str(element), 'html.parser')
            req_items = req_soup.find_all('div', class_='field__item') 
            req_texts = [item.get_text(strip=True, separator=' ') for item in req_items]
            output["requirements-satisfied"] = req_texts

    return output

def parse_semester_page(html_content, semester_info):
    """
    Parses a single course schedule page for a given semester to extract course details.
    
    The structure of the course listing seems to be:
    - Course blocks often contain the title/code followed by description and sections.
    - We look for a consistent structure (e.g., div with class 'course-listing' or similar)
      or strong tags containing the course code.
    """
    if not html_content:
        return []

    soup = BeautifulSoup(html_content, 'html.parser')
    courses = []
    
    # Find all elements that look like a course title/header.
    # We will look for <h3> or <h4> containing the course code pattern (e.g., "Info XXX").
    # The I School site often uses <h3> or simple divs for course headers.
    
    # A robust selector targets any element with a class name indicating a course listing
    # or the strong tag wrapping the course title/ID based on past observations of UC Berkeley sites.
    
    # Find all elements that contain course title and unit number
    course_elements = soup.find_all(lambda tag: (
        tag.name == "div"
        and tag.get('class') == ['views-row']
        and tag.find("span", class_="course-title")
        and tag.find("div", class_="views-field views-field-field-ci-section")
        and tag.find("div", class_="views-field views-field-nothing-1")
    ))

    if not course_elements:
        # Fallback: Check for strong tags that contain a course ID (e.g., "Info C8.")
        course_elements = soup.find_all('p')
        course_elements.extend(soup.find_all('li'))
        
    for element in course_elements:
        
        # 1. Extract Title, Code, and Units
        # Search the element text for patterns like "Info 101. Title (X units)"
        full_text = element.get_text(strip=True, separator='  ')
        
        # Regex to capture Course ID (e.g., Info 101), Title, and Units
        match = re.search(r'(?P<id>[A-Za-z]+\s*C?[0-9]{1,3}[A-Z]*)\.\s*(?P<title>.+?)\s*(?P<units>\(\d+(?:[-–]\d+)?\s*units\))', full_text, flags=re.IGNORECASE)

        if match:
            course_id = match.group('id').strip()
            title = match.group('title').strip()
            units = match.group('units').replace('(', '').replace(')', '').replace(' units', '').strip()
            if re.search(r'[-–]', units):
                units = [float(num) for num in re.split(r'[-–]', units)]
            else:
                units = float(units)
        else:
            continue

        # 2. Extract Description
        # The description is usually the text immediately following the title/units.
        # We assume the first significant block of text after the title is the description.
        after_units = full_text.split(match.group('units'), 1)[1].strip()
        after_units = re.sub(r'more information', '', after_units, flags=re.IGNORECASE) # remove more infomation
        description = re.split(r'(\s\sSection\s+\d+)', after_units)
        after_description = "".join(description[1:]).replace('\n', ' ').strip()
        description = description[0].strip()
        
        # 3. Extract Sections
        sections = []

        section_regex = re.compile(
            # Matches "Section X" (MANDATORY)
            r'Section\s*(?P<section_number>\d+)\s*'
            
            # --- START OPTIONAL SCHEDULE/LOCATION BLOCK ---
            r'(?:' 
                # Matches Schedule (e.g., MoWe 10:00 am - 11:30 am)
                # We assume if DAYS are present, START and END times must follow.
                r'(?P<days>[A-Za-z]+)\s+'
                r'(?P<start>\d{1,2}:\d{2}\s*(?:am|pm))\s*-\s*'
                r'(?P<end>\d{1,2}:\d{2}\s*(?:am|pm))\s*'
                
                # Matches Location (e.g., — 202 South Hall). This part is optional
                # only if the schedule portion above was matched.
                r'(?:—\s*(?P<location>.*?)\s*)?'
                
            r')?' 
            # --- END OPTIONAL BLOCK (The '?' makes everything inside optional) ---

            # Matches Instructor label (MANDATORY, starts immediately after section/location or time/location)
            r'Instructor\(s\):\s*'
            # NON-GREEDY RAW TEXT CAPTURE: Captures all remaining details
            r'(?P<raw_text>.*?)'
            # STOP BOUNDARY (Positive Lookahead)
            r'(?=Section\s*\d+|$)',
            flags=re.IGNORECASE | re.DOTALL 
        )

        matches = section_regex.finditer(after_description)
        if len(list(section_regex.finditer(after_description))) == 0:
            print(f"Full text for debugging:\n{after_description}")
            print(title+"\n"+"-"*40)

        for m in matches:
            days_list = parse_days(m.group('days'))  # map to list
            
            # instructor extraction
            raw_text = m.group("raw_text").strip()
            split_raw = raw_text.split("  ")
            instructor = split_raw[0].strip()
            if ',' in instructor:
                instructor = instructor.split(',')

            notes = ''
            lab_section_info = "N/A"
            
            if len(split_raw) > 1:
                raw_text = "  ".join(split_raw[1:]).strip()

            if 'discussions and labs' in raw_text.lower():
                extra_info = raw_text.split("discussions and labs")
                if len(extra_info) > 1:
                    notes = extra_info[0].strip()
                    lab_text = extra_info[1].strip()
                else:
                    lab_text = extra_info[0].strip()

                lab_section_info = parse_lab_section_info(lab_text)

            sections.append({
                "section_number": int(m.group('section_number')),
                "instructor": instructor,
                "days": days_list,
                "start_time": m.group('start').strip() if m.group('start') else "N/A",
                "end_time": m.group('end').strip() if m.group('end') else "N/A",
                "location": m.group('location').strip() if m.group('location') else "N/A",
                "notes": notes,
                "lab_section_info": lab_section_info
            })

        # Extract Prequisites if available
        course_href = element.find("a")["href"]
        course_html = fetch_html(f"{BASE_URL}{course_href}")
        course_content = parse_course_page(course_html)

        courses.append({
            "course_id": course_id,
            "title": title,
            "units": units,
            "description": description,
            "prerequisites": course_content.get("prerequisites", {}),
            "requirements_satisfied": course_content.get("requirements-satisfied", []),
            "sections": sections,
            "catalog_path": semester_info.get('catalog_path'), # maybe convert to dept later
            "year": semester_info.get('year'),
            "semester": semester_info.get('semester'),
            "source_url": semester_info.get('url')
        })

    #print(json.dumps(courses[11], indent=4))
    return courses


def run_full_crawl():
    """
    Step 3: Orchestrates the full crawling process across all specified catalogs and semesters.
    """
    all_courses = []
    
    for catalog_path in COURSE_CATALOGS:
        semester_urls = generate_semester_urls(catalog_path)
        
        for url in semester_urls:
            
            # Determine semester and year from the URL for metadata
            parts = url.split('/')
            
            # Default to 'catalog' if not a specific semester page
            semester = parts[-1] if parts[-1] in SEMESTERS else 'catalog'
            year = parts[-2] if parts[-2].isdigit() else 'N/A'
            
            # Only proceed if we have a valid year/catalog to identify the page
            if year != 'N/A' or semester == 'catalog': 
                
                semester_info = {
                    "catalog_path": catalog_path,
                    "url": url,
                    "year": year if year.isdigit() else 'N/A',
                    "semester": semester,
                }
                
                html_content = fetch_html(url)
                if html_content:
                    courses = parse_semester_page(html_content, semester_info)
                    
                    if courses:
                        print(f"-> Successfully extracted {len(courses)} courses from {url}")
                        all_courses.extend(courses)
                    else:
                        print(f"-> No courses found or page structure changed for {url}. Skipping.")
                
    
    # Save results to a JSON file
    output_filename = 'ischool_courses_data.json'
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(all_courses, f, ensure_ascii=False, indent=4)
        
    print(f"\n==============================================")
    print(f"Crawl finished. Total courses extracted: {len(all_courses)}")
    print(f"Data saved to {output_filename}")
    print(f"==============================================")
    
    return all_courses

if __name__ == '__main__':
    run_full_crawl()
    # parse_course_page(fetch_html("https://www.ischool.berkeley.edu/courses/info/247"))
    # parse_semester_page(fetch_html("https://www.ischool.berkeley.edu/courses/info/2026/spring"), {
    #     "catalog_path": "/courses/info",
    #     "url": "https://www.ischool.berkeley.edu/courses/info/2026/spring",
    #     "year": "2026",
    #     "semester": "spring",
    # })