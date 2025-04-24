return {
  'rachartier/tiny-code-action.nvim',
  dependencies = {
    { 'nvim-lua/plenary.nvim' },
    -- optional picker via fzf-lua
    { 'ibhagwan/fzf-lua' },
  },
  event = 'LspAttach',
  opts = {
    picker = { 'select' },
  },
}
