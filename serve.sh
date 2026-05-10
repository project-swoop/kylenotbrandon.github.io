#!/usr/bin/env bash
# Local preview: Ruby 3.3 + Bundler 4 (matches Gemfile.lock / CI). Requires Docker Desktop.
# The old jekyll/jekyll images ship Ruby 3.1 + Bundler 2; upgrading to Bundler 4 inside them breaks RubyGems.
set -euo pipefail
cd "$(dirname "$0")"
exec docker run --rm \
  -v "$PWD:/srv/jekyll" \
  -w /srv/jekyll \
  -p 4000:4000 \
  -p 35729:35729 \
  ruby:3.3-bookworm \
  bash -lc "gem install bundler -v 4.0.10 --no-document && bundle install && bundle exec jekyll serve --host 0.0.0.0 --livereload"
