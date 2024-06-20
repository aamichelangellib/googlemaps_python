#Carregando bibliotecas

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import streamlit as st
from PIL import Image

from time import sleep
import pulp
import itertools

#-Últimas atualizações-------------------------------------------------------------------
#Atualizações com relação à versão original do código:

    #- O script agora pode rodar no Streamlit
    #- O usuario agora pode inserir até 5 endereços, sendo mas do que 2 e menos do que 5.
    #- O script pode ler distancias que demoram mais do que 60 min, somando as horas com os minutos
    #- Agora o usuario pode fazer escolas no metodo do cálculo, sendo 
    #possível otimizar a rota em função da Distância (Km) ou do Tempo(hrs, min).

#-----------------------------------------------------------------------------------------

#adicionando o destino e verificando abade rotas aberta ou não

def aba_de_rotas_aberta(): # função para verificar se a aba de rotas esta aberta/ativa
        xpath = "//button[@class='YismEf']" #Botão Fechar Rotas
        botao_fechar_rotas = driver.find_elements(By.XPATH, xpath)
        return len(botao_fechar_rotas) > 0

def adicionar_destino(endereco, num_caixa=1):
    
    if not aba_de_rotas_aberta():
        botao_buscar = driver.find_element(By.ID, 'searchboxinput')
        botao_buscar.clear()
        botao_buscar.send_keys(endereco)
        sleep(5)
        botao_buscar.send_keys(Keys.ENTER)
    else:
        xpath="//div[contains(@id, 'directions-searchbox')]//input"
        caixas = driver.find_elements(By.XPATH, xpath)
        caixas = [c for c in caixas if c.is_displayed()]
        if len(caixas) >= num_caixa:
            caixa_endereco = caixas[num_caixa-1]
            caixa_endereco.send_keys(Keys.CONTROL + 'a')
            caixa_endereco.send_keys(Keys.DELETE)
            caixa_endereco.send_keys(endereco)
            caixa_endereco.send_keys(Keys.ENTER)
        else:
            print(f'Não foi possível adicionar o endereço {len(caixas)} | {num_caixa}')

            #Encontrando o botão de 'rotas' e clicando no botao. Aqui é utilizado um elemento mais generico, por conta do idioma
def abrir_rotas():
    xpath = "//button[@class='g88MCb S9kvJb ' and @data-value='Rotas']"
    wait = WebDriverWait(driver, timeout=10)
    botao_rotas = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
    botao_rotas.click()

    #Adicionando mais caixas de destinos
def adicionar_caixa_destino():
    xpath = "//span[text()='Adicionar destino']"
    wait = WebDriverWait(driver, timeout=5)
    wait.until(EC.visibility_of_element_located((By.XPATH, xpath))) #este botão esta presente mas não visível, então devemos colocar dessa forma para garantir que só clicamos nele se esta visível
    caixa_adicionar_destino = driver.find_element(By.XPATH, xpath)
    caixa_adicionar_destino.click()

    #Definindo tipo de meio de transporte
def selecionar_tipo_conducao(tipo_conducao="Carro"):
    xpath = f'//img[@aria-label="{tipo_conducao}"]'
    wait = WebDriverWait(driver, timeout=10)
    botao_conducao = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
    botao_conducao.click()

    #Retornar tempo em minutos
def retornar_tempo():
    xpath = "//div[@id='section-directions-trip-0']//div[contains(text(),'min')]"
    wait = WebDriverWait(driver, timeout=10)
    tempo = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
    if 'h' in tempo.text: #Condicional para verificar se tempo do texto contem horas. Se tiver, separa o texto e suma horas com minutos
        parte = tempo.text.split(' h')
        horas = int(parte[0].strip())*60 #O comando strip() elimina tab ou espaços vazíos antes e depois do texto
        minutos = int(parte[1].replace(' min', '').strip())
        tempo_total = int(horas + minutos) 
    else: #Se não tiver h no texto, então apenas tirar min e converter o texto para numero inteiro
        tempo_total = int(tempo.text.replace(' min', ''))

    return tempo_total #Retornar operação

#Retornar distancia em kilometros
def retornar_distancia():
    xpath = "//div[@id='section-directions-trip-0']//div[contains(text(),'km')]"
    wait = WebDriverWait(driver, timeout=10)
    tempo = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
    return float(tempo.text.replace(' km', '').replace(',','.'))

#Mostrar lista de enderecos
def mostrar_lista_enderecos(enderecos):
    x = 0
    for i in range(len(enderecos)):
        print('endereco',i, ': ', enderecos[i])


#----------------------------FUNÇÕES PRINCIPAIS--------------------------------

#função para gerar pares de distancia em função do tempo
def gerar_pares_distancia_tempo(enderecos):

    distancia_pares = {}

    driver.get("https://www.google.com/maps/")
    adicionar_destino(enderecos[0], 1)
    abrir_rotas()
    selecionar_tipo_conducao(tipo_conducao="Carro")

    for i, end1 in enumerate(enderecos):
        adicionar_destino(end1, 1)
        for j, end2 in enumerate(enderecos):
            if i != j:
                adicionar_destino(end2, 2)
                tempo_par = retornar_tempo()
                distancia_pares[f'{i}_{j}'] = tempo_par

    return distancia_pares

#função para gerar pares de distancia em função da distancia (km)
def gerar_pares_distancia_distancia(enderecos):

    distancia_pares = {}

    driver.get("https://www.google.com/maps/")
    adicionar_destino(enderecos[0], 1)
    abrir_rotas()
    selecionar_tipo_conducao(tipo_conducao="Carro")

    for i, end1 in enumerate(enderecos):
        adicionar_destino(end1, 1)
        for j, end2 in enumerate(enderecos):
            if i != j:
                adicionar_destino(end2, 2)
                distancia_par = retornar_distancia()
                distancia_pares[f'{i}_{j}'] = distancia_par

    return distancia_pares

# Função para otimizar
def gerar_otimizacao(enderecos, distancia_pares):

    def distancia(end1, end2):
        return distancia_pares[f'{end1}_{end2}']
    
    prob = pulp.LpProblem('TSP', pulp.LpMinimize)

    x = pulp.LpVariable.dicts('x', [(i, j) for i in range(len(enderecos)) for j in range(len(enderecos)) if i != j], cat='Binary')

    prob += pulp.lpSum([distancia(i, j) * x[(i, j)] for i in range(len(enderecos)) for j in range(len(enderecos)) if i != j])

    for i in range(len(enderecos)):
        prob += pulp.lpSum([x[(i, j)] for j in range(len(enderecos)) if i != j]) == 1
        prob += pulp.lpSum([x[(j, i)] for j in range(len(enderecos)) if i != j]) == 1
 
    for k in range(len(enderecos)):
        for S in range(2, len(enderecos)):
            for subset in itertools.combinations([i for i in range(len(enderecos)) if i != k], S):
                prob += pulp.lpSum([x[(i, j)] for i in subset for j in subset if i != j]) <= len(subset) - 1
    
    prob.solve(pulp.PULP_CBC_CMD())

    solucao = []
    cidade_inicial = 0
    proxima_cidade = cidade_inicial
    while True:
        for j in range(len(enderecos)):
            if j != proxima_cidade and x[(proxima_cidade, j)].value() == 1:
               solucao.append((proxima_cidade, j))
               proxima_cidade = j
               break
        if proxima_cidade == cidade_inicial:
            break
    
    print('Rota sugerida:')
    for i in range(len(solucao)):
        print(solucao[i][0], ' ->> ', solucao[i][1])
    
    return solucao

#funcao para mostrar rota otimizada

def mostrar_rota_otimizada(enderecos, solucao):
    driver.get("https://www.google.com/maps")

    adicionar_destino(enderecos[0], 1)
    abrir_rotas()

    for i in range(len(solucao)):
        adicionar_destino(enderecos[solucao[i][0]], i+1)
        adicionar_caixa_destino()
    
    adicionar_destino(enderecos[0], len(enderecos) + 1)


#armazenando endereços
if __name__ == '__main__':
    
    # Configurando o título da página URL
    st.set_page_config(
        page_title="Otimizar Rotas com Google Maps",
        page_icon="📌",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Carregando uma imagem
    image = Image.open('./images/google_maps_image.png')

    # Inserindo a imagem na página utilizando os comandos do stremalit
    st.image(image, use_column_width=True)
    st.write("<div align='center'><h2><i>Otimizador de rotas do Google Maps</i></h2></div>",
            unsafe_allow_html=True)
    st.write("")
    st.write('Este aplicativo pode calcular até 5 endereços. Para utilizar este otimizador de rotas, por favor inserir os endereços exatos dos locais que serão visitados.')
    st.write('Após clicar no botão "Otimizar rotas" um outro navegador se abrirá e mostrará a rota otimizada.')
    st.write(' ')

    #input boxes para endereços
    end1 = st.text_input('Endereço 1 (será o inicio e final do percurso)')
    end2 = st.text_input('Endereço 2')
    end3 = st.text_input('Endereço 3')
    end4 = st.text_input('Endereço 4')
    end5 = st.text_input('Endereço 5')

    tipo_calculo = st.selectbox('Otimizar rota por', ['Tempo (hrs, min)', 'Distância (Km)'])

    #ao inves disso aqui é necessário criar um diccionario
    enderecos = list(filter(None, [end1, end2, end3, end4, end5]))

        # Verifica se há pelo menos dois endereços para calcular a rota
    if len(enderecos) < 2:
        st.warning("Por favor, insira pelo menos dois endereços para calcular a rota.")
    else:
        # Mostra os endereços que serão utilizados
        st.write("Endereços fornecidos:", enderecos)

    # enderecos = [
    #             'Marcelo Torcuato de Alvear 842, C1058AAL Cdad. Autónoma de Buenos Aires, Argentina' #endereço inicial/final
    #             , 'Av. de Mayo 1370, C1085 Cdad. Autónoma de Buenos Aires, Argentina'
    #             , 'Av. Hipólito Yrigoyen s/n, C1087 Cdad. Autónoma de Buenos Aires, Argentina'
    #             , 'Florida 165, San Martín 170, 1005 Buenos Aires, Argentina'
    #             , 'Laprida 1125, C1425 Cdad. Autónoma de Buenos Aires'
    #             ]

    # adicionar_destino(enderecos[0], 1)
    # abrir_rotas()

    # adicionar_destino(enderecos[0], 1)
    # adicionar_destino(enderecos[1], 2)

    # adicionar_caixa_destino()
    # adicionar_destino(enderecos[2], 3)
    # adicionar_caixa_destino()
    # adicionar_destino(enderecos[3], 4)

    # selecionar_tipo_conducao(tipo_conducao="Carro")
    # sleep(3)
    # selecionar_tipo_conducao(tipo_conducao="Bicicleta")

    # print(retornar_tempo())
    # print(retornar_distancia())
    
    botao_otimizar = st.button('Otimizar rotas')
    botao_otimizar

    if botao_otimizar and tipo_calculo == 'Tempo (hrs, min)':
            
        #Abrir o Google Maps com 1ra condicional
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service)
        driver.implicitly_wait(2)
        driver.get('https://www.google.com/maps/')

        distancia_pares = gerar_pares_distancia_tempo(enderecos)
        solucao = gerar_otimizacao(enderecos, distancia_pares)
        mostrar_rota_otimizada(enderecos, solucao)
        mostrar_lista_enderecos(enderecos)
        print(solucao)
        st.write('Otimização finalizada com sucesso!')
        st.write('Esta otimização foi calculada em função do tempo (hrs, min).')    
        for i in range(len(solucao)):
            st.write(solucao[i][0], ' ->> ', solucao[i][1])

    elif botao_otimizar and tipo_calculo == 'Distância (Km)':

        #Abrir o Google Maps com 2da condicional
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service)
        driver.implicitly_wait(2)
        driver.get('https://www.google.com/maps/')

        distancia_pares = gerar_pares_distancia_distancia(enderecos)
        solucao = gerar_otimizacao(enderecos, distancia_pares)
        mostrar_rota_otimizada(enderecos, solucao)
        mostrar_lista_enderecos(enderecos)
        print(solucao)
        st.write('Otimização finalizada com sucesso!')
        st.write('Esta otimização foi calculada em função da distância (Km).')      
        for i in range(len(solucao)):
            st.write(solucao[i][0], ' ->> ', solucao[i][1])
                
          

sleep(100)