import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Topbar from './components/Topbar';
import MainContent from './components/MainContent';

/**
 * Main App Component
 * - Assembles Sidebar, Topbar, and MainContent components
 * - Manages sidebar collapse state and mobile menu functionality
 * - Responsive layout that adapts to different screen sizes
 * - HubSpot-style interface with professional styling
 */
function App() {
  // State for sidebar collapse functionality
  const [isCollapsed, setIsCollapsed] = useState(false);
  // State for mobile menu visibility
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  // Handle sidebar toggle for desktop
  const handleSidebarToggle = () => {
    setIsCollapsed(!isCollapsed);
  };

  // Handle mobile menu toggle
  const handleMobileToggle = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  // Close mobile menu when screen size changes to desktop
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 1024) { // lg breakpoint
        setIsMobileMenuOpen(false);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Close mobile menu on escape key
  useEffect(() => {
    const handleEscapeKey = (event) => {
      if (event.key === 'Escape') {
        setIsMobileMenuOpen(false);
      }
    };

    document.addEventListener('keydown', handleEscapeKey);
    return () => document.removeEventListener('keydown', handleEscapeKey);
  }, []);

  return (
    <div className="h-screen bg-slate-50 overflow-hidden">
      {/* Main Layout Container */}
      <div className="flex h-full">
        {/* Sidebar Component */}
        <Sidebar
          isCollapsed={isCollapsed}
          onToggle={handleSidebarToggle}
          isMobileMenuOpen={isMobileMenuOpen}
          onMobileToggle={handleMobileToggle}
        />

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Top Navigation Bar */}
          <Topbar
            isCollapsed={isCollapsed}
            onMobileToggle={handleMobileToggle}
            isMobileMenuOpen={isMobileMenuOpen}
          />

          {/* Main Content */}
          <MainContent isCollapsed={isCollapsed} />
        </div>
      </div>
    </div>
  );
}

export default App;