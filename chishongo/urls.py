from django.contrib import admin
from django.urls import path
from core import views
from core.views import bootstrap_live_users

urlpatterns = [
    path('', views.login_view, name='login'),
    path('home/', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('reports/', views.reports, name='reports'),
    path('stock-history/', views.stock_history, name='stock_history'),
    path('products/', views.products, name='products'),
    path('sales/', views.sales, name='sales'),
    path('deliveries/', views.deliveries, name='deliveries'),
    path('expenses/', views.expenses, name='expenses'),
    path('cashier-sales-entry/', views.cashier_sale_entry, name='cashier_sale_entry'),
    path('manager-delivery-entry/', views.manager_delivery_entry, name='manager_delivery_entry'),
    path('manager-new-product-entry/', views.manager_new_product_entry, name='manager_new_product_entry'),
    path('manager-expense-entry/', views.manager_expense_entry, name='manager_expense_entry'),
    path('logout/', views.logout_view, name='logout'),
    path('admin/', admin.site.urls),
    path('bootstrap-live-users/', bootstrap_live_users, name='bootstrap_live_users'),
]