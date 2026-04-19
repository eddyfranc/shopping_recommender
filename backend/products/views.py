# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Product
from .recommender import get_recommendations

@api_view(['GET'])
def search_products(request):
    query = request.GET.get('query', '')
    products = Product.objects.filter(name__icontains=query)

    recommendations = get_recommendations(query)

    return Response({
        "products": list(products.values()),
        "recommendations": recommendations
    })