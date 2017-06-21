from django.shortcuts import render
from django.views.generic import ListView

from achievements import models

class AchievementProgressList(ListView):
    context_object_name = 'achievement_progress'

    def get_queryset(self):
        return models.AchievementProgress.objects.filter(user=self.request.user, level__gte=1)

    def get_context_data(self, **kwargs):
        context = super(AchievementProgressList, self).get_context_data(**kwargs)
        # Add some upcoming achievements
        context['upcoming_achievements'] = models.AchievementProgress.objects.filter(user=self.request.user, level=0, progress__isnull=False)[:3]
        return context
