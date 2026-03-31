# typed: false
# frozen_string_literal: true

class Tick < Formula
  desc "Market data CLI tool for stocks, futures, and crypto"
  homepage "https://github.com/gamepunk/tick"
  url "https://github.com/gamepunk/tick/archive/refs/tags/v0.0.4.tar.gz"
  sha256 "e87ffc603e601fa5c7de697b7e81ef00bd5c76041532a1072b0a45817b955b2a"
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
