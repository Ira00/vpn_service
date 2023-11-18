# views.py
import re
from urllib.parse import urlparse

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
import requests
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from vpn_site.forms import UserProfileForm
from vpn_site.models import Site, Statistics

from decimal import Decimal


@login_required
def profile(request, username):
    user = User.objects.get(username=username)
    sites = Site.objects.filter(user=request.user)
    statistics = Statistics.objects.filter(user=request.user)
    context = {
        'user': user,
        'sites': sites,
        'statistics': statistics,
    }

    return render(request, 'vpn_site/profile.html', context=context)


@login_required
def create_site(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        url = request.POST.get('url')

        site = Site.objects.create(user=request.user, name=name, url=url)
        Statistics.objects.create(user=request.user, site=site)

    return redirect('profile', request.user.username)


@login_required
def proxy_route(request, user_site_name, routes_on_original_site):

    site = Site.objects.get(name=user_site_name, user=request.user)
    original_url = site.url + '/' + routes_on_original_site

    try:
        response = requests.get(routes_on_original_site)
        content = response.text

        base_url = urlparse(original_url).scheme + '://' + urlparse(original_url).hostname

        stats, created = Statistics.objects.get_or_create(user=request.user, site=site)
        stats.page_views += 1
        stats.data_received += Decimal(len(response.content)) / Decimal(1024)  # Конвертація в Decimal
        stats.data_sent += Decimal(len(response.content)) / Decimal(1024)  # Assuming the response content is data sent from the site
        stats.save()

        content = replace_internal_links(content, base_url, user_site_name)
        print(stats.page_views, routes_on_original_site)

        return HttpResponse(content)

    except requests.RequestException as e:
        return HttpResponse(f"Error: {e}", status=500)


def replace_internal_links(content, base_url, user_site_name):
    pattern = r'href="(\/[^"]+)"'
    matches = re.findall(pattern, content)

    for url in matches:
        if is_resource_link(url):
            continue
        if not url.startswith('//'):
            modified_url = f'{reverse("proxy_route", kwargs={"user_site_name": user_site_name, "routes_on_original_site": base_url + url})}'
        else:
            modified_url = f'{reverse("proxy_route", kwargs={"user_site_name": user_site_name, "routes_on_original_site": "https:"+url})}'
        # modified_url = modified_url.replace('//', '/')
        content = content.replace(f'href="{url}"', f'href="{modified_url}"')

    pattern_main_page = r'href="(\/)"'
    matches_main_page = re.findall(pattern_main_page, content)
    for url in matches_main_page:
        modified_url = f'{reverse("proxy_route", kwargs={"user_site_name": user_site_name, "routes_on_original_site": base_url})}'
        content = content.replace(f'href="{url}"', f'href="{modified_url}"')

    return content


def is_resource_link(url):
    # Define patterns for resource links (adjust as needed)
    resource_patterns = ['.js', '.css', '.png', '.jpg', '.gif']
    return any(pattern in url for pattern in resource_patterns)



def register(request):

    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse("profile", args=[request.user.username]))
    if request.method == 'POST':
        form = UserProfileForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserProfileForm()

    return render(request, 'vpn_site/register.html', {'form': form})

@login_required
def edit_profile(request, username):
    user = request.user

    if request.method == 'POST':
        # Update user data directly
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.save()
        return redirect('profile', username=user.username)

    return render(request, 'vpn_site/edit_profile.html', {'user': user})


def login_view(request):
    if request.method == "POST":
        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("profile", args=[user.username]))
        else:
            return render(request, "vpn_site/login.html", {
                "message": "Неправильне ім'я користувача та/або пароль."
            })
    else:
        return render(request, "vpn_site/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("login"))
