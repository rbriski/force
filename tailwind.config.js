module.exports = {
    content: ['./project/client/templates/**/*.html', './project/client/static/src/**/*.js', './node_modules/flowbite/**/*.js'],
    theme: {
        extend: {},
    },
    variants: {
        extend: {},
    },
    plugins: [
        require('@tailwindcss/forms'),
        require("flowbite/plugin")
    ]
}