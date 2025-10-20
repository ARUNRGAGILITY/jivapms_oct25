from django.contrib import admin
from .models import ConstructType, Construct


@admin.register(ConstructType)
class ConstructTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'position', 'active', 'deleted')
    list_filter = ('active', 'deleted')
    search_fields = ('name', 'code', 'synonyms')


@admin.register(Construct)
class ConstructAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'organization', 'site', 'parent', 'position', 'active', 'deleted')
    list_filter = ('type', 'site', 'organization', 'active', 'deleted')
    search_fields = ('name',)