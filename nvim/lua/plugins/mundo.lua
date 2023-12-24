return {
  'simnalamburt/vim-mundo',
  event = { 'BufReadPre', 'BufNewFile' },
  config = function()
    require('utils').keymapSet('', '<leader>dh', ':MundoToggle<CR>', { desc = '[D]ocument undo [H]istory' })

    vim.g.mundo_width = 35
    vim.g.mundo_preview_height = 20
    vim.g.mundo_right = 1
  end,
}
