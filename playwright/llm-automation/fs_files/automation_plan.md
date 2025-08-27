# Automation Test Plan for Hardee's Website

## 1. Test Scenarios
- **Homepage**: Verify the homepage loads correctly with promotional banners.
- **Menu Section**: Check that all menu items are displayed.
- **Ordering Functionality**: Test placing an order selected from the menu.
- **Store Locator**: Validate the functionality of the store locator.
- **Nutritional Information**: Verify that nutritional info for menu items is accessible.
- **Deals and Coupons**: Ensure that deals are displayed and clickable.

## 2. Test Cases

### Test Case 1: Verify Homepage Loads
- **Steps**: 
  1. Open the website.
- **Expected Result**: Homepage should load with visible promotional banners.
- **Priority**: High

### Test Case 2: Check Menu Items Display
- **Steps**:
  1. Navigate to the Menu section.
- **Expected Result**: All menu items should be displayed.
- **Priority**: High

### Test Case 3: Validate Ordering Functionality
- **Steps**:
  1. Select a menu item.
  2. Add to cart.
  3. Proceed to checkout.
- **Expected Result**: User should be able to place an order successfully.
- **Priority**: High

### Test Case 4: Store Locator Functionality
- **Steps**:
  1. Click on the Store Locator link.
  2. Enter zip code and search.
- **Expected Result**: List of nearby stores should be displayed.
- **Priority**: Medium

### Test Case 5: Nutritional Information Access
- **Steps**:
  1. Navigate to a menu item.
  2. Click on Nutritional Information link.
- **Expected Result**: Nutritional info for the item should be visible.
- **Priority**: Medium

### Test Case 6: Deals and Coupons Access
- **Steps**:
  1. Navigate to Deals section.
- **Expected Result**: Current deals should be displayed and clickable.
- **Priority**: Low

## 3. Edge Cases and Negative Testing
- Try placing an order without selecting an item.
- Validate the store locator with invalid zip codes.

## 4. Visual Validation Checkpoints
- Check images and banners for correct loading and display.