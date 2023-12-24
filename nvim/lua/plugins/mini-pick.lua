return {
  'echasnovski/mini.pick',
  keys = { '<leader>' },
  dependencies = {
    -- extra pickers
    'echasnovski/mini.extra',
    -- Project.nvim sorts out your current working directory while searching
    'ahmedkhalf/project.nvim',
    -- nice icons
    'nvim-tree/nvim-web-devicons',
  },
  config = function()
    -- automagically makes sure cwd and paths are set correctly
    require('project_nvim').setup()

    local MiniPick = require 'mini.pick'
    local MiniExtra = require 'mini.extra'

    -- function to calculate center of screen and use it as arguments to mini-pick window config
    local win_config = function()
      local height = math.floor(0.618 * vim.o.lines)
      local width = math.floor(0.618 * vim.o.columns)
      return {
        anchor = 'NW',
        height = height,
        width = width,
        border = 'double',
        row = math.floor(0.5 * (vim.o.lines - height)),
        col = math.floor(0.5 * (vim.o.columns - width)),
      }
    end

    MiniPick.setup {
      window = { config = win_config },
      mappings = {
        toggle_info = '<C-k>',
        toggle_preview = '<C-p>',
        move_down = '<Tab>',
        move_up = '<S-Tab>',
      },
    }
    MiniExtra.setup()

    require('utils').keymapSetList {
      -- Search using current buffers
      { 'n', '<leader><space>', MiniPick.builtin.buffers, { desc = '[ ] Find existing buffers' } },
      {
        'n',
        '<leader>/',
        function()
          MiniExtra.pickers.buf_lines()
        end,
        { desc = '[/] Fuzzily search in currently opened buffers' },
      },

      -- Search based on filename
      { 'n', '<leader>sf', MiniPick.builtin.files, { desc = '[S]earch [F]iles' } },
      { 'n', '<leader>?', MiniExtra.pickers.oldfiles, { desc = '[?] Find recently opened files' } },

      -- Search using grep
      { 'n', '<leader>sg', MiniPick.builtin.grep_live, { desc = '[S]earch by [G]rep' } },
      {
        'n',
        '<leader>sw',
        function()
          MiniPick.builtin.grep { pattern = vim.fn.escape(vim.fn.expand '<cword>', [[\/]]) }
        end,
        { desc = '[S]earch current [W]ord' },
      },

      -- Other search
      { 'n', '<leader>sh', MiniPick.builtin.help, { desc = '[S]earch [H]elp' } },
      { 'n', '<leader>sd', MiniExtra.pickers.diagnostic, { desc = '[S]earch [D]iagnostics' } },
      { 'n', '<leader>gf', MiniExtra.pickers.git_hunks, { desc = 'Search [G]it [F]iles' } },
      { 'n', '<leader>sr', MiniPick.builtin.resume, { desc = '[S]earch [R]resume' } },
    }
  end,
}
