# coding=utf-8
from unicodedata import name
from django.conf import settings
from django.contrib.auth.models import User

import os
import shutil
from pathlib import Path
from zipfile import ZipFile
from bs4 import BeautifulSoup
import re
import codecs
from urllib.parse import urlparse
import time
import base64
import requests
import uuid

from .forms import ParserForm
from .models import PresetParser, AffiliateNetwork, DownloadedPromo, ParserBatch
from .models import Geo
from .models import Option
from .api_keitaro import ApiKeitaro



class HandlerParser:
    """ Класс для бизнес-логики парсера """

    template_offer_link = str()  # Шаблон для ссылок в прокле
    site_download = str()  # Ссылка сайта для скачивания
    url_download = str()  # Ссылка сайта с index.html для скачивания
    path_download = str()  # Путь куда скачивать промо
    path_site = str()  # Путь к каталогу сайта
    path_index_html = str()  # Путь к index.html от промо
    name_site = str()  # Название сайта
    promo_zip = str()  # Путь к заархивированному промо
    messages_info = list()
    messages_success = list()
    zip_site = ''
    model = ''

    def _add_in_log(self, logger_line):
        self.log.append(logger_line)

        if settings.DEBUG:
            print(logger_line)

    def __init__(self, **kwargs):
        self.log = list()
        self.keitaro_folder_name = str(kwargs.get('keitaro_folder_name'))
        if kwargs.get('parser_batch_id'):
            self.parser_batch = ParserBatch.objects.get(pk=kwargs.get('parser_batch_id'))
        else:
            self.parser_batch = None
        self._add_in_log('Parser Batch ID: {}'.format(self.parser_batch))

        self.keitaro_server_number = str(kwargs.get('keitaro_server_number'))
        self._add_in_log('Keitaro Server Number: {}'.format(self.keitaro_server_number))

        self.keitaro_group_id = str(kwargs.get('keitaro_group_id'))
        self._add_in_log('Keitaro Group ID: {}'.format(self.keitaro_group_id))

        self.keitaro_landing_name = str(kwargs.get('keitaro_landing_name'))
        self._add_in_log('Keitaro Landing Name: {}'.format(self.keitaro_landing_name))

        if  kwargs.get('keitaro_affiliate_network_id', None) is None:
            self.keitaro_affiliate_network_id = None
        else:
            self.keitaro_affiliate_network_id = int(kwargs.get('keitaro_affiliate_network_id'))
            self._add_in_log('Keitaro Affiliate Network ID: {}'.format(self.keitaro_affiliate_network_id))

        if kwargs.get('preset_id'):
            self.preset = PresetParser.objects.get(pk=kwargs.get('preset_id'))
        else:
            self.preset = None
        self._add_in_log('Preset: {}'.format(self.preset))

        if kwargs.get('url'):
            self.url = kwargs.get('url')
            self._add_in_log('URL: {}'.format(self.url))
            self.archive_upload_path = None
        elif kwargs.get('archive_upload_path'):
            self.archive_upload_path = kwargs.get('archive_upload_path')
            self._add_in_log('Archive Upload Path: {}'.format(self.archive_upload_path))
            self.url = None

        self.type_promo = int(kwargs.get('type_promo'))
        self._add_in_log('Type Promo: {}'.format(self.type_promo))

        self.offer_id = str(kwargs.get('offer_id'))
        self._add_in_log('Offer ID: {}'.format(self.offer_id))

        self.source_id = str(kwargs.get('source_id'))
        self._add_in_log('Source ID: {}'.format(self.source_id))

        if kwargs.get('geo_id'):
            self.geo = Geo.objects.get(pk=kwargs.get('geo_id'))
        else:
            self.geo = None
        self._add_in_log('GEO: {}'.format(self.geo))

        # self.is_clear_all_script = kwargs.get('is_clear_all_script')
        # self._add_in_log('Clear ALL script: {}'.format(self.is_clear_all_script))

        # self.is_download_success_html = kwargs.get('is_download_success_html', False)
        # self._add_in_log('Download success.html: {}'.format(self.is_download_success_html))

        self.is_add_user_form = kwargs.get('is_add_user_form')
        self._add_in_log('Adding user form: {}'.format(self.is_add_user_form))

        try:
            self.owner = User.objects.get(pk=int(kwargs.get('user_id')))
        except:
            self.owner = None
        self._add_in_log('User: {}'.format(self.owner))

        try:
            self.aff_network_webvork = AffiliateNetwork.objects.get(name=AffiliateNetwork.AFF_WEBVORK)
        except:
            self.aff_network_webvork = None

        try:
            self.aff_network_everad = AffiliateNetwork.objects.get(name=AffiliateNetwork.AFF_EVERAD)
        except:
            self.aff_network_everad = None

        try:
            self.aff_network_leadbit = AffiliateNetwork.objects.get(name=AffiliateNetwork.AFF_LEADBIT)
        except:
            self.aff_network_leadbit = None

        try:
            self.aff_network_terraleads = AffiliateNetwork.objects.get(name=AffiliateNetwork.AFF_TERRALEADS)
        except:
            self.aff_network_terraleads = None

        try:
            self.aff_network_luckyonline = AffiliateNetwork.objects.get(name=AffiliateNetwork.AFF_LUCKY_ONLINE)
        except:
            self.aff_network_luckyonline = None

        # Подготовить данные
        self.can_handle = self.prepare_data()

        self.proxy = Option.get_value_by_name('parser.proxy')

    def prepare_data(self):
        """ Подготовить данные """

        # Если промо "прокладка", то подставляем макросы соответствующего трекера
        if self.type_promo == ParserForm.TYPE_PROMO_PRE_LANDING:
            if self.preset and self.preset.tracker == PresetParser.TRACKER_BINOM:
                self.template_offer_link = '{offer_link}'
            elif self.preset and self.preset.tracker == PresetParser.TRACKER_KEITARO:
                self.template_offer_link = '{offer}'

        if self.url:
            url_segments = urlparse(self.url)
            self.site_download = '{}://{}{}'.format(url_segments.scheme, url_segments.netloc, url_segments.path)

            if self.site_download[-10:] != 'index.html':
                if self.site_download[-1] != '/':
                    self.site_download += '/'
                self.url_download = self.site_download + 'index.html'
            else:
                self.url_download = self.site_download
            self._add_in_log('url_download: {}'.format(self.url_download))

            # * Пока отключил проверку, потому что некоторые промики специально возращают код ошибки сервера, чтобы не парсился ленд
            # response = requests.get(self.url_download)
            # if response.status_code != 200:
            #     self._add_in_log(f'Не доступен URL! Ошибка ответа {response.status_code}')
            #     return False

            self.name_site = uuid.uuid4()
            self._add_in_log('name_site: {}'.format(self.name_site))

            """Относительный путь к папке парсера + имя сайта"""
            self.path_download = './media/temp/parser/{}'.format(self.name_site)
            self._add_in_log('path_download: {}'.format(self.path_download))

            """Абсолютный путь к папке парсера + путь до папки, где лежит index.html"""
            self.path_site = '{}/{}'.format(settings.PARSER_PATH_SAVE, self.name_site)
            self._add_in_log('path_site: {}'.format(self.path_site))

            self.path_index_html = self.path_site + '/' + 'index.html'
            self._add_in_log('path_index_html: {}'.format(self.path_index_html))
        elif self.archive_upload_path:
            self.name_site = '{}'.format(self.archive_upload_path.split('/')[-1][1:-4])
            self._add_in_log('name_site: {}'.format(self.name_site))

            self.path_download = './media/temp/parser/{}'.format(self.name_site)
            self._add_in_log('path_download: {}'.format(self.path_download))

            with ZipFile(self.archive_upload_path, 'r') as z:
                self.path_site = '{}/{}'.format(settings.PARSER_PATH_SAVE, self.name_site)
                self._add_in_log('path_site: {}'.format(self.path_site))

                self.path_index_html = self.path_site + '/' + 'index.html'
                self._add_in_log('path_index_html: {}'.format(self.path_index_html))

                z.extractall(self.path_site)

        return True

    def download_site(self):
        """ Скачать сайт (index.html) """

        '''
        Скачать:
        wget -r -k -i -E -F -p -nd -e robots=off URL_SITE
        -r - рекурсивная загрука
        -k - коррекция гиперссылок так, чтобы они стали локальными.
        -i - скачивание файлов по ссылкам в HTML-документе
        -p - загрузка вспомогательных элементов для отображения Web-страницы: CSS, JavaScript и т.п.
        -q - выключить вывод сообщений
        -E - добавить к файлу расширение .html
        -F - при чтении URL из файла, включает чтение файла как HTML.
        '''

        '''
        Используемые прокси с 30 августа 2021:
        http://syrup:qQWFFQWfq@192.248.183.36:30160
        '''

        if self.url:
            print('Начинаем парсить промо...')
            command = 'wget -r -k -i -l -E -F -p -q -nd -e robots=off {} -P {}'.format(
                # self.proxy,
                self.url_download,
                self.path_site
            )
            os.system(command)
            print(self.path_site)
            print(os.path.exists(self.path_site + '/index.html'))
            if os.path.exists(self.path_site + '/index.html'):
                self._add_in_log('Скачался через wget промо.')
            else:
                self._add_in_log('Ошибка! Не скачался через wget промо.')

    def edit_success_html(self):
        """ Изменить success.html """

        if os.path.exists(self.path_site + '/success.html'):
            if self.type_promo in [ParserForm.TYPE_PROMO_LANDING_WITH_OFFER, ParserForm.TYPE_PROMO_PRE_LANDING_WITH_OFFER]:
                if self.preset:
                    fr = codecs.open(self.path_site + '/success.html', 'r', encoding='utf-8')
                    data = fr.read()

                    # Удалить все JS скрипты со страницы "спасибо"
                    data = re.sub(r'<\s*script\b[^<]*(?:(?!<\/script\s*>)<[^<]*)*<\s*\/\s*script\s*>', '', data)
                    self._add_in_log('success.html: удалены все скрипты.')

                    # Всегда удалять скрипт Leadbit.js
                    data = re.sub(r'ld.js', '_', data)
                    self._add_in_log('success.html: почищены скрипты leadbit.js.')

                    if self.preset.traffic_source == PresetParser.TRAFFIC_SOURCE_FB:
                        # Вставить Pixel FB, если это источник Facebook

                        pixel_fb = '''
                        <!-- Facebook Pixel Code -->
                        <script>
                        !function(f,b,e,v,n,t,s)
                        {if(f.fbq)return;n=f.fbq=function(){n.callMethod?
                        n.callMethod.apply(n,arguments):n.queue.push(arguments)};
                        if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
                        n.queue=[];t=b.createElement(e);t.async=!0;
                        t.src=v;s=b.getElementsByTagName(e)[0];
                        s.parentNode.insertBefore(t,s)}(window, document,'script',
                        'https://connect.facebook.net/en_US/fbevents.js');
                        fbq('init', '<?= $_GET["px"] ?>');
                        fbq('track', 'Lead');
                        fbq('track', 'AddToCart');
                        fbq('track', 'Purchase', {value: 0.00, currency: 'USD'});
                        fbq('track', 'SubmitApplication');
                        fbq('track', 'Contact');
                        </script>
                        <!-- End Facebook Pixel Code -->
                        </head>
                        '''
                        data = re.sub(r'</head>', pixel_fb, data)

                        self._add_in_log('success.html: Добавлен Facebook Pixel (Purchase)')
                    elif self.preset.traffic_source == PresetParser.TRAFFIC_SOURCE_MGID:
                        # Вставить MGID Sensor, если это источник MGID

                        data_mgid_sensor = '''
                        <script type="text/javascript">!function(){var e=document,a=window;a.MgSensorData=a.MgSensorData||[],a.MgSensorData.push({cid:501350,lng:"us",nosafari:!0,project:"a.mgid.com"});var t=e.getElementsByTagName("script")[0],n=e.createElement("script");n.type="text/javascript",n.async=!0;var r=Date.now?Date.now():(new Date).valueOf();n.src="//a.mgid.com/mgsensor.js?d="+r,t.parentNode.insertBefore(n,t)}();</script>
                        </head>
                        '''
                        data = re.sub(r'</head>', data_mgid_sensor, data)
                        self._add_in_log('success.html: mgid sensor - OK')

                    if self.preset.aff_network == self.aff_network_leadbit:
                        # Добавить style от Leadbit для success.html
                        style_order = '<style>body{margin:0;color:#fff;font:17px/25px Georgia,"Times New Roman",Times,serif;background:#1f242a;min-width:446px}img{border-style:none}a{text-decoration:none;color:#a82720}a:hover{text-decoration:underline}input,select,textarea{font:100% Georgia,"Times New Roman",Times,serif;vertical-align:middle;color:#000;outline:0}fieldset,form{margin:0;padding:0;border-style:none}q{quotes:none}q:before{content:''}q:after{content:''}#wrapper{width:100%;overflow:hidden;padding:50px 0}.container{width:440px;margin:0 auto;display:block;position:relative}.order-block{width:440px;border:4px dashed #fcca49;border-radius:30px;height:auto;margin:0 auto;position:relative;text-align:center;font-size:20px;line-height:30px;overflow:hidden;color:#d5e5eb}.order-block:after{display:block;clear:both;content:''}.decoration{background:url(../img/order-page-decoration.png) no-repeat;width:24px;height:32px;position:absolute;left:-23px;top:336px}.order-block .text-holder{padding:20px}.order-block h2{font:35px/35px Lobster,Arial,Helvetica,sans-serif;margin:0 0 59px;color:#fff}.order-block h2 span{display:block;font-size:45px;line-height:45px;color:#fcca49;margin:0 0 -2px}.order-block p{margin:0 0 18px}.order-block .text-box{bottom:20px;font-size:20px;line-height:30px;color:#1f242a;left:3px;width:100%;box-sizing:border-box;background:#fcca49;padding:20px}.order-block .text-box h2{font-size:35px;line-height:40px;color:#1f242a;margin:0 0 32px}.order-block .text-box h2 span{font-size:45px;line-height:45px;color:#ae1d1d;display:block;margin:-6px 0 0}.order-form{overflow:hidden}.order-form .text{background:url(../img/bg-order-page-text.png) no-repeat;width:253px;height:42px;float:left}.order-block .text-box p{margin:0 0 18px}.order-form .text input{background:0 0;border:none;width:227px;height:40px;float:left;font-size:16px;line-height:40px;color:#726033;padding:10px 13px 12px}.btn-save{border:none;background:url(../img/order-page-btn-save.png) no-repeat;width:129px;height:40px;float:right;font:20px/40px "Roboto Condensed",Arial,Helvetica,sans-serif;text-transform:uppercase;color:#fff;float:right;padding:0 0 2px;margin:0;cursor:pointer}</style></head>'
                        data = re.sub(r'</head>', style_order, data)
                        self._add_in_log('success.html: Добавлен style для спасибо от Leadbit')

                    with open(self.path_site + '/success.php', 'w', encoding='utf-8') as fw:
                        fw.write(data)
                        self._add_in_log('WGET success.html -> success.php')

    def download_success_html(self):
        """ Скачать страницу success.html """

        if self.url and self.type_promo == ParserForm.TYPE_PROMO_LANDING_WITH_OFFER:
            try:
                print('Начинаем парсить success.html...')
                command = 'wget -r -k -i -l -E -F -p -q -nd -e use_proxy=yes -e http_proxy=http://syrup:qQWFFQWfq@192.248.183.36:30160 -e robots=off {} -P {}'.format(
                    self.site_download + '/success.html',
                    self.path_site
                )
                os.system(command)

                if os.path.exists(self.path_site + '/success.html'):
                    self._add_in_log('Скачался через wget success.html')
                else:
                    self._add_in_log('Ошибка! Не скачался через wget success.html')
            except:
                pass

    def create_order_php(self):
        """ Создать файл order.php """

        data = self.preset.aff_network.order_php
        if data:
            # Вставить данные с формы в отведенные места в order.php
            data = re.sub('%OFFER_ID%', self.offer_id, data)
            self._add_in_log('order.php: Заменен ID оффера.')

            data = re.sub('%SOURCE_ID%', self.source_id, data)
            self._add_in_log('order.php: Заменен ID потока.')

            if self.preset:
                try:
                    data = re.sub('%TOKEN%', self.preset.token, data)
                    self._add_in_log('order.php: Заменен Token для API.')
                except:
                    pass

            if self.geo:
                data = re.sub('%GEO%', self.geo.iso.lower(), data)
                self._add_in_log('order.php: Заменены 2-буквы для ГЕО оффера.')

            with codecs.open(self.path_site + '/order.php', "w", encoding='utf-8') as f:
                f.write(data)
                self._add_in_log('Создан файл order.php с подготовленными значениями.')

    def _form_webvork(self, soup, form):
        """ Вставить input type=hidden, если ПП Webvork.com """

        if self.preset.tracker == PresetParser.TRACKER_KEITARO:

            # clickid
            soup_utm_medium = soup.find_all('input', {'name': "utm_medium"})
            if soup_utm_medium:
                for utm_medium in soup_utm_medium:
                    utm_medium['value'] = '{subid}'
                self._add_in_log('index.php: Для поля ввода utm_medium вставлено значение {subid}.')

            # px
            soup_utm_content = soup.find_all('input', {'name': "utm_content"})
            if soup_utm_content:
                for utm_content in soup_utm_content:
                    utm_content['value'] = '{sub_id_10}'
                self._add_in_log('index.php: Для поля ввода utm_content вставлено значение {sub_id_10}.')

            # Метка баера
            soup_utm_campaign = soup.find_all('input', {'name': "utm_campaign"})
            if soup_utm_campaign:
                for utm_campaign in soup_utm_campaign:
                    utm_campaign['value'] = '{sub_id_11}'
                self._add_in_log('index.php: Для поля ввода utm_campaign вставлено значение {sub_id_11}.')

        elif self.preset.tracker == PresetParser.TRACKER_BINOM:

            # clickid
            soup_utm_content = soup.find_all('input', {'name': "utm_content"})
            if soup_utm_content:
                for utm_content in soup_utm_content:
                    utm_content['value'] = '{clickid}'
                self._add_in_log('index.php: Для поля ввода utm_content вставлено значение {clickid}.')

            # Метка баера
            soup_utm_term = soup.find_all('input', {'name': "utm_term"})
            if soup_utm_term:
                for utm_term in soup_utm_term:
                    utm_term['value'] = '{user_id}'
                self._add_in_log('index.php: Для поля ввода utm_term вставлено значение {user_id}.')

    def _form_luckyonline(self, data):
        """ Вставить input type=hidden, если ПП Lucky.online """

        if self.preset.tracker == PresetParser.TRACKER_KEITARO:
            input_fields = '''
                    <input type="hidden" name="subid" value="{subid}">
                    <input type="hidden" name="subid1" value="{sub_id_10}">
                    <input type="hidden" name="subid2" value="{sub_id_11}">
                    </form>
                    '''
            data = re.sub(r'</form>', input_fields, data)

        return data

    def _form_everad(self, data):
        """ Вставить input type=hidden, если ПП Everad.com """

        if self.preset.tracker == PresetParser.TRACKER_KEITARO:
            input_fields = '''
                    <input type="hidden" name="sid5" value="{subid}">
                    <input type="hidden" name="sid2" value="{sub_id_10}">
                    <input type="hidden" name="sid1" value="{sub_id_11}">
                    </form>
                    '''
            data = re.sub(r'</form>', input_fields, data)

        elif self.preset.tracker == PresetParser.TRACKER_BINOM:
            input_fields = '''
                    <input type="hidden" name="sid1" value="{user_id}">
                    <input type="hidden" name="sid5" value="{clickid}">
                    </form>
                    '''
            data = re.sub(r'</form>', input_fields, data)

        return data

    def _form_terraleads(self, data):
        """ Вставить input type=hidden, если ПП Terraleads.com """

        if self.preset.tracker == PresetParser.TRACKER_KEITARO:
            input_fields = '''
                    <input type="hidden" name="sub_id" value="{subid}">
                    <input type="hidden" name="sub_id_1" value="{sub_id_10}">
                    <input type="hidden" name="sub_id_2" value="{sub_id_11}">
                    </form>
                    '''
            data = re.sub(r'</form>', input_fields, data)

        elif self.preset.tracker == PresetParser.TRACKER_BINOM:
            input_fields = '''
                    <input type="hidden" name="sid1" value="{user_id}">
                    <input type="hidden" name="sid5" value="{clickid}">
                    </form>
                    '''
            data = re.sub(r'</form>', input_fields, data)

        return data

    def _form_leadbit(self, data):
        """ Вставить input type=hidden, если ПП leadbit.com """

        if self.preset.tracker == PresetParser.TRACKER_KEITARO:

            input_fields = '''
                    <input type="hidden" name="sub1" value="{sub_id_11}">
                    <input type="hidden" name="sub2" value="{subid}">
                    <input type="hidden" name="sub3" value="">
                    <input type="hidden" name="sub4" value="{sub_id_10}">
                    <input type="hidden" name="sub5" value="">
                    </form>
                    '''
            data = re.sub(r'</form>', input_fields, data)

        elif self.preset.tracker == PresetParser.TRACKER_BINOM:

            input_fields = '''
                    <input type="hidden" name="sub1" value="{user_id}">
                    <input type="hidden" name="sub2" value="{clickid}">
                    <input type="hidden" name="sub3" value="">
                    <input type="hidden" name="sub4" value="">
                    <input type="hidden" name="sub5" value="">
                    </form>
                    '''
            data = re.sub(r'</form>', input_fields, data)

        return data

    def _edit_offer_form(self, soup, form):
        """ Добавить нужные теги на форме """

        form['method'] = 'POST'
        form['action'] = 'order.php'

        if self.preset.aff_network == self.aff_network_webvork:
            self._form_webvork(soup=soup, form=form)

    def add_user_form(self, soup):
        """ Вставить пользовательскую форма сбора лидов """

        form_tag = '''
                <div style="text-align: center; border: 1px solid black; padding: 40px; border-radius: 20px;">
                <form action="order.php" method="POST" id="form-lead" style="text-align: center;">
                <label for="form-lead-input-name">Name:</label>
                <input name="name" id="form-lead-input-name" required="" type="text" style="margin-bottom: 10px;" /><br/>
                <label for="form-lead-input-phone">Phone:</label>
                <input name="phone" id="form-lead-input-phone" required="" type="text" style="margin-bottom: 10px;"/><br/>
                <input type="submit"/>
                </form>
                </div>
                '''
        soup_form_tag = BeautifulSoup(form_tag, 'html.parser')
        soup.find('footer').replace_with(soup_form_tag)


    def _handler_beautifulsoup_for_index(self):
        """ Все манипуляции с файлом index.html через BeautifulSoup """

        with open(self.path_index_html, 'r', encoding='utf-8') as fr:
            soup = BeautifulSoup(fr.read(), 'html.parser')

        # Добавить пользовательскую форму перед первым тегом <footer>
        if self.is_add_user_form:
            self.add_user_form(soup)

        # Прокла или Прокла с оффером: Заменить ссылки на макрос трекера
        if self.type_promo in [ParserForm.TYPE_PROMO_PRE_LANDING, ParserForm.TYPE_PROMO_PRE_LANDING_WITH_OFFER]:
            for a in soup.find_all('a'):
                a['href'] = self.template_offer_link
            self._add_in_log('index.html: Заменены все ссылки на {}.'.format(self.template_offer_link))

            for span in soup.find_all('span'):
                if "data-href" in span.attrs:
                    span['data-href'] = self.template_offer_link
            self._add_in_log('index.html: В ссылки ссылки вида span[data-href=...] вставлено {}.'.format(self.template_offer_link))

        # Прокла или Прокла с оффером/MGID/Binom : Добавить соцметрики js
        if self.type_promo in [ParserForm.TYPE_PROMO_PRE_LANDING, ParserForm.TYPE_PROMO_PRE_LANDING_WITH_OFFER] \
                and self.preset.tracker == PresetParser.TRACKER_BINOM:
            # Вставить в head скрипт для отслеживания соц метрик с проклы
            soup.head.append('<script src="https://kreol.life/landers/libs/events.js"></script>')
            self._add_in_log('index.html: Добавлен js для отбивки соц метрик в Binom (с проклы).')

            # Вставить в head скрипт для отслеживания ботов и хостов с проклы
            soup.head.append('<script src="https://kreol.life/landers/libs/bot-detection.js"></script>')
            self._add_in_log('index.html: Добавлен js для определения ботов и отбивки в Binom.')

        # Лендинг с оффером/MGID/Binom : Соцметрики
        if self.type_promo in [ParserForm.TYPE_PROMO_LANDING_WITH_OFFER, ParserForm.TYPE_PROMO_PRE_LANDING_WITH_OFFER] \
                and self.preset.tracker == PresetParser.TRACKER_BINOM \
                and self.preset.traffic_source == PresetParser.TRAFFIC_SOURCE_MGID:
            # Вставить в head скрипт для отслеживания соц метрик с лендинга
            soup.head.append('<script src="https://kreol.life/landers/libs/events-lp.js"></script>')
            self._add_in_log('index.html: Добавлен js для отбивки соц метрик в Binom (с ленда оффера).')

        # Лендинг с оффером или Прокла с оффером : доработка формы
        if self.type_promo in [ParserForm.TYPE_PROMO_LANDING_WITH_OFFER, ParserForm.TYPE_PROMO_PRE_LANDING_WITH_OFFER]:
            elem_form = None
            for elem_form in soup.find_all('form'):
                self._edit_offer_form(soup, elem_form)

            if elem_form:
                # Это последняя форма на странице, на нее будет якорь
                elem_form['id'] = 'anchor-form-order'

            # Добавить атрибут required для input с названием name
            elements_input_name = soup.find_all('input', {'name': "name"})
            print(elements_input_name)
            if elements_input_name:
                for elem_input in elements_input_name:
                    print(elem_input)
                    elem_input['required'] = ''

            # Добавить атрибут required для input с названием phone
            elements_input_phone = soup.find_all('input', {'name': "phone"})
            if elements_input_phone:
                for elem_input in elements_input_phone:
                    elem_input['required'] = ''

        # Лендинг с оффером : доработка лендинга
        if self.type_promo in [ParserForm.TYPE_PROMO_LANDING_WITH_OFFER]:
            for elem_a in soup.find_all('a'):
                elem_a['href'] = '#anchor-form-order'
            self._add_in_log('index.html: Заменены все ссылки на якоря формы "{}".'.format('#anchor-form-order'))

        with open(self.path_index_html, 'w', encoding='utf-8') as fw:
            fw.write(soup.prettify())

    def _add_pixel_fb_for_keitaro(self, data):
        """ Вставить pixel fb с сабами кейтаро """

        pixel_fb = '''
            <!-- Facebook Pixel Code -->
            <script>
              !function(f,b,e,v,n,t,s)
              {if(f.fbq)return;n=f.fbq=function(){n.callMethod?
              n.callMethod.apply(n,arguments):n.queue.push(arguments)};
              if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
              n.queue=[];t=b.createElement(e);t.async=!0;
              t.src=v;s=b.getElementsByTagName(e)[0];
              s.parentNode.insertBefore(t,s)}(window, document,'script',
              'https://connect.facebook.net/en_US/fbevents.js');
              fbq('init', '{sub_id_10}');
              fbq('track', 'ViewContent', {
                content_name: 'Homepage of the site',
                content_category: 'Goods',
                content_type: 'product'
              });
            </script>
            <noscript>
              <img height="1" width="1" style="display:none"
                   src="https://www.facebook.com/tr?id={sub_id_10}&ev=PageView&noscript=1"/>
            </noscript>
            <!-- End Facebook Pixel Code -->
            </head>
            '''
        return re.sub(r'</head>', pixel_fb, data)

    def _handler_custom_for_index(self):
        """ Все манипуляции с файлом index.html стандартным способом """

        with open(self.path_index_html, "r", encoding='utf-8') as fr:
            data = fr.read()

        # Лендинг с оффером или Прокла с оффером : доработка формы
        if self.type_promo in [ParserForm.TYPE_PROMO_LANDING_WITH_OFFER, ParserForm.TYPE_PROMO_PRE_LANDING_WITH_OFFER]:
            if self.preset.aff_network == self.aff_network_everad:
                data = self._form_everad(data)
            elif self.preset.aff_network == self.aff_network_terraleads:
                data = self._form_terraleads(data)
            elif self.preset.aff_network == self.aff_network_leadbit:
                data = self._form_leadbit(data)
            elif self.preset.aff_network == self.aff_network_luckyonline:
                data = self._form_luckyonline(data)

        # Прокла или Прокла с оффером : Вставка Pixel FB (PageView)
        if self.type_promo in [ParserForm.TYPE_PROMO_PRE_LANDING, ParserForm.TYPE_PROMO_PRE_LANDING_WITH_OFFER] \
                and self.preset.tracker == PresetParser.TRACKER_KEITARO \
                and self.preset.traffic_source == PresetParser.TRAFFIC_SOURCE_FB:
            # data = self._add_pixel_fb_for_keitaro(data)  # убрал пиксель по таску 1401
            pass

        with open(self.path_index_html, "w", encoding='utf-8') as fw:
            fw.write(data)

    def edit_index_file(self):
        """ Изменение index.html """

        self._handler_beautifulsoup_for_index()
        self._handler_custom_for_index()

        # Изменить расширение с index.html на index.php
        p = Path(self.path_index_html)
        p.rename(Path(self.path_site+'/index.php'))
        self._add_in_log('index.html => index.php.')

    def _clear_javascript_in_index_file(self):
        """ Удалить script'ы из файла index """

        with open(self.path_index_html, "r", encoding='utf-8') as fr:
            data = fr.read()

        # Удалить все скрипты со страницы index
        # self.javascript = self.is_clear_all_script
        # if self.javascript:
        #     data = re.sub(r'<\s*script\b[^<]*(?:(?!<\/script\s*>)<[^<]*)*<\s*\/\s*script\s*>', '', data)
        #     self._add_in_log('Очищены скрипты.')

        # Очистка скрипта leadbit.com
        if self.preset.aff_network == self.aff_network_leadbit:
            data = re.sub(r'leadbit', '_', data)
            data = re.sub(r'ld.js', '_', data)
            self._add_in_log('Автоматически удален скрипт leadbit.js.')

        # Очистка скрипта Webvork.com
        if self.preset.aff_network == self.aff_network_webvork:
            data = re.sub(r'webvork', '_', data)
            data = re.sub(r'webvkrd', '_', data)
            self._add_in_log('Автоматически удален скрипт webvork.js.')

        # Очистка скрипта Everad.com
        if self.preset.aff_network == self.aff_network_everad:
            data = re.sub(r'everad', '_', data)
            self._add_in_log('Автоматически удален скрипт everad.js.')

        with open(self.path_index_html, "w", encoding='utf-8') as fw:
            fw.write(data)

    def edit_site(self):
        """ Редактирование скачанного промо """

        # Удалить script'ы из файла index
        self._clear_javascript_in_index_file()

        # Если пресет указан, то делаем все возможные доработки по промо
        if self.preset:
            self.edit_index_file()

            if self.type_promo in [ParserForm.TYPE_PROMO_LANDING_WITH_OFFER, ParserForm.TYPE_PROMO_PRE_LANDING_WITH_OFFER]:
                self.create_order_php()

    def edit_other_files(self):
        if self.preset.aff_network == self.aff_network_terraleads:
            # Очистка скрипта Terraleads.com

            with open(self.path_site + '/' + 'script_land.js', "r", encoding='utf-8') as fr:
                data = fr.read()

            data = re.sub(r'api.php', 'order.php', data)

            with open(self.path_site + '/' + 'script_land.js', "w", encoding='utf-8') as fw:
                fw.write(data)

    def archive_site(self):
        """ Заархивировать промо """
        print("archive")
        # self.promo_zip = '{}/{}.zip'.format(settings.PARSER_PATH_SAVE, self.name_site)
        # self.promo_dir = '{}/{}'.format(settings.PARSER_PATH_SAVE, self.name_site)
        # print(self.promo_zip)
        # import os
        #
        # foo = ZipFile(self.promo_zip, 'w')
        # print("flag1")
        # foo.write(self.promo_dir)
        # print("flag2")
        #
        # # Adding files from directory 'files'
        # for root, dirs, files in os.walk(self.path_download):
        #     for f in files:
        #         foo.write(os.path.join(root, f))
        # foo.close()
        """ Заархивировать промо """

        paths_files = []
        print(self.path_download)
        for root, directories, files in os.walk(self.path_download):
            for filename in files:
                filepath = os.path.join(root, filename)
                paths_files.append(filepath)
        self._add_in_log('Список файлов для архивирования готов.')

        self.promo_zip = '{}/{}.zip'.format(settings.PARSER_PATH_SAVE, self.name_site)
        with ZipFile(self.promo_zip, 'w') as z:
            for path in paths_files:
                try:
                    z.write(path)
                except:
                    pass
            self._add_in_log('Промо заархивировано.')

    def remove_site(self):
        """ Удалить рекурсивно скаченный сайт """

        if self.url:
            try:
                shutil.rmtree('{}/{}'.format(settings.PARSER_PATH_SAVE, self.name_site))
                self._add_in_log('Удалена временная папка.')
            except:
                self._add_in_log('ERROR! Не удалось удалить временную папку.')
        elif self.archive_upload_path:
            try:
                os.remove(self.archive_upload_path)
                self._add_in_log('Удален загруженный архив пользователем от ПП.')
            except:
                self._add_in_log('ERROR! Не удалось удалить загруженный архив пользователем от ПП.')

    def create_record(self):
        """ Создать начальную запись о том что была скачка """

        if self.url:
            url_promo = self.url
        else:
            url_promo = self.name_site

        self.model = DownloadedPromo.objects.create(
            url_promo=url_promo,
            type_promo=self.type_promo,
            preset=self.preset,
            owner=self.owner,
            parser_batch=self.parser_batch
        )
        print(f'Создана запись id={self.model}.')

    def add_promo_in_record(self):
        """Создать запись."""

        #         # self.promo_zip = f'{settings.PARSER_PAT
        #         self.model.status = DownloadedPromo.STATUS_DOWNLOAH_SAVE}/lp3.zip'  # для тестов

        self.model.archive_promo = self.promo_zip
        self.model.log = self.log
        self.model.save()
        print(f'Сохранен промо в БД.')

    def save_error_for_parser_batch(self, text_error):
        self.parser_batch.status = ParserBatch.STATUS_ERROR
        self.parser_batch.save()

    def upload_to_keitaro(self):
        """Загрузить промо в keitaro"""

        if self.keitaro_server_number not in ["1", "2"]:
            print(f'В Keitaro не загружаем.')
            return

        print(f'Перемещаем в Keitaro{self.keitaro_server_number}...')

        # Кодируем архив в base64
        with open(self.promo_zip, 'rb') as f:
            bytes = f.read()
            encode_string = base64.b64encode(bytes)
            archive_string = encode_string.decode('ascii')

        # Получаем Api-Key для Keitaro
        api_key = Option.get_value_by_name(f'keitaro{self.keitaro_server_number}.api-key')

        # Отправляем промо в Keitaro
        print(self.keitaro_server_number)
        print(api_key)
        try:
            api = ApiKeitaro(api_key, self.keitaro_server_number)
            data = {
                "name": self.keitaro_landing_name,
                "group_id": self.keitaro_group_id,
                "archive_string": archive_string,
                "keitaro_folder_name": self.keitaro_folder_name,
            }

            if self.type_promo == ParserForm.TYPE_PROMO_PRE_LANDING:
                response = api.post_create_landing_pages(data)
                keitaro_type_promo = DownloadedPromo.KEITARO_TYPE_PROMO_LANDING
            else:
                data.update({
                    "country": self.geo.iso,
                    "affiliate_network_id": self.keitaro_affiliate_network_id,
                    "notes": f"API: promoId={self.model.pk}; created={time.time()};"
                })
                response = api.post_create_offer(data)
                keitaro_type_promo = DownloadedPromo.KEITARO_TYPE_PROMO_OFFER
            try:
                result = response.json()
            except:
                result = response
            print(result)
            print('id' in result)
        except Exception as e:
            print("@#!#!@#")
            print(e)
            text_error = 'Не удалось выполнить API запрос к Keitaro'
            if self.parser_batch:
                self.save_error_for_parser_batch(text_error)
            self._add_in_log('ОШИБКА загрузки в Keitaro:')
            self._add_in_log(text_error)
            self.model.status = DownloadedPromo.STATUS_KEITARO_ERROR
            self.model.save()

            return False
        if 'id' in result:
            self._add_in_log('УСПЕШНО загружен в Keitaro:')
            self._add_in_log('Keitaro promo ID {0}: {1}'.format(keitaro_type_promo, result.get('id')))
            self._add_in_log('local_path {0}: {1}'.format(keitaro_type_promo, result.get('local_path')))

            self.model.keitaro_type_promo = keitaro_type_promo
            self.model.keitaro_promo_id = result.get('id')
            self.model.status = DownloadedPromo.STATUS_KEITARO_OK
            self.model.save()

            if self.parser_batch:
                self.parser_batch.status = 3
                self.parser_batch.save()
                print(self.parser_batch.status)
                print(self.parser_batch)
                print(self.parser_batch)


            return True
        else:
            text_error = response.text
            if self.parser_batch:
                self.save_error_for_parser_batch(response.text)
            self._add_in_log('ОШИБКА отправки в Keitaro:')
            self._add_in_log(text_error)
            self.model.status = DownloadedPromo.STATUS_KEITARO_ERROR
            self.model.save()
            return False

    def run(self):
        """Запуск парсера."""

        self.create_record()

        if self.can_handle:
            try:
                self.download_site()
                self.edit_site()
                self.edit_other_files()
                self.download_success_html()
                self.edit_success_html()
                self.archive_site()
                # self.remove_site()
                self.add_promo_in_record()
                self.upload_to_keitaro()

                return True
            except Exception as err:
                self.log.append(err)
                print(err)

                self.model.status = DownloadedPromo.STATUS_ERROR
                self.model.log = self.log
                self.model.save()

                return False
        else:
            self.model.status = DownloadedPromo.STATUS_ERROR
            self.model.log = self.log
            self.model.save()

            return False
