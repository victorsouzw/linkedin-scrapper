import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
from datetime import date



HOMEPAGE_URL = 'https://www.linkedin.com'
LOGIN_URL = 'https://www.linkedin.com/checkpoint/lg/login-submit'
client = requests.Session()

def get_nome_empresa(included_items):
    if included_items == None:
        return None
    
    for item in included_items:
        try:
            item_json = json.loads(item.text)

            if 'name' in item_json:
                return item_json['name']

        except Exception:
            pass        
    return None


def salvar_detalhes_vaga(detalhes_vaga : json, url_vaga, included : list):
    titulo = detalhes_vaga['title']
    empresa = get_nome_empresa(included)
    if empresa != None:
        id = str((titulo.encode() + empresa.encode()).hex())[:30]
    else: 
        id = str(titulo.encode().hex())[:30]

    nova_vaga = {
        'id': [id],
        'titulo': [detalhes_vaga['title']],
        'descricao': [detalhes_vaga['description']['text']],
        'url_de_aplicacao': [url_vaga],
        'vaga_remota':[detalhes_vaga['workRemoteAllowed']],
        'data_de_busca': [str(date.today())]
    }

    excel_path = 'vagas.xlsx'

    try:
        df_existente = pd.read_excel(excel_path)
        df_novos = pd.DataFrame(nova_vaga)
        df_final = pd.concat([df_existente, df_novos], ignore_index=True).drop_duplicates(subset='id', keep='first')
        
        with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
            df_final.to_excel(writer, index=False)

        with open('vagas.json', 'w', encoding='UTF-8') as f:
            json.dump(df_final.to_dict(orient= 'records'), f, ensure_ascii=False, indent=2)


        print(f'Dados da vaga com o titulo {titulo} foram adicionados ao arquivo vagas.json')


    except FileNotFoundError:
        df_novos = pd.DataFrame(nova_vaga)
        df_novos.to_excel(excel_path, index=False, engine='xlsxwriter')
        with open('vagas.json', 'w', encoding='UTF-8') as f:
            json.dump(df_novos.to_dict(orient= 'records'), f, ensure_ascii=False, indent=2)
        print(f'Dados da vaga com o titulo {titulo} foram adicionados ao arquivo vagas.json')

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

def extrair_included(vaga_items):
    for item in vaga_items:
        try:
            item_json = json.loads(item.text)

            if 'included' in item_json:
                return item_json['included']

        except Exception:
            pass        
    return None

def login(email, senha):
    global client
    html = client.get(HOMEPAGE_URL).content
    soup = BeautifulSoup(html, "html.parser")
    csrf = soup.find('input', {"name":"loginCsrfParam"})['value']

    login_information = {
        'session_key': email, ###ALTERAR EMAIL
        'session_password': senha,
        'loginCsrfParam': csrf,
    }

    result_login = client.post(LOGIN_URL, data=login_information)
    result_login_soup = BeautifulSoup(result_login.content, "html.parser")
    if result_login_soup.find(id='captchaInternalPath') is not None:
        raise Exception("O LinkedIn considerou o login suspeito. Solicitando um confirmação por código que foi enviado ao respectivo email. A resposta ao pin challenge não foi implementada.")


def extract_urls(data, key):
    if isinstance(data, dict):
        for k, v in data.items():
            if k == key and isinstance(v, str) and v.startswith('https://www.linkedin.com/jobs'):
                yield v
            elif isinstance(v, (dict, list)):
                yield from extract_urls(v, key)
    elif isinstance(data, list):
        for item in data:
            yield from extract_urls(item, key)



def gerar_urls(numero_paginas, url_busca):
    global client
    https_urls = list()
    for i in range(110, 210):
        page = str(25 * i)
        url_get = url_busca + '&refresh=true&start=' + page
        content = client.get(url_get).content
        soup = BeautifulSoup(content, "html.parser")
        bpr_guid_tags = soup.select('code[id^="bpr-guid"]')
        data = json.loads(str(bpr_guid_tags[-1].text).strip())

        https_urls_dentro = (list(extract_urls(data, 'actionTarget')))
        for url in https_urls_dentro:
            if url not in https_urls:
                https_urls.append(url)
    return https_urls

def buscar_e_salvar_vagas(numero_paginas, url_busca):
    global client
    https_urls = gerar_urls(numero_paginas, url_busca)
    for url in https_urls:
        # Send a GET request to the URL
        response = client.get(url)

        # Parse the response content with BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")

        vaga_items = soup.find_all('code')
        detalhes_vaga = extrair_detalhes_vaga(vaga_items)
        included = extrair_included(vaga_items)
        if detalhes_vaga != None:
            salvar_detalhes_vaga(detalhes_vaga, url, included)

def main():
    keyword = input("Digite o a sua busca vaga como buscaria no LinkedIn: ")
    numero_paginas = int(input("Digite o numero de paginas que deseja buscar: "))
    email = input("email: ")
    senha = input("senha: ")
    url_busca = 'https://www.linkedin.com/jobs/search/?keywords=' + keyword
    login(email, senha)
    buscar_e_salvar_vagas(numero_paginas, url_busca)

main()