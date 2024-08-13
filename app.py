
import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

data = pd.ExcelFile('data/courses_data.xlsx')
departments = data.sheet_names

courses_data = {}

for department in departments:
    df = data.parse(department)
    df.set_index('Code', inplace=True)
    courses_data[department] = df

def scrape_course_details(course_url):
    
    """
    Function to web-scrape course content and professor details directly from LSE website.
    """
    
    try:
        response = requests.get(course_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        content_div = soup.find('div', id = 'courseContent-Content')
        course_content = '\n'.join(p.get_text() for p in content_div.find_all('p')) if content_div else "Content not found."

        professor_div = soup.find('div', id = 'teacherResponsible-Content')
        professor_info = professor_div.get_text(strip = True) if professor_div else "Professor information not found."

        return course_content, professor_info
    
    except Exception as e:
        return f"An error occurred: {e}", None

if 'show_filter' not in st.session_state:
    st.session_state.show_filter = False

with st.sidebar:
    st.markdown("## Individual Course Pages")
    st.write("\n")

    selected_department = st.selectbox("Choose your department:", departments)
    df_selected_department = courses_data[selected_department]
    df_selected_department['Code & Name'] = df_selected_department.index + ' - ' + df_selected_department['Course Name']

    selected_course = st.selectbox("Choose your course:", df_selected_department['Code & Name'], on_change = lambda: st.session_state.update(show_filter = False))

    st.markdown("___")
    st.write('## Pragmatic Filtering')
    st.write("\n")
    
    if st.button("Browse and Filter Courses", type = 'primary'):
        st.session_state.show_filter = True

if st.session_state.show_filter:
    st.write("### Browse and Filter Courses")
    st.markdown("___")

    selected_filter_department = st.selectbox("Choose a department:", departments)
    df_filter_department = courses_data[selected_filter_department]

    unit_filter = st.selectbox("Unit Value", ["Display All", 0.5, 1])
    coursework_filter = st.slider("Minimum Coursework %", 0, 100, 0)

    filtered_courses = df_filter_department.copy()

    if unit_filter != "Display All":
        filtered_courses = filtered_courses[filtered_courses['Unit Value'] == unit_filter]

    filtered_courses = filtered_courses[
        filtered_courses['Coursework %'] >= coursework_filter / 100
    ]

    filtered_courses['Coursework %'] = (filtered_courses['Coursework %'] * 100).astype(int).astype(str) + '%'
    filtered_courses['Participation %'] = (filtered_courses['Participation %'] * 100).astype(int).astype(str) + '%'
    filtered_courses['Exam %'] = (filtered_courses['Exam %'] * 100).astype(int).astype(str) + '%'
    filtered_courses['1 (2024)'] = (filtered_courses['1 (2024)'] * 100).astype(int).astype(str) + '%'

    filtered_courses.rename(columns = {
        'Course Name': 'Course',
        'Unit Value': 'Units',
        'Mean (2024)': 'Mean Grade',
        '1 (2024)': 'First-Class Rate',
    }, inplace = True)

    st.write("\n")
    st.write('##### Click on table columns to sort courses by relevant filters')
    st.write("\n")

    st.dataframe(filtered_courses[['Course', 'Units', 'Mean Grade', 'First-Class Rate', 'Coursework %']], height = 500, width = 1000)

else:
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

    st.markdown(f"### {selected_course} <span style = 'color: red; font-size: 20px'> {unit_label} </span>", unsafe_allow_html = True)
    st.markdown("___")
    st.write(f"**Professor(s):** {professor_info}")
    st.write(f"**Assessment:** {key_statistics['Exam %'] * 100}% Exam | {key_statistics['Coursework %'] * 100}% Coursework | {key_statistics['Participation %'] * 100}% Class Participation")
    st.write("\n")

    st.write("#### Course Content:")
    st.markdown(f"<div style = 'font-size: 14px;'> {course_content} </div>", unsafe_allow_html = True)
    st.write("\n")

    st.write("#### Key Statistics (2023-2024):")
    st.write("\n")
    st.write(f"**Marks:** {int(key_statistics['Marks (2024)'])} | **Mean:** {key_statistics['Mean (2024)']:.1f} | **Highest Grade:** {int(key_statistics['Max (2024)'])} | **First-Class Rate:** {round(grades['1 (2024)'] * 100, 1)}% | **Fail Rate:** {round(grades['F (2024)'] * 100, 1)}%")
    st.write("\n")

    st.write("#### Past Year Grade Distribution (2023-2024):")
    st.write("\n")
    st.bar_chart(grades_df.set_index('Grade'), color = '#8B0000', horizontal = True, height = 400, x_label = 'Frequency (%)', y_label = 'Grade Classification')
