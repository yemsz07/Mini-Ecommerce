"""
Business logic services following Django best practices.
Ang file na ito ang nagsisilbing 'utak' ng iyong app.
"""
from django.db import transaction
from django.contrib import messages
from .models import Product, Order, OrderItem
from .cart import Cart
from decimal import Decimal
import logging

# Logger - Ito ang 'CCTV' ng system mo, nagtatala ng mga mahahalagang pangyayari.
logger = logging.getLogger(__name__)


class CartService:
    
    @staticmethod
    def get_cart_count(request):
        total = 0
        cart = Cart(request)
        if cart.cart:
            for item in cart.cart.values():
                total = total + item['quantity']
        return total
    
    @staticmethod
    def add_to_cart(request, product, quantity=1):
        """Pagdagdag ng produkto sa cart na may validation"""
        cart = Cart(request)
        cart.add(product=product, quantity=quantity)
        return cart
    
    @staticmethod
    def get_cart_totals(request):
        """
        Calculate cart totals
        Returns: {
            'subtotal': Decimal,  # Total price of all items
            'total': Decimal,     # Same as subtotal
            'cart_items': list    # Formatted cart items
        }
        """

        cart = Cart(request)
        cart_items = []
        total_price = Decimal('0.00')
        
        for product_id, item in cart.cart.items():
            try:
                product = Product.objects.get(id=int(product_id))
                quantity = item['quantity']
                
                # Simple calculation: price × quantity
                item_total = product.price * quantity
                
                cart_items.append({
                    'product': product,
                    'quantity': quantity,
                    'unit_price': product.price.quantize(Decimal('0.01')),
                    'subtotal': item_total.quantize(Decimal('0.01'))
                })
                
                total_price += item_total
                
            except Product.DoesNotExist:
                # Remove invalid items from cart
                del cart.cart[product_id]
                continue
        
        return {
            'subtotal': total_price.quantize(Decimal('0.01')),
            'total': total_price.quantize(Decimal('0.01')),
            'cart_items': cart_items
        }




class OrderService:
    """Service para sa paggawa ng Order at pag-handle ng database records"""
    
    @staticmethod
    def validate_purchase(product, quantity):
        """Dito tinitingnan kung 'valid' o pwedeng ituloy ang pagbili"""
        errors = []
        
        # Check kung zero o negative ang quantity
        if quantity <= 0:
            errors.append("Invalid quantity.")
        
        # Check kung may sapat pang stock sa bodega (database)
        if product.stock < quantity:
            errors.append(f"Insufficient stock. Only {product.stock} units available.")
        
        return errors
    
    @staticmethod
    @transaction.atomic  # "All or Nothing" - Kapag nag-error sa dulo, babawiin lahat ng changes sa DB.
    def create_order(request, product, quantity):
        """Paggawa ng order at pagbabawas ng stock sa bodega"""
        
        # Row locking: Sinasabi sa DB na 'Akin muna itong row na to, wag niyo muna ipahiram sa iba'
        # Ito ang proteksyon laban sa sabay-sabay na pagbili (Race Condition).
        product = Product.objects.select_for_update().get(id=product.id)
        
        # Patakbuhin ang validation check bago magbawas ng stock
        errors = OrderService.validate_purchase(product, quantity)
        if errors:
            return None, errors
        
        # Pag-update ng stock: Bawasan ang imbentaryo
        old_stock = product.stock
        product.stock -= quantity
        product.save()
        
        # Paggawa ng main Order record (Ang Header ng Resibo)
        order = Order.objects.create(
            customer=request.user,
            status='Pending'
        )
        
        # Paggawa ng OrderItem record (Ang listahan ng binili sa loob ng resibo)
        order_item = OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity
        )
        
        # Itala sa logs (CCTV) para sa audit trail
        total_price = quantity * product.price
        logger.info(
            f"ORDER_CREATED: {order.id} | User: {request.user.username} | "
            f"Product: {product.name} | Qty: {quantity} | "
            f"Stock: {old_stock} → {product.stock} | Total: ₱{total_price:.2f}"
        )
        
        return order, []
    
    @staticmethod
    def clear_cart_item(request, product_id):
        """Tatanggalin ang item sa cart session kapag nabayaran na"""
        cart = Cart(request)
        product_id_str = str(product_id) # Session keys are usually strings
        if product_id_str in cart.cart:
            del cart.cart[product_id_str]
            cart.save()


class PurchaseService:
    """Ang 'Main Entrance' ng purchase flow. Ito ang tatawagin ng iyong View."""
    
    @staticmethod
    def process_purchase(request, product_id, quantity):
        """Buong proseso mula pagkuha ng product hanggang paglinis ng cart"""
        try:
            # Hanapin ang produkto, kung wala, automatic pupunta sa 'except' block
            product = Product.objects.get(id=product_id)
            
            # 1. Simulan ang paggawa ng order (Tatawag sa OrderService)
            order, errors = OrderService.create_order(request, product, quantity)
            
            # Kung may error sa stock o validation, ibalik agad sa user
            if errors:
                return None, errors
            
            # 2. Kapag success, linisin ang cart para sa item na nabili na
            OrderService.clear_cart_item(request, product_id)
            
            # 3. Kwentahin ang total para ipakita sa success page
            total_price = quantity * product.price
            
            return {
                'order': order,
                'product': product,
                'quantity': quantity,
                'total_price': total_price
            }, []
            
        except Product.DoesNotExist:
            return None, ["Product not found."]
        except ValueError:
            return None, ["Invalid quantity provided."]
        except Exception as e:
            # Kung may hindi inaasahang error (e.g. database down), i-log ito
            logger.error(f"Purchase error: {str(e)} | User: {request.user.id} | Product: {product_id}")
            return None, ["An error occurred during purchase. Please try again."]