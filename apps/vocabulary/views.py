from rest_framework.filters import SearchFilter
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import IsAuthenticated

from common.filters import filter_choice

from .models import Vocabulary
from .serializers import VocabularySerializer


class VocabularyListCreateView(ListCreateAPIView):
    serializer_class = VocabularySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = ["word", "meaning", "translation", "example_sentence", "notes"]

    def get_queryset(self):
        queryset = Vocabulary.objects.filter(user=self.request.user)
        queryset = filter_choice(
            queryset, self.request, "mastery_level", Vocabulary.MasteryLevel.choices
        )
        return filter_choice(
            queryset, self.request, "part_of_speech", Vocabulary.PartOfSpeech.choices
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class VocabularyDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = VocabularySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Vocabulary.objects.filter(user=self.request.user)
