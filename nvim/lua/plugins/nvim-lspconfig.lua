-- NOTE: This is where your plugins related to LSP can be installed.
return {
  -- LSP Configuration & Plugins
  'neovim/nvim-lspconfig',
  dependencies = {
    -- `neodev` configures Lua LSP for your Neovim config, runtime and plugins
    -- used for completion, annotations and signatures of Neovim apis
    'folke/lazydev.nvim',
    'https://git.sr.ht/~whynothugo/lsp_lines.nvim',
  },
  event = 'BufEnter',
  config = function()
    local function text_format(symbol)
      local fragments = {}

      -- Indicator that shows if there are any other symbols in the same line
      local stacked_functions = symbol.stacked_count > 0 and (' | +%s'):format(symbol.stacked_count) or ''

      if symbol.references then
        local usage = symbol.references <= 1 and 'usage' or 'usages'
        local num = symbol.references == 0 and 'no' or symbol.references
        table.insert(fragments, ('%s %s'):format(num, usage))
      end

      if symbol.definition then
        table.insert(fragments, symbol.definition .. ' defs')
      end

      if symbol.implementation then
        table.insert(fragments, symbol.implementation .. ' impls')
      end

      return table.concat(fragments, ', ') .. stacked_functions
    end

    require('lazydev').setup {}
    require('lsp_lines').setup {}

    --  This function gets run when an LSP connects to a particular buffer.
    vim.api.nvim_create_autocmd('LspAttach', {
      group = vim.api.nvim_create_augroup('kickstart-lsp-attach', { clear = true }),
      callback = function(event)
        local MiniExtra = require 'mini.extra'
        local bufnr = event.buf

        require('utils').keymapSetList({
          { 'n', '<leader>rn', vim.lsp.buf.rename, { desc = '[R]e[n]ame' } },
          { 'n', '<leader>ca', vim.lsp.buf.code_action, { desc = '[C]ode [A]ction' } },
          {
            'n',
            'gD',
            function()
              MiniExtra.pickers.lsp { scope = 'declaration' }
            end,
            { desc = '[G]oto [D]eclaration' },
          },
          {
            'n',
            'gd',
            function()
              MiniExtra.pickers.lsp { scope = 'definition' }
            end,
            { desc = '[G]oto [D]efinition' },
          },
          {
            'n',
            '<leader>ds',
            function()
              MiniExtra.pickers.lsp { scope = 'document_symbol' }
            end,
            { desc = '[D]ocument [S]ymbols' },
          },
          {
            'n',
            'gI',
            function()
              MiniExtra.pickers.lsp { scope = 'implementation' }
            end,
            { desc = '[G]oto [I]mplementation' },
          },
          {
            'n',
            'gr',
            function()
              MiniExtra.pickers.lsp { scope = 'references' }
            end,
            { desc = '[G]oto [R]eferences' },
          },
          {
            'n',
            '<leader>D',
            function()
              MiniExtra.pickers.lsp { scope = 'type_definition' }
            end,
            { desc = 'Type [D]efinition' },
          },
          -- See `:help K` for why this keymap
          { 'n', 'K', vim.lsp.buf.hover, { desc = 'Hover Documentation' } },
          { { 'n', 'i' }, '<leader>k', vim.lsp.buf.signature_help, { desc = 'Signature Documentation' } },
          { 'n', '<leader>K', '<cmd>norm! K<cr>', { desc = 'Run keywordprg' } },
        }, bufnr, 'LSP: ')

        -- Enable inlay hints globaly
        local client = vim.lsp.get_client_by_id(event.data.client_id)
        if client and client.supports_method(vim.lsp.protocol.Methods.textDocument_inlayHint) then
          require('utils').keymapSet('n', '<leader>th', function()
            vim.lsp.inlay_hint.enable(not vim.lsp.inlay_hint.is_enabled { bufnr = bufnr })
          end, { desc = '[T]oggle Inlay [H]ints' }, bufnr, 'LSP: ')
        end

        -- Create a command `:Format` local to the LSP buffer
        vim.api.nvim_create_user_command('Format', function(args)
          local range = nil
          if args.count ~= -1 then
            local end_line = vim.api.nvim_buf_get_lines(0, args.line2 - 1, args.line2, true)[1]
            range = {
              start = { args.line1, 0 },
              ['end'] = { args.line2, end_line:len() },
            }
          end
          require('conform').format { async = true, lsp_fallback = true, range = range }
        end, { range = true })
      end,
    })
  end,
}
