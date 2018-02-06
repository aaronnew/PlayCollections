# coding=utf-8

import requests
import json
import time
import xlsxwriter
import traceback
import random

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
    'Accept': 'application/json;version=5.1.0',
    'Referer': 'http://food.petnet.io/'
}
recipe_ids = set()
workbook = xlsxwriter.Workbook('Expenses03.xlsx')
recipe_sheet = workbook.add_worksheet()
row_number = 0

proxies_ip = "http://121.31.102.146:8123"


def fetch(url, params=None):
    global proxies_ip
    proxies = {'http': proxies_ip, 'https': proxies_ip}
    try:
        resp = requests.get(url, params=params, headers=headers, proxies=proxies, timeout=20)
        print("fetch -> " + resp.url, "status -> " + str(resp.status_code))
        if resp.status_code != 200:
            print("426, input proxy ip:")
            proxies_ip = input()
            print("==OK==")
            return fetch(url, params)
    except Exception as e:
        # traceback.print_exc()
        print("Exception is {}, input proxy ip:".format(e))
        proxies_ip = input()
        print("==OK==")
        return fetch(url, params)
    return resp


def main():
    write_header()

    brands_url = "http://food.petnet.io/api/brands/"
    search_url = "http://food.petnet.io/api/recipes/search"
    search_params = {
        "search": "Royal Canin",
        "dog": "true",
        "cat": "true",
        "dry_food": "true",
        "wet_food": "true"
    }
    resp = fetch(brands_url, None)
    print("fetch -> " + resp.url, "status -> " + str(resp.status_code))
    brands = json.loads(resp.text)

    for brand in brands:

        search_params['search'] = brand['name']
        # for dog in ['true', 'false']:
        #     for cat in ['true', 'false']:
        #         for dry in ['true', 'false']:
        #             for wet in ['true', 'false']:
        #                 search_params['dog'] = dog
        #                 search_params['cat'] = cat
        #                 search_params['dry_food'] = dry
        #                 search_params['wet_food'] = wet

        resp = fetch(search_url, search_params)

        format_data(brand, json.loads(resp.text)['recipes'], search_params)
        # time.sleep(1)


def write_header():
    global row_number
    recipe_sheet.write(row_number, 0, "brand_name")
    recipe_sheet.write(row_number, 1, "formula")
    recipe_sheet.write(row_number, 2, "image")
    recipe_sheet.write(row_number, 3, "seo_path")
    recipe_sheet.write(row_number, 4, "score")
    recipe_sheet.write(row_number, 5, "upc")
    recipe_sheet.write(row_number, 6, "weight")
    recipe_sheet.write(row_number, 7, "price_per_kcal")
    recipe_sheet.write(row_number, 8, "discontinued")
    recipe_sheet.write(row_number, 9, "price")
    recipe_sheet.write(row_number, 10, "price_per_lb")
    recipe_sheet.write(row_number, 11, "kcal_per_container")
    row_number += 1


def format_data(brand, recipes, search_params):
    for recipe in recipes:

        if recipe['_id']['$oid'] in recipe_ids or not recipe.get('sizes'):
            continue
        else:
            recipe_ids.add(recipe['_id']['$oid'])

        for size in recipe['sizes']:
            row = list()
            row.append(recipe.get('brand_name'))
            row.append(recipe.get('formula'))
            row.append("https://d2xogj6atqrb4h.cloudfront.net/images/" + recipe.get('image') + ".png")
            row.append(recipe.get('seo_path'))
            row.append(recipe.get('score'))
            row.append(size.get('upc'))
            row.append(size.get('weight'))
            row.append(size.get('price_per_kcal'))
            row.append(size.get('discontinued'))
            row.append(size.get('price'))
            row.append(size.get('price_per_lb'))
            row.append(size.get('kcal_per_container'))
            write_excel(row)


def write_excel(data):
    global row_number
    col = 0
    for item in data:
        recipe_sheet.write(row_number, col, item)
        col += 1
    row_number += 1


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        traceback.print_exc()
    finally:
        workbook.close()
