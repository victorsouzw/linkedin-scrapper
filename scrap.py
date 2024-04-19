import requests
from bs4 import BeautifulSoup

URL = "https://realpython.github.io/fake-jobs/"
page = requests.get(URL)

soup = BeautifulSoup(page.content, "html.parser")
results = soup.find(id="ResultsContainer") ## get from id
# print(results.prettify())
python_jobs = results.find_all( ##passing a function to a BS4 method;
    "h2", string=lambda text: "python" in text.lower()  #above we find elements by class
                                                            #and by text content with a non exactly search from string
)

print(python_jobs)
# job_elements = results.find_all("div", class_="card-content") ## get from class
# for job_element in job_elements:
#     #print(job_element, end="\n"*2) ## still catching all html stufs
#     title_element = job_element.find("h2", class_="title") ## here we grab out only the fields that we want
#     company_element = job_element.find("h3", class_="company") ##  this returns also a beautifulSoup object
#     location_element = job_element.find("p", class_="location")
#     print(title_element.text.strip()) ## title_element still comming as html fields, here we grab the text inside it
#     print(company_element.text.strip())
#     print(location_element.text.strip())
#     print()
