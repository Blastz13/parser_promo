from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import View
from .forms import ParserForm, ParserBatchForm
from .models import *
# coding=utf-8
from unicodedata import name
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib import messages
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
from django.conf import settings

from .forms import ParserForm
from .models import PresetParser, AffiliateNetwork, DownloadedPromo, ParserBatch
from .models import Geo
from .models import Option
from .api_keitaro import ApiKeitaro
from .handler_parser import HandlerParser


def tools_parser_batch_list(request):
    parser_batch = ParserBatch.objects.all()
    return render(request, 'parser_promo/list.html', context={"parser_batchs": parser_batch})


def tools_parser_batch_run(request, pk):
    """Отправить список заданий в парсер."""

    # if not has_group(request.user, 'Руководители') and \
    #     not has_group(request.user, 'Верстальщики'):
    #     raise PermissionDenied

    # if has_group(request.user, 'Руководители'):
    parser_batch = get_object_or_404(ParserBatch, pk=pk)
    # else:
    #     parser_batch = get_object_or_404(ParserBatch, pk=pk, owner=request.user)

    messages.info(request, f'Обрабатываем пакетное задание #{parser_batch}')
    counter_processed = 0
    counter_missed = 0
    counter_reloaded = 0

    # if is_need_fixes:
    #     parser_batch.downloadedpromo_set.filter(status__in=[
    #         DownloadedPromo.STATUS_DOWNLOADED,
    #         DownloadedPromo.STATUS_ERROR,
    #         DownloadedPromo.STATUS_KEITARO_ERROR,
    #         DownloadedPromo.STATUS_PROCESS]
    #     ).delete()
        # messages.success(request, f'Удалены ошибочные и зависшие промо в пакетном задании.')

    for i, line in enumerate(parser_batch.text_tasks.splitlines()):
        params = line.split(';')

        '''
        Инедксы списка - обозначения.
        [0] - URL_ПРОМО;
        [1] - ПРЕСЕТ:1|2|3|4|5|6;
        [2] - ТИП_ПРОМО:1|2|3;
        [3] - ID_ОФФЕРА_ПП;
        [4] - ID_ПОТОКА_ПП;
        [5] - ГЕО;
        [6] - СКАЧАТЬ_СПАСИБО:1|0;
        [7] - НАЗВАНИЕ_ИСХОДЯЩЕГО_АРХИВА
        [8] - ID_ГРУППЫ_KEITARO
        [9] - НОМЕР_СЕРВЕРА_КЕЙТАРО
        [10] - ПАРТНЕРСКАЯ_СЕТЬ_ID_КЕЙТАРО
        '''

        # if is_need_fixes:
        #     # Если с таким URL уже есть промо загруженный в Кейтаро, то пропускаем
        #     promo = parser_batch.downloadedpromo_set.filter(status=DownloadedPromo.STATUS_KEITARO_OK, url_promo=params[0]).exists()
        #     if promo:
        #         counter_missed += 1
        #         continue
        #     else:
        #         counter_reloaded += 1

        preset = PresetParser.objects.get(pk=params[1])
        if not preset:
            messages.warning(request, f'Отсутствует пресет с ID={params[1]} в БД.')
            return redirect('tools_parser_batch_list')

        geo = Geo.objects.get(iso=params[5])
        if not geo:
            messages.warning(request, f'Отсутствует гео с названием {params[5]} в БД.')
            return redirect('tools_parser_batch_list')
        HandlerParser(
            preset_id=params[1],
            url=params[0],
            archive_upload_path=None,
            type_promo=params[2],
            offer_id=params[3],
            source_id=params[4],
            campaign_id=None,
            geo_id=geo.pk,
            is_clear_all_script=False,
            clear_aff_network_script=ParserForm.get_num_aff_network_script(preset.aff_network.name),
            # is_download_success_html=params[6],
            user_id=request.user.id,
            parser_batch_id=parser_batch.pk,
            keitaro_landing_name=params[7],
            keitaro_group_id=params[8],
            keitaro_server_number=params[9],
            keitaro_affiliate_network_id=params[10],
            keitaro_folder_name=params[11]
        ).run()
        messages.success(request, f'URL {params[0]} - отправлен в очередь на скачивание.')
        counter_processed += 1

    # if is_need_fixes:
    #     messages.info(request, f'Пропущено задач: {counter_missed}. Перегружено задач: {counter_reloaded}.')
    #
    messages.info(request, f'Отправлено задач на скачивание: {counter_processed}.')

    # parser_batch.status = ParserBatch.STATUS_RUN
    # parser_batch.save()

    return redirect('tools_parser_batch_list')


def tools_parser_batch_create(request):
    """Форма пакетного создания заданий для скачивания промо."""

    # if not has_group(request.user, 'Руководители') and \
    #     not has_group(request.user, 'Верстальщики'):
    #     raise PermissionDenied

    form = ParserBatchForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            model = form.save(commit=False)
            model.owner = request.user
            model.save()
            messages.success(request, 'Сохранено пакетное задание на скачивание промо. Не забудьте "Отправить в парсер"')

            return redirect('tools_parser_batch_list')
        else:
            pass
            messages.warning(request, 'Не удалось создать задание.')
            messages.error(request, form.errors)
    return render(request, "parser_promo/index.html", context={"form": form})
    # context = {
    #     'page_title': 'Добавление пакетного задания',
    #     'form': form,
    #     'presets_parser': PresetParser.objects.all(),
    #     'type_promo_choices': ParserForm.TYPE_PROMO_CHOICES
    # }
# class CreateTaskParser(View):
#     def get(self, request):
#         form = CreateTaskParserForm()
#         return render(request, 'parser_promo/index.html', context={"form": form})
#
#     def post(self, request):
#         """Отправить список заданий в парсер."""
#         form = CreateTaskParserForm(request.POST)
#         if form.is_valid():
#             cd = form.cleaned_data
#             for i, line in enumerate(cd["text_tasks"].splitlines()):
#                 params = line.split(';')
#
#                 '''
#                 Инедксы списка - обозначения.
#                 [0] - URL_ПРОМО;
#                 [1] - ПРЕСЕТ:1|2|3|4|5|6;
#                 [2] - ТИП_ПРОМО:1|2|3;
#                 [3] - ID_ОФФЕРА_ПП;
#                 [4] - ID_ПОТОКА_ПП;
#                 [5] - ГЕО;
#                 [6] - СКАЧАТЬ_СПАСИБО:1|0;
#                 [7] - НАЗВАНИЕ_ИСХОДЯЩЕГО_АРХИВА
#                 [8] - ID_ГРУППЫ_KEITARO
#                 [9] - НОМЕР_СЕРВЕРА_КЕЙТАРО
#                 [10] - ПАРТНЕРСКАЯ_СЕТЬ_ID_КЕЙТАРО
#                 '''
#
#
#                 print(params)
#                 preset = PresetParser.objects.get(pk=params[1])
#                 # if not preset:
#                 #     messages.warning(request, f'Отсутствует пресет с ID={params[1]} в БД.')
#                 #     return redirect('tools:tools_parser_batch_detail', pk=parser_batch.pk)
#
#                 geo = Geo.objects.get(iso=params[5])
#                 # if not geo:
#                     # messages.warning(request, f'Отсутствует гео с названием {params[5]} в БД.')
#                     # return redirect('tools:tools_parser_batch_detail', pk=parser_batch.pk)
#                 parser = HandlerParser(
#                     preset_id=params[1],
#                     url=params[0],
#                     archive_upload_path=None,
#                     type_promo=params[2],
#                     offer_id=params[3],
#                     source_id=params[4],
#                     campaign_id=None,
#                     geo_id=geo.pk,
#                     is_clear_all_script=False,
#                     clear_aff_network_script="FB",
#                     # is_download_success_html=params[6],
#                     user_id=request.user.id,
#                     parser_batch_id=1, # TODO: butch
#                     keitaro_landing_name=params[7],
#                     keitaro_group_id=params[8],
#                     keitaro_server_number=params[9],
#                     keitaro_affiliate_network_id=params[10]
#                 )
#                 parser.run()
#                 # download_promo_site_and_save_in_db.delay(
#                 #     preset_id=params[1],
#                 #     url=params[0],
#                 #     archive_upload_path=None,
#                 #     type_promo=params[2],
#                 #     offer_id=params[3],
#                 #     source_id=params[4],
#                 #     campaign_id=None,
#                 #     geo_id=geo.pk,
#                 #     is_clear_all_script=False,
#                 #     clear_aff_network_script=ParserForm.get_num_aff_network_script(preset.aff_network.name),
#                 #     # is_download_success_html=params[6],
#                 #     user_id=request.user.id,
#                 #     parser_batch_id=1, # TODO: butch
#                 #     keitaro_landing_name=params[7],
#                 #     keitaro_group_id=params[8],
#                 #     keitaro_server_number=params[9],
#                 #     keitaro_affiliate_network_id=params[10]
#                 # )