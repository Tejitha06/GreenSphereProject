"""
Nursery Orders API Routes
Handles saving and retrieving user's nursery plant orders
"""

from flask import Blueprint, request, jsonify
import logging
from datetime import datetime, timezone
from models import db, NurseryOrder, OrderItem, User

nursery_orders_bp = Blueprint('nursery_orders', __name__)
logger = logging.getLogger(__name__)


@nursery_orders_bp.route('/save', methods=['POST'])
def save_nursery_order():
    """
    Save a new nursery order to the database
    
    Request JSON:
    {
        "user_id": int,
        "order_id": string,
        "nursery": {
            "name": string,
            "area": string,
            "city": string,
            "state": string,
            "distance": string
        },
        "items": [
            {"name": string, "quantity": int, "unit_price": float}
        ],
        "total_plants": int,
        "total_amount": float,
        "payment_status": string,
        "delivery_address": string,
        "order_notes": string
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'user_id' not in data:
            return jsonify({'error': 'user_id is required', 'status': 'error'}), 400
        
        if 'order_id' not in data:
            return jsonify({'error': 'order_id is required', 'status': 'error'}), 400
        
        if 'items' not in data or not isinstance(data['items'], list):
            return jsonify({'error': 'items array is required', 'status': 'error'}), 400
        
        # Check if user exists
        user_id = data['user_id']
        user = User.query.get(user_id)
        if not user:
            logger.warning(f'Attempt to save order for non-existent user: {user_id}')
            return jsonify({'error': 'User not found', 'status': 'error'}), 404
        
        # Check if order already exists
        existing_order = NurseryOrder.query.filter_by(order_id=data['order_id']).first()
        if existing_order:
            logger.warning(f'Attempt to save duplicate order: {data["order_id"]}')
            return jsonify({'error': 'Order already exists', 'status': 'error'}), 409
        
        # Create new order
        nursery_info = data.get('nursery', {})
        
        new_order = NurseryOrder(
            user_id=user_id,
            order_id=data['order_id'],
            nursery_name=nursery_info.get('name', 'Unknown Nursery'),
            nursery_area=nursery_info.get('area'),
            nursery_city=nursery_info.get('city'),
            nursery_state=nursery_info.get('state'),
            nursery_distance=nursery_info.get('distance'),
            total_plants=data.get('total_plants', 0),
            total_amount=float(data.get('total_amount', 0)),
            payment_status=data.get('payment_status', 'pending'),
            order_status='placed',
            delivery_address=data.get('delivery_address'),
            order_notes=data.get('order_notes')
        )
        
        # Add order items
        for item in data['items']:
            if 'name' not in item or 'quantity' not in item or 'unit_price' not in item:
                return jsonify({'error': 'Each item must have name, quantity, and unit_price', 'status': 'error'}), 400
            
            total_price = float(item['unit_price']) * int(item['quantity'])
            
            order_item = OrderItem(
                plant_name=item['name'],
                quantity=int(item['quantity']),
                unit_price=float(item['unit_price']),
                total_price=total_price
            )
            new_order.order_items.append(order_item)
        
        # Save to database
        db.session.add(new_order)
        db.session.commit()
        
        logger.info(f'Order saved successfully: {data["order_id"]} for user {user_id}')
        
        return jsonify({
            'success': True,
            'message': 'Order saved successfully',
            'order': new_order.to_dict(),
            'status': 'success'
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error saving nursery order: {e}')
        return jsonify({
            'error': f'Error saving order: {str(e)}',
            'status': 'error'
        }), 500


@nursery_orders_bp.route('/user/<int:user_id>', methods=['GET'])
def get_user_orders(user_id):
    """
    Get all nursery orders for a specific user
    
    Query Parameters:
    - limit: Number of orders to return (default: 50)
    - offset: Number of orders to skip (default: 0)
    - status: Filter by order_status (optional)
    """
    try:
        # Check if user exists
        user = User.query.get(user_id)
        if not user:
            logger.warning(f'Attempt to fetch orders for non-existent user: {user_id}')
            return jsonify({'error': 'User not found', 'status': 'error'}), 404
        
        # Get query parameters
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        status_filter = request.args.get('status', None)
        
        # Build query
        query = NurseryOrder.query.filter_by(user_id=user_id)
        
        # Apply status filter if provided
        if status_filter:
            query = query.filter_by(order_status=status_filter)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination and sorting (newest first)
        orders = query.order_by(NurseryOrder.ordered_at.desc()).limit(limit).offset(offset).all()
        
        logger.info(f'Retrieved {len(orders)} orders for user {user_id}')
        
        return jsonify({
            'success': True,
            'data': [order.to_dict() for order in orders],
            'total': total_count,
            'count': len(orders),
            'limit': limit,
            'offset': offset,
            'status': 'success'
        }), 200
    
    except Exception as e:
        logger.error(f'Error fetching user orders: {e}')
        return jsonify({
            'error': f'Error fetching orders: {str(e)}',
            'status': 'error'
        }), 500


@nursery_orders_bp.route('/<int:order_id>', methods=['GET'])
def get_order_details(order_id):
    """
    Get details of a specific nursery order
    """
    try:
        order = NurseryOrder.query.get(order_id)
        
        if not order:
            logger.warning(f'Order not found: {order_id}')
            return jsonify({'error': 'Order not found', 'status': 'error'}), 404
        
        logger.info(f'Retrieved order details: {order.order_id}')
        
        return jsonify({
            'success': True,
            'data': order.to_dict(),
            'status': 'success'
        }), 200
    
    except Exception as e:
        logger.error(f'Error fetching order details: {e}')
        return jsonify({
            'error': f'Error fetching order: {str(e)}',
            'status': 'error'
        }), 500


@nursery_orders_bp.route('/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    """
    Update the status of an order
    
    Request JSON:
    {
        "order_status": "confirmed|delivered|cancelled",
        "payment_status": "paid|failed|refunded" (optional),
        "order_notes": "string" (optional)
    }
    """
    try:
        data = request.get_json()
        
        order = NurseryOrder.query.get(order_id)
        if not order:
            logger.warning(f'Attempt to update non-existent order: {order_id}')
            return jsonify({'error': 'Order not found', 'status': 'error'}), 404
        
        # Update order status if provided
        if 'order_status' in data:
            valid_statuses = ['placed', 'confirmed', 'delivered', 'cancelled']
            if data['order_status'] not in valid_statuses:
                return jsonify({'error': f'Invalid order_status. Must be one of: {", ".join(valid_statuses)}', 'status': 'error'}), 400
            order.order_status = data['order_status']
        
        # Update payment status if provided
        if 'payment_status' in data:
            valid_payment_statuses = ['pending', 'paid', 'failed', 'refunded']
            if data['payment_status'] not in valid_payment_statuses:
                return jsonify({'error': f'Invalid payment_status. Must be one of: {", ".join(valid_payment_statuses)}', 'status': 'error'}), 400
            order.payment_status = data['payment_status']
        
        # Update notes if provided
        if 'order_notes' in data:
            order.order_notes = data['order_notes']
        
        order.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        logger.info(f'Order status updated: {order.order_id}')
        
        return jsonify({
            'success': True,
            'message': 'Order status updated successfully',
            'data': order.to_dict(),
            'status': 'success'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error updating order status: {e}')
        return jsonify({
            'error': f'Error updating order: {str(e)}',
            'status': 'error'
        }), 500


@nursery_orders_bp.route('/<order_id>/cancel', methods=['POST'])
def cancel_order(order_id):
    """
    Cancel an order by its string order_id (e.g. ORD-2026-12345)
    or by its integer database id.
    """
    try:
        # Try string order_id first (e.g. "ORD-2026-12345")
        order = NurseryOrder.query.filter_by(order_id=order_id).first()

        # If not found by string, try integer primary key
        if not order:
            try:
                order = NurseryOrder.query.get(int(order_id))
            except (ValueError, TypeError):
                pass

        if not order:
            logger.warning(f'Cancel attempt for non-existent order: {order_id}')
            return jsonify({'success': False, 'message': 'Order not found'}), 404

        if order.order_status == 'cancelled':
            return jsonify({'success': False, 'message': 'Order is already cancelled'}), 400

        if order.order_status == 'delivered':
            return jsonify({'success': False, 'message': 'Delivered orders cannot be cancelled'}), 400

        order.order_status = 'cancelled'
        order.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        logger.info(f'Order cancelled: {order.order_id}')
        return jsonify({
            'success': True,
            'message': 'Order cancelled successfully',
            'data': order.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f'Error cancelling order {order_id}: {e}')
        return jsonify({'success': False, 'message': f'Error cancelling order: {str(e)}'}), 500


@nursery_orders_bp.route('/<int:order_id>/summary', methods=['GET'])
def get_order_summary(order_id):
    """
    Get a summary of a specific order (lightweight version)
    """
    try:
        order = NurseryOrder.query.get(order_id)
        
        if not order:
            logger.warning(f'Order not found for summary: {order_id}')
            return jsonify({'error': 'Order not found', 'status': 'error'}), 404
        
        summary = {
            'order_id': order.order_id,
            'nursery_name': order.nursery_name,
            'total_plants': order.total_plants,
            'total_amount': order.total_amount,
            'order_status': order.order_status,
            'payment_status': order.payment_status,
            'ordered_at': order.ordered_at.isoformat(),
            'item_count': len(order.order_items)
        }
        
        return jsonify({
            'success': True,
            'data': summary,
            'status': 'success'
        }), 200
    
    except Exception as e:
        logger.error(f'Error fetching order summary: {e}')
        return jsonify({
            'error': f'Error fetching order summary: {str(e)}',
            'status': 'error'
        }), 500
