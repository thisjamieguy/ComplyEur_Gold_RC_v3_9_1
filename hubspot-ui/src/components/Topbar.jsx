import React from 'react';
import {
  Search,
  Bell,
  User,
  Menu,
  X
} from 'lucide-react';

/**
 * Topbar Component
 * - Persistent top navigation bar
 * - Logo area, search bar, and profile section
 * - Mobile hamburger menu toggle
 * - Notification icons and user avatar
 */
const Topbar = ({ isCollapsed, onMobileToggle, isMobileMenuOpen }) => {
  return (
    <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between sticky top-0 z-30">
      {/* Left Section - Mobile Menu Toggle & Logo */}
      <div className="flex items-center space-x-4">
        {/* Mobile Menu Toggle */}
        <button
          onClick={onMobileToggle}
          className="p-2 rounded-lg hover:bg-gray-100 lg:hidden"
          aria-label="Toggle mobile menu"
        >
          {isMobileMenuOpen ? (
            <X className="w-5 h-5" />
          ) : (
            <Menu className="w-5 h-5" />
          )}
        </button>

        {/* Logo/Title Area - Hidden when sidebar is collapsed */}
        <div className={`${isCollapsed ? 'block' : 'hidden lg:block'}`}>
          <h2 className="text-lg font-semibold text-gray-900">
            Marketing
          </h2>
        </div>
      </div>

      {/* Center Section - Search Bar */}
      <div className="flex-1 max-w-md mx-4 hidden md:block">
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-4 w-4 text-gray-400" />
          </div>
          <input
            type="text"
            className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-hubspot-orange focus:border-hubspot-orange"
            placeholder="Search contacts, companies, deals..."
          />
        </div>
      </div>

      {/* Right Section - Notifications & Profile */}
      <div className="flex items-center space-x-3">
        {/* Search Icon for Mobile */}
        <button className="p-2 rounded-lg hover:bg-gray-100 md:hidden">
          <Search className="w-5 h-5 text-gray-500" />
        </button>

        {/* Notifications */}
        <div className="relative">
          <button className="p-2 rounded-lg hover:bg-gray-100 relative">
            <Bell className="w-5 h-5 text-gray-500" />
            {/* Notification Badge */}
            <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
          </button>
        </div>

        {/* Profile Dropdown */}
        <div className="relative">
          <button className="flex items-center space-x-2 p-2 rounded-lg hover:bg-gray-100">
            <div className="w-8 h-8 bg-hubspot-orange rounded-full flex items-center justify-center">
              <User className="w-5 h-5 text-white" />
            </div>
            <div className="hidden sm:block text-left">
              <div className="text-sm font-medium text-gray-900">John Doe</div>
              <div className="text-xs text-gray-500">Admin</div>
            </div>
          </button>
        </div>

        {/* Help/Settings Button */}
        <button className="p-2 rounded-lg hover:bg-gray-100 text-gray-500">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </button>
      </div>
    </header>
  );
};

export default Topbar;