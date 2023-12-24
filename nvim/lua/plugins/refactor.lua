return {
  'ThePrimeagen/refactoring.nvim',
  event = { 'BufReadPre', 'BufNewFile' },
  dependencies = {
    'nvim-lua/plenary.nvim',
    'nvim-treesitter/nvim-treesitter',
  },
  config = function()
    require('refactoring').setup()

    require('utils').keymapSet({ 'n', 'x' }, '<leader>rr', function()
      require('refactoring').select_refactor()
    end, { desc = 'Refactor this code' })
  end,
}
