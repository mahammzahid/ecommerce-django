from django.contrib import admin
from .models import  OrderItem, Product,Order, Cart, CartItem, Customer,Stock 

admin.site.register(Product)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Customer)
admin.site.register(Stock)

class StockAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity')
    list_editable = ('quantity',)   # 👈 edit directly in table
    list_filter = ('product',)
    search_fields = ('product__name',)