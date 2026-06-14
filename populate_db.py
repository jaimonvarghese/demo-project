import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vigorcart_project.settings')
django.setup()

from store.models import User, Shop, Category, Product

def populate():
    # 1. Create Categories
    c_equip, _ = Category.objects.get_or_create(name='Gym Equipment')
    c_supps, _ = Category.objects.get_or_create(name='Supplements')
    c_wear, _ = Category.objects.get_or_create(name='Activewear')
    c_foot, _ = Category.objects.get_or_create(name='Footwear')
    c_acc, _ = Category.objects.get_or_create(name='Accessories')

    # 2. Create Shop Owners
    def create_vendor(username, email):
        user, created = User.objects.get_or_create(username=username, email=email)
        if created:
            user.set_password('123')
            user.role = User.IS_SHOP_OWNER
            user.save()
        return user

    v1 = create_vendor('iron_master', 'iron@store.com')
    v2 = create_vendor('nutrition_pro', 'nutri@store.com')
    v3 = create_vendor('sole_runner', 'sole@store.com')

    # 3. Create Shops
    def create_shop(owner, name, email, location):
        shop, _ = Shop.objects.get_or_create(
            owner=owner,
            name=name,
            email=email,
            location=location,
            opening_hours='10 AM - 8 PM',
            is_verified=True
        )
        return shop

    s1 = create_shop(v1, 'Iron Master Equipment', 'sales@ironmaster.com', 'Mumbai, MH')
    s2 = create_shop(v2, 'Nutrition Pro', 'orders@nutripro.com', 'Delhi, DL')
    s3 = create_shop(v3, 'Sole Runner Hub', 'hello@solerunner.com', 'Bangalore, KA')

    # 4. Products Data
    products_data = [
        # Equipment
        ('Power Rack - Elite', 'Heavy duty power rack for home gyms.', 45000, 5, c_equip, s1),
        ('Olympic Barbell 20kg', 'Hard chrome finish, 7ft long.', 12000, 15, c_equip, s1),
        ('Hex Dumbbells (Pair 10kg)', 'Rubber encased hex dumbbells.', 3500, 20, c_equip, s1),
        ('Incline Bench', 'Adjustable bench with high density foam.', 8500, 10, c_equip, s1),
        
        # Supplements
        ('Whey Gold Standard 5lb', 'Double rich chocolate whey protein.', 6500, 40, c_supps, s2),
        ('Pre-Workout Blast', '30 servings of high energy formula.', 2800, 25, c_supps, s2),
        ('Creatine Monohydrate 250g', 'Pure micronized creatine.', 1200, 60, c_supps, s2),
        ('Multi-Vitamin Complex', '60 tablets essential nutrients.', 950, 100, c_supps, s2),
        
        # Footwear
        ('Road Running Shoes V1', 'Lightweight and responsive padding.', 5500, 30, c_foot, s3),
        ('Gym Training Shoes', 'Stable base for heavy lifting.', 4200, 25, c_foot, s3),
        ('Trail Blazers', 'Rugged grip for outdoor running.', 6200, 15, c_foot, s3),
        
        # Apparel/Activewear
        ('Dri-Fit Training Tee', 'Moisture wicking fabric, slim fit.', 1100, 50, c_wear, s3),
        ('High-Waist Leggings', 'Squat proof, compression fit.', 1800, 40, c_wear, s3),
        ('Zip-Up Hoodie', 'Comfortable warm-up jacket.', 2400, 30, c_wear, s1),
        
        # Accessories
        ('Protein Shaker 700ml', 'Leak proof with mixing ball.', 450, 200, c_acc, s2),
        ('Lifting Straps (Pair)', 'Heavy duty cotton with padding.', 650, 100, c_acc, s1),
        ('Gym Gym Bag 40L', 'Separate shoe compartment.', 1800, 35, c_acc, s3),
    ]

    for name, desc, price, stock, cat, shop in products_data:
        Product.objects.get_or_create(
            p_name=name,
            description=desc,
            price=price,
            stock_availability=stock,
            category=cat,
            shop=shop,
            detail=f"Premium {name} from {shop.name}. High quality guaranteed."
        )

    print(f"Successfully added {len(products_data)} products across {Category.objects.count()} categories.")

if __name__ == '__main__':
    populate()
