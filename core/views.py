from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def home(request):
    return HttpResponse("Hello! Elias's Django is live! 🚀 And I can just push changes.")