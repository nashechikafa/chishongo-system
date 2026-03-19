from django.contrib import admin
from .models import Product, Sale, StockDelivery, UserProfile, Expense

admin.site.site_header = "Chishongo Administration"
admin.site.site_title = "Chishongo Admin Portal"
admin.site.index_title = "Welcome to Chishongo Retail Management System"

admin.site.register(Product)
admin.site.register(Sale)
admin.site.register(StockDelivery)
admin.site.register(UserProfile)
admin.site.register(Expense)