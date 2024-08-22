import streamlit as st
import pandas as pd
import pickle

@st.cache_data(ttl = 3600)

def load_course_content_data():
    with open('data/course_content_data.pkl', 'rb') as file:
        return pickle.load(file)

course_content_data = load_course_content_data()

data = pd.ExcelFile('data/courses_data.xlsx')
departments = sorted(data.sheet_names)

courses_data = {}

for department in departments:
    df = data.parse(department)
    df.set_index('Code', inplace = True)
    courses_data[department] = df

if 'show_filter' not in st.session_state:
    st.session_state.show_filter = False

if 'show_keyword_search' not in st.session_state:
    st.session_state.show_keyword_search = False

with st.sidebar:
    st.image('data/lse_logo.png', width = 100)
    st.write("\n")
    
    st.markdown("## Individual Course Pages")
    st.write("\n")

    selected_department = st.selectbox("Choose your department:", departments)
    df_selected_department = courses_data[selected_department]

    df_selected_department['Code & Name'] = df_selected_department.index + ' - ' + df_selected_department['Course Name']
    selected_course = st.selectbox("Choose your course:", df_selected_department['Code & Name'], on_change = lambda: st.session_state.update(show_filter = False, show_keyword_search = False))

    st.markdown("___")
    st.write('## Browsing Options')
    st.write("\n")

    if st.button("Filter and Rank", type = 'primary', use_container_width = True):
        st.session_state.show_filter = True
        st.session_state.show_keyword_search = False

    if st.button("Keyword Search", type = 'primary', use_container_width = True):
        st.session_state.show_keyword_search = True
        st.session_state.show_filter = False

if st.session_state.show_filter:
    st.write("### Browse and Filter Courses")
    st.markdown("___")

    selected_filter_department = st.selectbox("Choose a department:", ['All Departments'] + departments)
    
    if selected_filter_department == 'All Departments':
        df_filter_department = pd.concat(courses_data.values())
    else:
        df_filter_department = courses_data[selected_filter_department]

    unit_filter = st.selectbox("Unit Value", ["Display All", 0.5, 1])
    st.write('\n')
    coursework_filter = st.slider("Minimum Coursework %", 0, 100, 0, step = 5)

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
        'Mean (2024)': 'Mean',
        '1 (2024)': 'First-Class %',
        'Coursework %': 'Coursework'
    }, inplace = True)

    st.write("\n")
    st.write('##### Click on table columns to sort courses by relevant filters')
    st.write("\n")

    st.dataframe(filtered_courses[['Course', 'Units', 'Mean', 'First-Class %', 'Coursework']], height = 600, width = 1000, column_config = {"Course": st.column_config.Column(width = 330)})

elif st.session_state.show_keyword_search:
    st.write("### Keyword Search")
    st.markdown("___")

    keyword = st.text_input("Enter keyword(s) to search:")

    if keyword:
        keyword_lower = keyword.lower()
        search_results = []

        for department, df in courses_data.items():
            df['Course Content'] = df.index.map(lambda course_code: course_content_data[department].get(course_code, {}).get('course_content', 'Content not found.'))

            df_filtered = df[df['Course Name'].str.contains(keyword_lower, case = False) | df['Course Content'].str.contains(keyword_lower, case = False)]

            if not df_filtered.empty:
                df_filtered['Department'] = department
                search_results.append(df_filtered)

        if search_results:
            search_results_df = pd.concat(search_results)

            search_results_df['Coursework %'] = (search_results_df['Coursework %'] * 100).astype(int).astype(str) + '%'
            search_results_df['Participation %'] = (search_results_df['Participation %'] * 100).astype(int).astype(str) + '%'
            search_results_df['Exam %'] = (search_results_df['Exam %'] * 100).astype(int).astype(str) + '%'
            search_results_df['1 (2024)'] = (search_results_df['1 (2024)'] * 100).astype(int).astype(str) + '%'

            search_results_df.rename(columns = {
                'Course Name': 'Course',
                'Unit Value': 'Units',
                'Mean (2024)': 'Mean',
                '1 (2024)': 'First-Class %',
                'Coursework %': 'Coursework'
            }, inplace = True)

            st.write(f"#### Results for '{keyword}':")
            st.write("\n")
            st.dataframe(search_results_df[['Course', 'Units', 'Mean', 'First-Class %', 'Coursework']], height = 600, width = 1000, column_config = {"Course": st.column_config.Column(width = 330)})
 
        else:
            st.write(f"No results found for '{keyword}'.")

else:
    selected_course_code = selected_course.split(" - ")[0]

    unit_value = df_selected_department.loc[selected_course_code, 'Unit Value']
    unit_label = "(Half Unit)" if unit_value == 0.5 else "(Full Unit)" if unit_value == 1 else ""

    department_code = selected_department[:2]

    course_content = course_content_data[selected_department][selected_course_code]['course_content']
    professor_info = course_content_data[selected_department][selected_course_code]['professor_info']

    key_statistics_columns = ['Marks (2024)', 'Mean (2024)', 'Max (2024)', 'Coursework %', 'Participation %', 'Exam %', 'Coursework Components', 'Exams']
    key_statistics = df_selected_department.loc[selected_course_code, key_statistics_columns]

    grades_columns = ['1 (2024)', '2A (2024)', '2B (2024)', '3 (2024)', 'P (2024)', 'F (2024)', 'AB (2024)']
    grades = df_selected_department.loc[selected_course_code, grades_columns]
    grades_df = pd.DataFrame({'Grade': ['1:1', '2:1', '2:2', '3', 'P', 'F', 'AB'], 'Frequency (%)': grades * 100})

    st.markdown(f"### {selected_course} <span style = 'color: red; font-size: 20px'> {unit_label} </span>", unsafe_allow_html = True)
    st.markdown("___")

    exams = key_statistics.get('Exams', 0)
    components = key_statistics.get('Coursework Components', 0)

    assessment_details = f"**Assessment:** {key_statistics['Exam %'] * 100}% Exam"

    if exams > 1:
        assessment_details += f" ({exams} Exams)"

    assessment_details += f" | {key_statistics['Coursework %'] * 100}% Coursework"

    if components > 1:
        assessment_details += f" ({components} Components)"

    assessment_details += f" | {key_statistics['Participation %'] * 100}% Class Participation"

    st.write(f"**Professor(s):** {professor_info}")
    st.write(assessment_details)
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

    st.bar_chart(grades_df.set_index('Grade'), color = '#8E0000', horizontal = True, height = 350, x_label = 'Frequency (%)', y_label = 'Grade Classification')