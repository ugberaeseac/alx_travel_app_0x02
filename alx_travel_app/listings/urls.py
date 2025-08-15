
from django.urls import path, include
from rest_framework import routers
from listings.views import UserViewSet, ListingViewSet, BookingViewSet, ReviewViewSet
from listings.views import PaymentListAPIView, ChapaInitiatePaymentAPIView, ChapaPaymentVerifyAPIView



router = routers.DefaultRouter()
router.register(r'users', UserViewSet, basename='user-view')
router.register(r'listings', ListingViewSet, basename='listing-view')
router.register(r'bookings', BookingViewSet, basename='booking-view')
router.register(r'reviews', ReviewViewSet, basename='review-view')




urlpatterns = [
    path('', include((router.urls, 'listings'))),
    path('payments/', PaymentListAPIView.as_view(), name='payment-list'),
    path('payment/chapa/', ChapaInitiatePaymentAPIView.as_view(), name='chapa-initiate'),
    path('payment/chapa/verify/', ChapaPaymentVerifyAPIView.as_view(), name='chapa-verify'),

]

#urlpatterns += router.urls
