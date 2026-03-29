# typed: false
# frozen_string_literal: true

class Tick < Formula
  desc "Market data CLI tool for stocks, futures, and crypto"
  homepage "https://github.com/gamepunk/tick"
  url "https://github.com/gamepunk/tick/archive/refs/tags/v0.0.3.tar.gz"
  sha256 "e92a7ede7512c5d77e298ecf6f6f8e25889bd4fc0d9b95eec77fdae547153890"
  license "MIT"
  head "https://github.com/gamepunk/tick.git", branch: "main"

  depends_on "python@3.10"

  def install
    system "python3", "-m", "pip", "install", *std_pip_args, "."
  end

  def caveats
    <<~EOS
      The command-line tool is installed as 'tick'.

      Examples:
        tick fetch AAPL -s 2024-01-01
        tick batch BTC-USD ETH-USD -s 2025-01-01
        tick info TSLA
    EOS
  end

  test do
    assert_match "行情数据下载工具", shell_output("#{bin}/tick --help", 0)
  end
end
