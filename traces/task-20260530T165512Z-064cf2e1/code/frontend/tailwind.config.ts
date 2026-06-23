import type { Config } from 'tailwindcss';

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  darkMode: ['class', '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#2563EB',
          50: '#adc2f2',
          500: '#628deb',
          600: '#4268bc',
          700: '#28488c',
          800: '#142b5e',
        },
        secondary: {
          DEFAULT: '#ebad24',
        },
        status: {
          online: '#10B981',
          warning: '#F59E0B',
          error: '#EF4444',
          offline: '#6B7280',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['Fira Code', 'Monaco', 'monospace'],
      },
      spacing: {
        '1': '4px',
        '2': '8px',
        '3': '12px',
        '4': '16px',
        '6': '24px',
        '8': '32px',
        '12': '48px',
        '16': '64px',
      },
      borderRadius: {
        sm: '4px',
        DEFAULT: '8px',
        md: '12px',
        lg: '16px',
        full: '9999px',
      },
      boxShadow: {
        card: '0 1px 3px 0 rgba(0,0,0,0.1), 0 1px 2px 0 rgba(0,0,0,0.06)',
        'card-hover': '0 4px 6px -1px rgba(0,0,0,0.1)',
        dropdown: '0 10px 15px -3px rgba(0,0,0,0.1)',
        modal: '0 25px 50px -12px rgba(0,0,0,0.25)',
      },
      animation: {
        'slide-down': 'slideDown 250ms ease-out',
        'fade-in': 'fadeIn 250ms ease-out',
        'pulse-dot': 'pulse 2s infinite',
      },
      keyframes: {
        slideDown: {
          from: { transform: 'translateY(-100%)', opacity: '0' },
          to: { transform: 'translateY(0)', opacity: '1' },
        },
        fadeIn: {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
      },
    },
  },
  plugins: [],
} satisfies Config;
