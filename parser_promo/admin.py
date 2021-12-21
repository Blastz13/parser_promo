from django.contrib import admin
from .models import ParserBatch, PresetParser, AffiliateNetwork, Geo, DownloadedPromo, Option


@admin.register(Option)
class OptionForm(admin.ModelAdmin):
    pass

@admin.register(ParserBatch)
class ParserBatchForm(admin.ModelAdmin):
    list_display = ["id", "status", "created", "text_tasks"]


@admin.register(PresetParser)
class PresetParserForm(admin.ModelAdmin):
    list_display = ["id", "name", "tracker", "traffic_source", "aff_network", "token"]


@admin.register(AffiliateNetwork)
class AffiliateNetworkForm(admin.ModelAdmin):
    pass


@admin.register(Geo)
class GeoForm(admin.ModelAdmin):
    pass


@admin.register(DownloadedPromo)
class DownloadedPromoForm(admin.ModelAdmin):
    list_display = ["status", "url_promo", "type_promo", "geo", "type_promo", "preset", "created"]
    list_filter = ["type_promo", "geo", "keitaro_group_id"]
