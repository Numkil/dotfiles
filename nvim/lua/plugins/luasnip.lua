return {
  'L3MON4D3/LuaSnip',
  event = { 'BufReadPre', 'BufNewFile' },
  dependencies = { 'rafamadriz/friendly-snippets' },
  -- follow latest release.
  version = 'v2.*', -- Replace <CurrentMajor> by the latest released major (first number of latest release)
  -- install jsregexp (optional!).
  build = 'make install_jsregexp',
  config = function()
    local luasnip = require 'luasnip'

    require('luasnip.loaders.from_vscode').lazy_load()
    luasnip.config.setup {}
    luasnip.filetype_extend('twig', { 'twig', 'html', 'all' })
    luasnip.filetype_extend('vue', { 'vue', 'html', 'all' })
  end,
}
