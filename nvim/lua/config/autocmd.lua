-- [[ Highlight on yank ]]
-- See `:help vim.hl.on_yank()`
local highlight_group = vim.api.nvim_create_augroup('YankHighlight', { clear = true })
vim.api.nvim_create_autocmd('TextYankPost', {
  callback = function()
    vim.hl.on_yank()
  end,
  group = highlight_group,
  pattern = '*',
})

-- [[ Reopen file in the last position it was edited ]]
local openGroup = vim.api.nvim_create_augroup('OpenLastPos', { clear = true })
vim.api.nvim_create_autocmd('BufRead', {
  callback = function(opts)
    vim.api.nvim_create_autocmd('BufWinEnter', {
      once = true,
      buffer = opts.buf,
      callback = function()
        local ft = vim.bo[opts.buf].filetype
        local last_known_line = vim.api.nvim_buf_get_mark(opts.buf, '"')[1]
        if not (ft:match 'commit' and ft:match 'rebase') and last_known_line > 1 and last_known_line <= vim.api.nvim_buf_line_count(opts.buf) then
          vim.api.nvim_feedkeys([[g`"]], 'nx', false)
        end
      end,
    })
  end,
  group = openGroup,
})

-- [[ Keep cursor centered ]]
local function stay_centered()
  -- Get the current cursor position
  local cursor = vim.api.nvim_win_get_cursor(0)
  local line = cursor[1]
  if vim.bo.filetype ~= 'oil' then
    if line ~= vim.b.last_line then
      -- Center the screen around the cursor
      vim.api.nvim_command 'normal! zz'
      -- Restore the cursor position
      vim.api.nvim_win_set_cursor(0, cursor)
    end
  end
end

local centerGroup = vim.api.nvim_create_augroup('StayCentered', { clear = true })
vim.api.nvim_create_autocmd('CursorMovedI', {
  group = centerGroup,
  callback = function()
    stay_centered()
  end,
})
vim.api.nvim_create_autocmd('CursorMoved', {
  group = centerGroup,
  callback = function()
    stay_centered()
  end,
})
vim.api.nvim_create_autocmd('BufEnter', {
  group = centerGroup,
  callback = function()
    stay_centered()
  end,
})

-- [[ Go into relative numbers only in visual mode ]]
local visual_event_group = vim.api.nvim_create_augroup('visual_event', { clear = true })
vim.api.nvim_create_autocmd('ModeChanged', {
  group = visual_event_group,
  pattern = { '*:[vV\x16]*' },
  callback = function()
    vim.wo.relativenumber = true
  end,
})

vim.api.nvim_create_autocmd('ModeChanged', {
  group = visual_event_group,
  pattern = { '[vV\x16]*:*' },
  callback = function()
    print 'VisualLeave'
    vim.wo.relativenumber = false
  end,
})

vim.api.nvim_create_autocmd('CursorHold', {
  callback = function()
    vim.diagnostic.open_float(nil, { focusable = false, source = 'if_many' })
  end,
})
