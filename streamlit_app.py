import streamlit as st

home = st.Page("./pages/home.py", title="Home")
newMeal = st.Page("./pages/meal.py", title="Consulta de Nutrientes")
report = st.Page("./pages/report.py", title="Relatório")

navbar = st.navigation({
        "Tenha o controle total da sua saúde": [home, newMeal, report]
})

navbar.run()
