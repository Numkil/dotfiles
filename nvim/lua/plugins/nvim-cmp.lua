return {
  -- Autocompletion
  'hrsh7th/nvim-cmp',
  event = { 'BufReadPre', 'BufNewFile' },
  dependencies = {
    -- Snippet Engine & its associated nvim-cmp source
    {
      'L3MON4D3/LuaSnip',
      build = 'make install_jsregexp',
    },
    'saadparwaiz1/cmp_luasnip',

    -- Adds LSP completion capabilities
    'hrsh7th/cmp-nvim-lsp',

    -- Adds some generic source functionality
    'hrsh7th/cmp-buffer',
    'hrsh7th/cmp-path',
    'hrsh7th/cmp-cmdline',

    -- Adds a number of user-friendly snippets
    'rafamadriz/friendly-snippets',

    -- copilot integration
    'supermaven-inc/supermaven-nvim',
  },
  config = function()
    -- [[ Configure supermaven ]]
    require('supermaven-nvim').setup {
      disable_inline_completion = false, -- disables inline completion for use with cmp
      disable_keymaps = true, -- disables built in keymaps for more manual control
    }

    -- [[ Configure nvim-cmp ]]
    -- See `:help cmp`
    local cmp = require 'cmp'
    local luasnip = require 'luasnip'

    require('luasnip.loaders.from_vscode').lazy_load()
    luasnip.config.setup {}
    luasnip.filetype_extend('twig', { 'twig', 'html', 'all' })

    cmp.setup {
      performance = {
        max_view_entries = 25,
      },
      snippet = {
        expand = function(args)
          luasnip.lsp_expand(args.body)
        end,
      },
      mapping = cmp.mapping.preset.insert {
        ['<C-d>'] = cmp.mapping.scroll_docs(-4),
        ['<C-f>'] = cmp.mapping.scroll_docs(4),
        ['<CR>'] = cmp.mapping(function(fallback)
          if cmp.visible() then
            if luasnip.expandable() then
              luasnip.expand()
            else
              cmp.confirm {
                select = true,
              }
            end
          else
            fallback()
          end
        end),
        ['<C-CR>'] = cmp.mapping(function(fallback)
          if require('supermaven-nvim.completion_preview').has_suggestion() then
            require('supermaven-nvim.completion_preview').on_accept_suggestion()
          else
            fallback()
          end
        end),
        ['<Tab>'] = cmp.mapping(function(fallback)
          if cmp.visible() then
            if #cmp.get_entries() == 1 then
              cmp.confirm { select = true }
            else
              cmp.select_next_item()
            end
          elseif luasnip.locally_jumpable(1) then
            luasnip.jump(1)
          else
            fallback()
          end
        end, { 'i', 's' }),
        ['<S-Tab>'] = cmp.mapping(function(fallback)
          if cmp.visible() then
            if #cmp.get_entries() == 1 then
              cmp.confirm { select = true }
            else
              cmp.select_prev_item()
            end
          elseif luasnip.locally_jumpable(-1) then
            luasnip.jump(-1)
          else
            fallback()
          end
        end, { 'i', 's' }),
      },
    }

    local preferred_sources = cmp.config.sources({
      { name = 'luasnip' },
      { name = 'nvim_lsp' },
    }, {
      { name = 'path' },
    })

    vim.api.nvim_create_autocmd('BufRead', {
      group = vim.api.nvim_create_augroup('CmpBufferDisableGrp', { clear = true }),
      callback = function(ev)
        local sources = preferred_sources
        if not require('utils').isFileTooBig(ev.buf) then
          sources[#sources + 1] = { name = 'buffer', keyword_length = 4 }
        end
        cmp.setup.buffer {
          sources = cmp.config.sources(sources),
        }
      end,
    })

    cmp.setup.cmdline({ '/', '?' }, {
      mapping = cmp.mapping.preset.cmdline(),
      sources = {
        { name = 'buffer' },
      },
    })

    cmp.setup.cmdline(':', {
      mapping = cmp.mapping.preset.cmdline(),
      sources = cmp.config.sources {
        { name = 'path' },
        { name = 'cmdline' },
      },
    })
  end,
}
