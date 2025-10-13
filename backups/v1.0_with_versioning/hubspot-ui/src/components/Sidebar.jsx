import React from 'react';
import {
  LayoutDashboard,
  Megaphone,
  Users,
  Headphones,
  BarChart3,
  Settings,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';

/**
 * Sidebar Component
 * - Persistent left navigation with collapsible functionality
 * - HubSpot-style navigation items with icons
 * - Responsive design with mobile hamburger menu support
 */
const Sidebar = ({ isCollapsed, onToggle, isMobileMenuOpen, onMobileToggle }) => {
  const navigationItems = [
    { icon: LayoutDashboard, label: 'Dashboard', active: false },
    { icon: Megaphone, label: 'Marketing', active: true },
    { icon: Users, label: 'Sales', active: false },
    { icon: Headphones, label: 'Service', active: false },
    { icon: BarChart3, label: 'Reports', active: false },
    { icon: Settings, label: 'Settings', active: false },
  ];

  return (
    <>
      {/* Mobile Overlay */}
      {isMobileMenuOpen && (
        <div
          className="fixed inset-0 z-40 bg-black bg-opacity-50 lg:hidden"
          onClick={onMobileToggle}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed left-0 top-0 z-50 h-full bg-hubspot-navy transition-transform duration-300 ease-in-out
        ${isCollapsed ? 'w-16' : 'w-64'}
        ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        lg:relative lg:translate-x-0
      `}>
        {/* Sidebar Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-600">
          <div className={`${isCollapsed ? 'hidden' : 'block'}`}>
            <h1 className="text-xl font-bold text-white">HubSpot</h1>
          </div>

          {/* Toggle Button */}
          <button
            onClick={onToggle}
            className="p-1 rounded hover:bg-slate-700 text-slate-300 hover:text-white hidden lg:block"
            aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {isCollapsed ? (
              <ChevronRight className="w-5 h-5" />
            ) : (
              <ChevronLeft className="w-5 h-5" />
            )}
          </button>
        </div>

        {/* Navigation Items */}
        <nav className="p-4 space-y-2">
          {navigationItems.map((item, index) => {
            const Icon = item.icon;
            return (
              <div
                key={index}
                className={`nav-item ${item.active ? 'active' : ''}`}
                title={isCollapsed ? item.label : ''}
              >
                <Icon className="w-5 h-5 flex-shrink-0" />
                <span className={`ml-3 ${isCollapsed ? 'hidden' : 'block'}`}>
                  {item.label}
                </span>
              </div>
            );
          })}
        </nav>

        {/* Sidebar Footer */}
        <div className="absolute bottom-4 left-4 right-4">
          <div className={`${isCollapsed ? 'hidden' : 'block'}`}>
            <div className="text-xs text-slate-400 mb-2">
              Account: Professional
            </div>
            <div className="text-xs text-slate-400">
              Updated 2 min ago
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Sidebar;