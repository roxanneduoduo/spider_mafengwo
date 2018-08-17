import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os.path
import time


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
		for a_link in dd.find_all('a'):
			if a_link.text != '':
				city_code = a_link['href'].split('/')[-1].split('.')[0]
				cities_url_dict[a_link.text] = {'code': a_link['href']}


	for dt in dt_list:
		for a_link in dt.find_all('a'):
			dt_code = a_link['href'].split('/')[-1].split('.')[0]
			get_city_url_from_citylist_page(dt_code)


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
		next_page_link = driver.find_element_by_xpath('//div[@id="citylistpagination"]/div/a[contains(@class, "pg-next")]')

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
			next_page_link = driver.find_element_by_xpath('//div[@id="citylistpagination"]/div/a[contains(@class, "pg-next")]') or None
	except Exception as err:
		print(err)

	driver.close()


def save_city_url_file():
	get_city_url(mdd_url)
	with open('cities_url.txt', 'w', encoding='utf-8') as f:
		for k, v in cities_url_dict.items():
			f.write(f"{k}: {v}\n")


def get_city_info(city_code):
	url = base_url + '/xc/' + city_code + '/'
	res = requests.get(url)
	res.raise_for_status()

	soup = BeautifulSoup(res.text, 'html.parser')
	tags_a = soup.select('li.impress-tip > a')
	tags = [a.text.split()[0] for a in tags_a]
	tag_all_count = sum([int(a.find('em').text) for a in tags_a])
	tag_jd_count, tag_cy_count, tag_gw_yl_tag = 0, 0, 0
	for a in tags_a:
		par = a.attrs['href'][1:3]
		em = a.find('em').text
		if par == 'jd':
			tag_jd_count += int(em)
		elif par == 'cy':
			tag_cy_count += int(em)
		elif par == 'gw' or par == 'yl':
			tag_gw_yl_tag += int(em)

	yj_url = base_url + '/yj/' + city_code + '/'
	res = requests.get(yj_url)
	res.raise_for_status()
	soup = BeautifulSoup(res.text, 'html.parser')
	total_city_yj = int(soup.select('span.count > span')[1].text)
	return {
		'tag_all_count': tag_all_count, 
		'tag_jd_count': tag_jd_count, 
		'tag_cy_count': tag_cy_count, 
		'tag_gw_yl_tag': tag_gw_yl_tag, 
		'total_city_yj': total_city_yj, 
		'tags': tags
	}


def get_city_food(city_code):
	pass


"""
if not os.path.exists('cities_url.txt'):
	save_city_url_file()


with open('cities_url.txt', 'r') as f:
	for line in f.readlines():
		city, url = line.split(': ')
		if not url.startswith('http://'):
			url = base_url + url

"""
print(get_city_info('10065'))
