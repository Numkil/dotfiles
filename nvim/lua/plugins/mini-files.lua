return {
  'echasnovski/mini.files',
  lazy = false, --- NOTE: Important that this plugin loads on startup so it works as file explorer
  priority = 1000, --- when opening a directory instead of a file
  dependencies = {
    'echasnovski/mini.icons',
  },
  config = function()
    local MiniFiles = require 'mini.files'
    local minifiles_toggle = function()
      if not MiniFiles.close() then
        MiniFiles.open(vim.api.nvim_buf_get_name(0), false)
      end
    end

    require('utils').keymapSet('n', '-', minifiles_toggle, { desc = 'Open current directory as buffer' })

    MiniFiles.setup {
      use_as_default_explorer = true,
    }
  end,
}
