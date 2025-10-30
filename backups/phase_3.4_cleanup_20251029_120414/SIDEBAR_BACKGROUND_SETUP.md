# Sidebar Background Image Setup

## How to Add Your Image to the Sidebar Background

The sidebar now has a subtle background overlay effect implemented. To add your uploaded image:

### Step 1: Upload Your Image
1. Place your image file in: `app/static/images/`
2. Supported formats: `.jpg`, `.jpeg`, `.png`, `.webp`
3. Recommended size: 800x600px or larger for best quality

### Step 2: Update the CSS
In `app/static/css/hubspot-style.css`, find line 46:
```css
background-image: url('../images/your-uploaded-image.jpg'); /* Replace with your image */
```

Replace `your-uploaded-image.jpg` with your actual filename:
```css
background-image: url('../images/my-background-image.jpg');
```

### Step 3: Adjust Overlay Opacity (Optional)
To make the background more or less visible, adjust the overlay opacity in line 73:
```css
background-color: rgba(78, 90, 98, 0.75); /* Change 0.75 to adjust opacity */
```
- `0.5` = More visible background
- `0.8` = Less visible background
- `0.9` = Very subtle background

### Current Effect
- Background image covers the entire sidebar
- Semi-transparent gray overlay maintains readability
- All sidebar content appears above the background
- Works on desktop, mobile, and collapsed states

The effect creates a subtle, professional look where your image is visible behind the gray overlay without interfering with text readability.

