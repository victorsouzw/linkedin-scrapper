import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
from datetime import date

client = requests.Session()

HOMEPAGE_URL = 'https://www.linkedin.com'
LOGIN_URL = 'https://www.linkedin.com/checkpoint/lg/login-submit'

def salvar_detalhes_vaga(detalhes_vaga : json):
    id = detalhes_vaga['jobPostingId']
    nova_vaga = {
        'id': [id],
        'titulo': [detalhes_vaga['title']],
        'descricao': [detalhes_vaga['description']['text']],
        'url_de_aplicacao': [detalhes_vaga['applyMethod']['companyApplyUrl']],
        'vaga_remota':[detalhes_vaga['workRemoteAllowed']],
        'data_de_busca': [date.today()]
    }

    excel_path = 'vagas.xlsx'

    try:
        df_existente = pd.read_excel(excel_path)
        df_novos = pd.DataFrame(nova_vaga)
        df_final = pd.concat([df_existente, df_novos], ignore_index=True).drop_duplicates(subset='id', keep='first')
        
        with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
            df_final.to_excel(writer, index=False)
        
        if (len(df_final) > len(df_existente)):
            print(f'Dados da vaga com o id {id} foram adicionados ao arquivo {excel_path}')
        else:
            print(f'Vaga com o id {id} já existe e não será adicionada novamente.')

    except FileNotFoundError:
        df_novos = pd.DataFrame(nova_vaga)
        df_novos.to_excel(excel_path, index=False, engine='xlsxwriter')
        
        print(f'Dados da vaga com o id {id} foram adicionados ao arquivo {excel_path}')

    except Exception as e:
        print(f'Ocorreu um erro: {str(e)}')

def extrair_detalhes_vaga(vaga_items):
    for item in vaga_items:
        item_json = json.loads(item.text)

        if 'data' in item_json and 'applyMethod' in item_json['data']:
            return item_json['data']
        
    return None

html = client.get(HOMEPAGE_URL).content
soup = BeautifulSoup(html, "html.parser")
csrf = soup.find('input', {"name":"loginCsrfParam"})['value']

file = open('senha.txt', 'r')
login_information = {
    'session_key':'rixasik327@luravell.com', ###ALTERAR EMAIL
    'session_password': file.read(),
    'loginCsrfParam': csrf,
}
file.close()

result_login = client.post(LOGIN_URL, data=login_information)
result_login_soup = BeautifulSoup(result_login.content, "html.parser")
if result_login_soup.find(id='captchaInternalPath') is not None:
    raise Exception("O LinkedIn considerou o login suspeito. Solicitando um confirmação por código que foi enviado ao respectivo email. A resposta ao pin challenge não foi implementada.")

# TODO deixar melhor a forma de adicionar a query
url_vagas_inicio = 'https://www.linkedin.com/search/results/all/?'
url_vagas_keywords = 'keywords=project manager "pleno"'
url_vagas_final = '&origin=GLOBAL_SEARCH_HEADER&sid=JTP'

content = client.get(url_vagas_inicio+url_vagas_keywords+url_vagas_final).content

soup = BeautifulSoup(content, "html.parser")

# Find all <code> tags with an id that starts with "bpr-guid"
bpr_guid_tags = soup.select('code[id^="bpr-guid"]')


# payload que queremos estão em <code id="bpr-guid-xxxxx" style="display: none"> // xxxx pq varia por request, usar o bpr-guid apenas
# vou alterar o codigo para salvar apenas o resultado util, para lidar com o caso de senha errado ou requisição incompleta, talvez seja necessário olhar novamente
# todo o html para entender o que está acontecendo. caso não existir o "bpr-guid" na requisição incorreta, conseguiremos verificar com isso

data = json.loads(str(bpr_guid_tags[-1].text).strip())
#pegar o último elemento da lista, pois são retornados varias tags <code bpr-guid...>

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

# Aqui teremos extraido as URLs para a página de detalhes das vagas
https_urls = set(extract_urls(data, 'url'))
with open('results.txt', 'w') as f:
    f.write(str(https_urls)) ## (jeito mais facil eu acho) pode ser usado para verificar as vagas novas, abre a file antes de popular ela na função de extrair s urls e se ja for existente ele nao vai adicionar porque é um set

for url in https_urls:
    # Send a GET request to the URL
    response = client.get(url)

    # Parse the response content with BeautifulSoup
    soup = BeautifulSoup(response.content, "html.parser")

    # Convert the BeautifulSoup object to a pretty string
    # pretty_html = soup.prettify()

    # Save the pretty HTML into a file named 'scrap-vaga.html'
    # with open('scrap-vaga.html', 'w', encoding='utf-8') as f:
    #    f.write(pretty_html)

    vaga_items = soup.find_all('code')
    detalhes_vaga = extrair_detalhes_vaga(vaga_items)
    if detalhes_vaga != None:
        salvar_detalhes_vaga(detalhes_vaga)

    


## Se o resultado do scrap-vaga tem o id "apply-button--default" quer dizer que tem aplicação simplificada
## Uma coluna de resultado "link para aplicação" e colocar link  ou "aplicação simplificada"
## o link para vaga está disponível na tag "applyUrl" daquelas vagas que não são simplificadas

## mais interessante pegar no primeiro scrap de busca todos links pra ir pra pagina detalhada da vaga
## na pagina das vagas pega as informações detalhadas e pimba, salva no csv
## da pra tentar adicionar data de postagem e data de expiração da vaga