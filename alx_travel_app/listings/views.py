from django.conf import settings
from django.shortcuts import render
from rest_framework import generics
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import User, Listing, Booking, Review, Payment, BookingChoice, PaymentChoice
from .serializers import UserSerializer, ListingSerializer, BookingSerializer, ReviewSerializer, PaymentSerializer
from decimal import Decimal
import requests
import uuid




class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer


class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer


class PaymentListAPIView(generics.ListAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer


class ChapaInitiatePaymentAPIView(APIView):
    def post(self, request):
        try:
            booking_id = request.data.get('booking_id')
            booking = Booking.objects.get(booking_id=booking_id)
        except Booking.DoesNotExist:
            return Response(
                {'detail': 'Booking not found'},
                status=status.HTTP_400_NOT_FOUND
                )

        if booking.status == BookingChoice.CONFIRMED:
            return Response(
                {'detail': 'This booking has already been paid and confirmed.'},
                status=status.HTTP_400_BAD_REQUEST
                )

        url = 'https://api.chapa.co/v1/transaction/initialize'
        txn_ref = str(uuid.uuid4())
        first_name = booking.traveler.first_name
        last_name = booking.traveler.last_name
        email = booking.traveler.email
        phone = booking.traveler.phone
        amount = str(booking.total_price)

        payload = {
            "amount": amount,
            "currency": "ETB",
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "phone_number": phone,
            "tx_ref": txn_ref,
            "callback_url": "https://webhook.site/077164d6-29cb-40df-ba29-8a00e59a7e60",
            "return_url": "http://127.0.0.1:8000/api/bookings/",
            "customization": {
            "title": "ALX Travel App",
            "description": "Payment for bookings"
        }
        }

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {settings.CHAPA_SECRET_KEY}'
        }

        response = requests.post(url, json=payload, headers=headers)
        response_data = response.json()

        if response.status_code != 200 or response_data.get('status') != 'success':
            return Response({'detail': 'Payment Failed', 'error_response': response_data}, status=status.HTTP_400_BAD_REQUEST)

        checkout_url = response_data['data']['checkout_url']

        payment = Payment.objects.create(
            booking=booking,
            amount=Decimal(amount),
            gateway='Chapa',
            paid=False,
            status=PaymentChoice.PENDING,
            txn_ref=txn_ref
        )
        payment_info = PaymentSerializer(payment).data
        print(payment_info)

        return Response({
            'detail': 'Payment Initiated',
            'checkout_url': checkout_url,
            'payment': payment_info
        })



class ChapaPaymentVerifyAPIView(APIView):
    def post(self, request):
        try:
            txn_ref = request.data.get('txn_ref')
            print(txn_ref)
            payment = Payment.objects.get(txn_ref=txn_ref)
        except Payment.DoesNotExist:
            return Response({'detail': 'Payment not found'}, status=status.HTTP_404_NOT_FOUND)

        url = f'https://api.chapa.co/v1/transaction/verify/{txn_ref}'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {settings.CHAPA_SECRET_KEY}'
        }

        response = requests.get(url, headers=headers)
        response_data = response.json()

        if response.status_code == 200 and response_data.get('status') == 'success':
            txn_status = response_data['data']['status']
            if txn_status == 'success':
                payment.booking.status = BookingChoice.CONFIRMED
                payment.paid = True
                payment.status = PaymentChoice.COMPLETED
                payment.booking.save()
            else:
                payment.paid = False
                payment.status = PaymentChoice.FAILED
        
        payment.save()
        payment_info = PaymentSerializer(payment).data
        return Response({'detail': 'Payment verification successful', 'payment': payment_info}, status=status.HTTP_200_OK)