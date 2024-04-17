return {
  'echasnovski/mini.files',
  keys = { '-' },
  dependencies = {
    'nvim-tree/nvim-web-devicons',
  },
  config = function()
    local MiniFiles = require 'mini.files'
    local minifiles_toggle = function()
      if not MiniFiles.close() then
        MiniFiles.open(vim.api.nvim_buf_get_name(0))
      end
    end

    require('utils').keymapSet('n', '-', minifiles_toggle, { desc = 'Open current directory as buffer' })

    MiniFiles.setup {
      use_as_default_explorer = true,
    }
  end,
}
