# Tüm kodları buradan yapacağız BACKEND
'''
from django.shortcuts import render
from .models import TomatoAnalysis
from django.db.models import Avg



def home(request):
    total = TomatoAnalysis.objects.count()
    average = TomatoAnalysis.objects.aggregate(Avg('ripeness_percentage'))['ripeness_percentage__avg']
    ham = TomatoAnalysis.objects.filter(category='ham').count()
    yari = TomatoAnalysis.objects.filter(category='yari').count()
    olgun = TomatoAnalysis.objects.filter(category='olgun').count()

    context = {
        'total':total,
        'average': round(average,2) if average else 0,
        'ham': ham,
        'yari':yari,
        'olgun':olgun,

    }
    return render(request, 'index.html',context)
'''

from django.shortcuts import render
from .models import AnalizGecmisi

def dashboard(request):
    son_analiz = AnalizGecmisi.objects.first() 
    
    if son_analiz:
        total = son_analiz.ham_sayisi + son_analiz.yari_olgun_sayisi + son_analiz.olgun_sayisi

        context = {
            'total': total,
            'average': son_analiz.ortalama_olgunluk,
            'ham': son_analiz.ham_sayisi,
            'yari': son_analiz.yari_olgun_sayisi,
            'olgun': son_analiz.olgun_sayisi,
        }
    else:
        context = {'total': 0, 'average': 0, 'ham': 0, 'yari': 0, 'olgun': 0}
        
    return render(request, 'index.html', context)

def analiz_gecmisi(request):
    tum_analizler = AnalizGecmisi.objects.all()
    
    return render(request, 'gecmis.html', {'analizler': tum_analizler})


def kameralar(request):
    return render(request, 'kameralar.html')

def ayarlar(request):
    return render(request, 'ayarlar.html')
