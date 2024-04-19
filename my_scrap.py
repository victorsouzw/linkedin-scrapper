import requests
from bs4 import BeautifulSoup

client = requests.Session()

HOMEPAGE_URL = 'https://www.linkedin.com'
LOGIN_URL = 'https://www.linkedin.com/checkpoint/lg/login-submit'

html = client.get(HOMEPAGE_URL).content
soup = BeautifulSoup(html, "html.parser")
csrf = soup.find('input', {"name":"loginCsrfParam"})['value']

file = open('senha.txt', 'r')
login_information = {
    'session_key':'seu_email@email.com', ###ALTERAR EMAIL
    'session_password': file.read(),
    'loginCsrfParam': csrf,
}
file.close()

client.post(LOGIN_URL, data=login_information)
url_vagas_inicio = 'https://www.linkedin.com/search/results/all/?'
url_vagas_keywords = 'keywords=project manager "pleno"'
url_vagas_final = '&origin=GLOBAL_SEARCH_HEADER&sid=JTP'
print(BeautifulSoup(client.get(url_vagas_inicio+url_vagas_keywords+url_vagas_final).content, "html.parser").prettify())
