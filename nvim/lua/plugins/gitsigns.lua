return {
  'lewis6991/gitsigns.nvim',
  event = { 'BufReadPre', 'BufNewFile' },
  config = function()
    require('gitsigns').setup {
      on_attach = function(bufnr)
        local gitsigns = require('gitsigns')
        require('utils').keymapSet('n', '<leader>gt', function() gitsigns.blame_line { full = true } end,
          { desc = 'Toggle the blame view' })
      end
    }
  end,
}
