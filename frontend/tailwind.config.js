/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./pages/**/*.html",
    "./components/**/*.{js,jsx}",
    "./src/**/*.{js,jsx}", // Include src for compatibility during migration
  ],

  // Dark mode strategy: class-based (toggle via .dark class on <html>)
  darkMode: 'class',

  theme: {
    extend: {
      // Extend Tailwind's default theme with design tokens from CSS variables
      colors: {
        // Background colors
        'bg-primary': 'var(--bg-primary)',
        'bg-secondary': 'var(--bg-secondary)',
        'bg-tertiary': 'var(--bg-tertiary)',

        // Text colors
        'text-primary': 'var(--text-primary)',
        'text-secondary': 'var(--text-secondary)',

        // Accent colors
        'accent-green': 'var(--accent-green)',
        'accent-blue': 'var(--accent-blue)',
        'accent-blue-dark': 'var(--accent-blue-dark)',
        'accent-red': 'var(--accent-red)',

        // Border colors
        'border': 'var(--border-color)',

        // Status colors
        'success-bg': 'var(--success-bg)',
        'success-text': 'var(--success-text)',
        'error-bg': 'var(--error-bg)',
        'error-text': 'var(--error-text)',
      },

      // Spacing scale (maps to CSS variables)
      spacing: {
        'xs': 'var(--spacing-xs)',
        'sm': 'var(--spacing-sm)',
        'md': 'var(--spacing-md)',
        'lg': 'var(--spacing-lg)',
        'xl': 'var(--spacing-xl)',
      },

      // Font family
      fontFamily: {
        'base': 'var(--font-family-base)',
      },

      // Font sizes
      fontSize: {
        'sm': 'var(--font-size-sm)',
        'base': 'var(--font-size-base)',
        'lg': 'var(--font-size-lg)',
      },
    },
  },

  plugins: [],
}
