import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import zipfile
import io
import os

PATHCSV = os.path.join(os.path.dirname(__file__), '../data/taco.csv')
tabelaTaco = pd.read_csv(PATHCSV, on_bad_lines='skip').loc[:, ~pd.read_csv(PATHCSV, on_bad_lines='skip').columns.str.contains('^Unnamed')]

def main():
    st.title("Relatório Geral de Nutrientes")

    if 'referenciasArmazenadas' in st.session_state and st.session_state.referenciasArmazenadas:
        if st.button("Exibir Relatório Geral"):
            allMeals = []
            for refeicao in st.session_state.referenciasArmazenadas:
                alimentos = refeicao['alimentos']
                tabelaFiltrada = tabelaTaco[tabelaTaco['Nome'].isin(alimentos)]
                colunasDesejadas = ['Nome', 'Energia (kcal)', 'Proteína (g)', 'Lipídeos (g)', 'Colesterol (mg)', 'Carboidrato (g)', 'Fibra Alimentar (g)']
                tabelaFiltrada = tabelaFiltrada[colunasDesejadas]

                for coluna in colunasDesejadas[1:]:
                    tabelaFiltrada[coluna] = pd.to_numeric(tabelaFiltrada[coluna], errors='coerce').fillna(0)

                allMeals.append(tabelaFiltrada)

            allMealsDf = pd.concat(allMeals)
            nutrientesTotais = allMealsDf.groupby('Nome').sum()

            st.write("Total de Nutrientes por Alimento em Todas as Refeições")
            figTotal, axTotal = plt.subplots(figsize=(10, 7))
            nutrientesTotais.sum(axis=1).plot(kind='barh', ax=axTotal)
            axTotal.set_title("Total Geral de Nutrientes por Alimento")
            axTotal.set_xlabel("Quantidade Total")
            axTotal.set_ylabel("Alimento")
            st.pyplot(figTotal)

            nutrientes = ['Energia (kcal)', 'Proteína (g)', 'Lipídeos (g)', 'Colesterol (mg)', 'Carboidrato (g)', 'Fibra Alimentar (g)']

            pdfBuffer = io.BytesIO()
            with PdfPages(pdfBuffer) as pdf:
                for nutriente in nutrientes:
                    st.write(f"Relatório Geral de {nutriente}")

                    if not nutrientesTotais[nutriente].empty:
                        figBar, axBar = plt.subplots(figsize=(10, 7))
                        nutrientesTotais[nutriente].plot(kind='barh', ax=axBar)
                        axBar.set_title(f"Total de {nutriente} por Alimento em Todas as Refeições")
                        axBar.set_xlabel("Quantidade")
                        axBar.set_ylabel("Alimento")
                        st.pyplot(figBar)
                        pdf.savefig(figBar)
                        plt.close(figBar)
                    else:
                        st.write(f"Não foi encontrado nenhum alimento que contenha {nutriente}")

            st.download_button(
                label="Baixar Relatórios em PDF",
                data=pdfBuffer.getvalue(),
                file_name="relatoriosNutrientes.pdf",
                mime="application/pdf"
            )

            zipBuffer = io.BytesIO()
            with zipfile.ZipFile(zipBuffer, 'w') as zipFile:
                imgTotalBytes = io.BytesIO()
                figTotal.savefig(imgTotalBytes, format='png')
                imgTotalBytes.seek(0)
                zipFile.writestr('totalGeralNutrientes.png', imgTotalBytes.getvalue())
                
                for nutriente in nutrientes:
                    if not nutrientesTotais[nutriente].empty:
                        figBar, axBar = plt.subplots(figsize=(10, 7))
                        nutrientesTotais[nutriente].plot(kind='barh', ax=axBar)
                        axBar.set_title(f"Total de {nutriente} por Alimento em Todas as Refeições")
                        axBar.set_xlabel("Quantidade")
                        axBar.set_ylabel("Alimento")
                        
                        # Salvar o gráfico em memória e adicionar ao ZIP
                        imgBytes = io.BytesIO()
                        figBar.savefig(imgBytes, format='png')
                        imgBytes.seek(0)
                        zipFile.writestr(f'{nutriente.replace(" ", "_")}.png', imgBytes.getvalue())
                        plt.close(figBar)

            st.download_button(
                label="Baixar Relatórios em ZIP",
                data=zipBuffer.getvalue(),
                file_name="relatoriosNutrientes.zip",
                mime="application/zip"
            )
    else:
        st.write("Nenhuma refeição foi cadastrada ainda.")
        
main()
