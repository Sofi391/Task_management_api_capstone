from datetime import timedelta
from django.db.models.functions import TruncDay,TruncWeek,TruncMonth,TruncYear
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .permissions import IsManager
from .serializers import ProductReportSerializer,StockReportSummarySerializer,TopSellingReportSerializer,TopSellingPerson,SummaryTimelineSerializer
from task_api.models import Sale,PurchaseOrder,Product
from django.utils import timezone
from django.db.models import Q, F, Sum, Avg, Count, Max, Min, ExpressionWrapper, DecimalField


# Create your views here.
class SalesReportView(APIView):
    permission_classes = (IsManager,)

    def get(self, request):
        from_date = request.query_params.get('from')
        to_date = request.query_params.get('to')
        sales_person = request.query_params.get('sales_person')

        sales = Sale.objects.filter(status='Completed')
        if from_date:
            sales = sales.filter(created_at__date__gte=from_date)
        if to_date:
            sales = sales.filter(created_at__date__lte=to_date)

        revenue_expression = ExpressionWrapper(
            F('quantity')*F('selling_price'),
            output_field = DecimalField(max_digits=15, decimal_places=2)
        )

        sales_summary = sales.aggregate(
            total_quantity=Sum('quantity',default=0),
            total_revenue=Sum(revenue_expression,default=0),
            total_sales=Count('id'),
        )

        response = {
            'period': {
                'from': from_date,
                'to': to_date,
            },
            'summary': {
                'total_quantity': sales_summary['total_quantity'],
                'total_sales_revenue': sales_summary['total_revenue'],
                'total_sales': sales_summary['total_sales'],
            },
        }

        if sales_person:
            sold_by = sales.filter(sold_by__username=sales_person)
            personal_summary = sold_by.aggregate(
                total_quantity_sold=Sum('quantity',default=0),
                total_revenue = Sum(revenue_expression,default=0),
                total_sales = Count('id'),
            )
            response['staff_summary'] = {
                'sales_person':sales_person,
                'total_quantity_sold': personal_summary['total_quantity_sold'],
                'total_sold_revenue': personal_summary['total_revenue'],
                'total_sales': personal_summary['total_sales'],
            }

        return Response(response,status=status.HTTP_200_OK)



class PurchaseReportView(APIView):
    permission_classes = (IsManager,)

    def get(self, request):
        from_date = request.query_params.get('from')
        to_date = request.query_params.get('to')

        purchase = PurchaseOrder.objects.filter(status='Completed')
        if from_date:
            purchase = purchase.filter(created_at__date__gte=from_date)
        if to_date:
            purchase = purchase.filter(created_at__date__lte=to_date)

        cost_expression = ExpressionWrapper(
            F('quantity')*F('unit_price'),
            output_field = DecimalField(max_digits=15, decimal_places=2)
        )

        purchase_summary = purchase.aggregate(
            total_quantity=Sum('quantity',default=0),
            total_cost=Sum(cost_expression,default=0),
            total_purchases=Count('id'),
        )

        response = {
            'period': {
                'from': from_date,
                'to': to_date,
            },
            'summary': {
                'total_quantity': purchase_summary['total_quantity'],
                'total_cost': purchase_summary['total_cost'],
                'total_purchases': purchase_summary['total_purchases'],
            },
        }

        return Response(response,status=status.HTTP_200_OK)


class StockReport(APIView):
    permission_classes = (IsManager,)

    def get(self, request):
        name = request.query_params.get('name')
        from_date = request.query_params.get('from')
        to_date = request.query_params.get('to')
        products = Product.objects.all()

        if name:
            products = products.filter(
                Q(name__icontains=name) |
                Q(category__icontains=name)
            )
        if from_date:
            products = products.filter(created_at__date__gte=from_date)
        if to_date:
            products = products.filter(created_at__date__lte=to_date)

        inventory_value = ExpressionWrapper(
            F('current_stock')*F('buying_price'),
            output_field = DecimalField(max_digits=15, decimal_places=2)
        )

        in_stock = products.filter(current_stock__gt=0).aggregate(
            total_products = Count('id'),
            total_quantity = Sum('current_stock',default=0),
            inventory_value=Sum(inventory_value,default=0),
        )

        stock_products = products.filter(current_stock__gt=0).order_by('-created_at')


        out_stock = products.filter(current_stock__lte=0).order_by('-created_at')
        low_stock = products.filter(current_stock__gt=0,current_stock__lte=F('reorder_level')).order_by('-created_at')

        summary_serializer = StockReportSummarySerializer(in_stock).data
        in_stock_serializer = ProductReportSerializer(stock_products,many=True).data
        out_stock_serializer = ProductReportSerializer(out_stock,many=True).data
        low_stock_serializer = ProductReportSerializer(low_stock,many=True).data


        response = {
            'summary': summary_serializer,
            'stock_products': in_stock_serializer,
            'low_stock_products': low_stock_serializer,
            'out_of_stock_products': out_stock_serializer
        }

        return Response(response,status=status.HTTP_200_OK)


class ProfitReport(APIView):
    permission_classes = (IsManager,)

    def get(self, request):
        from_date = request.query_params.get('from')
        to_date = request.query_params.get('to')
        product = request.query_params.get('product')

        total_sales = Sale.objects.filter(status='Completed')
        total_purchase = PurchaseOrder.objects.filter(status='Completed')

        if from_date:
            total_sales = total_sales.filter(created_at__date__gte=from_date)
            total_purchase = total_purchase.filter(created_at__date__gte=from_date)
        if to_date:
            total_sales = total_sales.filter(created_at__date__lte=to_date)
            total_purchase = total_purchase.filter(created_at__date__lte=to_date)
        if product:
            total_sales = total_sales.filter(product__name__icontains=product)
            total_purchase = total_purchase.filter(product__name__icontains=product)

        total_cost_calc = ExpressionWrapper(
            F('quantity')*F('unit_price'),
            output_field = DecimalField(max_digits=15, decimal_places=2)
        )
        total_revenue_calc = ExpressionWrapper(
            F('quantity')*F('selling_price'),
            output_field= DecimalField(max_digits=15, decimal_places=2)
        )

        total_cost = total_purchase.aggregate(
            total_cost=Sum(total_cost_calc,default=0),
            purchase_count = Count('id'),
            total_quantity = Sum('quantity',default=0),
        )
        total_revenue = total_sales.aggregate(
            total_revenue=Sum(total_revenue_calc,default=0),
            sales_count=Count('id'),
            total_quantity=Sum('quantity', default=0),
        )
        profit = total_revenue['total_revenue'] - total_cost['total_cost']
        profit_margin = round((profit / total_revenue['total_revenue'] * 100), 2) if total_revenue['total_revenue'] > 0 else 0

        return Response({
            'metadata': {
                'generated_at': timezone.now(),
                'from':from_date,
                'to': to_date,
                'filter_product': product if product else "All Products",
            },
            'summary':{
                'total_cost': total_cost['total_cost'],
                'total_revenue': total_revenue['total_revenue'],
                'net_profit': profit,
                'profit_margin': profit_margin,
            },
            'volume': {
                'sales_count': total_revenue['sales_count'],
                'purchases_count': total_cost['purchase_count'],
            },
            'quantity': {
                'sold_quantity': total_revenue['total_quantity'],
                'purchased_quantity': total_cost['total_quantity'],
            }
        },status=status.HTTP_200_OK)



class TopSellingProducts(APIView):
    permission_classes = (IsManager,)

    def get(self, request):
        from_date = request.query_params.get('from')
        to_date = request.query_params.get('to')
        try:
            limit = int(request.query_params.get('limit', 10))
        except (ValueError, TypeError):
            limit = 10
        sort_by = request.query_params.get('sort_by','sells')
        time_frame = request.query_params.get('time', 'week')
        now = timezone.now()

        sort_mapping = {
            'sells': '-total_sells',
            'revenue': '-total_revenue',
            'transactions': '-total_sells_transactions'
        }
        order_field = sort_mapping.get(sort_by, '-total_sells')

        time_mapping = {
            'today': now - timedelta(days=1),
            'week': now - timedelta(days=7),
            'month': now - timedelta(days=30),
            'year': now - timedelta(days=365),
            'overall': None
        }
        filter_time = time_mapping.get(time_frame)

        sells = Sale.objects.filter(status='Completed')
        if not (from_date or to_date) and filter_time:
            sells = sells.filter(created_at__gte=filter_time)

        if from_date:
            sells = sells.filter(created_at__date__gte=from_date)
        if to_date:
            sells = sells.filter(created_at__date__lte=to_date)

        total_revenue_calc = ExpressionWrapper(
            F('quantity') * F('selling_price'),
            output_field=DecimalField(max_digits=15, decimal_places=2)
        )

        total_sells = sells.values('product','product__name').annotate(
            product_id = F('product_id'),
            product_name = F ('product__name'),
            total_sells = Sum('quantity',default=0),
            total_revenue = Sum(total_revenue_calc,default=0),
            total_sells_transactions = Count('id'),
        ).order_by(order_field)[:limit]

        serializer = TopSellingReportSerializer(total_sells, many=True).data

        return Response({
            'metadata': {
                'generated_at': timezone.now(),
                'from': from_date,
                'to': to_date,
                'limit': limit,
            },
            'top_selling_products': serializer,
        },status=status.HTTP_200_OK)



class TopSellingPersonsView(APIView):
    permission_classes = (IsManager,)

    def get(self, request):
        from_date = request.query_params.get('from')
        to_date = request.query_params.get('to')
        try:
            limit = int(request.query_params.get('limit', 10))
        except (ValueError, TypeError):
            limit = 10
        sort_by = request.query_params.get('sort_by','sells')
        time_frame = request.query_params.get('time','week')
        now = timezone.now()

        sort_mapping = {
            'sells': '-total_sells',
            'revenue': '-total_revenue',
            'transactions': '-total_sells_transactions'
        }
        order_field = sort_mapping.get(sort_by, '-total_sells')

        time_mapping = {
            'today': now - timedelta(days=1),
            'week': now - timedelta(days=7),
            'month': now - timedelta(days=30),
            'year': now - timedelta(days=365),
            'overall': None
        }
        filter_time = time_mapping.get(time_frame)

        sells = Sale.objects.filter(status='Completed')
        if not (from_date or to_date) and filter_time:
            sells = sells.filter(created_at__gte=filter_time)
        if from_date:
            sells = sells.filter(created_at__date__gte=from_date)
        if to_date:
            sells = sells.filter(created_at__date__lte=to_date)

        total_revenue_calc = ExpressionWrapper(
            F('quantity') * F('selling_price'),
            output_field=DecimalField(max_digits=15, decimal_places=2)
        )

        total_sells = sells.values('sold_by','sold_by__username').annotate(
            sells_person_id = F('sold_by'),
            sells_person_name = F ('sold_by__username'),
            total_sells = Sum('quantity',default=0),
            total_revenue = Sum(total_revenue_calc,default=0),
            total_sells_transactions = Count('id'),
        ).order_by(order_field)[:limit]

        serializer = TopSellingPerson(total_sells, many=True).data

        return Response({
            'metadata': {
                'generated_at': timezone.now(),
                'active_time_frame': time_frame if not (from_date or to_date) else "custom",
                'from': from_date,
                'to': to_date,
                'limit': limit,
            },
            'top_sellers': serializer,
        },status=status.HTTP_200_OK)


class SummaryReports(APIView):
    permission_classes = (IsManager,)

    def get(self, request):
        from_date = request.query_params.get('from')
        to_date = request.query_params.get('to')
        group_by = request.query_params.get('group_by','day')

        trunc_map = {
            'day': TruncDay,
            'week': TruncWeek,
            'month': TruncMonth,
            'year': TruncYear,
        }

        total_revenue_calc = ExpressionWrapper(
            F('quantity') * F('selling_price'),
            output_field=DecimalField(max_digits=15, decimal_places=2)
        )
        total_purchase_calc = ExpressionWrapper(
            F('quantity') * F('unit_price'),
            output_field=DecimalField(max_digits=15, decimal_places=2)
        )
        sales = Sale.objects.filter(status='Completed')
        purchases = PurchaseOrder.objects.filter(status='Completed')
        if from_date:
            sales = sales.filter(created_at__date__gte=from_date)
            purchases = purchases.filter(created_at__date__gte=from_date)
        if to_date:
            sales = sales.filter(created_at__date__lte=to_date)
            purchases = purchases.filter(created_at__date__lte=to_date)

        sales_summary = sales.aggregate(
            total_sales = Sum('quantity',default=0),
            total_revenue = Sum(total_revenue_calc,default=0),
            total_sales_transactions = Count('id'),
        )
        purchases_summary = purchases.aggregate(
            total_purchases = Sum('quantity',default=0),
            total_cost = Sum(total_purchase_calc,default=0),
            total_purchase_transactions = Count('id'),
        )
        profit = sales_summary['total_revenue'] - purchases_summary['total_cost']
        profit_margin = round((profit / sales_summary['total_revenue'] * 100), 2) if sales_summary['total_revenue'] > 0 else 0

        if group_by not in ['day', 'week', 'month', 'year']:
            group_by = 'day'
        trunc_func = trunc_map[group_by]
        sales_list = sales.annotate(
            time_period = trunc_func('created_at')
        ).values('time_period').annotate(
            total_sales = Sum('quantity',default=0),
            total_revenue = Sum(total_revenue_calc,default=0),
            total_sales_transactions = Count('id'),
        ).order_by('-time_period')

        serializer = SummaryTimelineSerializer(sales_list, many=True).data

        return Response({
            'metadata': {
                'generated_at': timezone.now(),
                'from':from_date,
                'to':to_date,
                'time_period': group_by,
            },
            'summary': {
                'total_sales': sales_summary['total_sales'],
                'total_revenue': sales_summary['total_revenue'],
                'total_sales_transactions':sales_summary['total_sales_transactions'],
                'net_profit':profit,
                'profit_margin':profit_margin,
            },
            'timeline': serializer,
        })


