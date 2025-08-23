# D&D Wikis - The Portals

A collection of interactive D&D campaign stories and adventures, featuring a modern web interface with slideshow chapters and campaign management.

## Live Site
https://ldstrebel.github.io/dndwikis/

## Project Structure

```
dndwikis/
├── index.html              # Main homepage with campaign showcase
├── script.js               # JavaScript functionality and modal system
├── style.css               # Main stylesheet with theme variables
├── chpt-html-template.html # Template for creating new chapters
├── chapters/               # Chapter files directory
├── images/                 # Campaign artwork and assets
└── campaigns/              # Individual campaign directories
```

## Current Campaigns

### 1. The Chronicles of Meryl
- **Genre**: Fantasy Adventure
- **Chapters**: 2
- **Description**: She said it was just a babysitting job, there was no mention of trials!

### 2. Dungeon Crawlers
- **Genre**: Sci-Fi LitRPG
- **Chapters**: 2
- **Description**: In a world where reality blends with the digital, participants are thrust into deadly dungeons.

### 3. Verdant Scar
- **Genre**: Fantasy Adventure
- **Chapters**: 2
- **Description**: In the mystical realm of Eldara, a verdant valley scarred by ancient magic holds secrets that could reshape the world.

## How to Add a New Campaign

### Step 1: Add Campaign Card to Main Page
Edit `index.html` and add a new campaign card in the campaign grid section:

```html
<article class="campaign-card"
    data-genre="fantasy adventure"
    data-campaign-title="Your Campaign Name"
    data-poster-image="images/your-campaign-image.jpg"
    data-full-synopsis="Your campaign description here."
    data-chapters='[
        {"title": "Chapter 1: Title", "url": "your-ch1.html"},
        {"title": "Chapter 2: Title", "url": "your-ch2.html"}
    ]'>
    <div class="tarot-art-container">
        <img src="images/your-campaign-image.jpg" alt="Artwork for Your Campaign Name campaign" class="campaign-poster">
    </div>
    <div class="tarot-info-container">
        <h3 class="campaign-title">Your Campaign Name</h3>
    </div>
</article>
```

**Required Data Attributes:**
- `data-genre`: Campaign genre(s) for filtering
- `data-campaign-title`: Campaign name
- `data-poster-image`: Path to campaign artwork
- `data-full-synopsis`: Full campaign description
- `data-chapters`: JSON array of chapter objects with title and URL

### Step 2: Create Campaign Artwork
Add your campaign image to the `images/` directory. Recommended format: JPG or WebP, dimensions similar to existing campaign images.

### Step 3: Create Chapter Files
Use `chpt-html-template.html` as a starting point for each chapter:

1. **Copy the template** and rename it (e.g., `your-ch1.html`)
2. **Update the title** in both `<title>` tag and header
3. **Add your content** in the slideshow format
4. **Update slide counter** to match your total slide count

**Chapter Structure:**
- Each chapter uses a slideshow format with navigation
- Content is divided into `<div class="slide">` elements
- First slide is visible, others are hidden with `hidden` class
- Navigation buttons allow users to move between slides

### Step 4: Test Your Campaign
1. Open `index.html` in a browser
2. Click on your new campaign card
3. Verify the modal displays correctly
4. Test chapter navigation
5. Ensure all links work properly

## Technical Features

### Campaign Modal System
- Click any campaign card to open detailed view
- Displays campaign artwork, synopsis, and chapter list
- Genre tags are automatically generated from data attributes
- Responsive design with accessibility features

### Genre Filtering
- Filter campaigns by genre using the dropdown
- Supports multiple genres per campaign (space-separated)
- "All Genres" option shows all campaigns

### Chapter Navigation
- Slideshow format with Previous/Next buttons
- Keyboard navigation (Arrow keys)
- Slide counter showing current position
- Smooth fade transitions between slides

### Loading Animations
- Global loading overlay for page transitions
- D20 dice animation for chapter loading
- Smooth fade effects for better UX

## File Naming Conventions

- **Campaign files**: Use descriptive names (e.g., `verdant-scar.jpg`)
- **Chapter files**: Use campaign abbreviation + chapter number (e.g., `vs-ch1.html`)
- **Images**: Use descriptive names in lowercase with hyphens

## Styling and Themes

The site uses a custom color scheme defined in CSS variables:
- **Primary Teal**: #25B8B8
- **Primary Magenta**: #B42A8E
- **Dark Background**: #181A1B
- **Light Text**: #EAEAEA

Typography uses Google Fonts:
- **Primary**: MedievalSharp (for headings)
- **Secondary**: Cinzel Decorative (for body text)

## Browser Compatibility

- Modern browsers with ES6+ support
- Responsive design for mobile and desktop
- Progressive enhancement for older browsers

## Contributing

When adding new content:
1. Follow the existing naming conventions
2. Test thoroughly before committing
3. Ensure accessibility features are maintained
4. Update this README if adding new features

## License

© No electrons were harmed in the making of this whatever it is. All rights reserved.
