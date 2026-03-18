/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['DM Sans', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        soil: {
          50:  '#fdf6ee',
          100: '#f7e4c8',
          200: '#efc897',
          300: '#e4a55a',
          400: '#d9832a',
          500: '#b96518',
          600: '#8f4c12',
          700: '#6b380d',
          800: '#48260a',
          900: '#291606',
        },
        leaf: {
          50:  '#edfaf1',
          100: '#c8f0d4',
          200: '#90e0ab',
          300: '#4dc97a',
          400: '#1fad55',
          500: '#148a40',
          600: '#0e6830',
          700: '#0a4d24',
          800: '#063318',
          900: '#031a0d',
        },
        sky: {
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
        },
        danger: {
          400: '#f87171',
          500: '#ef4444',
          600: '#dc2626',
        },
        warn: {
          400: '#fbbf24',
          500: '#f59e0b',
          600: '#d97706',
        }
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.4s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
      },
      keyframes: {
        fadeIn:  { from: { opacity: 0 }, to: { opacity: 1 } },
        slideUp: { from: { opacity: 0, transform: 'translateY(12px)' }, to: { opacity: 1, transform: 'translateY(0)' } },
      }
    }
  },
  plugins: []
}
