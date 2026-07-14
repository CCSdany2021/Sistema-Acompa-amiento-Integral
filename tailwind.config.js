/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./acompanamiento/templates/**/*.html",
    "./estudiantes/templates/**/*.html",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#0f172a",
        'azul-insti': "#27418C",
        ocean: "#0ea5e9",
        mint: "#10b981",
        coral: "#fb7185",
        sand: "#f8fafc",
        brand: {
          50:  '#f0fdfa',
          100: '#ccfbf1',
          200: '#99f6e4',
          300: '#5eead4',
          400: '#2dd4bf',
          500: '#14b8a6',
          600: '#0d9488',
          700: '#0f766e',
          800: '#115e59',
          900: '#134e4a',
        }
      },
      boxShadow: {
        soft:    "0 10px 30px rgba(2, 6, 23, 0.08)",
        glow:    "0 0 20px rgba(13, 148, 136, 0.5)",
        'glow-lg': "0 0 30px rgba(13, 148, 136, 0.6)",
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'slide-in':   'slideIn 0.3s ease-out',
        'fade-in':    'fadeIn 0.2s ease-out',
      },
      keyframes: {
        slideIn: {
          '0%':   { transform: 'translateX(-100%)', opacity: '0' },
          '100%': { transform: 'translateX(0)',      opacity: '1' },
        },
        fadeIn: {
          '0%':   { opacity: '0' },
          '100%': { opacity: '1' },
        },
      }
    }
  },
  plugins: [],
}
