import json
import os.path
import threading
import time

import requests
from bs4 import BeautifulSoup

# заголовки для запроса
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.119 '
                  'YaBrowser/22.3.0.2434 Yowser/2.5 Safari/537.36',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,'
              'application/signed-exchange;v=b3;q=0.9 '
}

category_dict = {}


# получение пагинации
# находим последнюю станицу и чистим от мусора
# исключение добавлено потому, что есть разделы, у которых
# меньше 7 страниц. В этом случае пагинация немного отличается
def get_page_count(url):
    req = requests.get(url=url, headers=headers)
    soup = BeautifulSoup(req.text, 'lxml')
    try:
        page_count = int(soup.find('div', id='pages').find_all('a')[-1].text.split(" ")[1].strip())
    except:
        page_count = int(soup.find('div', id='pages').find_all('a')[-1].text.strip())
    return page_count


# получаем ссылки на категории и сохраняем с JSON
# получение ссылок происходит при каждом запуске программы
# так как считывается так же и количество стараниц в каждой категории
# и по прошествии времени оно может изменяться
def get_link_category(url):
    url_cats = 'https://w-dog.ru' + url.find('div', class_='word').find('a')['href']
    url_cat = str('https://w-dog.ru' + url.find('div', class_='word').find('a')['href']).split("/")
    url_cat_s = f'{url_cat[0]}//{url_cat[2]}/{url_cat[3]}/{url_cat[4]}/{url_cat[5]}'
    name_category = url.find('div', class_='word').find('a').text.strip()
    p_count = get_page_count(url_cats)
    category_dict[name_category] = {
        'url_category': url_cat_s,
        'page_count': p_count
    }

    with open('category_res.json', 'w', encoding='utf-8') as file:
        json.dump(category_dict, file, indent=4, ensure_ascii=False)


def thread_func_category():
    url = 'https://w-dog.ru/'
    req = requests.get(url=url, headers=headers)
    soup = BeautifulSoup(req.text, 'lxml')
    all_category = soup.find_all('div', class_='wpitem category')
    for url in all_category:
        t = threading.Thread(target=get_link_category, kwargs={'url': url})
        t.start()


# загрузка картинок из категории
# получение названия категории
# создание папки с именем категории куда будут загружаться картинки
# поиск всех ссылок настранице, скачивание их в цикле
# и сохранение в созданную папку
def get_pict_download(item, name_cat, count_cat):
    name_pict = item.find('b', class_='word').text.strip().replace("/", " ").replace('"', ''). \
        replace("'", "").replace(".", "")
    if not os.path.isfile(os.path.join(name_cat, f'{name_pict}.jpg')):
        url_pict = 'https://w-dog.ru' + item.find('div', class_='action-buttons').find('a')['href']
        req = requests.get(url=url_pict, headers=headers)
        with open(os.path.join(name_cat, f'{name_pict}.jpg'), 'wb') as file:
            file.write(req.content)


def thread_func(url_cat, count_cat, name_cat):
    start_time = time.monotonic()
    print(f'[+] Загружаю категорию "{name_cat}". Количество страниц: {count_cat}\n')
    for nc in range(1, count_cat + 1):
        print(f'[+] Загружаю >> Страница: {nc}/{count_cat}...')
        req = requests.get(url=f"{url_cat}{nc}/best/", headers=headers)
        soup = BeautifulSoup(req.text, 'lxml')
        name_cat = soup.find('div', id='content-top').find('h2').text.strip()
        if not os.path.isdir(name_cat):
            os.mkdir(name_cat)
        all_url_page = soup.find_all('div', class_='wpitem')
        for item in all_url_page:
            t = threading.Thread(target=get_pict_download, kwargs={'item': item, 'name_cat': name_cat,
                                                                   'count_cat': count_cat})
            t.start()
    print(f'\nВремя загрузки файлов: {time.monotonic() - start_time}')


def main():
    print('[+] Обновляю словарь...\n')
    thread_func_category()
    time.sleep(2)
    with open('category_res.json', 'r', encoding='utf-8') as file:
        cat_dict = json.load(file)
    dict_cat = {}
    for num, cat in enumerate(cat_dict):
        print(f'{num}. {cat} | {cat_dict[cat]["page_count"]} страниц...')
        dict_cat[num] = {
            'url_category': cat_dict[cat]["url_category"],
            'page_count': cat_dict[cat]["page_count"],
            'name_cat': cat
        }
    num_cat = int(input('\n[+] - Введите номер категории для загрузки: '))

    # передача данных для запуска потоков загрузки картинок
    if num_cat in dict_cat:
        thread_func(f"{dict_cat[num_cat]['url_category']}/", dict_cat[num_cat]['page_count'], dict_cat[num_cat]['name_cat'])
    else:
        print('[-] Вы ввели неверный номер категории для загрузки.')
        exit(0)


if __name__ == "__main__":
    main()