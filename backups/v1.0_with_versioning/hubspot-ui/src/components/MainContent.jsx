import React, { useState } from 'react';
import {
  Download,
  Plus,
  Filter,
  ChevronDown,
  Mail,
  TrendingUp,
  Eye,
  MousePointer,
  Activity
} from 'lucide-react';

/**
 * MainContent Component
 * - Main content area with section headers and tabs
 * - Sample cards/tables with clean typography
 * - HubSpot-style metrics and charts placeholders
 * - Export functionality button
 */
const MainContent = ({ isCollapsed }) => {
  const [activeTab, setActiveTab] = useState('manage');

  const tabs = [
    { id: 'manage', label: 'Manage', active: true },
    { id: 'analyze', label: 'Analyze', active: false },
    { id: 'health', label: 'Health', active: false },
  ];

  // Sample metrics data
  const metrics = [
    {
      title: 'Open Rate',
      value: '24.5%',
      change: '+2.1%',
      trend: 'up',
      icon: Eye,
      color: 'text-green-600'
    },
    {
      title: 'Click Rate',
      value: '3.8%',
      change: '+0.5%',
      trend: 'up',
      icon: MousePointer,
      color: 'text-blue-600'
    },
    {
      title: 'Bounce Rate',
      value: '2.1%',
      change: '-0.3%',
      trend: 'down',
      icon: TrendingUp,
      color: 'text-orange-600'
    },
    {
      title: 'Delivered',
      value: '98.7%',
      change: '+0.1%',
      trend: 'up',
      icon: Activity,
      color: 'text-purple-600'
    },
  ];

  // Sample email campaigns
  const campaigns = [
    {
      name: 'Welcome Series - Q4 2024',
      status: 'Active',
      sent: '12,450',
      opened: '3,051',
      clicked: '473',
      lastSent: '2 hours ago'
    },
    {
      name: 'Product Launch Announcement',
      status: 'Draft',
      sent: '0',
      opened: '0',
      clicked: '0',
      lastSent: 'Never'
    },
    {
      name: 'Newsletter - October 2024',
      status: 'Completed',
      sent: '8,732',
      opened: '2,149',
      clicked: '329',
      lastSent: '3 days ago'
    }
  ];

  return (
    <main className={`flex-1 bg-slate-50 transition-all duration-300 ${isCollapsed ? 'ml-16' : 'ml-64'} lg:ml-0`}>
      {/* Section Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center">
              <Mail className="w-6 h-6 mr-3 text-hubspot-orange" />
              Marketing Email
            </h1>
            <p className="text-sm text-gray-600 mt-1">
              Create, manage, and analyze your email campaigns
            </p>
          </div>

          {/* Export Button */}
          <button className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-hubspot-orange hover:bg-orange-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-hubspot-orange transition-colors duration-200">
            <Download className="w-4 h-4 mr-2" />
            Export
          </button>
        </div>

        {/* Tabs */}
        <div className="mt-4">
          <nav className="flex space-x-8">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors duration-200 ${
                  activeTab === tab.id
                    ? 'border-hubspot-orange text-hubspot-orange'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="p-6">
        {/* Metrics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {metrics.map((metric, index) => {
            const IconComponent = metric.icon;
            return (
              <div key={index} className="card">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">
                      {metric.title}
                    </p>
                    <p className="text-2xl font-bold text-gray-900">
                      {metric.value}
                    </p>
                    <p className={`text-sm ${metric.color} flex items-center mt-1`}>
                      <TrendingUp className="w-3 h-3 mr-1" />
                      {metric.change}
                    </p>
                  </div>
                  <div className={`p-3 rounded-full bg-gray-100 ${metric.color}`}>
                    <IconComponent className="w-6 h-6" />
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Campaign Management Section */}
        <div className="card">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-gray-900">
              Email Campaigns
            </h2>
            <div className="flex space-x-3">
              <button className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-hubspot-orange">
                <Filter className="w-4 h-4 mr-2" />
                Filter
                <ChevronDown className="w-4 h-4 ml-1" />
              </button>
              <button className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-hubspot-orange hover:bg-orange-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-hubspot-orange">
                <Plus className="w-4 h-4 mr-2" />
                Create email
              </button>
            </div>
          </div>

          {/* Campaign Table */}
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Campaign
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Sent
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Opened
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Clicked
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Last Sent
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {campaigns.map((campaign, index) => (
                  <tr key={index} className="hover:bg-gray-50 cursor-pointer">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {campaign.name}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        campaign.status === 'Active'
                          ? 'bg-green-100 text-green-800'
                          : campaign.status === 'Draft'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {campaign.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {campaign.sent}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {campaign.opened}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {campaign.clicked}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {campaign.lastSent}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </main>
  );
};

export default MainContent;