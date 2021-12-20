from django import forms

import requests

from .models import PresetParser, AffiliateNetwork, ParserBatch
# from .api_cloudflare import ApiCloudflare
from .models import Geo
# from app_storage.utils import has_group
# from app_storage.models import Option, Profile
# from app_storage.api_keitaro import ApiKeitaro


class ParserForm(forms.Form):
    """Форма для скачивания ленда или проклы."""

    # Тип промо
    TYPE_PROMO_PRE_LANDING = 1
    TYPE_PROMO_LANDING_WITH_OFFER = 2
    TYPE_PROMO_PRE_LANDING_WITH_OFFER = 3
    TYPE_PROMO_CHOICES = [
        (TYPE_PROMO_PRE_LANDING, 'Прокла'),
        (TYPE_PROMO_LANDING_WITH_OFFER, 'Ленд с оффером'),
        (TYPE_PROMO_PRE_LANDING_WITH_OFFER, 'Прокла с оффером'),
    ]

    # Название js-скрипта
    SCRIPT_LEADBIT = 1
    SCRIPT_WEBVORK = 2
    SCRIPT_EVERAD = 3
    SCRIPT_CHOICES = [
        (0, '---------'),
        # (SCRIPT_LEADBIT, 'leadbit.js'),  # Удаляется автоматом
        (SCRIPT_WEBVORK, 'webvork.js'),
        (SCRIPT_EVERAD, 'everad.js'),
    ]

    # Название js-скрипта
    KEITARO_1 = 1
    KEITARO_2 = 2
    KEITARO_CHOICES = [
        (0, '---------'),
        (KEITARO_1, 'Keitaro1'),
        (KEITARO_2, 'Keitaro2'),
    ]

    preset = forms.ModelChoiceField(
        label='Выберите пресет:',
        queryset=None,
        required=False,
        help_text='Если пресет не выбран, то просто скачается промо без обработки index.html'
    )
    type_promo = forms.ChoiceField(label='Тип промо', choices=TYPE_PROMO_CHOICES, required=False)
    offer_id = forms.CharField(label='ID оффера', required=False)
    source_id = forms.CharField(label='ID потока', required=False)
    geo = forms.ModelChoiceField(label='Гео', required=False, queryset=Geo.objects.all())
    # TODO: is_clear_all_script убрать из формы и обработчика
    # is_clear_all_script = forms.BooleanField(
    #     label='Удалить ВСЕ скрипты',
    #     required=False,
    #     help_text='Могут перестать работать таймеры, подставнока дат, рулетка и тд.'
    # )
    # is_download_success_html = forms.BooleanField(label='Скачать доступный /success.html, обработать и добавить на него pixel', required=False)
    url = forms.CharField(
        label='Укажите URL промо:',
        help_text='Вариант 1. Укажите URL, который необходимо скачать и обработать. Если в этом поле что-то указано, '
                  'то обрабатывается этот вариант.',
        required=False)
    file_archive = forms.FileField(
        label='Выберите архив с промо от ПП:',
        help_text='Вариант 2. Выберите архив (zip). Папку с файлами не архивировать! Необходимо выделить все файлы внутри папки '
                  'и заархивировать в zip.',
        required=False
    )
    is_add_user_form = forms.BooleanField(
        label='Добавить форму для сбора лидов (вместо &lt;footer&gt;). Работает, когда выбрана "Прокла с оффером" или "Ленд с оффером"',
        required=False
    )
    keitaro_server_number = forms.ChoiceField(
        label='Загрузить в Keitaro?', choices=KEITARO_CHOICES, required=False)
    keitaro_landing_name = forms.CharField(
        label='Название промо', max_length=100, required=False)
    keitaro_group_id = forms.ChoiceField(
        label='ID группы из Keitaro',
        choices=[(n, n,) for n in range(1000)], # Костыль для формирования псевда-списка, чтобы прошел валидацию
        required=False
    )

    @classmethod
    def get_num_aff_network_script(cls, aff_network_name):
        """Получить Номер JS-скрипта ПП."""

        if aff_network_name == 'Leadbit.com':
            return cls.SCRIPT_LEADBIT
        elif aff_network_name == 'Webvork.com':
            return cls.SCRIPT_WEBVORK
        elif aff_network_name == 'Everad.com':
            return cls.SCRIPT_EVERAD
        else:
            return None

    @classmethod
    def get_type_promo_value(cls, type_promo):
        if type_promo == cls.TYPE_PROMO_PRE_LANDING:
            return 'Прокла'
        elif type_promo == cls.TYPE_PROMO_LANDING_WITH_OFFER:
            return 'Ленд с оффером'
        elif type_promo == cls.TYPE_PROMO_PRE_LANDING_WITH_OFFER:
            return 'Прокла с оффером'

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request')
        super(ParserForm, self).__init__(*args, **kwargs)

        if has_group(request.user, 'Тимлиды') or has_group(request.user, 'Верстальщики'):
            self.fields['preset'].queryset = PresetParser.objects.filter(pk__in=(1, 3, 4, 9, 10,))
            self.fields['keitaro_server_number'].choices = [(0, '---------'), (self.KEITARO_1, 'Keitaro1'),]
        elif has_group(request.user, 'Руководители'):
            self.fields['preset'].queryset = PresetParser.objects.all()


class PresetParserForm(forms.ModelForm):
    """Форма для добавления/редактирования Пресета парсера."""

    class Meta:
        model = PresetParser
        fields = ('name', 'tracker', 'traffic_source', 'aff_network', 'token',)


class AffiliateNetworkForm(forms.ModelForm):
    """Форма для добавления/редактирования Партнерской сети."""

    order_php = forms.CharField(
        widget=forms.Textarea,
        help_text='Используются макросы: %GEO% - подставляет 2 буквы ГЕО, %TOKEN% - подставляет токен API для ПП, '
                  '%OFFER_ID% - ID оффера, %CAMPAIGN_ID% - ID кампании, %SOURCE_ID% - ID или хэш потока.'
    )

    class Meta:
        model = AffiliateNetwork
        fields = ('name', 'order_php',)


class ParserBatchForm(forms.ModelForm):
    """Форма для пакетного скачивания промо."""

    class Meta:
        model = ParserBatch
        fields = ('text_tasks',)
        widgets = {
            "text_tasks": forms.Textarea(attrs={"placeholder": "Формат строчки: URL_ПРОМО;ПРЕСЕТ:1|2|3|4|5|6;ТИП_ПРОМО:1|2|3;ID_ОФФЕРА_ПП;ID_ПОТОКА_ПП;ГЕО;СКАЧАТЬ_СПАСИБО:1|0;НАЗВАНИЕ_ИСХОДЯЩЕГО_АРХИВА;ID_ГРУППЫ_KEITARO;НОМЕР_КЕЙТАРО:1|2;ПАРТНЕРСКАЯ_СЕТЬ_ID_КЕЙТАРО"}),
        }
        help_texts = {
            'text_tasks': 'Формат строчки: URL_ПРОМО;ПРЕСЕТ:1|2|3|4|5|6;ТИП_ПРОМО:1|2|3;ID_ОФФЕРА_ПП;ID_ПОТОКА_ПП;ГЕО;'
                          'СКАЧАТЬ_СПАСИБО:1|0;НАЗВАНИЕ_ИСХОДЯЩЕГО_АРХИВА;ID_ГРУППЫ_KEITARO;НОМЕР_КЕЙТАРО:1|2;'
                          'ПАРТНЕРСКАЯ_СЕТЬ_ID_КЕЙТАРО',
        }

class AddDomainsKeitaroForm(forms.Form):
    """Форма для создания домена в Keitaro."""

    # Keitaro
    KEITARO_1 = 1
    KEITARO_2 = 2
    KEITARO_CHOICES = [
        (KEITARO_1, 'keitaro1.tk'),
        (KEITARO_2, 'keitaro2.tk')
    ]

    domains = forms.CharField(
        label='Список доменов',
        widget=forms.Textarea(attrs={'rows': 5}),
        help_text='Введите через запятую список доменов. Например: domain1.ru, domain2.com',
        required=True
    )
    keitaro = forms.ChoiceField(
        label='Keitaro',
        choices=KEITARO_CHOICES,
        required=True
    )

    def sendToKeitaro(self):
        """Отправить домены в Keitaro"""

        keitaro = self.cleaned_data.get('keitaro')
        option_name = f'keitaro{keitaro}.api-key'
        keitaro_api_key = Option.get_value_by_name(option_name)

        domains_list = self.cleaned_data.get('domains').split(',')

        for domain in domains_list:
            domain.strip()

            api = ApiKeitaro(keitaro_api_key, keitaro)
            data = {
                "name": domain
            }
            api.post_create_domain(data)


class AddDomainsCloudflareForm(forms.Form):
    """Форма для добавления домена в Cloudflare."""


    domains = forms.CharField(
        label='Список доменов',
        widget=forms.Textarea(attrs={'rows': 5}),
        help_text='Введите через запятую список доменов. Например: domain1.ru, domain2.com',
        required=True
    )
    email = forms.CharField(
        label="Email",
        max_length=255,
        required=True,
        help_text='Email к учетной записи Cloudflare',
        # initial='syrup.agency.service1@gmail.com',
    )
    global_api_key = forms.CharField(
        label="Global API Key",
        max_length=255,
        required=True,
        help_text='Перейти сюда <a href="https://dash.cloudflare.com/profile/api-tokens" target="_blank">https://dash.cloudflare.com/profile/api-tokens</a>. Нажать на кнопку View на против надписи Global API Key и скопировать код в это поле.',
        # initial='8520c83645ea75d2c3a05f2955f2b704daee5',
    )
    api_account_id = forms.CharField(
        label="API Account ID",
        max_length=255,
        required=True,
        help_text='Находится при клике на любом домене -> блок внизу справа с названием "API" и скопировать код Account ID.',
        # initial='9c4c647bdf06778ca420dc255dcceab0',
    )

    def sendToCloudflare(self):
        """Отправить домены в Cloudflare и получить выданные NS-сервера"""

        global_api_key = self.cleaned_data.get('global_api_key')
        api_account_id = self.cleaned_data.get('api_account_id')
        email = self.cleaned_data.get('email')
        domains_list = self.cleaned_data.get('domains').split(',')

        messages_success = list()
        messages_error = list()

        for domain in domains_list:
            domain.strip()

            api = ApiCloudflare(email, global_api_key)
            data = {
                "domain": domain,
                "api_account_id": api_account_id
            }

            try:
                name_server_str = ''
                response = api.post_create_zone(data)

                for name_server in response['result']['name_servers']:
                    name_server_str += name_server + ', '

                messages_success.append(f'NS-сервера для домена {domain}: {name_server_str}')
            except:
                messages_error.append(f'Не удалось добавить домен {domain} в CF.')

        return messages_success, messages_error


class GeneratorDomainForm(forms.Form):
    """Генератор имен для доменов"""

    numbers = forms.IntegerField(
        label='Количество доменов',
        required=True,
        initial=10
    )
    domain_zone = forms.CharField(
        label='Доменная зона',
        required=True,
        help_text='Например: site или com.',
        initial='site'
    )
    keyword = forms.CharField(
        label='Ключевое слово',
        required=False,
        help_text='По данном ключевому слову будут генерироваться имена. Например: beauty.',
    )

    def random_word_api(self):
        """Отправить запрос на получение рандомных слов."""

        numbers = self.cleaned_data.get('numbers')
        domain_zone = self.cleaned_data.get('domain_zone')
        keyword = self.cleaned_data.get('keyword')

        names_str = ''

        from random import randint

        if keyword:
            response = requests.get(f'https://api.datamuse.com/words?ml={keyword}')
            data = response.json()
            indexes = [randint(0, len(data)-1) for i in range(numbers)]

            for index in indexes:
                names_str += data[index].get('word') + '.' + domain_zone + ', '
        else:
            response = requests.get(f'http://random-word-api.herokuapp.com/word?number={numbers}')
            data = response.json()

            for name in data:
                names_str += f'{name}.{domain_zone}, '

        return names_str


class AddDomainsFreeForm(forms.Form):
    """Проверка свободен ли доимен в интернете через API Jsonwhois.io."""

    domains = forms.CharField(
        label='Список доменов',
        widget=forms.Textarea(attrs={'rows': 5}),
        help_text='Введите через запятую список доменов. Например: domain1.ru, domain2.com',
        required=True
    )

    def domain_availability_check(self):
        domains_list = self.cleaned_data.get('domains').split(',')
        message_success = ''
        message_error = ''

        for domain in domains_list:
            domain.strip()

            try:
                response = requests.head(f"https://{domain}")
                if response.status_code == 200:
                    message_success += f'{domain}, '
                else:
                    message_error += f'{domain}, '
            except requests.exceptions.ConnectionError:
                message_error += f'{domain}, '

        return message_success, message_error


class DomainVerificationForm(forms.Form):
    """Верификация домена для Facebook

    Создается на Keitaro html-файл с названием и содержимым кода от ФБ."""

    domain = forms.CharField(
        label='Домен',
        max_length=255,
        help_text='Введите домен, для которого скопировали код из БМ Facebook.',
        required=True
    )
    code = forms.CharField(
        label='Код из Facebook',
        max_length=255,
        required=True,
        help_text='Откройте БМ ФБ и выполните: Безопасность бренда → Домены → Добавить домен → Загрузка файла HTML. Нужно скопировать код из файла html и вставить в это поле.'
    )

    def sendToKeitaroForCreateHtmlFileWithCode(self):
        keitaro = self.cleaned_data.get('keitaro')
        code = self.cleaned_data.get('code')
        domain = self.cleaned_data.get('domain')

        message_success = list()
        message_error = list()

        domain.strip()
        response = requests.get(f'https://{domain}/domain-verification-for-fb/?code={code}')

        if code in response.text:
            message_success = f'{domain} - OK. Установлен код: {response.text}. Не забудьте подтвердить верификацию в Facebook.'
        else:
            message_error = f'{domain} - ОШИБКА! Не удалось установить код: {response.text}'

        return message_success, message_error


class PushserviceForm(forms.Form):
    """Форма для доставки пуш-уведомлений в pushservice.info"""

    # Страны
    COUNTRY_CHOICES = [
        (0, '---------'), ('Other', 'Other'), ('AD', 'AD'), ('AE', 'AE'), ('AL', 'AL'), ('AO', 'AO'), ('AR', 'AR'),
        ('AT', 'AT'), ('AU', 'AU'), ('BA', 'BA'), ('BE', 'BE'), ('BG', 'BG'), ('BR', 'BR'), ('BY', 'BY'), ('CA', 'CA'),
        ('CH', 'CH'), ('CL', 'CL'), ('CO', 'CO'), ('CV', 'CV'), ('CY', 'CY'), ('CZ', 'CZ'), ('DE', 'DE'), ('DK', 'DK'),
        ('EE', 'EE'), ('EG', 'EG'), ('ES', 'ES'), ('FI', 'FI'), ('FR', 'FR'), ('GB', 'GB'), ('GE', 'GE'), ('GH', 'GH'),
        ('GR', 'GR'), ('HK', 'HK'), ('HR', 'HR'), ('HU', 'HU'), ('ID', 'ID'), ('IE', 'IE'), ('IL', 'IL'), ('IN', 'IN'),
        ('IT', 'IT'), ('KZ', 'KZ'), ('LA', 'LA'), ('LR', 'LR'), ('LT', 'LT'), ('LU', 'LU'), ('LV', 'LV'), ('MD', 'MD'),
        ('MK', 'MK'), ('ML', 'ML'), ('MX', 'MX'), ('MY', 'MY'), ('MZ', 'MZ'), ('NL', 'NL'), ('NO', 'NO'), ('PH', 'PH'),
        ('PL', 'PL'), ('PS', 'PS'), ('PT', 'PT'), ('RO', 'RO'), ('RU', 'RU'), ('SE', 'SE'), ('SG', 'SG'), ('SI', 'SI'),
        ('SK', 'SK'), ('SL', 'SL'), ('ST', 'ST'), ('TH', 'TH'), ('TR', 'TR'), ('TT', 'TT'), ('UA', 'UA'), ('US', 'US'),
        ('ZA', 'ZA'),
    ]

    pushName = forms.CharField(label='Название пуша', max_length=40, required=True, help_text='Длина 40 символов.')
    pushTitle = forms.CharField(label='Заголовок', max_length=100, required=True, help_text='Длина 100 символов.')
    pushIcon = forms.CharField(
        label='Иконка (ссылка только HTTPS)',
        max_length=3000,
        required=False,
        help_text='Длина 3000 символов.',
        initial='https://'
    )
    pushImage = forms.CharField(
        label='Картинка (ссылка только HTTPS)',
        max_length=3000,
        required=False,
        help_text='Длина 3000 символов.',
        initial='https://'
    )
    pushText = forms.CharField(label='Текст', required=True, widget=forms.Textarea(attrs={'rows': '3'}))
    pushLink = forms.CharField(label='Ссылка с пуша', max_length=3000, required=True, help_text='Длина 3000 символов.')
    pushButton1Title = forms.CharField(label='Первая кнопка (название)', max_length=40, required=False, help_text='Длина 40 символов.')
    pushButton1Link = forms.CharField(label='Первая кнопка (ссылка)', max_length=3000, required=False, help_text='Длина 3000 символов.')
    pushButton2Title = forms.CharField(label='Вторая кнопка (название)', max_length=40, required=False, help_text='Длина 40 символов.')
    pushButton2Link = forms.CharField(label='Вторая кнопка (ссылка)', max_length=3000, required=False, help_text='Длина 3000 символов.')
    pushCountry = forms.ChoiceField(label='Страна', choices=COUNTRY_CHOICES, required=True)
    pushCategory = forms.ChoiceField(
        label='Категория',
        required=True,
        help_text='Если список категорий пустой - попросите руководителя, чтобы их назначил.'
    )

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request')
        super(PushserviceForm, self).__init__(*args, **kwargs)

        if has_group(request.user, 'Тимлиды'):
            category_list = list()
            for profile_category in request.user.profile.category.all():
                category_list.append((profile_category.name, profile_category.name))
            self.fields['pushCategory'].choices = category_list
        elif has_group(request.user, 'Руководители'):
            self.fields['pushCategory'].choices = Profile.CATEGORY_CHOICES

    def send(self):
        """Отправить пуш-уведомлений в pushservice.info"""
        return requests.post(url='https://pushservive.info/?page=api_add_push', data={
            'pushName': self.cleaned_data.get('pushName'),
            'pushTitle': self.cleaned_data.get('pushTitle'),
            'pushIcon': self.cleaned_data.get('pushIcon'),
            'pushImage': self.cleaned_data.get('pushImage'),
            'pushText': self.cleaned_data.get('pushText'),
            'pushLink': self.cleaned_data.get('pushLink'),
            'pushButton1Title': self.cleaned_data.get('pushButton1Title'),
            'pushButton1Link': self.cleaned_data.get('pushButton1Link'),
            'pushButton2Title': self.cleaned_data.get('pushButton2Title'),
            'pushButton2Link': self.cleaned_data.get('pushButton2Link'),
            'pushCountry': self.cleaned_data.get('pushCountry'),
            'pushCategory': self.cleaned_data.get('pushCategory')
        })
