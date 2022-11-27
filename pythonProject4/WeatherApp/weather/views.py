from django.shortcuts import render, redirect
from django.http import HttpResponse
import requests
from .models import City
from . import forms


# Create your views here.
def index(request):
    appid = "4541d65e7611fbd586436846fcd10bb7"
    url = "https://api.openweathermap.org/data/2.5/weather?q={}&units=metric&appid=" + appid

    cities = City.objects.all()

    all_cities = []

    for city in cities:
        try:
            res = requests.get(url.format(city)).json()
            city_info = {
                "city": city,
                "temp": res["main"]["temp"],
                "feels_like": res["main"]["feels_like"],
                "speed": res["wind"]["speed"],
                "clouds": res["clouds"]["all"],
                "humidity": res["main"]["humidity"],
                "icon": res["weather"][0]["icon"],
            }
        except KeyError:
            pass
        else:
            all_cities.append(city_info)
    context = {"all_info": all_cities}
    return render(request, 'weather/index.html', context)


def add_city(request):
    if request.method == "POST":
        form1 = forms.CityForm(request.POST)  # заполнение формы
        if form1.is_valid():  # проверка валидности формы
            form1.save()  # сохранение данных в базу
            return redirect('index')
    else:
        form1 = forms.CityForm()
    return render(request, 'weather/add_city.html', {"CityForm": form1})  # передача формы Form1 в шаблон


def del_city(request, id_city):
    city = City.objects.get(id=id_city)
    city.delete()
    return redirect('index')


def info(request):
    return render(request, 'weather/info.html')
