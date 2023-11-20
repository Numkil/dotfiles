local opts = {
  highlight = {
    pattern = [[.*<(KEYWORDS)]], -- Don't require a colon.
  },
  search = {
    pattern = [[\b(KEYWORDS)\b]], -- Match without the extra colon.
  },
}

return {
  'folke/todo-comments.nvim',
  dependencies = { 'nvim-lua/plenary.nvim' },
  event = { 'BufReadPre', 'BufNewFile' },
  config = function()
    require('todo-comments').setup(opts)

    vim.keymap.set('n', '<leader>st', ':TodoLocList<CR>', { desc = '[S]earch [Todos]' })
  end,
}
