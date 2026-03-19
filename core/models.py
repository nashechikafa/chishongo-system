from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('CEO', 'CEO'),
        ('Manager', 'Manager'),
        ('Cashier', 'Cashier'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.user.username} - {self.role}"


class Product(models.Model):
    name = models.CharField(max_length=200)
    quantity = models.IntegerField(default=0)
    buying_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    supplier = models.CharField(max_length=200)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Sale(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    cashier_name = models.CharField(max_length=200)
    quantity_sold = models.IntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True, null=True)
    sale_date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.product.quantity -= self.quantity_sold
            self.product.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} - {self.quantity_sold}"


class StockDelivery(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    manager_name = models.CharField(max_length=200)
    quantity_added = models.IntegerField()
    buying_cost_total = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True, null=True)
    delivery_date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.product.quantity += self.quantity_added
            self.product.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} +{self.quantity_added}"


class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('Transport', 'Transport'),
        ('Rent', 'Rent'),
        ('Wages', 'Wages'),
        ('Electricity', 'Electricity'),
        ('Airtime/Data', 'Airtime/Data'),
        ('Maintenance', 'Maintenance'),
        ('Miscellaneous', 'Miscellaneous'),
    ]

    recorded_by = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    expense_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.category} - {self.amount}"