from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required


def login_view(request):
    message = ""

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # ADMIN (no profile)
            if user.is_superuser and not hasattr(user, 'userprofile'):
                return redirect('/admin/')

            # USERS WITH ROLES
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


@login_required
def home(request):
    role = None

    if hasattr(request.user, 'userprofile'):
        role = request.user.userprofile.role

    return render(request, 'core/home.html', {
        'role': role
    })


def logout_view(request):
    logout(request)
    return redirect('login')