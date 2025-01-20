return {
  'folke/noice.nvim',
  dependencies = {
    'MunifTanjim/nui.nvim',
    'rcarriga/nvim-notify',
  },
  opts = {
    lsp = {
      progress = {
        enabled = true,
        view = 'cmdline',
      },
      override = {
        ['vim.lsp.util.convert_input_to_markdown_lines'] = true,
        ['vim.lsp.util.stylize_markdown'] = true,
        ['cmp.entry.get_documentation'] = true,
      },
      hover = {
        enabled = true,
        view = 'hover',
      },
      signature = {
        enabled = true,
        view = 'hover',
      },
    },
    presets = {
      command_palette = true,
      long_message_to_split = true,
      inc_rename = false,
    },
    views = {
      cmdline_popup = {
        position = {
          row = '50%',
          col = '50%',
        },
        size = {
          width = math.floor(vim.o.columns * 0.4),
          height = 'auto',
        },
      },
      popupmenu = {
        relative = 'editor',
        position = {
          row = 11,
          col = '50%',
        },
        size = {
          width = math.floor(vim.o.columns * 0.4),
          height = 'auto',
        },
      },
    },
  },
}
