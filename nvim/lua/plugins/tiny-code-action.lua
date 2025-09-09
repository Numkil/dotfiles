return {
  'rachartier/tiny-code-action.nvim',
  dependencies = {
    { 'nvim-lua/plenary.nvim' },
    -- optional picker via fzf-lua
    { 'ibhagwan/fzf-lua' },
  },
  event = 'LspAttach',
  config = function()
    require('tiny-code-action').setup {
      picker = {
        'fzf-lua',
        opts = {
          winborder = 'single',
        },
      },
    }

    require('utils').keymapSetList {
      {
        { 'n', 'x' },
        '<leader>ca',
        function()
          require('tiny-code-action').code_action()
        end,
        { desc = '[C]ode [A]ction' },
      },
    }
  end,
}
