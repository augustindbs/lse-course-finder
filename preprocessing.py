import pandas as pd
import requests
from bs4 import BeautifulSoup
import pickle

data = pd.ExcelFile('data/courses_data.xlsx')
departments = data.sheet_names

course_content_data = {}

def scrape_course_details(course_url_2025, course_url_2024):
    
    """
    Scrapes course details on the LSE website.

    Searches for data on the 2024-2025 website first, falls back to 2023-2024 otherwise.
    """
    
    try:
        response = requests.get(course_url_2025)
        response.raise_for_status()
    
    except requests.exceptions.HTTPError:
        response = requests.get(course_url_2024)
        response.raise_for_status()

    soup = BeautifulSoup(response.content, 'html.parser')

    content_div = soup.find('div', id='courseContent-Content')
    course_content = '\n'.join(p.get_text() for p in content_div.find_all('p')) if content_div else "Content not found."

    professor_div = soup.find('div', id='teacherResponsible-Content')
    professor_info = professor_div.get_text(strip=True) if professor_div else "Professor information not found."

    return course_content, professor_info

for department in departments:
    df = data.parse(department)
    df.set_index('Code', inplace = True)
    
    department_content = {}
    for index, row in df.iterrows():
        course_url_2025 = f"https://www.lse.ac.uk/resources/calendar2024-2025/courseGuides/{department[:2]}/2024_{index}.htm"
        course_url_2024 = f"https://www.lse.ac.uk/resources/calendar2023-2024/courseGuides/{department[:2]}/2023_{index}.htm"
        
        course_content, professor_info = scrape_course_details(course_url_2025, course_url_2024)
        department_content[index] = {
            'course_content': course_content,
            'professor_info': professor_info
        }
    
    course_content_data[department] = department_content

with open('data/course_content_data.pkl', 'wb') as file:
    pickle.dump(course_content_data, file)
