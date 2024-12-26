return {
  'stevearc/oil.nvim',
  config = function()
    require("oil").setup({
      view_options = {
        show_hidden = true,      -- Shows all hidden files
      },
      default_file_explorer = true, -- Ensures oil takes over directory buffers
    })

    require('utils').keymapSet('n', '-', '<CMD>Oil --float<CR>', { desc = 'Open parent directory' })
  end,
}
