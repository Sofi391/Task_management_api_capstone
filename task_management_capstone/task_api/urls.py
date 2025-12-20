from django.urls import path,include
from rest_framework.routers import DefaultRouter
from .views import (ProductViewSet,SupplierViewSet,PurchaseViewSet,
                    StockTransactionListView,SaleViewSet,
                    StockTransactionCreate,
                    )


router = DefaultRouter()
router.register('supplier',SupplierViewSet)
router.register('products', ProductViewSet)
router.register('purchases', PurchaseViewSet)
router.register('sales', SaleViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('transactions/', StockTransactionListView.as_view(),name='transaction_list'),
    path('transactions/create/', StockTransactionCreate.as_view(),name='transaction_create'),
]
