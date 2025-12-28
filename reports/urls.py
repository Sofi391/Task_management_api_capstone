from django.urls import path
from .views import (SalesReportView,PurchaseReportView,StockReport,
                    ProfitReport,TopSellingProducts,TopSellingPersonsView,SummaryReports)


urlpatterns = [
    path('sales/',SalesReportView.as_view(),name='sales'),
    path('purchases/',PurchaseReportView.as_view(),name='purchases'),
    path('stock/',StockReport.as_view(),name='stock'),
    path('profit/',ProfitReport.as_view(),name='profit'),
    path('top-selling/',TopSellingProducts.as_view(),name='top-selling'),
    path('top-sellers/',TopSellingPersonsView.as_view(),name='top-sellers'),
    path('summary/',SummaryReports.as_view(),name='summary'),
]