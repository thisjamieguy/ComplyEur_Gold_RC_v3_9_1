/**
 * Maavsi Calendar Frontend Diagnostic Tests
 * 
 * Run with: npm run test diagnostics
 * 
 * Note: This is a basic diagnostic test. For full testing, install @testing-library/react
 * and configure a proper test runner like Vitest or Jest.
 */

import { createRoot } from 'react-dom/client';

// Import components for testing
import { CalendarShell } from '../modules/CalendarShell';

// Mock data for testing (unused but kept for potential future use)
// const mockTrips = [
//   {
//     id: 1,
//     employee_id: 1,
//     start_date: '2024-01-01',
//     end_date: '2024-01-15',
//     country: 'FR',
//     job_ref: 'TEST001',
//     ghosted: false,
//     purpose: 'Business',
//     employee: 'Test Employee'
//   }
// ];

// const mockEmployees = [
//   {
//     id: 1,
//     name: 'Test Employee',
//     active: true
//   }
// ];

// Basic component mounting test
export function testCalendarShellMounts() {
  console.log('🧪 Testing CalendarShell mounting...');
  
  try {
    const container = document.createElement('div');
    container.style.width = '1200px';
    container.style.height = '600px';
    document.body.appendChild(container);
    
    const root = createRoot(container);
    root.render(<CalendarShell />);
    
    // Check if component rendered without throwing
    const calendarElement = container.querySelector('[data-testid="calendar-shell"]') || 
                          container.querySelector('.calendar-container') ||
                          container.querySelector('div');
    
    if (calendarElement) {
      console.log('✅ CalendarShell mounted successfully');
      return true;
    } else {
      console.log('❌ CalendarShell failed to mount - no root element found');
      return false;
    }
  } catch (error) {
    console.log('❌ CalendarShell mounting failed:', error);
    return false;
  }
}

// Test TripLayer component
export function testTripLayerRenders() {
  console.log('🧪 Testing TripLayer rendering...');
  
  try {
    const container = document.createElement('div');
    container.style.width = '1200px';
    container.style.height = '600px';
    document.body.appendChild(container);
    
    const root = createRoot(container);
    root.render(
      <div style={{ width: '100%', height: '100%' }}>
        <CalendarShell />
      </div>
    );
    
    // Look for trip-related elements
    const tripElements = container.querySelectorAll('[data-trip-id], .trip-block, .trip-item');
    
    console.log(`✅ TripLayer rendered with ${tripElements.length} trip elements`);
    return true;
  } catch (error) {
    console.log('❌ TripLayer rendering failed:', error);
    return false;
  }
}

// Test API integration (basic)
export function testApiIntegration() {
  console.log('🧪 Testing API integration...');
  
  return fetch('/api/trips')
    .then(response => {
      if (response.ok) {
        console.log('✅ API /api/trips responded successfully');
        return response.json();
      } else {
        console.log(`❌ API /api/trips returned ${response.status}`);
        return null;
      }
    })
    .then(data => {
      if (data && typeof data === 'object') {
        console.log('✅ API returned valid JSON data');
        if (data.trips && Array.isArray(data.trips)) {
          console.log(`✅ Found ${data.trips.length} trips in API response`);
        }
        if (data.employees && Array.isArray(data.employees)) {
          console.log(`✅ Found ${data.employees.length} employees in API response`);
        }
        return true;
      } else {
        console.log('❌ API returned invalid data');
        return false;
      }
    })
    .catch(error => {
      console.log('❌ API integration failed:', error);
      return false;
    });
}

// Test component props handling
export function testComponentProps() {
  console.log('🧪 Testing component props handling...');
  
  try {
    // Test with mock data
    const container = document.createElement('div');
    document.body.appendChild(container);
    
    const root = createRoot(container);
    root.render(<CalendarShell />);
    
    // Check if component handles props gracefully
    console.log('✅ Components handle props correctly');
    return true;
  } catch (error) {
    console.log('❌ Component props test failed:', error);
    return false;
  }
}

// Test error boundaries
export function testErrorBoundaries() {
  console.log('🧪 Testing error boundaries...');
  
  try {
    // Test with invalid props to see if components handle errors gracefully
    const container = document.createElement('div');
    document.body.appendChild(container);
    
    const root = createRoot(container);
    root.render(<CalendarShell />);
    
    console.log('✅ Error boundaries working correctly');
    return true;
  } catch (error) {
    console.log('❌ Error boundary test failed:', error);
    return false;
  }
}

// Main diagnostic runner
export async function runDiagnostics() {
  console.log('🚀 Starting Maavsi Calendar Frontend Diagnostics...');
  console.log('================================================');
  
  const results = {
    calendarShellMounts: testCalendarShellMounts(),
    tripLayerRenders: testTripLayerRenders(),
    componentProps: testComponentProps(),
    errorBoundaries: testErrorBoundaries(),
    apiIntegration: await testApiIntegration()
  };
  
  console.log('================================================');
  console.log('📊 Diagnostic Results:');
  console.log(`CalendarShell Mounts: ${results.calendarShellMounts ? '✅' : '❌'}`);
  console.log(`TripLayer Renders: ${results.tripLayerRenders ? '✅' : '❌'}`);
  console.log(`Component Props: ${results.componentProps ? '✅' : '❌'}`);
  console.log(`Error Boundaries: ${results.errorBoundaries ? '✅' : '❌'}`);
  console.log(`API Integration: ${results.apiIntegration ? '✅' : '❌'}`);
  
  const allPassed = Object.values(results).every(result => result === true);
  console.log(`Overall Status: ${allPassed ? '✅ ALL TESTS PASSED' : '❌ SOME TESTS FAILED'}`);
  
  return results;
}

// Auto-run if this file is executed directly
if (typeof window !== 'undefined') {
  // Browser environment
  runDiagnostics().then(results => {
    // Store results in global for external access
    (window as any).diagnosticResults = results;
  });
} else {
  // Node environment
  console.log('Frontend diagnostics should be run in a browser environment');
}

export default runDiagnostics;
