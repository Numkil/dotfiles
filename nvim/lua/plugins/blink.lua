return {
  'saghen/blink.cmp',
  event = { 'BufReadPre', 'BufNewFile' },
  -- optional: provides snippets for the snippet source
  dependencies = { 'rafamadriz/friendly-snippets' },

  -- use a release tag to download pre-built binaries
  version = '*',

  ---@module 'blink.cmp'
  ---@type blink.cmp.Config
  opts = {
    completion = {
      documentation = {
        auto_show = true,
        auto_show_delay_ms = 250,
        treesitter_highlighting = true,
      },
    },
    appearance = {
      nerd_font_variant = 'mono',
    },
    signature = {
      enabled = true,
      window = { border = 'rounded' },
    },
    keymap = {
      preset = 'enter',
      ['<Tab>'] = {
        function(cmp)
          return cmp.select_next()
        end,
        'snippet_forward',
        'fallback',
      },
      ['<S-Tab>'] = {
        function(cmp)
          return cmp.select_prev()
        end,
        'snippet_backward',
        'fallback',
      },
    },
    cmdline = {
      sources = function()
        local type = vim.fn.getcmdtype()
        -- Search forward and backward
        if type == '/' or type == '?' then
          return {}
        end
        -- Commands
        if type == ':' or type == '@' then
          return { 'cmdline' }
        end
        return {}
      end,
    },
    snippets = { preset = 'luasnip' },
    sources = {
      default = { 'lsp', 'path', 'snippets', 'buffer', 'lazydev' },
      providers = {
        lazydev = {
          name = 'LazyDev',
          module = 'lazydev.integrations.blink',
          -- make lazydev completions top priority (see `:h blink.cmp`)
          score_offset = 100,
        },
        cmdline = {
          min_keyword_length = 4,
          score_offset = 4,
        },
        snippets = {
          min_keyword_length = 1,
          score_offset = 4,
        },
        lsp = {
          min_keyword_length = 1,
          score_offset = 3,
        },
        path = {
          min_keyword_length = 3,
          score_offset = 2,
        },
        buffer = {
          min_keyword_length = 3,
          score_offset = 1,
        },
      },
    },
  },
  opts_extend = { 'sources.default' },
}
