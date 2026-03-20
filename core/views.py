from django.shortcuts import render, redirect
from django.db.models import Sum, F, DecimalField, ExpressionWrapper, Q, Count
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Product, Sale, StockDelivery, UserProfile, Expense


def login_view(request):
    message = ""

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            if user.is_superuser and not hasattr(user, 'userprofile'):
                return redirect('/admin/')

            if hasattr(user, 'userprofile'):
                role = user.userprofile.role

                if role == 'CEO':
                    return redirect('dashboard')
                elif role == 'Cashier':
                    return redirect('cashier_sale_entry')
                elif role == 'Manager':
                    return redirect('manager_delivery_entry')

            return redirect('home')
        else:
            message = "Invalid username or password"

    return render(request, 'core/login.html', {'message': message})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def home(request):
    role = None
    if hasattr(request.user, 'userprofile'):
        role = request.user.userprofile.role

    return render(request, 'core/home.html', {'role': role})


@login_required
def dashboard(request):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'CEO':
        return redirect('home')

    today = timezone.now().date()

    total_products = Product.objects.count()
    total_sales = Sale.objects.count()

    total_revenue = Sale.objects.aggregate(total=Sum('total_price'))['total'] or 0
    today_revenue = Sale.objects.filter(sale_date__date=today).aggregate(total=Sum('total_price'))['total'] or 0

    profit_expression = ExpressionWrapper(
        (F('product__selling_price') - F('product__buying_price')) * F('quantity_sold'),
        output_field=DecimalField(max_digits=12, decimal_places=2)
    )

    total_profit = Sale.objects.annotate(
        profit_amount=profit_expression
    ).aggregate(total=Sum('profit_amount'))['total'] or 0

    today_profit = Sale.objects.filter(
        sale_date__date=today
    ).annotate(
        profit_amount=profit_expression
    ).aggregate(total=Sum('profit_amount'))['total'] or 0

    total_expenses = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0
    today_expenses = Expense.objects.filter(expense_date__date=today).aggregate(total=Sum('amount'))['total'] or 0

    net_profit = total_profit - total_expenses
    today_net_profit = today_profit - today_expenses

    low_stock_products = Product.objects.filter(quantity__lt=5).order_by('quantity')
    critical_stock_products = Product.objects.filter(quantity__lte=2).order_by('quantity')

    reorder_suggestions = []
    for product in low_stock_products:
        target_level = 20
        reorder_qty = target_level - product.quantity
        if reorder_qty > 0:
            estimated_cost = reorder_qty * product.buying_price
            reorder_suggestions.append({
                'name': product.name,
                'current_stock': product.quantity,
                'reorder_qty': reorder_qty,
                'estimated_cost': estimated_cost,
                'supplier': product.supplier
            })

    top_products = (
        Sale.objects.values('product__name')
        .annotate(total_qty=Sum('quantity_sold'))
        .order_by('-total_qty')[:5]
    )

    cashier_performance = (
        Sale.objects.values('cashier_name')
        .annotate(
            total_sales_amount=Sum('total_price'),
            total_items_sold=Sum('quantity_sold')
        )
        .order_by('-total_sales_amount')
    )

    today_cashier_summary = (
        Sale.objects.filter(sale_date__date=today)
        .values('cashier_name')
        .annotate(
            today_sales_amount=Sum('total_price'),
            today_items_sold=Sum('quantity_sold'),
            today_sale_count=Count('id')
        )
        .order_by('-today_sales_amount')
    )

    today_manager_delivery_summary = (
        StockDelivery.objects.filter(delivery_date__date=today)
        .values('manager_name')
        .annotate(
            deliveries_count=Count('id'),
            total_quantity_added=Sum('quantity_added'),
            total_delivery_cost=Sum('buying_cost_total')
        )
        .order_by('-total_quantity_added')
    )

    today_manager_expense_summary = (
        Expense.objects.filter(expense_date__date=today)
        .values('recorded_by')
        .annotate(
            expenses_count=Count('id'),
            total_expense_amount=Sum('amount')
        )
        .order_by('-total_expense_amount')
    )

    profitable_products = (
        Sale.objects.annotate(
            profit_amount=profit_expression
        )
        .values('product__name')
        .annotate(total_profit=Sum('profit_amount'))
        .order_by('-total_profit')[:5]
    )

    recent_deliveries = StockDelivery.objects.order_by('-delivery_date')[:5]
    recent_expenses = Expense.objects.order_by('-expense_date')[:5]
    recent_sales = Sale.objects.order_by('-sale_date')[:5]

    monthly_sales = (
        Sale.objects.annotate(month=TruncMonth('sale_date'))
        .values('month')
        .annotate(
            revenue=Sum('total_price'),
            gross_profit=Sum(
                ExpressionWrapper(
                    (F('product__selling_price') - F('product__buying_price')) * F('quantity_sold'),
                    output_field=DecimalField(max_digits=12, decimal_places=2)
                )
            )
        )
        .order_by('month')
    )

    monthly_expenses = (
        Expense.objects.annotate(month=TruncMonth('expense_date'))
        .values('month')
        .annotate(expenses=Sum('amount'))
        .order_by('month')
    )

    expense_map = {item['month']: item['expenses'] for item in monthly_expenses}

    monthly_trends = []
    max_net_profit = 1

    for item in monthly_sales:
        month = item['month']
        revenue = item['revenue'] or 0
        gross_profit = item['gross_profit'] or 0
        expenses_amount = expense_map.get(month, 0) or 0
        net_profit_amount = gross_profit - expenses_amount

        if abs(net_profit_amount) > max_net_profit:
            max_net_profit = abs(net_profit_amount)

        monthly_trends.append({
            'month': month,
            'revenue': revenue,
            'gross_profit': gross_profit,
            'expenses': expenses_amount,
            'net_profit': net_profit_amount,
        })

    for item in monthly_trends:
        item['bar_width'] = max(5, int((abs(item['net_profit']) / max_net_profit) * 100))

    warnings = []

    if critical_stock_products.exists():
        warnings.append("Some products are critically low and may run out very soon.")
    if low_stock_products.exists():
        warnings.append("Some products are low in stock.")
    if net_profit < 0:
        warnings.append("Overall net profit is negative.")
    if today_net_profit < 0:
        warnings.append("Today's net profit is negative.")
    if not recent_sales.exists():
        warnings.append("No sales have been recorded yet.")

    context = {
        'total_products': total_products,
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'today_revenue': today_revenue,
        'total_profit': total_profit,
        'today_profit': today_profit,
        'total_expenses': total_expenses,
        'today_expenses': today_expenses,
        'net_profit': net_profit,
        'today_net_profit': today_net_profit,
        'low_stock_products': low_stock_products,
        'critical_stock_products': critical_stock_products,
        'reorder_suggestions': reorder_suggestions,
        'top_products': top_products,
        'cashier_performance': cashier_performance,
        'today_cashier_summary': today_cashier_summary,
        'today_manager_delivery_summary': today_manager_delivery_summary,
        'today_manager_expense_summary': today_manager_expense_summary,
        'profitable_products': profitable_products,
        'recent_deliveries': recent_deliveries,
        'recent_expenses': recent_expenses,
        'monthly_trends': monthly_trends,
        'warnings': warnings,
    }

    return render(request, 'core/dashboard.html', context)


@login_required
def reports(request):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'CEO':
        return redirect('home')

    today = timezone.now().date()

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    sales_queryset = Sale.objects.all()
    expenses_queryset = Expense.objects.all()
    deliveries_queryset = StockDelivery.objects.all()

    if start_date and end_date:
        sales_queryset = sales_queryset.filter(sale_date__date__range=[start_date, end_date])
        expenses_queryset = expenses_queryset.filter(expense_date__date__range=[start_date, end_date])
        deliveries_queryset = deliveries_queryset.filter(delivery_date__date__range=[start_date, end_date])

    total_revenue = sales_queryset.aggregate(total=Sum('total_price'))['total'] or 0

    profit_expression = ExpressionWrapper(
        (F('product__selling_price') - F('product__buying_price')) * F('quantity_sold'),
        output_field=DecimalField(max_digits=12, decimal_places=2)
    )

    total_profit = sales_queryset.annotate(
        profit_amount=profit_expression
    ).aggregate(total=Sum('profit_amount'))['total'] or 0

    total_expenses = expenses_queryset.aggregate(total=Sum('amount'))['total'] or 0
    net_profit = total_profit - total_expenses

    today_revenue = Sale.objects.filter(sale_date__date=today).aggregate(total=Sum('total_price'))['total'] or 0
    today_profit = Sale.objects.filter(sale_date__date=today).annotate(
        profit_amount=profit_expression
    ).aggregate(total=Sum('profit_amount'))['total'] or 0
    today_expenses = Expense.objects.filter(expense_date__date=today).aggregate(total=Sum('amount'))['total'] or 0
    today_net_profit = today_profit - today_expenses

    recent_sales = sales_queryset.order_by('-sale_date')[:10]
    recent_expenses = expenses_queryset.order_by('-expense_date')[:10]
    recent_deliveries = deliveries_queryset.order_by('-delivery_date')[:10]

    return render(request, 'core/reports.html', {
        'today': today,
        'start_date': start_date,
        'end_date': end_date,
        'total_revenue': total_revenue,
        'today_revenue': today_revenue,
        'total_profit': total_profit,
        'today_profit': today_profit,
        'total_expenses': total_expenses,
        'today_expenses': today_expenses,
        'net_profit': net_profit,
        'today_net_profit': today_net_profit,
        'recent_sales': recent_sales,
        'recent_expenses': recent_expenses,
        'recent_deliveries': recent_deliveries,
    })


@login_required
def stock_history(request):
    if not hasattr(request.user, 'userprofile'):
        return redirect('home')

    role = request.user.userprofile.role
    if role not in ['CEO', 'Manager']:
        return redirect('home')

    query = request.GET.get('q', '')

    sales = Sale.objects.all()
    deliveries = StockDelivery.objects.all()

    if query:
        sales = sales.filter(
            Q(product__name__icontains=query) |
            Q(cashier_name__icontains=query) |
            Q(notes__icontains=query)
        )
        deliveries = deliveries.filter(
            Q(product__name__icontains=query) |
            Q(manager_name__icontains=query) |
            Q(notes__icontains=query)
        )

    movements = []

    for sale in sales:
        movements.append({
            'type': 'SALE',
            'product': sale.product.name,
            'quantity': sale.quantity_sold,
            'person': sale.cashier_name,
            'notes': sale.notes,
            'date': sale.sale_date,
        })

    for delivery in deliveries:
        movements.append({
            'type': 'DELIVERY',
            'product': delivery.product.name,
            'quantity': delivery.quantity_added,
            'person': delivery.manager_name,
            'notes': delivery.notes,
            'date': delivery.delivery_date,
        })

    movements = sorted(movements, key=lambda x: x['date'], reverse=True)

    return render(request, 'core/stock_history.html', {
        'movements': movements,
        'query': query
    })


@login_required
def products(request):
    if not hasattr(request.user, 'userprofile'):
        return redirect('home')

    role = request.user.userprofile.role
    if role not in ['CEO', 'Manager']:
        return redirect('home')

    query = request.GET.get('q', '')
    products = Product.objects.all().order_by('name')

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(supplier__icontains=query)
        )

    return render(request, 'core/products.html', {
        'products': products,
        'query': query
    })


@login_required
def sales(request):
    if not hasattr(request.user, 'userprofile'):
        return redirect('home')

    role = request.user.userprofile.role
    if role not in ['CEO', 'Cashier']:
        return redirect('home')

    query = request.GET.get('q', '')
    sales = Sale.objects.all().order_by('-sale_date')

    if query:
        sales = sales.filter(
            Q(product__name__icontains=query) |
            Q(cashier_name__icontains=query) |
            Q(notes__icontains=query)
        )

    return render(request, 'core/sales.html', {
        'sales': sales,
        'query': query
    })


@login_required
def deliveries(request):
    if not hasattr(request.user, 'userprofile'):
        return redirect('home')

    role = request.user.userprofile.role
    if role not in ['CEO', 'Manager']:
        return redirect('home')

    query = request.GET.get('q', '')
    deliveries = StockDelivery.objects.all().order_by('-delivery_date')

    if query:
        deliveries = deliveries.filter(
            Q(product__name__icontains=query) |
            Q(manager_name__icontains=query) |
            Q(notes__icontains=query)
        )

    return render(request, 'core/deliveries.html', {
        'deliveries': deliveries,
        'query': query
    })


@login_required
def expenses(request):
    if not hasattr(request.user, 'userprofile'):
        return redirect('home')

    role = request.user.userprofile.role
    if role not in ['CEO', 'Manager']:
        return redirect('home')

    query = request.GET.get('q', '')
    expenses = Expense.objects.all().order_by('-expense_date')

    if query:
        expenses = expenses.filter(
            Q(recorded_by__icontains=query) |
            Q(category__icontains=query) |
            Q(description__icontains=query)
        )

    return render(request, 'core/expenses.html', {
        'expenses': expenses,
        'query': query
    })


@login_required
def cashier_sale_entry(request):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'Cashier':
        return redirect('home')

    products = Product.objects.all().order_by('name')
    message = ""

    if request.method == 'POST':
        product_id = request.POST.get('product')
        quantity_sold = int(request.POST.get('quantity_sold'))
        notes = request.POST.get('notes')

        product = Product.objects.get(id=product_id)
        total_price = product.selling_price * quantity_sold

        if quantity_sold > product.quantity:
            message = "Not enough stock available for this sale."
        else:
            Sale.objects.create(
                product=product,
                cashier_name=request.user.username,
                quantity_sold=quantity_sold,
                total_price=total_price,
                notes=notes
            )
            return redirect('sales')

    return render(request, 'core/cashier_sale_entry.html', {
        'products': products,
        'message': message
    })


@login_required
def manager_delivery_entry(request):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'Manager':
        return redirect('home')

    products = Product.objects.all().order_by('name')

    if request.method == 'POST':
        product_id = request.POST.get('product')
        quantity_added = int(request.POST.get('quantity_added'))
        buying_cost_total = request.POST.get('buying_cost_total')
        notes = request.POST.get('notes')

        product = Product.objects.get(id=product_id)

        StockDelivery.objects.create(
            product=product,
            manager_name=request.user.username,
            quantity_added=quantity_added,
            buying_cost_total=buying_cost_total,
            notes=notes
        )

        return redirect('deliveries')

    return render(request, 'core/manager_delivery_entry.html', {
        'products': products
    })


@login_required
def manager_new_product_entry(request):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'Manager':
        return redirect('home')

    if request.method == 'POST':
        name = request.POST.get('name')
        quantity = int(request.POST.get('quantity'))
        buying_price = request.POST.get('buying_price')
        selling_price = request.POST.get('selling_price')
        supplier = request.POST.get('supplier')

        Product.objects.create(
            name=name,
            quantity=quantity,
            buying_price=buying_price,
            selling_price=selling_price,
            supplier=supplier
        )

        return redirect('products')

    return render(request, 'core/manager_new_product_entry.html')


@login_required
def manager_expense_entry(request):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'Manager':
        return redirect('home')

    if request.method == 'POST':
        category = request.POST.get('category')
        description = request.POST.get('description')
        amount = request.POST.get('amount')

        Expense.objects.create(
            recorded_by=request.user.username,
            category=category,
            description=description,
            amount=amount
        )

        return redirect('expenses')

    return render(request, 'core/manager_expense_entry.html')