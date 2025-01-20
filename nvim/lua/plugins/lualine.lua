return {
  'nvim-lualine/lualine.nvim',
  dependencies = {
    'nvim-tree/nvim-web-devicons',
  },
  config = function()
    require('lualine').setup {
      options = { theme = 'everforest' },
      sections = {
        -- Add the macro recording status in the mode section
        lualine_b = {
          'branch',
          'diff',
          'diagnostics',
          {
            'macro',
            fmt = function()
              local reg = vim.fn.reg_recording()
              if reg ~= '' then
                return 'Recording @' .. reg
              end
              return nil
            end,
            color = { fg = '#f57d26' },
            draw_empty = false,
          },
        },
        lualine_x = {
          function()
            return require('lazydo').get_lualine_stats()
          end,
          cond = function()
            return require('lazydo')._initialized
          end,
        },
      },
      extensions = { 'fzf', 'lazy', 'mason', 'man', 'oil' },
    }
  end,
}
