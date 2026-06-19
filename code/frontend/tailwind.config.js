/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        glass: {
          DEFAULT: 'rgba(15, 23, 42, 0.6)',
          light: 'rgba(30, 41, 59, 0.4)',
          border: 'rgba(148, 163, 184, 0.1)',
        },
        accent: {
          DEFAULT: '#6366f1',
          light: '#818cf8',
          dark: '#4f46e5',
        },
        surface: {
          DEFAULT: '#0f172a',
          light: '#1e293b',
          lighter: '#334155',
        },
      },
      backdropBlur: { xs: '2px' },
    },
  },
  plugins: [],
}
