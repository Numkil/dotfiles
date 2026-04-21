---@type snacks.Config
require('snacks').setup {
  dashboard = {
    sections = {
      { section = 'header' },
      { section = 'keys', gap = 1, padding = 1 },
      { pane = 2, icon = ' ', title = 'Recent Files', section = 'recent_files', indent = 2, padding = 2 },
      { pane = 2, icon = ' ', title = 'Recent Files in current directory', cwd = true, section = 'recent_files', indent = 2, padding = 3 },
      {
        pane = 2,
        icon = ' ',
        title = 'Git Status',
        section = 'terminal',
        enabled = function()
          return Snacks.git.get_root() ~= nil
        end,
        cmd = 'git status --short --branch --renames',
        height = 10,
        padding = 5,
        ttl = 5 * 60,
        indent = 3,
      },
    },
  },
  bigfile = {},
  terminal = {},
  git = {},
  indent = {},
  input = {},
  scope = {},
  words = {},
  picker = {
    win = {
      input = {
        keys = {
          ['<S-Tab>'] = { 'list_up', mode = { 'i', 'n' } },
          ['<Tab>'] = { 'list_down', mode = { 'i', 'n' } },
        },
      },
    },
  },
}

vim.keymap.set('n', '<leader><space>', function() Snacks.picker.buffers() end, { desc = 'Buffers' })
vim.keymap.set('n', '<leader>/', function() Snacks.picker.grep_buffers() end, { desc = 'Grep Open Buffers' })
vim.keymap.set('n', '<leader>sf', function() Snacks.picker.files() end, { desc = 'Find Files' })
vim.keymap.set('n', '<leader>?', function() Snacks.picker.recent() end, { desc = 'Recent' })
vim.keymap.set('n', '<leader>sg', function() Snacks.picker.grep() end, { desc = 'Grep' })
vim.keymap.set({ 'n', 'x' }, '<leader>sw', function() Snacks.picker.grep_word() end, { desc = 'Visual selection or word' })
vim.keymap.set('n', '<leader>sh', function() Snacks.picker.help() end, { desc = 'Help Pages' })
vim.keymap.set('n', '<leader>sd', function() Snacks.picker.diagnostics() end, { desc = 'Diagnostics' })
vim.keymap.set('n', '<leader>gs', function() Snacks.picker.git_status() end, { desc = 'Git Status' })
vim.keymap.set('n', '<leader>sr', function() Snacks.picker.resume() end, { desc = 'Resume' })
vim.keymap.set('n', 'gd', function() Snacks.picker.lsp_definitions() end, { desc = 'Goto Definition' })
vim.keymap.set('n', 'gD', function() Snacks.picker.lsp_declarations() end, { desc = 'Goto Declaration' })
vim.keymap.set('n', '<leader>ds', function() Snacks.picker.lsp_symbols() end, { desc = '[D]ocument [S]ymbols' })
vim.keymap.set('n', 'gR', function() Snacks.picker.lsp_references() end, { nowait = true, desc = 'References' })
vim.keymap.set('n', 'gI', function() Snacks.picker.lsp_implementations() end, { desc = 'Goto Implementation' })
vim.keymap.set('n', 'gy', function() Snacks.picker.lsp_type_definitions() end, { desc = 'Goto T[y]pe Definition' })
