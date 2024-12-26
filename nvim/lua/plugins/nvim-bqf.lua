return {
    "kevinhwang91/nvim-bqf",
    ft = "qf",
    config = function()
        require("bqf").setup({
            auto_enable = true,
            preview = {
                auto_preview = false,
                border_chars = { "─", "│", "─", "│", "╭", "╮", "╯", "╰" },
            },
            func_map = {
                open = "<CR>",
                pscrollup = "<C-b>",
                pscrolldown = "<C-f>",
            },
        })
    end,
}
