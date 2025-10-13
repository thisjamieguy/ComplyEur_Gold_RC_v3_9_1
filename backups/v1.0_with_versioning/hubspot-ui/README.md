# HubSpot-Style Responsive Web App Layout

A professional, responsive web application layout inspired by HubSpot's interface, built with React and TailwindCSS.

## 🚀 Features

- **Responsive Design**: Adapts seamlessly from desktop to mobile
- **Collapsible Sidebar**: Toggle between expanded and collapsed states
- **Mobile Menu**: Hamburger menu with overlay for mobile devices
- **Professional Styling**: HubSpot-inspired color scheme and typography
- **Interactive Components**: Hover effects, active states, and smooth transitions
- **Sample Content**: Metrics cards, tables, and mock data for demonstration

## 🎨 Design System

### Colors
- **Background**: `#f8fafc` (Light gray)
- **Sidebar**: `#1e293b` (Navy blue)
- **Accent**: `#f97316` (HubSpot orange)
- **Text**: Various shades of gray for hierarchy

### Components
- **Sidebar**: Navigation with icons and collapse functionality
- **Topbar**: Search, notifications, and profile section
- **MainContent**: Tabbed interface with metrics and data tables
- **Cards**: Clean cards with subtle shadows and rounded corners

## 📦 Installation

1. Navigate to the project directory:
   ```bash
   cd hubspot-ui
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

4. Open [http://localhost:3000](http://localhost:3000) in your browser

## 🏗️ Project Structure

```
src/
├── components/
│   ├── Sidebar.jsx      # Left navigation with collapse functionality
│   ├── Topbar.jsx       # Top navigation bar with search and profile
│   └── MainContent.jsx  # Main content area with tabs and data
├── App.jsx              # Main application component
├── main.jsx             # React entry point
├── index.css            # TailwindCSS imports and custom styles
└── ...
```

## 🔧 Key Components

### Sidebar (`Sidebar.jsx`)
- Persistent left navigation with collapsible functionality
- Navigation items with Lucide React icons
- Mobile overlay and responsive behavior
- Active states and hover effects

### Topbar (`Topbar.jsx`)
- Logo area, search bar, and profile section
- Mobile hamburger menu toggle
- Notification icons and user avatar
- Responsive search bar (hidden on mobile)

### MainContent (`MainContent.jsx`)
- Section headers with tabs (Manage, Analyze, Health)
- Metrics cards with sample data
- Data tables with hover effects
- Export functionality button

### App (`App.jsx`)
- Main layout container
- State management for sidebar and mobile menu
- Responsive breakpoint handling
- Keyboard shortcuts (ESC to close mobile menu)

## 📱 Responsive Behavior

- **Desktop**: Full sidebar with toggle button
- **Tablet**: Collapsed sidebar by default
- **Mobile**: Hidden sidebar with hamburger menu overlay

## 🎯 Interactive Features

- ✅ Sidebar collapse/expand toggle
- ✅ Mobile hamburger menu with overlay
- ✅ Tab switching in main content
- ✅ Hover effects on navigation and table rows
- ✅ Responsive search bar
- ✅ Notification badges
- ✅ Export button functionality

## 🛠️ Technologies Used

- **React 18** - UI framework
- **TailwindCSS** - Utility-first CSS framework
- **Lucide React** - Beautiful icon library
- **Vite** - Fast build tool and dev server

## 📄 License

This project is created as a demonstration of HubSpot-style UI components and is free to use and modify.