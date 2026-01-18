from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views import generic

from .forms import CustomUserCreationForm, UserProfileForm
from .models import User

class RegisterView(generic.CreateView):
    """
    View for user registration
    """
    form_class = CustomUserCreationForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('login')
    
    def form_valid(self, form):
        # Save the new user
        response = super().form_valid(form)
        messages.success(self.request, _('Your account has been created. You can now log in.'))
        return response

@login_required
def profile(request):
    """
    View for user profile management
    """
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _('Your profile has been updated.'))
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'users/profile.html', {
        'form': form,
    })

@login_required
def profile_delete(request):
    """
    View for account deletion
    """
    if request.method == 'POST':
        user = request.user
        user.delete()
        messages.success(request, _('Your account has been deleted.'))
        return redirect('home')
    
    return render(request, 'users/profile_delete.html')

@login_required
def settings(request):
    """
    View for user settings management
    """
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _('Your settings have been updated.'))
            return redirect('settings')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'users/settings.html', {
        'form': form,
    })
