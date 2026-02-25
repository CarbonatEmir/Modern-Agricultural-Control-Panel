#veritabanının kodlarını buradan yapacağız.

''' from django.db import models

class TomatoAnalysis(models.Model):
    image_name = models.CharField(max_length=200)
    ripeness_percentage = models.IntegerField()
    category = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.image_name 

# Create your models here.
'''
from django.db import models

class AnalizGecmisi(models.Model):
    kamera_adi = models.CharField(max_length=50)
    ham_sayisi = models.IntegerField(default=0)
    yari_olgun_sayisi = models.IntegerField(default=0)
    olgun_sayisi = models.IntegerField(default=0)
    ortalama_olgunluk = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    analiz_tarihi = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'analiz_gecmisi' # Veritabanındaki tablo adını tam olarak belirtiyoruz
        ordering = ['-analiz_tarihi'] # Hep en son analiz en üstte gelsin