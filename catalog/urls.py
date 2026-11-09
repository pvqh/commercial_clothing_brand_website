from django.urls import path
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

from catalog.views.category import category_page
from catalog.views.home import home_page
from catalog.views.product import product_page

app_name = "catalog"

urlpatterns = [
    path("", home_page, name="home"),
    path(format_lazy("{}<slug:slug>/", _("catalog/")), category_page, name="category"),
    path(format_lazy("{}<slug:slug>/", _("product/")), product_page, name="product"),
]
