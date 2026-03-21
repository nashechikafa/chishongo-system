from django.db import migrations
from django.contrib.auth.hashers import make_password


def create_live_users(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    UserProfile = apps.get_model('core', 'UserProfile')

    # Admin
    admin_user, created = User.objects.get_or_create(
        username='nashe',
        defaults={
            'email': 'chikafawaltermunashe@gmail.com',
            'is_staff': True,
            'is_superuser': True,
            'password': make_password('walter201206'),
        }
    )
    if not created:
        admin_user.email = 'chikafawaltermunashe@gmail.com'
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.password = make_password('walter201206')
        admin_user.save()

    # CEO
    ceo_user, created = User.objects.get_or_create(
        username='ceo1',
        defaults={
            'email': 'ceo1@example.com',
            'password': make_password('chishongo2010'),
        }
    )
    if not created:
        ceo_user.password = make_password('chishongo2010')
        ceo_user.save()

    # Manager
    manager_user, created = User.objects.get_or_create(
        username='manager1',
        defaults={
            'email': 'manager1@example.com',
            'password': make_password('tsitsidzashe'),
        }
    )
    if not created:
        manager_user.password = make_password('tsitsidzashe')
        manager_user.save()

    # Cashier
    cashier_user, created = User.objects.get_or_create(
        username='cashier1',
        defaults={
            'email': 'cashier1@example.com',
            'password': make_password('maitanatswa'),
        }
    )
    if not created:
        cashier_user.password = make_password('maitanatswa')
        cashier_user.save()

    # Profiles
    UserProfile.objects.get_or_create(user=ceo_user, defaults={'role': 'CEO'})
    UserProfile.objects.get_or_create(user=manager_user, defaults={'role': 'Manager'})
    UserProfile.objects.get_or_create(user=cashier_user, defaults={'role': 'Cashier'})


def remove_live_users(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    User.objects.filter(username__in=['nashe', 'ceo1', 'manager1', 'cashier1']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_expense'),
    ]

    operations = [
        migrations.RunPython(create_live_users, remove_live_users),
    ]