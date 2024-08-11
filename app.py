
import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

data = pd.ExcelFile('data/courses_data.xlsx')
departments = data.sheet_names

courses_data = {}

for department in departments:
    df = data.parse(department)
    df.set_index('Code', inplace = True)
    courses_data[department] = df

def scrape_course_details(course_url):
    
    """
    Scrape course content and professor info from the given URL.
    """
    
    try:
        response = requests.get(course_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        content_div = soup.find('div', id = 'courseContent-Content')

        if content_div:
            paragraphs = content_div.find_all('p')
            course_content = '\n'.join(p.get_text() for p in paragraphs)
        else:
            course_content = "Content not found."

        professor_div = soup.find('div', id = 'teacherResponsible-Content')

        if professor_div:
            professor_info = professor_div.get_text(strip = True)
        else:
            professor_info = "Professor information not found."
        
        return course_content, professor_info
        
    except Exception as e:
        return f"An error occurred: {e}", None

selected_department = st.sidebar.selectbox("Choose your department:", departments)
df_selected_department = courses_data[selected_department]

df_selected_department['Code & Name'] = df_selected_department.index + ' - ' + df_selected_department['Course Name']
selected_course = st.sidebar.selectbox("Choose your course:", df_selected_department['Code & Name'])

selected_course_code = selected_course.split(" - ")[0]

unit_value = df_selected_department.loc[selected_course_code, 'Unit Value']
unit_label = "(Half Unit)" if unit_value == 0.5 else "(Full Unit)" if unit_value == 1 else ""

base_url = 'https://www.lse.ac.uk/resources/calendar2023-2024/courseGuides/'
department_code = selected_department[:2]
course_url = f"{base_url}{department_code}/2023_{selected_course_code}.htm"
course_content, professor_info = scrape_course_details(course_url)

key_statistics_columns = ['Marks (2024)', 'Mean (2024)', 'Max (2024)', 'Coursework %', 'Participation %', 'Exam %', 'Coursework Components', 'Exams']
key_statistics = df_selected_department.loc[selected_course_code, key_statistics_columns]

grades_columns = ['1 (2024)', '2A (2024)', '2B (2024)', '3 (2024)', 'P (2024)', 'F (2024)', 'AB (2024)']
grades = df_selected_department.loc[selected_course_code, grades_columns]
grades_df = pd.DataFrame({'Grade': ['1:1', '2:1', '2:2', '3', 'P', 'F', 'AB'], 'Frequency (%)': grades * 100})

first_2024 = round(grades['1 (2024)'] * 100, 1)
fail_2024 = round(grades['F (2024)'] * 100, 1)

marks_2024 = key_statistics['Marks (2024)'] = int(key_statistics['Marks (2024)'])
mean_2024 = key_statistics['Mean (2024)'] = f"{key_statistics['Mean (2024)']:.1f}"
max_2024 = key_statistics['Max (2024)'] = int(key_statistics['Max (2024)'])
coursework = key_statistics['Coursework %'] = f"{int(key_statistics['Coursework %'] * 100)}%"
participation = key_statistics['Participation %'] = f"{int(key_statistics['Participation %'] * 100)}%"
exam = key_statistics['Exam %'] = f"{int(key_statistics['Exam %'] * 100)}%"
components = key_statistics['Coursework Components'] = int(key_statistics['Coursework Components'])
exams = key_statistics['Exams'] = int(key_statistics['Exams'])


# STREAMLIT STYLING


st.markdown(f"### {selected_course} <span style = 'color: red; font-size: 20px'> {unit_label} </span>", unsafe_allow_html = True)

st.markdown("___")
st.write(f"**Professor:** {professor_info}")
st.write(f"**Assessment:** {exam} Exam | {coursework} Coursework | {participation} Class Participation")
st.write("\n")

st.write("#### Course Content:")
st.markdown(f"""<div style = 'font-size: 14px;'> {course_content} </div>""", unsafe_allow_html = True)
st.write("\n")

st.write("#### Key Statistics (2023-2024):")
st.write("\n")
st.write(f"**Marks:** {marks_2024} | **Mean:** {mean_2024} | **Highest Grade:** {max_2024} | **First-Class Rate:** {first_2024}% | **Fail Rate**: {fail_2024}%")
st.write("\n")


st.write("#### Past Year Grade Distribution (2023-2024):")
st.write("\n")
st.bar_chart(grades_df.set_index('Grade'), color = '#8B0000', horizontal = True, height = 400, x_label = 'Frequency (%)', y_label = 'Grade Classification')
