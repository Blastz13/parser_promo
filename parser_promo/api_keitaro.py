import os

import requests
import time

from .models import Option

import json
class ApiKeitaro:
    """
    Класс для работы с Keitaro API
    @url https://admin-api.docs.keitaro.io
    """

    api_url_keitaro1 = ''  # 167.71.33.108
    api_url_keitaro2 = ''  # 160.20.147.203
    api_version = 'v1'
    headers = {'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}

    def __init__(self, api_key, keitaro_server_number=1):
        """Constructor"""

        try:
            self.api_url_keitaro1 = 'http://{}/admin_api/'.format(Option.get_value_by_name('keitaro1.ip'))
        except Exception as ex:
            print("PIZDEC ")
            raise ex

        try:
            self.api_url_keitaro2 = 'http://{}/admin_api/'.format(Option.get_value_by_name('keitaro2.ip'))
        except Exception as ex:
            raise ex

        headers = {
            'Api-Key': api_key,
        }
        self.api_url = self._get_api_url_server(keitaro_server_number)
        self.headers.update(headers)

    def _get_api_url_server(self, keitaro_server_number):
        """Получить URL сервера Keitaro."""

        if int(keitaro_server_number) == 1:
            return self.api_url_keitaro1
        else:
            return self.api_url_keitaro2

    def _requests_get(self, api_url_method, params):
        """ Отправка GET запроса (curl) """

        return requests.get(
            self.api_url + self.api_version + api_url_method,
            params=params,
            headers=self.headers,
        )

    def _requests_post(self, api_url_method, json):
        """ Отправка POST запроса (curl) """
        return requests.post(
            self.api_url + self.api_version + api_url_method,
            headers=self.headers,
            json=json
        )

    def _requests_post2(self, api_url_method, data):
        """ Отправка POST запроса (curl) """
        return requests.post(
            self.api_url + self.api_version + api_url_method,
            headers=self.headers,
            data=data
        )

    def get_all_campaigns(self):
        """ Получить все кампании """

        response = self._requests_get('/campaigns', params=None)

        return response.json()

    def get_campaign(self, id):
        """ Получить одну компанию """

        response = self._requests_get('/campaigns/{}'.format(id), params=None)

        return response.json()

    def post_report_build(self, campaign_id, date_begin, date_end):
        """
        Получить статистику
        @url https://admin-api.docs.keitaro.io/#tag/Reports
        Для date_begin и date_end формат YYYY-MM-DD
        """
        payload = {
            "range": {"from": str(date_begin), "to": str(date_end), "timezone": "Europe/Moscow"},
            "metrics": ["approve", "campaign_unique_clicks", "leads", "lp_clicks", "conversions", "sales", "rejected",
                        "sale_revenue"],
            "filters": [{"name": "campaign_id", "operator": "EQUALS", "expression": campaign_id}]
        }
        response = self._requests_post('/report/build', json=payload)

        return response.json()

    def post_conversions(self, date_begin, date_end):
        """ Получить конверсии"""

        payload = {
            "range": {"from": str(date_begin), "to": str(date_end), "timezone": "Europe/Moscow"},
            "columns": ["revenue", "sub_id_15"],
            "filters": [{"name": "status", "operator": "EQUALS", "expression": "sale"}]
        }
        response = self._requests_post('/conversions/log', json=payload)

        return response.json()

    def get_landing_page(self, landing_page_id):
        """Получить лендинг по его ID."""

        response = self._requests_get(f'/landing_pages/{landing_page_id}', params=None)

        return response.json()

    def post_create_landing_pages(self, params):
        """Загрузить лендинг в Keitaro."""
        print("Create_landing")
        folder = params.get("keitaro_folder_name")
        if folder:
            pass
        else:
            folder = params.get("name")

        s1 = """{"action_options": {"folder": """ + '''"{}"'''.format(folder)
        s2 = '}, "name":'
        s3 = ' "{}", "group_id": "17","state": "active", "landing_type": "local", "action_type": "local_file", "archive":'.format(params.get('name'))
        s4 = '"data:application/zip;base64,{0}"'.format(params.get('archive_string'))
        s5 = '}'
        q = s1 + s2 + s3 + s4 + s5
        f = open("file.txt", "w")
        f.write(q)
        f.close()
        s = """exec curl  -H 'Api-Key: cca10e6386c93734ff144e53d8c39708' --data '@file.txt' 'http://167.71.48.51/admin_api/v1/landing_pages'"""
        qq = os.popen(s).read()
        r = json.loads(qq)
        return r

        # print("create лэндиннг")
        # data = {
        #     "action_options": {"folder": "test"},
        #     "name": "TESTIK",
        #     "group_id": params.get('group_id'),
        #     "state": "active",
        #     "landing_type": "local",
        #     "action_type": "local_file",
        #     "archive": "data:application/zip;base64,{0}".format(params.get('archive_string'))
        # }
        # print(data)
        # return self._requests_post2('/landing_pages', data=data)

    def post_create_offer(self, params):
        """Загрузить оффер в Keitaro."""
        print("Create_offer")
        folder = params.get("keitaro_folder_name")
        if folder:
            pass
        else:
            folder = params.get("name")
        s1 = '''{"payout_auto": "true",
        "payout_type": "CPA",
        "state": "active",
        "offer_type": "local",
        "action_type": "local_file",'''

        s2 = '''"action_options": {''' + '''"folder": "{}"'''.format(folder) +'''},'''
        s3 = '''"name": "{}", '''.format(params.get("name"))
        s4 = '''"group_id": "{}",'''.format(params.get('group_id'))
        s5 = '''"country": "{}",'''.format(params.get('country'))
        s6 = '''"affiliate_network_id": "{}",'''.format(params.get('affiliate_network_id'))
        s7 = '''"archive": "{}",'''.format(params.get('archive_string'))
        s8 = '''"notes": "{}"'''.format(params.get('notes')) + "}"
        q = s1 + s2 +s3 +s4 + s5 +s6 +s7 +s8
        f = open("file.txt", "w")
        f.write(q)
        f.close()
        s = """exec curl  -H 'Api-Key: cca10e6386c93734ff144e53d8c39708' --data '@file.txt' 'http://167.71.48.51/admin_api/v1/offers'"""
        qq = os.popen(s).read()
        # r = json.loads(q)
        # print(r['preview_path'])

        r = json.loads(qq)
        return r

        # data = {
        #     "action_options": {"folder": "11111111"},
        #     "name": params.get('name'),
        #     "group_id": params.get('group_id'),
        #     "state": "active",
        #     "offer_type": "local",
        #     "action_type": "local_file",
        #     "country": params.get('country'),
        #     "affiliate_network_id": params.get('affiliate_network_id'),
        #     "archive": "data:application/zip;base64,{0}".format(params.get('archive_string')),
        #     "payout_auto": "true",
        #     "payout_type": "CPA",
        #     "notes": params.get('notes')
        # }
        # 
        # return self._requests_post2('/offers', data=data)


    def post_create_domain(self, params):
        """Добавить домен в Keitaro."""

        payload = {
            "name": params.get('name'),
            "catch_not_found": False,
            "notes": "Adding via API",
            "ssl_redirect": True,
            "allow_indexing": False
        }
        response = self._requests_post('/domains', json=payload)

        return response.json()

    def get_groups(self, type_group='landings'):
        """Получить список группы указанного типа.
        https://admin-api.docs.keitaro.io/#tag/Groups
        type: "campaigns" "offers" "landings"
        """

        response = self._requests_get(f'/groups?type={type_group}', params=None)

        return response.json()

    def get_affiliate_networks(self, type_group='landings'):
        """Получить список партнерских сетей.
        https://admin-api.docs.keitaro.io/#tag/Affiliate-Networks
        """

        response = self._requests_get(f'/affiliate_networks', params=None)

        return response.json()