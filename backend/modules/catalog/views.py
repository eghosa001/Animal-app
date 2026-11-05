from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny

from .models import Species
from .serializers import SpeciesSerializer


class SpeciesListView(ListAPIView):
    permission_classes = (AllowAny,)
    serializer_class = SpeciesSerializer
    queryset = Species.objects.all()
    pagination_class = None
