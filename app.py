import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os.path
import time
import json
import threading
import sqlite3


chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--window-size=1920x1080')

chrome_driver = 'C:\\code\\selenium\\driver\\chromedriver.exe'

base_url = 'http://www.mafengwo.cn'
mdd_url = base_url + '/mdd'


cities_url_dict = {}


def get_city_url(init_url):
	res = requests.get(init_url)
	res.raise_for_status()

	soup = BeautifulSoup(res.text, 'html.parser')
	main_land_div = soup.select('div.hot-list')[0]
	dd_list = main_land_div.find_all('dd')
	dt_list = main_land_div.find_all('dt')

	for dd in dd_list:
		print(dd)
		for a_link in dd.find_all('a'):
			if a_link.text != '':
				city_code = a_link['href'].split('/')[-1].split('.')[0]
				cities_url_dict[a_link.text] = {'code': city_code}


	dt_code_list = []
	for dt in dt_list:
		print(dt)
		for a_link in dt.find_all('a'):
			dt_code = a_link['href'].split('/')[-1].split('.')[0]
			dt_code_list.append(dt_code)



	while dt_code_list:
		a, b, c = dt_code_list.pop(), dt_code_list.pop(), dt_code_list.pop()
		print(a, b, c)
		t1, t2, t3 = [threading.Thread(target=get_city_url_from_citylist_page, args=(code,)) 
						for code in (a, b, c)] 

		t1.start()
		t2.start()
		t3.start()
		t1.join()
		t2.join()
		t3.join()



def get_city_url_from_citylist_page(dt_code):
	dt_city_list_url = mdd_url + '/citylist/' + dt_code + '.html'
	driver = webdriver.Chrome(chrome_options=chrome_options, executable_path=chrome_driver)
	driver.get(dt_city_list_url)
	# driver.set_window_size(1120, 550)

	city_titles = driver.find_elements_by_css_selector('div.title')
	for title in city_titles:
		parent_a = title.find_element_by_xpath('..')
		city = title.text.strip().split('\n')[0]
		if cities_url_dict.get(city, None) is None:
			city_code = parent_a.get_attribute('href').split('/')[-1].split('.')[0]
			cities_url_dict[city] = {'code': city_code}

	try:
		next_page_link = \
			driver.find_element_by_xpath('//div[@id="citylistpagination"]/div/a[contains(@class, "pg-next")]')

		while next_page_link:
			next_page_link.click()
			time.sleep(10)
			city_titles = driver.find_elements_by_css_selector('div.title')
			for title in city_titles:
				parent_a = title.find_element_by_xpath('..')
				city = title.text.strip().split('\n')[0]
				if cities_url_dict.get(city, None) is None:
					city_code = parent_a.get_attribute('href').split('/')[-1].split('.')[0]
					cities_url_dict[city] = {'code': city_code}
			next_page_link = \
				driver.find_element_by_xpath('//div[@id="citylistpagination"]/div/a[contains(@class, "pg-next")]') or None
	except Exception as err:
		print(err)

	driver.quit()
	time.sleep(10)


def save_city_info_file():
	with open('cities_china.json', 'w', encoding='utf-8') as f:
		json_str = json.dumps(cities_url_dict)
		f.write(json_str)

def get_static_page_soup(url):
	try:
		res = requests.get(url)
		res.raise_for_status()
		soup = BeautifulSoup(res.text, 'html.parser')

		return soup
	except Exception as err:
		with open('failed_url.log', 'w') as f:
			f.write(f'{url} \n {err} \n--------------------------------------------------------------------------')


def get_city_info(city_code):
	url = base_url + '/xc/' + city_code + '/'
	soup = get_static_page_soup(url)

	div_aside = soup.select('div.p-aside')[0]
	if div_aside.find_all() is []:
		tag_all_count, tag_jd_count, tag_cy_count, tag_gw_yl_count = 0, 0, 0, 0
		tags = []
	else:

		tags_a = soup.select('li.impress-tip > a')
		tags = [a.text.split()[0] for a in tags_a]

		tag_all_count = 0
		for a in tags_a:
			if a.find('em'):
				em_num = int(a.find('em').text.strip())
				tag_all_count += em_num

		tag_jd_count, tag_cy_count, tag_gw_yl_count = 0, 0, 0
		for a in tags_a:
			par = a.attrs['href'][1:3]

			if a.find('em'):
				em = a.find('em').text.strip()
			else:
				em = '0'

			if par == 'jd':
				tag_jd_count += int(em)
			elif par == 'cy':
				tag_cy_count += int(em)
			elif par == 'gw' or par == 'yl':
				tag_gw_yl_count += int(em)

	
	return {
		'tag_all_count': tag_all_count, 
		'tag_jd_count': tag_jd_count, 
		'tag_cy_count': tag_cy_count, 
		'tag_gw_yl_count': tag_gw_yl_count, 
		'total_city_yj': get_city_youji(city_code), 
		'tags': tags
	}


def get_city_youji(city_code):
	url = base_url + '/yj/' + city_code + '/'
	soup = get_static_page_soup(url)

	if soup.select('span.count > span'):
		total_city_yj = int(soup.select('span.count > span')[1].text)
	else:
		total_city_yj = int(len(soup.select('li.post-item.clearfix')))
	return total_city_yj


def get_city_food(city_code):
	url = base_url + '/cy/' + city_code + '/'
	soup = get_static_page_soup(url)

	indexes = soup.select('ol.list-rank > li.rank-item em.r-num')
	foods = soup.select('ol.list-rank > li > a > h3')
	counts = soup.select('ol.list-rank > li > a > span.trend')
	return {index.text: [food.text, count.text] for index, food, count in zip(indexes, foods, counts)}


def get_city_jingdian(city_code):
	url = base_url + '/jd/' + city_code + '/gonglve.html'
	soup = get_static_page_soup(url)

	jingdians = soup.select('div.item.clearfix h3 a')
	indexes = soup.select('div.item.clearfix h3 > span.num')
	jingdians_clear = [jingdians[i] for i in range(1, len(jingdians), 2)]
	dianpings = soup.select('div.item.clearfix h3 span.rev-total > em')
	return {index.text: [jingdian.attrs['title'], dianping.text] 
		for index, jingdian, dianping in zip(indexes, jingdians_clear, dianpings)}


def connect_db(name):
	if not os.path.exists(name):
		conn = sqlite3.connect(name)
		c = conn.cursor()
		c.execute("""CREATE TABLE city_basic_info (
			city_code integer primary key, 
			city_name text, 
			tag_all_count integer, 
			tag_jd_count integer, 
			tag_cy_count integer, 
			tag_gw_yl_count integer, 
			total_city_yj integer, 
			tags text);""")
		c.execute("""CREATE TABLE city_food (
			id integer primary key not null, 
			city_code integer, 
			food_index integer, 
			food_name text, 
			food_hot integer, 
			FOREIGN KEY (city_code) REFERENCES city_basic_info (city_code));""")
		c.execute("""CREATE TABLE city_jd (
			id integer primary key not null, 
			city_code integer, 
			jd_index integer, 
			jd_name text, 
			jd_hot integer, 
			FOREIGN KEY (city_code) REFERENCES city_basic_info (city_code));""")
	else:
		conn = sqlite3.connect(name)
		c = conn.cursor()
	return conn, c


def save_city_info_to_db(city_code, cursor):
	info = get_city_info(city_code)

	cursor.execute("""INSERT INTO city_basic_info (
				city_code, 
				city_name, 
				tag_all_count, 
				tag_jd_count, 
				tag_cy_count, 
				tag_gw_yl_count, 
				total_city_yj, tags) VALUES 
				(?, ?, ?, ?, ?, ?, ?, ?)""", (
					city_code, 
					city, 
					info['tag_all_count'], 
					info['tag_jd_count'], 
					info['tag_cy_count'], 
					info['tag_gw_yl_count'], 
					info['total_city_yj'], 
					str(info['tags'])))

def save_city_food_to_db(city_code, cursor):
	food = get_city_food(city_code)

	for key, value in food.items():
		cursor.execute("""INSERT INTO city_food (city_code, food_index, food_name, food_hot) VALUES (?, ?, ?, ?)""", 
					(city_code, key, value[0], value[1]))


def save_city_jd_to_db(city_code, cursor):
	jd = get_city_jingdian(city_code)

	for k, v in jd.items():
		cursor.execute("""INSERT INTO city_jd (city_code, jd_index, jd_name, jd_hot) VALUES (?, ?, ?, ?)""", 
						(city_code, k, v[0], v[1]))



if __name__ == '__main__':
	if not os.path.exists('cities_china.json'):
		get_city_url(mdd_url)
		save_city_info_file()

	with open('cities_china.json', 'r', encoding='utf-8') as f:
		cities_url_dict = json.loads(f.read())

	conn, c = connect_db('result.db')

	for city, value in list(cities_url_dict.items()):
		city_code = value['code']
		print(city, city_code)
		if c.execute("SELECT * FROM city_basic_info WHERE city_code=" + city_code).fetchall() == []:
			save_city_info_to_db(city_code, c)
		if c.execute("SELECT * FROM city_food WHERE city_code=" + city_code).fetchall() == []:
			save_city_food_to_db(city_code, c)
		if c.execute("SELECT * FROM city_jd WHERE city_code=" + city_code).fetchall() == []:
			save_city_jd_to_db(city_code, c)

		conn.commit()
	conn.close()
