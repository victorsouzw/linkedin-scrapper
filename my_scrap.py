import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
from datetime import date

client = requests.Session()

HOMEPAGE_URL = 'https://www.linkedin.com'
LOGIN_URL = 'https://www.linkedin.com/checkpoint/lg/login-submit'

def salvar_detalhes_vaga(detalhes_vaga : json, url_vaga):
    titulo = detalhes_vaga['title']
    nova_vaga = {
        'titulo': [detalhes_vaga['title']],
        'descricao': [detalhes_vaga['description']['text']],
        'url_de_aplicacao': [url_vaga],
        'vaga_remota':[detalhes_vaga['workRemoteAllowed']],
        'data_de_busca': [date.today()]
    }

    excel_path = 'vagas.xlsx'

    try:
        df_existente = pd.read_excel(excel_path)
        df_novos = pd.DataFrame(nova_vaga)
        df_final = pd.concat([df_existente, df_novos], ignore_index=True)
        
        with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
            df_final.to_excel(writer, index=False)


        print(f'Dados da vaga com o titulo {titulo} foram adicionados ao arquivo {excel_path}')


    except FileNotFoundError:
        df_novos = pd.DataFrame(nova_vaga)
        df_novos.to_excel(excel_path, index=False, engine='xlsxwriter')
        
        print(f'Dados da vaga com o titulo {titulo} foram adicionados ao arquivo {excel_path}')

    except Exception as e:
        print(f'Ocorreu um erro: {str(e)}')

def extrair_detalhes_vaga(vaga_items):
    for item in vaga_items:
        try:
            item_json = json.loads(item.text)

            if 'data' in item_json and 'applyMethod' in item_json['data']:
                return item_json['data']

        except Exception:
            pass        
    return None

html = client.get(HOMEPAGE_URL).content
soup = BeautifulSoup(html, "html.parser")
csrf = soup.find('input', {"name":"loginCsrfParam"})['value']

file = open('senha.txt', 'r')
login_information = {
    'session_key':'starr6438@uorak.com', ###ALTERAR EMAIL
    'session_password': file.read(),
    'loginCsrfParam': csrf,
}
file.close()

result_login = client.post(LOGIN_URL, data=login_information)
result_login_soup = BeautifulSoup(result_login.content, "html.parser")
if result_login_soup.find(id='captchaInternalPath') is not None:
    raise Exception("O LinkedIn considerou o login suspeito. Solicitando um confirmação por código que foi enviado ao respectivo email. A resposta ao pin challenge não foi implementada.")

# TODO deixar melhor a forma de adicionar a query
keyword = input("Digite o a sua busca vaga como buscaria no LinkedIn: ")
numero_paginas = int(input("Digite o numero de paginas que deseja buscar: "))
url_vagas_inicio = 'https://www.linkedin.com/search/results/all/?'
url_vagas_keywords = 'keywords='+keyword
url_vagas_final = '&origin=GLOBAL_SEARCH_HEADER&sid=JTP'



def extract_urls(data, key):
    if isinstance(data, dict):
        for k, v in data.items():
            if k == key and isinstance(v, str) and v.startswith('https') and 'NAVIGATION_JOB_CARD' in v:
                yield v
            elif isinstance(v, (dict, list)):
                yield from extract_urls(v, key)
    elif isinstance(data, list):
        for item in data:
            yield from extract_urls(item, key)

https_urls = list()

for i in range(0,numero_paginas):
    content = client.get(
        url_vagas_inicio + url_vagas_keywords + url_vagas_final + '&refres=true&start=' + str(25 * i)).content
    soup = BeautifulSoup(content, "html.parser")
    bpr_guid_tags = soup.select('code[id^="bpr-guid"]')
    data = json.loads(str(bpr_guid_tags[-1].text).strip())

    https_urls_dentro = (list(extract_urls(data, 'url')))
    for url in https_urls_dentro:
        if url not in https_urls:
            https_urls.append(url)

for url in https_urls:
    # Send a GET request to the URL
    response = client.get(url)

    # Parse the response content with BeautifulSoup
    soup = BeautifulSoup(response.content, "html.parser")

    vaga_items = soup.find_all('code')
    detalhes_vaga = extrair_detalhes_vaga(vaga_items)
    if detalhes_vaga != None:
        salvar_detalhes_vaga(detalhes_vaga, url)