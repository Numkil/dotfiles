return {
  'nvim-telescope/telescope.nvim',
  dependencies = {
    'nvim-lua/plenary.nvim',
    'nvim-tree/nvim-web-devicons',
    -- Project.nvim sorts out your current working directory while searching
    'ahmedkhalf/project.nvim',
  },
  config = function()
    require('telescope').setup()

    local builtin = require('telescope.builtin')
    require('utils').keymapSetList {
      { 'n', '<leader><space>', builtin.buffers,                   { desc = 'Search in buffers' } },
      { 'n', '<leader>/',       builtin.current_buffer_fuzzy_find, { desc = 'Search fuzzily in current buffer' } },
      { 'n', '<leader>sf',      builtin.find_files,                { desc = 'Search in files' } },
      { 'n', '<leader>?',       builtin.oldfiles,                  { desc = 'Search in oldfiles' } },
      { 'n', '<leader>sg',      builtin.live_grep,                 { desc = 'Search by string in cwd' } },
      { 'n', '<leader>sw',      builtin.grep_string,               { desc = 'Search current word in cwd' } },
      { 'n', '<leader>sh',      builtin.help_tags,                 { desc = 'Search in help pages' } },
      { 'n', '<leader>sd',      builtin.diagnostics,               { desc = 'Search in diagnostics' } },
      { 'n', '<leader>gf',      builtin.git_status,                { desc = 'Show git status' } },
      { 'n', '<leader>sr',      builtin.resume,                    { desc = 'Resume last search' } },
    }
  end
}
