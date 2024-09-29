import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO, BytesIO
import zipfile
from matplotlib.backends.backend_pdf import PdfPages
import os

PATHCSV = os.path.join(os.path.dirname(__file__), '../data/taco.csv')
tabelaTaco = pd.read_csv(PATHCSV, on_bad_lines='skip')

def toCsv(df, data):
    buffer = StringIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)
    return buffer.getvalue()

def toExcel(df, data):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Resultados')
    buffer.seek(0)
    return buffer.getvalue()

def getPlotImage(fig):
    imgBytes = BytesIO()
    fig.savefig(imgBytes, format='png')
    imgBytes.seek(0)
    return imgBytes

def createZipWithPlotsAndCsv(figsAndTitles, csvData, nomeCsv):
    zipBuffer = BytesIO()
    with zipfile.ZipFile(zipBuffer, 'w', zipfile.ZIP_DEFLATED) as zipFile:
        for fig, title in figsAndTitles:
            imgBytes = getPlotImage(fig)
            zipFile.writestr(f'{title}.png', imgBytes.getvalue())
        zipFile.writestr(f'{nomeCsv}.csv', csvData)
    zipBuffer.seek(0)
    return zipBuffer.getvalue()

def createPdfWithPlots(figsAndTitles):
    pdfBuffer = BytesIO()
    with PdfPages(pdfBuffer) as pdf:
        for fig, title in figsAndTitles:
            pdf.savefig(fig)
    pdfBuffer.seek(0)
    return pdfBuffer.getvalue()

def main():
    st.title("Selecionador de Alimentos")

    opcoes = tabelaTaco['Nome'].unique()

    if 'alimentosSelecionados' not in st.session_state:
        st.session_state.alimentosSelecionados = []
        st.session_state.tabelaConfirmada = False
        st.session_state.referenciasArmazenadas = []

    novosSelecionados = st.multiselect(
        "Selecione os alimentos:",
        opcoes,
        default=st.session_state.alimentosSelecionados
    )


    dataSelecionada = st.date_input("Selecione a data:")
    data_formatada = dataSelecionada.strftime("%d/%m/%Y")

    if st.button("Exibir Seleção de Alimentos"):
        if not novosSelecionados:
            st.error("Nenhum alimento foi selecionado. Por favor, selecione ao menos um alimento.")
        else:
            st.session_state.alimentosSelecionados = novosSelecionados
            st.session_state.tabelaConfirmada = True

    if st.button("Salvar Refeições"):
        if not novosSelecionados:
            st.error("Não é possível salvar uma refeição sem alimentos. Selecione pelo menos um alimento.")
        else:
            refeicao = {
                'data': data_formatada,
                'alimentos': novosSelecionados
            }
            st.session_state.referenciasArmazenadas.append(refeicao)
            st.write("Refeição salva com sucesso!")

    if st.button("Limpar Lista de Alimentos"):
        st.session_state.alimentosSelecionados = []
        st.session_state.tabelaConfirmada = False
        st.rerun()

    if st.session_state.tabelaConfirmada:
        tabelaFiltrada = tabelaTaco[tabelaTaco['Nome'].isin(st.session_state.alimentosSelecionados)]

        todasAsColunas = [col for col in tabelaTaco.columns if col not in ['id', 'Nome']]
        
        colunasSelecionadas = st.multiselect(
            "Selecione as colunas para consulta:",
            todasAsColunas,
            default=['Energia (kcal)', 'Proteína (g)', 'Lipídeos (g)', 'Colesterol (mg)', 'Carboidrato (g)', 'Fibra Alimentar (g)']
        )

        if not colunasSelecionadas:
            st.error("Nenhuma coluna foi selecionada. Por favor, selecione ao menos uma coluna.")
            return

        colunasSelecionadas.insert(0, 'Nome')

        tabelaFiltrada = tabelaFiltrada[colunasSelecionadas]

        for coluna in colunasSelecionadas[2:]:  
            tabelaFiltrada[coluna] = pd.to_numeric(tabelaFiltrada[coluna], errors='coerce').fillna(0)

        tabelaFiltrada = tabelaFiltrada[(tabelaFiltrada[colunasSelecionadas[2:]] > 0).any(axis=1)]

        somaNutrientes = tabelaFiltrada.drop(columns=['Nome']).sum()

        st.write("Tabela de nutrientes dos alimentos selecionados:")
        st.dataframe(tabelaFiltrada)

        figBar, axBar = plt.subplots(figsize=(10, 7))
        tabelaFiltrada.set_index('Nome')[colunasSelecionadas[2:]].plot(kind='barh', stacked=True, ax=axBar)
        axBar.set_title("Total de Nutrientes por Alimento")
        axBar.set_xlabel("Quantidade")
        axBar.set_ylabel("Alimento")
        axBar.legend(title="Nutrientes")
        st.pyplot(figBar)

        figsAndTitles = []
        for coluna in colunasSelecionadas[2:]:
            dados = tabelaFiltrada[['Nome', coluna]]
            dados = dados[dados[coluna] > 0]
            dadosGrouped = dados.groupby('Nome').sum()

            if not dadosGrouped.empty:
                figPie, axPie = plt.subplots()
                axPie.pie(dadosGrouped[coluna], labels=dadosGrouped.index, autopct='%1.1f%%', startangle=90)
                axPie.set_title(f"{coluna} (Total: {somaNutrientes[coluna]:.2f})")
                figsAndTitles.append((figPie, f"graficoPizza_{coluna}"))
                st.pyplot(figPie)
                st.write(f"Total geral para {coluna}: {somaNutrientes[coluna]:.2f}")
            else:
                st.write(f"Gráfico de {coluna}:")
                st.write("Não há nenhum alimento com este nutriente")

        nomeArquivo = f"dadosRefeicao_{dataSelecionada.strftime('%d-%m-%Y')}" 

        csv = toCsv(tabelaFiltrada, nomeArquivo)
        st.download_button(
            label="Baixar Tabela como CSV",
            data=csv,
            file_name=f'{nomeArquivo}.csv',
            mime='text/csv'
        )

        excel = toExcel(tabelaFiltrada, nomeArquivo)
        st.download_button(
            label="Baixar Tabela como Excel",
            data=excel,
            file_name=f'{nomeArquivo}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

        pdfFile = createPdfWithPlots(figsAndTitles)
        st.download_button(
            label="Baixar Todos os Gráficos em PDF",
            data=pdfFile,
            file_name=f'{nomeArquivo}_graficos.pdf',
            mime='application/pdf'
        )

        zipFile = createZipWithPlotsAndCsv(figsAndTitles, csv, nomeArquivo)
        st.download_button(
            label="Baixar Todos os Gráficos e Tabela como ZIP",
            data=zipFile,
            file_name=f'{nomeArquivo}_graficos_e_csv.zip',
            mime='application/zip'
        )

main()
