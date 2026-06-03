from bs4 import BeautifulSoup as soup
import requests, re, time, random
from requests import exceptions as reqexc
from fake_headers import Headers

# 🔥 Импорты прокси закомментированы, так как библиотека несовместима с новым Python
# from .proxy import Proxy

class VacancyScrapper:
    __url_search = "https://hh.ru/search/vacancy"
    __url_vacancy = "https://hh.ru/vacancy"

    @classmethod
    def get_search_url(self): return self.__url_search

    @classmethod
    def get_vacancy_url(self): return self.__url_vacancy

    headers = {
         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
         "Accept": "*/*",
         "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
         "Connection": "keep-alive"
    }

    __fake_header = Headers()

    params = {
         "salary": None,
         "st": "searchVacancy",
         "text": "",
         "page": 0
    }

    sleep_time = {
        'min': 0.3,  # 🔥 Увеличили минимальную задержку, чтобы не блокировали
        'max': 1.0
    }

    def __init__(self, params=None, sleep_time=None):
        if sleep_time: self.sleep_time = sleep_time
        if params: self.params = params
        # 🔥 Убрали инициализацию прокси: self.proxy = Proxy()

    def __wait(self):
        time.sleep(self.sleep_time["min"]+(random.random()*(self.sleep_time["max"]-self.sleep_time["min"])))

    # В методе get_page, замените возврат рекурсии на безопасный:
    def get_page(self, url, use_params=True):
        exceptions = (reqexc.Timeout, reqexc.TooManyRedirects, reqexc.RequestException, reqexc.HTTPError)
        unparsed = None
        try:
            self.__wait()
            params = self.params if use_params else None
            print(url)
            
            # 🔥 Прямой запрос без прокси
            response = requests.get(url, 
                                    headers=self.__fake_header.generate() or self.headers, 
                                    params=params,
                                    timeout=15)
            
            # 🔥 Проверка статуса ответа
            if response.status_code != 200:
                print(f"⚠️ HTTP {response.status_code} для {url}")
                return None
                
            unparsed = soup(response.text, 'html.parser')
        except exceptions as err: 
            print(f"get page error: {str(err)}")
            return None  # 🔥 Возвращаем None вместо рекурсии

        return unparsed  

    def get_vacancy_page(self, url, id=None):
        if id: 
            url = self.__url_vacancy + "/" + id
        return self.get_page(url, use_params=False)

    def get_searching_results_page(self, page_number=None):
        self.params['page'] = page_number or 0
        return self.get_page(self.__url_search)

    def get_page_count(self):            
        response = self.get_searching_results_page()
        if not response: return 1 # 🔥 Если ошибка, возвращаем 1 страницу
        
        pager_buttons = response.select("div[data-qa='pager-block'] a[class='bloko-button'][data-qa='pager-page']")  
        page_numbers = [] 

        for pager_button in (pager_buttons or []):              
            page_numbers.append(int(pager_button.get_text()))

        if len(page_numbers) == 0:
             page_numbers.append(1)
        
        return max(page_numbers)

    def get_vacancy_links(self):
        page_count = self.get_page_count()
        links = []

        for i in range(page_count):
            vacancys_on_page = False       
            while not vacancys_on_page:                
                response = self.get_searching_results_page(page_number=i)
                if not response: break # 🔥 Выход, если ошибка
                
                 # ищем блоки с вакансиями
                vacancys_on_page = response.find_all("div", attrs={"class": 'vacancy-serp-item'})  
                vacancys_on_page = (vacancys_on_page if len(vacancys_on_page or []) > 0 else False)
            
            # выдергиваем url
            for vacancy_block in (vacancys_on_page or []):
                link_container = vacancy_block.find("a", attrs={"class": 'bloko-link'})
                if link_container and link_container.get('href'):
                    links.append(re.sub(r'\?.+', r'', str(link_container['href'])))

        return links