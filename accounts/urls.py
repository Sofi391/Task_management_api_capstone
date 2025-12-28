from django.urls import path
from .views import SignupView,VerifyOtpView,OtpResendView,LoginView,OtpRequestView,PasswordResetView,LogoutView


urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('verify/otp/', VerifyOtpView.as_view(), name='verify_otp'),
    path('otp/resend/', OtpResendView.as_view(), name='otp_resend'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('otp/request/', OtpRequestView.as_view(), name='otp_request'),
    path('password-reset/', PasswordResetView.as_view(), name='password_reset'),
]
