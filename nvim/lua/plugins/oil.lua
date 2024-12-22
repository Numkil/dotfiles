return {
  'stevearc/oil.nvim',
  config = function()
    require('oil').setup()

    require('utils').keymapSet('n', '-', '<CMD>Oil --float<CR>', { desc = 'Open parent directory' })
  end,
}
