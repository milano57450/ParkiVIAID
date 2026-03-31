# ============================================================
# PROJET ParkiVIAD - Étudiant 3 : Backend & Base de données
# Fichier de démarrage : modèles Django + premiers endpoints
# ============================================================
# Prérequis (à installer sur le Raspberry Pi ou votre PC) :
#   pip install django djangorestframework psycopg2-binary
#
# Pour créer le projet Django :
#   django-admin startproject parkiviad_backend
#   cd parkiviad_backend
#   python manage.py startapp parking
# ============================================================


# ---- FICHIER : parking/models.py ----
# Ce fichier définit la structure de votre base de données.
# Django va créer automatiquement les tables PostgreSQL.

from django.db import models


class Place(models.Model):
    """
    Représente une place de parking physique.
    """
    STATUT_CHOICES = [
        ('LIBRE', 'Libre'),
        ('OCCUPEE', 'Occupée'),
        ('RESERVEE', 'Réservée'),
        ('HORS_SERVICE', 'Hors service'),
    ]

    numero = models.IntegerField(unique=True)            # Numéro de la place (ex: 42)
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='LIBRE'
    )
    zone = models.CharField(max_length=10, default='A')  # Zone A, B, C...
    derniere_mise_a_jour = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Place {self.numero} ({self.statut})"

    class Meta:
        ordering = ['numero']


class Badge(models.Model):
    """
    Badge RFID DESFire autorisé à entrer dans le parking.
    """
    uid = models.CharField(max_length=64, unique=True)   # Identifiant unique du badge
    proprietaire = models.CharField(max_length=100)      # Nom du porteur
    actif = models.BooleanField(default=True)            # Badge valide ou révoqué
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Badge {self.uid} - {self.proprietaire}"


class EvenementAcces(models.Model):
    """
    Log de chaque entrée/sortie ou tentative d'accès.
    Permet la supervision et la détection de fraude.
    """
    TYPE_CHOICES = [
        ('ENTREE', 'Entrée'),
        ('SORTIE', 'Sortie'),
        ('REFUS', 'Accès refusé'),
        ('ALERTE', 'Alerte sécurité'),
    ]

    badge = models.ForeignKey(
        Badge,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    type_evenement = models.CharField(max_length=20, choices=TYPE_CHOICES)
    horodatage = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)           # Détails supplémentaires

    def __str__(self):
        return f"{self.type_evenement} à {self.horodatage}"

    class Meta:
        ordering = ['-horodatage']  # Les plus récents en premier


# ============================================================
# ---- FICHIER : parking/serializers.py ----
# Transforme les objets Python en JSON (pour l'API REST)
# ============================================================

from rest_framework import serializers
# from .models import Place, Badge, EvenementAcces  # décommenter dans le vrai fichier


class PlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = '__all__'  # Tous les champs


class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = ['id', 'uid', 'proprietaire', 'actif', 'date_creation']


class EvenementAccesSerializer(serializers.ModelSerializer):
    badge_uid = serializers.CharField(source='badge.uid', read_only=True)

    class Meta:
        model = EvenementAcces
        fields = ['id', 'badge', 'badge_uid', 'type_evenement', 'horodatage', 'description']


# ============================================================
# ---- FICHIER : parking/views.py ----
# Les endpoints de l'API (ce que le serveur répond)
# ============================================================

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
# from .models import Place, Badge, EvenementAcces       # décommenter dans le vrai fichier
# from .serializers import *                             # décommenter dans le vrai fichier


class PlaceViewSet(viewsets.ModelViewSet):
    """
    Endpoints automatiques pour les places :
      GET    /api/places/           -> liste toutes les places
      POST   /api/places/           -> crée une place
      GET    /api/places/{id}/      -> détail d'une place
      PUT    /api/places/{id}/      -> modifie une place
      DELETE /api/places/{id}/      -> supprime une place
    """
    queryset = Place.objects.all()
    serializer_class = PlaceSerializer

    @action(detail=False, methods=['get'])
    def libres(self, request):
        """
        Endpoint spécial : GET /api/places/libres/
        Retourne uniquement les places libres.
        Utile pour l'affichage temps réel.
        """
        places_libres = Place.objects.filter(statut='LIBRE')
        serializer = self.get_serializer(places_libres, many=True)
        return Response({
            'count': places_libres.count(),
            'places': serializer.data
        })

    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """
        Endpoint spécial : GET /api/places/statistiques/
        Retourne un résumé du parking.
        """
        total = Place.objects.count()
        libres = Place.objects.filter(statut='LIBRE').count()
        occupees = Place.objects.filter(statut='OCCUPEE').count()

        return Response({
            'total': total,
            'libres': libres,
            'occupees': occupees,
            'taux_occupation': round((occupees / total * 100), 1) if total > 0 else 0
        })


class BadgeViewSet(viewsets.ModelViewSet):
    """
    CRUD complet pour les badges RFID.
    """
    queryset = Badge.objects.all()
    serializer_class = BadgeSerializer

    @action(detail=False, methods=['post'])
    def verifier(self, request):
        """
        Endpoint : POST /api/badges/verifier/
        Corps : { "uid": "ABCD1234" }
        Vérifie si un badge est autorisé (pour l'ESP32/RFID).
        """
        uid = request.data.get('uid')
        if not uid:
            return Response({'erreur': 'UID manquant'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            badge = Badge.objects.get(uid=uid, actif=True)
            # Log de l'accès accordé
            EvenementAcces.objects.create(
                badge=badge,
                type_evenement='ENTREE',
                description=f"Accès accordé - Badge {uid}"
            )
            return Response({'autorise': True, 'proprietaire': badge.proprietaire})
        except Badge.DoesNotExist:
            # Log du refus
            EvenementAcces.objects.create(
                badge=None,
                type_evenement='REFUS',
                description=f"Badge inconnu ou révoqué : {uid}"
            )
            return Response({'autorise': False}, status=status.HTTP_403_FORBIDDEN)


class EvenementAccesViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Lecture seule des logs d'accès (pour le dashboard).
    """
    queryset = EvenementAcces.objects.all()[:100]  # Les 100 derniers
    serializer_class = EvenementAccesSerializer


# ============================================================
# ---- FICHIER : parking/urls.py ----
# Enregistre les routes de l'API
# ============================================================

from rest_framework.routers import DefaultRouter
# from .views import PlaceViewSet, BadgeViewSet, EvenementAccesViewSet  # décommenter

router = DefaultRouter()
router.register(r'places', PlaceViewSet)
router.register(r'badges', BadgeViewSet)
router.register(r'evenements', EvenementAccesViewSet)

urlpatterns = router.urls


# ============================================================
# ---- COMMANDES À EXÉCUTER dans le terminal ----
# (après avoir créé le projet Django)
# ============================================================

# 1. Créer les tables dans la base de données :
#    python manage.py makemigrations
#    python manage.py migrate

# 2. Créer un admin :
#    python manage.py createsuperuser

# 3. Peupler la base avec des places de test :
#    python manage.py shell
#    >>> from parking.models import Place
#    >>> for i in range(1, 21):
#    ...     Place.objects.create(numero=i)
#    >>> print(Place.objects.count(), "places créées")

# 4. Lancer le serveur de développement :
#    python manage.py runserver 0.0.0.0:8000
#    -> Accessible sur http://localhost:8000/api/
