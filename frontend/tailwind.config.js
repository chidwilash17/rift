/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          900: '#0d1117',
          800: '#161b22',
          700: '#1c2333',
          600: '#21262d',
          500: '#30363d',
        },
        accent: {
          blue: '#58a6ff',
          purple: '#bc8cff',
          green: '#3fb950',
          red: '#f85149',
          orange: '#d29922',
          cyan: '#39d2c0',
        }
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'monospace'],
        sans: ['Inter', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
