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

    appearance = {
      nerd_font_variant = 'mono',
    },

    signature = {
      enabled = true,
      window = { border = 'rounded' },
    },

    sources = {
      default = { 'lsp', 'path', 'snippets', 'buffer' },
      cmdline = function()
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
      providers = {
        cmdline = {
          min_keyword_length = 3,
        },
        buffer = {
          min_keyword_length = 3,
          max_items = 5,
        },
      },
    },
  },
  opts_extend = { 'sources.default' },
}
