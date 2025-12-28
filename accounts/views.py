from rest_framework import status, permissions
from rest_framework.generics import CreateAPIView
from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from django.conf import settings
from .serializers import (SignupSerializer,OtpVerificationSerializer,
                          OtpResendSerializer,LoginSerializer,OtpCodeSerializer,
                          PassResetSerializer,
                          )

def send_otp(otp):
    send_mail(
        subject="Your Verification Code",
        message=f"""
    Hello {otp.user.username},

    Your verification code is: {otp.code}

    This code is valid for the next 5 minutes. 
    Please use it to complete your action. 
    If you did not request this, please ignore this email.

    Thank you,
    The Inventory Management Team
    """,
        from_email=f"Inventory Management System<{settings.EMAIL_HOST_USER}>",
        recipient_list=[otp.user.email],
        fail_silently=False
    )


# Create your views here.
class SignupView(CreateAPIView):
    model = User
    serializer_class = SignupSerializer
    permission_classes = (permissions.AllowAny,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            otp = serializer.save()
            try:
                send_otp(otp)
            except Exception as e:
                print(f"unable to send otp code: {e}")
            return Response({
                'message':'Otp sent successfully',
            },status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyOtpView(APIView):
    permission_classes = (permissions.AllowAny,)
    def post(self, request, *args, **kwargs):
        serializer = OtpVerificationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            try:
                send_mail(
                    subject="Welcome to Inventory Management System",
                    message = f"""
        Hello {user.username},

        Your account has been successfully verified.

        Welcome to the Inventory Management System! You can now login and start managing your inventory.

        Thank you,
        Inventory Management Team
        """,

                from_email=f"Inventory Management System<{settings.EMAIL_HOST_USER}>",
                    recipient_list=[user.email],
                    fail_silently=False
                )
            except Exception as e:
                print(f"Unable to send email, {e}")
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                "message": "Your account has been successfully verified and you are now logged in.",
            },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class OtpResendView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = OtpResendSerializer(data=request.data)
        if serializer.is_valid():
            otp = serializer.save()
            try:
                send_otp(otp)
            except Exception as e:
                print(f"unable to send otp code: {e}")
            return Response({
                'message':'Otp sent successfully',
            },status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                "message": "Login successful."
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({
                'detail':'Refresh token required',
            },status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({
                'detail':'Successfully logged out',
            },status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response({
                'detail':'Invalid or Expired Token',
            },status=status.HTTP_400_BAD_REQUEST)


class OtpRequestView(APIView):
    permission_classes = (permissions.AllowAny,)
    def post(self, request):
        serializer = OtpCodeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            otp = serializer.instance
            try:
                send_otp(otp)
            except Exception as e:
                print(f"Unable to send email, {e}")
            return Response({
                "message": "OTP code sent successfully",
            },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = PassResetSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            try:
                send_mail(
                    subject="Your Password Has Been Reset",
                    message=f"""
            Hello {user.username},

            This is a confirmation that your account password has been successfully reset. 
            If you did not request this change, please contact our support team immediately.

            Thank you,
            The Event Management Team
            """,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False
                )
            except Exception as e:
                print(f"Unable to send email, {e}")
            return Response({
                "message": "Password reset successfully",
            },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

