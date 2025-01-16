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
      },
      extensions = { 'fzf', 'lazy', 'mason', 'man', 'oil' },
    }
  end,
}
