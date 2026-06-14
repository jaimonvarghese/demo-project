import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vigorcart_project.settings')
django.setup()

from store.models import Category, Product

data = {}
categories = Category.objects.all()

for cat in categories:
    products = Product.objects.filter(category=cat)
    if products.exists():
        cat_data = []
        for p in products:
            cat_data.append({
                'id': p.id,
                'name': p.p_name,
                'price': float(p.price) if p.price else None,
                'stock': p.stock_availability,
                'size': p.size,
                'description': p.description,
                'asset_id': p.asset_id,
                'shop': p.shop.name if p.shop else None,
            })
        data[cat.name] = cat_data

with open('products_by_category.json', 'w') as f:
    json.dump(data, f, indent=4)

print("Successfully exported products to products_by_category.json")
