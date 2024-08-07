-- debug.lua
--
-- Shows how to use the DAP plugin to debug your code.
--
return {
  'mfussenegger/nvim-dap',
  dependencies = {
    -- Creates a beautiful debugger UI
    'rcarriga/nvim-dap-ui',
    'nvim-neotest/nvim-nio',
  },
  keys = { '<F5>' },
  config = function()
    local dap = require 'dap'
    local dapui = require 'dapui'

    -- Dap UI setup
    -- For more information, see |:help nvim-dap-ui|
    dapui.setup {
      -- Set icons to characters that are more likely to work in every terminal.
      --    Feel free to remove or use ones that you like more! :)
      --    Don't feel like these are good choices.
      icons = { expanded = '▾', collapsed = '▸', current_frame = '*' },
      controls = {
        icons = {
          pause = '⏸',
          play = '▶',
          step_into = '⏎',
          step_over = '⏭',
          step_out = '⏮',
          step_back = 'b',
          run_last = '▶▶',
          terminate = '⏹',
          disconnect = '⏏',
        },
      },
    }

    require('utils').keymapSetList {
      { 'n', '<F5>',      dap.continue,          { desc = 'Debug: Start/Continue' } },
      { 'n', '<F1>',      dap.step_into,         { desc = 'Debug: Step Into' } },
      { 'n', '<F2>',      dap.step_over,         { desc = 'Debug: Step Over' } },
      { 'n', '<F3>',      dap.step_out,          { desc = 'Debug: Step Out' } },
      { 'n', '<leader>b', dap.toggle_breakpoint, { desc = 'Debug: Toggle Breakpoint' } },
      {
        'n',
        '<leader>B',
        function()
          dap.set_breakpoint(vim.fn.input 'Breakpoint condition: ')
        end,
        { desc = 'Debug: Set Breakpoint' },
      },
      -- Toggle to see last session result. Without this, you can't see session output in case of unhandled exception.
      { 'n', '<F7>', dapui.toggle, { desc = 'Debug: See last session result.' } },
    }

    -- Setup PHP debugging
    dap.adapters.php = {
      type = 'executable',
      command = 'node',
      args = { vim.fn.stdpath 'data' .. '/mason/packages/php-debug-adapter/extension/out/phpDebug.js' },
    }

    dap.configurations.php = {
      {
        type = 'php',
        request = 'launch',
        name = 'Listen for Xdebug',
        port = 9003,
        pathMappings = {
          ['/var/www/html'] = '${workspaceFolder}',
        },
      },
    }

    dap.listeners.after.event_initialized['dapui_config'] = dapui.open
    dap.listeners.before.event_terminated['dapui_config'] = dapui.close
    dap.listeners.before.event_exited['dapui_config'] = dapui.close
  end,
}
