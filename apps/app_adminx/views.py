from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render


@staff_member_required
def adminx_home(request):
    return render(request, 'app_adminx/home.html', {})
