# accounts/views.py
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth import login
from django.contrib import messages
from .forms import CustomUserCreationForm

class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('dashboard')  # Redirect to dashboard after signup
    template_name = 'registration/signup.html'
    
    def form_valid(self, form):
        response = super().form_valid(form)
        # Log the user in after successful signup
        login(self.request, self.object)
        messages.success(self.request, 'Welcome! Let\'s set up your virtual phone system.')
        return response