local luasnip = require 'luasnip'

require('luasnip.loaders.from_vscode').lazy_load()
luasnip.config.setup {}
luasnip.filetype_extend('twig', { 'twig', 'html', 'all' })
luasnip.filetype_extend('vue', { 'vue', 'html', 'all' })
