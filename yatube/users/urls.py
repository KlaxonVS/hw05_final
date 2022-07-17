from django.contrib.auth.views import (LoginView,
                                       LogoutView,
                                       PasswordChangeView,
                                       PasswordChangeDoneView,
                                       PasswordResetView,
                                       PasswordResetDoneView,
                                       PasswordResetConfirmView,
                                       PasswordResetCompleteView,
                                       )
from django.urls import path

from . import views

app_name = 'users'

urlpatterns = [
    path('signup/', views.SignUp.as_view(), name='signup'),
    path('login/',
         LoginView.as_view(template_name='users/login.html'),
         name='login'),
    path('logout/',
         LogoutView.as_view(template_name='users/logged_out.html'),
         name='logout'),
    path('password_change/',
         (PasswordChangeView.as_view
          (template_name='users/password_change.html')),
         name='password_change'),
    path('password_change/done/',
         (PasswordChangeDoneView.as_view
          (template_name='users/password_change_done.html')),
         name='password_change_done'),
    path('password_reset/',
         (PasswordResetView.as_view
          (template_name='users/password_reset.html')),
         name='password_reset'),
    path('password_reset/done/',
         (PasswordResetDoneView.as_view
          (template_name='users/password_reset_done.html')),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         (PasswordResetConfirmView.as_view
          (template_name='users/reset_confirm.html')),
         name='reset_confirm'),
    path('reset/done/',
         (PasswordResetCompleteView.as_view
          (template_name='users/reset_done.html')),
         name='reset_done'),
]
