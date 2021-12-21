from django.db import models

from django.db import models
from django.shortcuts import reverse
from django.contrib.auth.models import User


class Option(models.Model):
    """Модель для хранения настроек приложений."""

    name = models.CharField(verbose_name='Название', max_length=255)
    value = models.TextField(verbose_name='Значение')
    desc = models.CharField(verbose_name='Описание', max_length=255)

    # Служебные поля
    created = models.DateTimeField(auto_now_add=True, verbose_name='Добавлен')
    modified = models.DateTimeField(auto_now=True, verbose_name='Обновлен')

    class Meta:
        verbose_name_plural = "Конфиги"
        ordering = ['-modified']

    def __str__(self):
        return '{}'.format(self.name)

    def get_absolute_url(self):
        return reverse('option_detail', kwargs={'pk': self.pk})

    def get_update_url(self):
        return reverse('option_update', kwargs={"pk": self.pk})

    def get_delete_url(self):
        return reverse('option_delete')

    # @classmethod
    # def is_facebook_api_active(cls, profile=None):
    #     """ Получить настройку - Активирован ли Facebook API или нет """
    #
    #     option = cls.objects.get(name='facebook.api')
    #
    #     if int(option.value) == 1:
    #         return True
    #     else:
    #         if profile:
    #             # Facebook доступен/недоступен индивидуально для пользователя.
    #             if profile.connect_fb_api in [Profile.CONNECT_FB_API_INDIGO, Profile.CONNECT_FB_API_OWN_PROXY]:
    #                 return True
    #     return False

    @staticmethod
    def get_value_by_name(name):
        """Получить значение опции по ее имени."""

        try:
            return Option.objects.get(name=name).value
        except:
            return None


class AffiliateNetwork(models.Model):
    """Партнерские сети."""

    # Настроенные партнерские сети для парсера
    AFF_WEBVORK = 'Webvork.com'
    AFF_EVERAD = 'Everad.com'
    AFF_LEADBIT = 'Leadbit.com'
    AFF_LUCKY_ONLINE = 'Lucky.online'
    AFF_TERRALEADS = 'Terraleads.com'

    name = models.CharField(max_length=255, verbose_name='Название')
    order_php = models.TextField(verbose_name='Содержимое файла order.php', default='<?php ')
    instruction = models.CharField(verbose_name='Инструкция', max_length=255, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, verbose_name='Добавлен')
    modified = models.DateTimeField(auto_now=True, verbose_name='Обновлен')

    class Meta:
        verbose_name_plural = "Партнерские сети"
        ordering = ['-modified']

    def __str__(self):
        return '{}'.format(self.name)

    def get_absolute_url(self):
        return reverse('tools:aff_network_detail', kwargs={'pk': self.pk})

    def get_update_url(self):
        return reverse('tools:aff_network_update', kwargs={"pk": self.pk})

    def get_delete_url(self):
        return reverse('tools:aff_network_delete')


class PresetParser(models.Model):
    """Пресеты для парсера."""

    TRACKER_KEITARO = 1
    TRACKER_BINOM = 2
    TRACKER_CHOICES = [
        (0, '---------'),
        (TRACKER_KEITARO, 'Keitaro'),
        (TRACKER_BINOM, 'Binom'),
    ]

    TRAFFIC_SOURCE_FB = 1
    TRAFFIC_SOURCE_MGID = 2
    TRAFFIC_SOURCE_CHOICES = [
        (0, '---------'),
        (TRAFFIC_SOURCE_FB, 'Facebook'),
        (TRAFFIC_SOURCE_MGID, 'MGID'),
    ]

    name = models.CharField(verbose_name='Название', max_length=255)
    tracker = models.SmallIntegerField(verbose_name='Трекер', choices=TRACKER_CHOICES, default=TRACKER_KEITARO)
    traffic_source = models.SmallIntegerField(
        verbose_name='Источник трафика', choices=TRAFFIC_SOURCE_CHOICES, default=TRAFFIC_SOURCE_FB)
    aff_network = models.ForeignKey('AffiliateNetwork', verbose_name='ПП', on_delete=models.CASCADE)
    token = models.CharField(verbose_name='Токен ПП для API', max_length=255, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, verbose_name='Добавлен')
    modified = models.DateTimeField(auto_now=True, verbose_name='Обновлен')

    class Meta:
        verbose_name_plural = "Пресеты парсера"
        ordering = ['name']

    def __str__(self):
        return '{0} ({1}/{2}/{3})'.format(
            self.name, self.get_traffic_source_display(), self.get_tracker_display(), self.aff_network)

    def get_absolute_url(self):
        return reverse('tools:preset_parser_detail', kwargs={'pk': self.pk})

    def get_update_url(self):
        return reverse('tools:preset_parser_update', kwargs={"pk": self.pk})

    def get_delete_url(self):
        return reverse('tools:preset_parser_delete')


class DownloadedPromo(models.Model):
    """ Модель Скачанные промо """

    # Тип промо
    TYPE_PROMO_LANDING_HOT = 1
    TYPE_PROMO_LANDING_WITH_OFFER = 2
    TYPE_PROMO_LANDING_HOT_WITH_OFFER = 3
    TYPE_PROMO_CHOICES = [
        (TYPE_PROMO_LANDING_HOT, 'Прокла'),
        (TYPE_PROMO_LANDING_WITH_OFFER, 'Ленд с оффером'),
        (TYPE_PROMO_LANDING_HOT_WITH_OFFER, 'Прокла с оффером'),
    ]

    # Тип промо
    STATUS_PROCESS = 1
    STATUS_DOWNLOADED = 2
    STATUS_KEITARO_OK = 3
    STATUS_ERROR = 10
    STATUS_KEITARO_ERROR = 11
    STATUS_CHOICES = [
        (STATUS_PROCESS, 'Парсится...'),
        (STATUS_DOWNLOADED, 'Готово'),
        (STATUS_KEITARO_OK, 'Загружен в Keitaro'),
        (STATUS_ERROR, 'Ошибка!'),
        (STATUS_KEITARO_ERROR, 'Ошибка загрузки в Keitaro!'),
    ]

    # Тип промо в Keitaro
    KEITARO_TYPE_PROMO_LANDING = 1
    KEITARO_TYPE_PROMO_OFFER = 2
    KEITARO_TYPE_PROMO_CHOICES = [
        (KEITARO_TYPE_PROMO_LANDING, 'Лендинг (keitaro)'),
        (KEITARO_TYPE_PROMO_OFFER, 'Оффер (keitaro)'),
    ]
    geo = models.CharField(max_length=255, blank=True, verbose_name="Гео")
    keitaro_group_id = models.IntegerField(blank=True, verbose_name="Кейтаро id группы")
    url_promo = models.CharField(max_length=255, verbose_name='Промо')
    archive_promo = models.CharField(max_length=255, verbose_name='Подготовленный промо-архив', blank=True, null=True)
    archive_promo_zip = models.FileField(upload_to='media/', blank=True)
    type_promo = models.SmallIntegerField(verbose_name='Тип промо', choices=TYPE_PROMO_CHOICES)
    preset = models.ForeignKey('PresetParser', verbose_name='Пресет', on_delete=models.CASCADE, blank=True, null=True)
    status = models.SmallIntegerField(verbose_name='Статус', choices=STATUS_CHOICES, default=STATUS_PROCESS)
    log = models.TextField(verbose_name='Лог', blank=True, null=True)
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Владелец', editable=False, blank=True, null=True)
    parser_batch = models.ForeignKey(
        'ParserBatch', on_delete=models.CASCADE, verbose_name='Пакетное задание', editable=False, blank=True, null=True)
    keitaro_type_promo = models.SmallIntegerField(
        verbose_name='Тип промо в Keitaro', choices=KEITARO_TYPE_PROMO_CHOICES, blank=True, null=True)
    keitaro_promo_id = models.IntegerField(verbose_name='ID лендинга/оффера в Keitaro', blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, verbose_name='Добавлен')
    modified = models.DateTimeField(auto_now=True, verbose_name='Обновлен')

    class Meta:
        verbose_name_plural = "Скачанные промо"
        ordering = ['-pk']

    def __str__(self):
        # return '{} ({})'.format(self.archive_promo, self.type_promo)
        return f'{self.pk}'

    def get_delete_url(self):
        return reverse('tools:downloaded_promo_delete')

    @property
    def get_formatting_log(self):
        from django.utils.html import format_html

        html = '<pre class="small">'
        log_list = self.log.split(',')

        for item in log_list:
            html += item + '<br/>'

        html += '<pre>'

        return format_html(html)


class ParserBatch(models.Model):
    """Модель пакетных заданий для парсера."""

    STATUS_NEW = 1
    STATUS_RUN = 2
    STATUS_OK = 3
    STATUS_ERROR = 10
    STATUS_CHOICES = [
        (0, '---------'),
        (STATUS_NEW, 'Новый'),
        (STATUS_RUN, 'Выполняется'),
        (STATUS_OK, 'Выполнен.'),
        (STATUS_ERROR, 'Ошибка в парсере!'),
    ]

    text_tasks = models.TextField(verbose_name='Текст пакетных заданий', blank=False)
    status = models.SmallIntegerField(verbose_name='Статус', choices=STATUS_CHOICES, default=STATUS_NEW)
    created = models.DateTimeField(auto_now_add=True, verbose_name='Добавлен')
    modified = models.DateTimeField(auto_now=True, verbose_name='Обновлен')
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Владелец', editable=False, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Пакетные запросы"
        ordering = ['-pk']

    def __str__(self):
        return f'{self.pk}'

    def get_absolute_url(self):
        return reverse('tools:tools_parser_batch_detail', kwargs={'pk': self.pk})

    def get_update_url(self):
        return reverse('tools:tools_parser_batch_update', kwargs={"pk": self.pk})

    def get_delete_url(self):
        return reverse('tools:tools_parser_batch_delete')

    def get_run_tasks_url(self):
        return reverse('tools:tools_parser_batch_run', kwargs={"pk": self.pk, "is_need_fixes": None})

    def get_run_fixes_tasks_url(self):
        return reverse('tools:tools_parser_batch_run', kwargs={"pk": self.pk, "is_need_fixes": True})


class Geo(models.Model):
    """ Модель для хранения ГЕО (страны) """

    name = models.CharField(verbose_name='Название страны', max_length=100)
    iso = models.CharField(verbose_name='Код ISO', max_length=2)
    created = models.DateTimeField(auto_now_add=True, verbose_name='Добавлен')
    modified = models.DateTimeField(auto_now=True, verbose_name='Обновлен')

    class Meta:
        verbose_name_plural = "Гео"
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.iso})'

    def get_absolute_url(self):
        return reverse('tools:geo_detail', kwargs={'pk': self.pk})

    def get_update_url(self):
        return reverse('tools:geo_update', kwargs={"pk": self.pk})

    def get_delete_url(self):
        return reverse('tools:geo_delete')
