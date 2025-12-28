from django.contrib import admin
from .models import Product,Supplier,StockTransaction,PurchaseOrder,Sale

# Register your models here.
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name','sku','supplier__name','selling_price','buying_price','current_stock')
    list_filter = ('id','name','supplier__name')


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name','email','phone','address')


@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = ('product__name','created_by__username','quantity','unit_price','transaction_type','note')


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('product__name','supplier__name','status','quantity','unit_price')


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('product__name','sold_by__username','status','quantity','selling_price')


