/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        hubspot: {
          orange: '#f97316',
          navy: '#1e293b',
          slate: '#475569',
          gray: '#64748b'
        }
      }
    },
  },
  plugins: [],
}