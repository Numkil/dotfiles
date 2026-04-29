vim.g.canola = {
  view_options = {
    show_hidden = true,
  },
  default_file_explorer = true,
}

require('utils').keymapSet('n', '-', '<CMD>Canola --float<CR>', { desc = 'Open parent directory' })
