from django.conf import settings
from .models import Product

class Cart:
    # constructor para sa cart
    def __init__(self, request):
        self.request = request
        self.session = request.session
        
        # get the cart from the session, if it doesn't exist, create an empty cart
        self.cart = self.session.get(settings.CART_SESSION_ID, {})
        
    def add(self, product, quantity=1, override_quantity=False):
        #  kino-convert nito sa String ang product.id dahil nagkakaroon ng error sa JSON kapag decimal ang gamit
        product_id = str(product.id)

        # ito yung nagsasabi kay Django na kapag ang product_id ay wala sa cart gumawa ng new entry/new table at ipakita ang quantity at price
        if product_id not in self.cart:
            self.cart[product_id] = {'quantity': 0, 'price': str(product.price)}
        
        # ito naman ang nagbabago or update sa cart na kapag ang product ay dinagdagan automatic itong mag update sa cart 
        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        
        # once nag add automatic mag update ng quantity + 1
        else:
            self.cart[product_id]['quantity'] += quantity
        
        # temporary save the cart
        self.save()
        
    def save(self):
        # save the cart
        self.session[settings.CART_SESSION_ID] = self.cart
        # mark the session as "modified" to make sure it gets saved
        self.session.modified = True
        
    def clear(self):
        # clear the cart
        self.cart = {}
        self.save()
        
    def remove(self, product):
        # remove the product from the cart
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()
            
    def __iter__(self):
        # ito yung susi para makuha ang mga product_id na inilagay mo sa session/cart
        product_ids = self.cart.keys()

        # kinukuha nito yung mga details sa database Product kung saan naka partner ang mga product_ids na ibinigay mo sa session/cart
        products = Product.objects.filter(id__in=product_ids)
        
        # dito pinagsasama ang data sa session/cart at data sa database Product
        for product in products:
            self.cart[str(product.id)]['product'] = product
            
        # dito pinagsasama ang total price at quantity ng item
        for item in self.cart.values():
            item['total_price'] = float(item['price']) * item['quantity']
            yield item

    # dito binibilang kung ilan yung items at kung ilan din ang quantity ng bawat item sa cart     
    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())
        
    # dito binibilang ang total price ng lahat ng item sa cart     
    def get_total_price(self):
        return sum(float(item['price']) * item['quantity'] for item in self.cart.values())