-- [[ Basic Keymaps ]]
-- Alias :W with :w because I keep accidentally typing it
vim.cmd [[ cnoreabbrev <expr> W getcmdtype() == ":" && getcmdline() == "W" ? "w" : "W" ]]

require('utils').keymapSetList {
  -- Because mac touch bar...
  { '', '<f1>', '<Nop>' },
  -- Remap for dealing with word wrap
  { 'n', 'k', "v:count == 0 ? 'gk' : 'k'", { desc = 'up', expr = true } },
  { 'n', 'j', "v:count == 0 ? 'gj' : 'j'", { desc = 'down', expr = true } },
  -- More comfortably flip through buffers
  { '', '<leader>n', ':bnext<CR>', { desc = 'Next buffer' } },
  { '', '<leader>N', ':bprevious<CR>', { desc = 'Previous buffer' } },
  -- Easier navigation in splits
  { 'n', '<C-k>', ':wincmd k<CR>', { desc = 'navigate between split' } },
  { 'n', '<C-j>', ':wincmd j<CR>', { desc = 'navigate between split' } },
  { 'n', '<C-h>', ':wincmd h<CR>', { desc = 'navigate between split' } },
  { 'n', '<C-l>', ':wincmd l<CR>', { desc = 'navigate between split' } },
  -- scrolling remaps
  { 'n', '<C-u>', '<C-u>zz', { desc = 'Scroll up' } },
  { 'n', '<C-d>', '<C-d>zz', { desc = 'Scroll down' } },
  -- Visual shifting ( does not exit Visual mode )
  { 'v', '<', '<gv', { desc = 'Shift left without exiting V' } },
  { 'v', '>', '>gv', { desc = 'Shift rightt without exiting V' } },
  -- Diagnostic keymaps
  { 'n', '[d', vim.diagnostic.goto_prev, { desc = 'Go to previous diagnostic message' } },
  { 'n', ']d', vim.diagnostic.goto_next, { desc = 'Go to next diagnostic message' } },
  { 'n', '<leader>e', vim.diagnostic.open_float, { desc = 'Open floating diagnostic message' } },
  { 'n', '<leader>q', vim.diagnostic.setloclist, { desc = 'Open diagnostics list' } },
  -- Clear notifications and search
  {
    'n',
    '<Esc>',
    function()
      vim.cmd 'Noice dismiss'
      vim.cmd 'nohl'
    end,
    { desc = 'Clear notifications and search' },
  },
}
