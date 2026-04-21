-- [[ Configure Matchup ]]
vim.g.matchup_matchparen_offscreen = { method = 'popup' }
vim.g.matchup_treesitter_enabled = true

-- [[ Configure Treesitter ]]
-- The new nvim-treesitter (main branch) only handles parser installation.
-- Neovim 0.12 only auto-starts highlighting for bundled parsers,
-- so we need to explicitly start it for community parsers.
require('nvim-treesitter').setup {}

-- Install parsers via TSInstall command
local parsers = require('utils.external-tools').parsers
local installed = require('nvim-treesitter.config').get_installed()
local to_install = vim.tbl_filter(function(p)
  return not vim.list_contains(installed, p)
end, parsers)
if #to_install > 0 then
  require('nvim-treesitter.install').install(to_install)
end

-- Enable treesitter highlighting for all filetypes that have a parser
vim.api.nvim_create_autocmd('FileType', {
  callback = function(args)
    local lang = vim.treesitter.language.get_lang(args.match)
    if lang and pcall(vim.treesitter.language.inspect, lang) then
      vim.treesitter.start(args.buf)
    end
  end,
})

-- [[ Configure Textobjects ]]
local ok_select, ts_select = pcall(require, 'nvim-treesitter.textobjects.select')
local ok_move,   ts_move   = pcall(require, 'nvim-treesitter.textobjects.move')
local ok_swap,   ts_swap   = pcall(require, 'nvim-treesitter.textobjects.swap')

if ok_select and ok_move and ok_swap then
  require('nvim-treesitter-textobjects').setup {
    select = {
      lookahead = true,
    },
    move = {
      set_jumps = true,
    },
  }
end

if ok_select then
  -- Select keymaps
  for _, mapping in ipairs {
    { 'aa', '@parameter.outer' },
    { 'ia', '@parameter.inner' },
    { 'af', '@function.outer' },
    { 'if', '@function.inner' },
    { 'ac', '@class.outer' },
    { 'ic', '@class.inner' },
  } do
    vim.keymap.set({ 'x', 'o' }, mapping[1], function()
      ts_select.select_textobject(mapping[2], 'textobjects')
    end, { desc = 'Textobject: ' .. mapping[2] })
  end
end

if ok_move then
  -- Move keymaps
  for _, mapping in ipairs {
    { ']m', 'goto_next_start', '@function.outer' },
    { ']]', 'goto_next_start', '@class.outer' },
    { ']M', 'goto_next_end', '@function.outer' },
    { '][', 'goto_next_end', '@class.outer' },
    { '[m', 'goto_previous_start', '@function.outer' },
    { '[[', 'goto_previous_start', '@class.outer' },
    { '[M', 'goto_previous_end', '@function.outer' },
    { '[]', 'goto_previous_end', '@class.outer' },
  } do
    vim.keymap.set({ 'n', 'x', 'o' }, mapping[1], function()
      ts_move[mapping[2]](mapping[3], 'textobjects')
    end, { desc = 'TS move: ' .. mapping[2] .. ' ' .. mapping[3] })
  end
end

if ok_swap then
  -- Swap keymaps
  vim.keymap.set('n', '<leader>a', function()
    ts_swap.swap_next '@parameter.inner'
  end, { desc = 'Swap next parameter' })
  vim.keymap.set('n', '<leader>A', function()
    ts_swap.swap_previous '@parameter.inner'
  end, { desc = 'Swap previous parameter' })
end

-- [[ Incremental selection via treesitter nodes ]]
local function get_node_range(node)
  local sr, sc, er, ec = node:range()
  return sr, sc, er, ec
end

local current_node = nil
vim.keymap.set({ 'n', 'x' }, '<C-space>', function()
  if current_node == nil then
    current_node = vim.treesitter.get_node()
    if not current_node then
      return
    end
  else
    local parent = current_node:parent()
    if parent then
      current_node = parent
    end
  end
  local sr, sc, er, ec = get_node_range(current_node)
  vim.fn.setpos("'<", { 0, sr + 1, sc + 1, 0 })
  vim.fn.setpos("'>", { 0, er + 1, ec, 0 })
  vim.cmd 'normal! gv'
end, { desc = 'Incremental treesitter node selection' })

vim.keymap.set('x', '<M-space>', function()
  if current_node then
    local child = current_node:child(0)
    if child then
      current_node = child
    end
  end
  if current_node then
    local sr, sc, er, ec = get_node_range(current_node)
    vim.fn.setpos("'<", { 0, sr + 1, sc + 1, 0 })
    vim.fn.setpos("'>", { 0, er + 1, ec, 0 })
    vim.cmd 'normal! gv'
  end
end, { desc = 'Decremental treesitter node selection' })

-- Reset node tracking when leaving visual mode
vim.api.nvim_create_autocmd('ModeChanged', {
  pattern = '[vV\x16]*:*',
  callback = function()
    current_node = nil
  end,
})

-- [[ Other plugins ]]
require('rainbow-delimiters.setup').setup {}

require('ts_context_commentstring').setup {
  enable_autocmd = false,
}

local get_option_function = vim.filetype.get_option
vim.filetype.get_option = function(filetype, option)
  return option == 'commentstring' and require('ts_context_commentstring.internal').calculate_commentstring() or get_option_function(filetype, option)
end
