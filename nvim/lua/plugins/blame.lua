return {
  {
    'FabijanZulj/blame.nvim',
    event = { 'BufReadPre', 'BufNewFile' },
    config = function()
      require('blame').setup()

      require('utils').keymapSet('n', '<leader>gt', ':BlameToggle<CR>', { desc = 'Toggle the blame view' })
    end,
  },
}
