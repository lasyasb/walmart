import os
import logging
import json
import re
import requests
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
from mistral_recipe_bot import get_mistral_recipes
from models import db, User, Product, Budget, CartItem, SharedCartSession, SharedCartItem, RecommendationLog

# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "cobudget-dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Database configuration
# Database configuration
database_url = os.environ.get("DATABASE_URL")

# ✅ Add SQLite fallback for environments like Colab
if not database_url:
    database_url = "sqlite:///walmart.db"

if database_url.startswith("postgres://"):
    # Fix for newer SQLAlchemy versions that require postgresql://
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


# Initialize database
db.init_app(app)

# Comprehensive product catalog with proper categories (prices in rupees)
SAMPLE_PRODUCTS = [
    # Fruits & Vegetables
    {
        "id":
        "FV001",
        "name":
        "Fresh Bananas",
        "price":
        45,
        "category":
        "Fruits & Vegetables",
        "tags": ["fruits", "fresh", "organic", "bananas"],
        "image_url":
        "https://www.bbassets.com/media/uploads/p/l/10000027_32-fresho-banana-robusta.jpg"
    },
    {
        "id": "FV002",
        "name": "Red Apples",
        "price": 180,
        "category": "Fruits & Vegetables",
        "tags": ["fruits", "apples", "fresh", "red"],
        "image_url": "https://www.bbassets.com/media/uploads/p/l/40033819_35-fresho-apple-shimla.jpg"
    },
    {
        "id": "FV003",
        "name": "Spinach Leaves",
        "price": 65,
        "category": "Fruits & Vegetables",
        "tags": ["vegetables", "greens", "spinach", "fresh"],
        "image_url": "https://sahajaaharam.com/files/Spinach.jpg"
    },
    {
        "id": "FV004",
        "name": "Carrots",
        "price": 55,
        "category": "Fruits & Vegetables",
        "tags": ["vegetables", "carrots", "fresh", "orange"],
        "image_url": "https://suttindseeds.in/wp-content/uploads/2023/02/CARROT-F-1-INDIAN-RED-2.jpg"
    
    },

    # Baby Food
    {
        "id": "BF001",
        "name": "Cerelac Baby Cereal",
        "price": 275,
        "category": "Baby Food",
        "tags": ["baby", "cereal", "nutrition", "cerelac"],
"image_url": "https://images.squarespace-cdn.com/content/v1/577d692d2e69cff0a51027a9/1472987610185-D0XJN161KLDZQR6N1WG1/Cerelac.JPG"
        },
    {
        "id": "BF002",
        "name": "Baby Diapers Size M",
        "price": 890,
        "category": "Baby Food",
        "tags": ["baby", "diapers", "hygiene", "medium"],
        "image_url": "https://gpsretail.in/wp-content/uploads/2024/11/teddy.jpg"
    },
    {
        "id": "BF003",
        "name": "Baby Wipes",
        "price": 145,
        "category": "Baby Food",
        "tags": ["baby", "wipes", "gentle", "cleaning"],
        "image_url": "https://www.healthklin.com/image/cache/catalog/PRODUCTIMAGES/mee-mee-wipes-72-pcs-225x350.jpg"
    },

    # Breakfast & Sauces
    {
        "id": "BS001",
        "name": "Kellogg's Corn Flakes",
        "price": 285,
        "category": "Breakfast & Sauces",
        "tags": ["cereal", "breakfast", "kelloggs", "cornflakes"],
        "image_url": "https://nagabazaar.com/cdn/shop/files/Kelloggs-Corn-Flakes-with-Real-Strawberry-Puree-300g.jpg"
    },
    {
        "id": "BS002",
        "name": "Maggi Tomato Ketchup",
        "price": 125,
        "category": "Breakfast & Sauces",
        "tags": ["sauce", "ketchup", "maggi", "tomato"],
        "image_url": "https://www.onionz.in/uploads/items/655de0b0c2d11c1df7f500c74b2a706e.jpg"
    },
    {
        "id": "BS003",
        "name": "Kissan Mixed Fruit Jam",
        "price": 165,
        "category": "Breakfast & Sauces",
        "tags": ["jam", "fruit", "spread", "kissan"],
        "image_url": "https://m.media-amazon.com/images/I/81QlwJRj53L.jpg"
    },

    # Cleaning Essentials
    {
        "id": "CE001",
        "name": "Surf Excel Detergent",
        "price": 345,
        "category": "Cleaning Essentials",
        "tags": ["detergent", "washing", "clothes", "surf"],
        "image_url": "https://cdn.grofers.com/da/cms-assets/cms/product/42ea51e6-8154-4bb0-9d29-18cc53896ecb.jpg"
    },
    {
        "id": "CE002",
        "name": "Lizol Floor Cleaner",
        "price": 185,
        "category": "Cleaning Essentials",
        "tags": ["cleaner", "floor", "disinfectant", "lizol"],
        "image_url": "https://gharstuff.com/wp-content/uploads/2020/08/Lizol-Floral-Floor-Cleaner-500ml.jpg"
    },
    {
        "id": "CE003",
        "name": "Vim Dishwash Liquid",
        "price": 95,
        "category": "Cleaning Essentials",
        "tags": ["dishwash", "liquid", "cleaning", "vim"],
        "image_url": "https://www.bbassets.com/media/uploads/p/l/900459772_4-vim-dishwash-liquid-gel.jpg"
    },

    # Atta, Rice, Oil & Dals
    {
        "id": "AR001",
        "name": "Aashirvaad Whole Wheat Atta",
        "price": 485,
        "category": "Atta, Rice, Oil & Dals",
        "tags": ["atta", "wheat", "flour", "aashirvaad"],
        "image_url": "https://www.bbassets.com/media/uploads/p/l/126903_12-aashirvaad-atta-whole-wheat.jpg"
    },
    {
        "id": "AR002",
        "name": "Basmati Rice 5kg",
        "price": 725,
        "category": "Atta, Rice, Oil & Dals",
        "tags": ["rice", "basmati", "grain", "cooking"],
        "image_url": "https://bf1af2.akinoncloudcdn.com/products/2024/09/09/71598/8ad31a32-4715-4142-8f62-2a6c0d714f50.jpg"
    },
    {
        "id": "AR003",
        "name": "Fortune Sunflower Oil",
        "price": 650,
        "category": "Atta, Rice, Oil & Dals",
        "tags": ["oil", "cooking", "sunflower", "fortune"],
        "image_url": "https://m.media-amazon.com/images/I/81FbVYZJYyL.jpg"
    },
    {
        "id": "AR004",
        "name": "Toor Dal",
        "price": 185,
        "category": "Atta, Rice, Oil & Dals",
        "tags": ["dal", "lentils", "protein", "toor"],
        "image_url": "https://dhatuorganics.com/wp-content/uploads/2025/01/Organic-Toor-Dal-front.jpg"
    },

    # Dairy, Bread & Eggs
    {
        "id": "DB001",
        "name": "Amul Fresh Milk",
        "price": 65,
        "category": "Dairy, Bread & Eggs",
        "tags": ["milk", "dairy", "fresh", "amul"],
        "image_url": "https://gharstuff.com/wp-content/uploads/2019/03/Amul-Gold-Milk-500ml.jpg"
    },
    {
        "id": "DB002",
        "name": "Britannia Bread",
        "price": 35,
        "category": "Dairy, Bread & Eggs",
        "tags": ["bread", "loaf", "britannia", "wheat"],
        "image_url": "https://cdn.grofers.com/da/cms-assets/cms/product/8622bfed-5e2d-415d-8a85-99c5fb7bac04.jpg"
    },
    {
        "id": "DB003",
        "name": "Farm Fresh Eggs",
        "price": 125,
        "category": "Dairy, Bread & Eggs",
        "tags": ["eggs", "protein", "fresh", "dozen"],
        "image_url":  "https://shop.purityprayag.com/cdn/shop/products/HitaFarmsOrganic-6-Eggs-F.jpg"
    },

    # Tea, Coffee & More
    {
        "id": "TC001",
        "name": "Tata Tea Gold",
        "price": 425,
        "category": "Tea, Coffee & More",
        "tags": ["tea", "tata", "premium", "beverage"],
        "image_url": "https://mcprod.spencers.in/media/catalog/product/1/0/1008950_4.jpg"
    },
    {
        "id": "TC002",
        "name": "Nescafe Instant Coffee",
        "price": 285,
        "category": "Tea, Coffee & More",
        "tags": ["coffee", "instant", "nescafe", "beverage"],
        "image_url":  "https://essentials.my/wp-content/uploads/2021/08/nescafe-gold-soluble-coffee-100g-min-1.jpg"
    },


    # Masala & Dry Fruits
    {
        "id": "MD001",
        "name": "MDH Garam Masala",
        "price": 85,
        "category": "Masala & Dry Fruits",
        "tags": ["spices", "masala", "cooking", "mdh"],
        "image_url": "https://kohinoorfoods.ca/cdn/shop/products/MDH_garam_masala.jpg"
    },
    {
        "id": "MD002",
        "name": "Almonds 250g",
        "price": 485,
        "category": "Masala & Dry Fruits",
        "tags": ["nuts", "almonds", "dry fruits", "healthy"],
        "image_url": "https://www.suvidhasupermart.com/uploads/suvidha-supermart/products/nutraj-california-almonds-250g-441455_l.jpg"
    },
    {
        "id": "MD003",
        "name": "Cashews 200g",
        "price": 565,
        "category": "Masala & Dry Fruits",
        "tags": ["nuts", "cashews", "dry fruits", "premium"],
        "image_url": "https://cdn.grofers.com/app/images/products/sliding_image/527969a.jpg"
    },

    # Cold Drinks & Juices
    {
        "id": "CD001",
        "name": "Coca Cola 1.25L",
        "price": 65,
        "category": "Cold Drinks & Juices",
        "tags": ["cola", "soft drink", "beverage", "coca"],
        "image_url": "https://5.imimg.com/data5/QA/WB/WF/SELLER-14933844/coca-cola-cold-drink-500x500.jpg"
    },
    {
        "id": "CD002",
        "name": "Real Orange Juice",
        "price": 125,
        "category": "Cold Drinks & Juices",
        "tags": ["juice", "orange", "real", "fresh"],
        "image_url": "https://m.media-amazon.com/images/I/61lYCT3C-7L.jpg"
    },

    # Biscuits
    {
        "id": "BI001",
        "name": "Parle-G Biscuits",
        "price": 25,
        "category": "Biscuits",
        "tags": ["biscuits", "parle", "glucose", "snack"],
        "image_url": "https://img.clevup.in/277874/SKU-3231_0-1742396696089.jpg"
    },
    {
        "id": "BI002",
        "name": "Oreo Cookies",
        "price": 55,
        "category": "Biscuits",
        "tags": ["cookies", "oreo", "chocolate", "cream"],
        "image_url": "https://m.media-amazon.com/images/I/51WQR3qg9vL.jpg"
    },

    # Sweet Cravings
    {
        "id": "SC001",
        "name": "Cadbury Dairy Milk",
        "price": 85,
        "category": "Sweet Cravings",
        "tags": ["chocolate", "cadbury", "sweet", "dairy milk"],
        "image_url": "https://springs.com.pk/cdn/shop/files/CDM-90G.jpg"
    },
    {
        "id": "SC002",
        "name": "Haldiram's Gulab Jamun",
        "price": 165,
        "category": "Sweet Cravings",
        "tags": ["sweets", "gulab jamun", "haldirams", "dessert"],
        "image_url": "https://assets.giftalove.com/resources/common/giftimages/largeimage/haldiram-gulab-jamun.jpg"
    },

    # Munchies
    {
        "id": "MU001",
        "name": "Lay's Potato Chips",
        "price": 25,
        "category": "Munchies",
        "tags": ["chips", "snacks", "lays", "potato"],
        "image_url": "https://www.quickpantry.in/cdn/shop/products/lay-s-chile-limon-potato-chips-32-g-quick-pantry.jpg"
    },
    {
        "id": "MU002",
        "name": "Kurkure Masala Munch",
        "price": 20,
        "category": "Munchies",
        "tags": ["snacks", "kurkure", "spicy", "munch"],
        "image_url": "https://aamaderbazar.com/wp-content/uploads/2024/03/kurkure-masala-munch-chips-40-gm.jpg"
    },


    # Makeup & Beauty
    {
        "id": "MB001",
        "name": "Lakme Foundation",
        "price": 565,
        "category": "Makeup & Beauty",
        "tags": ["makeup", "foundation", "lakme", "beauty"],
        "image_url": "https://www.lakmeindia.com/cdn/shop/files/24135_S1-8901030995255_800x.jpg"
    },
    {
        "id": "MB002",
        "name": "Himalaya Face Wash",
        "price": 125,
        "category": "Makeup & Beauty",
        "tags": ["skincare", "face wash", "himalaya", "natural"],
        "image_url": "https://5.imimg.com/data5/SELLER/Default/2020/12/MS/LV/GZ/120430256/himalaya-face-wash-500x500.jpg"
    },

    # Hygiene & Grooming
    {
        "id": "HG001",
        "name": "Colgate Toothpaste",
        "price": 85,
        "category": "Hygiene & Grooming",
        "tags": ["toothpaste", "dental", "colgate", "oral care"],
        "image_url":  "https://www.sabziadda.com/wp-content/uploads/2021/02/Colgate-Maxfresh-Spicy-Fresh-Toothpaste.jpg"
    },
    {
        "id": "HG002",
        "name": "Head & Shoulders Shampoo",
        "price": 265,
        "category": "Hygiene & Grooming",
        "tags": ["shampoo", "hair care", "head shoulders", "dandruff"],
        "image_url":  "https://5.imimg.com/data5/SELLER/Default/2022/1/TD/AS/SE/6235227/head-and-shoulders-hair-shampoo.jpg"
    },


    # Frozen Food & Ice Creams
    {
        "id": "FF001",
        "name": "Amul Ice Cream",
        "price": 185,
        "category": "Frozen Food & Ice Creams",
        "tags": ["ice cream", "frozen", "amul", "dessert"],
        "image_url": "https://5.imimg.com/data5/OW/WE/MY-30494656/amul-realmilk-ice-cream.jpg"
    },
    {
        "id": "FF002",
        "name": "McCain Fries",
        "price": 225,
        "category": "Frozen Food & Ice Creams",
        "tags": ["frozen", "fries", "mccain", "potato"],
        "image_url": "https://nlmaconline.com/cdn/shop/products/MCCAINCajunFront.jpg"
    },

    # Meats, Fish & Eggs
    {
        "id": "MF001",
        "name": "Fresh Chicken 1kg",
        "price": 285,
        "category": "Meats, Fish & Eggs",
        "tags": ["chicken", "fresh", "meat", "protein"],
        "image_url": "https://dailygroceryshop.com/wp-content/uploads/2020/05/Chicken-curry-dailygroceryshop.jpg"
    },
    {
        "id": "MF002",
        "name": "Fish Fillets",
        "price": 385,
        "category": "Meats, Fish & Eggs",
        "tags": ["fish", "seafood", "fillets", "protein"],
        "image_url": "https://fooppers.in/wp-content/uploads/2021/05/Basa-Fish-Fillets-Online-450x450.jpg"
    },

    # Bath & Body
    {
        "id": "BB001",
        "name": "Dove Soap",
        "price": 65,
        "category": "Bath & Body",
        "tags": ["soap", "bath", "dove", "moisturizing"],
        "image_url": "https://petracarestore.com/wp-content/uploads/2023/11/petracare-image-264.jpg"
    },
    
    {
        "id": "BB002",
        "name": "Nivea Body Lotion",
        "price": 185,
        "category": "Bath & Body",
        "tags": ["lotion", "body care", "nivea", "moisturizer"],
        "image_url":  "https://5.imimg.com/data5/EH/DU/SN/SELLER-100106295/body-lotion-500x500.jpg"
    },

    # Health & Baby Care
    {
        "id": "HB001",
        "name": "Vicks VapoRub",
        "price": 125,
        "category": "Health & Baby Care",
        "tags": ["health", "vicks", "cold relief", "balm"],
        "image_url": "https://online-pharmacy4u.co.uk/cdn/shop/products/vicks_vaporub_1_1.jpg"
    },
    {
        "id": "HB002",
        "name": "Dettol Antiseptic",
        "price": 145,
        "category": "Health & Baby Care",
        "tags": ["antiseptic", "dettol", "disinfectant", "health"],
        "image_url": "https://rapidtestkit.com.my/wp-content/uploads/2022/02/dettol-antiseptic-germicide-liquid-500ml.jpeg"
    },

    # Home Needs
    {
        "id": "HN001",
        "name": "Philips LED Bulb",
        "price": 285,
        "category": "Home Needs",
        "tags": ["bulb", "led", "philips", "lighting"],
        "image_url": "https://5.imimg.com/data5/SELLER/Default/2024/3/404191839/TA/QY/MH/107262425/philips-steller-light-500x500.jpg"
    },
    {
        "id": "HN002",
        "name": "Godrej Air Freshener",
        "price": 125,
        "category": "Home Needs",
        "tags": ["air freshener", "godrej", "fragrance", "home"],
        "image_url": "https://www.urbangroc.com/wp-content/uploads/2022/05/godrej-aer-cool-freshner.jpg"
    },

    # Electricals & Accessories
    {
        "id": "EA001",
        "name": "Samsung Phone Charger",
        "price": 785,
        "category": "Electricals & Accessories",
        "tags": ["charger", "samsung", "phone", "electronics"],
        "image_url": "https://image-us.samsung.com/SamsungUS/home/mobile/mobile-accessories/pdp/ep-ta20jweusta/features/Flexibility_121316.jpg"
    },
    {
        "id": "EA002",
        "name": "Boat Earphones",
        "price": 1285,
        "category": "Electricals & Accessories",
        "tags": ["earphones", "boat", "audio", "wireless"],
        "image_url": "https://m.media-amazon.com/images/I/51JM8TpHVSL.jpg"
    }
]


@app.route('/')
def index():
    """Main application route"""
    return render_template(
        'index.html',
        firebase_api_key=os.environ.get('FIREBASE_API_KEY'),
        firebase_project_id=os.environ.get('FIREBASE_PROJECT_ID'),
        firebase_app_id=os.environ.get('FIREBASE_APP_ID'))


@app.route('/api/recommend', methods=['POST'])
def recommend_products():
    """
    Smart recommendation endpoint that filters products based on user prompt and budget
    """
    try:
        data = request.get_json()
        prompt = data.get('prompt', '').lower().strip()
        budget = float(data.get('budget', 0))

        if not prompt:
            return jsonify({"error": "Prompt is required"}), 400

        # Get products from database
        products = Product.query.filter_by(in_stock=True).all()
        recommended = []

        # Split prompt into keywords for better matching
        keywords = [
            word.strip() for word in prompt.split() if len(word.strip()) > 2
        ]

        for product in products:
            # Parse tags from JSON
            tags = json.loads(product.tags) if product.tags else []

            # Calculate match score
            score = 0
            product_text = f"{product.name.lower()} {product.category.lower()} {' '.join(tags).lower()}"

            # Exact phrase match gets highest score
            if prompt in product_text:
                score += 10

            # Keyword matching
            for keyword in keywords:
                if keyword in product.name.lower():
                    score += 5
                elif keyword in product.category.lower():
                    score += 3
                elif any(keyword in tag.lower() for tag in tags):
                    score += 2

            # Budget filter
            if budget > 0 and float(product.price) > budget:
                continue

            if score > 0:
                recommended.append({
                    'id': product.id,
                    'name': product.name,
                    'price': float(product.price),
                    'category': product.category,
                    'tags': tags,
                    'description': product.description,
                    'image_url': product.image_url,
                    'in_stock': product.in_stock,
                    'match_score': score
                })

        # Sort by match score (descending) then by price (ascending)
        recommended.sort(key=lambda x: (-x['match_score'], x['price']))
        recommended = recommended[:12]  # Limit to top 12 results

        return jsonify({
            "success": True,
            "products": recommended,
            "count": len(recommended),
            "query": prompt,
            "budget": budget
        })

    except Exception as e:
        logging.error(f"Error in recommend_products: {str(e)}")
        return jsonify({"error": "Failed to get recommendations"}), 500


@app.route('/api/products', methods=['GET'])
def get_products():
    """Get all available products"""
    try:
        # Get products from database
        products = Product.query.all()

        # Convert to list of dictionaries
        products_list = []
        for product in products:
            products_list.append({
                'id':
                product.id,
                'name':
                product.name,
                'price':
                float(product.price),
                'category':
                product.category,
                'tags':
                json.loads(product.tags) if product.tags else [],
                'description':
                product.description,
                'image_url':
                product.image_url,
                'in_stock':
                product.in_stock
            })

        return jsonify({'success': True, 'products': products_list})

    except Exception as e:
        logging.error(f"Error in get_products: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/walmart-image')
def walmart_image():
    """Get product image from Walmart website"""
    query = request.args.get("q")
    if not query:
        return jsonify({"error": "Missing query"}), 400

    try:
        # Use a search engine approach for better image results
        search_url = f"https://www.google.com/search?q={query}+walmart&tbm=isch"
        headers = {
            "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        response = requests.get(search_url, headers=headers, timeout=10)
        html = response.text

        # Look for image URLs in the search results
        image_patterns = [
            r'https://i5\.walmartimages\.com/[^"&]+',
            r'https://i5\.wimg\.com/[^"&]+',
            r'https://walmart\.com/[^"]*\.jpg',
            r'https://walmart\.com/[^"]*\.jpeg',
            r'https://walmart\.com/[^"]*\.png'
        ]

        for pattern in image_patterns:
            matches = re.findall(pattern, html)
            if matches:
                # Filter out very small images and select the first good one
                for match in matches[:3]:  # Try first 3 matches
                    if len(match) > 50:  # Basic quality filter
                        logging.info(f"Found image for {query}: {match}")
                        return jsonify({"image": match})

        # If no images found, try a simple product search
        simple_search = f"https://www.walmart.com/search?q={query.split()[0]}"
        response = requests.get(simple_search, headers=headers, timeout=5)

        walmart_patterns = [
            r'"image":\s*"(https://i5\.walmartimages\.com/[^"]+)"',
            r'"thumbnail":\s*"(https://i5\.walmartimages\.com/[^"]+)"'
        ]

        for pattern in walmart_patterns:
            matches = re.findall(pattern, response.text)
            if matches:
                image_url = matches[0].replace('\\/', '/')
                logging.info(f"Found Walmart image for {query}: {image_url}")
                return jsonify({"image": image_url})

        logging.warning(f"No image found for {query}")
        return jsonify({"image": ""})

    except Exception as e:
        logging.error(f"Error fetching image for {query}: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/shared-cart/create', methods=['POST'])
def create_shared_cart():
    """Create a new shared cart session"""
    try:
        data = request.get_json()
        cart_name = data.get('name', 'Shared Cart')
        user_email = data.get('user_email', 'anonymous@example.com')
        user_uid = data.get('user_uid', 'anonymous')

        # For now, use a simple approach without strict user validation
        # This allows the shared cart to work immediately
        user_id = 1  # Default user ID for shared cart functionality

        # Generate unique 8-character ID
        import string
        import random
        cart_id = ''.join(
            random.choices(string.ascii_uppercase + string.digits, k=8))

        # Check if ID already exists (very unlikely but good practice)
        while SharedCartSession.query.get(cart_id):
            cart_id = ''.join(
                random.choices(string.ascii_uppercase + string.digits, k=8))

        # Create new session
        session = SharedCartSession()
        session.id = cart_id
        session.name = cart_name
        session.created_by_user_id = user_id

        db.session.add(session)
        db.session.commit()

        return jsonify({
            "success": True,
            "session_id": cart_id,
            "name": cart_name
        })

    except Exception as e:
        logging.error(f"Error creating shared cart: {str(e)}")
        return jsonify({"error": "Failed to create shared cart"}), 500


@app.route('/api/shared-cart/join/<session_id>')
def join_shared_cart(session_id):
    """Join an existing shared cart session"""
    try:
        session = SharedCartSession.query.get(session_id)
        if not session or not session.is_active:
            return jsonify({"error": "Cart not found or inactive"}), 404

        return jsonify({
            "success": True,
            "session": {
                "id": session.id,
                "name": session.name,
                "created_at": session.created_at.isoformat()
            }
        })

    except Exception as e:
        logging.error(f"Error joining shared cart: {str(e)}")
        return jsonify({"error": "Failed to join shared cart"}), 500


@app.route('/api/shared-cart/<session_id>/items')
def get_shared_cart_items(session_id):
    """Get all items in a shared cart session"""
    try:
        session = SharedCartSession.query.get(session_id)
        if not session:
            return jsonify({"error": "Cart not found"}), 404

        items_data = []
        user_totals = {}

        for item in session.items:
            # Get product from database
            product_db = Product.query.get(item.product_id)
            if not product_db:
                continue

            # Get user info
            user = User.query.get(item.added_by_user_id)
            user_email = user.email if user else "unknown@example.com"

            product_data = {
                "id": product_db.id,
                "name": product_db.name,
                "price": float(product_db.price),
                "category": product_db.category,
                "tags": json.loads(product_db.tags) if product_db.tags else []
            }

            item_data = {
                "id": item.id,
                "product": product_data,
                "added_by": user_email,
                "quantity": item.quantity,
                "added_at": item.added_at.isoformat()
            }
            items_data.append(item_data)

            # Calculate user totals
            if user_email not in user_totals:
                user_totals[user_email] = 0
            user_totals[user_email] += product_data['price'] * item.quantity

        grand_total = sum(user_totals.values())

        return jsonify({
            "success": True,
            "session": {
                "id": session.id,
                "name": session.name
            },
            "items": items_data,
            "user_totals": user_totals,
            "grand_total": grand_total
        })

    except Exception as e:
        logging.error(f"Error getting shared cart items: {str(e)}")
        return jsonify({"error": "Failed to get shared cart items"}), 500


@app.route('/api/shared-cart/<session_id>/add', methods=['POST'])
def add_to_shared_cart(session_id):
    """Add item to shared cart session"""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        user_email = data.get('user_email', 'anonymous@example.com')

        session = SharedCartSession.query.get(session_id)
        if not session:
            return jsonify({"error": "Cart not found"}), 404

        # Create new shared cart item
        item = SharedCartItem()
        item.session_id = session_id
        item.product_id = product_id
        item.added_by_user_id = 1  # Placeholder
        item.quantity = 1

        db.session.add(item)
        db.session.commit()

        return jsonify({"success": True, "item_id": item.id})

    except Exception as e:
        logging.error(f"Error adding to shared cart: {str(e)}")
        return jsonify({"error": "Failed to add to shared cart"}), 500


# Initialize database tables and seed data
def init_database():
    """Initialize database tables and populate with sample products"""
    with app.app_context():
        # Create all tables
        db.create_all()

        # Check if products already exist
        if Product.query.count() == 0:
            # Seed products from SAMPLE_PRODUCTS
            for product_data in SAMPLE_PRODUCTS:
                product = Product()
                product.id = product_data['id']
                product.name = product_data['name']
                product.price = product_data['price']
                product.category = product_data['category']
                product.tags = json.dumps(product_data['tags'])
                product.description = f"Quality {product_data['name']} from Walmart"
                product.image_url = product_data.get('image_url')
                product.in_stock = True
                db.session.add(product)

            db.session.commit()
            logging.info(
                f"Seeded {len(SAMPLE_PRODUCTS)} products into database")


@app.route('/api/init_database', methods=['POST'])
def init_database_route():
    """Initialize database with sample products"""
    try:
        init_database()
        return jsonify({"success": True, "message": "Database initialized successfully"})
    except Exception as e:
        print(f"Error initializing database: {e}")
        return jsonify({"error": str(e)}), 500


# Initialize database when app starts
init_database()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

# Sample product list used for Smart Search and NutriBasket
sample_products = [
    {"id": 1, "name": "Basmati Rice", "category": "Grocery", "price": 120, "tags": ["biryani", "rice"]},
    {"id": 2, "name": "Chicken Masala", "category": "Spices", "price": 75, "tags": ["biryani", "spices"]},
    {"id": 3, "name": "Sweets Box", "category": "Snacks", "price": 300, "tags": ["wedding", "sweets"]},
    {"id": 4, "name": "Rose Bouquet", "category": "Flowers", "price": 200, "tags": ["wedding", "flowers"]},
    {"id": 5, "name": "Avocados", "category": "Fruits", "price": 250, "tags": ["keto", "high protein"]},
    {"id": 6, "name": "Spinach Leaves", "category": "Vegetables", "price": 55, "tags": ["low sodium", "keto", "high protein"]},
    {"id": 7, "name": "Sugar-Free Biscuits", "category": "Snacks", "price": 85, "tags": ["low sugar"]},
    {"id": 8, "name": "Cheddar Cheese", "category": "Dairy", "price": 190, "tags": ["keto", "high protein"]}
]


@app.route("/recommend-smart", methods=["POST"])
def recommend_smart():
    data = request.get_json()
    keyword = data.get("keyword", "").lower()

    context_map = {
        "biryani": ["rice", "spices", "chicken", "saffron", "yogurt"],
        "wedding": ["sweets", "decorations", "flowers", "snacks", "juice"],
        "keto": ["almonds", "avocados", "eggs", "cheese", "spinach"],
        "party": ["chips", "soda", "cake", "cups", "snacks"]
    }

    relevant_tags = context_map.get(keyword, [])
    if not relevant_tags:
        return jsonify([])

    matching_products = [p for p in sample_products if "tags" in p and any(tag.lower() in p["tags"] for tag in relevant_tags)]
    return jsonify(matching_products)


@app.route("/recommend-nutrition", methods=["POST"])
def recommend_nutrition():
    data = request.get_json()
    preferences = data.get("preferences", [])
    matching_products = [p for p in sample_products if "tags" in p and any(tag.lower() in p["tags"] for tag in preferences)]
    return jsonify(matching_products)



@app.route('/api/recipe-bot', methods=['POST'])
def recipe_bot():
    try:
        data = request.get_json()
        print("Received data:", data)
        prompt = data.get("prompt", "").strip()
        if not prompt:
            print("Empty prompt")
            return jsonify({"error": "Prompt required"}), 400

        mistral_key = os.getenv("MISTRAL_API_KEY", "1I0BiIiBuxpv8xXlposfEkrzx93rsZWO")
        if not mistral_key:
            print("Missing MISTRAL_API_KEY in env")
            return jsonify({"error": "Mistral API key missing"}), 500

        result = get_mistral_recipes(prompt, mistral_key)
        print("Mistral API responded with:", result)
        return jsonify({"success": True, "recipe": result})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
