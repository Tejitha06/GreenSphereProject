# Profile & Orders - Testing Guide

## Quick Test Steps

### Prerequisites
- Flask backend running (`python app.py` or `python run.py`)
- User logged in (stored in localStorage as `currentUser`)
- Database initialized

### Test 1: Access Profile Page
1. Go to any page (e.g., dashboard.html)
2. Click **"Profile"** in the navigation
3. ✅ You should see your profile information loaded
4. ✅ User name, email, and details should display

### Test 2: View Orders (Empty State)
1. On Profile page, check the **"My Orders"** tab
2. If no orders exist, you should see:
   - 🛒 Empty state icon
   - "No Orders Yet" message
   - "Browse Nursery" button
3. ✅ Should display gracefully with no errors

### Test 3: Place an Order
1. Go to **Nurseries** page (nursery.html)
2. Click on any nursery → "View Plants"
3. Add plants to cart (click plant cards)
4. Click **"Proceed to Checkout"**
5. Review cart and click **"Complete Purchase"**
6. ✅ Should see confirmation

### Test 4: View Saved Order
1. Go to **Profile** page
2. Check **"My Orders"** tab
3. ✅ Your order should appear as a card showing:
   - Order ID (ORD-2026-xxxxx)
   - Nursery name
   - Number of items
   - Total amount
   - Order status (should be "placed")
   - Payment status (should be "pending")

### Test 5: View Order Details
1. On the order card, click **"View Details"**
2. Modal should open showing:
   - ✅ Order Information section (ID, date, status)
   - ✅ Nursery Details section
   - ✅ Items Ordered section (plant names, quantities, prices)
   - ✅ Order Summary section (total plants, total amount)
3. Click **"X"** to close modal

### Test 6: Navigation Access
Verify Profile link works from all pages:
- ✅ Dashboard.html - "View Orders" button
- ✅ Dashboard.html - Profile icon sidebar
- ✅ identify.html - Profile link in navbar
- ✅ disease.html - Profile link in navbar
- ✅ nursery.html - Profile link in navbar
- ✅ my-garden.html - Profile link in navbar
- ✅ nursery-order.html - Profile link in navbar

### Test 7: User Logout
1. On Profile page, scroll down
2. Click **"Logout"** button
3. ✅ Should redirect to registration page
4. ✅ localStorage should be cleared

### Test 8: API Verification (Advanced)
Open browser Console (F12) and test:

```javascript
// Get current user ID
const user = JSON.parse(localStorage.getItem('currentUser'));
console.log(user.id);

// Fetch user's orders
fetch(`/api/nursery/orders/user/${user.id}`)
  .then(r => r.json())
  .then(data => console.log(data));
  
// Expected response:
{
  "success": true,
  "data": [
    {
      "id": 1,
      "order_id": "ORD-2026-12345",
      "nursery_name": "Green Valley",
      "total_plants": 5,
      "total_amount": 1500,
      "order_status": "placed",
      "payment_status": "pending",
      "items": [...]
    }
  ],
  "status": "success"
}
```

## Expected Results Summary

| Test | Expected Outcome | Status |
|------|------------------|--------|
| Access Profile | Page loads with user info | ✅ |
| Empty Orders | Shows "No Orders Yet" message | ✅ |
| Place Order | Order saved to database | ✅ |
| View Orders | Orders display as cards | ✅ |
| View Details | Modal shows all info | ✅ |
| Navigation | Profile link works everywhere | ✅ |
| Logout | Clears session and redirects | ✅ |
| API | Returns correct JSON | ✅ |

## Troubleshooting

### Profile Page Won't Load
- Check if logged in (look for `currentUser` in localStorage)
- Check browser console for errors
- Verify Flask backend is running

### Orders Not Showing
- Check if orders were actually saved (should see "Order saved successfully" during checkout)
- Verify `/api/nursery/orders/user/{userId}` returns data
- Check browser Network tab for API response

### Modal Won't Open
- Check console for JavaScript errors
- Verify order details are being fetched
- Check if Bootstrap CSS is loaded

### Logout Not Working
- Verify localStorage is being cleared
- Check if registration.html exists and is accessible
- Check window.location is working

## Success Indicators

✅ All tests pass when:
1. Profile page loads without errors
2. Orders appear after placing one
3. Order details modal opens correctly
4. Navigation works from all pages
5. Logout clears session properly
6. API endpoints return valid JSON
7. User info displays accurately
8. No console errors

---
**Last Updated**: 2026
**Version**: 1.0
**Status**: Ready for Testing
