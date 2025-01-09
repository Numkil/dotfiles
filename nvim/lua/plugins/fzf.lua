return {
  'ibhagwan/fzf-lua',
  -- optional for icon support
  dependencies = {
    'nvim-tree/nvim-web-devicons',
    -- Project.nvim sorts out your current working directory while searching
    'ahmedkhalf/project.nvim',
  },
  config = function()
    -- calling `setup` is optional for customization
    require('fzf-lua').setup {
      winopts = {
        height = 0.7,
        width = 0.7,
        row = 0.5,
        col = 0.5,
        preview = {
          wrap = 'nowrap',
          vertical = 'down:50%',
          horizontal = 'right:50%',
          scrollbar = false, -- `false` or string:'float|border'
        },
      },
      keymap = {
        fzf = {
          ['tab'] = 'down',
          ['shift-tab'] = 'up',
        },
      },
    }

    local builtin = require 'fzf-lua'
    require('utils').keymapSetList {
      { 'n', '<leader><space>', builtin.buffers, { desc = 'Search in buffers' } },
      { 'n', '<leader>/', builtin.grep_curbuf, { desc = 'Search fuzzily in current buffer' } },
      { 'n', '<leader>sf', builtin.files, { desc = 'Search in files' } },
      { 'n', '<leader>?', builtin.oldfiles, { desc = 'Search in oldfiles' } },
      { 'n', '<leader>sg', builtin.live_grep, { desc = 'Search by string in cwd' } },
      { 'n', '<leader>sw', builtin.grep_cword, { desc = 'Search current word in cwd' } },
      { 'n', '<leader>sh', builtin.helptags, { desc = 'Search in help pages' } },
      { 'n', '<leader>sd', builtin.diagnostics_document, { desc = 'Search in diagnostics' } },
      { 'n', '<leader>gf', builtin.git_status, { desc = 'Show git status' } },
      { 'n', '<leader>sr', builtin.resume, { desc = 'Resume last search' } },
    }
  end,
}
