from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import render, reverse
from django.views.generic import ListView

from achievements import models
from achievements import calculate


class AchievementProgressList(LoginRequiredMixin, ListView):
    context_object_name = 'achievement_progress'

    def get_queryset(self):
        return models.AchievementProgress.objects.filter(user=self.request.user, level__gte=1)

    def get_context_data(self, **kwargs):
        context = super(AchievementProgressList, self).get_context_data(**kwargs)
        # Add some upcoming achievements
        context['upcoming_achievements'] = models.AchievementProgress.objects.filter(user=self.request.user, level=0, progress__isnull=False)[:3]
        return context

@login_required
def calculate_achievements(request):
    user = request.user
    print('request user', user)
    for achievement in models.Achievement.objects.all():
        print(achievement)
        func = getattr(calculate, achievement.code)
        level, progress = func(user)
        print(level, progress)
        if level > 0 or progress is not None:
            models.AchievementProgress.objects.update_or_create(
                user=user,
                achievement=achievement,
                defaults={
                    'level': level,
                    'progress': progress,
                }
            )
    return HttpResponseRedirect(reverse('progress_list'))
