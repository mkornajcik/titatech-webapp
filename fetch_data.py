import requests
from bs4 import BeautifulSoup
from app import app, db  # Import app and db from app.py
from models import Product, Category

# Initialize db with app
db.init_app(app)


def clean_price(price_str):
    try:
        # Remove non-breaking space and other non-numeric characters
        clean_str = price_str.replace('$', '').replace(',', '').replace('\xa0', '').split('–')[0].strip()
        return float(clean_str)
    except ValueError as e:
        print(f"Could not convert price: {price_str}. Error: {e}")
        return None


def scrape_cpus():
    with app.app_context():
        url = 'https://www.newegg.com/p/pl?N=100006676&cm_sp=shop-all-products-_-categroy-_-CPUs-Processors-top'
        scrape_category(url, 'CPUs')


def scrape_gpus():
    with app.app_context():
        url = 'https://www.newegg.com/p/pl?N=100006662&cm_sp=shop-all-products-_-categroy-_-GPUs-Video-Graphics-Devices-top'
        scrape_category(url, 'GPUs')


def scrape_category(url, category_name):
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    products = []
    for item in soup.select('.item-container'):
        name_tag = item.select_one('.item-title')
        price_tag = item.select_one('.price-current')
        image_tag = item.select_one('.item-img img')

        if name_tag and price_tag and image_tag:
            name = name_tag.text.strip()
            price = clean_price(price_tag.text.strip())
            if price is None:
                continue  # Skip products where price could not be determined
            image_url = image_tag['src']
            description = "No description available"

            product = Product(name=name, description=description, price=price, image_url=image_url)
            products.append(product)

    # Check if the category already exists in the database
    category = Category.query.filter_by(name=category_name).first()
    if not category:
        category = Category(name=category_name)
        db.session.add(category)
        db.session.commit()

    # Assign category_id to each product
    for product in products:
        product.category_id = category.id

    db.session.add_all(products)
    db.session.commit()


if __name__ == '__main__':
    scrape_cpus()
    scrape_gpus()
